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
    input_path = storage.resolve_relative_path(payload.image_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input image does not exist: {payload.image_path}")

    output_relative_path = storage.build_output_relative_path(task_id, payload.image_path)
    output_path = storage.resolve_relative_path(output_relative_path)
    storage.ensure_parent_directory(output_path)

    with Image.open(input_path) as image:
        resized = image.resize((payload.width, payload.height))
        save_format = image.format or None
        resized.save(output_path, format=save_format)

    return {"output_path": output_relative_path}
