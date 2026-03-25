# API Service Plan

This document defines the Phase 1 plan for the `api` service.

The API service is a FastAPI application responsible for receiving task creation requests, validating input, saving tasks in PostgreSQL, and publishing task messages to RabbitMQ.

---

## Purpose

The API service is the entry point for the system.

Its responsibilities are:

- receive requests from the UI
- validate task input
- persist tasks in PostgreSQL
- publish tasks to RabbitMQ
- expose task status endpoints
- expose a health endpoint

Out of scope for this service:

- executing task business logic
- long-running background processing
- direct image resizing
- direct email sending

---

## Phase 1 Scope

Supported task types:

- `resize_image`
- `send_email`

Required endpoints:

- `POST /tasks`
- `GET /tasks/{task_id}`
- `GET /health`
- `POST /uploads`

---

## Request Flow

1. for `resize_image`, UI uploads the file with `POST /uploads`
2. API stores the file in a temporary local path
3. UI sends `POST /tasks` with the uploaded file reference in the payload
4. API validates `task_type` and `payload`
5. API moves or attaches the uploaded file into a task-owned path
6. API creates a row in `tasks`
7. API publishes a message to RabbitMQ
8. API returns `202 Accepted` with `task_id`
9. UI polls `GET /tasks/{task_id}` for status updates

Core rule:

- the task must be stored in PostgreSQL before publishing to RabbitMQ
- uploaded files for `resize_image` should be stored as temporary uploads before task creation

---

## API Design

### `POST /tasks`

Request:

```json
{
  "task_type": "send_email",
  "payload": {
    "to": "user@example.com",
    "subject": "Welcome",
    "body": "Hello"
  }
}
```

Response:

```json
{
  "task_id": "uuid",
  "status": "PENDING"
}
```

Status code:

- `202 Accepted`

Validation rules:

- `task_type` must be supported
- `payload` must match the schema for the selected task type
- invalid requests return `400` or `422`

### `GET /tasks/{task_id}`

Response:

```json
{
  "id": "uuid",
  "type": "send_email",
  "status": "PENDING",
  "payload": {},
  "result": null,
  "error_message": null,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

Possible statuses:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

### `GET /health`

Response:

```json
{
  "status": "ok"
}
```

### `POST /uploads`

Responsibilities:

- accept multipart file upload
- store the file on the local filesystem under a temporary upload path such as `uploads/tmp/...`
- return a temporary upload reference for use in `POST /tasks`

Phase 1 upload rule:

- `POST /uploads` is the required upload flow for `resize_image`
- `POST /tasks` should not accept raw file content

### Upload Lifecycle

Recommended file lifecycle:

1. `POST /uploads` stores a file under a temporary path such as `uploads/tmp/<upload_id>.<ext>`
2. `POST /tasks` for `resize_image` receives that temporary upload reference
3. during task creation, the API moves or attaches the file to a task-owned path such as `uploads/tasks/<task_id>/input.<ext>`
4. the worker reads the task-owned file path from the task payload

Orphan upload handling:

- temporary uploads that are never attached to a task are allowed to exist briefly
- a cleanup job should delete stale files from `uploads/tmp/` after a TTL

---

## Data Model

### `tasks` Table

Suggested columns:

- `id` UUID primary key
- `type` text not null
- `status` text not null
- `payload` JSONB not null
- `result` JSONB null
- `error_message` text null
- `created_at` timestamptz not null
- `updated_at` timestamptz not null

Suggested indexes:

- `id`
- `status`
- `created_at`

Status semantics:

- `PENDING`: created and waiting for worker pickup
- `PROCESSING`: worker started execution
- `COMPLETED`: task finished successfully
- `FAILED`: task ended with error

---

## RabbitMQ Publishing Design

### Exchange and Queue

- exchange: `tasks`
- queue: `tasks.phase1`
- routing key: `task.created`

### Message Payload

```json
{
  "task_id": "uuid",
  "task_type": "send_email"
}
```

Design rule:

- keep queue messages small
- PostgreSQL is the source of truth
- worker should re-read full task details from the DB

### Failure Behavior

- if DB insert fails, return `500`
- if publish fails after DB insert, return `500` and log the failure clearly

Phase 1 note:

- this publish failure edge case is acceptable in MVP, but must be documented for later reliability work

---

## Suggested Project Structure

```text
services/api/
  app/
    api/
      routes/
        tasks.py
        health.py
        uploads.py
    core/
      config.py
    db/
      base.py
      session.py
      models/
        task.py
    schemas/
      task.py
      upload.py
    services/
      task_service.py
      publisher.py
      storage.py
    main.py
  migrations/
  tests/
  Dockerfile
  pyproject.toml
```

### Module Responsibilities

- `routes/tasks.py`: task endpoints
- `routes/health.py`: health checks
- `routes/uploads.py`: required upload flow for `resize_image`
- `schemas/task.py`: Pydantic request and response models
- `models/task.py`: SQLAlchemy task model
- `services/task_service.py`: DB operations, upload attachment, and orchestration
- `services/publisher.py`: RabbitMQ integration
- `services/storage.py`: file storage abstraction for temporary uploads and task-owned files

---

## Implementation Details

### Validation

Use Pydantic models to validate:

- base task request
- task-specific payload shape

Recommended approach:

- define one payload model per task type
- map `task_type` to payload schema
- reject mismatched payloads early

### Persistence

Recommended stack:

- FastAPI
- SQLAlchemy
- Alembic
- psycopg

Persistence flow:

1. create UUID
2. insert task row with `PENDING`
3. commit transaction
4. publish RabbitMQ message
5. return response

### Storage

Recommendation for Phase 1:

- use local filesystem storage
- keep storage access behind `services/storage.py` so MinIO can replace it later without changing route or task logic
- store uploaded files first in a temporary directory such as `uploads/tmp/`
- move or attach files into a task-owned path during `POST /tasks`
- add TTL-based cleanup for temporary uploads that were never attached to a task

---

## Environment Variables

- `API_PORT`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `RABBITMQ_URL`
- `STORAGE_MODE`
- `LOCAL_STORAGE_PATH`
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`

---

## Testing Plan

Required tests:

- create valid `send_email` task
- create valid `resize_image` task
- reject unsupported `task_type`
- reject invalid payload shape
- fetch existing task
- return `404` for missing task
- verify task row is created before publish logic completes

Optional tests:

- upload file and return storage path
- move a temporary upload into a task-owned path during task creation
- delete stale files from the temporary upload directory after TTL

---

## Future Follow-Up

- migrate `services/storage.py` from local filesystem storage to MinIO while preserving the API contract used by uploads and task creation

---

## Acceptance Criteria

- `POST /tasks` creates a task and returns `task_id`
- `POST /uploads` stores `resize_image` inputs in a temporary local path
- task creation moves or attaches uploaded files into a task-owned path
- task is stored in PostgreSQL with `PENDING` status
- message is published to RabbitMQ
- `GET /tasks/{task_id}` returns the correct task state
- API remains thin and does not execute task logic itself

---

## Implementation Order

1. bootstrap FastAPI project
2. configure PostgreSQL connection and migrations
3. create `tasks` table and ORM model
4. implement request and response schemas
5. implement `POST /tasks`
6. implement RabbitMQ publisher
7. implement `GET /tasks/{task_id}`
8. implement `GET /health`
9. implement `POST /uploads`
10. attach or move temporary uploads during task creation
11. add temporary upload cleanup
12. add tests
