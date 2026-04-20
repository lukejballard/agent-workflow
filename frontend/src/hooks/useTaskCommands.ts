/**
 * useTaskCommands — typed async command helpers for mutating task state.
 *
 * Wraps the API layer with unified loading / error state so callers do not
 * need to manage repetitive try/catch/finally blocks.
 */

import { useState, useCallback } from "react";
import { createTask, transitionTask, createPlan } from "../api/agentRuntime";
import type {
  AgentPlan,
  AgentTask,
  CreatePlanPayload,
  CreateTaskPayload,
  TransitionPayload,
} from "../types/agentRuntime";

export interface UseTaskCommandsResult {
  loading: boolean;
  error: Error | null;
  createTask: (payload: CreateTaskPayload) => Promise<AgentTask | null>;
  transitionTask: (
    taskId: string,
    payload: TransitionPayload,
  ) => Promise<AgentTask | null>;
  createPlan: (
    taskId: string,
    payload: CreatePlanPayload,
  ) => Promise<AgentPlan | null>;
}

export function useTaskCommands(): UseTaskCommandsResult {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const runCommand = useCallback(
    async <T>(fn: () => Promise<T>): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        return await fn();
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const handleCreateTask = useCallback(
    (payload: CreateTaskPayload) =>
      runCommand<AgentTask>(() => createTask(payload)),
    [runCommand],
  );

  const handleTransitionTask = useCallback(
    (taskId: string, payload: TransitionPayload) =>
      runCommand<AgentTask>(() => transitionTask(taskId, payload)),
    [runCommand],
  );

  const handleCreatePlan = useCallback(
    (taskId: string, payload: CreatePlanPayload) =>
      runCommand<AgentPlan>(() => createPlan(taskId, payload)),
    [runCommand],
  );

  return {
    loading,
    error,
    createTask: handleCreateTask,
    transitionTask: handleTransitionTask,
    createPlan: handleCreatePlan,
  };
}
