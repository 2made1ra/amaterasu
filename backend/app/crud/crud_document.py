from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from datetime import datetime


def create_document(db: Session, title: str, file_path: str, owner_id: int):
    db_obj = Document(
        title=title,
        file_path=file_path,
        owner_id=owner_id,
        status=DocumentStatus.PENDING
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
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
    return db.query(Document).filter(Document.owner_id == owner_id).offset(skip).limit(limit).all()


def get_confirmed_documents_by_owner(db: Session, owner_id: int):
    return (
        db.query(Document)
        .filter(Document.owner_id == owner_id, Document.status == DocumentStatus.CONFIRMED)
        .order_by(Document.created_at.desc())
        .all()
    )


def confirm_document(db: Session, document_id: int, deadline: datetime = None):
    db_obj = get_document(db, document_id)
    if db_obj:
        if deadline:
            db_obj.extracted_deadline = deadline
        db_obj.status = DocumentStatus.CONFIRMED
        db.commit()
        db.refresh(db_obj)
    return db_obj
