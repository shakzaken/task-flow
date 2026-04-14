# Worker Service Tasks

This document breaks `docs/phase1/WORKER_PLAN.md` into implementation tasks and ordered steps for Phase 1 of the `worker-service`.

The goal is to provide a practical execution checklist that matches the planned worker architecture:

- sync-first worker execution for Phase 1
- bounded thread-pool task processing
- repositories for database access
- services for orchestration and infrastructure
- explicit handler dispatch by task type
- shared filesystem access for file-based tasks

---

## Task 1: Bootstrap the `worker-service`

Objective:
Create the initial worker project structure and isolated Python environment.

Checklist:

- [x] Create the `worker-service/` directory structure described in `WORKER_PLAN.md`.
- [x] Initialize `uv` for the service.
- [x] Create `worker-service/.venv`.
- [x] Add `pyproject.toml` with the initial runtime and development dependencies.
- [x] Add `app/main.py` and bootstrap the FastAPI application shell.
- [x] Add placeholder modules for `consumers/task_consumer.py`, `services/task_executor.py`, `handlers/send_email.py`, `handlers/resize_image.py`, `services/storage.py`, and `services/email_sender.py`.
- [x] Add an optional route module for `app/api/routes/health.py`.
- [x] Confirm the service starts locally.

Done when:

- [x] The worker runs successfully.
- [x] The project layout matches the planned module structure.
- [x] Dependencies are isolated to `worker-service`.

---

## Task 2: Add configuration and dependency wiring

Objective:
Create the base configuration and dependency layer for the worker runtime.

Checklist:

- [x] Add `app/core/config.py` using typed settings for environment variables.
- [x] Define `POSTGRES_HOST`.
- [x] Define `POSTGRES_PORT`.
- [x] Define `POSTGRES_DB`.
- [x] Define `POSTGRES_USER`.
- [x] Define `POSTGRES_PASSWORD`.
- [x] Define `RABBITMQ_URL`.
- [x] Define `WORKER_CONSUMER_QUEUE`.
- [x] Define `WORKER_MAX_CONCURRENCY`.
- [x] Define `RABBITMQ_PREFETCH_COUNT`.
- [x] Define `DB_POOL_SIZE`.
- [x] Define `DB_MAX_OVERFLOW`.
- [x] Define `EMAIL_PROVIDER_MODE`.
- [x] Define `LOCAL_STORAGE_PATH`.
- [x] Define `OUTPUT_STORAGE_PATH`.
- [x] Add database engine and session setup in `app/db/session.py` using synchronous SQLAlchemy sessions.
- [x] Add SQLAlchemy base metadata in `app/db/base.py`.
- [x] Create dependency providers or explicit constructors for repositories and services.
- [x] Keep dependency construction explicit and easy to override in tests.

Done when:

- [x] Settings load through Pydantic.
- [x] The worker can create its dependencies from one clear composition root.
- [x] Sync DB sessions are scoped cleanly for worker-thread use.

---

## Task 3: Add the worker-side task model and repository

Objective:
Support worker reads and state updates against the existing `tasks` table.

Checklist:

- [x] Create `app/db/models/task.py` if the worker keeps a local ORM model definition.
- [x] Ensure the ORM model matches the Phase 1 task table contract.
- [x] Create `app/db/repositories/task_repository.py`.
- [x] Implement task lookup by `task_id`.
- [x] Implement status update support.
- [x] Implement success result persistence support.
- [x] Implement failure error-message persistence support.
- [x] Keep repository methods limited to database concerns.
- [x] Keep status-transition rules out of the repository.
- [x] Ensure commits happen through explicit repository or session boundaries used by the executor.

Done when:

- [x] The worker can load the source-of-truth task row from PostgreSQL.
- [x] The worker can persist `PROCESSING`, `COMPLETED`, and `FAILED` transitions.
- [x] Persistence logic stays isolated from handlers and consumer code.

---

## Task 4: Implement the storage service for worker-side file access

Objective:
Resolve and manage shared filesystem paths used by `resize_image`.

Checklist:

- [x] Create `app/services/storage.py`.
- [x] Resolve relative task payload paths against `LOCAL_STORAGE_PATH`.
- [x] Add support for reading task-owned input files from the shared storage root.
- [x] Add support for building deterministic output paths under `OUTPUT_STORAGE_PATH` or a configured subpath.
- [x] Return relative output paths suitable for task result storage.
- [x] Keep path resolution logic out of handlers.
- [x] Keep the interface replaceable by a future MinIO-backed implementation.

Done when:

- [x] `resize_image` can read files produced by `api-service`.
- [x] Output files are written to deterministic task-specific paths.
- [x] Storage concerns are isolated from handlers and repositories.

---

## Task 5: Implement the email sender service

Objective:
Encapsulate email-provider behavior behind a deterministic Phase 1 abstraction.

Checklist:

- [x] Create `app/services/email_sender.py`.
- [x] Implement a fake or mock provider mode for Phase 1.
- [x] Read provider behavior from `EMAIL_PROVIDER_MODE`.
- [x] Return a clear success result for valid `send_email` requests.
- [x] Surface provider failures as exceptions usable by the executor.
- [x] Keep provider-specific behavior out of the handler.
- [x] Keep the service easy to replace with a real provider in a later phase.

Done when:

- [x] `send_email` processing does not require a real email account in Phase 1.
- [x] Email behavior is deterministic and easy to test.
- [x] Provider logic is isolated in one service.

