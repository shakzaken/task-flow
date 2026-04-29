interface FileUploadFieldProps {
  accept: string;
  error?: string | null;
  helperText: string;
  id: string;
  label: string;
  onChange: (file: File | null) => void;
  selectedFile: File | null;
}

export default function FileUploadField({
  accept,
  error,
  helperText,
  id,
  label,
  onChange,
  selectedFile
}: FileUploadFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <div className={`upload-dropzone${error ? " upload-dropzone-error" : ""}`}>
        <input
          accept={accept}
          aria-label={label}
          className="upload-dropzone-input"
          id={id}
          name={id}
          onChange={(event) => onChange(event.target.files?.[0] ?? null)}
          type="file"
        />
        <div className="upload-dropzone-body">
          <span className="upload-dropzone-icon" aria-hidden="true">
            ↑
          </span>
          <div className="upload-dropzone-copy">
            <strong>{selectedFile ? selectedFile.name : "Choose a file to upload"}</strong>
            <p>{selectedFile ? `${selectedFile.type || "File"} · ${selectedFile.size} bytes` : helperText}</p>
          </div>
          <span className="upload-dropzone-button">Browse file</span>
        </div>
      </div>
      {error ? <span className="field-error">{error}</span> : null}
    </label>
  );
}
