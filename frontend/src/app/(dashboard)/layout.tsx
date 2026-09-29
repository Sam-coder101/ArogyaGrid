'use client';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import StatCard from '@/components/StatCard';
import { DashboardProvider, useDashboard } from '@/components/DashboardProvider';

function DashboardShell({ children }: { children: React.ReactNode }) {
  const { summary, demoStatus, refreshStats } = useDashboard();
  const pathname = usePathname();

  const handleReseed = async () => {
    if (confirm("Reset database to initial state?")) {
      const { api } = await import('@/lib/api');
      await api.seedDatabase();
      refreshStats();
    }
  };

  const tabs = [
    { id: '/', label: 'Demo Loop' },
    { id: '/alerts', label: 'Alerts' },
    { id: '/redist', label: 'Redistribution' },
    { id: '/rx', label: 'Prescription' },
    { id: '/epi', label: 'Epi Signals' }
  ];

  return (
    <div className="min-h-screen text-[var(--color-ink)] flex flex-col selection:bg-[var(--color-primary)] selection:text-white gradient-bg">
      {/* ── HEADER ── */}
      <header className="px-8 py-5 flex justify-between items-center sticky top-0 z-20 glass-surface">
        <div>
          <h1 className="text-2xl font-bold tracking-tight m-0 bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
            ArogyaGrid
          </h1>
          <p className="text-sm text-[var(--color-ink)]/60 m-0 mt-1 font-medium">Federated AI | PHC Supply Chain Intelligence</p>
        </div>
        <div className="flex gap-4 items-center">
          {demoStatus && (
            <div className="flex gap-4 text-xs font-semibold bg-[var(--color-primary)]/10 px-4 py-2 rounded-full border border-[var(--color-primary)]/20 text-[var(--color-primary-deep)]">
              <span className="flex items-center gap-1.5"><span className="text-[var(--color-accent)] animate-pulse">●</span> {demoStatus.database.phcs} PHCs</span>
              <span className="flex items-center gap-1.5"><span className="text-[var(--color-accent)] animate-pulse">●</span> {demoStatus.database.medicines} Medicines</span>
            </div>
          )}
          <button 
            onClick={handleReseed}
            className="text-xs font-semibold px-4 py-2 bg-[var(--color-surface)] border border-[var(--color-line)] rounded-full hover-lift transition-all flex items-center gap-1 text-[var(--color-ink)] hover:text-[var(--color-primary)] shadow-sm"
          >
            Re-seed DB
          </button>
          <a href="/docs" target="_blank" className="text-xs font-semibold text-[var(--color-ink)]/70 hover:text-[var(--color-accent)] transition-colors flex items-center gap-1">
            API Docs
          </a>
        </div>
      </header>

      {/* ── MAIN CONTAINER ── */}
      <main className="flex-1 w-full max-w-[1600px] mx-auto px-8 py-8 flex flex-col gap-8">
        
        {/* ── KPI STRIP ── */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatCard index={0} label="PHCs" value={summary?.total_phcs || 0} accent="var(--color-primary)" />
          <StatCard index={1} label="Open Alerts" value={summary?.open_alerts || 0} accent="var(--color-signal-critical)" />
          <StatCard index={2} label="HIGH Severity" value={summary?.high_severity_alerts || 0} accent="var(--color-signal-critical)" />
          <StatCard index={3} label="Pending Redistrib." value={summary?.pending_redistributions || 0} accent="var(--color-accent)" />
          <StatCard index={4} label="Disease Signals" value={summary?.disease_signals || 0} accent="var(--color-accent)" />
          <StatCard index={5} label="Posters Generated" value={summary?.posters_generated || 0} accent="var(--color-primary)" />
        </div>

        {/* ── TABS ── */}
        <div className="border-b border-[var(--color-line)] flex gap-8">
          {tabs.map(t => (
            <Link
              key={t.id}
              href={t.id}
              className={`pb-3 text-sm font-semibold relative transition-colors ${pathname === t.id ? 'text-[var(--color-primary)]' : 'text-[var(--color-ink)]/60 hover:text-[var(--color-ink)]'}`}
            >
              {t.label}
              {pathname === t.id && (
                <motion.div
                  layoutId="activeTabIndicator"
                  className="absolute bottom-[-1px] left-0 right-0 h-[2px] bg-[var(--color-primary)]"
                />
              )}
            </Link>
          ))}
        </div>

        {/* ── MAIN CONTENT ── */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </main>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DashboardProvider>
      <DashboardShell>{children}</DashboardShell>
    </DashboardProvider>
  );
}
