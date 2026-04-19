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

export default function TaskStatusPanel({
  error,
  isPolling,
  isSubmitting,
  tasks
}: TaskStatusPanelProps) {
  return (
    <section className="panel status-panel">
      <div className="status-panel-top">
        <div>
          <p className="eyebrow">Recent Tasks</p>
          <h2>Latest 10 task executions</h2>
        </div>
        {isPolling ? <p className="inline-note">Refreshing...</p> : null}
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
                  <h3>{formatTaskType(task.type)}</h3>
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
