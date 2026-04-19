import type { TaskType } from "../types/task";

interface TaskTypeSelectorProps {
  onChange: (taskType: TaskType) => void;
  value: TaskType;
}

const TASK_OPTIONS: Array<{ description: string; label: string; value: TaskType }> = [
  {
    value: "send_email",
    label: "Send Email",
    description: "Submit a simple delivery task with recipient, subject, and message body."
  },
  {
    value: "merge_pdfs",
    label: "Merge PDFs",
    description: "Upload two PDF documents and combine them into a single file in page order."
  },
  {
    value: "summarize_pdf",
    label: "Summarize PDF",
    description: "Upload one PDF and generate a summarized PDF that can be downloaded."
  },
  {
    value: "resize_image",
    label: "Resize Image",
    description: "Upload an image first, then create a resize task with explicit dimensions."
  }
];

export default function TaskTypeSelector({ onChange, value }: TaskTypeSelectorProps) {
  return (
    <fieldset className="panel selector-panel">
      <legend className="eyebrow">Task Type</legend>
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
            <span className="selector-title">{option.label}</span>
            <span className="selector-description">{option.description}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
