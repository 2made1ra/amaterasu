from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.document import DocumentStatus

class DocumentBase(BaseModel):
    title: str

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    extracted_deadline: Optional[datetime] = None

class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    extracted_deadline: Optional[datetime]
    status: DocumentStatus
    created_at: datetime
    owner_id: int

    class Config:
        from_attributes = True

class ExtractedMetadata(BaseModel):
    deadline: Optional[datetime]
    summary: Optional[str]
    raw_text: str
