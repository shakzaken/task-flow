from __future__ import annotations

from uuid import UUID

from PIL import Image

from app.schemas import ResizeImagePayload
from app.services.storage import StorageService


def handle_resize_image(
    task_id: UUID,
    payload: ResizeImagePayload,
    storage: StorageService,
) -> dict[str, str]:
    with storage.task_workspace(task_id) as workspace:
        try:
            input_path = storage.download_to_path(payload.image_path, workspace / "input-image")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Input image does not exist: {payload.image_path}") from exc
        output_relative_path = storage.build_output_relative_path(task_id, payload.image_path)
        output_path = workspace / f"output{input_path.suffix or '.jpg'}"

        with Image.open(input_path) as image:
            resized = image.resize((payload.width, payload.height))
            save_format = image.format or None
            resized.save(output_path, format=save_format)

        storage.upload_file(output_path, output_relative_path)
        return {"output_path": output_relative_path}
