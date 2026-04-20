/**
 * AgentControlCenter — task queue page with new-task form.
 *
 * This page is deliberately thin:
 * - Data fetching and mutations go through `useTaskCommands`.
 * - Display is delegated to `TaskCard` components.
 * - The task list is polled every 10 s while no SSE list endpoint exists.
 *
 * Accessibility:
 * - `<main>` landmark for the page body.
 * - `aria-live` region announces task list changes.
 * - Form inputs have associated `<label>` elements.
 * - Loading state sets `aria-busy` on the list container.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { TaskCard } from "../components/agent/TaskCard";
import { useTaskCommands } from "../hooks/useTaskCommands";
import { listTasks } from "../api/agentRuntime";
import type { AgentTask } from "../types/agentRuntime";

const POLL_INTERVAL_MS = 10_000;

export default function AgentControlCenter() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [fetchError, setFetchError] = useState<Error | null>(null);
  const [polling, setPolling] = useState(false);
  const [objective, setObjective] = useState("");
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { loading, error: cmdError, createTask } = useTaskCommands();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await listTasks();
      setTasks(data);
      setFetchError(null);
    } catch (err) {
      setFetchError(err instanceof Error ? err : new Error(String(err)));
    }
  }, []);

  // Poll the task list on mount and every POLL_INTERVAL_MS milliseconds.
  useEffect(() => {
    setPolling(true);
    void fetchTasks();
    intervalRef.current = setInterval(() => void fetchTasks(), POLL_INTERVAL_MS);
    return () => {
      if (intervalRef.current !== null) clearInterval(intervalRef.current);
      setPolling(false);
    };
  }, [fetchTasks]);

  async function handleCreateTask(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (objective.trim() === "") return;
    const task = await createTask({ objective: objective.trim() });
    if (task !== null) {
      setObjective("");
      await fetchTasks();
    }
  }

  const pendingCount = tasks.filter(
    (t) => !["DONE", "FAILED", "CANCELLED"].includes(t.state),
  ).length;

  return (
    <main aria-label="Agent Control Center" className="control-center">
      <header className="control-center__header">
        <h1>Agent Control Center</h1>
        <p className="control-center__summary">
          {tasks.length} task{tasks.length !== 1 ? "s" : ""} ·{" "}
          {pendingCount} active
        </p>
      </header>

      {/* New-task form */}
      <section aria-label="Create a new task" className="control-center__new-task">
        <h2>New task</h2>
        <form onSubmit={(e) => void handleCreateTask(e)} noValidate>
          <div className="form-row">
            <label htmlFor="objective-input">Objective</label>
            <input
              id="objective-input"
              type="text"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Describe the task objective…"
              aria-required="true"
              disabled={loading}
              className="form-row__input"
            />
          </div>

          <button
            type="submit"
            disabled={loading || objective.trim() === ""}
            aria-disabled={loading || objective.trim() === ""}
            className="btn btn--primary"
            aria-label="Create new task"
          >
            {loading ? "Creating…" : "Create task"}
          </button>

          {cmdError !== null && (
            <p
              role="alert"
              aria-live="assertive"
              className="form-error"
            >
              {cmdError.message}
            </p>
          )}
        </form>
      </section>

      {/* Task list */}
      <section aria-label="Task queue" className="control-center__task-list">
        <h2>Task queue</h2>

        {fetchError !== null && (
          <p role="alert" className="fetch-error">
            Failed to load tasks: {fetchError.message}
          </p>
        )}

        <div
          aria-busy={polling}
          aria-live="polite"
          aria-relevant="additions removals"
          className="task-grid"
        >
          {tasks.length === 0 && !fetchError && (
            <p className="task-grid__empty">No tasks yet. Create one above.</p>
          )}
          {tasks.map((task) => (
            <TaskCard
              key={task.task_id}
              task={task}
              onSelect={(id) => setSelectedTaskId(id === selectedTaskId ? null : id)}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
