from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse


DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
API_PREFIXES = {"artifacts", "health", "tasks", "uploads"}

router = APIRouter(tags=["frontend"])


@router.get("/", include_in_schema=False)
async def serve_frontend_index(request: Request) -> FileResponse:
    return _index_response(_static_dir(request))


@router.get("/{relative_path:path}", include_in_schema=False)
async def serve_frontend_path(relative_path: str, request: Request) -> FileResponse:
    first_segment = relative_path.split("/", 1)[0]
    if first_segment in API_PREFIXES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")

    static_dir = _static_dir(request)
    if relative_path.startswith("assets/"):
        asset_path = _safe_static_path(static_dir, relative_path)
        if asset_path.is_file():
            return FileResponse(asset_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Static asset was not found.")

    return _index_response(static_dir)


def _static_dir(request: Request) -> Path:
    return getattr(request.app.state, "frontend_static_dir", DEFAULT_STATIC_DIR)


def _index_response(static_dir: Path) -> FileResponse:
    index_path = static_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend build was not found. Run scripts/build_frontend_for_api.sh first.",
        )
    return FileResponse(index_path, media_type="text/html")


def _safe_static_path(static_dir: Path, relative_path: str) -> Path:
    candidate = (static_dir / relative_path).resolve()
    root = static_dir.resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Static asset was not found.")
    return candidate
