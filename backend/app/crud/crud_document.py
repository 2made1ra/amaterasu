import logging
from datetime import datetime

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


def get_active_contract_facts(db: Session, document_id: int):
    document = get_document(db, document_id)
    if not document:
        return None

    query = db.query(ContractFact).filter(ContractFact.document_id == document_id)
    if document.active_extraction_version is not None:
        query = query.filter(ContractFact.extraction_version == document.active_extraction_version)
    return query.order_by(ContractFact.extraction_version.desc()).first()
