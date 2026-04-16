import logging
from pathlib import Path

from app.celery_app import celery_app
from app.core.config import settings
from app.crud import crud_document
from app.db.session import SessionLocal
from app.models.document import (
    DocumentApprovalSource,
    DocumentIndexingStatus,
    DocumentProcessingStatus,
    DocumentReviewStatus,
    IngestionSource,
)
from app.models.extraction_run import ExtractionRunStatus
from app.services.document_indexing import (
    DocumentIndexingError,
    generate_document_summary,
    split_markdown_into_chunks,
)
from app.services.document_parser import (
    DocumentParsingError,
    parse_pdf_to_markdown,
    read_parsing_metadata,
    resolve_markdown_artifact_path,
)
from app.services.fact_extraction import (
    FactExtractionError,
    FactExtractionValidationError,
    CURRENT_CONTRACT_FACTS_SCHEMA_VERSION,
    extract_contract_facts_from_markdown,
    has_complete_required_facts,
    is_contract_facts_indexable,
    prepare_contract_facts_payload,
    validate_contract_facts_payload,
)
from app.services.qdrant_index import QdrantIndexError, get_contract_vector_index
from app.tasks.base import LoggedTask


logger = logging.getLogger(__name__)


def select_document_queue(ingestion_source, queue_priority) -> str:
    queue_priority_value = getattr(queue_priority, "value", queue_priority)
    ingestion_source_value = getattr(ingestion_source, "value", ingestion_source)

    if queue_priority_value == "LOW" or ingestion_source_value == "BULK_IMPORT":
        return settings.CELERY_BULK_QUEUE
    return settings.CELERY_HIGH_PRIORITY_QUEUE


def enqueue_index_document(document):
    queue_name = select_document_queue(document.ingestion_source, document.queue_priority)
    try:
        async_result = index_document.apply_async(args=[document.id], queue=queue_name)
    except Exception as exc:  # pragma: no cover - broker availability depends on environment
        logger.exception(
            "document_indexing_enqueue_failed document_id=%s queue=%s error=%s",
            document.id,
            queue_name,
            exc,
        )
        return None

    logger.info(
        "document_indexing_enqueued document_id=%s queue=%s task_id=%s",
        document.id,
        queue_name,
        async_result.id,
    )
    return async_result


