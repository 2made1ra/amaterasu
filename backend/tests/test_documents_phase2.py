import importlib
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
from app.services.fact_extraction import (
    FactExtractionValidationError,
    has_complete_required_facts,
    is_contract_facts_indexable,
    prepare_contract_facts_payload,
    validate_contract_facts_payload,
)
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


def test_worker_import_bootstraps_models_for_document_queries(db_session, test_user):
    importlib.import_module("app.worker")

    document = crud_document.create_document(
        db_session,
        title="Worker bootstrap contract",
        file_path="/tmp/worker-bootstrap.pdf",
        owner_id=test_user.id,
        content_type="application/pdf",
        file_size_bytes=64,
        ingestion_source=IngestionSource.USER_UPLOAD,
        queue_priority=QueuePriority.HIGH,
        trusted_import=False,
    )

    fetched_document = crud_document.get_document(db_session, document.id)

    assert fetched_document is not None
    assert fetched_document.id == document.id
    assert fetched_document.owner_id == test_user.id


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
        lambda file_path: SimpleNamespace(
            markdown="# Contract",
            artifact_path=str(tmp_path / "contract.md"),
            metadata_path=str(tmp_path / "contract.parse.json"),
        ),
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
    assert captured["args"][3].endswith("contract.parse.json")


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
        lambda markdown, **kwargs: SimpleNamespace(
            model_dump=lambda: {
                "company_name": "Acme LLC",
                "signatory_name": "Ivan Petrov",
                "contact_phone": "+7 999 123-45-67",
                "service_price": "150000 RUB",
                "service_subject": "Logistics support",
                "service_completion_date": "2026-05-20",
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
    assert stored_facts.schema_version == 3
    assert stored_facts.facts["company_name"] == "Acme LLC"
    assert stored_facts.facts["signatory_name"] == "Ivan Petrov"
    assert stored_facts.facts["contact_phone"] == "+7 999 123-45-67"
    assert stored_facts.facts["service_price"] == "150000 RUB"
    assert stored_facts.facts["service_subject"] == "Logistics support"
    assert stored_facts.facts["service_completion_date"] == "2026-05-20"
    assert stored_facts.facts["missing_required_fields"] == []
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

    def fail_extract(_markdown, **kwargs):
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


def test_extract_document_facts_requires_prd_required_fields():
    try:
        validate_contract_facts_payload(
            {
                "company_name": "Acme LLC",
                "signatory_name": "Ivan Petrov",
                "contact_phone": "+7 999 123-45-67",
                "service_price": "150000 RUB",
                "service_subject": "Logistics support",
            }
        )
    except FactExtractionValidationError:
        pass
    else:
        raise AssertionError("Expected validation error for missing service_completion_date")


def test_extract_document_facts_validation_accepts_required_prd_fields():
    facts = validate_contract_facts_payload(
        {
            "company_name": "Acme LLC",
            "signatory_name": "Ivan Petrov",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
        }
    )

    assert facts.company_name == "Acme LLC"
    assert facts.service_completion_date == "2026-05-20"


def test_prepare_contract_facts_payload_preserves_document_kind_and_missing_required_fields():
    facts = prepare_contract_facts_payload(
        {
            "document_kind": "supplier_order",
            "company_name": "Acme LLC",
            "signatory_name": None,
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
        },
        parsing_metadata={"quality_label": "medium", "quality_score": 0.55, "extraction_method": "ocr"},
    )

    assert facts.document_kind == "supplier_order"
    assert facts.missing_required_fields == ["signatory_name"]
    assert facts.parsing_method == "ocr"
    assert facts.parser_quality == "medium"


def test_prepare_contract_facts_payload_backfills_sparse_required_fields_from_title_and_markdown():
    facts = prepare_contract_facts_payload(
        {
            "service_subject": "Provision of services or scope of work defined by numbered articles.",
            "effective_date": "12.11.2024",
        },
        parsing_metadata={"quality_label": "high", "quality_score": 0.93, "extraction_method": "ocr"},
        markdown=(
            "2.1.1leHaorOBOpa coCTaB19eT 6O00O(HeIleC1 TIC)py6en\n"
            "3.2.CpoKoKa3ycT:12.112024no16.11.2024\n"
            "Director\n"
            "AHTOCHKOn A.B\n"
        ),
        document_title="Единый_оператор_мероприятий_Арбузов_Роман_Игоревич_договор.pdf",
    )

    assert facts.company_name == "Единый оператор мероприятий"
    assert facts.signatory_name == "Арбузов Роман Игоревич"
    assert facts.service_price == "60000 RUB"
    assert facts.service_completion_date == "2024-11-16"
    assert facts.document_title == "Единый оператор мероприятий Арбузов Роман Игоревич"
    assert facts.missing_required_fields == ["contact_phone"]


def test_prepare_contract_facts_payload_sanitizes_null_and_non_string_list_items():
    facts = prepare_contract_facts_payload(
        {
            "company_name": "Acme LLC",
            "signatory_name": "Ivan Petrov",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
            "source_hints": {
                "company_name": None,
                "service_price": {"page_number": "2", "snippet": "  150000 RUB  "},
                "service_subject": "Scope listed in section 2",
            },
            "parties": [None, "Acme LLC", 123, "  Globex  "],
            "obligations": [None, "Deliver by 2026-05-20", {"invalid": True}],
            "risks": [None, "Penalty for late delivery"],
        }
    )

    assert "company_name" not in facts.source_hints
    assert facts.source_hints["service_price"].page_number == 2
    assert facts.source_hints["service_price"].snippet == "150000 RUB"
    assert facts.source_hints["service_subject"].snippet == "Scope listed in section 2"
    assert facts.parties == ["Acme LLC", "Globex"]
    assert facts.obligations == ["Deliver by 2026-05-20"]
    assert facts.risks == ["Penalty for late delivery"]


def test_has_complete_required_facts_requires_all_mandatory_business_fields():
    assert has_complete_required_facts(
        {
            "company_name": "Acme LLC",
            "signatory_name": "Ivan Petrov",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
        }
    )
    assert not has_complete_required_facts(
        {
            "company_name": "Acme LLC",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
        }
    )


def test_indexability_blocks_low_quality_or_incomplete_facts():
    assert is_contract_facts_indexable(
        {
            "company_name": "Acme LLC",
            "signatory_name": "Ivan Petrov",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
            "parser_quality": "medium",
            "parser_quality_score": 0.66,
        }
    )
    assert not is_contract_facts_indexable(
        {
            "company_name": "Acme LLC",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
            "parser_quality": "medium",
            "parser_quality_score": 0.66,
        }
    )
    assert not is_contract_facts_indexable(
        {
            "company_name": "Acme LLC",
            "signatory_name": "Ivan Petrov",
            "contact_phone": "+7 999 123-45-67",
            "service_price": "150000 RUB",
            "service_subject": "Logistics support",
            "service_completion_date": "2026-05-20",
            "parser_quality": "low",
            "parser_quality_score": 0.21,
        }
    )


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
