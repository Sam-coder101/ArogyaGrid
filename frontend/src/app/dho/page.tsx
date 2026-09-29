'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { api, Alert, Redistribution } from '@/lib/api';

export default function DHODashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [redists, setRedists] = useState<Redistribution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [fetchedAlerts, fetchedRedists] = await Promise.all([
          api.listAlerts({ state: 'West Bengal' }),
          api.listRedistributions()
        ]);
        setAlerts(fetchedAlerts);
        setRedists(fetchedRedists);
      } catch (err) {
        console.error("Failed to load DHO data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const getRedistForAlert = (alert: Alert) => {
    return redists.find(r => r.drug_name === alert.drug_name && r.to_phc === alert.phc_name && r.status === 'PENDING');
  };

  const handleApprove = async (id: number) => {
    await api.approveRedist(id);
    setRedists(prev => prev.map(r => r.id === id ? { ...r, status: 'APPROVED' } : r));
  };

  return (
    <div className="flex h-screen w-full bg-transparent overflow-hidden">
      {/* Sidebar Nav */}
      <aside className="w-64 flex-shrink-0 glass-surface border-r border-[var(--color-line)] flex flex-col z-10 relative">
        <div className="p-4 border-b border-[var(--color-line)] flex items-center justify-between">
          <h1 className="text-h1 text-[var(--color-primary)] font-['Fraunces']">ArogyaGrid</h1>
        </div>
        
        <div className="px-4 py-3 border-b border-[var(--color-line)]">
          <div className="text-caption mb-1">District</div>
          <select className="w-full text-body bg-[var(--color-canvas)] border border-[var(--color-line)] rounded-sm px-2 py-1 outline-none">
            <option>Purulia</option>
          </select>
          <div className="text-caption mt-3 mb-1">Role</div>
          <select className="w-full text-body bg-[var(--color-canvas)] border border-[var(--color-line)] rounded-sm px-2 py-1 outline-none">
            <option>DHO</option>
          </select>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-2">
            <li><a href="#" className="flex px-3 py-2 text-body text-[var(--color-ink)] hover:bg-[var(--color-canvas)] rounded-sm">Overview</a></li>
            <li><a href="#" className="flex px-3 py-2 text-body font-bold text-[var(--color-primary-deep)] bg-[var(--color-primary)]/10 rounded-sm items-center justify-between">Alerts<span className="w-2 h-2 rounded-full bg-[var(--color-accent)]"></span></a></li>
            <li><a href="#" className="flex px-3 py-2 text-body text-[var(--color-ink)] hover:bg-[var(--color-canvas)] rounded-sm">Forecast</a></li>
            <li><a href="#" className="flex px-3 py-2 text-body text-[var(--color-ink)] hover:bg-[var(--color-canvas)] rounded-sm">Transfers</a></li>
            <li><a href="#" className="flex px-3 py-2 text-body text-[var(--color-ink)] hover:bg-[var(--color-canvas)] rounded-sm">Posters</a></li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <header className="mb-8">
          <h2 className="text-display mb-2">Active Alerts ({alerts.length})</h2>
          <p className="text-body text-[var(--color-ink)]/70 max-w-2xl">
            Review critical stock-out predictions and approve AI-suggested cross-district transfers.
          </p>
        </header>

        {loading ? (
          <div className="text-body">Loading alerts from agents...</div>
        ) : (
          <div className="space-y-4 max-w-4xl">
            {alerts.length === 0 ? (
              <div className="text-body text-[var(--color-ink)]/70">No active alerts. Run the demo loop to generate some!</div>
            ) : (
              alerts.map(alert => {
                const redist = getRedistForAlert(alert);
                const isCritical = alert.severity === 'HIGH';
                
                return (
                  <Card key={alert.id} className={`p-4 flex flex-col gap-4 shadow-[0_1px_3px_rgba(0,0,0,0.1)] ${isCritical ? 'border-[var(--color-signal-critical)]' : ''}`}>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <Badge variant={isCritical ? 'critical' : 'accent'} icon={<span className="mr-1">{isCritical ? '⬤' : '▲'}</span>}>
                          {alert.severity}
                        </Badge>
                        <h3 className="text-h2">{alert.drug_name} — {alert.phc_name}</h3>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-body">
                      <div>
                        <span className="font-semibold">Predicted status:</span> <span className={`${isCritical ? 'text-[var(--color-signal-critical)] font-bold' : ''}`}>
                          {alert.alert_type === 'STOCK_OUT' ? 'Stock-out predicted' : 'Critical shortage'} on {new Date(alert.predicted_date).toLocaleDateString()}
                        </span>
                      </div>
                      
                      {redist && (
                        <div className="flex flex-col gap-1">
                          <div><span className="font-semibold">Suggested source:</span> {redist.from_phc}</div>
                          <div className="text-caption text-[var(--color-ink)]/70">
                            ({redist.distance_km.toFixed(1)}km, surplus: {redist.qty} units)
                          </div>
                        </div>
                      )}
                    </div>

                    {redist && (
                      <div className="flex justify-end pt-2 border-t border-[var(--color-line)]">
                        <Button 
                          variant="accent" 
                          onClick={() => handleApprove(redist.id)}
                          disabled={redist.status === 'APPROVED'}
                          className={redist.status === 'APPROVED' ? 'opacity-50 cursor-not-allowed' : ''}
                        >
                          {redist.status === 'APPROVED' ? '✓ Transfer Approved' : 'Approve transfer'}
                        </Button>
                      </div>
                    )}
                  </Card>
                );
              })
            )}
          </div>
        )}
      </main>
    </div>
  );
}
