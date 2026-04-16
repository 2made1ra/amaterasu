from __future__ import annotations

import logging
import uuid
from typing import Any

from app.core.config import settings
from app.services.llm import get_embeddings


logger = logging.getLogger(__name__)


class QdrantIndexError(RuntimeError):
    pass


def build_collection_configs(vector_size: int | None = None):
    try:
        from qdrant_client.http import models
    except ImportError as exc:  # pragma: no cover - dependency boundary
        raise QdrantIndexError("Missing qdrant-client dependency") from exc

    resolved_vector_size = vector_size or settings.QDRANT_VECTOR_SIZE
    vector_params = models.VectorParams(size=resolved_vector_size, distance=models.Distance.COSINE)
    return {
        settings.QDRANT_SUMMARY_COLLECTION: vector_params,
        settings.QDRANT_CHUNK_COLLECTION: vector_params,
    }


class ContractVectorIndex:
    def __init__(self, client=None, embeddings=None, vector_size: int | None = None):
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:  # pragma: no cover - dependency boundary
            raise QdrantIndexError("Missing qdrant-client dependency") from exc

        self.client = client or QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.embeddings = embeddings or get_embeddings()
        self.collection_configs = build_collection_configs(vector_size)

    def ensure_collections(self) -> None:
        existing_collections = {collection.name for collection in self.client.get_collections().collections}
        for collection_name, vector_params in self.collection_configs.items():
            if collection_name in existing_collections:
                continue
            self.client.create_collection(collection_name=collection_name, vectors_config=vector_params)
            logger.info("qdrant_collection_created collection=%s", collection_name)

    def delete_document_vectors(self, document_id: int) -> None:
        from qdrant_client.http import models

        selector = models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        )
        for collection_name in self.collection_configs:
            self.client.delete(collection_name=collection_name, points_selector=selector, wait=True)
            logger.info("qdrant_document_vectors_deleted collection=%s document_id=%s", collection_name, document_id)

    def upsert_summary(self, *, document, summary: str) -> None:
        vector = self._embed_texts([summary])[0]
        point = self._build_point(
            point_namespace="summary",
            document=document,
            text=summary,
            chunk_index=None,
            vector=vector,
        )
        self.client.upsert(
            collection_name=settings.QDRANT_SUMMARY_COLLECTION,
            points=[point],
            wait=True,
        )
        logger.info("qdrant_summary_upserted document_id=%s", document.id)

    def upsert_chunks(self, *, document, chunks: list[str]) -> None:
        vectors = self._embed_texts(chunks)
        points = [
            self._build_point(
                point_namespace="chunk",
                document=document,
                text=chunk,
                chunk_index=index,
                vector=vector,
            )
            for index, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        self.client.upsert(
            collection_name=settings.QDRANT_CHUNK_COLLECTION,
            points=points,
            wait=True,
        )
        logger.info("qdrant_chunks_upserted document_id=%s chunk_count=%s", document.id, len(points))

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        if hasattr(self.embeddings, "embed_documents"):
            return self.embeddings.embed_documents(texts)
        if hasattr(self.embeddings, "embed_query"):
            return [self.embeddings.embed_query(text) for text in texts]
        raise QdrantIndexError("Configured embeddings client does not support document embeddings")

    def _build_point(
        self,
        *,
        point_namespace: str,
        document,
        text: str,
        chunk_index: int | None,
        vector: list[float],
    ):
        from qdrant_client.http import models

        metadata = {
            "document_id": document.id,
            "owner_id": document.owner_id,
            "document_title": document.title,
            "approval_source": getattr(document.approval_source, "value", document.approval_source),
            "chunk_index": chunk_index,
        }
        payload: dict[str, Any] = {
            "document_id": document.id,
            "owner_id": document.owner_id,
            "document_title": document.title,
            "review_status": getattr(document.review_status, "value", document.review_status),
            "approval_source": getattr(document.approval_source, "value", document.approval_source),
            "page_content": text,
            "metadata": metadata,
        }
        if chunk_index is not None:
            payload["chunk_index"] = chunk_index

        return models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{point_namespace}:{document.id}:{chunk_index}")),
            vector=vector,
            payload=payload,
        )


def get_contract_vector_index() -> ContractVectorIndex:
    return ContractVectorIndex()
