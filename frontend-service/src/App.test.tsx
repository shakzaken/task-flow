import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import App from "./App";

function createJsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json"
    }
  });
}

describe("App", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() => {
      throw new Error("Unexpected fetch call");
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("switches task types and renders the correct form", async () => {
    const user = userEvent.setup();
    vi.mocked(globalThis.fetch).mockResolvedValue(createJsonResponse({ tasks: [] }));
    render(<App />);

    expect(screen.getByRole("textbox", { name: "To" })).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /merge pdfs/i }));

    expect(screen.getByLabelText("First PDF")).toBeInTheDocument();
    expect(screen.getByLabelText("Second PDF")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "To" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /summarize pdf/i }));

    expect(screen.getByLabelText("PDF File")).toBeInTheDocument();
    expect(screen.queryByLabelText("First PDF")).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /resize image/i }));

    expect(screen.getByLabelText("Image File")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "To" })).not.toBeInTheDocument();
  });

  it("shows required validation for send_email fields", async () => {
    const user = userEvent.setup();
    vi.mocked(globalThis.fetch).mockResolvedValue(createJsonResponse({ tasks: [] }));
    render(<App />);

    await user.click(screen.getByRole("button", { name: /create task/i }));

    expect(screen.getByText("Recipient email is required.")).toBeInTheDocument();
    expect(screen.getByText("Subject is required.")).toBeInTheDocument();
    expect(screen.getByText("Message body is required.")).toBeInTheDocument();
  });

  it("uploads the file before creating a resize_image task", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ upload_id: "up-1", path: "uploads/tmp/up-1.png", filename: "demo.png" }), {
          status: 201,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task_id: "task-1", status: "PENDING" }), {
          status: 202,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-1",
              type: "resize_image",
              status: "COMPLETED",
              payload: { image_path: "uploads/tasks/task-1/input.png", width: 300, height: 200 },
              result: { output_path: "outputs/task-1/output.png" },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:05Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.click(screen.getByRole("radio", { name: /resize image/i }));
    await user.upload(
      screen.getByLabelText("Image File"),
      new File(["image"], "demo.png", { type: "image/png" })
    );
    await user.clear(screen.getByLabelText("Width"));
    await user.type(screen.getByLabelText("Width"), "300");
    await user.clear(screen.getByLabelText("Height"));
    await user.type(screen.getByLabelText("Height"), "200");
    await user.click(screen.getByRole("button", { name: /upload and create task/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://localhost:8000/tasks?limit=10");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://localhost:8000/uploads");
    expect(fetchMock.mock.calls[2]?.[0]).toBe("http://localhost:8000/tasks");

    const taskRequest = fetchMock.mock.calls[2]?.[1];
    expect(taskRequest?.method).toBe("POST");
    expect(taskRequest?.body).toBe(
      JSON.stringify({
        task_type: "resize_image",
        payload: {
          image_path: "uploads/tmp/up-1.png",
          width: 300,
          height: 200
        }
      })
    );
  });

  it("uploads both files before creating a merge_pdfs task", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-1", path: "uploads/tmp/up-1.pdf", filename: "first.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-2", path: "uploads/tmp/up-2.pdf", filename: "second.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task_id: "task-pdf-1", status: "PENDING" }), {
          status: 202,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-pdf-1",
              type: "merge_pdfs",
              status: "COMPLETED",
              payload: {
                first_pdf_path: "uploads/tasks/task-pdf-1/input-1.pdf",
                second_pdf_path: "uploads/tasks/task-pdf-1/input-2.pdf"
              },
              result: { output_path: "outputs/task-pdf-1/output.pdf", page_count: 5 },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:05Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.click(screen.getByRole("radio", { name: /merge pdfs/i }));
    await user.upload(
      screen.getByLabelText("First PDF"),
      new File(["first"], "first.pdf", { type: "application/pdf" })
    );
    await user.upload(
      screen.getByLabelText("Second PDF"),
      new File(["second"], "second.pdf", { type: "application/pdf" })
    );
    await user.click(screen.getByRole("button", { name: /upload and create task/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://localhost:8000/tasks?limit=10");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://localhost:8000/uploads");
    expect(fetchMock.mock.calls[2]?.[0]).toBe("http://localhost:8000/uploads");
    expect(fetchMock.mock.calls[3]?.[0]).toBe("http://localhost:8000/tasks");

    const taskRequest = fetchMock.mock.calls[3]?.[1];
    expect(taskRequest?.method).toBe("POST");
    expect(taskRequest?.body).toBe(
      JSON.stringify({
        task_type: "merge_pdfs",
        payload: {
          first_pdf_path: "uploads/tmp/up-1.pdf",
          second_pdf_path: "uploads/tmp/up-2.pdf"
        }
      })
    );
  });

  it("uploads one file before creating a summarize_pdf task", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-s-1", path: "uploads/tmp/up-s-1.pdf", filename: "report.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ task_id: "task-summary-1", status: "PENDING" }), {
          status: 202,
          headers: { "Content-Type": "application/json" }
        })
      )
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-summary-1",
              type: "summarize_pdf",
              status: "COMPLETED",
              payload: { pdf_path: "uploads/tasks/task-summary-1/input.pdf" },
              result: { output_path: "outputs/task-summary-1/output.pdf", summary_model: "openrouter/free" },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:05Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.click(screen.getByRole("radio", { name: /summarize pdf/i }));
    await user.upload(
      screen.getByLabelText("PDF File"),
      new File(["report"], "report.pdf", { type: "application/pdf" })
    );
    await user.click(screen.getByRole("button", { name: /upload and create task/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(4));
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://localhost:8000/uploads");
    expect(fetchMock.mock.calls[2]?.[0]).toBe("http://localhost:8000/tasks");
    expect(fetchMock.mock.calls[2]?.[1]?.body).toBe(
      JSON.stringify({
        task_type: "summarize_pdf",
        payload: {
          pdf_path: "uploads/tmp/up-s-1.pdf"
        }
      })
    );
  });

  it("shows a new task immediately before the backend list catches up", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-new", status: "PENDING" }, 202))
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }));

    render(<App pollingIntervalMs={1000} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(screen.getByText("task-new")).toBeInTheDocument());
    expect(screen.getByText("PENDING")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("renders a completed task in the recent activity feed", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-2", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-2",
              type: "resize_image",
              status: "COMPLETED",
              payload: { image_path: "uploads/tasks/task-2/input.png", width: 300, height: 200 },
              result: { output_path: "outputs/task-2/output.png" },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:02Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(screen.getByText("COMPLETED")).toBeInTheDocument());
    expect(screen.getByText("Latest 10 task executions")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download image" })).toHaveAttribute(
      "href",
      "http://localhost:8000/artifacts/outputs/task-2/output.png"
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("renders a completed merged pdf task in the recent activity feed", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-1", path: "uploads/tmp/up-1.pdf", filename: "first.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-2", path: "uploads/tmp/up-2.pdf", filename: "second.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-merge", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-merge",
              type: "merge_pdfs",
              status: "COMPLETED",
              payload: {
                first_pdf_path: "uploads/tasks/task-merge/input-1.pdf",
                second_pdf_path: "uploads/tasks/task-merge/input-2.pdf"
              },
              result: { output_path: "outputs/task-merge/output.pdf", page_count: 7 },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:02Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.click(screen.getByRole("radio", { name: /merge pdfs/i }));
    await user.upload(
      screen.getByLabelText("First PDF"),
      new File(["first"], "first.pdf", { type: "application/pdf" })
    );
    await user.upload(
      screen.getByLabelText("Second PDF"),
      new File(["second"], "second.pdf", { type: "application/pdf" })
    );

    await user.click(screen.getByRole("button", { name: /upload and create task/i }));

    await waitFor(() => expect(screen.getByText("COMPLETED")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Download merged PDF" })).toHaveAttribute(
      "href",
      "http://localhost:8000/artifacts/outputs/task-merge/output.pdf"
    );
  });

  it("renders a completed summary pdf task in the recent activity feed", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ upload_id: "up-3", path: "uploads/tmp/up-3.pdf", filename: "report.pdf" }),
          {
            status: 201,
            headers: { "Content-Type": "application/json" }
          }
        )
      )
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-summary", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-summary",
              type: "summarize_pdf",
              status: "COMPLETED",
              payload: {
                pdf_path: "uploads/tasks/task-summary/input.pdf"
              },
              result: { output_path: "outputs/task-summary/output.pdf", summary_model: "openrouter/free" },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:02Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.click(screen.getByRole("radio", { name: /summarize pdf/i }));
    await user.upload(
      screen.getByLabelText("PDF File"),
      new File(["report"], "report.pdf", { type: "application/pdf" })
    );
    await user.click(screen.getByRole("button", { name: /upload and create task/i }));

    await waitFor(() => expect(screen.getByText("COMPLETED")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Download summary PDF" })).toHaveAttribute(
      "href",
      "http://localhost:8000/artifacts/outputs/task-summary/output.pdf"
    );
  });

  it("keeps polling while at least one recent task is not completed", async () => {
    vi.useFakeTimers();
    try {
      const fetchMock = vi.mocked(globalThis.fetch);

      fetchMock
        .mockResolvedValueOnce(
          createJsonResponse({
            tasks: [
              {
                id: "task-pending",
                type: "send_email",
                status: "PENDING",
                payload: {},
                result: null,
                error_message: null,
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:00Z"
              }
            ]
          })
        )
        .mockResolvedValueOnce(
          createJsonResponse({
            tasks: [
              {
                id: "task-pending",
                type: "send_email",
                status: "PENDING",
                payload: {},
                result: null,
                error_message: null,
                created_at: "2026-01-01T00:00:00Z",
                updated_at: "2026-01-01T00:00:01Z"
              }
            ]
          })
        );

      render(<App pollingIntervalMs={25} />);

      await Promise.resolve();
      await Promise.resolve();
      expect(fetchMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(25);
      });
      expect(fetchMock).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it("stops polling when all recent tasks are terminal", async () => {
    vi.useFakeTimers();
    try {
      const fetchMock = vi.mocked(globalThis.fetch);

      fetchMock.mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-done",
              type: "send_email",
              status: "COMPLETED",
              payload: {},
              result: { delivered: true },
              error_message: null,
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:01Z"
            }
          ]
        })
      );

      render(<App pollingIntervalMs={25} />);

      await Promise.resolve();
      await Promise.resolve();
      expect(fetchMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        await vi.advanceTimersByTimeAsync(80);
      });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it("renders a failed task in the recent activity feed", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-3", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          tasks: [
            {
              id: "task-3",
              type: "send_email",
              status: "FAILED",
              payload: {},
              result: null,
              error_message: "SMTP rejected the message.",
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:02Z"
            }
          ]
        })
      );

    render(<App pollingIntervalMs={1000} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(screen.getByText("SMTP rejected the message.")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("renders request-level API failures and the empty state intentionally", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ detail: "Validation failed" }), {
          status: 422,
          headers: { "Content-Type": "application/json" }
        })
      );

    render(<App />);

    expect(
      screen.getByText("No tasks yet. Submit a task to start building the activity feed.")
    ).toBeInTheDocument();

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() =>
      expect(screen.getByText("Request failed: Request failed with status 422")).toBeInTheDocument()
    );
  });

  it("renders polling errors clearly", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ tasks: [] }))
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-4", status: "PENDING" }, 202))
      .mockRejectedValueOnce(new Error("Network down"));

    render(<App pollingIntervalMs={1000} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() =>
      expect(screen.getByText("Status request failed: Network down")).toBeInTheDocument()
    );
  });
});