@celery_app.task(name="app.tasks.documents.process_document", bind=True, base=LoggedTask)
def process_document(self, document_id: int):
    db = SessionLocal()
    extraction_run = None
    try:
        logger.info(
            "document_processing_task_started task_id=%s document_id=%s",
            self.request.id,
            document_id,
        )
        document = crud_document.get_document(db, document_id)
        if not document:
            logger.warning("document_processing_task_missing_document task_id=%s document_id=%s", self.request.id, document_id)
            return None

        extraction_version = crud_document.get_next_extraction_version(db, document.id)
        extraction_run = crud_document.create_extraction_run(
            db,
            document_id=document.id,
            extraction_version=extraction_version,
            status=ExtractionRunStatus.RUNNING,
        )
        crud_document.update_document_processing_status(db, document.id, "PARSING")

        parsed_document = parse_pdf_to_markdown(document.file_path)
        queue_name = select_document_queue(document.ingestion_source, document.queue_priority)
        async_result = extract_document_facts.apply_async(
            args=[document.id, extraction_run.id, parsed_document.artifact_path, parsed_document.metadata_path],
            queue=queue_name,
        )
        logger.info(
            "document_processing_enqueued_fact_extraction document_id=%s extraction_run_id=%s queue=%s task_id=%s markdown_path=%s",
            document.id,
            extraction_run.id,
            queue_name,
            async_result.id,
            parsed_document.artifact_path,
        )
        return {
            "document_id": document.id,
            "extraction_run_id": extraction_run.id,
            "markdown_path": parsed_document.artifact_path,
            "extract_task_id": async_result.id,
        }
    except DocumentParsingError as exc:
        logger.exception("document_processing_parser_error document_id=%s error=%s", document_id, exc)
        if extraction_run is None:
            extraction_version = crud_document.get_next_extraction_version(db, document_id)
            extraction_run = crud_document.create_extraction_run(
                db,
                document_id=document_id,
                extraction_version=extraction_version,
                status=ExtractionRunStatus.RUNNING,
            )
        crud_document.fail_extraction_run(
            db,
            extraction_run.id,
            error_details={"source": "pdf_parsing", "message": str(exc)},
        )
        crud_document.mark_document_processing_failed(db, document_id, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(
    name="app.tasks.documents.extract_document_facts",
    bind=True,
    base=LoggedTask,
    rate_limit=settings.CELERY_EXTRACTION_RATE_LIMIT,
)
def extract_document_facts(
    self,
    document_id: int,
    extraction_run_id: int,
    markdown_path: str,
    metadata_path: str | None = None,
):
    db = SessionLocal()
    try:
        logger.info(
            "document_fact_extraction_started task_id=%s document_id=%s extraction_run_id=%s markdown_path=%s",
            self.request.id,
            document_id,
            extraction_run_id,
            markdown_path,
        )
        markdown = Path(markdown_path).read_text(encoding="utf-8")
        parsing_metadata = read_parsing_metadata(metadata_path)
        if parsing_metadata is None:
            extracted_facts = extract_contract_facts_from_markdown(markdown)
        else:
            extracted_facts = extract_contract_facts_from_markdown(markdown, parsing_metadata=parsing_metadata)
        extracted_facts = prepare_contract_facts_payload(
            extracted_facts.model_dump(),
            parsing_metadata=parsing_metadata,
        )
        extraction_run = crud_document.get_extraction_run(db, extraction_run_id)
        if extraction_run is None:
            raise RuntimeError(f"Extraction run {extraction_run_id} not found")

        crud_document.upsert_contract_facts(
            db,
            document_id=document_id,
            extraction_version=extraction_run.extraction_version,
            schema_version=CURRENT_CONTRACT_FACTS_SCHEMA_VERSION,
            facts=extracted_facts.model_dump(),
        )
        crud_document.complete_extraction_run(db, extraction_run.id)
        document = crud_document.mark_document_facts_ready(
            db,
            document_id,
            extraction_run.extraction_version,
        )
        extracted_facts_payload = extracted_facts.model_dump()
        missing_required_fields = getattr(
            extracted_facts,
            "missing_required_fields",
            extracted_facts_payload.get("missing_required_fields", []),
        )

        if (
            document is not None
            and document.review_status == DocumentReviewStatus.PENDING_REVIEW
            and document.trusted_import
            and document.ingestion_source == IngestionSource.BULK_IMPORT
            and has_complete_required_facts(extracted_facts_payload)
        ):
            approved_document = crud_document.approve_document(
                db,
                document_id=document.id,
                approval_source=DocumentApprovalSource.TRUSTED_IMPORT,
                approved_by_user_id=None,
            )
            async_result = enqueue_index_document(approved_document)
            if async_result is not None:
                crud_document.update_document_indexing_status(
                    db,
                    approved_document.id,
                    DocumentIndexingStatus.QUEUED,
                )
            logger.info(
                "document_auto_approved_from_trusted_import document_id=%s extraction_run_id=%s",
                document.id,
                extraction_run_id,
            )
        elif document is not None and missing_required_fields:
            logger.info(
                "document_fact_extraction_missing_required_fields document_id=%s extraction_run_id=%s missing=%s",
                document.id,
                extraction_run_id,
                ",".join(missing_required_fields),
            )
        logger.info(
            "document_fact_extraction_completed task_id=%s document_id=%s extraction_run_id=%s",
            self.request.id,
            document_id,
            extraction_run_id,
        )
        return {
            "document_id": document_id,
            "extraction_run_id": extraction_run_id,
            "processing_status": "FACTS_READY",
        }
    except FactExtractionValidationError as exc:
        logger.exception("document_fact_extraction_validation_error document_id=%s error=%s", document_id, exc)
        crud_document.fail_extraction_run(
            db,
            extraction_run_id,
            error_details={"source": "llm_validation", "message": str(exc)},
        )
        crud_document.mark_document_processing_failed(db, document_id, str(exc))
        raise
    except FactExtractionError as exc:
        logger.exception("document_fact_extraction_provider_error document_id=%s error=%s", document_id, exc)
        crud_document.fail_extraction_run(
            db,
            extraction_run_id,
            error_details={"source": "llm_provider", "message": str(exc)},
        )
        crud_document.mark_document_processing_failed(db, document_id, str(exc))
        raise
    except Exception as exc:
        logger.exception("document_fact_extraction_unexpected_error document_id=%s error=%s", document_id, exc)
        crud_document.fail_extraction_run(
            db,
            extraction_run_id,
            error_details={"source": "runtime", "message": str(exc)},
        )
        crud_document.mark_document_processing_failed(db, document_id, str(exc))
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.documents.index_document", bind=True, base=LoggedTask)
def index_document(self, document_id: int):
    db = SessionLocal()
    try:
        logger.info("document_indexing_started task_id=%s document_id=%s", self.request.id, document_id)
        document = crud_document.get_document(db, document_id)
        if not document:
            logger.warning("document_indexing_missing_document task_id=%s document_id=%s", self.request.id, document_id)
            return None

        if document.review_status != DocumentReviewStatus.APPROVED or document.approval_source not in {
            DocumentApprovalSource.MANUAL,
            DocumentApprovalSource.TRUSTED_IMPORT,
        }:
            logger.info(
                "document_indexing_skipped_unapproved task_id=%s document_id=%s review_status=%s approval_source=%s",
                self.request.id,
                document_id,
                document.review_status.value,
                getattr(document.approval_source, "value", document.approval_source),
            )
            return {
                "document_id": document_id,
                "indexing_status": document.indexing_status.value,
                "skipped": True,
            }

        facts = crud_document.get_active_contract_facts(db, document.id)
        if facts is None:
            raise DocumentIndexingError("Document facts are missing for indexing")
        if not is_contract_facts_indexable(facts.facts):
            raise DocumentIndexingError("Document facts are incomplete or parser quality is too low for indexing")

        markdown_path = resolve_markdown_artifact_path(document.file_path)
        if not markdown_path.exists():
            raise DocumentIndexingError(f"Markdown artifact is missing: {markdown_path}")

        crud_document.update_document_indexing_status(db, document.id, DocumentIndexingStatus.INDEXING)
        markdown = markdown_path.read_text(encoding="utf-8")
        validated_facts = validate_contract_facts_payload(facts.facts)
        summary = validated_facts.summary or generate_document_summary(markdown, facts.facts)
        chunks = split_markdown_into_chunks(markdown)

        vector_index = get_contract_vector_index()
        vector_index.ensure_collections()
        vector_index.delete_document_vectors(document.id)
        vector_index.upsert_summary(document=document, summary=summary)
        vector_index.upsert_chunks(document=document, chunks=chunks)

        indexed_document = crud_document.update_document_indexing_status(
            db,
            document.id,
            DocumentIndexingStatus.INDEXED,
            last_error=None,
        )
        logger.info(
            "document_indexing_completed task_id=%s document_id=%s chunk_count=%s approval_source=%s",
            self.request.id,
            document.id,
            len(chunks),
            indexed_document.approval_source.value if indexed_document and indexed_document.approval_source else None,
        )
        return {
            "document_id": document.id,
            "indexing_status": DocumentIndexingStatus.INDEXED.value,
            "chunk_count": len(chunks),
        }
    except (DocumentIndexingError, QdrantIndexError) as exc:
        logger.exception("document_indexing_pipeline_error document_id=%s error=%s", document_id, exc)
        crud_document.mark_document_indexing_failed(db, document_id, str(exc))
        raise
    except Exception as exc:
        logger.exception("document_indexing_unexpected_error document_id=%s error=%s", document_id, exc)
        crud_document.mark_document_indexing_failed(db, document_id, str(exc))
        raise
    finally:
        db.close()
