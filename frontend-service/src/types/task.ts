export type TaskType = "resize_image" | "send_email";

export type TaskStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface SendEmailPayload {
  to: string;
  subject: string;
  body: string;
}

export interface ResizeImagePayload {
  image_path: string;
  width: number;
  height: number;
}

export interface CreateTaskRequest {
  task_type: TaskType;
  payload: SendEmailPayload | ResizeImagePayload;
}

export interface CreateTaskResponse {
  task_id: string;
  status: TaskStatus;
}

export interface TaskResponse {
  id: string;
  type: TaskType;
  status: TaskStatus;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  tasks: TaskResponse[];
}

export interface UploadResponse {
  upload_id: string;
  path: string;
  filename: string;
}
