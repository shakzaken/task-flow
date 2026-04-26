# Task Flow

Task Flow is an asynchronous task-processing application built around a FastAPI `api-service`, a background `worker-service`, and a React/Vite `frontend-service`. The API accepts task creation and upload requests, persists task state in PostgreSQL, publishes background work to RabbitMQ, and serves task status for the UI. The worker executes background tasks and stores file inputs/outputs in S3-compatible object storage. Local development uses MinIO for object storage.

## Main Local Workflow

The main local workflow now runs the full stack with Docker Compose.

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

If you want to run services directly on your machine instead of Docker, use the service-local `.env` files:

- `api-service/.env`
- `worker-service/.env`
- `frontend-service/.env`

To build the frontend into the API service for a single deployable HTTP service, run from the repo root:

```bash
./scripts/build_frontend_for_api.sh
```
