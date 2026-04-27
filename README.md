# Task Flow

Task Flow is an asynchronous task-processing application built around a FastAPI `api-service`, a background `worker-service`, and a React/Vite `frontend-service`. The API accepts task creation and upload requests, persists task state in PostgreSQL, publishes background work to RabbitMQ, and serves task status for the UI. The worker executes background tasks and stores file inputs/outputs in S3-compatible object storage. Local development uses MinIO for object storage.

## Local Workflow Options

You have two supported local development options:

1. Full Docker Compose stack
2. Non-Docker local run with service processes on your machine

Docker-specific env files:

- `api-service/.env.docker`
- `worker-service/.env.docker`

Start the full stack from the repo root:

```bash
docker compose up --build
```

Main endpoints:

- App and API: `http://localhost:8000`
- Worker health: `http://localhost:8001/health`
- RabbitMQ management: `http://localhost:15672`
- MinIO console: `http://localhost:9001`

The Compose stack includes:

- PostgreSQL
- Redis
- RabbitMQ
- MinIO
- `api-migrate`
- `api-service`
- `worker-service`

To stop and remove the disposable local data:

```bash
docker compose down -v
```

## Non-Docker Local Workflow

If you want to run the application without Docker, use the normal service-local `.env` files:

- `api-service/.env`
- `worker-service/.env`
- `frontend-service/.env`

For non-Docker local infra, see [docs/LOCAL_INFRA_SETUP.md](/Users/yakir/projects/claude/task-flow/docs/LOCAL_INFRA_SETUP.md).

Run the API:

```bash
cd api-service
UV_CACHE_DIR=.uv-cache uv sync --dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run the worker:

```bash
cd worker-service
UV_CACHE_DIR=.uv-cache uv sync --dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

For the UI, you have two non-Docker choices.

Option A: run the frontend dev server

```bash
cd frontend-service
npm install
npm run dev
```

Option B: build the frontend into `api-service` and let the API serve it

```bash
./scripts/build_frontend_for_api.sh
```

That script forces a same-origin frontend build, so the bundled UI talks to whichever `api-service` host served the page instead of hardcoding `http://localhost:8000`.

Then open:

```text
http://localhost:8000
```

This means both local workflows are supported:

- Docker Compose: full app and infra in containers
- Non-Docker: app services on your machine with local infra and service-local env files
