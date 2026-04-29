import type { TaskType } from "../types/task";

interface TaskTypeSelectorProps {
  onChange: (taskType: TaskType) => void;
  value: TaskType;
}

const TASK_OPTIONS: Array<{
  description: string;
  label: string;
  meta: string;
  value: TaskType;
}> = [
  {
    value: "send_email",
    label: "Send Email",
    description: "Submit a simple delivery task with recipient, subject, and message body.",
    meta: "Outbound notification"
  },
  {
    value: "merge_pdfs",
    label: "Merge PDFs",
    description: "Upload two PDF documents and combine them into a single file in page order.",
    meta: "Two uploads, one artifact"
  },
  {
    value: "summarize_pdf",
    label: "Summarize PDF",
    description: "Upload one PDF and generate a summarized PDF that can be downloaded.",
    meta: "LLM-assisted output"
  },
  {
    value: "resize_image",
    label: "Resize Image",
    description: "Upload an image first, then create a resize task with explicit dimensions.",
    meta: "Deterministic dimensions"
  }
];

function getTaskGlyph(value: TaskType) {
  if (value === "send_email") {
    return "✉";
  }
  if (value === "merge_pdfs") {
    return "⇄";
  }
  if (value === "summarize_pdf") {
    return "◫";
  }
  return "⬒";
}

export default function TaskTypeSelector({ onChange, value }: TaskTypeSelectorProps) {
  return (
    <fieldset className="panel selector-panel">
      <div className="selector-header">
        <legend className="eyebrow">Task Type</legend>
        <p className="selector-header-copy">
          Choose the workflow you want to dispatch into the processing queue.
        </p>
      </div>
      <div className="selector-grid">
        {TASK_OPTIONS.map((option) => (
          <label
            className={`selector-card${option.value === value ? " selector-card-active" : ""}`}
            key={option.value}
          >
            <input
              checked={option.value === value}
              name="task-type"
              onChange={() => onChange(option.value)}
              type="radio"
              value={option.value}
            />
            <span className="selector-glyph" aria-hidden="true">
              {getTaskGlyph(option.value)}
            </span>
            <span className="selector-meta">{option.meta}</span>
            <span className="selector-title">{option.label}</span>
            <span className="selector-description">{option.description}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
