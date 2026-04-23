# Local Infrastructure Setup

This document explains how to run PostgreSQL, RabbitMQ, Redis, and MinIO locally for this project.

The connection values used by the project now live in service-specific env files:

- `api-service/.env`
- `worker-service/.env`
- `frontend-service/.env`

---

## Current Connection Values

Recommended local values across the service env files:

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

## Start PostgreSQL With Brew

If you installed PostgreSQL with Homebrew, the exact formula name may be versioned, for example `postgresql@16`.

Check the installed service name:

```bash
brew services list
```

Start PostgreSQL:

```bash
brew services start <your-postgres-formula>
```

Examples:

```bash
brew services start postgresql@16
brew services start postgresql@15
```

Verify it is running:

```bash
brew services list
pg_isready -h localhost -p 5432
```

---

## Create The PostgreSQL User And Database

The local service env files assume this database setup:

- database: `task_flow`
- user: `yakir`
- password: empty

One simple way to create them:

```bash
psql postgres
```

Then run:

```sql
CREATE DATABASE task_flow OWNER yakir;
```

Exit with:

```sql
\q
```

If you change these values, update both `api-service/.env` and `worker-service/.env` to match.

---

## Start RabbitMQ With Brew

Start RabbitMQ:

```bash
brew services start rabbitmq
```

Verify it is running:

```bash
brew services list
```

The local service env files expect:

- host: `localhost`
- port: `5672`
- username: `guest`
- password: `guest`

That matches the default local RabbitMQ setup in many Homebrew installs.

---

## Start Redis With Brew

Start Redis:

```bash
brew services start redis
```

Verify it is running:

```bash
brew services list
redis-cli ping
```

The local service env files expect:

- Redis URL: `redis://localhost:6379/0`
- host: `localhost`
- port: `6379`
- database: `0`

If `redis-cli ping` returns `PONG`, Redis is running and reachable on the expected local address.

---

## Start MinIO With Docker

The app now uses S3-compatible object storage instead of the shared local filesystem. For local development, run MinIO:

```bash
docker compose -f docker-compose.minio.yml up -d
```

This starts:

- S3 API on `http://localhost:9000`
- MinIO console on `http://localhost:9001`

Default local credentials in [docker-compose.minio.yml](/Users/yakir/projects/claude/task-flow/docker-compose.minio.yml):

- access key: `minioadmin`
- secret key: `minioadmin`

Recommended values for both `api-service/.env` and `worker-service/.env` for local object storage:

```env
S3_ENDPOINT=http://localhost:9000
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

## Stop Services

Stop PostgreSQL:

```bash
brew services stop <your-postgres-formula>
```

Stop RabbitMQ:

```bash
brew services stop rabbitmq
```

Stop Redis:

```bash
brew services stop redis
```

Stop MinIO:

```bash
docker compose -f docker-compose.minio.yml down
```

---

## Notes

- `api-service` and `worker-service` should each read from their own `.env` file.
- Redis connection values should be set in both `api-service/.env` and `worker-service/.env` when both services need them.
- `api-service` and `worker-service` should use the same S3-compatible storage settings in their own `.env` files.
- If you later move these services into separate Docker containers, keep the service-specific environment values aligned with the same connection contract.
- Local development now uses MinIO as the object storage backend instead of a shared filesystem path.
