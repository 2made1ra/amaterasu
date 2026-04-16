from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.document import (
    DocumentIndexingStatus,
    DocumentProcessingStatus,
    DocumentReviewStatus,
    IngestionSource,
    QueuePriority,
)


class DocumentBase(BaseModel):
    title: str


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    model_config = ConfigDict(extra="forbid")


class ContractFactResponse(BaseModel):
    extraction_version: int
    schema_version: int
    facts: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    content_type: str
    file_size_bytes: int
    status: str
    extracted_deadline: Optional[datetime] = None
    review_status: DocumentReviewStatus
    processing_status: DocumentProcessingStatus
    indexing_status: DocumentIndexingStatus
    active_extraction_version: Optional[int]
    last_error: Optional[str]
    batch_id: Optional[str]
    ingestion_source: Optional[IngestionSource]
    queue_priority: Optional[QueuePriority]
    trusted_import: Optional[bool]
    created_at: datetime
    updated_at: datetime
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    facts: Optional[ContractFactResponse] = None


class UploadDocumentResponse(BaseModel):
    document_id: int
    review_status: DocumentReviewStatus
    processing_status: DocumentProcessingStatus
    queue_priority: Optional[QueuePriority] = None
    batch_id: Optional[str] = None
    trusted_import: Optional[bool] = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class ContractChatRequest(BaseModel):
    query: str


class ContractChatResponse(BaseModel):
    answer: str
