import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTaskCommands } from "../hooks/useTaskCommands";

// ---------------------------------------------------------------------------
// Module mock — replace the whole API module with controllable stubs
// ---------------------------------------------------------------------------

vi.mock("../api/agentRuntime", () => ({
  createTask: vi.fn(),
  transitionTask: vi.fn(),
  createPlan: vi.fn(),
}));

import * as apiModule from "../api/agentRuntime";

const mockCreateTask = vi.mocked(apiModule.createTask);
const mockTransitionTask = vi.mocked(apiModule.transitionTask);
const mockCreatePlan = vi.mocked(apiModule.createPlan);

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const FAKE_TASK = {
  task_id: "t1",
  objective: "Do something",
  state: "PENDING" as const,
  plan: null,
  trace_id: "tr-1",
  created_at: "2026-04-18T10:00:00.000Z",
  updated_at: "2026-04-18T10:00:00.000Z",
};

const FAKE_PLAN = {
  plan_id: "plan-1",
  task_id: "t1",
  revision: 1,
  steps: [],
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

describe("useTaskCommands", () => {
  it("starts with loading=false and error=null", () => {
    const { result } = renderHook(() => useTaskCommands());
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // createTask
  // ---------------------------------------------------------------------------

  it("returns the task on successful createTask", async () => {
    mockCreateTask.mockResolvedValue(FAKE_TASK);
    const { result } = renderHook(() => useTaskCommands());

    let task: typeof FAKE_TASK | null = null;
    await act(async () => {
      task = await result.current.createTask({ objective: "Do something" });
    });

    expect(task).toEqual(FAKE_TASK);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets error and returns null when createTask throws", async () => {
    mockCreateTask.mockRejectedValue(new Error("Network error"));
    const { result } = renderHook(() => useTaskCommands());

    let task: typeof FAKE_TASK | null = FAKE_TASK;
    await act(async () => {
      task = await result.current.createTask({ objective: "Fail" });
    });

    expect(task).toBeNull();
    expect(result.current.error?.message).toBe("Network error");
    expect(result.current.loading).toBe(false);
  });

  // ---------------------------------------------------------------------------
  // transitionTask
  // ---------------------------------------------------------------------------

  it("returns updated task on successful transitionTask", async () => {
    const updated = { ...FAKE_TASK, state: "PLANNING" as const };
    mockTransitionTask.mockResolvedValue(updated);
    const { result } = renderHook(() => useTaskCommands());

    let res: typeof updated | null = null;
    await act(async () => {
      res = await result.current.transitionTask("t1", { target_state: "PLANNING" });
    });

    expect(res?.state).toBe("PLANNING");
    expect(result.current.error).toBeNull();
  });

  it("sets error when transitionTask throws", async () => {
    mockTransitionTask.mockRejectedValue(new Error("Invalid transition"));
    const { result } = renderHook(() => useTaskCommands());

    await act(async () => {
      await result.current.transitionTask("t1", { target_state: "DONE" });
    });

    expect(result.current.error?.message).toBe("Invalid transition");
  });

  // ---------------------------------------------------------------------------
  // createPlan
  // ---------------------------------------------------------------------------

  it("returns plan on successful createPlan", async () => {
    mockCreatePlan.mockResolvedValue(FAKE_PLAN);
    const { result } = renderHook(() => useTaskCommands());

    let plan: typeof FAKE_PLAN | null = null;
    await act(async () => {
      plan = await result.current.createPlan("t1", { steps: [] });
    });

    expect(plan?.plan_id).toBe("plan-1");
    expect(result.current.error).toBeNull();
  });

  it("sets error when createPlan throws", async () => {
    mockCreatePlan.mockRejectedValue(new Error("Plan creation failed"));
    const { result } = renderHook(() => useTaskCommands());

    await act(async () => {
      await result.current.createPlan("t1", { steps: [] });
    });

    expect(result.current.error?.message).toBe("Plan creation failed");
  });

  // ---------------------------------------------------------------------------
  // Error is cleared on next successful command
  // ---------------------------------------------------------------------------

  it("clears previous error on next successful createTask", async () => {
    mockCreateTask
      .mockRejectedValueOnce(new Error("First failure"))
      .mockResolvedValueOnce(FAKE_TASK);
    const { result } = renderHook(() => useTaskCommands());

    await act(async () => {
      await result.current.createTask({ objective: "fail" });
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.createTask({ objective: "ok" });
    });
    expect(result.current.error).toBeNull();
  });
});
