'use client';
import type { DemoEvent } from "@/lib/useDemoLoop";

interface Props { events: DemoEvent[]; }

const eventStyles: Record<string, { color: string; prefix: string }> = {
  demo_start:              { color: "text-blue-600",   prefix: "SYS" },
  phase:                   { color: "text-purple-600", prefix: "PHS" },
  workflow_start:          { color: "text-blue-600",   prefix: "RUN" },
  forecast:                { color: "text-cyan-600",   prefix: "FCT" },
  alert:                   { color: "text-red-600",    prefix: "WRN" },
  no_alert:                { color: "text-emerald-600",  prefix: "OK " },
  redistribution:          { color: "text-amber-600",  prefix: "OPT" },
  prescription_explanation:{ color: "text-cyan-600",   prefix: "OCR" },
  epi_signals:             { color: "text-purple-600", prefix: "EPI" },
  poster:                  { color: "text-emerald-600",  prefix: "GEN" },
  workflow_complete:       { color: "text-emerald-600",  prefix: "DON" },
  demo_complete:           { color: "text-emerald-600",  prefix: "END" },
  error:                   { color: "text-red-600",    prefix: "ERR" },
};

function summarise(evt: DemoEvent): string {
  const d = evt.data as Record<string, unknown> | undefined;
  if (!d) return evt.message ?? "";
  if (evt.event === "forecast")   return `Forecast: ${d.drug_name} at ${d.phc_name} — ${d.predicted_qty} units predicted`;
  if (evt.event === "alert")      return `ALERT (${d.severity}): ${d.drug_name} at ${d.phc_name} — ${d.days_remaining} days left`;
  if (evt.event === "redistribution") {
    const arr = d as unknown as Record<string, unknown>[];
    if (Array.isArray(arr) && arr.length > 0) return `Redist: ${arr[0].from_phc_name} → ${arr[0].to_phc_name}: ${arr[0].qty} units of ${arr[0].drug_name}`;
  }
  if (evt.event === "prescription_explanation") return `Prescription: ${(d.drugs as unknown[])?.length ?? 0} drugs explained (${d.language})`;
  if (evt.event === "epi_signals") {
    const arr = d as unknown as Record<string, unknown>[];
    if (Array.isArray(arr) && arr.length > 0) return `Signal: ${arr[0].disease_hypothesis} — ${arr[0].geo_block}`;
    return "Epi: No signals above threshold";
  }
  if (evt.event === "poster") return `Poster generated: ${d.disease_hypothesis} / ${d.geo_target}`;
  if (evt.event === "phase")  return `Phase ${(evt as unknown as Record<string, unknown>).phase}: ${(evt as unknown as Record<string, unknown>).name}`;
  return evt.message ?? evt.event;
}

import { motion, AnimatePresence } from 'framer-motion';

export default function EventLog({ events }: Props) {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-xs text-[var(--color-ink)]/70">
      {events.length === 0 ? (
        <div className="text-[var(--color-ink)]/40 italic">Waiting for demo to start...</div>
      ) : (
        <AnimatePresence>
          {events.map((evt, i) => {
            const style = eventStyles[evt.event] ?? { color: "text-[var(--color-ink)]/60", prefix: "LOG" };
            return (
              <motion.div 
                key={i} 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-start gap-3 py-1 border-b border-[var(--color-line)]/30 last:border-0"
              >
                <span className={`flex-shrink-0 font-bold ${style.color}`}>[{style.prefix}]</span>
                <span className="truncate flex-1 font-medium">{summarise(evt)}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      )}
    </div>
  );
}
