import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.services.llm import get_llm


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
        return [item for item in value if item in REQUIRED_FACT_FIELDS]


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


def _extract_json_payload(raw_response: str) -> dict[str, Any]:
    candidate = raw_response.strip()
    fenced_match = JSON_BLOCK_PATTERN.search(candidate)
    if fenced_match:
        candidate = fenced_match.group(1).strip()

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise FactExtractionValidationError("LLM response was not valid JSON") from exc

    if not isinstance(payload, dict):
        raise FactExtractionValidationError("LLM response must decode to a JSON object")
    return payload


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
    llm = get_llm()
    prompt = _build_prompt(markdown, parsing_metadata=parsing_metadata)
    try:
        response = llm.invoke(prompt)
    except Exception as exc:  # pragma: no cover - provider boundary
        raise FactExtractionError(str(exc)) from exc

    if not isinstance(response, str):
        response = str(response)
    return _extract_json_payload(response)


def _enrich_extracted_facts(
    facts: ExtractedContractFacts,
    *,
    parsing_metadata: dict[str, Any] | None = None,
) -> ExtractedContractFacts:
    payload = facts.model_dump()
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
) -> ExtractedContractFacts:
    payload = _request_facts_payload(markdown, parsing_metadata=parsing_metadata)
    return prepare_contract_facts_payload(payload, parsing_metadata=parsing_metadata)


def prepare_contract_facts_payload(
    payload: dict[str, Any],
    *,
    parsing_metadata: dict[str, Any] | None = None,
) -> ExtractedContractFacts:
    try:
        facts = ExtractedContractFacts.model_validate(payload)
    except ValidationError as exc:
        raise FactExtractionValidationError("LLM response did not match the expected fact schema") from exc
    return _enrich_extracted_facts(facts, parsing_metadata=parsing_metadata)


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
