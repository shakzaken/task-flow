import { getApiBaseUrl } from "../api/client";
import type { TaskResponse } from "../types/task";

export function getTaskDownloadUrl(task: TaskResponse): string | null {
  if (task.status !== "COMPLETED") {
    return null;
  }

  if (task.type !== "resize_image" && task.type !== "merge_pdfs") {
    return null;
  }

  const outputPath = task.result?.output_path;
  return typeof outputPath === "string" ? `${getApiBaseUrl()}/artifacts/${outputPath}` : null;
}
