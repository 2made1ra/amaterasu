from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.llm import get_llm


class DocumentIndexingError(RuntimeError):
    pass


def _get_text_splitter_class():
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        return RecursiveCharacterTextSplitter
    except ImportError:
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            return RecursiveCharacterTextSplitter
        except ImportError as exc:  # pragma: no cover - dependency boundary
            raise DocumentIndexingError(
                "Missing text splitter dependency. Install `langchain-text-splitters`."
            ) from exc


def _extract_llm_text(response: Any) -> str:
    if isinstance(response, str):
        return response.strip()

    content = getattr(response, "content", None)
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part).strip()

    return str(response).strip()


def generate_document_summary(markdown: str, facts: dict[str, Any] | None = None) -> str:
    llm = get_llm()
    facts_json = json.dumps(facts or {}, ensure_ascii=True, sort_keys=True)
    prompt = (
        "You are summarizing a contract for retrieval.\n"
        "Write a concise summary in 4-6 sentences covering the parties, obligations, dates, value, and scope when present.\n"
        "Use the extracted facts when helpful, but do not invent missing details.\n\n"
        f"Extracted facts:\n{facts_json}\n\n"
        f"Contract markdown:\n{markdown[:6000]}"
    )

    if hasattr(llm, "invoke"):
        response = llm.invoke(prompt)
    else:
        response = llm(prompt)

    summary = _extract_llm_text(response)
    if not summary:
        raise DocumentIndexingError("LLM returned an empty summary")
    return summary


def split_markdown_into_chunks(markdown: str) -> list[str]:
    RecursiveCharacterTextSplitter = _get_text_splitter_class()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.INDEXING_CHUNK_SIZE,
        chunk_overlap=settings.INDEXING_CHUNK_OVERLAP,
    )
    chunks = [chunk.strip() for chunk in splitter.split_text(markdown) if chunk.strip()]
    if not chunks:
        raise DocumentIndexingError("Chunking produced no indexable text")
    return chunks
