import { useState, type FormEvent } from "react";

import type { SendEmailPayload } from "../types/task";

interface SendEmailFormProps {
  disabled?: boolean;
  onSubmit: (payload: SendEmailPayload) => void | Promise<void>;
}

interface SendEmailErrors {
  body?: string;
  subject?: string;
  to?: string;
}

export default function SendEmailForm({ disabled = false, onSubmit }: SendEmailFormProps) {
  const [values, setValues] = useState<SendEmailPayload>({
    to: "",
    subject: "",
    body: ""
  });
  const [errors, setErrors] = useState<SendEmailErrors>({});

  function validate(nextValues: SendEmailPayload): SendEmailErrors {
    const nextErrors: SendEmailErrors = {};
    if (!nextValues.to.trim()) {
      nextErrors.to = "Recipient email is required.";
    }
    if (!nextValues.subject.trim()) {
      nextErrors.subject = "Subject is required.";
    }
    if (!nextValues.body.trim()) {
      nextErrors.body = "Message body is required.";
    }
    return nextErrors;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    await onSubmit(values);
  }

  return (
    <form className="panel form-panel" onSubmit={handleSubmit}>
      <div className="form-copy">
        <p className="eyebrow">Email Task</p>
        <h2>Compose a one-off delivery request.</h2>
      </div>

      <label className="field">
        <span>To</span>
        <input
          name="to"
          onChange={(event) => setValues((current) => ({ ...current, to: event.target.value }))}
          placeholder="user@example.com"
          type="email"
          value={values.to}
        />
        {errors.to ? <span className="field-error">{errors.to}</span> : null}
      </label>

      <label className="field">
        <span>Subject</span>
        <input
          name="subject"
          onChange={(event) =>
            setValues((current) => ({ ...current, subject: event.target.value }))
          }
          placeholder="Welcome"
          type="text"
          value={values.subject}
        />
        {errors.subject ? <span className="field-error">{errors.subject}</span> : null}
      </label>

      <label className="field">
        <span>Body</span>
        <textarea
          name="body"
          onChange={(event) => setValues((current) => ({ ...current, body: event.target.value }))}
          placeholder="Hello"
          rows={5}
          value={values.body}
        />
        {errors.body ? <span className="field-error">{errors.body}</span> : null}
      </label>

      <button className="primary-button" disabled={disabled} type="submit">
        {disabled ? "Submitting..." : "Create Task"}
      </button>
    </form>
  );
}
