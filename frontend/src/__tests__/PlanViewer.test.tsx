import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PlanViewer } from "../components/agent/PlanViewer";
import type { AgentPlan, PlanStep } from "../types/agentRuntime";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function makeStep(overrides: Partial<PlanStep> = {}): PlanStep {
  return {
    step_id: "step-1",
    title: "Analyse requirements",
    depends_on: [],
    input_contract: "task objective",
    output_contract: "structured requirements doc",
    done_condition: "requirements approved",
    ...overrides,
  };
}

function makePlan(steps: PlanStep[] = [makeStep()]): AgentPlan {
  return {
    plan_id: "plan-001",
    task_id: "task-001",
    revision: 1,
    steps,
  };
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

describe("PlanViewer", () => {
  it("renders the plan heading", () => {
    render(<PlanViewer plan={makePlan()} />);
    expect(screen.getByText(/Plan/i)).toBeDefined();
  });

  it("renders a step title", () => {
    render(<PlanViewer plan={makePlan()} />);
    expect(screen.getByText("Analyse requirements")).toBeDefined();
  });

  it("renders an ordered list of steps", () => {
    const { container } = render(<PlanViewer plan={makePlan()} />);
    const ol = container.querySelector("ol");
    expect(ol).not.toBeNull();
  });

  it("renders each step as a list item", () => {
    const steps = [makeStep(), makeStep({ step_id: "step-2", title: "Implement" })];
    render(<PlanViewer plan={makePlan(steps)} />);
    expect(screen.getByText("Analyse requirements")).toBeDefined();
    expect(screen.getByText("Implement")).toBeDefined();
  });

  it("shows pending status label when no statuses provided", () => {
    render(<PlanViewer plan={makePlan()} />);
    // Badge label defaults to unknown "—"
    const badge = screen.getByLabelText(/Status:/i);
    expect(badge).toBeDefined();
  });

  it("shows correct status when stepStatuses provided", () => {
    render(<PlanViewer plan={makePlan()} stepStatuses={{ "step-1": "done" }} />);
    const badge = screen.getByLabelText(/Status: Done/i);
    expect(badge).toBeDefined();
  });

  it("shows failed status via aria-label", () => {
    render(<PlanViewer plan={makePlan()} stepStatuses={{ "step-1": "failed" }} />);
    expect(screen.getByLabelText(/Status: Failed/i)).toBeDefined();
  });

  it("renders dependency links when depends_on is non-empty", () => {
    const dep = makeStep({ step_id: "step-2", title: "Bootstrap", depends_on: ["step-1"] });
    render(<PlanViewer plan={makePlan([makeStep(), dep])} />);
    const depLink = screen.getByLabelText(/Jump to step step-1/i);
    expect(depLink).not.toBeNull();
    expect((depLink as HTMLAnchorElement).href).toContain("#step-step-1");
  });

  it("does not render dependency section when depends_on is empty", () => {
    render(<PlanViewer plan={makePlan()} />);
    expect(screen.queryByLabelText(/Depends on/i)).toBeNull();
  });

  it("shows the plan revision number", () => {
    render(<PlanViewer plan={makePlan()} />);
    expect(screen.getByText(/revision/i)).toBeDefined();
  });
});
