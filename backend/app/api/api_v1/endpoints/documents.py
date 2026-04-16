import logging
import os
import shutil
import uuid
from json import JSONDecodeError, loads
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.crud import crud_document
from app.models.document import (
    DocumentApprovalSource,
    DocumentIndexingStatus,
    DocumentProcessingStatus,
    DocumentReviewStatus,
    IngestionSource,
    QueuePriority,
)
from app.schemas.document import (
    ConfirmDocumentRequest,
    ContractChatRequest,
    ContractChatResponse,
    DocumentDetailResponse,
    DocumentResponse,
    UploadDocumentResponse,
)
from app.services import workspace
from app.tasks.documents import enqueue_index_document, process_document, select_document_queue


router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _resolve_upload_dir() -> Path:
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _validate_pdf_upload(file: UploadFile) -> int:
    content_type = (file.content_type or "").lower()
    filename = file.filename or ""
    if content_type not in ALLOWED_CONTENT_TYPES and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File is too large")

    return file_size


def _resolve_upload_metadata(
    ingestion_source: IngestionSource | None,
    queue_priority: QueuePriority | None,
    trusted_import: bool | None,
) -> tuple[IngestionSource, QueuePriority, bool]:
    resolved_ingestion_source = ingestion_source or IngestionSource.USER_UPLOAD
    if queue_priority is not None:
        resolved_queue_priority = queue_priority
    elif resolved_ingestion_source == IngestionSource.BULK_IMPORT:
        resolved_queue_priority = QueuePriority.LOW
    else:
        resolved_queue_priority = QueuePriority.HIGH
    return resolved_ingestion_source, resolved_queue_priority, bool(trusted_import)


def _dispatch_document_processing(document_id: int, ingestion_source: IngestionSource, queue_priority: QueuePriority):
    queue_name = select_document_queue(ingestion_source, queue_priority)
    try:
        async_result = process_document.apply_async(args=[document_id], queue=queue_name)
    except Exception as exc:  # pragma: no cover - broker availability depends on environment
        logger.exception(
            "document_processing_enqueue_failed document_id=%s queue=%s error=%s",
            document_id,
            queue_name,
            exc,
        )
        return None

    logger.info(
        "document_processing_enqueued document_id=%s queue=%s task_id=%s",
        document_id,
        queue_name,
        async_result.id,
    )
    return async_result


@router.post("/upload", response_model=UploadDocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    batch_id: str | None = Form(default=None),
    ingestion_source: IngestionSource | None = Form(default=None),
    queue_priority: QueuePriority | None = Form(default=None),
    trusted_import: bool | None = Form(default=None),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    file_size = _validate_pdf_upload(file)
    ingestion_source, queue_priority, trusted_import = _resolve_upload_metadata(
        ingestion_source,
        queue_priority,
        trusted_import,
    )

    safe_filename = f"{uuid.uuid4()}.pdf"
    file_path = _resolve_upload_dir() / safe_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = crud_document.create_document(
        db,
        title=file.filename or safe_filename,
        file_path=str(file_path),
        owner_id=current_user.id,
        content_type=file.content_type or "application/pdf",
        file_size_bytes=file_size,
        batch_id=batch_id,
        ingestion_source=ingestion_source,
        queue_priority=queue_priority,
        trusted_import=trusted_import,
    )

    _dispatch_document_processing(document.id, ingestion_source, queue_priority)

    return {
        "document_id": document.id,
        "review_status": document.review_status,
        "processing_status": document.processing_status,
        "queue_priority": document.queue_priority,
        "batch_id": document.batch_id,
        "trusted_import": document.trusted_import,
        "message": "Document uploaded and queued for asynchronous processing.",
    }


@router.post("/{document_id}/confirm", response_model=DocumentResponse)
async def confirm_document(
    document_id: int,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    document = crud_document.get_document_for_owner(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processing_status != DocumentProcessingStatus.FACTS_READY:
        raise HTTPException(status_code=409, detail="Document facts are not ready for review")

    if document.review_status != DocumentReviewStatus.PENDING_REVIEW:
        raise HTTPException(status_code=409, detail="Document has already been reviewed")

    payload_facts = None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        payload = ConfirmDocumentRequest.model_validate(body or {})
        payload_facts = payload.facts
    else:
        form = await request.form()
        legacy_deadline = form.get("deadline")
        facts_json = form.get("facts_json")
        if legacy_deadline:
            logger.info("Ignoring legacy deadline confirmation payload for document %s during phase 3", document_id)
        if facts_json:
            try:
                payload_facts = loads(facts_json)
            except JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail="facts_json must contain valid JSON") from exc

    active_facts = crud_document.get_active_contract_facts(db, document.id)
    if active_facts is None:
        raise HTTPException(status_code=409, detail="Document facts are not available for confirmation")

    if payload_facts is not None:
        crud_document.upsert_contract_facts(
            db,
            document_id=document.id,
            extraction_version=active_facts.extraction_version,
            schema_version=active_facts.schema_version,
            facts=payload_facts,
        )

    approved_document = crud_document.approve_document(
        db,
        document_id=document.id,
        approval_source=DocumentApprovalSource.MANUAL,
        approved_by_user_id=current_user.id,
    )
    async_result = enqueue_index_document(approved_document)
    if async_result is not None:
        approved_document = crud_document.update_document_indexing_status(
            db,
            approved_document.id,
            DocumentIndexingStatus.QUEUED,
        )
    return approved_document


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    return crud_document.get_documents_by_owner(db, current_user.id, skip, limit)


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_status(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    document = crud_document.get_document_for_owner(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    facts = crud_document.get_active_contract_facts(db, document.id)
    payload = DocumentResponse.model_validate(document).model_dump()
    payload["facts"] = None
    if facts is not None:
        payload["facts"] = {
            "extraction_version": facts.extraction_version,
            "schema_version": facts.schema_version,
            "facts": facts.facts,
            "created_at": facts.created_at,
        }
    return payload


@router.get("/{document_id}/preview")
def preview_document(
    document_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    document = crud_document.get_document_for_owner(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file is missing")
    return FileResponse(document.file_path, media_type="application/pdf", filename=document.title)


@router.post("/{document_id}/chat", response_model=ContractChatResponse)
def chat_about_document(
    document_id: int,
    request: ContractChatRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    document = crud_document.get_document_for_owner(db, document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        answer = workspace.build_contract_chat_reply(db, current_user.id, document_id, query)
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"answer": answer}
