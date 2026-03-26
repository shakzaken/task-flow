# Project Plan

This document is the main implementation plan for the project.

Local Homebrew-based PostgreSQL, RabbitMQ, and Redis setup is documented in `docs/LOCAL_INFRA_SETUP.md`.

It currently covers only:

- Phase 1: Core Task System (MVP)
- Phase 5: Real-Time Updates
- Phase 7: Multi-Worker & Scalability

The phases are intentionally ordered by dependency. Phase 1 establishes the core system, Phase 5 adds client-facing real-time visibility, and Phase 7 extends the system to run safely across multiple worker instances.

---

## Project Goal

Build an asynchronous task processing platform with:

- A FastAPI-based `api-service`
- A queue-backed task execution flow
- A `worker-service` for task processing
- PostgreSQL for task state
- Redis for coordination and real-time features
- file storage for image-based tasks
- A scalable `worker-service` model that supports multiple concurrent consumers

---

## Architecture Scope

Core components for the current plan:

- `api-service`: receives task creation requests and exposes task status
- Message Broker: transports tasks from API to workers
- `worker-service`: consumes and executes queued jobs
- PostgreSQL: source of truth for task records
- Redis: supports real-time messaging and connection coordination
- File Storage: stores uploaded files and task artifacts

Recommended stack:

- Python with FastAPI
- PostgreSQL
- Redis
- RabbitMQ or Kafka
- local filesystem for Phase 1, with MinIO or AWS S3 as a later migration path
- Docker and Docker Compose

Engineering rules for this plan:

- use Pydantic models for request and response validation at the API boundary
- keep FastAPI routes thin and dependency-injected
- keep database access inside repository classes
- keep infrastructure access and business-flow orchestration inside service classes
- keep repository logic free of business rules
- use explicit type hints across Python code
- use `uv` as the Python package manager for Python services
- keep a separate `.venv` per Python service rather than one shared environment
- keep React components small, typed, and focused
- avoid adding abstractions or libraries unless the implementation clearly benefits

---

## Phase 1: Core Task System (MVP)

### Objective

Deliver the first working version of the platform with asynchronous task creation, background execution, and persisted task state.

### Scope

- Expose `POST /tasks` to create a task
- Expose `POST /uploads` for `resize_image` inputs
- Expose `GET /tasks/{task_id}` to fetch task status
- Support at least two task types:
  - `resize_image`
  - `send_email`
- Persist task lifecycle in PostgreSQL
- Publish created tasks to the queue
- Run workers that consume tasks and update status
- Store uploaded files and generated outputs on the local filesystem
- Use a shared mounted storage path so `api-service` and `worker-service` can access the same files
- Move temporary uploads into task-owned paths during task creation

### Data Model

Create a `tasks` table with:

- `id` (UUID)
- `type`
- `status`
- `payload` (JSON)
- `result` (JSON or NULL)
- `error_message`
- `created_at`
- `updated_at`

Initial statuses:

- `PENDING`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

### Deliverables

- `api-service` with task creation and task retrieval endpoints
- Database schema and migrations
- Queue publishing flow from API to broker
- `worker-service` runtime with task handlers
- Storage integration for file inputs and outputs
- separate `uv`-managed Python environments for `api-service` and `worker-service`
- Docker Compose setup for local development

### Architecture Notes

- route handlers should validate request models, call services, and return response models
- repository classes should own task persistence and queries
- service classes should coordinate storage attachment, queue publishing, and task execution flows
- task payload contracts should be represented with explicit typed models instead of passing raw dictionaries between layers when a typed model is clearer
- file paths stored in task payloads should be relative to a shared storage root, not host-specific absolute paths

### Acceptance Criteria

- A client can create a task and receive a `task_id`
- A client can upload an image file before creating a `resize_image` task
- A created task is persisted before processing starts
- A worker consumes the task and executes the correct handler
- Files written during task creation are readable by the worker through the shared storage mount
- Task state transitions are visible through `GET /tasks/{task_id}`
- Success writes a result payload
- Failure writes an error message and marks the task as failed

### Suggested Implementation Order

1. Define project structure and local Docker services
2. Initialize `uv` and separate `.venv` directories for `api-service` and `worker-service`
3. Create DB schema and migration flow
4. Implement `POST /tasks`
5. Implement queue publish after task creation
6. Implement worker consumer and task dispatching
7. Implement `GET /tasks/{task_id}`
8. Add upload and local storage handling for image-based tasks
9. Attach temporary uploads to task-owned paths
10. Verify end-to-end flow for both task types

### Future Follow-Up

- Migrate the Phase 1 storage abstraction from local filesystem storage to MinIO so the system moves closer to the planned AWS S3 deployment model

