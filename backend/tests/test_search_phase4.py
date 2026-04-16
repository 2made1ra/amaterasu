from types import SimpleNamespace

from app.crud import crud_document
from app.models.contract_fact import ContractFact
from app.models.document import (
    DocumentReviewStatus,
    IngestionSource,
    QueuePriority,
)
from app.services.query_router import QueryRoute, route_query
from app.services.sql_search import search_contract_facts
from app.services.vector_search import ContractVectorSearcher
from app.services.workspace import build_workspace_query_result


def _create_approved_document(
    db_session,
    test_user,
    tmp_path,
    *,
    title: str,
    supplier: str,
    effective_date: str,
    termination_date: str | None = None,
):
    document = crud_document.create_document(
        db_session,
        title=title,
        file_path=str(tmp_path / f"{title}.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=1024,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.review_status = DocumentReviewStatus.APPROVED
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=1,
            facts={
                "supplier": supplier,
                "effective_date": effective_date,
                "termination_date": termination_date,
                "summary": f"{title} summary",
            },
        )
    )
    db_session.commit()
    db_session.refresh(document)
    return document


def test_query_router_classifies_phase4_routes():
    assert route_query("List contracts for Acme in 2023").route == QueryRoute.SQL_ONLY
    assert route_query("Which contracts mention data residency?").route == QueryRoute.SUMMARY_ONLY
    assert route_query("Explain the payment obligations for Acme in 2023").route == QueryRoute.HYBRID_SQL_AND_CHUNKS
    assert route_query("Show the exact wording of the termination clause").route == QueryRoute.CHUNKS_ONLY
    assert route_query("What are the termination obligations across our approved contracts?").route == QueryRoute.SUMMARY_THEN_CHUNKS


def test_sql_search_filters_by_year_supplier_and_date_range(db_session, test_user, tmp_path):
    acme_2023 = _create_approved_document(
        db_session,
        test_user,
        tmp_path,
        title="Acme 2023 MSA",
        supplier="Acme LLC",
        effective_date="2023-02-15",
        termination_date="2024-02-15",
    )
    _create_approved_document(
        db_session,
        test_user,
        tmp_path,
        title="Acme 2024 Renewal",
        supplier="Acme LLC",
        effective_date="2024-01-10",
        termination_date="2025-01-10",
    )
    _create_approved_document(
        db_session,
        test_user,
        tmp_path,
        title="Globex 2023 Services",
        supplier="Globex Corp",
        effective_date="2023-07-01",
        termination_date="2023-12-31",
    )

    matches = search_contract_facts(
        db_session,
        owner_id=test_user.id,
        filters=route_query("List contracts for Acme in 2023 from 2023-01-01 to 2023-12-31").filters,
    )

    assert [match.document.id for match in matches] == [acme_2023.id]
    assert matches[0].facts["supplier"] == "Acme LLC"


def test_summary_then_chunks_limits_chunk_search_to_top_three_documents():
    search_calls = []

    class FakeClient:
        def search(self, *, collection_name, query_vector, query_filter, limit):
            search_calls.append(
                {
                    "collection_name": collection_name,
                    "query_filter": query_filter,
                    "limit": limit,
                }
            )
            if collection_name == "contract_summaries":
                return [
                    SimpleNamespace(
                        score=0.9,
                        payload={"document_id": 101, "document_title": "A", "page_content": "summary a"},
                    ),
                    SimpleNamespace(
                        score=0.8,
                        payload={"document_id": 102, "document_title": "B", "page_content": "summary b"},
                    ),
                    SimpleNamespace(
                        score=0.7,
                        payload={"document_id": 103, "document_title": "C", "page_content": "summary c"},
                    ),
                    SimpleNamespace(
                        score=0.6,
                        payload={"document_id": 104, "document_title": "D", "page_content": "summary d"},
                    ),
                ]
            return [
                SimpleNamespace(
                    score=0.95,
                    payload={"document_id": 103, "document_title": "C", "page_content": "chunk c"},
                )
            ]

    class FakeEmbeddings:
        def embed_query(self, query):
            return [0.1, 0.2, 0.3]

    searcher = ContractVectorSearcher(client=FakeClient(), embeddings=FakeEmbeddings())
    result = searcher.search_summary_then_chunks(query="explain data residency", owner_id=77)

    assert result.shortlisted_document_ids == [101, 102, 103]
    assert len(search_calls) == 2
    assert search_calls[0]["collection_name"] == "contract_summaries"
    assert search_calls[1]["collection_name"] == "contract_chunks"
    assert search_calls[1]["query_filter"].model_dump(exclude_none=True) == {
        "must": [
            {"key": "owner_id", "match": {"value": 77}},
            {"key": "document_id", "match": {"any": [101, 102, 103]}},
        ]
    }


def test_workspace_query_result_uses_sql_orchestration(db_session, test_user, tmp_path):
    document = _create_approved_document(
        db_session,
        test_user,
        tmp_path,
        title="Acme Master Services Agreement",
        supplier="Acme LLC",
        effective_date="2023-03-20",
        termination_date="2024-03-20",
    )

    result = build_workspace_query_result(db_session, test_user.id, "List contracts for Acme in 2023")

    assert result.route == "SQL_ONLY"
    assert result.total_matches == 1
    assert result.result_tree[0]["document_id"] == document.id
    assert "Acme Master Services Agreement" in result.assistant_message
