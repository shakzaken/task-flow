import { getApiBaseUrl } from "../api/client";
import type { TaskResponse } from "../types/task";

export function getTaskDownloadUrl(task: TaskResponse): string | null {
  if (task.type !== "resize_image" || task.status !== "COMPLETED") {
    return null;
  }

  const outputPath = task.result?.output_path;
  return typeof outputPath === "string" ? `${getApiBaseUrl()}/artifacts/${outputPath}` : null;
}
