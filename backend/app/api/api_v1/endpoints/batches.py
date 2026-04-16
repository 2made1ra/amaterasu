from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import crud_document
from app.models.document import DocumentProcessingStatus, DocumentReviewStatus
from app.schemas.batch import BatchAggregateCounts, BatchStatusResponse


router = APIRouter()


@router.get("/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(
    batch_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    owner_id = None if getattr(current_user, "is_admin", False) else current_user.id
    documents = crud_document.get_documents_by_batch_id(db, batch_id, owner_id=owner_id)
    if not documents:
        raise HTTPException(status_code=404, detail="Batch not found")

    processing_counts = Counter(document.processing_status.value for document in documents)
    review_counts = Counter(document.review_status.value for document in documents)
    indexing_counts = Counter(document.indexing_status.value for document in documents)

    aggregate_counts = BatchAggregateCounts(
        queued=processing_counts.get(DocumentProcessingStatus.QUEUED.value, 0),
        parsing=processing_counts.get(DocumentProcessingStatus.PARSING.value, 0),
        ready_for_review=sum(
            1
            for document in documents
            if document.processing_status == DocumentProcessingStatus.FACTS_READY
            and document.review_status == DocumentReviewStatus.PENDING_REVIEW
        ),
        failed=sum(
            1
            for document in documents
            if document.processing_status == DocumentProcessingStatus.FAILED
            or document.indexing_status.value == "FAILED"
        ),
        approved=review_counts.get(DocumentReviewStatus.APPROVED.value, 0),
        indexed=indexing_counts.get("INDEXED", 0),
    )

    return BatchStatusResponse(
        batch_id=batch_id,
        total_documents=len(documents),
        processing_status_counts=dict(processing_counts),
        review_status_counts=dict(review_counts),
        indexing_status_counts=dict(indexing_counts),
        aggregate_counts=aggregate_counts,
    )
