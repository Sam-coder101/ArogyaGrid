'use client';
import { createContext, useContext, useEffect, useState } from 'react';
import { api, DashboardSummary, DemoStatus, Alert, Redistribution, EpiSignal } from '@/lib/api';
import { useDemoLoop, DemoEvent, AgentState } from '@/lib/useDemoLoop';

interface DashboardContextType {
  summary: DashboardSummary | null;
  demoStatus: DemoStatus | null;
  alerts: Alert[];
  redists: Redistribution[];
  epiSignals: EpiSignal[];
  refreshStats: () => Promise<void>;
  demo: {
    running: boolean;
    run: () => Promise<void>;
    events: DemoEvent[];
    agents: AgentState[];
  };
}

const DashboardContext = createContext<DashboardContextType | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [demoStatus, setDemoStatus] = useState<DemoStatus | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [redists, setRedists] = useState<Redistribution[]>([]);
  const [epiSignals, setEpiSignals] = useState<EpiSignal[]>([]);
  
  const demo = useDemoLoop();

  const refreshStats = async () => {
    try {
      const sum = await api.getSummary();
      const stat = await api.getStatus();
      const al = await api.listAlerts();
      const re = await api.listRedistributions();
      const ep = await api.getEpiSignals();

      setSummary(sum);
      setDemoStatus(stat);
      setAlerts(al);
      setRedists(re);
      setEpiSignals(ep);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshStats();
    const interval = setInterval(refreshStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardContext.Provider value={{ summary, demoStatus, alerts, redists, epiSignals, refreshStats, demo }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const context = useContext(DashboardContext);
  if (!context) throw new Error('useDashboard must be used within DashboardProvider');
  return context;
}
