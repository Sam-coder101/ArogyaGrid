import { useState, useCallback, useRef } from "react";

export type AgentStatus = "idle" | "running" | "success" | "error";

export interface AgentState {
  id: string;
  label: string;
  icon: string;
  status: AgentStatus;
  output?: unknown;
  error?: string;
  timestamp?: string;
}

export interface DemoEvent {
  event: string;
  data?: unknown;
  message?: string;
  phase?: number;
}

const INITIAL_AGENTS: AgentState[] = [
  { id: "orchestrator",   label: "Orchestrator Agent",              icon: "🎯", status: "idle" },
  { id: "forecast",       label: "Demand Forecast Agent",           icon: "📈", status: "idle" },
  { id: "warning",        label: "Stock-out Early Warning Agent",   icon: "⚠️", status: "idle" },
  { id: "redistribution", label: "Redistribution Optimizer Agent",  icon: "🔄", status: "idle" },
  { id: "prescription",   label: "Prescription Explainer Agent",    icon: "💊", status: "idle" },
  { id: "epi",            label: "Epidemiological Signal Agent",    icon: "🦠", status: "idle" },
  { id: "poster",         label: "Awareness Poster Agent",          icon: "📢", status: "idle" },
];

const EVENT_AGENT_MAP: Record<string, string> = {
  workflow_start:         "orchestrator",
  phase:                  "orchestrator",
  forecast:               "forecast",
  no_alert:               "warning",
  alert:                  "warning",
  redistribution:         "redistribution",
  prescription_explanation: "prescription",
  epi_signals:            "epi",
  poster:                 "poster",
  demo_complete:          "orchestrator",
};

export function useDemoLoop() {
  const [agents, setAgents] = useState<AgentState[]>(INITIAL_AGENTS);
  const [events, setEvents] = useState<DemoEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [done, setDone]       = useState(false);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const setAgentStatus = useCallback((id: string, status: AgentStatus, output?: unknown, error?: string) => {
    setAgents(prev => prev.map(a =>
      a.id === id ? { ...a, status, output, error, timestamp: new Date().toISOString() } : a
    ));
  }, []);

  const reset = useCallback(() => {
    setAgents(INITIAL_AGENTS);
    setEvents([]);
    setRunning(false);
    setDone(false);
    setSummary(null);
  }, []);

  const run = useCallback(async () => {
    reset();
    setRunning(true);
    setAgentStatus("orchestrator", "running");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("http://localhost:8000/api/demo/run-full-loop", {
        method: "POST",
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done: streamDone, value } = await reader.read();
        if (streamDone) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const evt: DemoEvent = JSON.parse(line.slice(6));
            setEvents(prev => [...prev, evt]);

            const agentId = EVENT_AGENT_MAP[evt.event];

            switch (evt.event) {
              case "demo_start":
              case "workflow_start":
              case "phase":
                setAgentStatus("orchestrator", "running");
                break;

              case "forecast":
                setAgentStatus("orchestrator", "success");
                setAgentStatus("forecast", "success", evt.data);
                break;

              case "alert":
                setAgentStatus("warning", "success", evt.data);
                break;

              case "no_alert":
                if (agents.find(a => a.id === "warning")?.status === "idle")
                  setAgentStatus("warning", "running");
                break;

              case "redistribution":
                setAgentStatus("redistribution", "success", evt.data);
                break;

              case "prescription_explanation":
                setAgentStatus("prescription", "success", evt.data);
                break;

              case "epi_signals":
                setAgentStatus("epi", "success", evt.data);
                break;

              case "poster":
                setAgentStatus("poster", "success", evt.data);
                break;

              case "workflow_complete":
                if ((evt as unknown as Record<string, unknown>).summary) {
                  setSummary((evt as unknown as Record<string, unknown>).summary as Record<string, unknown>);
                }
                break;

              case "demo_complete":
                setAgentStatus("orchestrator", "success");
                setDone(true);
                break;

              case "error":
                if (agentId) setAgentStatus(agentId, "error", undefined, String((evt as unknown as Record<string, unknown>).error ?? "Unknown error"));
                break;
            }

            // Mark in-progress agents for subsequent steps
            if (evt.event === "alert") setAgentStatus("redistribution", "running");
            if (evt.event === "redistribution") setAgentStatus("prescription", "running");
            if (evt.event === "prescription_explanation") setAgentStatus("epi", "running");
            if (evt.event === "epi_signals") setAgentStatus("poster", "running");

          } catch { /* skip malformed lines */ }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") {
        setAgentStatus("orchestrator", "error", undefined, String(err));
      }
    } finally {
      setRunning(false);
    }
  }, [reset, setAgentStatus, agents]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setRunning(false);
  }, []);

  return { agents, events, running, done, summary, run, stop, reset };
}
