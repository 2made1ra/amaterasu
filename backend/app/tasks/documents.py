import logging
from pathlib import Path

from app.celery_app import celery_app
from app.core.config import settings
from app.crud import crud_document
from app.db.session import SessionLocal
from app.models.extraction_run import ExtractionRunStatus
from app.services.document_parser import DocumentParsingError, parse_pdf_to_markdown
from app.services.fact_extraction import (
    FactExtractionError,
    FactExtractionValidationError,
    extract_contract_facts_from_markdown,
)
from app.tasks.base import LoggedTask


logger = logging.getLogger(__name__)


def select_document_queue(ingestion_source, queue_priority) -> str:
    queue_priority_value = getattr(queue_priority, "value", queue_priority)
    ingestion_source_value = getattr(ingestion_source, "value", ingestion_source)

    if queue_priority_value == "LOW" or ingestion_source_value == "BULK_IMPORT":
        return settings.CELERY_BULK_QUEUE
    return settings.CELERY_HIGH_PRIORITY_QUEUE


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
            args=[document.id, extraction_run.id, parsed_document.artifact_path],
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
def extract_document_facts(self, document_id: int, extraction_run_id: int, markdown_path: str):
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
        extracted_facts = extract_contract_facts_from_markdown(markdown)
        extraction_run = crud_document.get_extraction_run(db, extraction_run_id)
        if extraction_run is None:
            raise RuntimeError(f"Extraction run {extraction_run_id} not found")

        crud_document.upsert_contract_facts(
            db,
            document_id=document_id,
            extraction_version=extraction_run.extraction_version,
            schema_version=1,
            facts=extracted_facts.model_dump(),
        )
        crud_document.complete_extraction_run(db, extraction_run.id)
        crud_document.mark_document_facts_ready(
            db,
            document_id,
            extraction_run.extraction_version,
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
