from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.uploads import router as uploads_router


def create_app() -> FastAPI:
    app = FastAPI(title="Task Flow API Service", version="0.1.0")
    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(uploads_router)
    return app


app = create_app()

