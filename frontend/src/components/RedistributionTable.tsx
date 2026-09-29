'use client';
import type { Redistribution } from "@/lib/api";
import { api } from "@/lib/api";
import { useState } from "react";

interface Props { recs: Redistribution[]; onRefresh: () => void; }

export default function RedistributionTable({ recs, onRefresh }: Props) {
  const [acting, setActing] = useState<number | null>(null);

  async function approve(id: number) { setActing(id); await api.approveRedist(id); onRefresh(); setActing(null); }
  async function reject(id: number)  { setActing(id); await api.rejectRedist(id);  onRefresh(); setActing(null); }

  if (recs.length === 0) return (
    <div className="glass-surface p-12 text-center rounded-2xl premium-shadow flex flex-col items-center justify-center">
      <div className="text-4xl mb-4 p-4 bg-[var(--color-primary)]/10 rounded-full">🔄</div>
      <h3 className="text-lg font-bold text-[var(--color-ink)] mb-2">Network Balanced</h3>
      <p className="text-[var(--color-ink)]/60 max-w-md">No pending redistribution recommendations. AI confirms current inventory levels are optimal.</p>
    </div>
  );

  return (
    <div className="glass-surface overflow-hidden rounded-2xl premium-shadow">
      <div className="p-5 border-b border-[var(--color-line)] bg-white/40">
        <h3 className="font-bold text-[var(--color-ink)] flex items-center gap-2">
          <span className="text-[var(--color-primary)]">🔄</span> Redistribution Recommendations — Pending DHO Approval ({recs.length})
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--color-line)] bg-[var(--color-canvas)]/50">
              {["Medicine", "From PHC", "To PHC", "Qty", "Distance", "Rationale", "Actions"].map(h => (
                <th key={h} className="text-left px-5 py-4 font-bold text-xs uppercase tracking-wider text-[var(--color-ink)]/50">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-line)]">
            {recs.map((r) => (
              <tr key={r.id} className="hover:bg-[var(--color-primary)]/5 transition-colors">
                <td className="px-5 py-4 font-bold text-[var(--color-primary)]">{r.drug_name}</td>
                <td className="px-5 py-4"><div className="font-semibold text-[var(--color-ink)]">{r.from_phc}</div><div className="text-xs text-[var(--color-ink)]/60">{r.from_district}</div></td>
                <td className="px-5 py-4"><div className="font-semibold text-[var(--color-ink)]">{r.to_phc}</div><div className="text-xs text-[var(--color-ink)]/60">{r.to_district}</div></td>
                <td className="px-5 py-4 font-bold text-[var(--color-signal-ok)]">{r.qty}</td>
                <td className="px-5 py-4 text-xs font-semibold text-[var(--color-ink)]/70">{r.distance_km} km</td>
                <td className="px-5 py-4 text-xs max-w-xs text-[var(--color-ink)]/70">
                  <div className="line-clamp-2">{r.rationale}</div>
                </td>
                <td className="px-5 py-4">
                  <div className="flex gap-2">
                    <button onClick={() => approve(r.id)} disabled={acting === r.id}
                            className="text-xs px-4 py-2 rounded-lg font-bold transition-all bg-[var(--color-signal-ok)]/10 text-[var(--color-signal-ok)] hover:bg-[var(--color-signal-ok)]/20 border border-[var(--color-signal-ok)]/20 disabled:opacity-50 hover-lift">
                      ✓ Approve
                    </button>
                    <button onClick={() => reject(r.id)} disabled={acting === r.id}
                            className="text-xs px-4 py-2 rounded-lg font-bold transition-all bg-[var(--color-signal-critical)]/10 text-[var(--color-signal-critical)] hover:bg-[var(--color-signal-critical)]/20 border border-[var(--color-signal-critical)]/20 disabled:opacity-50 hover-lift">
                      ✗ Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
