import { useState, type FormEvent } from "react";

import { uploadFile } from "../api/uploads";
import type { SummarizePdfPayload } from "../types/task";

interface SummarizePdfFormProps {
  disabled?: boolean;
  onSubmit: (payload: SummarizePdfPayload) => void | Promise<void>;
}

export default function SummarizePdfForm({ disabled = false, onSubmit }: SummarizePdfFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadPath, setUploadPath] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setUploadError(null);

    if (!file) {
      setFileError("PDF file is required.");
      return;
    }

    setFileError(null);
    setIsUploading(true);
    try {
      const uploadResponse = await uploadFile(file);
      setUploadPath(uploadResponse.path);
      await onSubmit({
        pdf_path: uploadResponse.path,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed.";
      setUploadError(message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="form-copy">
        <p className="eyebrow">Summarize PDF</p>
        <h2>Upload one PDF and generate a downloadable summary document.</h2>
      </div>

      <label className="field">
        <span>PDF File</span>
        <input
          accept="application/pdf,.pdf"
          name="pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          type="file"
        />
        {fileError ? <span className="field-error">{fileError}</span> : null}
      </label>

      {uploadError ? <p className="banner banner-error">{uploadError}</p> : null}
      {uploadPath ? <p className="inline-note">Uploaded reference: {uploadPath}</p> : null}

      <button className="primary-button" disabled={disabled || isUploading} type="submit">
        {isUploading ? "Uploading..." : disabled ? "Submitting..." : "Upload And Create Task"}
      </button>
    </form>
  );
}
