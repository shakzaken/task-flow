import { useState } from "react";

import { createTask } from "../api/tasks";
import type { CreateTaskRequest, CreateTaskResponse } from "../types/task";

export function useCreateTask() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitTask(request: CreateTaskRequest): Promise<CreateTaskResponse | null> {
    setIsSubmitting(true);
    setError(null);

    try {
      return await createTask(request);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error ? submissionError.message : "Failed to create task.";
      setError(message);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }

  return {
    error,
    isSubmitting,
    submitTask
  };
}
