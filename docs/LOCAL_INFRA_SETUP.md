# Local Infrastructure Setup

This project supports two local modes:

1. Docker Compose
2. Non-Docker local run

Use Docker Compose when you want the full stack in containers.
Use the non-Docker path when you want to run `api-service`, `worker-service`, and optionally `frontend-service` directly on your machine.

---

## Docker Compose Mode

Docker Compose uses:

- `api-service/.env.docker`
- `worker-service/.env.docker`

### Main Command

Start the full local stack from the repo root:

```bash
docker compose up --build
```

Stop it and remove disposable data:

```bash
docker compose down -v
```

---

### Docker Connection Values

Recommended local values across the Docker env files:

- PostgreSQL host: `localhost`
- PostgreSQL port: `5432`
- PostgreSQL database: `task_flow`
- PostgreSQL user: `yakir`
- PostgreSQL password: empty
- RabbitMQ URL: `amqp://guest:guest@localhost:5672/`
- Redis URL: `redis://localhost:6379/0`
- S3 bucket: `task-flow`
- S3 endpoint: `http://localhost:9000`
- S3 region: `us-east-1`
- S3 access key: `minioadmin`
- S3 secret key: `minioadmin`
- S3 force path style: `true`
- S3 auto create bucket: `true`

---

### Exposed Ports

- App and API: `8000`
- Worker health: `8001`
- PostgreSQL: `5432`
- RabbitMQ: `5672`
- RabbitMQ management: `15672`
- Redis: `6379`
- MinIO API: `9000`
- MinIO console: `9001`

---

### Docker Services

The stack includes these services:

- `postgres`
- `redis`
- `rabbitmq`
- `minio`
- `api-migrate`
- `api-service`
- `worker-service`

`api-migrate` runs Alembic migrations before the API and worker start.

---

### Docker Env Files

The Docker stack does not use the normal local `.env` files. It uses:

- `api-service/.env.docker`
- `worker-service/.env.docker`

These use Docker service names such as `postgres`, `redis`, `rabbitmq`, and `minio` instead of `localhost`.

---

### MinIO

MinIO is included in the main Compose stack, so you do not need the separate MinIO-only Compose file for the main local workflow.

Default local credentials in Docker:

- access key: `minioadmin`
- secret key: `minioadmin`

The API and worker use these Docker-local object storage values:

```env
S3_ENDPOINT=http://minio:9000
S3_REGION=us-east-1
S3_BUCKET=task-flow
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_USE_SSL=false
S3_FORCE_PATH_STYLE=true
S3_AUTO_CREATE_BUCKET=true
```

The services can auto-create the local bucket on startup when `S3_AUTO_CREATE_BUCKET=true`.

---

### UI

The Docker local workflow serves the built UI from `api-service`. Open:

```text
http://localhost:8000
```

The standalone `frontend-service` dev server is no longer the main local workflow.

---

---

## Non-Docker Local Mode

Non-Docker local mode uses:

- `api-service/.env`
- `worker-service/.env`
- `frontend-service/.env`

### Non-Docker Infra

You can run the infra locally outside Docker.

PostgreSQL with Homebrew:

```bash
brew services start postgresql@16
```

RabbitMQ with Homebrew:

```bash
brew services start rabbitmq
```

Redis with Homebrew:

```bash
brew services start redis
```

For MinIO, you can either:

1. run the native MinIO binary on your machine
2. use the small MinIO-only Compose file:

```bash
docker compose -f docker-compose.minio.yml up -d
```

If you want a truly no-Docker path, use the native MinIO binary and point:

```env
S3_ENDPOINT=http://localhost:9000
```

in both `api-service/.env` and `worker-service/.env`.

### Non-Docker App Processes

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

### Non-Docker UI Options

Option A: run the frontend dev server

```bash
cd frontend-service
npm install
npm run dev
```

Option B: build the UI into the API and serve it from `api-service`

```bash
./scripts/build_frontend_for_api.sh
```

This build path forces `VITE_API_BASE_URL` to be empty so the bundled UI uses the same origin as the `api-service` serving the page.

Then open:

```text
http://localhost:8000
```

### Summary

Supported local options are now:

- Docker Compose: everything in containers
- Non-Docker: services on your machine, infra local, UI either Vite dev server or API-served build
