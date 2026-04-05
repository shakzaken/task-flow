import { apiRequest } from "./client";
import type { UploadResponse } from "../types/task";

export function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<UploadResponse>("/uploads", {
    method: "POST",
    body: formData
  });
}

