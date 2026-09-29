'use client';
import { useDashboard } from '@/components/DashboardProvider';
import RedistributionTable from '@/components/RedistributionTable';

export default function RedistTab() {
  const { redists, refreshStats } = useDashboard();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 tracking-tight">Redistribution Recommendations</h2>
      <RedistributionTable recs={redists} onRefresh={refreshStats} />
    </div>
  );
}
