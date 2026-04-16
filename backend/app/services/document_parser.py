from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from app.core.config import settings


@dataclass(slots=True)
class ParsedDocument:
    markdown: str
    artifact_path: str


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


def _build_markdown(pdf_path: Path) -> str:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # pragma: no cover - defensive library boundary
        raise DocumentParsingError(str(exc)) from exc

    sections: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        page_text = _extract_page_text(page)
        if not page_text:
            page_text = "_No extractable text found on this page._"
        sections.append(f"## Page {page_index}\n\n{page_text}")

    markdown = "\n\n".join(sections).strip()
    if not markdown:
        raise DocumentParsingError("PDF parsing produced no markdown output")
    return markdown


def _write_markdown_artifact(pdf_path: Path, markdown: str) -> Path:
    artifact_root = Path(settings.PARSED_MARKDOWN_DIR)
    artifact_root.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_root / f"{pdf_path.stem}.md"
    artifact_path.write_text(markdown, encoding="utf-8")
    return artifact_path


def parse_pdf_to_markdown(pdf_path: str | Path) -> ParsedDocument:
    """
    Use pypdf's layout extraction mode as the current repository baseline until
    DocLing is added to the runtime dependencies.
    """

    resolved_path = Path(pdf_path)
    if not resolved_path.exists():
        raise DocumentParsingError(f"PDF file does not exist: {resolved_path}")

    markdown = _build_markdown(resolved_path)
    artifact_path = _write_markdown_artifact(resolved_path, markdown)
    return ParsedDocument(markdown=markdown, artifact_path=str(artifact_path))
