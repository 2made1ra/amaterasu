import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.services.llm import get_llm


JSON_BLOCK_PATTERN = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class ExtractedContractFacts(BaseModel):
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


def _build_prompt(markdown: str) -> str:
    return (
        "Extract contract facts from the markdown below and respond with JSON only.\n"
        "Use this schema:\n"
        "{"
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
        f"Markdown:\n{markdown}"
    )


def _request_facts_payload(markdown: str) -> dict[str, Any]:
    llm = get_llm()
    prompt = _build_prompt(markdown)
    try:
        response = llm.invoke(prompt)
    except Exception as exc:  # pragma: no cover - provider boundary
        raise FactExtractionError(str(exc)) from exc

    if not isinstance(response, str):
        response = str(response)
    return _extract_json_payload(response)


def extract_contract_facts_from_markdown(markdown: str) -> ExtractedContractFacts:
    payload = _request_facts_payload(markdown)
    try:
        return ExtractedContractFacts.model_validate(payload)
    except ValidationError as exc:
        raise FactExtractionValidationError("LLM response did not match the expected fact schema") from exc
