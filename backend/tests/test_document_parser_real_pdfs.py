from pathlib import Path

import pytest

from app.services.document_parser import parse_pdf_to_markdown, read_parsing_metadata


SAMPLE_PDFS = [
    Path("/Users/2madeira/DEV/test_files/Единый_оператор_мероприятий_Парк_Отель_Основной_Договор_№21_05_24.pdf"),
    Path("/Users/2madeira/DEV/test_files/Единый_оператор_мероприятий_Гостиница_Славянка_Договор_на_оказание.pdf"),
    Path("/Users/2madeira/DEV/test_files/Единый_оператор_мероприятий_ГБУЗ_СО_ССМП_Капинос_Заказ_поставщику.pdf"),
    Path("/Users/2madeira/DEV/test_files/Единый_оператор_мероприятий_Арбузов_Роман_Игоревич_договор_Договор.pdf"),
    Path("/Users/2madeira/DEV/test_files/ЕВЕРГРИН_ИВЕНТС_Тукарев_Павел_Юрьевич_самозанятый_Планируемый_расход.pdf"),
    Path("/Users/2madeira/DEV/test_files/ЕВЕРГРИН_ИВЕНТС_ПЕТРУШИН_АЛЕКСЕЙ_ВАЛЕРЬЕВИЧ_самозанятый_Заказ_поставщику.pdf"),
]


@pytest.mark.integration
@pytest.mark.parametrize("pdf_path", SAMPLE_PDFS, ids=lambda path: path.stem[:40])
def test_parser_extracts_meaningful_markdown_from_real_sample_pdfs(tmp_path, monkeypatch, pdf_path):
    if not pdf_path.exists():
        pytest.skip(f"sample PDF is missing: {pdf_path}")

    from app.core.config import settings

    artifact_root = tmp_path / "artifacts"
    monkeypatch.setattr(settings, "PARSED_MARKDOWN_DIR", str(artifact_root))

    parsed = parse_pdf_to_markdown(pdf_path)
    metadata = read_parsing_metadata(parsed.metadata_path)

    assert Path(parsed.artifact_path).exists()
    assert Path(parsed.metadata_path).exists()
    assert len(parsed.markdown) > 600
    assert "## Page 1" in parsed.markdown
    assert parsed.quality_score >= 0.35
    assert parsed.extraction_method in {"ocr", "mixed", "text"}
    assert metadata is not None
    assert metadata["total_text_chars"] > 300
    assert metadata["usable_page_count"] >= 1
    assert metadata["quality_label"] in {"high", "medium"}
    assert "Передан через Диадок" not in parsed.markdown[:300]
