# API Service Tasks

This document breaks `docs/phase1/API_PLAN.md` into implementation tasks and ordered steps for Phase 1 of the `api-service`.

The goal is to provide a practical execution checklist that matches the planned architecture:

- thin FastAPI routes
- explicit Pydantic schemas
- repositories for database access
- services for orchestration and infrastructure
- PostgreSQL persistence before RabbitMQ publish
- shared filesystem storage for upload-based tasks

---

## Task 1: Bootstrap the `api-service`

Objective:
Create the initial FastAPI service structure and isolated Python environment.

Checklist:

- [x] Create the `api-service/` directory structure described in `API_PLAN.md`.
- [x] Initialize `uv` for the service.
- [x] Create `api-service/.venv`.
- [x] Add `pyproject.toml` with the initial runtime and development dependencies.
- [x] Add `app/main.py` and bootstrap the FastAPI application.
- [x] Add placeholder route modules for `app/api/routes/tasks.py`, `app/api/routes/health.py`, and `app/api/routes/uploads.py`.
- [x] Register the routers in the FastAPI app.
- [x] Confirm the app starts locally.

Done when:

- [x] The service runs successfully.
- [x] The project layout matches the planned module structure.
- [x] Dependencies are isolated to `api-service`.

---

## Task 2: Add configuration and dependency wiring

Objective:
Create the base configuration and dependency layer used by routes, repositories, and services.

Checklist:

- [x] Add `app/core/config.py` using typed settings for environment variables.
- [x] Define `API_PORT`.
- [x] Define `POSTGRES_HOST`.
- [x] Define `POSTGRES_PORT`.
- [x] Define `POSTGRES_DB`.
- [x] Define `POSTGRES_USER`.
- [x] Define `POSTGRES_PASSWORD`.
- [x] Define `RABBITMQ_URL`.
- [x] Define `STORAGE_MODE`.
- [x] Define `LOCAL_STORAGE_PATH`.
- [x] Define `MINIO_ENDPOINT`.
- [x] Define `MINIO_ACCESS_KEY`.
- [x] Define `MINIO_SECRET_KEY`.
- [x] Add database session setup in `app/db/session.py`.
- [x] Add SQLAlchemy base metadata in `app/db/base.py`.
- [x] Create FastAPI dependency providers for the database session.
- [x] Create FastAPI dependency providers for the task repository.
- [x] Create FastAPI dependency providers for the publisher service.
- [x] Create FastAPI dependency providers for the storage service.
- [x] Create FastAPI dependency providers for the task service.
- [x] Keep dependency construction explicit and easy to override in tests.

Done when:

- [x] Settings load through Pydantic.
- [x] The app can create its dependencies through FastAPI injection.
- [x] Services and repositories can be swapped in tests.

---

## Task 3: Set up PostgreSQL migrations and the task model

Objective:
Create the persisted task record used as the source of truth.

Checklist:

- [x] Initialize Alembic in `api-service`.
- [x] Configure Alembic to use the service database settings.
- [x] Create the SQLAlchemy task model in `app/db/models/task.py`.
- [x] Define the `id` column.
- [x] Define the `type` column.
- [x] Define the `status` column.
- [x] Define the `payload` column.
- [x] Define the `result` column.
- [x] Define the `error_message` column.
- [x] Define the `created_at` column.
- [x] Define the `updated_at` column.
- [x] Add an index for `id`.
- [x] Add an index for `status`.
- [x] Add an index for `created_at`.
- [x] Generate and review the migration.
- [x] Apply the migration locally.

Done when:

- [x] The `tasks` table exists in PostgreSQL.
- [x] The ORM model matches the migration.
- [x] The schema reflects the Phase 1 status and payload design.

---

## Task 4: Define API schemas and task payload models

Objective:
Make request and response contracts explicit and typed.

Checklist:

- [x] Create `app/schemas/task.py`.
- [x] Define a base task request schema with `task_type` and `payload`.
- [x] Define a payload schema for `send_email`.
- [x] Define a payload schema for `resize_image`.
- [x] Define the create-task response schema.
- [x] Define the get-task response schema.
- [x] Add validation that maps `task_type` to the correct payload model.
- [x] Reject unsupported task types early.
- [x] Reject mismatched payload shapes early.
- [x] Create `app/schemas/upload.py` for upload response models.

Done when:

- [x] All task inputs and outputs are represented by Pydantic models.
- [x] Payload validation is type-specific.
- [x] Routes do not pass raw dictionaries as public contracts.

---

## Task 5: Implement the task repository

Objective:
Isolate task persistence logic in a repository class.

Checklist:

- [x] Create `app/db/repositories/task_repository.py`.
- [x] Implement task creation in the repository.
- [x] Implement task lookup by id in the repository.
- [x] Add update persistence support if the service flow needs it.
- [x] Keep repository methods limited to database concerns.
- [x] Avoid business logic in the repository.
- [x] Avoid validation branching in the repository.
- [x] Avoid RabbitMQ logic in the repository.
- [x] Return ORM models or clearly typed internal objects usable by the service.

