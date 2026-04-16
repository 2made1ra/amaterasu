"""Проверка доступности LLM в LM Studio (OpenAI-совместимый API на локальной сети)."""

import pytest
import httpx

from app.core.config import settings


def _models_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/models"


@pytest.mark.integration
def test_lmstudio_lists_configured_llm_model():
    """Сервер из LMSTUDIO_API_BASE отвечает, в списке моделей есть LLM_MODEL."""
    if settings.LLM_PROVIDER != "lmstudio":
        pytest.skip("ожидается LLM_PROVIDER=lmstudio")

    url = _models_url(settings.LMSTUDIO_API_BASE)
    headers = {"Authorization": f"Bearer {settings.LMSTUDIO_API_KEY}"}

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=headers)
    except httpx.RequestError as exc:
        pytest.fail(f"LM Studio недоступен по адресу из LMSTUDIO_API_BASE: {exc}")

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
