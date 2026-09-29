'use client';
import { useDashboard } from '@/components/DashboardProvider';
import AlertsTable from '@/components/AlertsTable';

export default function AlertsTab() {
  const { alerts, refreshStats } = useDashboard();

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 tracking-tight">Active Alerts</h2>
      <AlertsTable alerts={alerts} onRefresh={refreshStats} />
    </div>
  );
}
