'use client';
import type { EpiSignal } from "@/lib/api";

const trendColors: Record<string, string> = {
  RISING:  "text-[var(--color-signal-critical)]",
  STABLE:  "text-amber-500",
  FALLING: "text-[var(--color-signal-ok)]",
  UNKNOWN: "text-[var(--color-ink)]/50",
};
const trendIcons: Record<string, string> = { RISING: "↗", STABLE: "→", FALLING: "↘", UNKNOWN: "?" };
const diseaseIcons: Record<string, string> = {
  dengue: "🦟", malaria: "🦟", diarrhoeal: "💧", respiratory: "🌡️",
};

function getIcon(hypothesis: string) {
  for (const [k, v] of Object.entries(diseaseIcons)) {
    if (hypothesis.toLowerCase().includes(k)) return v;
  }
  return "🦠";
}

export default function EpiSignalCard({ signal }: { signal: EpiSignal }) {
  return (
    <div className="glass-surface p-6 rounded-2xl premium-shadow hover-lift animate-in">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl p-2 bg-[var(--color-primary)]/5 rounded-xl border border-[var(--color-primary)]/10">
            {getIcon(signal.disease_hypothesis)}
          </span>
          <div>
            <div className="font-bold text-base capitalize text-[var(--color-ink)]">{signal.disease_hypothesis}</div>
            <div className="text-xs mt-1 font-semibold text-[var(--color-ink)]/60">
              {signal.geo_block} · {signal.district}, {signal.state}
            </div>
          </div>
        </div>
        <div className="text-right flex-shrink-0 bg-[var(--color-canvas)] px-3 py-2 rounded-xl border border-[var(--color-line)] shadow-sm">
          <div className={`font-bold text-sm ${trendColors[signal.trend]}`}>
            {trendIcons[signal.trend]} {signal.trend}
          </div>
          <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--color-ink)]/50 mt-1">
            {Math.round(signal.confidence * 100)}% conf
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs font-semibold text-[var(--color-ink)]/70">
        <span className="flex items-center gap-1.5 bg-[var(--color-surface)] px-2.5 py-1.5 rounded-lg border border-[var(--color-line)] shadow-sm">
          📋 {signal.contributing_case_count} cases detected
        </span>
        {signal.alert_threshold_crossed && (
          <span className="px-2.5 py-1.5 bg-[var(--color-signal-critical)]/10 text-[var(--color-signal-critical)] rounded-lg border border-[var(--color-signal-critical)]/20 animate-pulse">
            🚨 Outbreak Threshold
          </span>
        )}
      </div>

      {/* Confidence bar */}
      <div className="mt-4 h-2 rounded-full overflow-hidden bg-[var(--color-line)]">
        <div className="h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(13,148,136,0.5)]"
             style={{ width: `${signal.confidence * 100}%`, background: `linear-gradient(90deg, var(--color-accent), var(--color-primary))` }} />
      </div>
    </div>
  );
}
