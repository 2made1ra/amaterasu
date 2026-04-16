from pydantic import BaseModel


class BatchAggregateCounts(BaseModel):
    queued: int
    parsing: int
    ready_for_review: int
    failed: int
    approved: int
    indexed: int


class BatchStatusResponse(BaseModel):
    batch_id: str
    total_documents: int
    processing_status_counts: dict[str, int]
    review_status_counts: dict[str, int]
    indexing_status_counts: dict[str, int]
    aggregate_counts: BatchAggregateCounts
