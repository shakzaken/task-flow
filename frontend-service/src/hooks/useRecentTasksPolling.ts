import { useEffect, useState } from "react";

import { listTasks } from "../api/tasks";
import type { TaskResponse } from "../types/task";

const DEFAULT_INTERVAL_MS = 2000;
const DEFAULT_LIMIT = 10;
const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED"]);

function mergeTasks(serverTasks: TaskResponse[], optimisticTasks: TaskResponse[]) {
  const merged = new Map<string, TaskResponse>();

  for (const task of optimisticTasks) {
    merged.set(task.id, task);
  }

  for (const task of serverTasks) {
    merged.set(task.id, task);
  }

  return Array.from(merged.values())
    .sort((left, right) => right.created_at.localeCompare(left.created_at))
    .slice(0, DEFAULT_LIMIT);
}

export function useRecentTasksPolling(
  refreshKey: number,
  optimisticTasks: TaskResponse[],
  intervalMs = DEFAULT_INTERVAL_MS
) {
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    setTasks((current) => mergeTasks(current, optimisticTasks));
  }, [optimisticTasks]);

  useEffect(() => {
    let cancelled = false;
    let timerId: number | undefined;

    const poll = async () => {
      setIsPolling(true);
      let shouldContinuePolling = optimisticTasks.some((task) => !TERMINAL_STATUSES.has(task.status));

      try {
        const response = await listTasks(DEFAULT_LIMIT);
        if (cancelled) {
          return;
        }

        const nextTasks = mergeTasks(response.tasks, optimisticTasks);
        setTasks(nextTasks);
        setError(null);
        shouldContinuePolling = nextTasks.some((task) => !TERMINAL_STATUSES.has(task.status));
      } catch (pollError) {
        if (cancelled) {
          return;
        }

        const message = pollError instanceof Error ? pollError.message : "Polling failed.";
        setError(message);
      } finally {
        if (!cancelled) {
          setIsPolling(false);
          if (shouldContinuePolling) {
            timerId = window.setTimeout(poll, intervalMs);
          }
        }
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timerId) {
        window.clearTimeout(timerId);
      }
    };
  }, [intervalMs, optimisticTasks, refreshKey]);

  return {
    error,
    isPolling,
    tasks
  };
}
