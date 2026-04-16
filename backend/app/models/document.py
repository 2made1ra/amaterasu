import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class DocumentReviewStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentProcessingStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PARSING = "PARSING"
    FACTS_READY = "FACTS_READY"
    FAILED = "FAILED"


class DocumentIndexingStatus(str, enum.Enum):
    NOT_INDEXED = "NOT_INDEXED"
    QUEUED = "QUEUED"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class IngestionSource(str, enum.Enum):
    USER_UPLOAD = "USER_UPLOAD"
    BULK_IMPORT = "BULK_IMPORT"
    SERVICE_IMPORT = "SERVICE_IMPORT"


class QueuePriority(str, enum.Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False, default="application/pdf")
    file_size_bytes = Column(Integer, nullable=False)
    review_status = Column(
        Enum(DocumentReviewStatus, native_enum=False),
        nullable=False,
        default=DocumentReviewStatus.PENDING_REVIEW,
    )
    processing_status = Column(
        Enum(DocumentProcessingStatus, native_enum=False),
        nullable=False,
        default=DocumentProcessingStatus.QUEUED,
    )
    indexing_status = Column(
        Enum(DocumentIndexingStatus, native_enum=False),
        nullable=False,
        default=DocumentIndexingStatus.NOT_INDEXED,
    )
    active_extraction_version = Column(Integer, nullable=True)
    last_error = Column(String, nullable=True)
    batch_id = Column(String, nullable=True, index=True)
    ingestion_source = Column(Enum(IngestionSource, native_enum=False), nullable=True)
    queue_priority = Column(Enum(QueuePriority, native_enum=False), nullable=True)
    trusted_import = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    owner = relationship("User")
    contract_facts = relationship(
        "ContractFact",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(ContractFact.extraction_version)",
    )
    extraction_runs = relationship(
        "ExtractionRun",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="desc(ExtractionRun.created_at)",
    )

    @property
    def status(self) -> str:
        if self.review_status == DocumentReviewStatus.APPROVED:
            return "CONFIRMED"
        return self.review_status.value

    @property
    def extracted_deadline(self):
        return None
