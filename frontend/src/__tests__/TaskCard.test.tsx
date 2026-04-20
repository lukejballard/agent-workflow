import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TaskCard } from "../components/agent/TaskCard";
import type { AgentTask } from "../types/agentRuntime";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeTask(overrides: Partial<AgentTask> = {}): AgentTask {
  return {
    task_id: "task-001",
    objective: "Write unit tests",
    state: "PENDING",
    plan: null,
    trace_id: "trace-abc",
    created_at: "2026-04-18T10:00:00.000Z",
    updated_at: "2026-04-18T10:00:00.000Z",
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

describe("TaskCard", () => {
  it("renders the task objective", () => {
    render(<TaskCard task={makeTask()} />);
    expect(screen.getByText("Write unit tests")).toBeDefined();
  });

  it("has role=article landmark", () => {
    render(<TaskCard task={makeTask()} />);
    const article = screen.getByRole("article");
    expect(article).toBeDefined();
  });

  it("exposes accessible aria-label containing the objective", () => {
    render(<TaskCard task={makeTask()} />);
    const article = screen.getByRole("article", { name: /Write unit tests/i });
    expect(article).toBeDefined();
  });

  it("shows the state badge with aria-label", () => {
    render(<TaskCard task={makeTask({ state: "EXECUTING" })} />);
    const badge = screen.getByLabelText(/State: Executing/i);
    expect(badge).toBeDefined();
  });

  it("renders a View detail button for non-terminal tasks", () => {
    render(<TaskCard task={makeTask()} onSelect={vi.fn()} />);
    const btn = screen.getByRole("button", { name: /View details for task/i });
    expect(btn).toBeDefined();
  });

  it("hides the View detail button for terminal DONE tasks", () => {
    render(<TaskCard task={makeTask({ state: "DONE" })} onSelect={vi.fn()} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("hides the View detail button for terminal FAILED tasks", () => {
    render(<TaskCard task={makeTask({ state: "FAILED" })} onSelect={vi.fn()} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("hides the View detail button when onSelect is not provided", () => {
    render(<TaskCard task={makeTask()} />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("calls onSelect with taskId when View detail is clicked", () => {
    const onSelect = vi.fn();
    render(<TaskCard task={makeTask()} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onSelect).toHaveBeenCalledWith("task-001");
  });

  it("renders task_id in a code element", () => {
    render(<TaskCard task={makeTask()} />);
    expect(screen.getByText("task-001")).toBeDefined();
  });

  it("renders a time element for created_at", () => {
    const { container } = render(<TaskCard task={makeTask()} />);
    const timeEl = container.querySelector("time");
    expect(timeEl).not.toBeNull();
    expect(timeEl?.getAttribute("dateTime")).toBe("2026-04-18T10:00:00.000Z");
  });
});
