/**
 * TraceTimeline — chronological list of agent events for a task.
 *
 * Accessibility:
 * - `aria-live="polite"` announces new events to screen readers.
 * - Each event is a `<li>` with semantic time and event-type information.
 * - "Clear" button has an explicit aria-label.
 */

import type { AgentEvent } from "../../types/agentRuntime";

interface TraceTimelineProps {
  events: AgentEvent[];
  connected: boolean;
  onClear?: () => void;
}

const EVENT_TYPE_MAP: Record<string, string> = {
  task_state_transition: "State transition",
  tool_call_started: "Tool started",
  tool_call_finished: "Tool finished",
  approval_required: "Approval required",
};

function formatEventType(raw: string): string {
  return EVENT_TYPE_MAP[raw] ?? raw;
}

export function TraceTimeline({ events, connected, onClear }: TraceTimelineProps) {
  return (
    <section aria-label="Trace timeline" className="trace-timeline">
      <header className="trace-timeline__header">
        <h2>
          Trace
          {connected && (
            <span
              className="trace-timeline__live-indicator"
              aria-label="Live — connected"
              role="status"
            >
              {" "}
              ● Live
            </span>
          )}
        </h2>

        {onClear !== undefined && events.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            aria-label="Clear all trace events"
            className="trace-timeline__clear-btn"
          >
            Clear
          </button>
        )}
      </header>

      {events.length === 0 ? (
        <p className="trace-timeline__empty">No events yet.</p>
      ) : (
        <ol
          className="trace-timeline__list"
          aria-label="Agent events"
          aria-live="polite"
          aria-relevant="additions"
        >
          {events.map((ev) => (
            <li key={ev.event_id} className="trace-event">
              <time
                dateTime={ev.occurred_at}
                className="trace-event__time"
                aria-label={`Event time: ${new Date(ev.occurred_at).toLocaleString()}`}
              >
                {new Date(ev.occurred_at).toLocaleTimeString()}
              </time>

              <span className="trace-event__type" aria-label={`Event type: ${formatEventType(ev.event_type)}`}>
                {formatEventType(ev.event_type)}
              </span>

              <span className="trace-event__task-id" aria-label={`Task: ${ev.task_id}`}>
                {ev.task_id.slice(0, 8)}…
              </span>

              {ev.step_id !== null && (
                <span className="trace-event__step" aria-label={`Step: ${ev.step_id}`}>
                  step: {ev.step_id}
                </span>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
