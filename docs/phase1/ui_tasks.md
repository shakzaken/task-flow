# Frontend Service Tasks

This document breaks `docs/phase1/UI_PLAN.md` into implementation tasks and ordered steps for Phase 1 of the `frontend-service`.

The goal is to provide a practical execution checklist that matches the planned frontend architecture:

- Vite with React and TypeScript
- small functional components
- typed API contracts
- simple local state and focused hooks
- explicit loading, empty, and error states
- separate upload and task-creation flow for `resize_image`

---

## Task 1: Bootstrap the `frontend-service`

Objective:
Create the React + TypeScript application and base project structure.

Checklist:

- [x] Create the `frontend-service/` directory.
- [x] Initialize the project with Vite.
- [x] Configure React and TypeScript.
- [x] Add the recommended base structure under `src/`.
- [x] Create `src/main.tsx`.
- [x] Create `src/App.tsx`.
- [x] Add a `public/` directory if needed.
- [x] Add `package.json`, `tsconfig.json`, and `vite.config.ts`.
- [x] Confirm the app starts locally.

Done when:

- [x] The frontend runs as a Vite app.
- [x] TypeScript is enabled.
- [x] The project structure matches the Phase 1 plan.

---

## Task 2: Add environment configuration

Objective:
Define the frontend environment setup for API communication.

Checklist:

- [x] Add support for `VITE_API_BASE_URL`.
- [x] Create a typed way to read the API base URL in frontend code.
- [x] Ensure API modules all resolve requests from the same base URL source.
- [x] Document or scaffold the expected local environment file if needed.

Done when:

- [x] The frontend can target the API service through configuration.
- [x] API modules do not hardcode host-specific URLs.

---

## Task 3: Define shared frontend types

Objective:
Create explicit TypeScript models for task types, statuses, requests, and responses.

Checklist:

- [x] Create `src/types/task.ts`.
- [x] Define `TaskType` as `resize_image | send_email`.
- [x] Define `TaskStatus` as `PENDING | PROCESSING | COMPLETED | FAILED`.
- [x] Define `CreateTaskRequest`.
- [x] Define `CreateTaskResponse`.
- [x] Define `TaskResponse`.
- [x] Define typed payload models for `send_email`.
- [x] Define typed payload models for `resize_image`.
- [x] Define upload response types for `POST /uploads`.

Done when:

- [x] The UI uses typed task contracts consistently.
- [x] Component and API code can share the same task models.

---

## Task 4: Implement the shared API client

Objective:
Centralize HTTP request behavior for the frontend.

Checklist:

- [x] Create `src/api/client.ts`.
- [x] Build a small shared request helper around `fetch`.
- [x] Resolve request URLs from `VITE_API_BASE_URL`.
- [x] Handle JSON request and response parsing.
- [x] Surface non-2xx responses as usable frontend errors.
- [x] Keep the client simple and easy to test.

Done when:

- [x] Frontend API modules use one shared request layer.
- [x] Network and API errors can be handled consistently.

---

## Task 5: Implement task API modules

Objective:
Encapsulate frontend API calls for task creation and task lookup.

Checklist:

- [x] Create `src/api/tasks.ts`.
- [x] Add a function for `POST /tasks`.
- [x] Add a function for `GET /tasks/{task_id}`.
- [x] Use the shared client from `api/client.ts`.
- [x] Return typed task responses.
- [x] Keep task API logic out of presentation components.

Done when:

- [x] The UI has a dedicated task API module.
- [x] Task-related HTTP logic is isolated from component rendering.

---

## Task 6: Implement the upload API module

Objective:
Support the separate upload flow required for `resize_image`.

Checklist:

- [x] Create `src/api/uploads.ts`.
- [x] Add a function for `POST /uploads`.
- [x] Send multipart form data for file uploads.
- [x] Return the temporary upload reference from the typed response.
- [x] Keep upload API logic separate from task API logic.

