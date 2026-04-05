import { useEffect, useState } from "react";

import { getTask } from "../api/tasks";
import type { TaskResponse } from "../types/task";

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED"]);
const DEFAULT_INTERVAL_MS = 2000;

export function useTaskPolling(taskId: string | null, intervalMs = DEFAULT_INTERVAL_MS) {
  const [task, setTask] = useState<TaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!taskId) {
      setTask(null);
      setError(null);
      setIsPolling(false);
      return;
    }

    let cancelled = false;
    let timerId: number | undefined;

    const poll = async () => {
      setIsPolling(true);

      try {
        const nextTask = await getTask(taskId);
        if (cancelled) {
          return;
        }

        setTask(nextTask);
        setError(null);

        if (TERMINAL_STATUSES.has(nextTask.status)) {
          setIsPolling(false);
          return;
        }

        timerId = window.setTimeout(poll, intervalMs);
      } catch (pollError) {
        if (cancelled) {
          return;
        }

        const message = pollError instanceof Error ? pollError.message : "Polling failed.";
        setError(message);
        setIsPolling(false);
      }
    };

    void poll();

    return () => {
      cancelled = true;
      setIsPolling(false);
      if (timerId) {
        window.clearTimeout(timerId);
      }
    };
  }, [intervalMs, taskId]);

  return {
    error,
    isPolling,
    task
  };
}
