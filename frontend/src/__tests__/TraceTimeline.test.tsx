import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TraceTimeline } from "../components/agent/TraceTimeline";
import type { AgentEvent } from "../types/agentRuntime";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeEvent(overrides: Partial<AgentEvent> = {}): AgentEvent {
  return {
    event_id: "evt-001",
    event_type: "task_state_transition",
    trace_id: "trace-001",
    run_id: null,
    task_id: "task-001",
    step_id: null,
    occurred_at: "2026-04-18T10:00:00.000Z",
    sequence: 0,
    payload: {},
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Rendering — empty state
// ---------------------------------------------------------------------------

describe("TraceTimeline", () => {
  it("renders a section with accessible label", () => {
    render(<TraceTimeline events={[]} connected={false} />);
    expect(screen.getByRole("region", { name: /Trace timeline/i })).toBeDefined();
  });

  it("shows empty message when there are no events", () => {
    render(<TraceTimeline events={[]} connected={false} />);
    expect(screen.getByText(/No events yet/i)).toBeDefined();
  });

  it("does not render the Clear button when events is empty", () => {
    render(<TraceTimeline events={[]} connected={false} onClear={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /Clear/i })).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Live indicator
  // ---------------------------------------------------------------------------

  it("shows Live indicator when connected is true", () => {
    render(<TraceTimeline events={[]} connected={true} />);
    expect(screen.getByLabelText(/Live — connected/i)).toBeDefined();
  });

  it("hides Live indicator when connected is false", () => {
    render(<TraceTimeline events={[]} connected={false} />);
    expect(screen.queryByLabelText(/Live — connected/i)).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Events rendered
  // ---------------------------------------------------------------------------

  it("renders event list when events are present", () => {
    render(<TraceTimeline events={[makeEvent()]} connected={false} />);
    const list = screen.getByRole("list", { name: /Agent events/i });
    expect(list).toBeDefined();
  });

  it("renders a list item per event", () => {
    const events = [
      makeEvent({ event_id: "e1", sequence: 0 }),
      makeEvent({ event_id: "e2", sequence: 1 }),
    ];
    render(<TraceTimeline events={events} connected={false} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("renders the human-friendly event type label", () => {
    render(<TraceTimeline events={[makeEvent()]} connected={false} />);
    expect(screen.getByLabelText(/Event type: State transition/i)).toBeDefined();
  });

  it("renders a time element per event", () => {
    const { container } = render(<TraceTimeline events={[makeEvent()]} connected={false} />);
    const times = container.querySelectorAll("time");
    expect(times).toHaveLength(1);
  });

  it("renders the Clear button when events are present", () => {
    render(
      <TraceTimeline events={[makeEvent()]} connected={false} onClear={vi.fn()} />,
    );
    expect(screen.getByRole("button", { name: /Clear all trace events/i })).toBeDefined();
  });

  it("calls onClear when Clear is clicked", () => {
    const onClear = vi.fn();
    render(<TraceTimeline events={[makeEvent()]} connected={false} onClear={onClear} />);
    fireEvent.click(screen.getByRole("button", { name: /Clear all trace events/i }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("renders step_id badge when step_id is present", () => {
    render(
      <TraceTimeline events={[makeEvent({ step_id: "step-42" })]} connected={false} />,
    );
    expect(screen.getByLabelText(/Step: step-42/i)).toBeDefined();
  });

  it("does not render step badge when step_id is null", () => {
    render(<TraceTimeline events={[makeEvent({ step_id: null })]} connected={false} />);
    expect(screen.queryByLabelText(/Step:/i)).toBeNull();
  });

  it("has aria-live=polite on the event list", () => {
    const { container } = render(
      <TraceTimeline events={[makeEvent()]} connected={false} />,
    );
    const ol = container.querySelector("ol");
    expect(ol?.getAttribute("aria-live")).toBe("polite");
  });
});
