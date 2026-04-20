import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ApprovalPanel } from "../components/agent/ApprovalPanel";
import type { AgentTask } from "../types/agentRuntime";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeTask(overrides: Partial<AgentTask> = {}): AgentTask {
  return {
    task_id: "task-001",
    objective: "Deploy service",
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

describe("ApprovalPanel", () => {
  it("has an accessible section landmark", () => {
    render(
      <ApprovalPanel task={makeTask()} onApprove={vi.fn()} onDeny={vi.fn()} />,
    );
    expect(screen.getByRole("region", { name: /Approval panel/i })).toBeDefined();
  });

  it("renders the Approve button for PENDING task", () => {
    render(
      <ApprovalPanel task={makeTask()} onApprove={vi.fn()} onDeny={vi.fn()} />,
    );
    const btn = screen.getByRole("button", {
      name: /Approve task "Deploy service" — advance to PLANNING/i,
    });
    expect(btn).toBeDefined();
  });

  it("renders the Deny/Cancel button for non-terminal tasks", () => {
    render(
      <ApprovalPanel task={makeTask()} onApprove={vi.fn()} onDeny={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: /Deny and cancel/i })).toBeDefined();
  });

  it("shows terminal message for DONE state", () => {
    render(
      <ApprovalPanel
        task={makeTask({ state: "DONE" })}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(screen.getByText(/terminal state/i)).toBeDefined();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("shows terminal message for FAILED state", () => {
    render(
      <ApprovalPanel
        task={makeTask({ state: "FAILED" })}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(screen.getByText(/terminal state/i)).toBeDefined();
  });

  it("shows terminal message for CANCELLED state", () => {
    render(
      <ApprovalPanel
        task={makeTask({ state: "CANCELLED" })}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(screen.getByText(/terminal state/i)).toBeDefined();
  });

  it("calls onApprove with taskId and next state on Approve click", () => {
    const onApprove = vi.fn();
    render(
      <ApprovalPanel task={makeTask()} onApprove={onApprove} onDeny={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Approve task/i }));
    expect(onApprove).toHaveBeenCalledWith("task-001", "PLANNING");
  });

  it("calls onDeny with taskId on Deny click", () => {
    const onDeny = vi.fn();
    render(
      <ApprovalPanel task={makeTask()} onApprove={vi.fn()} onDeny={onDeny} />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Deny and cancel/i }));
    expect(onDeny).toHaveBeenCalledWith("task-001");
  });

  it("disables both buttons when loading is true", () => {
    render(
      <ApprovalPanel
        task={makeTask()}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
        loading={true}
      />,
    );
    screen.getAllByRole("button").forEach((btn) => {
      expect((btn as HTMLButtonElement).disabled).toBe(true);
    });
  });

  it("shows error message when error prop is provided", () => {
    render(
      <ApprovalPanel
        task={makeTask()}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
        error={new Error("Server unreachable")}
      />,
    );
    expect(screen.getByText(/Server unreachable/i)).toBeDefined();
  });

  it("shows Processing message when loading is true", () => {
    render(
      <ApprovalPanel
        task={makeTask()}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
        loading={true}
      />,
    );
    expect(screen.getByText(/Processing/i)).toBeDefined();
  });

  it("maps EXECUTING → VALIDATING for next state", () => {
    render(
      <ApprovalPanel
        task={makeTask({ state: "EXECUTING" })}
        onApprove={vi.fn()}
        onDeny={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("button", { name: /advance to VALIDATING/i }),
    ).toBeDefined();
  });
});
