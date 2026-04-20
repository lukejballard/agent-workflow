/**
 * PlanViewer — renders a plan's steps with their dependency relationships.
 *
 * Accessibility:
 * - Ordered list (`<ol>`) conveys natural step sequence.
 * - Dependency badges use aria-describedby to link back to their parent step.
 */

import type { AgentPlan, PlanStep, StepExecutionStatus } from "../../types/agentRuntime";

interface PlanViewerProps {
  plan: AgentPlan;
  /** Optional map of step_id → execution status for live progress display. */
  stepStatuses?: Record<string, StepExecutionStatus>;
}

const STATUS_LABEL: Record<StepExecutionStatus, string> = {
  pending: "Pending",
  in_progress: "In progress",
  done: "Done",
  failed: "Failed",
  blocked: "Blocked",
};

function statusClass(status: StepExecutionStatus | undefined): string {
  if (status === "done") return "step-status step-status--done";
  if (status === "failed") return "step-status step-status--failed";
  if (status === "in_progress") return "step-status step-status--active";
  if (status === "blocked") return "step-status step-status--blocked";
  return "step-status step-status--pending";
}

function StepItem({
  step,
  status,
}: {
  step: PlanStep;
  status: StepExecutionStatus | undefined;
}) {
  const descId = `step-desc-${step.step_id}`;

  return (
    <li className="plan-step" id={`step-${step.step_id}`}>
      <div className="plan-step__row">
        <span className="plan-step__id" aria-hidden="true">
          {step.step_id}
        </span>
        <strong className="plan-step__title">{step.title}</strong>
        <span
          className={statusClass(status)}
          aria-label={`Status: ${status !== undefined ? STATUS_LABEL[status] : "Unknown"}`}
        >
          {status !== undefined ? STATUS_LABEL[status] : "—"}
        </span>
      </div>

      <div id={descId} className="plan-step__contracts">
        <span>
          <strong>In:</strong> {step.input_contract}
        </span>
        <span>
          <strong>Done when:</strong> {step.done_condition}
        </span>
      </div>

      {step.depends_on.length > 0 && (
        <p className="plan-step__deps" aria-label="Depends on">
          Depends on:{" "}
          {step.depends_on.map((dep) => (
            <a
              key={dep}
              href={`#step-${dep}`}
              aria-label={`Jump to step ${dep}`}
              className="plan-step__dep-link"
            >
              {dep}
            </a>
          ))}
        </p>
      )}
    </li>
  );
}

export function PlanViewer({ plan, stepStatuses = {} }: PlanViewerProps) {
  return (
    <section aria-label="Plan viewer" className="plan-viewer">
      <header className="plan-viewer__header">
        <h2>Plan</h2>
        <span className="plan-viewer__meta">
          {plan.steps.length} step{plan.steps.length !== 1 ? "s" : ""} · revision{" "}
          {plan.revision}
        </span>
      </header>

      {plan.steps.length === 0 ? (
        <p className="plan-viewer__empty">No steps defined.</p>
      ) : (
        <ol className="plan-viewer__steps" aria-label="Plan steps">
          {plan.steps.map((step) => (
            <StepItem
              key={step.step_id}
              step={step}
              status={stepStatuses[step.step_id]}
            />
          ))}
        </ol>
      )}
    </section>
  );
}