Done when:

- [x] The frontend can upload a file before task creation.
- [x] The upload flow returns the reference needed for `resize_image`.

---

## Task 7: Build the task type selector

Objective:
Let the user switch between supported task types.

Checklist:

- [x] Create `src/components/TaskTypeSelector.tsx`.
- [x] Render available task types.
- [x] Track the currently selected task type.
- [x] Notify the parent component when the selection changes.
- [x] Make the component small and explicitly typed.

Done when:

- [x] The user can switch between `send_email` and `resize_image`.
- [x] The selected task type can drive dynamic form rendering.

---

## Task 8: Build the `send_email` form

Objective:
Collect and validate input for `send_email` task creation.

Checklist:

- [x] Create `src/components/SendEmailForm.tsx`.
- [x] Add fields for `to`, `subject`, and `body`.
- [x] Validate required fields before submission.
- [x] Show inline validation messages.
- [x] Emit a typed payload to the parent submit flow.
- [x] Keep the component focused on form input concerns.

Done when:

- [x] The form captures valid `send_email` input.
- [x] Invalid form input is shown clearly to the user.

---

## Task 9: Build the `resize_image` form

Objective:
Collect image resize inputs and support the upload-first flow.

Checklist:

- [x] Create `src/components/ResizeImageForm.tsx`.
- [x] Add file input support.
- [x] Add fields for `width` and `height`.
- [x] Validate that a file is selected.
- [x] Validate that width is provided.
- [x] Validate that height is provided.
- [x] Upload the selected file through `POST /uploads` before task creation.
- [x] Store the returned temporary upload reference in component or hook state.
- [x] Emit a typed `resize_image` payload using that upload reference.
- [x] Ensure `POST /tasks` never sends raw file content.

Done when:

- [x] The form completes the upload-first flow for `resize_image`.
- [x] Task creation uses the returned upload reference and dimensions.

---

## Task 10: Implement task creation state and submission flow

Objective:
Coordinate task submission, loading state, and submission errors.

Checklist:

- [x] Create `src/hooks/useCreateTask.ts`.
- [x] Accept typed task input from the active form.
- [x] Submit `POST /tasks` through `api/tasks.ts`.
- [x] Track submit loading state.
- [x] Track submit success state.
- [x] Track submit error state.
- [x] Return the created `task_id`.
- [x] Keep request orchestration out of presentation components.

Done when:

- [x] Task submission is handled in one focused hook.
- [x] Components can render loading and error states explicitly.

---

## Task 11: Implement polling for task status

Objective:
Track task execution progress after task creation.

Checklist:

- [x] Create `src/hooks/useTaskPolling.ts`.
- [x] Start polling after a task is created successfully.
- [x] Poll `GET /tasks/{task_id}` every 2 to 3 seconds.
- [x] Update frontend state with the latest task response.
- [x] Stop polling on `COMPLETED`.
- [x] Stop polling on `FAILED`.
- [x] Surface polling errors in the UI.
- [x] Avoid polling when there is no active `task_id`.

Done when:

- [x] The UI tracks task progress through polling.
- [x] Polling stops on terminal states.

---

## Task 12: Build the task status display

Objective:
Show the latest task state, result, and failure details.

Checklist:

- [x] Create `src/components/TaskStatusCard.tsx`.
- [x] Display task id.
- [x] Display task type.
- [x] Display task status.
- [x] Display task timestamps when available.
- [x] Display task result when status is `COMPLETED`.
- [x] Display `error_message` when status is `FAILED`.
- [x] Render loading, empty, and error states intentionally.

Done when:

- [x] The latest submitted task can be tracked visually.
- [x] Success and failure details are shown clearly.

---

## Task 13: Build the home page composition

Objective:
Assemble the single-page MVP experience.

Checklist:

