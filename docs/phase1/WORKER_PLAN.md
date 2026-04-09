# Worker Service Plan

This document defines the Phase 1 plan for the `worker-service` service.

The worker service is responsible for consuming task messages from RabbitMQ, loading task data from PostgreSQL, executing task handlers, and updating task status.

---

## Purpose

The worker is the execution engine of the system.

Its responsibilities are:

- consume task messages from RabbitMQ
- load task details from PostgreSQL
- update task status
- dispatch work by task type
- store execution result or error
- expose a health endpoint if needed

Out of scope for this service:

- accepting user task creation requests
- owning API contracts for the UI
- being the source of truth for task state

Architecture rules for this service:

- keep persistence logic inside repository classes
- keep infrastructure and execution orchestration inside service classes
- keep handler classes or modules focused on task-specific business logic
- use explicit type hints and typed task payload models where practical
- inject repositories and services explicitly so worker flows stay testable
- use `uv` to manage Python dependencies for this service
- keep this service in its own virtual environment at `worker-service/.venv`
- keep dependencies isolated in this service's own `pyproject.toml`

---

## Phase 1 Scope

Supported task types:

- `resize_image`
- `send_email`

Phase 1 task statuses used by the worker:

- `PROCESSING`
- `COMPLETED`
- `FAILED`

The task is expected to already exist in PostgreSQL with status `PENDING` before the worker receives the queue message.

---

## Worker Flow

1. worker receives a RabbitMQ message
2. worker reads `task_id` and `task_type`
3. worker submits the task to a bounded thread pool
4. a worker thread loads the task row from PostgreSQL
5. the worker thread updates status to `PROCESSING`
6. the worker thread selects the correct task handler
7. the worker thread executes task logic
8. the worker thread writes `result` and status `COMPLETED` on success
9. the worker thread writes `error_message` and status `FAILED` on failure

Core rule:

- the worker should not trust RabbitMQ as the full source of task data and should read the full payload from PostgreSQL

---

## RabbitMQ Consumption Design

### Queue Setup

- exchange: `tasks`
- queue: `tasks.phase1`
- routing key: `task.created`

### Message Shape

```json
{
  "task_id": "uuid",
  "task_type": "resize_image"
}
```

### Consumption Rules

- use a bounded thread pool for task execution
- keep the consumer loop responsible for message intake and task submission only
- acknowledge the message only after task processing is complete
- if task execution fails, mark DB status as `FAILED`
- malformed messages should be rejected and logged

Phase 1 note:

- advanced retry handling and dead-letter queues are intentionally out of scope

---

## Task Handler Design

### `send_email`

Input payload example:

```json
{
  "to": "user@example.com",
  "subject": "Welcome",
  "body": "Hello"
}
```

Expected result:

```json
{
  "delivered": true
}
```

Implementation notes:

- use a fake email sender or mock provider in Phase 1
- isolate provider logic in a service class
- keep handler deterministic and easy to test

### `resize_image`

Input payload example:

```json
{
  "image_path": "uploads/tasks/<task_id>/input.jpg",
  "width": 300,
  "height": 200
}
```

Expected result:

```json
{
  "output_path": "outputs/<task_id>/output.jpg"
}
```

Implementation notes:

- use Pillow for image processing
- read from local filesystem storage
- expect the API to provide a task-owned file path, not a temporary upload path
- expect the stored `image_path` to be relative to a shared storage root
- write output to a deterministic task-specific path

Shared storage rule:

- `worker-service` must mount the same shared storage volume used by `api-service`
- the worker should resolve paths such as `uploads/tasks/<task_id>/input.jpg` against a shared root such as `/shared-data`
- the worker should not depend on API-container-only paths

---

## Suggested Project Structure

```text
worker-service/
  .venv/
  app/
    consumers/
      task_consumer.py
    core/
      config.py
    db/
      session.py
      models/
        task.py
      repositories/
        task_repository.py
    handlers/
      send_email.py
      resize_image.py
    services/
      task_executor.py
      storage.py
      email_sender.py
    api/
      routes/
        health.py
    main.py
  tests/
  Dockerfile
  pyproject.toml
  uv.lock
```

### Module Responsibilities

