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

const PIPELINE_STEPS = [
  "Upload and validate the source files",
  "Persist metadata and queue the background task",
  "Process in the Python worker and publish the artifact"
];

const SYSTEM_SURFACES = ["FastAPI API", "Python Worker", "RabbitMQ", "Redis", "PostgreSQL", "S3 / MinIO"];

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
  const activeCount = tasks.filter(
    (task) => task.status === "PENDING" || task.status === "PROCESSING"
  ).length;
  const completedCount = tasks.filter((task) => task.status === "COMPLETED").length;
  const failedCount = tasks.filter((task) => task.status === "FAILED").length;
  const latestTask = tasks[0];

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
      <div className="app-frame">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <span className="sidebar-brand-icon" aria-hidden="true">
              ✦
            </span>
            <div>
              <p className="sidebar-brand-label">Workspace</p>
              <h1>Task Flow</h1>
            </div>
          </div>

          <div className="sidebar-section">
            <p className="sidebar-section-title">Pipeline</p>
            <ol className="sidebar-step-list">
              {PIPELINE_STEPS.map((step, index) => (
                <li className="sidebar-step-item" key={step}>
                  <span className="sidebar-step-index">0{index + 1}</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="sidebar-section">
            <p className="sidebar-section-title">Core Services</p>
            <div className="sidebar-service-list">
              {SYSTEM_SURFACES.map((surface) => (
                <span className="sidebar-service-pill" key={surface}>
                  {surface}
                </span>
              ))}
            </div>
          </div>
        </aside>

        <section className="dashboard-main">
          <header className="dashboard-header">
            <div>
              <p className="eyebrow">Operations Hub</p>
              <h2>Dashboard</h2>
              <p className="dashboard-copy">
                Launch background file workflows, monitor queue activity, and collect finished
                artifacts from one control surface.
              </p>
            </div>
          </header>

          <section className="dashboard-top-grid">
            <article className="summary-card summary-card-primary">
              <div className="summary-card-icon" aria-hidden="true">
                ◎
              </div>
              <div>
                <p className="summary-card-label">Queue activity</p>
                <strong>{activeCount}</strong>
                <p className="summary-card-copy">Tasks currently moving through the worker pipeline.</p>
              </div>
            </article>

            <article className="summary-card">
              <div className="summary-card-icon" aria-hidden="true">
                ✓
              </div>
              <div>
                <p className="summary-card-label">Completed</p>
                <strong>{completedCount}</strong>
                <p className="summary-card-copy">Recent jobs ready for review and download.</p>
              </div>
            </article>

            <article className="summary-card">
              <div className="summary-card-icon" aria-hidden="true">
                !
              </div>
              <div>
                <p className="summary-card-label">Failed</p>
                <strong>{failedCount}</strong>
                <p className="summary-card-copy">Items that need a retry or a payload fix.</p>
              </div>
            </article>

            <article className="summary-card">
              <div className="summary-card-icon" aria-hidden="true">
                → 
              </div>
              <div>
                <p className="summary-card-label">Latest event</p>
                <strong>{latestTask ? latestTask.type.replace(/_/g, " ") : "No tasks yet"}</strong>
                <p className="summary-card-copy">
                  {latestTask
                    ? `${latestTask.status} · ${new Date(latestTask.updated_at).toLocaleTimeString()}`
                    : "Submit your first task to light up the feed."}
                </p>
              </div>
            </article>
          </section>

          <div className="dashboard-content-grid">
            <section className="workspace-column">
              <div className="workspace-header">
                <p className="eyebrow">File Upload</p>
                <h3>Prepare and dispatch a task</h3>
              </div>

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
        </section>
      </div>
    </main>
  );
}
