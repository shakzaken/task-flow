import { useState } from "react";

import SendEmailForm from "../components/SendEmailForm";
import ResizeImageForm from "../components/ResizeImageForm";
import TaskStatusCard from "../components/TaskStatusCard";
import TaskTypeSelector from "../components/TaskTypeSelector";
import { useCreateTask } from "../hooks/useCreateTask";
import { useTaskPolling } from "../hooks/useTaskPolling";
import type { ResizeImagePayload, SendEmailPayload, TaskType } from "../types/task";

interface HomePageProps {
  pollingIntervalMs?: number;
}

export default function HomePage({ pollingIntervalMs }: HomePageProps) {
  const [taskType, setTaskType] = useState<TaskType>("send_email");
  const { error: submitError, isSubmitting, lastCreatedTask, submitTask } = useCreateTask();
  const { error: pollingError, isPolling, task } = useTaskPolling(
    lastCreatedTask?.task_id ?? null,
    pollingIntervalMs
  );

  async function handleSendEmailSubmit(payload: SendEmailPayload) {
    await submitTask({
      task_type: "send_email",
      payload
    });
  }

  async function handleResizeImageSubmit(payload: ResizeImagePayload) {
    await submitTask({
      task_type: "resize_image",
      payload
    });
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Phase 1 Control Surface</p>
        <h1>Submit asynchronous tasks without losing sight of what the system is doing.</h1>
        <p className="hero-copy">
          Use the API-backed forms below to create a task, receive a task id, and watch the status
          move from pending to a terminal state.
        </p>
      </section>

      <div className="layout-grid">
        <section className="stack">
          <TaskTypeSelector onChange={setTaskType} value={taskType} />
          {submitError ? <p className="banner banner-error">Request failed: {submitError}</p> : null}
          {taskType === "send_email" ? (
            <SendEmailForm disabled={isSubmitting} onSubmit={handleSendEmailSubmit} />
          ) : (
            <ResizeImageForm disabled={isSubmitting} onSubmit={handleResizeImageSubmit} />
          )}
        </section>

        <TaskStatusCard
          error={pollingError}
          isPolling={isPolling}
          isSubmitting={isSubmitting}
          task={task}
        />
      </div>
    </main>
  );
}
