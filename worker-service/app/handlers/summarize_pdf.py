from __future__ import annotations

from pathlib import Path
from uuid import UUID

from pypdf import PdfReader
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.schemas import SummarizePdfPayload
from app.services.pdf_summary import PdfSummaryService
from app.services.storage import StorageService


def handle_summarize_pdf(
    task_id: UUID,
    payload: SummarizePdfPayload,
    storage: StorageService,
    pdf_summary_service: PdfSummaryService,
) -> dict[str, int | str]:
    input_path = storage.resolve_relative_path(payload.pdf_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input PDF does not exist: {payload.pdf_path}")

    reader = PdfReader(str(input_path))
    extracted_pages = [(page.extract_text() or "").strip() for page in reader.pages]
    document_text = "\n\n".join(text for text in extracted_pages if text)
    if not document_text.strip():
        raise RuntimeError("The PDF did not contain extractable text.")

    summary_result = pdf_summary_service.summarize_document(document_text)
    summary_text = summary_result["summary"]

    output_relative_path = storage.build_output_relative_path(task_id, payload.pdf_path)
    output_path = storage.resolve_relative_path(output_relative_path)
    storage.ensure_parent_directory(output_path)
    _write_summary_pdf(
        output_path=output_path,
        title=input_path.name,
        summary_text=summary_text,
    )

    return {
        "output_path": output_relative_path,
        "page_count": len(reader.pages),
        "summary_model": summary_result["model"],
    }


def _write_summary_pdf(output_path: Path, title: str, summary_text: str) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=LETTER)
    width, height = LETTER
    margin = 56
    y = height - margin

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, y, "PDF Summary")
    y -= 24

    pdf.setFont("Helvetica", 11)
    for line in _wrap_text(f"Source: {title}", width - (margin * 2), "Helvetica", 11):
        pdf.drawString(margin, y, line)
        y -= 16

    y -= 8
    for raw_line in summary_text.splitlines():
        lines = _wrap_text(raw_line or " ", width - (margin * 2), "Helvetica", 11)
        for line in lines:
            if y <= margin:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y = height - margin
            pdf.drawString(margin, y, line)
            y -= 16
        y -= 4

    pdf.save()


def _wrap_text(text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current_line = words[0]
    for word in words[1:]:
        candidate = f"{current_line} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines
