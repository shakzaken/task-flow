from __future__ import annotations

from uuid import UUID

from pypdf import PdfReader, PdfWriter

from app.schemas import MergePdfsPayload
from app.services.storage import StorageService


def handle_merge_pdfs(
    task_id: UUID,
    payload: MergePdfsPayload,
    storage: StorageService,
) -> dict[str, int | str]:
    with storage.task_workspace(task_id) as workspace:
        try:
            first_input_path = storage.download_to_path(payload.first_pdf_path, workspace / "input-1.pdf")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"First input PDF does not exist: {payload.first_pdf_path}") from exc
        try:
            second_input_path = storage.download_to_path(payload.second_pdf_path, workspace / "input-2.pdf")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Second input PDF does not exist: {payload.second_pdf_path}") from exc

        writer = PdfWriter()

        for input_path in (first_input_path, second_input_path):
            reader = PdfReader(str(input_path))
            for page in reader.pages:
                writer.add_page(page)

        output_relative_path = storage.build_output_relative_path(task_id, payload.first_pdf_path)
        output_path = workspace / "output.pdf"

        with output_path.open("wb") as output_file:
            writer.write(output_file)

        storage.upload_file(output_path, output_relative_path, content_type="application/pdf")
        return {
            "output_path": output_relative_path,
            "page_count": len(writer.pages),
        }