- `consumers/task_consumer.py`: RabbitMQ subscription and message handling
- `repositories/task_repository.py`: task lookup and status/result persistence
- `services/task_executor.py`: orchestration of status transitions, handler dispatch, and threaded task execution
- `handlers/send_email.py`: email task logic
- `handlers/resize_image.py`: image resize logic
- `services/storage.py`: storage abstraction
- `services/email_sender.py`: email provider abstraction
- `api/routes/health.py`: optional health endpoint
- `main.py`: application startup and thread-pool lifecycle

---

## Runtime Design

Phase 1 requires a thread-pool execution model.

Required runtime pattern:

- use a lightweight FastAPI app with `/health`
- start the consumer during application startup
- submit each accepted task to a bounded thread pool
- execute blocking task handlers inside worker threads
- keep thread-pool size configurable

Why this is required in Phase 1:

- it fits the current task mix without forcing a full async handler stack
- it works cleanly with blocking libraries used for image processing, filesystem access, and email sending
- it keeps the MVP easier to implement and reason about than an async execution model
- it still allows controlled parallel task execution

Phase 1 rules:

- do not implement task execution as a fully async per-task flow
- do not create an unbounded number of threads
- use explicit concurrency limits

---

## Database Interaction

The worker must update the existing `tasks` row.

Required fields touched by the worker:

- `status`
- `result`
- `error_message`
- `updated_at`

Status transition rules:

- `PENDING` -> `PROCESSING`
- `PROCESSING` -> `COMPLETED`
- `PROCESSING` -> `FAILED`

Recommended implementation:

- read current row by `task_id` through a repository
- fail safely if task does not exist
- commit after each meaningful state transition
- keep DB sessions scoped to the worker thread that is processing the task
- keep transition rules in the executor or a dedicated service, not in the repository

---

## Error Handling

### Processing Errors

If a handler raises an exception:

- capture a safe error message
- update task row to `FAILED`
- persist `error_message`

### Queue Errors

If the queue message is malformed:

- log it
- reject the message

### Data Errors

If the task row cannot be found:

- log the issue
- reject or acknowledge the message based on the chosen RabbitMQ client behavior

Phase 1 rule:

- make failures visible in PostgreSQL when possible

---

## Environment Variables

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `RABBITMQ_URL`
- `WORKER_CONSUMER_QUEUE`
- `WORKER_MAX_CONCURRENCY`
- `EMAIL_PROVIDER_MODE`
- `LOCAL_STORAGE_PATH` for the shared storage root, for example `/shared-data`
- `OUTPUT_STORAGE_PATH` if outputs need a separate configured subpath under the shared root

## Local Development Environment

- manage this service with `uv`
- create and use a dedicated environment at `worker-service/.venv`
- do not share a Python virtual environment with `api-service`
- keep local development dependencies aligned with the service's Docker image inputs

---

## Testing Plan

Required tests:

- consume valid task message
- submit tasks through the thread pool with bounded concurrency
- process `send_email` task successfully
- process `resize_image` task successfully
- mark task as `FAILED` when handler throws
- update status transitions correctly
- write result payload on success
- verify the repository is responsible for persistence updates
- verify executor logic can be tested with injected fake services or repositories

Useful integration tests:

- consume message from RabbitMQ and update PostgreSQL end to end
- verify resized image output exists
- verify `resize_image` reads from a task-owned input path
- verify `resize_image` resolves stored relative paths against the shared storage root

---

## Future Follow-Up

- migrate `services/storage.py` from local filesystem storage to MinIO without changing handler contracts for `resize_image`

---

## Acceptance Criteria

- worker consumes messages from RabbitMQ
- worker executes task handlers through a bounded thread pool
- worker loads task payload from PostgreSQL
- worker updates status to `PROCESSING`
- worker completes `send_email` and `resize_image`
- worker can read files written by `api-service` through the shared storage mount
- worker stores `result` on success
- worker stores `error_message` and `FAILED` on error
- worker keeps persistence concerns in repositories and orchestration concerns in services

---

## Implementation Order

1. bootstrap worker project
2. initialize `uv`, `pyproject.toml`, and `worker-service/.venv`
3. configure DB and RabbitMQ connectivity
4. implement consumer
5. implement task executor service
6. implement `send_email` handler
7. implement `resize_image` handler
8. add optional `/health`
9. add worker tests
