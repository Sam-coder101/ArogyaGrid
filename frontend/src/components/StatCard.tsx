'use client';
import { motion } from 'framer-motion';

interface Props { label: string; value: number | string; accent?: string; sublabel?: string; index?: number; }

export default function StatCard({ label, value, accent = "var(--color-primary)", sublabel, index = 0 }: Props) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1, ease: "easeOut" }}
      className="glass-surface rounded-2xl p-5 flex flex-col justify-between hover-lift premium-shadow"
    >
      <div>
        <div className="text-3xl font-bold tracking-tight" style={{ color: accent }}>{value}</div>
        <div className="text-xs font-bold uppercase tracking-wider text-[var(--color-ink)]/70 mt-2">{label}</div>
      </div>
      {sublabel && <div className="text-xs mt-3 text-[var(--color-ink)]/50">{sublabel}</div>}
    </motion.div>
  );
}
