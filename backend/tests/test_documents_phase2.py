from pathlib import Path
from types import SimpleNamespace

from app.core.config import settings
from app.crud import crud_document
from app.models.contract_fact import ContractFact
from app.models.document import (
    Document,
    DocumentIndexingStatus,
    DocumentProcessingStatus,
    DocumentReviewStatus,
    IngestionSource,
    QueuePriority,
)
from app.models.extraction_run import ExtractionRun, ExtractionRunStatus
from app.services.bulk_ingestion import build_upload_plan
from app.services.fact_extraction import FactExtractionValidationError
from app.tasks.documents import extract_document_facts, process_document


def test_upload_enqueues_process_document_on_high_priority_queue(client, monkeypatch):
    captured = {}

    def fake_apply_async(*, args, queue):
        captured["args"] = args
        captured["queue"] = queue
        return SimpleNamespace(id="task-ui-001")

    monkeypatch.setattr("app.api.api_v1.endpoints.documents.process_document.apply_async", fake_apply_async)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("contract.pdf", b"%PDF-1.4 example", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue_priority"] == "HIGH"
    assert captured["queue"] == settings.CELERY_HIGH_PRIORITY_QUEUE
    assert captured["args"] == [payload["document_id"]]


def test_upload_routes_bulk_imports_to_bulk_queue(client, monkeypatch):
    captured = {}

    def fake_apply_async(*, args, queue):
        captured["args"] = args
        captured["queue"] = queue
        return SimpleNamespace(id="task-bulk-001")

    monkeypatch.setattr("app.api.api_v1.endpoints.documents.process_document.apply_async", fake_apply_async)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("bulk.pdf", b"%PDF-1.4 bulk", "application/pdf")},
        data={
            "batch_id": "batch-001",
            "ingestion_source": "BULK_IMPORT",
            "queue_priority": "LOW",
            "trusted_import": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue_priority"] == "LOW"
    assert captured["queue"] == settings.CELERY_BULK_QUEUE
    assert captured["args"] == [payload["document_id"]]


def test_worker_startup_registers_document_tasks():
    from app.celery_app import celery_app

    assert "app.tasks.documents.process_document" in celery_app.tasks
    assert "app.tasks.documents.extract_document_facts" in celery_app.tasks


def test_process_document_marks_parsing_and_enqueues_fact_extraction(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Contract",
        file_path=str(tmp_path / "contract.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=128,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )
    Path(document.file_path).write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.documents.parse_pdf_to_markdown",
        lambda file_path: SimpleNamespace(markdown="# Contract", artifact_path=str(tmp_path / "contract.md")),
    )

    captured = {}

    def fake_apply_async(*, args, queue):
        captured["args"] = args
        captured["queue"] = queue
        return SimpleNamespace(id="task-extract-001")

    monkeypatch.setattr("app.tasks.documents.extract_document_facts.apply_async", fake_apply_async)

    result = process_document.run(document.id)

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    extraction_runs = db_session.query(ExtractionRun).filter(ExtractionRun.document_id == document.id).all()

    assert result["document_id"] == document.id
    assert refreshed_document.processing_status == DocumentProcessingStatus.PARSING
    assert len(extraction_runs) == 1
    assert extraction_runs[0].status == ExtractionRunStatus.RUNNING
    assert captured["queue"] == settings.CELERY_HIGH_PRIORITY_QUEUE
    assert captured["args"][0] == document.id


def test_process_document_failure_marks_document_failed(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Broken Contract",
        file_path=str(tmp_path / "broken.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=128,
    )
    Path(document.file_path).write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)

    def fail_parse(_file_path):
        from app.services.document_parser import DocumentParsingError

        raise DocumentParsingError("parser failed")

    monkeypatch.setattr("app.tasks.documents.parse_pdf_to_markdown", fail_parse)

    try:
        process_document.run(document.id)
    except Exception:
        pass

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    extraction_run = db_session.query(ExtractionRun).filter(ExtractionRun.document_id == document.id).one()

    assert refreshed_document.processing_status == DocumentProcessingStatus.FAILED
    assert refreshed_document.last_error == "parser failed"
    assert extraction_run.status == ExtractionRunStatus.FAILED
    assert extraction_run.error_details["source"] == "pdf_parsing"


def test_extract_document_facts_persists_validated_facts(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Ready Contract",
        file_path=str(tmp_path / "ready.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=256,
    )
    extraction_run = crud_document.create_extraction_run(
        db_session,
        document_id=document.id,
        extraction_version=1,
        status=ExtractionRunStatus.RUNNING,
    )
    extraction_run_id = extraction_run.id
    markdown_path = tmp_path / "ready.md"
    markdown_path.write_text("# Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.tasks.documents.extract_contract_facts_from_markdown",
        lambda markdown: SimpleNamespace(
            model_dump=lambda: {
                "document_title": "Ready Contract",
                "parties": ["Acme LLC", "Globex"],
                "summary": "Agreement summary",
            }
        ),
    )

    result = extract_document_facts.run(document.id, extraction_run_id, str(markdown_path))

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    refreshed_run = db_session.get(ExtractionRun, extraction_run_id)
    stored_facts = db_session.query(ContractFact).filter(ContractFact.document_id == document.id).one()

    assert result["processing_status"] == "FACTS_READY"
    assert refreshed_document.processing_status == DocumentProcessingStatus.FACTS_READY
    assert refreshed_document.active_extraction_version == 1
    assert refreshed_run.status == ExtractionRunStatus.SUCCEEDED
    assert stored_facts.facts["document_title"] == "Ready Contract"


def test_extract_document_facts_invalid_payload_marks_failure(
    db_session,
    session_factory,
    test_user,
    monkeypatch,
    tmp_path,
):
    document = crud_document.create_document(
        db_session,
        title="Invalid Contract",
        file_path=str(tmp_path / "invalid.pdf"),
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=256,
    )
    extraction_run = crud_document.create_extraction_run(
        db_session,
        document_id=document.id,
        extraction_version=1,
        status=ExtractionRunStatus.RUNNING,
    )
    extraction_run_id = extraction_run.id
    markdown_path = tmp_path / "invalid.md"
    markdown_path.write_text("# Contract", encoding="utf-8")

    monkeypatch.setattr("app.tasks.documents.SessionLocal", session_factory)

    def fail_extract(_markdown):
        raise FactExtractionValidationError("schema mismatch")

    monkeypatch.setattr("app.tasks.documents.extract_contract_facts_from_markdown", fail_extract)

    try:
        extract_document_facts.run(document.id, extraction_run_id, str(markdown_path))
    except FactExtractionValidationError:
        pass

    db_session.expire_all()
    refreshed_document = db_session.get(Document, document.id)
    refreshed_run = db_session.get(ExtractionRun, extraction_run_id)

    assert refreshed_document.processing_status == DocumentProcessingStatus.FAILED
    assert refreshed_document.last_error == "schema mismatch"
    assert refreshed_run.status == ExtractionRunStatus.FAILED
    assert refreshed_run.error_details["source"] == "llm_validation"


def test_extract_document_facts_task_exposes_rate_limit():
    assert extract_document_facts.rate_limit == settings.CELERY_EXTRACTION_RATE_LIMIT


def test_bulk_import_plan_splits_large_inputs_into_batches_of_fifty(tmp_path):
    file_paths = []
    for index in range(120):
        file_path = tmp_path / f"contract-{index:03d}.pdf"
        file_path.write_bytes(b"%PDF-1.4")
        file_paths.append(file_path)

    upload_plan = build_upload_plan(file_paths, batch_size=50, batch_prefix="archive")
    batch_ids = {request.batch_id for request in upload_plan}

    assert len(upload_plan) == 120
    assert len(batch_ids) == 3
    assert sum(1 for request in upload_plan if request.batch_id == "archive-001-of-003") == 50
    assert sum(1 for request in upload_plan if request.batch_id == "archive-002-of-003") == 50
    assert sum(1 for request in upload_plan if request.batch_id == "archive-003-of-003") == 20


def test_bulk_importer_uploads_one_file_per_request_and_propagates_batch_metadata(tmp_path):
    from app.services.bulk_ingestion import run_bulk_import

    pdf_paths = []
    for index in range(3):
        file_path = tmp_path / f"batch-{index:02d}.pdf"
        file_path.write_bytes(b"%PDF-1.4")
        pdf_paths.append(file_path)

    captured_requests = []

    class FakeUploader:
        def upload(self, request):
            captured_requests.append(request)
            return {"document_id": len(captured_requests)}

    results = run_bulk_import(
        tmp_path,
        uploader=FakeUploader(),
        batch_size=2,
        batch_prefix="quarterly",
        trusted_import=True,
    )

    assert len(results) == 3
    assert [request.file_path.name for request in captured_requests] == [path.name for path in pdf_paths]
    assert captured_requests[0].batch_id == "quarterly-001-of-002"
    assert captured_requests[1].batch_id == "quarterly-001-of-002"
    assert captured_requests[2].batch_id == "quarterly-002-of-002"
    assert all(request.trusted_import is True for request in captured_requests)


def test_get_batch_status_returns_aggregated_counts(client, db_session, test_user):
    documents = [
        Document(
            title="Queued",
            file_path="/tmp/queued.pdf",
            owner_id=test_user.id,
            content_type="application/pdf",
            file_size_bytes=100,
            batch_id="batch-ops",
            ingestion_source=IngestionSource.BULK_IMPORT,
            queue_priority=QueuePriority.LOW,
            processing_status=DocumentProcessingStatus.QUEUED,
            review_status=DocumentReviewStatus.PENDING_REVIEW,
            indexing_status=DocumentIndexingStatus.NOT_INDEXED,
        ),
        Document(
            title="Parsing",
            file_path="/tmp/parsing.pdf",
            owner_id=test_user.id,
            content_type="application/pdf",
            file_size_bytes=100,
            batch_id="batch-ops",
            ingestion_source=IngestionSource.BULK_IMPORT,
            queue_priority=QueuePriority.LOW,
            processing_status=DocumentProcessingStatus.PARSING,
            review_status=DocumentReviewStatus.PENDING_REVIEW,
            indexing_status=DocumentIndexingStatus.NOT_INDEXED,
        ),
        Document(
            title="Ready",
            file_path="/tmp/ready.pdf",
            owner_id=test_user.id,
            content_type="application/pdf",
            file_size_bytes=100,
            batch_id="batch-ops",
            ingestion_source=IngestionSource.BULK_IMPORT,
            queue_priority=QueuePriority.LOW,
            processing_status=DocumentProcessingStatus.FACTS_READY,
            review_status=DocumentReviewStatus.PENDING_REVIEW,
            indexing_status=DocumentIndexingStatus.NOT_INDEXED,
        ),
        Document(
            title="Failed",
            file_path="/tmp/failed.pdf",
            owner_id=test_user.id,
            content_type="application/pdf",
            file_size_bytes=100,
            batch_id="batch-ops",
            ingestion_source=IngestionSource.BULK_IMPORT,
            queue_priority=QueuePriority.LOW,
            processing_status=DocumentProcessingStatus.FAILED,
            review_status=DocumentReviewStatus.PENDING_REVIEW,
            indexing_status=DocumentIndexingStatus.NOT_INDEXED,
        ),
        Document(
            title="Approved",
            file_path="/tmp/approved.pdf",
            owner_id=test_user.id,
            content_type="application/pdf",
            file_size_bytes=100,
            batch_id="batch-ops",
            ingestion_source=IngestionSource.BULK_IMPORT,
            queue_priority=QueuePriority.LOW,
            processing_status=DocumentProcessingStatus.FACTS_READY,
            review_status=DocumentReviewStatus.APPROVED,
            indexing_status=DocumentIndexingStatus.INDEXED,
        ),
    ]
    db_session.add_all(documents)
    db_session.commit()

    response = client.get("/api/v1/batches/batch-ops")

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"] == "batch-ops"
    assert payload["total_documents"] == 5
    assert payload["aggregate_counts"] == {
        "queued": 1,
        "parsing": 1,
        "ready_for_review": 1,
        "failed": 1,
        "approved": 1,
        "indexed": 1,
    }
