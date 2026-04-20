/**
 * Typed API helpers for the agent-runtime backend.
 *
 * One function per endpoint.  All network logic lives here; components and
 * pages use these only through hooks.
 */

import type {
  AgentPlan,
  AgentTask,
  CreatePlanPayload,
  CreateTaskPayload,
  TransitionPayload,
} from "../types/agentRuntime";

const BASE: string = (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} → ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

export function createTask(payload: CreateTaskPayload): Promise<AgentTask> {
  return request<AgentTask>("/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTasks(): Promise<AgentTask[]> {
  return request<AgentTask[]>("/tasks");
}

export function getTask(taskId: string): Promise<AgentTask> {
  return request<AgentTask>(`/tasks/${taskId}`);
}

export function transitionTask(
  taskId: string,
  payload: TransitionPayload,
): Promise<AgentTask> {
  return request<AgentTask>(`/tasks/${taskId}/transitions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Plans
// ---------------------------------------------------------------------------

export function createPlan(
  taskId: string,
  payload: CreatePlanPayload,
): Promise<AgentPlan> {
  return request<AgentPlan>(`/tasks/${taskId}/plan`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTaskPlan(taskId: string): Promise<AgentPlan> {
  return request<AgentPlan>(`/tasks/${taskId}/plan`);
}
