from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.llm import get_embeddings


class VectorSearchDependencyError(RuntimeError):
    pass


@dataclass(slots=True)
class VectorHit:
    document_id: int
    score: float | None
    text: str
    document_title: str | None = None


@dataclass(slots=True)
class SummaryThenChunksResult:
    shortlisted_document_ids: list[int]
    summary_hits: list[VectorHit]
    chunk_hits: list[VectorHit]


class ContractVectorSearcher:
    def __init__(self, client=None, embeddings=None):
        if client is None:
            try:
                from qdrant_client import QdrantClient
            except ImportError as exc:  # pragma: no cover - dependency boundary
                raise VectorSearchDependencyError("Missing qdrant-client dependency") from exc
            client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        self.client = client
        self.embeddings = embeddings or get_embeddings()

    def search_summaries(self, *, query: str, owner_id: int, limit: int = 3) -> list[VectorHit]:
        filter_obj = self._build_filter(owner_id=owner_id, document_ids=None)
        raw_hits = self._search(
            collection_name=settings.QDRANT_SUMMARY_COLLECTION,
            query=query,
            filter_obj=filter_obj,
            limit=limit,
        )
        return self._to_vector_hits(raw_hits)

    def search_chunks(
        self,
        *,
        query: str,
        owner_id: int,
        document_ids: list[int] | None = None,
        limit: int = 6,
    ) -> list[VectorHit]:
        filter_obj = self._build_filter(owner_id=owner_id, document_ids=document_ids)
        raw_hits = self._search(
            collection_name=settings.QDRANT_CHUNK_COLLECTION,
            query=query,
            filter_obj=filter_obj,
            limit=limit,
        )
        return self._to_vector_hits(raw_hits)

    def search_summary_then_chunks(
        self,
        *,
        query: str,
        owner_id: int,
        summary_limit: int = 3,
        chunk_limit: int = 6,
    ) -> SummaryThenChunksResult:
        summary_hits = self.search_summaries(query=query, owner_id=owner_id, limit=summary_limit)

        shortlisted_document_ids: list[int] = []
        for hit in summary_hits:
            if hit.document_id in shortlisted_document_ids:
                continue
            shortlisted_document_ids.append(hit.document_id)
            if len(shortlisted_document_ids) == summary_limit:
                break

        if not shortlisted_document_ids:
            return SummaryThenChunksResult(
                shortlisted_document_ids=[],
                summary_hits=summary_hits,
                chunk_hits=[],
            )

        chunk_hits = self.search_chunks(
            query=query,
            owner_id=owner_id,
            document_ids=shortlisted_document_ids,
            limit=chunk_limit,
        )
        return SummaryThenChunksResult(
            shortlisted_document_ids=shortlisted_document_ids,
            summary_hits=summary_hits,
            chunk_hits=chunk_hits,
        )

    def _search(self, *, collection_name: str, query: str, filter_obj, limit: int):
        query_vector = self._embed_query(query)
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=filter_obj,
            limit=limit,
        )

    def _embed_query(self, query: str) -> list[float]:
        if hasattr(self.embeddings, "embed_query"):
            return self.embeddings.embed_query(query)
        if hasattr(self.embeddings, "embed_documents"):
            return self.embeddings.embed_documents([query])[0]
        raise VectorSearchDependencyError("Configured embeddings client does not support query embeddings")

    def _build_filter(self, *, owner_id: int, document_ids: list[int] | None):
        try:
            from qdrant_client.http import models
        except ImportError as exc:  # pragma: no cover - dependency boundary
            raise VectorSearchDependencyError("Missing qdrant-client dependency") from exc

        must_conditions = [
            models.FieldCondition(
                key="owner_id",
                match=models.MatchValue(value=owner_id),
            )
        ]
        if document_ids:
            if len(document_ids) == 1:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_ids[0]),
                    )
                )
            else:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=document_ids),
                    )
                )

        return models.Filter(must=must_conditions)

    def _to_vector_hits(self, raw_hits) -> list[VectorHit]:
        hits: list[VectorHit] = []
        for hit in raw_hits:
            payload = getattr(hit, "payload", {}) or {}
            hits.append(
                VectorHit(
                    document_id=int(payload["document_id"]),
                    score=getattr(hit, "score", None),
                    text=payload.get("page_content", ""),
                    document_title=payload.get("document_title"),
                )
            )
        return hits


def get_contract_vector_searcher() -> ContractVectorSearcher:
    return ContractVectorSearcher()
