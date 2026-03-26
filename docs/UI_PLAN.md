# Frontend Service Plan

This document defines the Phase 1 plan for the `frontend-service` project.

The UI is a React + TypeScript application that lets a user create tasks and track task status through the API service.

---

## Purpose

The UI is the user-facing project.

Its responsibilities are:

- present task submission forms
- call the API service
- display task creation responses
- poll task status until completion or failure
- show result or error details

Out of scope for this project:

- direct RabbitMQ communication
- direct database access
- server-side task execution
- real-time websockets in Phase 1

Architecture rules for this project:

- use Vite with React and TypeScript
- prefer small functional components with explicit prop types
- keep data-fetching logic out of presentation components when separation improves clarity
- prefer local component state unless shared state is clearly required
- handle loading, empty, and error states explicitly

---

## Phase 1 Scope

Supported task types:

- `resize_image`
- `send_email`

Main user flows:

- create a task
- receive `task_id`
- track task status
- view task result or failure

Phase 1 UI can be a single-page application.

---

## User Flow

1. user opens the UI
2. user selects a task type
3. UI renders the matching form fields
4. for `resize_image`, UI uploads the selected file with `POST /uploads`
5. UI receives a temporary upload reference
6. user submits the form
7. UI sends `POST /tasks` to the API with that upload reference
8. UI receives `task_id`
9. UI polls `GET /tasks/{task_id}`
10. UI displays `PENDING`, `PROCESSING`, `COMPLETED`, or `FAILED`
11. UI stops polling on terminal state

---

## API Integration

### Create Task

Endpoint:

- `POST /tasks`

Example request:

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

Example response:

```json
{
  "task_id": "uuid",
  "status": "PENDING"
}
```

### Get Task Status

Endpoint:

- `GET /tasks/{task_id}`

Example response:

```json
{
  "id": "uuid",
  "type": "send_email",
  "status": "COMPLETED",
  "payload": {},
  "result": {
    "delivered": true
  },
  "error_message": null,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Upload Flow

For `resize_image`, the UI should:

1. upload the file first
2. receive a temporary upload reference
3. send that reference in the `resize_image` task payload

Phase 1 rule:

- the UI should not send raw file content in `POST /tasks`
- the upload request and task-creation request are separate actions

---

## Recommended UI Structure

```text
frontend-service/
  src/
    api/
      client.ts
      tasks.ts
      uploads.ts
    components/
      TaskTypeSelector.tsx
      ResizeImageForm.tsx
      SendEmailForm.tsx
      TaskStatusCard.tsx
    pages/
      HomePage.tsx
    hooks/
      useCreateTask.ts
      useTaskPolling.ts
    types/
      task.ts
    App.tsx
    main.tsx
  public/
  Dockerfile
  package.json
  tsconfig.json
  vite.config.ts
```

### Module Responsibilities

- `api/client.ts`: shared HTTP client
- `api/tasks.ts`: task-related API calls
- `api/uploads.ts`: upload API for `resize_image`
- `components/TaskTypeSelector.tsx`: task type switching
- `components/ResizeImageForm.tsx`: image task input form
- `components/SendEmailForm.tsx`: email task input form
- `components/TaskStatusCard.tsx`: task state rendering
- `hooks/useCreateTask.ts`: task-creation state and submission flow
- `hooks/useTaskPolling.ts`: polling logic
- `types/task.ts`: frontend task types

---

## Screen Design

### Home Page

The MVP can be a single page with:

- page title and short description
- task type selector
- dynamic task form
- submit button
- latest submitted task status panel
- explicit loading and error states for submit and polling flows

### Task Forms

#### `send_email`

Fields:

- `to`
- `subject`
- `body`

#### `resize_image`

Fields:

- uploaded file reference
- `width`
- `height`

---

## TypeScript Models

Suggested types:

```ts
export type TaskType = "resize_image" | "send_email";

export type TaskStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface CreateTaskRequest {
  task_type: TaskType;
  payload: Record<string, unknown>;
}

export interface CreateTaskResponse {
  task_id: string;
  status: TaskStatus;
}

export interface TaskResponse {
  id: string;
  type: TaskType;
  status: TaskStatus;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
```

---

## Polling Design

Recommended behavior:

- start polling after task creation succeeds
- poll every 2 to 3 seconds
- stop on `COMPLETED` or `FAILED`
- surface network errors in the UI

Suggested terminal states:

- `COMPLETED`
- `FAILED`

Phase 1 note:

- polling is enough for MVP
- websockets belong to a later phase

---

## Testing Plan

Required tests:

- task type switching renders the correct form
- `send_email` form validates required fields
- `resize_image` upload flow sends the file before task creation
- polling stops on `COMPLETED` and `FAILED`
- API request failures and task failures render clear error states
- loading and empty states are rendered intentionally, not left implicit

---

## Recommended Frontend Stack

- React
- TypeScript
- Vite

Keep state management simple in Phase 1:

- local component state is enough
- a small custom hook for polling is enough
- add a form or validation library only if the forms become hard to reason about without one

---

## Error Handling

The UI should handle:

- invalid form input
- API validation errors
- network failures
- failed tasks

Recommended UX:

- show inline validation messages
- show request-level error banner if API call fails
- show task status clearly
- show `error_message` when task status is `FAILED`

---

## Environment Variables

- `VITE_API_BASE_URL`

If uploads are supported and served separately, keep the upload path derived from the same base URL unless backend architecture requires otherwise.

---

## Future Follow-Up

- preserve the upload and task-submission flow so the backend can later switch from local filesystem storage to MinIO without requiring a UI redesign

---

## Acceptance Criteria

- user can submit either supported task type
- UI sends correct request shape to the API
- UI displays returned `task_id`
- UI polls for task status
- UI displays success result or failure message
- UI remains usable without real-time features

---

## Implementation Order

1. bootstrap React + TypeScript app
2. create base API client
3. implement task type selector
4. implement `send_email` form
5. implement `resize_image` form
6. implement submit flow
7. implement polling hook
8. implement status card
9. add tests
