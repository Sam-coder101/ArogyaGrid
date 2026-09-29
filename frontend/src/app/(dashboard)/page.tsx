'use client';
import AgentPipeline from '@/components/AgentPipeline';
import EventLog from '@/components/EventLog';
import { useDashboard } from '@/components/DashboardProvider';

export default function DemoTab() {
  const { demoStatus, demo: { running, run, events, agents } } = useDashboard();

  return (
    <div className="grid grid-cols-12 gap-6 h-full">
      {/* Left Column: Pipeline & Trigger */}
      <div className="col-span-4 flex flex-col gap-6">
        <section className="glass-surface p-6 rounded-2xl premium-shadow">
          <h2 className="text-lg font-bold mb-2">Full Demo Loop</h2>
          <p className="text-sm text-[var(--color-ink)]/70 mb-4">
            Triggers all agents end-to-end: Forecast, Warning, Redistribution, Prescription OCR, Epi Signal, Awareness Poster.
          </p>
          <button 
            onClick={run}
            disabled={running}
            className={`w-full py-3 rounded-xl font-bold text-sm ${running ? 'bg-[var(--color-line)] text-[var(--color-ink)]/50 cursor-not-allowed' : 'btn-primary-anim'}`}
          >
            {running ? 'Demo Running...' : '▶ Run Full Demo Loop'}
          </button>
        </section>
        
        <section className="flex-1 glass-surface rounded-2xl p-4 premium-shadow">
          <AgentPipeline agents={agents} />
        </section>
      </div>

      {/* Right Column: Logs & Config */}
      <div className="col-span-8 flex flex-col gap-6 h-[calc(100vh-280px)]">
        <section className="flex-1 flex flex-col glass-surface text-[var(--color-ink)] rounded-2xl overflow-hidden premium-shadow">
          <div className="px-4 py-3 bg-[var(--color-canvas)]/50 border-b border-[var(--color-line)] flex justify-between items-center backdrop-blur-md">
            <h3 className="text-xs font-bold tracking-wider uppercase text-[var(--color-primary)]">Agent Event Log</h3>
            {running && <span className="text-[var(--color-accent)] text-xs font-bold animate-pulse">● LIVE</span>}
          </div>
          <EventLog events={events} />
        </section>

        <section className="glass-surface p-6 rounded-2xl premium-shadow">
          <h3 className="text-xs font-bold tracking-wider text-[var(--color-primary)] mb-3 uppercase">Provider Status</h3>
          {demoStatus ? (
            <div className="grid grid-cols-3 gap-y-2 text-sm font-mono">
              {Object.entries(demoStatus.providers).map(([k, v]) => (
                <div key={k}>
                  <span className="text-[var(--color-ink)]/60">{k}:</span> 
                  <span className={`ml-1 font-semibold ${v === 'REAL' ? 'text-[var(--color-signal-ok)]' : 'text-[var(--color-accent)]'}`}>{v}</span>
                </div>
              ))}
            </div>
          ) : <div className="text-sm text-[var(--color-ink)]/50">Loading...</div>}
          
          <div className="mt-4 pt-3 border-t border-[var(--color-line)]">
            <p className="text-xs text-[var(--color-ink)]/70 leading-relaxed">
              <strong>Architecture Note — Provider Stubs</strong><br/>
              Vertex AI Forecasting, Document AI, Imagen 3, and Cloud Translation are each stubbed behind a Provider interface. 
              <strong>Gemini calls are real</strong> when GOOGLE_API_KEY is set. 
              Set USE_REAL_FORECAST=true, USE_REAL_IMAGEN=true, etc. to activate real GCP APIs with no other code changes.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
