from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.crud import crud_document


@dataclass
class WorkspaceQueryResult:
    assistant_message: str
    result_tree: list[dict]
    total_matches: int
    route: str
    grouping_mode: str = "flat"


def _document_to_result_node(document) -> dict:
    badges = [document.status.value]
    if document.extracted_deadline:
        badges.append(document.extracted_deadline.date().isoformat())

    return {
        "id": f"contract-{document.id}",
        "type": "contract",
        "title": document.title,
        "document_id": document.id,
        "children": [],
        "has_children": False,
        "preview_available": True,
        "badges": badges,
        "meta": {
            "deadline": document.extracted_deadline.isoformat() if document.extracted_deadline else None,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "status": document.status.value,
        },
    }


def _filter_documents(documents: list, query: str) -> list:
    normalized = query.strip().lower()
    if not normalized:
        return documents

    matched = [doc for doc in documents if normalized in doc.title.lower()]
    return matched or documents


def _fallback_answer(query: str, documents: list) -> str:
    if not documents:
        return (
            "I could not find any confirmed contracts for this workspace yet. "
            "Upload and confirm a contract to start building search results."
        )

    if query.strip():
        preview_titles = ", ".join(doc.title for doc in documents[:3])
        if len(documents) == 1:
            return f"I found 1 contract that looks relevant: {preview_titles}."
        return f"I found {len(documents)} relevant contracts. Top matches: {preview_titles}."

    return "Your contract workspace is ready. Ask a question to narrow the results."


def build_workspace_query_result(db: Session, owner_id: int, query: str) -> WorkspaceQueryResult:
    documents = crud_document.get_confirmed_documents_by_owner(db, owner_id)
    matched_documents = _filter_documents(documents, query)
    result_tree = [_document_to_result_node(document) for document in matched_documents]

    route = "fallback"
    try:
        from app.services import rag

        assistant_message = rag.query_rag(query, owner_id)
        route = "rag"
    except Exception:
        assistant_message = _fallback_answer(query, matched_documents)

    return WorkspaceQueryResult(
        assistant_message=assistant_message,
        result_tree=result_tree,
        total_matches=len(result_tree),
        route=route,
    )


def build_contract_chat_reply(db: Session, owner_id: int, document_id: int, query: str) -> str:
    document = crud_document.get_document_for_owner(db, document_id, owner_id)
    if not document:
        raise ValueError("Document not found")

    try:
        from app.services import rag

        return rag.query_rag(query, owner_id, document_id)
    except Exception:
        return (
            f"I am working in the context of \"{document.title}\". "
            "The contract-specific RAG stack is unavailable right now, so I can only confirm the document context."
        )
