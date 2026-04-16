from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Literal

from pypdf import PdfReader

from app.core.config import settings


DIADOC_LINE_PATTERNS = (
    re.compile(r"^\s*Передан через Диадок\b", re.IGNORECASE),
    re.compile(r"^\s*Подписан через Диадок\b", re.IGNORECASE),
    re.compile(r"^\s*Страница\s+\d+\s+из\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*[0-9a-f-]{24,}\s*$", re.IGNORECASE),
    re.compile(r"^\s*Документ подписан электронной подписью\b", re.IGNORECASE),
)
CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")


@dataclass(slots=True)
class PageParsingResult:
    page_number: int
    extraction_method: Literal["text", "ocr", "mixed"]
    quality_score: float
    quality_label: Literal["high", "medium", "low"]
    raw_text_chars: int
    normalized_text_chars: int
    low_quality_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsingMetadata:
    extraction_method: Literal["text", "ocr", "mixed"]
    quality_score: float
    quality_label: Literal["high", "medium", "low"]
    page_count: int
    usable_page_count: int
    low_quality_page_count: int
    total_text_chars: int
    pages: list[PageParsingResult]


@dataclass(slots=True)
class ParsedDocument:
    markdown: str
    artifact_path: str
    metadata_path: str
    extraction_method: Literal["text", "ocr", "mixed"]
    quality_score: float
    quality_label: Literal["high", "medium", "low"]


class DocumentParsingError(RuntimeError):
    pass


def _extract_page_text(page) -> str:
    try:
        text = page.extract_text(extraction_mode="layout")
    except TypeError:
        text = page.extract_text()
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(str(exc)) from exc
    return (text or "").strip()


