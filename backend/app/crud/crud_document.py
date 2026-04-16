import logging
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

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


logger = logging.getLogger(__name__)


def _log_status_transition(document_id: int, field: str, previous, current) -> None:
    if previous == current:
        return

    logger.info(
        "document_status_transition document_id=%s field=%s from=%s to=%s",
        document_id,
        field,
        previous,
        current,
    )


def create_document(
    db: Session,
    *,
    title: str,
    file_path: str,
    owner_id: int,
    content_type: str,
    file_size_bytes: int,
    batch_id: str | None = None,
    ingestion_source: IngestionSource | None = None,
    queue_priority: QueuePriority | None = None,
    trusted_import: bool | None = None,
):
    db_obj = Document(
        title=title,
        file_path=file_path,
        owner_id=owner_id,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        review_status=DocumentReviewStatus.PENDING_REVIEW,
        processing_status=DocumentProcessingStatus.QUEUED,
        indexing_status=DocumentIndexingStatus.NOT_INDEXED,
        batch_id=batch_id,
        ingestion_source=ingestion_source,
        queue_priority=queue_priority,
        trusted_import=trusted_import,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    _log_status_transition(db_obj.id, "review_status", None, db_obj.review_status.value)
    _log_status_transition(db_obj.id, "processing_status", None, db_obj.processing_status.value)
    _log_status_transition(db_obj.id, "indexing_status", None, db_obj.indexing_status.value)
    return db_obj


def update_document_processing_status(
    db: Session,
    document_id: int,
    processing_status: DocumentProcessingStatus | str,
    *,
    last_error: str | None = None,
):
    db_obj = get_document(db, document_id)
    if not db_obj:
        return None

    next_status = (
        processing_status
        if isinstance(processing_status, DocumentProcessingStatus)
        else DocumentProcessingStatus(processing_status)
    )
    previous_status = db_obj.processing_status.value
    db_obj.processing_status = next_status
    db_obj.last_error = last_error
    db.commit()
    db.refresh(db_obj)
    _log_status_transition(db_obj.id, "processing_status", previous_status, db_obj.processing_status.value)
    return db_obj


def mark_document_processing_failed(db: Session, document_id: int, error_message: str):
    return update_document_processing_status(
        db,
        document_id,
        DocumentProcessingStatus.FAILED,
        last_error=error_message,
    )


def mark_document_facts_ready(db: Session, document_id: int, extraction_version: int):
    db_obj = get_document(db, document_id)
    if not db_obj:
        return None

    previous_status = db_obj.processing_status.value
    db_obj.processing_status = DocumentProcessingStatus.FACTS_READY
    db_obj.active_extraction_version = extraction_version
    db_obj.last_error = None
    db.commit()
    db.refresh(db_obj)
    _log_status_transition(db_obj.id, "processing_status", previous_status, db_obj.processing_status.value)
    return db_obj


def get_document(db: Session, document_id: int):
    return db.query(Document).filter(Document.id == document_id).first()


def get_document_for_owner(db: Session, document_id: int, owner_id: int):
    return (
        db.query(Document)
        .filter(Document.id == document_id, Document.owner_id == owner_id)
        .first()
    )


def get_documents_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Document)
        .filter(Document.owner_id == owner_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_confirmed_documents_by_owner(db: Session, owner_id: int):
    return (
        db.query(Document)
        .filter(Document.owner_id == owner_id, Document.review_status == DocumentReviewStatus.APPROVED)
        .order_by(Document.created_at.desc())
        .all()
    )


def confirm_document(db: Session, document_id: int, deadline: datetime = None):
    db_obj = get_document(db, document_id)
    if db_obj:
        previous_review_status = db_obj.review_status.value
        db_obj.review_status = DocumentReviewStatus.APPROVED
        db.commit()
        db.refresh(db_obj)
        _log_status_transition(db_obj.id, "review_status", previous_review_status, db_obj.review_status.value)
    return db_obj


def get_next_extraction_version(db: Session, document_id: int) -> int:
    current_max = (
        db.query(func.max(ExtractionRun.extraction_version))
        .filter(ExtractionRun.document_id == document_id)
        .scalar()
    )
    return (current_max or 0) + 1


def create_extraction_run(
    db: Session,
    *,
    document_id: int,
    extraction_version: int,
    status: ExtractionRunStatus = ExtractionRunStatus.QUEUED,
):
    db_obj = ExtractionRun(
        document_id=document_id,
        extraction_version=extraction_version,
        status=status,
        started_at=datetime.now(timezone.utc) if status == ExtractionRunStatus.RUNNING else None,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    logger.info(
        "extraction_run_created document_id=%s extraction_run_id=%s extraction_version=%s status=%s",
        document_id,
        db_obj.id,
        extraction_version,
        db_obj.status.value,
    )
    return db_obj


def get_extraction_run(db: Session, extraction_run_id: int):
    return db.query(ExtractionRun).filter(ExtractionRun.id == extraction_run_id).first()


def complete_extraction_run(db: Session, extraction_run_id: int):
    db_obj = get_extraction_run(db, extraction_run_id)
    if not db_obj:
        return None

    db_obj.status = ExtractionRunStatus.SUCCEEDED
    db_obj.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    logger.info(
        "extraction_run_succeeded extraction_run_id=%s document_id=%s",
        db_obj.id,
        db_obj.document_id,
    )
    return db_obj


def fail_extraction_run(db: Session, extraction_run_id: int, *, error_details: dict):
    db_obj = get_extraction_run(db, extraction_run_id)
    if not db_obj:
        return None

    db_obj.status = ExtractionRunStatus.FAILED
    db_obj.error_details = error_details
    db_obj.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    logger.error(
        "extraction_run_failed extraction_run_id=%s document_id=%s error_source=%s",
        db_obj.id,
        db_obj.document_id,
        error_details.get("source"),
    )
    return db_obj


def upsert_contract_facts(
    db: Session,
    *,
    document_id: int,
    extraction_version: int,
    schema_version: int,
    facts: dict,
):
    db_obj = (
        db.query(ContractFact)
        .filter(
            ContractFact.document_id == document_id,
            ContractFact.extraction_version == extraction_version,
        )
        .first()
    )

    if db_obj is None:
        db_obj = ContractFact(
            document_id=document_id,
            extraction_version=extraction_version,
            schema_version=schema_version,
            facts=facts,
        )
        db.add(db_obj)
    else:
        db_obj.schema_version = schema_version
        db_obj.facts = facts

    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_active_contract_facts(db: Session, document_id: int):
    document = get_document(db, document_id)
    if not document:
        return None

    query = db.query(ContractFact).filter(ContractFact.document_id == document_id)
    if document.active_extraction_version is not None:
        query = query.filter(ContractFact.extraction_version == document.active_extraction_version)
    return query.order_by(ContractFact.extraction_version.desc()).first()


def get_documents_by_batch_id(db: Session, batch_id: str, owner_id: int | None = None):
    query = db.query(Document).filter(Document.batch_id == batch_id)
    if owner_id is not None:
        query = query.filter(Document.owner_id == owner_id)
    return query.order_by(Document.created_at.asc()).all()
