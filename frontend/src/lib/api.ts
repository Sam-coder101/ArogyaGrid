// ArogyaGrid API client
// All calls go through Next.js rewrites -> FastAPI at localhost:8000

const BASE = "http://localhost:8000/api";

export async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text.slice(0, 200)}`);
  }
  return res.json();
}

export const api = {
  // ── Demo ──────────────────────────────────────────────────────────────────
  seedDatabase: () => fetchJSON<{ status: string; message: string }>("/demo/seed", { method: "POST" }),
  getStatus:    () => fetchJSON<DemoStatus>("/demo/status"),

  // ── Dashboard ─────────────────────────────────────────────────────────────
  getSummary:    (state?: string) => fetchJSON<DashboardSummary>(`/dashboard/summary${state ? `?state=${state}` : ""}`),
  getMapData:    (state?: string) => fetchJSON<PHCMapPoint[]>(`/dashboard/map-data${state ? `?state=${state}` : ""}`),
  getEpiSignals: () => fetchJSON<EpiSignal[]>("/dashboard/epi-signals"),
  getPosters:    () => fetchJSON<Poster[]>("/dashboard/posters"),

  // ── Stock ─────────────────────────────────────────────────────────────────
  listPHCs:     (state?: string) => fetchJSON<PHC[]>(`/stock/phcs${state ? `?state=${state}` : ""}`),
  getPHCStock:  (id: string)     => fetchJSON<PHCStock>(`/stock/${id}`),

  // ── Alerts ────────────────────────────────────────────────────────────────
  listAlerts:   (params?: { state?: string; severity?: string }) =>
    fetchJSON<Alert[]>(`/alerts/?${new URLSearchParams(params as Record<string, string> ?? {})}`),
  ackAlert:     (id: number)     => fetchJSON<{ status: string }>(`/alerts/${id}/ack`, { method: "POST" }),

  // ── Forecast ─────────────────────────────────────────────────────────────
  getForecastResults: () => fetchJSON<ForecastResult[]>("/forecast/results?limit=20"),

  // ── Redistribution ────────────────────────────────────────────────────────
  listRedistributions: () => fetchJSON<Redistribution[]>("/redistribution/"),
  approveRedist:       (id: number) => fetchJSON<{ status: string }>(`/redistribution/${id}/approve`, { method: "POST" }),
  rejectRedist:        (id: number) => fetchJSON<{ status: string }>(`/redistribution/${id}/reject`, { method: "POST" }),

  // ── Prescription ──────────────────────────────────────────────────────────
  explainPrescription: (file: File, language: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("language", language);
    return fetchJSON<PrescriptionExplanation>("/prescription/explain", { method: "POST", body: form });
  },
};

// ── Types ─────────────────────────────────────────────────────────────────────
export interface DemoStatus {
  database: { phcs: number; medicines: number; inventory_items: number; alerts: number; dispensation_records: number };
  providers: Record<string, string>;
  gemini_model: string;
}
export interface DashboardSummary {
  total_phcs: number; open_alerts: number; high_severity_alerts: number;
  medium_severity_alerts: number; pending_redistributions: number;
  disease_signals: number; forecasts_generated: number; posters_generated: number;
}
export interface PHCMapPoint { id: string; name: string; district: string; state: string; latitude: number; longitude: number; category: string; status: "ok" | "warning" | "critical"; open_alerts: number; }
export interface PHC { id: string; name: string; district: string; state: string; category: string; latitude: number; longitude: number; }
export interface PHCStock { phc_id: string; phc_name: string; district: string; state: string; inventory: InventoryItem[]; }
export interface InventoryItem { drug_id: string; drug_name: string; therapeutic_class: string; quantity: number; unit: string; essential: boolean; }
export interface Alert { id: number; alert_type: string; phc_id: string; phc_name: string; district: string; state: string; drug_id: string; drug_name: string; severity: "HIGH" | "MEDIUM" | "LOW"; predicted_date: string; confidence: number; status: string; recommended_action: string; created_at: string; }
export interface ForecastResult { id: number; phc_id: string; phc_name: string; drug_id: string; drug_name: string; horizon_days: number; predicted_qty: number; confidence: number; explanation: string; created_at: string; }
export interface Redistribution { id: number; from_phc: string; from_district: string; to_phc: string; to_district: string; drug_name: string; qty: number; distance_km: number; rationale: string; status: string; created_at: string; }
export interface EpiSignal { id: number; geo_block: string; state: string; district: string; disease_hypothesis: string; confidence: number; trend: string; contributing_case_count: number; alert_threshold_crossed: boolean; created_at: string; }
export interface Poster { id: number; disease_signal_id: number; language: string; geo_target: string; caption_text: string; image_url: string; created_at: string; }
export interface DrugExplanation { name: string; dosage: string; frequency: string; db_match: string; molecule: string; therapeutic_class: string; manufacturer: string; side_effects: string[]; alternatives: string[]; explanation: string; confidence: number; }
export interface PrescriptionExplanation { ocr_confidence: number; doctor_name: string; prescription_date: string; drugs: DrugExplanation[]; disclaimer: string; language: string; agent: string; }
