from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.query_router import QueryFilters, QueryRoute, route_query
from app.services.sql_search import search_contract_facts
from app.services.vector_search import (
    ContractVectorSearcher,
    VectorSearchDependencyError,
    VectorHit,
    get_contract_vector_searcher,
)


@dataclass(slots=True)
class SearchOrchestrationResult:
    assistant_message: str
    route: QueryRoute
    documents: list[Document]
    filters: QueryFilters
    total_matches: int
    snippets_by_document: dict[int, list[str]] = field(default_factory=dict)


def orchestrate_contract_search(
    db: Session,
    *,
    owner_id: int,
    query: str,
    document_id: int | None = None,
    vector_searcher: ContractVectorSearcher | None = None,
) -> SearchOrchestrationResult:
    decision = route_query(query, document_id=document_id)

    if decision.route == QueryRoute.SQL_ONLY:
        sql_matches = search_contract_facts(db, owner_id=owner_id, filters=decision.filters)
        documents = [match.document for match in sql_matches]
        return SearchOrchestrationResult(
            assistant_message=_format_sql_answer(sql_matches, decision.filters),
            route=decision.route,
            documents=documents,
            filters=decision.filters,
            total_matches=len(documents),
        )

    vector_searcher = vector_searcher or get_contract_vector_searcher()

    if decision.route == QueryRoute.SUMMARY_ONLY:
        summary_hits = vector_searcher.search_summaries(query=query, owner_id=owner_id, limit=3)
        return _build_vector_result(
            db,
            owner_id=owner_id,
            route=decision.route,
            filters=decision.filters,
            summary_hits=summary_hits,
            chunk_hits=[],
            answer=_format_summary_answer(summary_hits),
        )

    if decision.route == QueryRoute.CHUNKS_ONLY:
        chunk_hits = vector_searcher.search_chunks(
            query=query,
            owner_id=owner_id,
            document_ids=decision.filters.document_ids or None,
            limit=6,
        )
        return _build_vector_result(
            db,
            owner_id=owner_id,
            route=decision.route,
            filters=decision.filters,
            summary_hits=[],
            chunk_hits=chunk_hits,
            answer=_format_chunk_answer(chunk_hits),
        )

    if decision.route == QueryRoute.HYBRID_SQL_AND_CHUNKS:
        sql_matches = search_contract_facts(db, owner_id=owner_id, filters=decision.filters)
        matched_document_ids = [match.document.id for match in sql_matches]
        chunk_hits = (
            vector_searcher.search_chunks(
                query=query,
                owner_id=owner_id,
                document_ids=matched_document_ids,
                limit=6,
            )
            if matched_document_ids
            else []
        )
        answer = _format_hybrid_answer(sql_matches, chunk_hits, decision.filters)
        return _build_vector_result(
            db,
            owner_id=owner_id,
            route=decision.route,
            filters=decision.filters,
            summary_hits=[],
            chunk_hits=chunk_hits,
            answer=answer,
            preferred_document_ids=matched_document_ids,
        )

    summary_then_chunks = vector_searcher.search_summary_then_chunks(query=query, owner_id=owner_id)
    return _build_vector_result(
        db,
        owner_id=owner_id,
        route=decision.route,
        filters=decision.filters,
        summary_hits=summary_then_chunks.summary_hits,
        chunk_hits=summary_then_chunks.chunk_hits,
        answer=_format_summary_then_chunks_answer(
            summary_then_chunks.summary_hits,
            summary_then_chunks.chunk_hits,
        ),
        preferred_document_ids=summary_then_chunks.shortlisted_document_ids,
    )


def safe_orchestrate_contract_search(
    db: Session,
    *,
    owner_id: int,
    query: str,
    document_id: int | None = None,
) -> SearchOrchestrationResult:
    try:
        return orchestrate_contract_search(
            db,
            owner_id=owner_id,
            query=query,
            document_id=document_id,
        )
    except VectorSearchDependencyError:
        decision = route_query(query, document_id=document_id)
        sql_matches = search_contract_facts(db, owner_id=owner_id, filters=decision.filters)
        documents = [match.document for match in sql_matches]
        return SearchOrchestrationResult(
            assistant_message=_fallback_answer(query, documents),
            route=decision.route,
            documents=documents,
            filters=decision.filters,
            total_matches=len(documents),
        )


def _build_vector_result(
    db: Session,
    *,
    owner_id: int,
    route: QueryRoute,
    filters: QueryFilters,
    summary_hits: list[VectorHit],
    chunk_hits: list[VectorHit],
    answer: str,
    preferred_document_ids: list[int] | None = None,
) -> SearchOrchestrationResult:
    ordered_document_ids = preferred_document_ids or _dedupe_document_ids(summary_hits + chunk_hits)
    documents = _load_documents_by_ids(db, owner_id=owner_id, document_ids=ordered_document_ids)
    return SearchOrchestrationResult(
        assistant_message=answer,
        route=route,
        documents=documents,
        filters=filters,
        total_matches=len(documents),
        snippets_by_document=_group_snippets_by_document(chunk_hits or summary_hits),
    )


