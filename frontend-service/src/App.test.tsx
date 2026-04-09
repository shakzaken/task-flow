import { render, screen, waitFor } from "@testing-library/react";
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
    render(<App />);

    expect(screen.getByRole("textbox", { name: "To" })).toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /resize image/i }));

    expect(screen.getByLabelText("Image File")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "To" })).not.toBeInTheDocument();
  });

  it("shows required validation for send_email fields", async () => {
    const user = userEvent.setup();
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
        new Response(
          JSON.stringify({
            id: "task-1",
            type: "resize_image",
            status: "COMPLETED",
            payload: { image_path: "uploads/tasks/task-1/input.png", width: 300, height: 200 },
            result: { output_path: "outputs/task-1/output.png" },
            error_message: null,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:05Z"
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" }
          }
        )
      );

    render(<App pollingIntervalMs={25} />);

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

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://localhost:8000/uploads");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://localhost:8000/tasks");

    const taskRequest = fetchMock.mock.calls[1]?.[1];
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

  it("stops polling after COMPLETED", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-2", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          id: "task-2",
          type: "send_email",
          status: "COMPLETED",
          payload: {},
          result: { delivered: true },
          error_message: null,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:02Z"
        })
      );

    render(<App pollingIntervalMs={25} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(screen.getByText("COMPLETED")).toBeInTheDocument());

    await new Promise((resolve) => window.setTimeout(resolve, 80));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("stops polling after FAILED and shows the task error", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-3", status: "PENDING" }, 202))
      .mockResolvedValueOnce(
        createJsonResponse({
          id: "task-3",
          type: "send_email",
          status: "FAILED",
          payload: {},
          result: null,
          error_message: "SMTP rejected the message.",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:02Z"
        })
      );

    render(<App pollingIntervalMs={25} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(screen.getByText("SMTP rejected the message.")).toBeInTheDocument());

    await new Promise((resolve) => window.setTimeout(resolve, 80));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("renders request-level API failures and the empty state intentionally", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.mocked(globalThis.fetch);

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Validation failed" }), {
        status: 422,
        headers: { "Content-Type": "application/json" }
      })
    );

    render(<App />);

    expect(screen.getByText("No task yet. Submit a task to start tracking progress.")).toBeInTheDocument();

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
      .mockResolvedValueOnce(createJsonResponse({ task_id: "task-4", status: "PENDING" }, 202))
      .mockRejectedValueOnce(new Error("Network down"));

    render(<App pollingIntervalMs={25} />);

    await user.type(screen.getByRole("textbox", { name: "To" }), "user@example.com");
    await user.type(screen.getByRole("textbox", { name: "Subject" }), "Welcome");
    await user.type(screen.getByRole("textbox", { name: "Body" }), "Hello");
    await user.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() =>
      expect(screen.getByText("Status request failed: Network down")).toBeInTheDocument()
    );
  });
});
