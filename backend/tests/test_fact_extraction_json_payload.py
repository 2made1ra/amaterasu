"""Тесты разбора JSON из ответа LLM (fact_extraction._extract_json_payload)."""

import pytest

from app.services.fact_extraction import FactExtractionValidationError, _extract_json_payload


def test_extract_json_plain_object():
    raw = '{"company_name": "Acme", "document_kind": "unknown"}'
    out = _extract_json_payload(raw)
    assert out["company_name"] == "Acme"


def test_extract_json_fenced_block():
    raw = 'Here:\n```json\n{"company_name": "X", "document_kind": "unknown"}\n```'
    out = _extract_json_payload(raw)
    assert out["company_name"] == "X"


def test_extract_json_prefix_before_object():
    raw = 'OM\nSome noise\n{"company_name": "Y", "document_kind": "unknown"}'
    out = _extract_json_payload(raw)
    assert out["company_name"] == "Y"


def test_extract_json_rejects_non_object():
    with pytest.raises(FactExtractionValidationError, match="JSON object"):
        _extract_json_payload("[1, 2, 3]")


def test_extract_json_truncated_raises_clear_message():
    raw = 'Prefix {"company_name": "Z", "summary": "incomplete'
    with pytest.raises(FactExtractionValidationError, match="truncated"):
        _extract_json_payload(raw)