def _load_documents_by_ids(db: Session, *, owner_id: int, document_ids: list[int]) -> list[Document]:
    if not document_ids:
        return []

    documents = (
        db.query(Document)
        .filter(Document.owner_id == owner_id, Document.id.in_(document_ids))
        .all()
    )
    by_id = {document.id: document for document in documents}
    return [by_id[document_id] for document_id in document_ids if document_id in by_id]


def _dedupe_document_ids(hits: list[VectorHit]) -> list[int]:
    ordered_ids: list[int] = []
    for hit in hits:
        if hit.document_id not in ordered_ids:
            ordered_ids.append(hit.document_id)
    return ordered_ids


def _group_snippets_by_document(hits: list[VectorHit]) -> dict[int, list[str]]:
    snippets: dict[int, list[str]] = {}
    for hit in hits:
        if not hit.text:
            continue
        snippets.setdefault(hit.document_id, []).append(_trim_snippet(hit.text))
    return snippets


def _format_sql_answer(matches, filters: QueryFilters) -> str:
    if not matches:
        return f"I could not find any approved contracts matching {_describe_filters(filters)}."

    lines = [f"I found {len(matches)} approved contract(s) matching {_describe_filters(filters)}:"]
    for match in matches[:5]:
        facts = match.facts
        supplier = facts.get("company_name") or facts.get("supplier") or ", ".join(facts.get("parties") or [])
        effective_date = (
            facts.get("service_completion_date")
            or facts.get("effective_date")
            or facts.get("termination_date")
            or "unknown date"
        )
        lines.append(f"- {match.document.title} ({supplier or 'unknown company'}, {effective_date})")
    return "\n".join(lines)


def _format_summary_answer(summary_hits: list[VectorHit]) -> str:
    if not summary_hits:
        return "I could not find any approved contracts that matched that topic."

    lines = [f"I found {len(_dedupe_document_ids(summary_hits))} relevant contract(s)."]
    for hit in summary_hits[:3]:
        title = hit.document_title or f"Document {hit.document_id}"
        lines.append(f"- {title}: {_trim_snippet(hit.text)}")
    return "\n".join(lines)


def _format_chunk_answer(chunk_hits: list[VectorHit]) -> str:
    if not chunk_hits:
        return "I could not find a relevant passage in the approved contract set."

    lines = ["I found these relevant contract passages:"]
    for hit in chunk_hits[:4]:
        title = hit.document_title or f"Document {hit.document_id}"
        lines.append(f"- {title}: {_trim_snippet(hit.text)}")
    return "\n".join(lines)


def _format_hybrid_answer(sql_matches, chunk_hits: list[VectorHit], filters: QueryFilters) -> str:
    if not sql_matches:
        return f"I could not find any approved contracts matching {_describe_filters(filters)}."

    lines = [f"I found {len(sql_matches)} structured match(es) for {_describe_filters(filters)}."]
    if chunk_hits:
        lines.append("Relevant passages from those contracts:")
        for hit in chunk_hits[:4]:
            title = hit.document_title or f"Document {hit.document_id}"
            lines.append(f"- {title}: {_trim_snippet(hit.text)}")
    return "\n".join(lines)


def _format_summary_then_chunks_answer(summary_hits: list[VectorHit], chunk_hits: list[VectorHit]) -> str:
    if not summary_hits and not chunk_hits:
        return "I could not find any approved contracts that answered that question."

    if chunk_hits:
        lines = ["I reviewed the most relevant contracts and found these passages:"]
        for hit in chunk_hits[:4]:
            title = hit.document_title or f"Document {hit.document_id}"
            lines.append(f"- {title}: {_trim_snippet(hit.text)}")
        return "\n".join(lines)

    return _format_summary_answer(summary_hits)


def _fallback_answer(query: str, documents: list[Document]) -> str:
    if not documents:
        return (
            "I could not find any approved contracts for this workspace yet. "
            "Upload and confirm a contract to start building search results."
        )

    preview_titles = ", ".join(document.title for document in documents[:3])
    if query.strip():
        if len(documents) == 1:
            return f"I found 1 contract that looks relevant: {preview_titles}."
        return f"I found {len(documents)} relevant contracts. Top matches: {preview_titles}."
    return "Your contract workspace is ready. Ask a question to narrow the results."


def _describe_filters(filters: QueryFilters) -> str:
    parts: list[str] = []
    if filters.supplier:
        parts.append(f'supplier "{filters.supplier}"')
    if filters.year is not None:
        parts.append(f"year {filters.year}")
    if filters.date_from is not None or filters.date_to is not None:
        parts.append(
            f"date range {filters.date_from.isoformat() if filters.date_from else '...'}"
            f" to {filters.date_to.isoformat() if filters.date_to else '...'}"
        )
    if not parts:
        return "the current workspace filters"
    return ", ".join(parts)


def _trim_snippet(text: str, limit: int = 180) -> str:
    compact_text = " ".join(text.split())
    if len(compact_text) <= limit:
        return compact_text
    return f"{compact_text[: limit - 3].rstrip()}..."
