from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.contract_fact import ContractFact
from app.models.document import Document, DocumentReviewStatus
from app.services.query_router import QueryFilters


@dataclass(slots=True)
class SQLSearchMatch:
    document: Document
    facts: dict


def search_contract_facts(
    db: Session,
    *,
    owner_id: int,
    filters: QueryFilters,
) -> list[SQLSearchMatch]:
    if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
        return []

    query = (
        db.query(Document, ContractFact)
        .join(ContractFact, ContractFact.document_id == Document.id)
        .filter(
            Document.owner_id == owner_id,
            Document.review_status == DocumentReviewStatus.APPROVED,
            or_(
                Document.active_extraction_version.is_(None),
                ContractFact.extraction_version == Document.active_extraction_version,
            ),
        )
        .order_by(Document.created_at.desc(), ContractFact.extraction_version.desc())
    )

    if filters.document_ids:
        query = query.filter(Document.id.in_(filters.document_ids))

    if filters.supplier:
        supplier_value = filters.supplier.lower()
        supplier_fields = (
            ContractFact.facts["company_name"].as_string(),
            ContractFact.facts["supplier"].as_string(),
            ContractFact.facts["vendor"].as_string(),
            ContractFact.facts["counterparty"].as_string(),
            ContractFact.facts["document_title"].as_string(),
        )
        query = query.filter(
            or_(*[func.lower(func.coalesce(field, "")).like(f"%{supplier_value}%") for field in supplier_fields])
        )

    if filters.year is not None:
        year_prefix = f"{filters.year}-%"
        query = query.filter(
            or_(
                func.coalesce(ContractFact.facts["year"].as_string(), "") == str(filters.year),
                func.coalesce(ContractFact.facts["effective_date"].as_string(), "").like(year_prefix),
                func.coalesce(ContractFact.facts["termination_date"].as_string(), "").like(year_prefix),
                func.coalesce(ContractFact.facts["service_completion_date"].as_string(), "").like(year_prefix),
            )
        )

    if filters.date_from is not None:
        date_floor = filters.date_from.isoformat()
        query = query.filter(
            func.coalesce(
                ContractFact.facts["service_completion_date"].as_string(),
                ContractFact.facts["effective_date"].as_string(),
                ContractFact.facts["termination_date"].as_string(),
                "",
            )
            >= date_floor
        )

    if filters.date_to is not None:
        date_ceiling = filters.date_to.isoformat()
        query = query.filter(
            func.coalesce(
                ContractFact.facts["service_completion_date"].as_string(),
                ContractFact.facts["effective_date"].as_string(),
                ContractFact.facts["termination_date"].as_string(),
                "",
            )
            <= date_ceiling
        )

    seen_document_ids: set[int] = set()
    matches: list[SQLSearchMatch] = []
    for document, contract_fact in query.all():
        if document.id in seen_document_ids:
            continue
        seen_document_ids.add(document.id)
        matches.append(SQLSearchMatch(document=document, facts=contract_fact.facts))
    return matches
