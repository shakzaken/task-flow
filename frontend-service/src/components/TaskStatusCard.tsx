import type { TaskResponse } from "../types/task";

interface TaskStatusCardProps {
  error: string | null;
  isPolling: boolean;
  isSubmitting: boolean;
  task: TaskResponse | null;
}

export default function TaskStatusCard({
  error,
  isPolling,
  isSubmitting,
  task
}: TaskStatusCardProps) {
  if (error) {
    return (
      <section className="panel status-panel">
        <p className="eyebrow">Task Status</p>
        <p className="banner banner-error">Status request failed: {error}</p>
      </section>
    );
  }

  if (!task && !isSubmitting) {
    return (
      <section className="panel status-panel">
        <p className="eyebrow">Task Status</p>
        <p className="empty-state">No task yet. Submit a task to start tracking progress.</p>
      </section>
    );
  }

  if (!task && isSubmitting) {
    return (
      <section className="panel status-panel">
        <p className="eyebrow">Task Status</p>
        <p className="empty-state">Task creation in progress.</p>
      </section>
    );
  }

  return (
    <section className="panel status-panel">
      <div className="status-header">
        <div>
          <p className="eyebrow">Latest Task</p>
          <h2>{task?.type === "resize_image" ? "Resize Image" : "Send Email"}</h2>
        </div>
        <span className={`status-pill status-${task?.status.toLowerCase()}`}>{task?.status}</span>
      </div>

      <dl className="status-grid">
        <div>
          <dt>Task ID</dt>
          <dd>{task?.id}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{task?.created_at ?? "-"}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd>{task?.updated_at ?? "-"}</dd>
        </div>
      </dl>

      {isPolling ? <p className="inline-note">Refreshing task status...</p> : null}
      {task?.status === "COMPLETED" ? (
        <pre className="result-block">{JSON.stringify(task.result, null, 2)}</pre>
      ) : null}
      {task?.status === "FAILED" ? (
        <p className="banner banner-error">{task.error_message ?? "Task failed."}</p>
      ) : null}
    </section>
  );
}

