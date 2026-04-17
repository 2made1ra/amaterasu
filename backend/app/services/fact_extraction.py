import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.services.llm import extract_llm_text, get_llm, split_text_for_llm


JSON_BLOCK_PATTERN = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
CURRENT_CONTRACT_FACTS_SCHEMA_VERSION = 3
REQUIRED_FACT_FIELDS = (
    "company_name",
    "signatory_name",
    "contact_phone",
    "service_price",
    "service_subject",
    "service_completion_date",
)
DOCUMENT_KIND_VALUES = {"contract", "supplier_order", "planned_expense", "unknown"}
GENERIC_TITLE_TOKENS = {"contract", "pdf", "договор", "контракт", "document", "документ"}
OCR_DATE_RANGE_PATTERN = re.compile(
    r"(?P<start_day>\d{1,2})[./-](?P<start_month>\d{1,2})[./-](?P<start_year>\d{2,4})"
    r"\s*(?:по|до|no|to|[-–—])\s*"
    r"(?P<end_day>\d{1,2})[./-](?P<end_month>\d{1,2})[./-](?P<end_year>\d{2,4})",
    re.IGNORECASE,
)
OCR_PRICE_PATTERN = re.compile(
    r"(?P<amount>\d[\dOОoо\s]{2,10}\d|\d[\dOОoо]{2,10})"
    r"\s*(?:\([^)]{0,80}\))?\s*(?:руб(?:л[еяй]|ей)?|р(?:уб)?\.?|py6\w*|rub)\b",
    re.IGNORECASE,
)
OCR_COMPANY_PATTERN = re.compile(
    r"\b(?P<prefix>ООО|OOO|ОАО|AO|ЗАО|ZAO|ИП|IP)\b\s*[\"'«»《》]?(?P<name>[^\n]{2,80})",
    re.IGNORECASE,
)
OCR_INITIALS_NAME_PATTERN = re.compile(
    r"\b(?P<name>[A-ZА-ЯЁ][A-Za-zА-Яа-яЁё-]{2,}\s+[A-ZА-ЯЁ]\.[A-ZА-ЯЁ]\.)\b"
)


