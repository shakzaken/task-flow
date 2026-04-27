# Local Infrastructure Setup

This document explains the Docker Compose local stack for this project. It runs PostgreSQL, RabbitMQ, Redis, MinIO, the migration job, the API service, and the worker service together.

The Docker Compose stack uses:

- `api-service/.env.docker`
- `worker-service/.env.docker`

---

## Main Command

Start the full local stack from the repo root:

```bash
docker compose up --build
```

Stop it and remove disposable data:

```bash
docker compose down -v
```

---

## Docker Connection Values

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

## Exposed Ports

- App and API: `8000`
- Worker health: `8001`
- PostgreSQL: `5432`
- RabbitMQ: `5672`
- RabbitMQ management: `15672`
- Redis: `6379`
- MinIO API: `9000`
- MinIO console: `9001`

---

## Docker Services

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

## Docker Env Files

The Docker stack does not use the normal local `.env` files. It uses:

- `api-service/.env.docker`
- `worker-service/.env.docker`

These use Docker service names such as `postgres`, `redis`, `rabbitmq`, and `minio` instead of `localhost`.

---

## MinIO

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

## UI

The Docker local workflow serves the built UI from `api-service`. Open:

```text
http://localhost:8000
```

The standalone `frontend-service` dev server is no longer the main local workflow.

---

## Alternative Manual Setup

If you want to run infrastructure manually with Homebrew instead, you can still do that, but Docker Compose is now the recommended path.

Check the installed PostgreSQL service name:

```bash
brew services list
```
