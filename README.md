# Task Flow

Task Flow is an asynchronous task-processing application built around a FastAPI `api-service` and a React/Vite `frontend-service`. The API accepts task creation and upload requests, persists task state in PostgreSQL, publishes background work to RabbitMQ, and serves task status for the UI, while the frontend submits `send_email` and `resize_image` jobs and polls for status updates. The wider project design also includes Redis for coordination and a `worker-service` for background execution, with shared filesystem storage for file-based task inputs and outputs.

Before running the application, create the `task_flow` PostgreSQL database in Postgres.

Configure each service with its own `.env` file before starting the services:

- `api-service/.env`
- `worker-service/.env`
- `frontend-service/.env`

The API and worker should use the same S3-compatible storage settings. For local development, point both of them at MinIO.

Then start the local infrastructure expected by those service env files:

- PostgreSQL
- RabbitMQ
- Redis

Run the API service in one terminal:

```bash
cd api-service
UV_CACHE_DIR=.uv-cache uv sync --dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the frontend service in another terminal:

```bash
cd frontend-service
npm install
npm run dev
```

The frontend uses `http://localhost:8000` by default through `VITE_API_BASE_URL`.

The project docs also describe a `worker-service` as part of the target architecture, but that service directory is not present in this checkout.
