# Phase 1 Plan

This document defines the phase-level plan for Phase 1 only.

Phase 1 delivers the first end-to-end version of the platform: a user can submit a task, the system persists it, a worker processes it asynchronously, and the UI can track it to completion or failure.

Service-specific implementation details live in:

- `docs/API_PLAN.md`
- `docs/WORKER_PLAN.md`
- `docs/UI_PLAN.md`

---

## Phase Goal

Build a working MVP for asynchronous task submission and processing across three projects:

- `api-service`: accepts task requests, persists task state, and publishes queue messages
- `worker-service`: consumes queued work and executes supported task handlers
- `frontend-service`: submits tasks and tracks their status through the API

Phase 1 focuses on the core request-to-processing flow. Real-time updates, retries, advanced reliability patterns, and horizontal scaling belong to later phases.

---

## In Scope

- asynchronous task creation through the API
- persisted task state in PostgreSQL
- queue-based handoff from API to worker
- worker execution for supported task types
- UI-based task submission and status tracking
- local development orchestration for all required services

Supported task types:

- `resize_image`
- `send_email`

---

## Out of Scope

- websockets or other real-time push updates
- dead-letter queues and advanced retry policies
- multi-worker scaling strategy
- authentication and authorization
- production-grade observability and operations

---

## Cross-Service Rules

These rules apply to the whole phase and must stay consistent across all projects:

- PostgreSQL is the source of truth for task state.
- The API must persist the task before publishing to the queue.
- Queue messages should stay minimal and contain only execution intent, not the full task payload.
- The worker must load task details from PostgreSQL before execution.
- The UI should treat polling as the Phase 1 status-update mechanism.
- `resize_image` uploads should go through a separate upload step before task creation.
- temporary uploads should be moved or attached to task-owned paths before worker execution.
- file-based task inputs and outputs must live under a shared storage location visible to both `api-service` and `worker-service`.
- task payloads should store relative file paths that both services resolve against the same shared storage root.
- API request and response contracts should use explicit Pydantic models.
- FastAPI routes should stay thin and use explicit dependency injection.
- repository classes should own persistence concerns.
- service classes should own orchestration and infrastructure access.
- React components should stay small, typed, and focused on UI concerns.
- Python services should use `uv` for dependency management.
- each Python service should keep its own `.venv` inside its project directory.
- `api-service` and `worker-service` should not share one Python virtual environment.

Canonical task statuses for Phase 1:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

Required transition path:

- `PENDING` -> `PROCESSING`
- `PROCESSING` -> `COMPLETED`
- `PROCESSING` -> `FAILED`

---

## End-to-End Flow

1. For `resize_image`, the UI uploads the file before task creation.
2. The API stores the file as a temporary local upload.
3. The UI submits a supported task to the API.
4. The API validates the request, attaches the uploaded file to a task-owned path when needed, and creates the task in PostgreSQL with status `PENDING`.
5. The API publishes a queue message for the new task.
6. The worker consumes the message and loads the task from PostgreSQL.
7. The worker updates the task to `PROCESSING` and executes the correct handler.
8. The worker writes either a success result with `COMPLETED` or an error with `FAILED`.
9. The UI polls the API until the task reaches a terminal state.

---

## Shared Dependencies

Phase 1 requires these shared platform components:

- PostgreSQL for persisted task records
- RabbitMQ for background task delivery
- local filesystem storage for file-based task inputs and outputs
- a shared mounted storage path used by both `api-service` and `worker-service`
- Docker Compose for local orchestration

---

## Deliverables

- `api-service`, `worker-service`, and `frontend-service` wired together end to end
- a shared task lifecycle contract used consistently across services
- a temporary-upload flow for `resize_image` with task-owned file paths
- infrastructure needed to run the MVP locally
- successful execution path for both supported task types

---

## Testing Expectations

- each service should include at least one meaningful automated test for every non-trivial flow it owns
- Phase 1 testing should cover both supported task types end to end
- failure paths should be tested explicitly for validation, processing, and status updates
- any bug fixed during Phase 1 should add a regression test

---

## Implementation Sequence

1. Set up the repository structure and local infrastructure.
2. Initialize per-service Python environments with `uv` for `api-service` and `worker-service`.
3. Establish the shared task contract: supported task types, statuses, and payload ownership.
4. Build the API task-creation and task-read flow.
5. Build the worker consumption and task-execution flow.
6. Build the UI submission and polling flow.
7. Verify the complete path for `send_email` and `resize_image`.

Detailed implementation order for each project is documented in the service-specific plan files.

---

## Acceptance Criteria

Phase 1 is complete when all of the following are true:

- a user can submit either supported task type from the UI
- `resize_image` uploads are stored temporarily before task creation
- temporary uploads are attached to task-owned paths before worker execution
- file-based task inputs are readable by `worker-service` after `api-service` saves them
- the API persists each new task before background processing begins
- the API publishes work to the queue after persistence succeeds
- the worker consumes queued tasks and executes the correct handler
- task state transitions are visible through the API
- successful execution stores a result
- failed execution stores an error message
- the full flow runs locally end to end

---

## Risks

- storage requirements can complicate the image-processing flow if upload handling expands too early
- temporary uploads require cleanup so unused files do not accumulate
- weak contract alignment between `api-service`, `worker-service`, and `frontend-service` can cause payload or status drift
- publish-after-persist failure remains a known MVP reliability gap until a later phase addresses it

---

## Future Follow-Up

- migrate the Phase 1 storage abstraction from local filesystem storage to MinIO
