/**
 * useTaskStream — subscribes to the SSE event stream for a single task.
 *
 * The server endpoint is `GET /api/tasks/{taskId}/events`.  Events arrive as
 * JSON-encoded AgentEvent objects.  On connection error the hook stores the
 * error and closes the source; callers can re-mount to reconnect.
 */

import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "../types/agentRuntime";

const BASE: string = (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "/api";

export interface UseTaskStreamResult {
  events: AgentEvent[];
  connected: boolean;
  error: Error | null;
  clearEvents: () => void;
}

export function useTaskStream(taskId: string | null): UseTaskStreamResult {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (taskId === null) return;

    const url = `${BASE}/tasks/${taskId}/events`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.addEventListener("open", () => {
      setConnected(true);
      setError(null);
    });

    source.addEventListener("message", (e: MessageEvent<string>) => {
      try {
        const ev = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev, ev]);
      } catch {
        // Non-JSON keepalive frames — silently skip.
      }
    });

    source.addEventListener("error", () => {
      setConnected(false);
      setError(new Error("Event stream disconnected."));
      source.close();
    });

    return () => {
      source.close();
      setConnected(false);
      sourceRef.current = null;
    };
  }, [taskId]);

  function clearEvents(): void {
    setEvents([]);
  }

  return { events, connected, error, clearEvents };
}
