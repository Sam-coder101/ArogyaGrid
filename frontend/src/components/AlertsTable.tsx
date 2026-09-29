'use client';
import type { Alert } from "@/lib/api";
import { api } from "@/lib/api";
import { useState } from "react";

interface Props { alerts: Alert[]; onRefresh: () => void; }

const severityBadge: Record<string, string> = {
  HIGH:   "bg-[var(--color-signal-critical)]/10 text-[var(--color-signal-critical)] border-[var(--color-signal-critical)]/20",
  MEDIUM: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  LOW:    "bg-[var(--color-accent)]/10 text-[var(--color-accent)] border-[var(--color-accent)]/20",
};

export default function AlertsTable({ alerts, onRefresh }: Props) {
  const [acking, setAcking] = useState<number | null>(null);

  async function ack(id: number) {
    setAcking(id);
    await api.ackAlert(id);
    onRefresh();
    setAcking(null);
  }

  if (alerts.length === 0) {
    return (
      <div className="glass-surface p-12 text-center rounded-2xl premium-shadow flex flex-col items-center justify-center">
        <div className="text-4xl mb-4 p-4 bg-[var(--color-signal-ok)]/10 rounded-full">✅</div>
        <h3 className="text-lg font-bold text-[var(--color-ink)] mb-2">System Healthy</h3>
        <p className="text-[var(--color-ink)]/60 max-w-md">No open stock-out alerts. Run the demo loop to generate AI-predicted alerts.</p>
      </div>
    );
  }

  return (
    <div className="glass-surface overflow-hidden rounded-2xl premium-shadow">
      <div className="p-5 border-b border-[var(--color-line)] bg-white/40">
        <h3 className="font-bold text-[var(--color-ink)] flex items-center gap-2">
          <span className="text-amber-500">⚠️</span> Open Stock-Out Alerts ({alerts.length})
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-line)] bg-[var(--color-canvas)]/50">
              {["Severity", "PHC", "District", "State", "Medicine", "Days Left", "Predicted Stock-out", "Action"].map(h => (
                <th key={h} className="text-left px-5 py-4 font-bold text-xs uppercase tracking-wider text-[var(--color-ink)]/50">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-line)]">
            {alerts.map((a, i) => (
              <tr key={a.id} className="hover:bg-[var(--color-primary)]/5 transition-colors">
                <td className="px-5 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${severityBadge[a.severity] || severityBadge.LOW}`}>
                    {a.severity}
                  </span>
                </td>
                <td className="px-5 py-4 font-semibold text-[var(--color-ink)]">{a.phc_name}</td>
                <td className="px-5 py-4 text-[var(--color-ink)]/70">{a.district}</td>
                <td className="px-5 py-4 text-[var(--color-ink)]/70">{a.state}</td>
                <td className="px-5 py-4 font-bold text-[var(--color-primary)]">{a.drug_name}</td>
                <td className="px-5 py-4 font-semibold">
                  <span className={a.severity === "HIGH" ? "text-[var(--color-signal-critical)]" : "text-amber-600"}>
                    {a.recommended_action?.match(/(\d+) day/)?.[1] ?? "—"} days
                  </span>
                </td>
                <td className="px-5 py-4 text-[var(--color-ink)]/60">
                  {a.predicted_date ? new Date(a.predicted_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—"}
                </td>
                <td className="px-5 py-4">
                  <button onClick={() => ack(a.id)} disabled={acking === a.id}
                          className="text-xs px-4 py-2 rounded-lg font-bold transition-all bg-[var(--color-signal-ok)]/10 text-[var(--color-signal-ok)] hover:bg-[var(--color-signal-ok)]/20 border border-[var(--color-signal-ok)]/20 disabled:opacity-50 hover-lift">
                    {acking === a.id ? "Processing..." : "Acknowledge"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