---

## Task 6: Implement the task executor service

Objective:
Centralize status transitions, handler dispatch, and task execution orchestration.

Checklist:

- [x] Create `app/services/task_executor.py`.
- [x] Inject the task repository.
- [x] Inject the storage service.
- [x] Inject the email sender service.
- [x] Load the task row by `task_id` before execution.
- [x] Fail safely when the task row does not exist.
- [x] Update task status to `PROCESSING` before running a handler.
- [x] Dispatch execution by `task_type`.
- [x] Write result payload and `COMPLETED` on success.
- [x] Write `error_message` and `FAILED` on handler failure.
- [x] Keep state-transition rules in the executor or an executor-owned service boundary.
- [x] Keep DB sessions scoped to the worker thread processing the task.

Done when:

- [x] The executor owns orchestration and status transitions.
- [x] Handlers focus only on task-specific logic.
- [x] Failure and success paths are persisted consistently.

---

## Task 7: Implement the RabbitMQ consumer

Objective:
Consume queue messages and submit valid work to the bounded thread pool.

Checklist:

- [x] Create `app/consumers/task_consumer.py`.
- [x] Implement RabbitMQ connection behavior.
- [x] Bind to the `tasks.phase1` queue.
- [x] Consume messages with the Phase 1 message shape containing `task_id` and `task_type`.
- [x] Configure RabbitMQ prefetch using `RABBITMQ_PREFETCH_COUNT`.
- [x] Validate the incoming message shape.
- [x] Reject malformed messages and log the reason.
- [x] Keep the consumer loop responsible only for message intake and task submission.
- [x] Submit accepted work to a bounded thread pool sized by `WORKER_MAX_CONCURRENCY`.
- [x] Acknowledge a message only after task processing completes.
- [x] Keep queue-specific behavior out of handlers and repositories.

Done when:

- [x] The worker can consume valid task messages from RabbitMQ.
- [x] Invalid messages are rejected and logged safely.
- [x] The consumer delegates execution to the thread pool without owning business logic.

---

## Task 8: Implement the task handlers

Objective:
Add the task-specific business logic for the supported Phase 1 task types.

Checklist:

- [x] Implement `app/handlers/send_email.py`.
- [x] Validate or parse the stored `send_email` payload into a typed model if needed.
- [x] Delegate delivery behavior to `email_sender.py`.
- [x] Return a typed internal result such as `{"delivered": true}`.
- [x] Implement `app/handlers/resize_image.py`.
- [x] Validate or parse the stored `resize_image` payload into a typed model if needed.
- [x] Resolve the input image path through `storage.py`.
- [x] Use Pillow for image resizing.
- [x] Write the resized output to a deterministic task-specific path.
- [x] Return a typed internal result such as `{"output_path": "..."}`.
- [x] Keep handler code focused on task-specific logic only.

Done when:

- [x] Both supported task types execute through dedicated handlers.
- [x] `send_email` uses the email service abstraction.
- [x] `resize_image` uses the storage abstraction and writes output successfully.

---

## Task 9: Add the FastAPI health endpoint and startup wiring

Objective:
Use FastAPI as the worker shell for health checks and runtime startup.

Checklist:

- [x] Implement `app/api/routes/health.py`.
- [x] Return a simple healthy response from `GET /health`.
- [x] Start the consumer during FastAPI application startup.
- [x] Initialize the bounded thread pool during startup.
- [x] Shut down the consumer cleanly on application shutdown.
- [x] Shut down the thread pool cleanly on application shutdown.
- [x] Keep FastAPI concerns separate from task execution logic.

Done when:

- [x] The worker exposes `/health`.
- [x] The consumer and thread pool are started and stopped through the application lifecycle.
- [x] The FastAPI boundary stays small and operational in purpose.

---

## Task 10: Add worker tests

Objective:
Verify the required Phase 1 worker behavior with focused automated tests.

Checklist:

- [x] Add repository tests for task lookup and persistence updates.
- [x] Add executor tests for `PENDING` -> `PROCESSING` -> `COMPLETED`.
- [x] Add executor tests for `PENDING` -> `PROCESSING` -> `FAILED`.
- [x] Add tests that `send_email` processes successfully with the fake provider.
- [x] Add tests that `resize_image` processes successfully and writes output.
- [x] Add tests that malformed queue messages are rejected.
- [x] Add tests that valid messages are submitted through the bounded thread pool.
- [x] Add tests that success result payloads are persisted.
- [x] Add tests that failure error messages are persisted.
- [x] Add tests that repository and service dependencies can be injected as fakes.
- [x] Add at least one integration test that consumes a RabbitMQ message and updates PostgreSQL end to end if local test infrastructure supports it.
- [x] Add an integration test that verifies `resize_image` resolves stored relative paths against the shared storage root.

Done when:

- [x] Required worker flows are covered by automated tests.
- [x] Regression risk is reduced for status transitions, handler execution, and queue consumption.
- [x] The worker plan acceptance criteria are exercised by the test suite.

---

## Suggested Implementation Order

1. Complete Task 1 and Task 2 to establish the worker project and runtime configuration.
2. Complete Task 3, Task 4, and Task 5 to build the worker-side dependencies.
3. Complete Task 6 and Task 7 to wire execution orchestration and queue consumption.
4. Complete Task 8 to add both supported task handlers.
5. Complete Task 9 to finish lifecycle wiring and health reporting.
6. Complete Task 10 before considering Phase 1 worker work done.
