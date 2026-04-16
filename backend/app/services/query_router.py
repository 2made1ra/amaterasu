from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class QueryRoute(str, Enum):
    SQL_ONLY = "SQL_ONLY"
    SUMMARY_ONLY = "SUMMARY_ONLY"
    SUMMARY_THEN_CHUNKS = "SUMMARY_THEN_CHUNKS"
    CHUNKS_ONLY = "CHUNKS_ONLY"
    HYBRID_SQL_AND_CHUNKS = "HYBRID_SQL_AND_CHUNKS"


_LIST_REPORT_KEYWORDS = (
    "list",
    "show",
    "count",
    "report",
    "table",
    "how many",
    "which contracts",
    "find contracts",
)
_DISCOVERY_KEYWORDS = (
    "which contracts mention",
    "find contracts about",
    "find contracts mentioning",
    "topic",
    "overview",
    "discover",
    "surface",
)
_EXPLANATION_KEYWORDS = (
    "explain",
    "why",
    "how",
    "what does",
    "what do",
    "clause",
    "clauses",
    "obligation",
    "obligations",
    "risk",
    "risks",
    "payment",
    "renewal",
    "termination",
    "governing law",
    "penalty",
)
_CHUNK_FOCUSED_KEYWORDS = (
    "quote",
    "exact wording",
    "section",
    "paragraph",
    "line",
    "excerpt",
)
_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
_DATE_RANGE_PATTERN = re.compile(
    r"\b(?:from|between)\s+(20\d{2}-\d{2}-\d{2})\s+(?:to|and)\s+(20\d{2}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
_SUPPLIER_ANCHORED_PATTERN = re.compile(
    r"\b(?:supplier|vendor|contractor|counterparty)\s*(?:is|=|named|for|:)?\s*[\"']?([A-Za-z0-9][A-Za-z0-9&.,() /-]{1,80}?)[\"']?(?=\s+\b(?:in|from|between|with|and|that|where|whose)\b|[?.!,]|$)",
    re.IGNORECASE,
)
_FOR_WITH_PATTERN = re.compile(
    r"\b(?:for|with)\s+([A-Z][A-Za-z0-9&.,() /-]{1,80}?)(?=\s+\b(?:in|from|between|covering|about|that|where|whose)\b|[?.!,]|$)"
)


@dataclass(slots=True)
class QueryFilters:
    year: int | None = None
    supplier: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    document_ids: list[int] = field(default_factory=list)

    def has_structured_filters(self) -> bool:
        return any(
            (
                self.year is not None,
                self.supplier is not None,
                self.date_from is not None,
                self.date_to is not None,
                bool(self.document_ids),
            )
        )


@dataclass(slots=True)
class QueryRouteDecision:
    route: QueryRoute
    filters: QueryFilters


def route_query(query: str, *, document_id: int | None = None) -> QueryRouteDecision:
    filters = extract_query_filters(query)
    if document_id is not None:
        filters.document_ids = [document_id]
        return QueryRouteDecision(route=QueryRoute.CHUNKS_ONLY, filters=filters)

    normalized = " ".join(query.lower().split())
    if _is_hybrid_query(normalized, filters):
        route = QueryRoute.HYBRID_SQL_AND_CHUNKS
    elif _is_chunks_only_query(normalized):
        route = QueryRoute.CHUNKS_ONLY
    elif _is_summary_only_query(normalized):
        route = QueryRoute.SUMMARY_ONLY
    elif _is_sql_only_query(normalized, filters):
        route = QueryRoute.SQL_ONLY
    else:
        route = QueryRoute.SUMMARY_THEN_CHUNKS

    return QueryRouteDecision(route=route, filters=filters)


def extract_query_filters(query: str) -> QueryFilters:
    stripped_query = query.strip()
    filters = QueryFilters()

    year_match = _YEAR_PATTERN.search(stripped_query)
    if year_match:
        filters.year = int(year_match.group(1))

    date_range_match = _DATE_RANGE_PATTERN.search(stripped_query)
    if date_range_match:
        filters.date_from = date.fromisoformat(date_range_match.group(1))
        filters.date_to = date.fromisoformat(date_range_match.group(2))
        if filters.date_from > filters.date_to:
            filters.date_from, filters.date_to = filters.date_to, filters.date_from

    supplier_match = _SUPPLIER_ANCHORED_PATTERN.search(stripped_query)
    if supplier_match:
        filters.supplier = _normalize_phrase(supplier_match.group(1))
    else:
        contextual_match = _FOR_WITH_PATTERN.search(stripped_query)
        if contextual_match and _looks_like_supplier_query(stripped_query):
            filters.supplier = _normalize_phrase(contextual_match.group(1))

    return filters


def _is_sql_only_query(normalized_query: str, filters: QueryFilters) -> bool:
    has_list_intent = any(keyword in normalized_query for keyword in _LIST_REPORT_KEYWORDS)
    return has_list_intent or filters.has_structured_filters()


def _is_hybrid_query(normalized_query: str, filters: QueryFilters) -> bool:
    if not filters.has_structured_filters():
        return False
    return any(keyword in normalized_query for keyword in _EXPLANATION_KEYWORDS)


def _is_chunks_only_query(normalized_query: str) -> bool:
    return any(keyword in normalized_query for keyword in _CHUNK_FOCUSED_KEYWORDS)


def _is_summary_only_query(normalized_query: str) -> bool:
    return any(keyword in normalized_query for keyword in _DISCOVERY_KEYWORDS)


def _looks_like_supplier_query(query: str) -> bool:
    lowered = query.lower()
    return any(keyword in lowered for keyword in _LIST_REPORT_KEYWORDS + _EXPLANATION_KEYWORDS)


def _normalize_phrase(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ,.")
