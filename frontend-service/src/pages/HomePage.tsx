import { useState } from "react";

import MergePdfsForm from "../components/MergePdfsForm";
import SendEmailForm from "../components/SendEmailForm";
import ResizeImageForm from "../components/ResizeImageForm";
import SummarizePdfForm from "../components/SummarizePdfForm";
import TaskStatusPanel from "../components/TaskStatusPanel";
import TaskTypeSelector from "../components/TaskTypeSelector";
import { useCreateTask } from "../hooks/useCreateTask";
import { useRecentTasksPolling } from "../hooks/useRecentTasksPolling";
import type {
  MergePdfsPayload,
  ResizeImagePayload,
  SendEmailPayload,
  SummarizePdfPayload,
  TaskResponse,
  TaskType
} from "../types/task";

interface HomePageProps {
  pollingIntervalMs?: number;
}

export default function HomePage({ pollingIntervalMs }: HomePageProps) {
  const [taskType, setTaskType] = useState<TaskType>("send_email");
  const [refreshKey, setRefreshKey] = useState(0);
  const [optimisticTasks, setOptimisticTasks] = useState<TaskResponse[]>([]);
  const { error: submitError, isSubmitting, submitTask } = useCreateTask();
  const { error: pollingError, isPolling, tasks } = useRecentTasksPolling(
    refreshKey,
    optimisticTasks,
    pollingIntervalMs
  );

  function addOptimisticTask(
    taskId: string,
    type: TaskType,
    payload: MergePdfsPayload | SendEmailPayload | ResizeImagePayload | SummarizePdfPayload
  ) {
    const timestamp = new Date().toISOString();
    const optimisticTask: TaskResponse = {
      id: taskId,
      type,
      status: "PENDING",
      payload: payload as unknown as Record<string, unknown>,
      result: null,
      error_message: null,
      created_at: timestamp,
      updated_at: timestamp
    };

    setOptimisticTasks((current) => {
      const next = [optimisticTask, ...current.filter((task) => task.id !== taskId)];
      return next.slice(0, 10);
    });
  }

  async function handleSendEmailSubmit(payload: SendEmailPayload) {
    const created = await submitTask({
      task_type: "send_email",
      payload
    });
    if (created) {
      addOptimisticTask(created.task_id, "send_email", payload);
      setRefreshKey((current) => current + 1);
    }
  }

  async function handleResizeImageSubmit(payload: ResizeImagePayload) {
    const created = await submitTask({
      task_type: "resize_image",
      payload
    });
    if (created) {
      addOptimisticTask(created.task_id, "resize_image", payload);
      setRefreshKey((current) => current + 1);
    }
  }

  async function handleMergePdfsSubmit(payload: MergePdfsPayload) {
    const created = await submitTask({
      task_type: "merge_pdfs",
      payload
    });
    if (created) {
      addOptimisticTask(created.task_id, "merge_pdfs", payload);
      setRefreshKey((current) => current + 1);
    }
  }

  async function handleSummarizePdfSubmit(payload: SummarizePdfPayload) {
    const created = await submitTask({
      task_type: "summarize_pdf",
      payload
    });
    if (created) {
      addOptimisticTask(created.task_id, "summarize_pdf", payload);
      setRefreshKey((current) => current + 1);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Task Flow Console</p>
        <h1>Submit work and monitor queue activity in one place.</h1>
        <p className="hero-copy">
          Create email and image jobs from the control panel, then review the latest ten tasks and
          their current status without leaving the page.
        </p>
      </section>

      <div className="layout-grid">
        <section className="stack">
          <TaskTypeSelector onChange={setTaskType} value={taskType} />
          {submitError ? <p className="banner banner-error">Request failed: {submitError}</p> : null}
          {taskType === "send_email" ? (
            <SendEmailForm disabled={isSubmitting} onSubmit={handleSendEmailSubmit} />
          ) : taskType === "merge_pdfs" ? (
            <MergePdfsForm disabled={isSubmitting} onSubmit={handleMergePdfsSubmit} />
          ) : taskType === "summarize_pdf" ? (
            <SummarizePdfForm disabled={isSubmitting} onSubmit={handleSummarizePdfSubmit} />
          ) : (
            <ResizeImageForm disabled={isSubmitting} onSubmit={handleResizeImageSubmit} />
          )}
        </section>

        <TaskStatusPanel
          error={pollingError}
          isPolling={isPolling}
          isSubmitting={isSubmitting}
          tasks={tasks}
        />
      </div>
    </main>
  );
}
