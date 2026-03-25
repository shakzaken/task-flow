# Project Plan

This document is the main implementation plan for the project.

It currently covers only:

- Phase 1: Core Task System (MVP)
- Phase 5: Real-Time Updates
- Phase 7: Multi-Worker & Scalability

The phases are intentionally ordered by dependency. Phase 1 establishes the core system, Phase 5 adds client-facing real-time visibility, and Phase 7 extends the system to run safely across multiple worker instances.

---

## Project Goal

Build an asynchronous task processing platform with:

- A FastAPI-based API service
- A queue-backed task execution flow
- Background workers for task processing
- PostgreSQL for task state
- Redis for coordination and real-time features
- file storage for image-based tasks
- A scalable worker model that supports multiple concurrent consumers

---

## Architecture Scope

Core components for the current plan:

- API Service: receives task creation requests and exposes task status
- Message Broker: transports tasks from API to workers
- Workers: consume and execute queued jobs
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

- API service with task creation and task retrieval endpoints
- Database schema and migrations
- Queue publishing flow from API to broker
- Worker runtime with task handlers
- Storage integration for file inputs and outputs
- Docker Compose setup for local development

### Acceptance Criteria

- A client can create a task and receive a `task_id`
- A client can upload an image file before creating a `resize_image` task
- A created task is persisted before processing starts
- A worker consumes the task and executes the correct handler
- Task state transitions are visible through `GET /tasks/{task_id}`
- Success writes a result payload
- Failure writes an error message and marks the task as failed

### Suggested Implementation Order

1. Define project structure and local Docker services
2. Create DB schema and migration flow
3. Implement `POST /tasks`
4. Implement queue publish after task creation
5. Implement worker consumer and task dispatching
6. Implement `GET /tasks/{task_id}`
7. Add upload and local storage handling for image-based tasks
8. Attach temporary uploads to task-owned paths
9. Verify end-to-end flow for both task types

### Future Follow-Up

- Migrate the Phase 1 storage abstraction from local filesystem storage to MinIO so the system moves closer to the planned AWS S3 deployment model

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

---

## Cross-Phase Decisions

These decisions should stay consistent across all included phases:

- PostgreSQL is the source of truth for task state
- Queue messages should carry only the data needed for execution
- Task payload validation should happen at API boundaries
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