Done when:

- [x] All task inserts and lookup queries are handled by the repository.
- [x] Route handlers do not contain direct SQLAlchemy logic.
- [x] The repository stays focused on persistence only.

---

## Task 6: Implement filesystem storage service for uploads

Objective:
Support the Phase 1 upload flow using shared local storage.

Checklist:

- [x] Create `app/services/storage.py`.
- [x] Implement local filesystem storage behind a service abstraction.
- [x] Resolve all disk paths against `LOCAL_STORAGE_PATH`.
- [x] Add support for storing temporary uploads under `uploads/tmp/`.
- [x] Add support for moving or attaching files into task-owned paths under `uploads/tasks/<task_id>/`.
- [x] Return relative paths instead of host-specific absolute paths.
- [x] Persist relative paths in task payload data.
- [x] Add internal path resolution from relative path to filesystem path.
- [x] Keep the interface replaceable by a future MinIO-backed implementation.

Done when:

- [x] Temporary uploads are written under the shared storage root.
- [x] Task-owned files use relative paths suitable for PostgreSQL payload storage.
- [x] Storage concerns are isolated from routes and repositories.

---

## Task 7: Implement the RabbitMQ publisher service

Objective:
Encapsulate queue publishing in a dedicated service.

Checklist:

- [x] Create `app/services/publisher.py`.
- [x] Implement RabbitMQ connection behavior.
- [x] Implement publish behavior.
- [x] Publish to the `tasks` exchange.
- [x] Publish to the `tasks.phase1` queue.
- [x] Use the `task.created` routing key.
- [x] Keep the message payload minimal with `task_id`.
- [x] Keep the message payload minimal with `task_type`.
- [x] Add clear logging around publish attempts.
- [x] Add clear logging around publish failures.
- [x] Keep connection details out of route handlers.

Done when:

- [x] The API can publish the required message shape.
- [x] Publisher behavior is isolated in one service.
- [x] Publish failures are surfaced clearly to the orchestrating service.

---

## Task 8: Implement the task service orchestration flow

Objective:
Centralize task creation logic in a service class.

Checklist:

- [x] Create `app/services/task_service.py`.
- [x] Inject the task repository.
- [x] Inject the storage service.
- [x] Inject the publisher service.
- [x] Validate task type and payload in the service flow.
- [x] Create a task id in the service flow.
- [x] Attach or move the uploaded file for `resize_image` when needed.
- [x] Create the task row with `PENDING`.
- [x] Commit the database transaction before publishing.
- [x] Publish the RabbitMQ message after commit.
- [x] Return the typed create-task response model.
- [x] Implement task lookup by id through the repository.
- [x] Keep HTTP-specific response handling out of the service.
- [x] Document the known Phase 1 behavior for publish failure after DB commit.

Done when:

- [x] The service owns validation coordination, storage attachment, persistence, and publish flow.
- [x] Task persistence happens before publishing.
- [x] Route handlers only delegate to the service.

---

## Task 9: Implement `POST /uploads`

Objective:
Support the required temporary upload flow for `resize_image`.

Checklist:

- [x] Implement `app/api/routes/uploads.py`.
- [x] Accept multipart file uploads.
- [x] Delegate file storage to `storage.py`.
- [x] Save uploaded files under `uploads/tmp/<upload_id>.<ext>`.
- [x] Return a typed upload reference response for later use in `POST /tasks`.
- [x] Reject unsupported upload requests when needed.
- [x] Reject malformed upload requests when needed.

Done when:

- [x] Uploads are accepted through a dedicated route.
- [x] Files are stored temporarily under the shared storage root.
- [x] `POST /tasks` does not need raw file content.

---

## Task 10: Implement `POST /tasks`

Objective:
Create new tasks through a thin route backed by the task service.

Checklist:

- [x] Implement the create-task handler in `app/api/routes/tasks.py`.
- [x] Accept the typed request schema.
- [x] Inject the task service through FastAPI dependencies.
- [x] Delegate all business flow to the task service.
- [x] Return `202 Accepted`.
- [x] Return `task_id` in the response.
- [x] Return `status` in the response.
- [x] Return `400` or `422` for invalid task input.
- [x] Return `500` when persistence fails.
- [x] Return `500` when publish fails.

Done when:

- [x] The route remains thin.
- [x] New tasks are stored with `PENDING`.
- [x] RabbitMQ publishing occurs only after the task row exists.

---

## Task 11: Implement `GET /tasks/{task_id}`

Objective:
Expose persisted task state to the UI.

Checklist:

- [x] Add the read-task endpoint in `app/api/routes/tasks.py`.
- [x] Inject the task service.
- [x] Fetch the task by id using the service and repository.
- [x] Return `id` in the response.
- [x] Return `type` in the response.
- [x] Return `status` in the response.
- [x] Return `payload` in the response.
- [x] Return `result` in the response.
- [x] Return `error_message` in the response.
- [x] Return `created_at` in the response.
- [x] Return `updated_at` in the response.
- [x] Return `404` for missing tasks.

