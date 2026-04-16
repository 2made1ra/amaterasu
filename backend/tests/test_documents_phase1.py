from pathlib import Path

from sqlalchemy import inspect


def test_phase1_schema_upgrade_creates_expected_tables_and_columns(session_factory):
    engine = session_factory.kw["bind"]
    inspector = inspect(engine)

    assert {"documents", "contract_facts", "extraction_runs"}.issubset(set(inspector.get_table_names()))

    document_columns = {column["name"]: column for column in inspector.get_columns("documents")}
    assert {"batch_id", "ingestion_source", "queue_priority", "trusted_import"}.issubset(document_columns)
    assert document_columns["batch_id"]["nullable"] is True
    assert document_columns["ingestion_source"]["nullable"] is True
    assert document_columns["queue_priority"]["nullable"] is True
    assert document_columns["trusted_import"]["nullable"] is True


def test_upload_document_creates_record_with_phase1_statuses(client, db_session):
    from app.models.document import Document

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.pdf", b"%PDF-1.4 example", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_status"] == "PENDING_REVIEW"
    assert payload["processing_status"] == "QUEUED"

    document = db_session.get(Document, payload["document_id"])
    assert document is not None
    assert document.review_status.value == "PENDING_REVIEW"
    assert document.processing_status.value == "QUEUED"
    assert Path(document.file_path).exists()


def test_upload_rejects_invalid_file_type(client):
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed"


def test_upload_persists_optional_batch_metadata(client, db_session):
    from app.models.document import Document

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("batch.pdf", b"%PDF-1.4 batch", "application/pdf")},
        data={
            "batch_id": "batch-001",
            "ingestion_source": "BULK_IMPORT",
            "queue_priority": "LOW",
            "trusted_import": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    document = db_session.get(Document, payload["document_id"])

    assert document.batch_id == "batch-001"
    assert document.ingestion_source.value == "BULK_IMPORT"
    assert document.queue_priority.value == "LOW"
    assert document.trusted_import is True


def test_get_document_status_returns_facts_and_batch_metadata(client, db_session):
    from app.models.contract_fact import ContractFact
    from app.models.document import (
        Document,
        DocumentProcessingStatus,
        DocumentReviewStatus,
        IngestionSource,
        QueuePriority,
    )

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("status.pdf", b"%PDF-1.4 status", "application/pdf")},
        data={
            "batch_id": "batch-xyz",
            "ingestion_source": "SERVICE_IMPORT",
            "queue_priority": "NORMAL",
            "trusted_import": "false",
        },
    )
    document_id = upload_response.json()["document_id"]

    document = db_session.get(Document, document_id)
    document.processing_status = DocumentProcessingStatus.FACTS_READY
    document.review_status = DocumentReviewStatus.PENDING_REVIEW
    document.active_extraction_version = 2
    document.batch_id = "batch-xyz"
    document.ingestion_source = IngestionSource.SERVICE_IMPORT
    document.queue_priority = QueuePriority.NORMAL
    db_session.add(
        ContractFact(
            document_id=document.id,
            extraction_version=2,
            schema_version=1,
            facts={"supplier": "Acme LLC", "amount": 1500},
        )
    )
    db_session.commit()

    response = client.get(f"/api/v1/documents/{document.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document.id
    assert payload["processing_status"] == "FACTS_READY"
    assert payload["batch_id"] == "batch-xyz"
    assert payload["ingestion_source"] == "SERVICE_IMPORT"
    assert payload["queue_priority"] == "NORMAL"
    assert payload["facts"]["facts"]["supplier"] == "Acme LLC"


def test_get_document_status_returns_404_for_missing_document(client):
    response = client.get("/api/v1/documents/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"
