import { useState, type FormEvent } from "react";

import { uploadFile } from "../api/uploads";
import FileUploadField from "./FileUploadField";
import type { MergePdfsPayload } from "../types/task";

interface MergePdfsFormProps {
  disabled?: boolean;
  onSubmit: (payload: MergePdfsPayload) => void | Promise<void>;
}

interface MergePdfsErrors {
  firstFile?: string;
  secondFile?: string;
}

export default function MergePdfsForm({ disabled = false, onSubmit }: MergePdfsFormProps) {
  const [firstFile, setFirstFile] = useState<File | null>(null);
  const [secondFile, setSecondFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<MergePdfsErrors>({});
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadPaths, setUploadPaths] = useState<{ first: string; second: string } | null>(null);

  function validate(): MergePdfsErrors {
    const nextErrors: MergePdfsErrors = {};

    if (!firstFile) {
      nextErrors.firstFile = "First PDF is required.";
    }
    if (!secondFile) {
      nextErrors.secondFile = "Second PDF is required.";
    }

    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);
    setUploadError(null);

    if (Object.keys(nextErrors).length > 0 || !firstFile || !secondFile) {
      return;
    }

    setIsUploading(true);

    try {
      const [firstUpload, secondUpload] = await Promise.all([uploadFile(firstFile), uploadFile(secondFile)]);

      setUploadPaths({
        first: firstUpload.path,
        second: secondUpload.path
      });

      await onSubmit({
        first_pdf_path: firstUpload.path,
        second_pdf_path: secondUpload.path
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
        <p className="eyebrow">Merge PDFs</p>
        <h2>Upload two PDFs and combine them into one ordered document.</h2>
      </div>

      <FileUploadField
        accept="application/pdf,.pdf"
        error={errors.firstFile}
        helperText="Drag in the first source PDF or browse your files."
        id="first-pdf"
        label="First PDF"
        onChange={setFirstFile}
        selectedFile={firstFile}
      />

      <FileUploadField
        accept="application/pdf,.pdf"
        error={errors.secondFile}
        helperText="Drag in the second source PDF or browse your files."
        id="second-pdf"
        label="Second PDF"
        onChange={setSecondFile}
        selectedFile={secondFile}
      />

      {uploadError ? <p className="banner banner-error">{uploadError}</p> : null}
      {uploadPaths ? (
        <div className="upload-reference-list">
          <p className="inline-note">First upload: {uploadPaths.first}</p>
          <p className="inline-note">Second upload: {uploadPaths.second}</p>
        </div>
      ) : null}

      <button className="primary-button" disabled={disabled || isUploading} type="submit">
        {isUploading ? "Uploading..." : disabled ? "Submitting..." : "Upload And Create Task"}
      </button>
    </form>
  );
}
