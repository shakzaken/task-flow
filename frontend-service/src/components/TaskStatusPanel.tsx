import { getTaskDownloadUrl } from "../utils/taskArtifacts";
import type { TaskResponse } from "../types/task";

interface TaskStatusPanelProps {
  error: string | null;
  isPolling: boolean;
  isSubmitting: boolean;
  tasks: TaskResponse[];
}

function formatTaskType(type: TaskResponse["type"]) {
  if (type === "resize_image") {
    return "Resize Image";
  }
  if (type === "merge_pdfs") {
    return "Merge PDFs";
  }
  if (type === "summarize_pdf") {
    return "Summarize PDF";
  }
  return "Send Email";
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatRelativeTimestamp(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) {
    return "just now";
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function TaskStatusPanel({
  error,
  isPolling,
  isSubmitting,
  tasks
}: TaskStatusPanelProps) {
  const completedCount = tasks.filter((task) => task.status === "COMPLETED").length;
  const runningCount = tasks.filter(
    (task) => task.status === "PENDING" || task.status === "PROCESSING"
  ).length;
  const failedCount = tasks.filter((task) => task.status === "FAILED").length;

  return (
    <section className="panel status-panel">
      <div className="status-panel-top">
        <div>
          <p className="eyebrow">Recent Tasks</p>
          <h2>Execution feed and artifact history</h2>
          <p className="status-panel-copy">
            Follow the latest activity coming out of the queue and download outputs as soon as they
            are ready.
          </p>
        </div>
        {isPolling ? <p className="inline-note">Refreshing...</p> : null}
      </div>

      <div className="status-summary-grid">
        <article className="status-summary-card">
          <span className="status-summary-value">{tasks.length}</span>
          <span className="status-summary-label">Recent tasks</span>
        </article>
        <article className="status-summary-card">
          <span className="status-summary-value">{runningCount}</span>
          <span className="status-summary-label">In flight</span>
        </article>
        <article className="status-summary-card">
          <span className="status-summary-value">{completedCount}</span>
          <span className="status-summary-label">Completed</span>
        </article>
        <article className="status-summary-card">
          <span className="status-summary-value">{failedCount}</span>
          <span className="status-summary-label">Failed</span>
        </article>
      </div>

      {error ? <p className="banner banner-error">Status request failed: {error}</p> : null}
      {!tasks.length && !isSubmitting ? (
        <p className="empty-state">No tasks yet. Submit a task to start building the activity feed.</p>
      ) : null}
      {!tasks.length && isSubmitting ? <p className="empty-state">Task creation in progress.</p> : null}

      {tasks.length ? (
        <div className="task-feed" aria-live="polite">
          {tasks.map((task) => (
            <article className="task-row" key={task.id}>
              <div className="task-row-main">
                <div className="task-row-title">
                  <div className="task-row-heading">
                    <h3>{formatTaskType(task.type)}</h3>
                    <p className="task-row-relative-time">{formatRelativeTimestamp(task.updated_at)}</p>
                  </div>
                  <span className={`status-pill status-${task.status.toLowerCase()}`}>
                    {task.status}
                  </span>
                </div>
                <p className="task-row-id">{task.id}</p>
              </div>

              <dl className="task-meta">
                <div>
                  <dt>Created</dt>
                  <dd>{formatTimestamp(task.created_at)}</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{formatTimestamp(task.updated_at)}</dd>
                </div>
              </dl>

              {getTaskDownloadUrl(task) ? (
                <a
                  className="artifact-link"
                  download
                  href={getTaskDownloadUrl(task) ?? undefined}
                  target="_blank"
                  rel="noreferrer"
                >
                  {task.type === "merge_pdfs"
                    ? "Download merged PDF"
                    : task.type === "summarize_pdf"
                      ? "Download summary PDF"
                      : "Download image"}
                </a>
              ) : null}
              {task.status === "FAILED" && task.error_message ? (
                <p className="task-error">{task.error_message}</p>
              ) : null}
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