Done when:

- [x] The UI can poll for status.
- [x] The endpoint reflects PostgreSQL state accurately.
- [x] Missing tasks are handled explicitly.

---

## Task 12: Implement `GET /health`

Objective:
Expose a minimal health endpoint for local development and container checks.

Checklist:

- [x] Implement `app/api/routes/health.py`.
- [x] Return a typed response with `status: "ok"`.
- [x] Register the route in the application.

Done when:

- [x] `GET /health` returns the expected payload.
- [x] The endpoint is available without extra business dependencies.

---

## Task 13: Add temporary upload attachment behavior for `resize_image`

Objective:
Complete the file lifecycle from temporary upload to task-owned input.

Checklist:

- [x] Ensure `resize_image` payload accepts an upload reference, not raw bytes.
- [x] Resolve the temporary upload reference during task creation.
- [x] Move or attach the file into `uploads/tasks/<task_id>/input.<ext>`.
- [x] Store the relative task-owned path in the task payload.
- [x] Make sure the worker-facing payload uses a path under the shared storage root.
- [x] Handle missing upload references with a clear validation error.
- [x] Handle invalid upload references with a clear validation error.

Done when:

- [x] `resize_image` tasks reference task-owned files.
- [x] The worker can resolve the stored relative path.
- [x] Temporary upload references are no longer the final payload contract.

---

## Task 14: Add temporary upload cleanup

Objective:
Prevent stale files from accumulating in `uploads/tmp/`.

Checklist:

- [x] Define a TTL rule for unused temporary uploads.
- [x] Add cleanup logic for stale files under `uploads/tmp/`.
- [x] Keep the cleanup mechanism isolated from request handlers.
- [x] Document whether cleanup runs as a script, scheduled process, or service method for Phase 1.

Done when:

- [x] Stale temporary uploads can be removed safely.
- [x] Cleanup behavior is documented and testable.

---

## Task 15: Add automated tests

Objective:
Cover the main API flows and enforce the architecture rules from the plan.

Checklist:

- [x] Add test setup for the FastAPI app.
- [x] Add test setup for dependency overrides.
- [x] Add test setup for test database usage.
- [x] Add a test for valid `send_email` task creation.
- [x] Add a test for valid `resize_image` task creation.
- [x] Add a test for unsupported `task_type`.
- [x] Add a test for invalid payload shape.
- [x] Add a test for fetching an existing task.
- [x] Add a test for returning `404` on a missing task.
- [x] Add a test verifying the task row is created before publish logic completes.
- [x] Add a test verifying route handlers delegate to services instead of embedding persistence logic.
- [x] Add a test verifying dependency-injected services can be replaced in tests.
- [x] Add an optional test for upload file handling.
- [x] Add an optional test for moving temporary uploads into task-owned paths.
- [x] Add an optional test for writing files under the shared storage root.
- [x] Add an optional test for storing relative paths in payloads.
- [x] Add an optional test for cleaning stale temporary uploads.

Done when:

- [x] The main Phase 1 flows are covered by automated tests.
- [x] Architecture boundaries are enforced by test structure.
- [x] Regressions in validation, persistence, and upload flow are easier to catch.

---

## Recommended Delivery Sequence

Track progress here as implementation advances:

- [x] Task 1: Bootstrap the `api-service`
- [x] Task 2: Add configuration and dependency wiring
- [x] Task 3: Set up PostgreSQL migrations and the task model
- [x] Task 4: Define API schemas and task payload models
- [x] Task 5: Implement the task repository
- [x] Task 6: Implement filesystem storage service for uploads
- [x] Task 7: Implement the RabbitMQ publisher service
- [x] Task 8: Implement the task service orchestration flow
- [x] Task 9: Implement `POST /uploads`
- [x] Task 10: Implement `POST /tasks`
- [x] Task 11: Implement `GET /tasks/{task_id}`
- [x] Task 12: Implement `GET /health`
- [x] Task 13: Add temporary upload attachment behavior for `resize_image`
- [x] Task 14: Add temporary upload cleanup
- [x] Task 15: Add automated tests

---

## Final Implementation Checklist

- [x] FastAPI app is bootstrapped under `api-service`.
- [x] Dependencies are managed with `uv` and isolated in `api-service/.venv`.
- [x] Database migrations and ORM model exist for `tasks`.
- [x] Request and response schemas are explicit and typed.
- [x] Repository owns task persistence.
- [x] Services own storage, publish, and orchestration logic.
- [x] `POST /uploads` stores temporary files under shared storage.
- [x] `POST /tasks` validates input, persists the task, and then publishes.
- [x] `GET /tasks/{task_id}` exposes persisted task state.
- [x] `GET /health` returns `status: ok`.
- [x] `resize_image` uses upload references and task-owned file paths.
- [x] Temporary upload cleanup is defined.
- [x] Automated tests cover the required Phase 1 flows.
