'use client';
import { motion } from 'framer-motion';
import type { AgentState } from "@/lib/useDemoLoop";

interface Props { agents: AgentState[]; }

const statusColors: Record<string, string> = {
  idle:    "text-[var(--color-ink)]/40",
  running: "text-[var(--color-primary)]",
  success: "text-[var(--color-signal-ok)]",
  error:   "text-[var(--color-signal-critical)]",
};
const statusDot: Record<string, string> = {
  idle:    "bg-[var(--color-line)]",
  running: "bg-[var(--color-primary)] animate-pulse",
  success: "bg-[var(--color-signal-ok)]",
  error:   "bg-[var(--color-signal-critical)]",
};

export default function AgentPipeline({ agents }: Props) {
  return (
    <div className="flex flex-col gap-3">
      {agents.map((agent, i) => (
        <motion.div 
          key={agent.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: i * 0.1 }}
        >
          <div className={`p-4 rounded-xl flex items-center gap-3 transition-all ${agent.status === 'running' ? 'border border-[var(--color-primary)]/50 bg-[var(--color-primary)]/5 premium-shadow hover-lift' : 'border border-[var(--color-line)] bg-[var(--color-surface)]/50 shadow-sm'}`}>
            <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 shadow-sm ${statusDot[agent.status]}`} />
            <div className="flex-1 min-w-0">
              <div className={`text-caption font-semibold ${statusColors[agent.status]}`}>
                {agent.label}
              </div>
              {agent.status === "running" && (
                <div className="text-xs mt-0.5 text-[var(--color-primary)] font-medium animate-pulse">
                  Executing...
                </div>
              )}
              {agent.status === "success" && agent.output != null && (
                <div className="text-xs mt-0.5 truncate text-[var(--color-ink)]/60">
                  {getOutputSummary(agent.id, agent.output)}
                </div>
              )}
              {agent.status === "error" && agent.error && (
                <div className="text-xs mt-0.5 text-[var(--color-signal-critical)]">
                  {String(agent.error).slice(0, 80)}
                </div>
              )}
            </div>
          </div>
          {i < agents.length - 1 && (
            <div className="ml-5 w-px h-3 bg-[var(--color-line)] opacity-50" />
          )}
        </motion.div>
      ))}
    </div>
  );
}

function getOutputSummary(agentId: string, output: unknown): string {
  if (!output) return "";
  try {
    if (agentId === "forecast") {
      const d = output as Record<string, unknown>;
      return `${d.drug_name}: ${d.predicted_qty} units / ${d.horizon_days}d  (${Math.round((d.confidence as number)*100)}% conf)`;
    }
    if (agentId === "warning") {
      const d = output as Record<string, unknown>;
      return `${d.severity} alert — ${d.drug_name} at ${d.phc_name} (${d.days_remaining}d left)`;
    }
    if (agentId === "redistribution") {
      const arr = output as Record<string, unknown>[];
      if (arr.length > 0) return `${arr[0].from_phc_name} → ${arr[0].to_phc_name}: ${arr[0].qty} units`;
    }
    if (agentId === "prescription") {
      const d = output as Record<string, unknown>;
      const drugs = (d.drugs as unknown[]) ?? [];
      return `${drugs.length} drug(s) explained`;
    }
    if (agentId === "epi") {
      const arr = output as Record<string, unknown>[];
      if (arr.length > 0) return `${arr[0].disease_hypothesis} — ${arr[0].geo_block}`;
      return "No signals above threshold";
    }
    if (agentId === "poster") {
      const d = output as Record<string, unknown>;
      return `Poster: ${d.disease_hypothesis} / ${d.geo_target}`;
    }
  } catch { /* */ }
  return "Completed";
}
