import { useState, type FormEvent } from "react";

import { uploadFile } from "../api/uploads";
import FileUploadField from "./FileUploadField";
import type { ResizeImagePayload } from "../types/task";

interface ResizeImageFormProps {
  disabled?: boolean;
  onSubmit: (payload: ResizeImagePayload) => void | Promise<void>;
}

interface ResizeImageErrors {
  file?: string;
  height?: string;
  width?: string;
}

export default function ResizeImageForm({ disabled = false, onSubmit }: ResizeImageFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [width, setWidth] = useState("300");
  const [height, setHeight] = useState("200");
  const [errors, setErrors] = useState<ResizeImageErrors>({});
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadPath, setUploadPath] = useState<string | null>(null);

  function validate(): ResizeImageErrors {
    const nextErrors: ResizeImageErrors = {};

    if (!file) {
      nextErrors.file = "Image file is required.";
    }
    if (!width.trim()) {
      nextErrors.width = "Width is required.";
    }
    if (!height.trim()) {
      nextErrors.height = "Height is required.";
    }

    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate();
    setErrors(nextErrors);
    setUploadError(null);

    if (Object.keys(nextErrors).length > 0 || !file) {
      return;
    }

    setIsUploading(true);

    try {
      const uploadResponse = await uploadFile(file);
      setUploadPath(uploadResponse.path);
      await onSubmit({
        image_path: uploadResponse.path,
        width: Number(width),
        height: Number(height)
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
        <p className="eyebrow">Resize Task</p>
        <h2>Upload first, then request deterministic output dimensions.</h2>
      </div>

      <FileUploadField
        accept="image/*"
        error={errors.file}
        helperText="Drop an image asset here before requesting a resized output."
        id="image"
        label="Image File"
        onChange={setFile}
        selectedFile={file}
      />

      <div className="field-row">
        <label className="field">
          <span>Width</span>
          <input
            min="1"
            name="width"
            onChange={(event) => setWidth(event.target.value)}
            type="number"
            value={width}
          />
          {errors.width ? <span className="field-error">{errors.width}</span> : null}
        </label>

        <label className="field">
          <span>Height</span>
          <input
            min="1"
            name="height"
            onChange={(event) => setHeight(event.target.value)}
            type="number"
            value={height}
          />
          {errors.height ? <span className="field-error">{errors.height}</span> : null}
        </label>
      </div>

      {uploadError ? <p className="banner banner-error">{uploadError}</p> : null}
      {uploadPath ? <p className="inline-note">Uploaded reference: {uploadPath}</p> : null}

      <button className="primary-button" disabled={disabled || isUploading} type="submit">
        {isUploading ? "Uploading..." : disabled ? "Submitting..." : "Upload And Create Task"}
      </button>
    </form>
  );
}
