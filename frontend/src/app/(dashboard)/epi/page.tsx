'use client';
import { useDashboard } from '@/components/DashboardProvider';
import EpiSignalCard from '@/components/EpiSignalCard';

export default function EpiTab() {
  const { epiSignals } = useDashboard();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 tracking-tight">Epidemiological Signals</h2>
      <div className="grid grid-cols-2 gap-4">
        {epiSignals.length > 0 ? epiSignals.map(sig => (
          <EpiSignalCard key={sig.id} signal={sig} />
        )) : (
          <div className="col-span-2 text-sm text-[var(--color-ink)]/70">No active signals found.</div>
        )}
      </div>
    </div>
  );
}
