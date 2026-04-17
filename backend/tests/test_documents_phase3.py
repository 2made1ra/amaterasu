from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import inspect

from app.core.config import settings
from app.crud import crud_document
from app.models.contract_fact import ContractFact
from app.models.document import (
    Document,
    DocumentApprovalSource,
    DocumentIndexingStatus,
    DocumentProcessingStatus,
    DocumentReviewStatus,
    IngestionSource,
    QueuePriority,
)
from app.models.extraction_run import ExtractionRun, ExtractionRunStatus
from app.services.qdrant_index import ContractVectorIndex, build_collection_configs
from app.tasks.documents import extract_document_facts, index_document


def test_phase3_schema_upgrade_adds_approval_audit_columns(session_factory):
    engine = session_factory.kw["bind"]
    inspector = inspect(engine)

    document_columns = {column["name"] for column in inspector.get_columns("documents")}
    assert {"approval_source", "approved_at", "approved_by_user_id"}.issubset(document_columns)


def test_confirm_document_updates_facts_and_enqueues_indexing(client, db_session, test_user, monkeypatch, tmp_path):
    document = crud_document.create_document(
        db_session,
        title="Manual Review Contract",
        file_path=str(tmp_path / "manual.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=512,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=3,
            facts={
                "company_name": "Acme LLC",
                "signatory_name": "Ivan Petrov",
                "contact_phone": "+7 999 123-45-67",
                "service_price": "1000 RUB",
                "service_subject": "Consulting",
                "service_completion_date": "2026-05-15",
            },
        )
    )
    db_session.commit()

    captured = {}

    def fake_apply_async(*, args, queue):
        captured["args"] = args
        captured["queue"] = queue
        return SimpleNamespace(id="task-index-manual-001")

    monkeypatch.setattr("app.tasks.documents.index_document.apply_async", fake_apply_async)

    response = client.post(
        f"/api/v1/documents/{document.id}/confirm",
        json={
            "facts": {
                "company_name": "Globex",
                "signatory_name": "Petr Sidorov",
                "contact_phone": "+7 900 000-00-00",
                "service_price": "2500 RUB",
                "service_subject": "Equipment maintenance",
                "service_completion_date": "2026-06-30",
                "summary": "Updated after manual review",
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_status"] == "APPROVED"
    assert payload["approval_source"] == "MANUAL"
    assert payload["approved_by_user_id"] == test_user.id
    assert payload["indexing_status"] == "QUEUED"
    assert captured["args"] == [document.id]
    assert captured["queue"] == settings.CELERY_HIGH_PRIORITY_QUEUE

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    refreshed_facts = db_session.query(ContractFact).filter(ContractFact.document_id == document.id).one()

    assert refreshed_document.review_status == DocumentReviewStatus.APPROVED
    assert refreshed_document.approval_source == DocumentApprovalSource.MANUAL
    assert refreshed_document.indexing_status == DocumentIndexingStatus.QUEUED
    assert refreshed_facts.facts["company_name"] == "Globex"
    assert refreshed_facts.facts["service_price"] == "2500 RUB"


def test_confirm_document_rejects_incomplete_required_facts(client, db_session, test_user, tmp_path):
    document = crud_document.create_document(
        db_session,
        title="Manual Review Contract",
        file_path=str(tmp_path / "manual-invalid.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=512,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=3,
            facts={
                "company_name": "Acme LLC",
                "signatory_name": "Ivan Petrov",
                "contact_phone": "+7 999 123-45-67",
                "service_price": "1000 RUB",
                "service_subject": "Consulting",
                "service_completion_date": "2026-05-15",
            },
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/documents/{document.id}/confirm",
        json={"facts": {"company_name": "Globex"}},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "LLM response did not match the expected fact schema"


def test_confirm_document_rejects_existing_incomplete_facts_without_manual_override(client, db_session, test_user, tmp_path):
    document = crud_document.create_document(
        db_session,
        title="Manual Review Contract",
        file_path=str(tmp_path / "manual-existing-invalid.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=512,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=3,
            facts={
                "company_name": "Acme LLC",
                "signatory_name": None,
                "contact_phone": "+7 999 123-45-67",
                "service_price": "1000 RUB",
                "service_subject": "Consulting",
                "service_completion_date": "2026-05-15",
                "missing_required_fields": ["signatory_name"],
            },
        )
    )
    db_session.commit()

    response = client.post(f"/api/v1/documents/{document.id}/confirm")

    assert response.status_code == 400
    assert response.json()["detail"] == "LLM response did not match the expected fact schema"


def test_trusted_bulk_document_auto_approves_and_enqueues_indexing(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Trusted Import Contract",
        file_path=str(tmp_path / "trusted.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=256,
        ingestion_source=IngestionSource.BULK_IMPORT,
        queue_priority=QueuePriority.LOW,
        trusted_import=True,
    )
    extraction_run = crud_document.create_extraction_run(
        db_session,
        document_id=document.id,
        extraction_version=1,
        status=ExtractionRunStatus.RUNNING,
    )
    markdown_path = tmp_path / "trusted.md"
    markdown_path.write_text("# Trusted Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.documents.extract_contract_facts_from_markdown",
        lambda markdown, **kwargs: SimpleNamespace(
            model_dump=lambda: {
                "company_name": "Trusted Co",
                "signatory_name": "Anna Smirnova",
                "contact_phone": "+7 922 000-11-22",
                "service_price": "50000 RUB",
                "service_subject": "Warehouse services",
                "service_completion_date": "2026-07-01",
                "missing_required_fields": [],
                "parser_quality": "medium",
                "parser_quality_score": 0.61,
                "summary": "Approved",
            }
        ),
    )

    captured = {}

    def fake_apply_async(*, args, queue):
        captured["args"] = args
        captured["queue"] = queue
        return SimpleNamespace(id="task-index-trusted-001")

    monkeypatch.setattr("app.tasks.documents.index_document.apply_async", fake_apply_async)

    result = extract_document_facts.run(document.id, extraction_run.id, str(markdown_path))

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    stored_facts = db_session.query(ContractFact).filter(ContractFact.document_id == document.id).one()

    assert result["processing_status"] == "FACTS_READY"
    assert refreshed_document.processing_status == DocumentProcessingStatus.FACTS_READY
    assert refreshed_document.review_status == DocumentReviewStatus.APPROVED
    assert refreshed_document.approval_source == DocumentApprovalSource.TRUSTED_IMPORT
    assert refreshed_document.indexing_status == DocumentIndexingStatus.QUEUED
    assert stored_facts.facts["company_name"] == "Trusted Co"
    assert captured["args"] == [document.id]
    assert captured["queue"] == settings.CELERY_BULK_QUEUE


def test_normal_document_stops_at_facts_ready_without_auto_approval(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Normal Upload Contract",
        file_path=str(tmp_path / "normal.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=256,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    extraction_run = crud_document.create_extraction_run(
        db_session,
        document_id=document.id,
        extraction_version=1,
        status=ExtractionRunStatus.RUNNING,
    )
    markdown_path = tmp_path / "normal.md"
    markdown_path.write_text("# Normal Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.documents.extract_contract_facts_from_markdown",
        lambda markdown, **kwargs: SimpleNamespace(
            model_dump=lambda: {
                "company_name": "Standard Co",
                "signatory_name": "Maria Volkova",
                "contact_phone": "+7 343 000-00-01",
                "service_price": "12000 RUB",
                "service_subject": "Cleaning services",
                "service_completion_date": "2026-05-28",
                "missing_required_fields": [],
                "parser_quality": "medium",
                "parser_quality_score": 0.64,
            }
        ),
    )

    captured = {"called": False}

    def fake_apply_async(*, args, queue):
        captured["called"] = True
        return SimpleNamespace(id="task-index-normal-001")

    monkeypatch.setattr("app.tasks.documents.index_document.apply_async", fake_apply_async)

    extract_document_facts.run(document.id, extraction_run.id, str(markdown_path))

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)

    assert refreshed_document.processing_status == DocumentProcessingStatus.FACTS_READY
    assert refreshed_document.review_status == DocumentReviewStatus.PENDING_REVIEW
    assert refreshed_document.approval_source is None
    assert refreshed_document.indexing_status == DocumentIndexingStatus.NOT_INDEXED
    assert captured["called"] is False


def test_trusted_bulk_document_with_missing_required_fields_stops_for_review(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Trusted Import Missing Fields",
        file_path=str(tmp_path / "trusted-missing.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=256,
        ingestion_source=IngestionSource.BULK_IMPORT,
        queue_priority=QueuePriority.LOW,
        trusted_import=True,
    )
    extraction_run = crud_document.create_extraction_run(
        db_session,
        document_id=document.id,
        extraction_version=1,
        status=ExtractionRunStatus.RUNNING,
    )
    markdown_path = tmp_path / "trusted-missing.md"
    markdown_path.write_text("# Trusted Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.documents.extract_contract_facts_from_markdown",
        lambda markdown, **kwargs: SimpleNamespace(
            model_dump=lambda: {
                "document_kind": "supplier_order",
                "company_name": "Trusted Co",
                "signatory_name": None,
                "contact_phone": "+7 922 000-11-22",
                "service_price": "50000 RUB",
                "service_subject": "Warehouse services",
                "service_completion_date": "2026-07-01",
                "missing_required_fields": ["signatory_name"],
                "parser_quality": "medium",
                "parser_quality_score": 0.61,
            },
            missing_required_fields=["signatory_name"],
        ),
    )

    captured = {"called": False}

    def fake_apply_async(*, args, queue):
        captured["called"] = True
        return SimpleNamespace(id="task-index-trusted-missing-001")

    monkeypatch.setattr("app.tasks.documents.index_document.apply_async", fake_apply_async)

    extract_document_facts.run(document.id, extraction_run.id, str(markdown_path))

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    stored_facts = db_session.query(ContractFact).filter(ContractFact.document_id == document.id).one()

    assert refreshed_document.processing_status == DocumentProcessingStatus.FACTS_READY
    assert refreshed_document.review_status == DocumentReviewStatus.PENDING_REVIEW
    assert refreshed_document.approval_source is None
    assert refreshed_document.indexing_status == DocumentIndexingStatus.NOT_INDEXED
    assert stored_facts.facts["missing_required_fields"] == ["signatory_name"]
    assert captured["called"] is False


def test_qdrant_setup_ensures_summary_and_chunk_collections():
    created_collections = []

    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(collections=[])

        def create_collection(self, *, collection_name, vectors_config):
            created_collections.append((collection_name, vectors_config))

    class FakeEmbeddings:
        def embed_documents(self, texts):
            return [[0.1] * 8 for _ in texts]

    configs = build_collection_configs(vector_size=8)
    vector_index = ContractVectorIndex(client=FakeClient(), embeddings=FakeEmbeddings(), vector_size=8)
    vector_index.ensure_collections()

    assert set(configs) == {settings.QDRANT_SUMMARY_COLLECTION, settings.QDRANT_CHUNK_COLLECTION}
    assert configs[settings.QDRANT_SUMMARY_COLLECTION].size == 8
    assert configs[settings.QDRANT_CHUNK_COLLECTION].size == 8
    assert [name for name, _ in created_collections] == [
        settings.QDRANT_SUMMARY_COLLECTION,
        settings.QDRANT_CHUNK_COLLECTION,
    ]


def test_index_document_deletes_old_vectors_before_upserting_new_ones(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "PARSED_MARKDOWN_DIR", str(artifact_root))

    document = crud_document.create_document(
        db_session,
        title="Indexed Contract",
        file_path=str(tmp_path / "indexed.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=512,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.review_status = DocumentReviewStatus.APPROVED
    document.approval_source = DocumentApprovalSource.MANUAL
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=3,
            facts={
                "company_name": "Indexable Co",
                "signatory_name": "Elena Volkova",
                "contact_phone": "+7 343 111-22-33",
                "service_price": "42000 RUB",
                "service_subject": "Event logistics",
                "service_completion_date": "2026-06-01",
                "summary": None,
                "parser_quality": "medium",
                "parser_quality_score": 0.71,
            },
        )
    )
    db_session.commit()

    metadata_path = artifact_root / "indexed.parse.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        '{"quality_label":"medium","quality_score":0.71,"extraction_method":"ocr","page_count":1,"usable_page_count":1,"low_quality_page_count":0,"total_text_chars":200,"pages":[]}',
        encoding="utf-8",
    )

    markdown_path = artifact_root / "indexed.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("# Indexed Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr("app.tasks.documents.generate_document_summary", lambda markdown, facts: "summary text")
    monkeypatch.setattr("app.tasks.documents.split_markdown_into_chunks", lambda markdown: ["chunk a", "chunk b"])

    calls = []

    class FakeVectorIndex:
        def ensure_collections(self):
            calls.append("ensure")

        def delete_document_vectors(self, document_id):
            calls.append(("delete", document_id))

        def upsert_summary(self, *, document, summary):
            calls.append(("summary", document.id, summary))

        def upsert_chunks(self, *, document, chunks):
            calls.append(("chunks", document.id, list(chunks)))

    monkeypatch.setattr("app.tasks.documents.get_contract_vector_index", lambda: FakeVectorIndex())

    result = index_document.run(document.id)

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)

    assert result["indexing_status"] == "INDEXED"
    assert refreshed_document.indexing_status == DocumentIndexingStatus.INDEXED
    assert calls == [
        "ensure",
        ("delete", document.id),
        ("summary", document.id, "summary text"),
        ("chunks", document.id, ["chunk a", "chunk b"]),
    ]


def test_index_document_rejects_low_quality_facts(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "PARSED_MARKDOWN_DIR", str(artifact_root))

    document = crud_document.create_document(
        db_session,
        title="Low Quality Contract",
        file_path=str(tmp_path / "low-quality.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=512,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.review_status = DocumentReviewStatus.APPROVED
    document.approval_source = DocumentApprovalSource.MANUAL
    document.active_extraction_version = 1
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=1,
            schema_version=3,
            facts={
                "company_name": "Indexable Co",
                "signatory_name": "Elena Volkova",
                "contact_phone": "+7 343 111-22-33",
                "service_price": "42000 RUB",
                "service_subject": "Event logistics",
                "service_completion_date": "2026-06-01",
                "parser_quality": "low",
                "parser_quality_score": 0.22,
            },
        )
    )
    db_session.commit()

    markdown_path = artifact_root / "low-quality.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("# Low Quality Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)

    try:
        index_document.run(document.id)
    except Exception:
        pass

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)

    assert refreshed_document.indexing_status == DocumentIndexingStatus.FAILED


def test_worker_startup_registers_index_document_task():
    from app.celery_app import celery_app

    assert "app.tasks.documents.index_document" in celery_app.tasks
