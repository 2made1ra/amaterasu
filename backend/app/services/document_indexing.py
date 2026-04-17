from __future__ import annotations

import json
from typing import Any

from app.core.config import settings
from app.services.llm import extract_llm_text, get_llm, split_text_for_llm


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


def generate_document_summary(markdown: str, facts: dict[str, Any] | None = None) -> str:
    llm = get_llm("summarization")
    facts_json = json.dumps(facts or {}, ensure_ascii=True, sort_keys=True)
    markdown_chunks = split_text_for_llm(markdown)
    partial_summaries = []

    for chunk_index, chunk in enumerate(markdown_chunks, start=1):
        prompt = (
            "You are summarizing a contract for retrieval.\n"
            "Write a concise summary in 4-6 sentences covering the parties, obligations, dates, value, and scope when present.\n"
            "Use the extracted facts when helpful, but do not invent missing details.\n"
            "Preserve precise business entities and dates when they are visible.\n\n"
            f"Extracted facts:\n{facts_json}\n\n"
            f"Contract markdown chunk {chunk_index}/{len(markdown_chunks)}:\n{chunk}"
        )

        if hasattr(llm, "invoke"):
            response = llm.invoke(prompt)
        else:
            response = llm(prompt)
        partial_summary = extract_llm_text(response)
        if partial_summary:
            partial_summaries.append(partial_summary)

    if not partial_summaries:
        raise DocumentIndexingError("LLM returned an empty summary")

    if len(partial_summaries) == 1:
        summary = partial_summaries[0]
    else:
        merge_prompt = (
            "You are summarizing a contract for retrieval.\n"
            "Merge the partial summaries below into one final retrieval summary in 4-6 sentences.\n"
            "Keep the answer compact, factual, and suitable for vector search.\n"
            "Do not invent details that are absent from the partial summaries.\n\n"
            f"Extracted facts:\n{facts_json}\n\n"
            "Partial summaries:\n"
            + "\n\n".join(
                f"Part {index}:\n{partial_summary}"
                for index, partial_summary in enumerate(partial_summaries, start=1)
            )
        )

        if hasattr(llm, "invoke"):
            response = llm.invoke(merge_prompt)
        else:
            response = llm(merge_prompt)
        summary = extract_llm_text(response)

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
