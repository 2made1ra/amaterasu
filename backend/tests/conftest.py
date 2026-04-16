"""Загружает backend/.env до импорта настроек, чтобы тесты видели LM Studio и модель."""

from pathlib import Path

from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND_ROOT / ".env")