class FactSourceHint(BaseModel):
    page_number: int | None = None
    snippet: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ExtractedContractFacts(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company_name: str | None = None
    signatory_name: str | None = None
    contact_phone: str | None = None
    service_price: str | None = None
    service_subject: str | None = None
    service_completion_date: str | None = None
    document_kind: Literal["contract", "supplier_order", "planned_expense", "unknown"] = "unknown"
    source_hints: dict[str, FactSourceHint] = Field(default_factory=dict)
    missing_required_fields: list[str] = Field(default_factory=list)
    parsing_method: str | None = None
    parser_quality: Literal["high", "medium", "low"] | None = None
    parser_quality_score: float | None = None
    document_title: str | None = None
    contract_type: str | None = None
    parties: list[str] = Field(default_factory=list)
    effective_date: str | None = None
    termination_date: str | None = None
    renewal_terms: str | None = None
    payment_terms: str | None = None
    governing_law: str | None = None
    obligations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    summary: str | None = None

    @field_validator(*REQUIRED_FACT_FIELDS, mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("missing_required_fields", mode="before")
    @classmethod
    def normalize_missing_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            normalized_item = item.strip()
            if normalized_item in REQUIRED_FACT_FIELDS and normalized_item not in normalized:
                normalized.append(normalized_item)
        return normalized

    @field_validator("parties", "obligations", "risks", mode="before")
    @classmethod
    def normalize_string_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            return []

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    @field_validator("source_hints", mode="before")
    @classmethod
    def normalize_source_hints(cls, value):
        if value is None or not isinstance(value, dict):
            return {}

        normalized: dict[str, dict[str, Any]] = {}
        for field_name, hint in value.items():
            if not isinstance(field_name, str):
                continue
            normalized_field = field_name.strip()
            if not normalized_field:
                continue
            if hint is None:
                continue

            if isinstance(hint, FactSourceHint):
                if hint.page_number is None and not hint.snippet:
                    continue
                normalized[normalized_field] = hint.model_dump(exclude_none=True)
                continue

            if isinstance(hint, str):
                snippet = hint.strip()
                if snippet:
                    normalized[normalized_field] = {"snippet": snippet}
                continue

            if not isinstance(hint, dict):
                continue

            page_number = hint.get("page_number")
            snippet = hint.get("snippet")

            normalized_page: int | None = None
            if isinstance(page_number, int):
                normalized_page = page_number
            elif isinstance(page_number, float) and page_number.is_integer():
                normalized_page = int(page_number)
            elif isinstance(page_number, str):
                stripped_page = page_number.strip()
                if stripped_page.isdigit():
                    normalized_page = int(stripped_page)

            normalized_snippet: str | None = None
            if isinstance(snippet, str):
                cleaned_snippet = snippet.strip()
                if cleaned_snippet:
                    normalized_snippet = cleaned_snippet

            if normalized_page is None and normalized_snippet is None:
                continue

            normalized_hint: dict[str, Any] = {}
            if normalized_page is not None:
                normalized_hint["page_number"] = normalized_page
            if normalized_snippet is not None:
                normalized_hint["snippet"] = normalized_snippet
            normalized[normalized_field] = normalized_hint

        return normalized


class ValidatedContractFacts(ExtractedContractFacts):
    company_name: str
    signatory_name: str
    contact_phone: str
    service_price: str
    service_subject: str
    service_completion_date: str

    @field_validator(*REQUIRED_FACT_FIELDS)
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Field must not be empty")
        return value.strip()


class FactExtractionError(RuntimeError):
    pass


class FactExtractionValidationError(FactExtractionError):
    pass


def _normalize_year(year: str) -> str:
    if len(year) == 2:
        return f"20{year}"
    return year.zfill(4)


def _normalize_date_value(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    match = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", trimmed)
    if match:
        day, month, year = match.groups()
        return f"{_normalize_year(year)}-{month.zfill(2)}-{day.zfill(2)}"

    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", trimmed)
    if match:
        return trimmed

    return trimmed


def _normalize_ocr_search_text(text: str | None) -> str:
    if not text:
        return ""

    normalized = text
    normalized = re.sub(r"(?<!\d)(\d{1,2})[./-](\d{2})(\d{4})(?!\d)", r"\1.\2.\3", normalized)
    normalized = re.sub(
        r"(?<=\d)[OОoо](?=[\d.,])|(?<=[\d.,])[OОoо](?=\d)",
        "0",
        normalized,
    )
    return normalized


def _normalize_amount_token(raw_amount: str) -> str | None:
    if not raw_amount:
        return None

    candidate = re.sub(r"[OОoо]", "0", raw_amount)
    candidate = re.sub(r"\s+", "", candidate)
    candidate = re.sub(r"[^\d.,]", "", candidate)
    digits_only = re.sub(r"[^\d]", "", candidate)
    if not digits_only:
        return None

    if 4 <= len(digits_only) <= 9:
        return digits_only
    return None


def _extract_completion_date_from_markdown(markdown: str | None) -> str | None:
    search_text = _normalize_ocr_search_text(markdown)
    match = OCR_DATE_RANGE_PATTERN.search(search_text)
    if not match:
        return None

    return _normalize_date_value(
        f"{match.group('end_day')}.{match.group('end_month')}.{_normalize_year(match.group('end_year'))}"
    )


def _extract_price_from_markdown(markdown: str | None) -> str | None:
    search_text = _normalize_ocr_search_text(markdown)
    match = OCR_PRICE_PATTERN.search(search_text)
    if not match:
        return None

    amount = _normalize_amount_token(match.group("amount"))
    if not amount:
        return None
    return f"{amount} RUB"


def _extract_company_from_markdown(markdown: str | None) -> str | None:
    if not markdown:
        return None

    match = OCR_COMPANY_PATTERN.search(markdown)
    if not match:
        return None

    company = f"{match.group('prefix')} {match.group('name')}"
    company = re.split(r"[,\n]", company, maxsplit=1)[0]
    company = company.strip(" \"'«»《》.:;")
    return company or None


def _extract_signatory_from_markdown(markdown: str | None) -> str | None:
    if not markdown:
        return None

    match = OCR_INITIALS_NAME_PATTERN.search(markdown)
    if not match:
        return None
    return match.group("name").strip()


def _is_title_name_token(token: str) -> bool:
    return bool(re.fullmatch(r"[А-ЯЁ][а-яё]+", token))


def _extract_title_company_and_signatory(title: str | None) -> tuple[str | None, str | None, str | None]:
    if not title:
        return None, None, None

    stem = Path(title).stem
    tokens = [
        re.sub(r"[^\wА-Яа-яЁё-]+", "", token)
        for token in re.split(r"[_\s]+", stem)
    ]
    tokens = [token for token in tokens if token]
    cleaned_title = " ".join(token for token in tokens if token.lower() not in GENERIC_TITLE_TOKENS).strip() or None

    signatory_name = None
    company_name = None

    for name_length in (3, 2):
        for start_index in range(len(tokens) - name_length, -1, -1):
            window = tokens[start_index : start_index + name_length]
            if not all(_is_title_name_token(token) for token in window):
                continue

            signatory_name = " ".join(window)
            company_tokens = [
                token
                for token in tokens[:start_index]
                if token.lower() not in GENERIC_TITLE_TOKENS
            ]
            company_name = " ".join(company_tokens).strip() or None
            return cleaned_title, company_name, signatory_name

    return cleaned_title, company_name, signatory_name


def _apply_field_fallbacks(
    payload: dict[str, Any],
    *,
    markdown: str | None = None,
    document_title: str | None = None,
) -> dict[str, Any]:
    next_payload = dict(payload)
    cleaned_title, title_company, title_signatory = _extract_title_company_and_signatory(document_title)

    if cleaned_title and not next_payload.get("document_title"):
        next_payload["document_title"] = cleaned_title
    if not next_payload.get("company_name"):
        next_payload["company_name"] = title_company or _extract_company_from_markdown(markdown)
    if not next_payload.get("signatory_name"):
        next_payload["signatory_name"] = title_signatory or _extract_signatory_from_markdown(markdown)
    if not next_payload.get("service_price"):
        next_payload["service_price"] = _extract_price_from_markdown(markdown)
    if not next_payload.get("service_completion_date"):
        next_payload["service_completion_date"] = (
            _extract_completion_date_from_markdown(markdown)
            or _normalize_date_value(next_payload.get("termination_date"))
            or _normalize_date_value(next_payload.get("effective_date"))
        )

    return next_payload


def _slice_first_balanced_json_object(s: str) -> str | None:
    """Return substring from first `{` through matching `}` (string-aware), or None if unclosed."""
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    i = start
    in_string = False
    escape = False
    while i < len(s):
        c = s[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]
        i += 1
    return None


def _extract_json_payload(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    candidate = text
    fenced_match = JSON_BLOCK_PATTERN.search(candidate)
    if fenced_match:
        candidate = fenced_match.group(1).strip()

    def _as_fact_dict(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise FactExtractionValidationError("LLM response must decode to a JSON object")
        return payload

    try:
        return _as_fact_dict(json.loads(candidate))
    except json.JSONDecodeError:
        pass

    for probe in (_slice_first_balanced_json_object(candidate), _slice_first_balanced_json_object(text)):
        if not probe:
            continue
        try:
            return _as_fact_dict(json.loads(probe))
        except json.JSONDecodeError:
            continue

    for probe in (candidate, text):
        if "{" in probe and _slice_first_balanced_json_object(probe) is None:
            raise FactExtractionValidationError(
                "LLM output appears truncated by the token limit; could not parse JSON"
            )

    raise FactExtractionValidationError("LLM response was not valid JSON")


def _build_prompt(markdown: str, parsing_metadata: dict[str, Any] | None = None) -> str:
    parsing_metadata_json = json.dumps(parsing_metadata or {}, ensure_ascii=False, sort_keys=True)
    return (
        "Extract structured business facts from the Russian-language document markdown below and respond with JSON only.\n"
        "The document may be a contract, supplier order, planned expense, or an unknown adjacent business form.\n"
        "Classify it into one of: contract, supplier_order, planned_expense, unknown.\n"
        "Do not invent facts. During extraction, required business fields may be null only if they are truly absent or unreadable.\n"
        "Use business equivalents when the exact contract wording is missing.\n"
        "Map synonyms as follows:\n"
        "- company_name: company, contractor, vendor, customer, client, counterparty, заказчик, исполнитель, контрагент, поставщик\n"
        "- signatory_name: signatory, contact person, responsible person, signed by, подписант, контактное лицо, ответственный\n"
        "- contact_phone: phone, mobile, tel, телефон, контактный телефон\n"
        "- service_price: price, amount, total, value, sum, стоимость, сумма, цена, планируемый расход\n"
        "- service_subject: service, scope, work item, description, предмет, наименование услуг, описание работ\n"
        "- service_completion_date: completion date, act date, delivery date, event date, срок оказания, дата акта, срок поставки, дата мероприятия\n"
        "Return source_hints for required fields with a page_number and a short snippet when possible.\n"
        "Use this schema:\n"
        "{"
        '"company_name": "string | null", '
        '"signatory_name": "string | null", '
        '"contact_phone": "string | null", '
        '"service_price": "string | null", '
        '"service_subject": "string | null", '
        '"service_completion_date": "string | null", '
        '"document_kind": "contract | supplier_order | planned_expense | unknown", '
        '"source_hints": {"company_name": {"page_number": 1, "snippet": "..."}, "service_price": {"page_number": 2, "snippet": "..."}}, '
        '"document_title": "string | null", '
        '"contract_type": "string | null", '
        '"parties": ["string"], '
        '"effective_date": "string | null", '
        '"termination_date": "string | null", '
        '"renewal_terms": "string | null", '
        '"payment_terms": "string | null", '
        '"governing_law": "string | null", '
        '"obligations": ["string"], '
        '"risks": ["string"], '
        '"summary": "string | null"'
        "}\n\n"
        f"Parsing metadata:\n{parsing_metadata_json}\n\n"
        f"Markdown:\n{markdown}"
    )


def _request_facts_payload(markdown: str, parsing_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    llm = get_llm("fact_extraction")
    markdown_chunks = split_text_for_llm(markdown)
    payloads: list[dict[str, Any]] = []

    for chunk_index, chunk in enumerate(markdown_chunks, start=1):
        chunk_metadata = dict(parsing_metadata or {})
        chunk_metadata["chunk_index"] = chunk_index
        chunk_metadata["chunk_count"] = len(markdown_chunks)
        prompt = _build_prompt(chunk, parsing_metadata=chunk_metadata)
        try:
            response = llm.invoke(prompt)
        except Exception as exc:  # pragma: no cover - provider boundary
            raise FactExtractionError(str(exc)) from exc

        payloads.append(_extract_json_payload(extract_llm_text(response)))

    if len(payloads) == 1:
        return payloads[0]
    return _merge_facts_payloads(payloads)


def _merge_facts_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "document_kind": "unknown",
        "source_hints": {},
        "parties": [],
        "obligations": [],
        "risks": [],
    }

    scalar_fields = (
        "company_name",
        "signatory_name",
        "contact_phone",
        "service_price",
        "service_subject",
        "service_completion_date",
        "document_title",
        "contract_type",
        "effective_date",
        "termination_date",
        "renewal_terms",
        "payment_terms",
        "governing_law",
        "summary",
        "parsing_method",
        "parser_quality",
        "parser_quality_score",
    )
    list_fields = ("parties", "obligations", "risks", "missing_required_fields")

    for payload in payloads:
        for field_name in scalar_fields:
            value = payload.get(field_name)
            if value in (None, "", []):
                continue

            if field_name == "summary" and merged.get("summary"):
                if len(str(value)) > len(str(merged["summary"])):
                    merged[field_name] = value
                continue

            if field_name == "parser_quality_score" and merged.get("parser_quality_score") is not None:
                merged[field_name] = max(float(merged[field_name]), float(value))
                continue

            if field_name == "parser_quality" and merged.get("parser_quality"):
                rank = {"low": 0, "medium": 1, "high": 2}
                current = rank.get(str(merged[field_name]), -1)
                candidate = rank.get(str(value), -1)
                if candidate > current:
                    merged[field_name] = value
                continue

            merged.setdefault(field_name, value)
            if not merged.get(field_name):
                merged[field_name] = value

        if payload.get("document_kind") in DOCUMENT_KIND_VALUES and merged["document_kind"] == "unknown":
            merged["document_kind"] = payload["document_kind"]

        source_hints = payload.get("source_hints")
        if isinstance(source_hints, dict):
            for field_name, hint in source_hints.items():
                merged["source_hints"].setdefault(field_name, hint)

        for field_name in list_fields:
            values = payload.get(field_name) or []
            if isinstance(values, str):
                values = [values]
            for value in values:
                if value and value not in merged.setdefault(field_name, []):
                    merged[field_name].append(value)

    return merged


def _enrich_extracted_facts(
    facts: ExtractedContractFacts,
    *,
    parsing_metadata: dict[str, Any] | None = None,
    markdown: str | None = None,
    document_title: str | None = None,
) -> ExtractedContractFacts:
    payload = _apply_field_fallbacks(
        facts.model_dump(),
        markdown=markdown,
        document_title=document_title,
    )
    payload["missing_required_fields"] = [
        field_name for field_name in REQUIRED_FACT_FIELDS if not payload.get(field_name)
    ]

    if parsing_metadata:
        payload["parsing_method"] = payload.get("parsing_method") or parsing_metadata.get("extraction_method")
        payload["parser_quality"] = payload.get("parser_quality") or parsing_metadata.get("quality_label")
        payload["parser_quality_score"] = payload.get("parser_quality_score") or parsing_metadata.get("quality_score")

    if payload.get("document_kind") not in DOCUMENT_KIND_VALUES:
        payload["document_kind"] = "unknown"

    return ExtractedContractFacts.model_validate(payload)


def extract_contract_facts_from_markdown(
    markdown: str,
    *,
    parsing_metadata: dict[str, Any] | None = None,
    document_title: str | None = None,
) -> ExtractedContractFacts:
    payload = _request_facts_payload(markdown, parsing_metadata=parsing_metadata)
    return prepare_contract_facts_payload(
        payload,
        parsing_metadata=parsing_metadata,
        markdown=markdown,
        document_title=document_title,
    )


def prepare_contract_facts_payload(
    payload: dict[str, Any],
    *,
    parsing_metadata: dict[str, Any] | None = None,
    markdown: str | None = None,
    document_title: str | None = None,
) -> ExtractedContractFacts:
    try:
        facts = ExtractedContractFacts.model_validate(payload)
    except ValidationError as exc:
        raise FactExtractionValidationError("LLM response did not match the expected fact schema") from exc
    return _enrich_extracted_facts(
        facts,
        parsing_metadata=parsing_metadata,
        markdown=markdown,
        document_title=document_title,
    )


def validate_contract_facts_payload(payload: dict[str, Any]) -> ValidatedContractFacts:
    try:
        return ValidatedContractFacts.model_validate(payload)
    except ValidationError as exc:
        raise FactExtractionValidationError("LLM response did not match the expected fact schema") from exc


def has_complete_required_facts(payload: dict[str, Any]) -> bool:
    try:
        facts = prepare_contract_facts_payload(payload)
    except FactExtractionValidationError:
        return False
    return not facts.missing_required_fields


def is_contract_facts_indexable(payload: dict[str, Any]) -> bool:
    if not has_complete_required_facts(payload):
        return False

    try:
        facts = prepare_contract_facts_payload(payload)
    except FactExtractionValidationError:
        return False

    if facts.parser_quality == "low":
        return False
    if facts.parser_quality_score is not None and facts.parser_quality_score < 0.4:
        return False
    return True