### Testing Expectations

- add at least one meaningful automated test for each non-trivial Phase 1 task
- cover both happy paths and failure paths for task creation and task execution
- add regression tests for bug fixes introduced during the phase

### Risks

- Storage flow can complicate the MVP if upload handling is mixed into the first API version
- Temporary uploads need TTL cleanup so orphan files do not accumulate
- Task execution contracts may drift if payload validation is weak
- Worker failure handling will remain basic until later phases

---

## Phase 5: Real-Time Updates

### Objective

Improve the client experience by pushing task state changes in real time instead of relying only on polling.

### Dependencies

This phase depends on Phase 1 being complete and stable because task lifecycle events must already exist before they can be broadcast to clients.

### Scope

- Add a WebSocket server or WebSocket endpoints in the API service
- Push task updates to subscribed clients
- Keep polling as a fallback mechanism
- Use Redis to help track active connections and user-to-connection mapping

### Deliverables

- Real-time subscription flow for task updates
- Event publishing on task status changes
- Redis-backed connection state management
- Fallback polling documented and supported

### Acceptance Criteria

- A connected client receives task status changes without repeated polling
- Task updates are emitted for at least:
  - `PENDING`
  - `PROCESSING`
  - `COMPLETED`
  - `FAILED`
- A disconnected client can still fetch status through `GET /tasks/{task_id}`
- Multiple concurrent client connections can subscribe without corrupting task state

### Suggested Implementation Order

1. Define event contract for task status changes
2. Add status-change publisher in API and worker flows
3. Implement WebSocket connection handling
4. Add Redis-backed connection/session coordination
5. Expose client subscription model by task or user
6. Validate fallback polling path

### Risks

- Connection tracking can become inconsistent if Redis usage is underspecified
- Event ordering may become confusing if updates are emitted from multiple services without a shared contract
- WebSocket support adds operational complexity compared to polling alone

### Testing Expectations

- test event emission on each task status transition
- test disconnected-client fallback through `GET /tasks/{task_id}`
- test connection-management failure paths, not only successful subscriptions

---

## Phase 7: Multi-Worker & Scalability

### Objective

Enable horizontal scaling so the system can process tasks using multiple worker instances safely and efficiently.

### Dependencies

This phase depends on Phase 1 for the core execution model and benefits from Phase 5 if real-time updates must reflect work completed by any worker instance.

### Scope

- Run multiple worker instances as competing consumers
- Support scaling worker count up and down
- Handle queue overload and backpressure

### Deliverables

- Multi-worker deployment model in Docker Compose or equivalent
- Verified competing-consumer behavior
- Queue and worker configuration for safe concurrent processing
- Backpressure strategy for overload scenarios

### Acceptance Criteria

- Multiple workers can consume from the same queue without duplicate execution of the same task
- Throughput improves when worker instances are scaled up
- The system remains stable when task volume spikes
- Overload behavior is defined, visible, and bounded

### Suggested Implementation Order

1. Run multiple worker replicas against the same broker
2. Verify queue semantics and task acknowledgement behavior
3. Load test with concurrent task creation
4. Define worker concurrency and prefetch settings
5. Add overload controls such as bounded queue settings or rate limiting at ingress
6. Document scaling guidance for local and production-like environments

### Risks

- Duplicate processing can appear if acknowledgements and failure handling are not well defined
- Real-time events may be emitted inconsistently across workers without a shared event path
- Backpressure is easy to postpone, but lack of it creates system instability under load

### Testing Expectations

- verify competing-consumer behavior under multiple worker instances
- test duplicate-prevention assumptions around acknowledgement and failure
- exercise overload and backpressure behavior with focused load tests

---

## Cross-Phase Decisions

These decisions should stay consistent across all included phases:

- PostgreSQL is the source of truth for task state
- Queue messages should carry only the data needed for execution
- Task payload validation should happen at API boundaries
- API boundary validation should use explicit Pydantic models
- repositories should own persistence and services should own orchestration or infrastructure access
- Workers should be stateless and horizontally scalable
- Real-time updates should be derived from task status transitions, not separate business logic

---

## Milestones

### Milestone 1

Phase 1 completed and running locally end to end.

### Milestone 2

Phase 5 completed with live task update delivery and polling fallback.

### Milestone 3

Phase 7 completed with multiple workers processing tasks under load.

---

## Out of Scope for This Plan

The following phases are intentionally excluded for now:

- Phase 2: Reliability and Robustness
- Phase 3: Performance and Caching
- Phase 4: Scheduling and Priorities
- Phase 6: Observability and Monitoring
- Phase 8: Advanced Features
