"""Проверка доступности LLM и эмбеддингов в LM Studio (OpenAI-совместимый API на локальной сети)."""

import pytest
import httpx

from app.core.config import settings


def _models_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/models"


def _embeddings_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/embeddings"


def _skip_if_unreachable(exc: httpx.RequestError) -> None:
    pytest.skip(
        f"LM Studio недоступен по LMSTUDIO_API_BASE ({settings.LMSTUDIO_API_BASE}): {exc}"
    )


@pytest.mark.integration
def test_lmstudio_lists_configured_llm_model():
    """Сервер из LMSTUDIO_API_BASE отвечает, в списке моделей есть LLM и embedding модели."""
    if settings.LLM_PROVIDER != "lmstudio":
        pytest.skip("ожидается LLM_PROVIDER=lmstudio")

    url = _models_url(settings.LMSTUDIO_API_BASE)
    headers = {"Authorization": f"Bearer {settings.LMSTUDIO_API_KEY}"}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=headers)
    except httpx.RequestError as exc:
        _skip_if_unreachable(exc)

    assert response.status_code == 200, (
        f"ожидался HTTP 200 от /v1/models, получено {response.status_code}: "
        f"{response.text[:500]}"
    )

    payload = response.json()
    models = payload.get("data") or []
    model_ids = {item.get("id") for item in models if isinstance(item, dict)}

    assert settings.LLM_MODEL in model_ids, (
        f"модель {settings.LLM_MODEL!r} не найдена среди загруженных в LM Studio. "
        f"Доступные id: {sorted(model_ids)}"
    )
    assert settings.FACT_EXTRACTION_MODEL in model_ids, (
        f"модель fact extraction {settings.FACT_EXTRACTION_MODEL!r} не найдена в LM Studio. "
        f"Доступные id: {sorted(model_ids)}"
    )
    assert settings.SUMMARIZATION_MODEL in model_ids, (
        f"модель summarization {settings.SUMMARIZATION_MODEL!r} не найдена в LM Studio. "
        f"Доступные id: {sorted(model_ids)}"
    )

    if settings.EMBEDDINGS_PROVIDER == "lmstudio":
        assert settings.EMBEDDINGS_MODEL in model_ids, (
            f"embedding-модель {settings.EMBEDDINGS_MODEL!r} не найдена среди загруженных в LM Studio. "
            f"Доступные id: {sorted(model_ids)}"
        )


@pytest.mark.integration
def test_lmstudio_embeddings_endpoint_returns_vectors():
    """POST /v1/embeddings отвечает 200 и возвращает непустой вектор для EMBEDDINGS_MODEL."""
    if settings.EMBEDDINGS_PROVIDER != "lmstudio":
        pytest.skip("ожидается EMBEDDINGS_PROVIDER=lmstudio")

    url = _embeddings_url(settings.LMSTUDIO_API_BASE)
    headers = {
        "Authorization": f"Bearer {settings.LMSTUDIO_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"model": settings.EMBEDDINGS_MODEL, "input": "ping"}

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=body)
    except httpx.RequestError as exc:
        _skip_if_unreachable(exc)

    assert response.status_code == 200, (
        f"ожидался HTTP 200 от /v1/embeddings, получено {response.status_code}: "
        f"{response.text[:500]}"
    )

    payload = response.json()
    rows = payload.get("data") or []
    assert isinstance(rows, list) and len(rows) > 0, (
        f"ожидался непустой data[] в ответе embeddings, получено: {payload!r}"[:800]
    )

    first = rows[0]
    assert isinstance(first, dict), f"ожидался объект в data[0], получено: {first!r}"
    vector = first.get("embedding")
    assert isinstance(vector, list) and len(vector) > 0, (
        f"ожидался непустой список embedding, получено: {first!r}"[:800]
    )
    assert all(isinstance(x, (int, float)) for x in vector), (
        "элементы embedding должны быть числами"
    )
