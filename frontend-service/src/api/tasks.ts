import { apiRequest } from "./client";
import type { CreateTaskRequest, CreateTaskResponse, TaskResponse } from "../types/task";

export function createTask(request: CreateTaskRequest): Promise<CreateTaskResponse> {
  return apiRequest<CreateTaskResponse>("/tasks", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export function getTask(taskId: string): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/${taskId}`);
}

