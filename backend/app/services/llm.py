from __future__ import annotations

from typing import Any, Literal

from app.core.config import settings


LlmPurpose = Literal["default", "fact_extraction", "summarization"]

_llm_instances: dict[tuple[str, str], object] = {}
_embeddings_instance = None


class LMStudioEmbeddings:
    """OpenAI-compatible embeddings client that always sends raw strings to LM Studio."""

    def __init__(self, *, base_url: str, api_key: str, model: str, client: Any | None = None):
        if client is None:
            from openai import OpenAI

            client = OpenAI(base_url=base_url, api_key=api_key)
        self.client = client
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        normalized_texts = [text if isinstance(text, str) else str(text) for text in texts]
        if not normalized_texts:
            return []

        response = self.client.embeddings.create(
            model=self.model,
            input=normalized_texts,
            encoding_format="float",
        )
        return [list(item.embedding) for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        vectors = self.embed_documents([query])
        return vectors[0] if vectors else []


def extract_llm_text(response: Any) -> str:
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


def resolve_llm_model(purpose: LlmPurpose = "default") -> str:
    if purpose == "fact_extraction":
        return settings.FACT_EXTRACTION_MODEL
    if purpose == "summarization":
        return settings.SUMMARIZATION_MODEL
    return settings.LLM_MODEL


def get_llm(purpose: LlmPurpose = "default"):
    provider = settings.LLM_PROVIDER
    model_name = resolve_llm_model(purpose)
    cache_key = (provider, model_name)

    if cache_key in _llm_instances:
        return _llm_instances[cache_key]

    if provider == "lmstudio":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            base_url=settings.LMSTUDIO_API_BASE,
            api_key=settings.LMSTUDIO_API_KEY,
            model=model_name,
            max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        )
    else:
        from langchain_community.llms import HuggingFacePipeline
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)
        llm = HuggingFacePipeline(pipeline=pipe)

    _llm_instances[cache_key] = llm
    return llm


def get_embeddings():
    global _embeddings_instance

    if _embeddings_instance is not None:
        return _embeddings_instance

    if settings.EMBEDDINGS_PROVIDER == "lmstudio":
        _embeddings_instance = LMStudioEmbeddings(
            base_url=settings.LMSTUDIO_API_BASE,
            api_key=settings.LMSTUDIO_API_KEY,
            model=settings.EMBEDDINGS_MODEL,
        )
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        _embeddings_instance = HuggingFaceEmbeddings(model_name=settings.EMBEDDINGS_MODEL)

    return _embeddings_instance


def estimate_llm_input_char_budget() -> int:
    available_tokens = (
        settings.LLM_CONTEXT_WINDOW
        - settings.LLM_RESERVED_OUTPUT_TOKENS
        - settings.LLM_PROMPT_OVERHEAD_TOKENS
    )
    available_tokens = max(256, available_tokens)
    return max(1500, int(available_tokens * settings.LLM_APPROX_CHARS_PER_TOKEN))


def split_text_for_llm(text: str, *, target_chars: int | None = None) -> list[str]:
    text = text.strip()
    if not text:
        return []

    budget = target_chars or estimate_llm_input_char_budget()
    if len(text) <= budget:
        return [text]

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        except ImportError as exc:  # pragma: no cover - dependency boundary
            raise RuntimeError(
                "Missing text splitter dependency. Install `langchain-text-splitters`."
            ) from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=budget,
        chunk_overlap=min(settings.LLM_CHUNK_OVERLAP_CHARS, max(0, budget // 5)),
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]
