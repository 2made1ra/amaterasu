from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import crud_document
from app.schemas.document import DocumentResponse, ExtractedMetadata
from app.services import rag
import os
import shutil
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=dict)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Step 1: Upload PDF, parse, and extract metadata (Human-in-the-Loop start).
    Returns temporary document id and extracted metadata.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Sanitize filename by generating a UUID
    safe_filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create pending document in DB
    doc = crud_document.create_document(db, title=file.filename, file_path=file_path, owner_id=current_user.id)

    # Process PDF and extract metadata
    docs = rag.process_pdf(file_path)
    full_text = " ".join([d.page_content for d in docs])
    metadata = rag.extract_metadata_from_text(full_text)

    # Parse mock date string into datetime object
    try:
        deadline = datetime.strptime(metadata.get("deadline"), "%Y-%m-%d")
    except:
        deadline = None

    return {
        "document_id": doc.id,
        "extracted_deadline": deadline,
        "message": "Please review and confirm the extracted deadline."
    }

@router.post("/{document_id}/confirm", response_model=DocumentResponse)
def confirm_document(
    document_id: int,
    deadline: datetime = Form(None),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Step 2: Confirm metadata, save to vector store.
    """
    doc = crud_document.get_document(db, document_id)
    if not doc or doc.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Update DB status
    doc = crud_document.confirm_document(db, document_id, deadline)

    # Vectorize and save to Qdrant
    docs = rag.process_pdf(doc.file_path)
    rag.save_to_vectorstore(docs, doc.id, doc.owner_id)

    return doc

@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    return crud_document.get_documents_by_owner(db, current_user.id, skip, limit)