- [x] Create `src/pages/HomePage.tsx`.
- [x] Add a page title and short description.
- [x] Render the task type selector.
- [x] Render the correct form for the selected task type.
- [x] Connect form submission to `useCreateTask`.
- [x] Connect task polling to `useTaskPolling`.
- [x] Render request-level error messaging.
- [x] Render the latest task status panel.
- [x] Keep orchestration readable and avoid unnecessary global state.

Done when:

- [x] The home page supports the full Phase 1 user flow.
- [x] A user can create and track either supported task type from one page.

---

## Task 14: Wire the app entry point

Objective:
Make the home page the main rendered experience.

Checklist:

- [x] Render `HomePage` from `App.tsx`.
- [x] Mount the React app from `main.tsx`.
- [x] Keep the app shell minimal for Phase 1.

Done when:

- [x] The single-page task UI is the default app entry point.

---

## Task 15: Add explicit UX states and error handling

Objective:
Make the MVP clear and usable during success, failure, and in-between states.

Checklist:

- [x] Add inline validation messages for invalid form input.
- [x] Add a request-level error banner for API failures.
- [x] Add a loading state during uploads.
- [x] Add a loading state during task creation.
- [x] Add a loading or refreshing state during polling.
- [x] Add an empty state before any task is submitted.
- [x] Show failed-task `error_message` clearly.
- [x] Ensure error states are intentional instead of implicit.

Done when:

- [x] Validation, network, and task failure states are visible to the user.
- [x] Loading and empty states are not ambiguous.

---

## Task 16: Add automated tests

Objective:
Cover the main UI flows and failure cases described in the plan.

Checklist:

- [x] Add test setup for the React app.
- [x] Add tests for task type switching.
- [x] Add tests that `send_email` renders the correct form.
- [x] Add tests that `resize_image` renders the correct form.
- [x] Add tests that `send_email` validates required fields.
- [x] Add tests that `resize_image` uploads the file before task creation.
- [x] Add tests that polling stops on `COMPLETED`.
- [x] Add tests that polling stops on `FAILED`.
- [x] Add tests that API request failures render a clear error state.
- [x] Add tests that task failures render a clear error state.
- [x] Add tests that loading states render intentionally.
- [x] Add tests that empty states render intentionally.

Done when:

- [x] The main Phase 1 UI flows are covered by automated tests.
- [x] Validation, upload, polling, and failure behavior are verified.

---

## Recommended Delivery Sequence

Track progress here as implementation advances:

- [x] Task 1: Bootstrap the `frontend-service`
- [x] Task 2: Add environment configuration
- [x] Task 3: Define shared frontend types
- [x] Task 4: Implement the shared API client
- [x] Task 5: Implement task API modules
- [x] Task 6: Implement the upload API module
- [x] Task 7: Build the task type selector
- [x] Task 8: Build the `send_email` form
- [x] Task 9: Build the `resize_image` form
- [x] Task 10: Implement task creation state and submission flow
- [x] Task 11: Implement polling for task status
- [x] Task 12: Build the task status display
- [x] Task 13: Build the home page composition
- [x] Task 14: Wire the app entry point
- [x] Task 15: Add explicit UX states and error handling
- [x] Task 16: Add automated tests

---

## Final Implementation Checklist

- [x] `frontend-service` is bootstrapped with Vite, React, and TypeScript.
- [x] API base URL configuration is driven by `VITE_API_BASE_URL`.
- [x] Shared task and upload types are defined.
- [x] Task and upload API modules are implemented.
- [x] The task type selector drives dynamic form rendering.
- [x] The `send_email` form validates and submits correctly.
- [x] The `resize_image` form uploads first and then creates the task.
- [x] Task creation state is handled through a focused hook.
- [x] Polling is handled through a focused hook.
- [x] The latest task status is displayed clearly.
- [x] The home page supports the full Phase 1 submission and tracking flow.
- [x] Loading, empty, validation, and failure states are explicit.
- [x] Automated tests cover the required Phase 1 UI flows.
