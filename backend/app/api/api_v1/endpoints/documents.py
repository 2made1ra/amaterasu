import logging
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.crud import crud_document
from app.models.document import IngestionSource, QueuePriority
from app.schemas.document import (
    ContractChatRequest,
    ContractChatResponse,
    DocumentDetailResponse,
    DocumentResponse,
    UploadDocumentResponse,
)
from app.services import workspace


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


def _dispatch_document_processing(document_id: int, queue_priority: QueuePriority | None) -> None:
    logger.info(
        "document_processing_placeholder_queued document_id=%s queue_priority=%s",
        document_id,
        queue_priority.value if queue_priority else None,
    )
    pass


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

    _dispatch_document_processing(document.id, queue_priority)

    return {
        "document_id": document.id,
        "review_status": document.review_status,
        "processing_status": document.processing_status,
        "batch_id": document.batch_id,
        "trusted_import": document.trusted_import,
        "message": "Document uploaded and queued for asynchronous processing.",
    }


@router.post("/{document_id}/confirm", response_model=DocumentResponse)
def confirm_document(
    document_id: int,
    deadline: str | None = Form(None),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    doc = crud_document.get_document(db, document_id)
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    if deadline:
        logger.info("Ignoring legacy deadline confirmation payload for document %s during phase 1", document_id)

    doc = crud_document.confirm_document(db, document_id, None)
    return doc


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