def _normalize_text(text: str) -> str:
    if not text:
        return ""

    normalized_lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if any(pattern.match(line) for pattern in DIADOC_LINE_PATTERNS):
            continue
        normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def _assess_text_quality(text: str) -> tuple[float, list[str]]:
    if not text:
        return 0.0, ["empty"]

    stripped = text.strip()
    char_count = len(stripped)
    digit_count = sum(char.isdigit() for char in stripped)
    word_count = len(stripped.split())
    cyrillic_count = len(CYRILLIC_PATTERN.findall(stripped))
    latin_count = len(LATIN_PATTERN.findall(stripped))

    reasons: list[str] = []
    if char_count < settings.PARSER_MIN_PAGE_TEXT_CHARS:
        reasons.append("too_short")
    if word_count < 10:
        reasons.append("low_word_count")
    if (cyrillic_count + latin_count) < max(20, char_count // 6):
        reasons.append("low_text_density")
    if digit_count > max(cyrillic_count + latin_count, 1) * 1.5:
        reasons.append("digit_heavy")

    score = (
        min(char_count / 600, 1.0) * 0.55
        + min(word_count / 120, 1.0) * 0.20
        + min((cyrillic_count + latin_count) / 350, 1.0) * 0.25
    )
    if "digit_heavy" in reasons:
        score *= 0.75

    return round(min(score, 1.0), 3), reasons


def _quality_label(score: float) -> Literal["high", "medium", "low"]:
    if score >= 0.72:
        return "high"
    if score >= settings.PARSER_MIN_DOCUMENT_QUALITY_SCORE:
        return "medium"
    return "low"


@lru_cache(maxsize=1)
def _get_ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:  # pragma: no cover - dependency boundary
        raise DocumentParsingError(
            "OCR dependencies are missing. Install `rapidocr_onnxruntime`, `pypdfium2`, and `pillow`."
        ) from exc
    return RapidOCR()


def _render_page_for_ocr(pdf_document, page_index: int):
    try:
        page = pdf_document[page_index]
        bitmap = page.render(scale=settings.OCR_RENDER_SCALE)
        return bitmap.to_numpy()
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(f"OCR rendering failed for page {page_index + 1}: {exc}") from exc


def _extract_ocr_text(pdf_document, page_index: int) -> str:
    image = _render_page_for_ocr(pdf_document, page_index)
    engine = _get_ocr_engine()
    try:
        result, _ = engine(image)
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(f"OCR failed for page {page_index + 1}: {exc}") from exc

    if not result:
        return ""
    return "\n".join(item[1] for item in result if len(item) >= 2 and item[1]).strip()


def _read_pdf(pdf_path: Path):
    try:
        return PdfReader(str(pdf_path))
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(str(exc)) from exc


def _open_pdf_for_rendering(pdf_path: Path):
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - dependency boundary
        raise DocumentParsingError(
            "PDF rendering dependencies are missing. Install `pypdfium2`."
        ) from exc

    try:
        return pdfium.PdfDocument(str(pdf_path))
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(f"Could not open PDF for OCR rendering: {exc}") from exc


def _choose_best_page_text(
    *,
    pdf_document,
    page,
    page_index: int,
) -> tuple[str, PageParsingResult]:
    raw_text = _extract_page_text(page)
    normalized_text = _normalize_text(raw_text)
    text_score, text_reasons = _assess_text_quality(normalized_text)

    chosen_text = normalized_text
    chosen_score = text_score
    chosen_reasons = list(text_reasons)
    method: Literal["text", "ocr", "mixed"] = "text"

    needs_ocr = text_score < settings.PARSER_MIN_PAGE_QUALITY_SCORE
    if needs_ocr:
        ocr_raw_text = _extract_ocr_text(pdf_document, page_index)
        normalized_ocr_text = _normalize_text(ocr_raw_text)
        ocr_score, ocr_reasons = _assess_text_quality(normalized_ocr_text)

        if normalized_text and normalized_ocr_text:
            combined_text = _normalize_text(f"{normalized_text}\n{normalized_ocr_text}")
            combined_score, combined_reasons = _assess_text_quality(combined_text)
        else:
            combined_text = normalized_ocr_text or normalized_text
            combined_score = max(text_score, ocr_score)
            combined_reasons = ocr_reasons if normalized_ocr_text else text_reasons

        candidates = [
            ("text", normalized_text, text_score, text_reasons),
            ("ocr", normalized_ocr_text, ocr_score, ocr_reasons),
            ("mixed", combined_text, combined_score, combined_reasons),
        ]
        method, chosen_text, chosen_score, chosen_reasons = max(
            candidates,
            key=lambda item: (item[2], len(item[1] or "")),
        )

    if not chosen_text:
        chosen_text = "_No extractable text found on this page._"

    return chosen_text, PageParsingResult(
        page_number=page_index + 1,
        extraction_method=method,
        quality_score=chosen_score,
        quality_label=_quality_label(chosen_score),
        raw_text_chars=len(raw_text),
        normalized_text_chars=len(chosen_text.replace("_No extractable text found on this page._", "")),
        low_quality_reasons=chosen_reasons,
    )


def _build_markdown_and_metadata(pdf_path: Path) -> tuple[str, ParsingMetadata]:
    reader = _read_pdf(pdf_path)
    render_pdf = _open_pdf_for_rendering(pdf_path)

    sections: list[str] = []
    page_results: list[PageParsingResult] = []

    for page_index, page in enumerate(reader.pages):
        page_text, page_result = _choose_best_page_text(
            pdf_document=render_pdf,
            page=page,
            page_index=page_index,
        )
        sections.append(f"## Page {page_index + 1}\n\n{page_text}")
        page_results.append(page_result)

    markdown = "\n\n".join(sections).strip()
    total_text_chars = sum(page.normalized_text_chars for page in page_results)
    usable_pages = [page for page in page_results if page.quality_score >= settings.PARSER_MIN_PAGE_QUALITY_SCORE]
    quality_score = round(mean(page.quality_score for page in page_results), 3) if page_results else 0.0
    page_methods = {page.extraction_method for page in page_results}
    extraction_method: Literal["text", "ocr", "mixed"]
    if len(page_methods) == 1:
        extraction_method = next(iter(page_methods))
    else:
        extraction_method = "mixed"

    metadata = ParsingMetadata(
        extraction_method=extraction_method,
        quality_score=quality_score,
        quality_label=_quality_label(quality_score),
        page_count=len(page_results),
        usable_page_count=len(usable_pages),
        low_quality_page_count=len(page_results) - len(usable_pages),
        total_text_chars=total_text_chars,
        pages=page_results,
    )

    if total_text_chars < settings.PARSER_MIN_DOCUMENT_TEXT_CHARS:
        raise DocumentParsingError("PDF parsing produced no usable text after OCR fallback")
    if metadata.quality_score < settings.PARSER_MIN_DOCUMENT_QUALITY_SCORE and not usable_pages:
        raise DocumentParsingError("PDF parsing quality is too low for reliable extraction")
    if not markdown:
        raise DocumentParsingError("PDF parsing produced no markdown output")

    return markdown, metadata


def _write_markdown_artifact(pdf_path: Path, markdown: str) -> Path:
    artifact_path = resolve_markdown_artifact_path(pdf_path)
    artifact_path.write_text(markdown, encoding="utf-8")
    return artifact_path


def _write_metadata_artifact(pdf_path: Path, metadata: ParsingMetadata) -> Path:
    metadata_path = resolve_parsing_metadata_artifact_path(pdf_path)
    metadata_path.write_text(json.dumps(asdict(metadata), ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata_path


def resolve_markdown_artifact_path(pdf_path: str | Path) -> Path:
    artifact_root = Path(settings.PARSED_MARKDOWN_DIR)
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root / f"{Path(pdf_path).stem}.md"


def resolve_parsing_metadata_artifact_path(pdf_path: str | Path) -> Path:
    artifact_root = Path(settings.PARSED_MARKDOWN_DIR)
    artifact_root.mkdir(parents=True, exist_ok=True)
    return artifact_root / f"{Path(pdf_path).stem}.parse.json"


def read_parsing_metadata(metadata_path: str | Path | None) -> dict | None:
    if not metadata_path:
        return None

    resolved_path = Path(metadata_path)
    if not resolved_path.exists():
        return None

    try:
        return json.loads(resolved_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(f"Could not read parsing metadata: {exc}") from exc


def parse_pdf_to_markdown(pdf_path: str | Path) -> ParsedDocument:
    resolved_path = Path(pdf_path)
    if not resolved_path.exists():
        raise DocumentParsingError(f"PDF file does not exist: {resolved_path}")

    markdown, metadata = _build_markdown_and_metadata(resolved_path)
    artifact_path = _write_markdown_artifact(resolved_path, markdown)
    metadata_path = _write_metadata_artifact(resolved_path, metadata)

    return ParsedDocument(
        markdown=markdown,
        artifact_path=str(artifact_path),
        metadata_path=str(metadata_path),
        extraction_method=metadata.extraction_method,
        quality_score=metadata.quality_score,
        quality_label=metadata.quality_label,
    )
