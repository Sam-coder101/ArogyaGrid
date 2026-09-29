'use client';
import { useState, useRef } from "react";
import type { PrescriptionExplanation } from "@/lib/api";
import { api } from "@/lib/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिंदी (Hindi)" },
  { code: "mr", label: "मराठी (Marathi)" },
  { code: "bn", label: "বাংলা (Bengali)" },
  { code: "ta", label: "தமிழ் (Tamil)" },
  { code: "te", label: "తెలుగు (Telugu)" },
];

export default function PrescriptionUploader() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [lang, setLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PrescriptionExplanation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = ev => setPreview(ev.target?.result as string);
    reader.readAsDataURL(f);
  }

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.explainPrescription(file, lang);
      setResult(res);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="glass-surface p-8 rounded-3xl premium-shadow">
      <h2 className="font-bold text-lg mb-2 text-[var(--color-primary)]">
        💊 Prescription Explainer Agent
      </h2>
      <p className="text-sm mb-6 text-[var(--color-ink)]/70">
        Upload a prescription photo. The agent uses Gemini multimodal OCR to read drug names,
        looks them up in a vetted medicine database, then explains each drug in plain language.
      </p>

      <div className="flex flex-col sm:flex-row gap-6 mb-6">
        {/* File drop zone */}
        <div
          onClick={() => inputRef.current?.click()}
          className={`flex-1 border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${preview ? 'border-transparent' : 'border-[var(--color-primary)]/30 hover:border-[var(--color-primary)] bg-[var(--color-surface)] hover:bg-[var(--color-primary)]/5'}`}
        >
          {preview ? (
            <img src={preview} alt="prescription preview" className="max-h-56 mx-auto rounded-xl object-contain shadow-sm" />
          ) : (
            <div className="py-8">
              <div className="text-4xl mb-3">📷</div>
              <div className="text-sm font-bold text-[var(--color-ink)]">
                Click to upload prescription image
              </div>
              <div className="text-xs mt-1 text-[var(--color-ink)]/50 font-medium">JPG, PNG, WebP</div>
            </div>
          )}
          <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
        </div>

        {/* Controls */}
        <div className="flex flex-col gap-4 min-w-[200px]">
          <div>
            <label className="text-xs font-bold uppercase tracking-wider text-[var(--color-ink)]/50 block mb-2">
              Explanation Language
            </label>
            <select value={lang} onChange={e => setLang(e.target.value)}
                    className="w-full rounded-xl px-4 py-3 text-sm font-bold bg-[var(--color-surface)] text-[var(--color-ink)] border border-[var(--color-line)] focus:border-[var(--color-primary)] outline-none shadow-sm transition-colors">
              {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>

          <button onClick={submit} disabled={!file || loading}
                  className="btn-primary-anim w-full justify-center mt-auto rounded-xl py-3 font-bold text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
            {loading ? (
              <><span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analysing...</>
            ) : "Explain Prescription"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl p-4 text-sm mb-4 bg-[var(--color-signal-critical)]/10 text-[var(--color-signal-critical)] border border-[var(--color-signal-critical)]/20 font-medium">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4 animate-in">
          <div className="flex flex-wrap gap-4 text-xs font-semibold text-[var(--color-ink)]/60 bg-[var(--color-surface)] p-3 rounded-lg border border-[var(--color-line)] inline-flex shadow-sm">
            <span>👨‍⚕️ {result.doctor_name || "Dr. (not detected)"}</span>
            <span>📅 {result.prescription_date || "Date not detected"}</span>
            <span className="text-[var(--color-primary)]">🎯 OCR Confidence: {Math.round(result.ocr_confidence * 100)}%</span>
          </div>

          {result.drugs.map((drug, i) => (
            <div key={i} className="rounded-2xl p-6 bg-[var(--color-surface)] border border-[var(--color-line)] shadow-sm hover-lift transition-all">
              <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                <div>
                  <h3 className="font-bold text-lg text-[var(--color-primary)]">{drug.db_match || drug.name}</h3>
                  <div className="text-xs mt-1 text-[var(--color-ink)]/50 font-semibold uppercase tracking-wide">
                    {drug.molecule} &bull; {drug.therapeutic_class} &bull; {drug.manufacturer}
                  </div>
                </div>
                <div className="text-right bg-[var(--color-canvas)] px-3 py-2 rounded-lg border border-[var(--color-line)]">
                  <div className="text-sm font-bold text-[var(--color-ink)]">{drug.dosage}</div>
                  <div className="text-xs font-semibold text-[var(--color-ink)]/60">{drug.frequency}</div>
                </div>
              </div>

              <div className="text-sm leading-relaxed mb-5 text-[var(--color-ink)]/80 font-medium">
                {drug.explanation}
              </div>

              {drug.side_effects.length > 0 && (
                <div className="mb-4">
                  <div className="text-xs font-bold uppercase tracking-wider mb-2 text-amber-500">
                    ⚡ Side effects to watch for:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {drug.side_effects.map((s, j) => (
                      <span key={j} className="px-2.5 py-1 bg-amber-500/10 text-amber-600 rounded-md text-[11px] font-bold border border-amber-500/20">{s}</span>
                    ))}
                  </div>
                </div>
              )}

              {drug.alternatives.length > 0 && (
                <div className="text-xs bg-[var(--color-primary)]/5 p-3 rounded-lg text-[var(--color-ink)]/70 font-medium border border-[var(--color-primary)]/10">
                  <span className="font-bold text-[var(--color-primary)]">Ask your doctor about alternatives:</span> {drug.alternatives.join(", ")}
                </div>
              )}
            </div>
          ))}

          <div className="rounded-xl p-5 text-xs bg-amber-500/10 border border-amber-500/20 text-amber-700 font-medium leading-relaxed">
            <span className="font-bold uppercase tracking-wider block mb-1">Disclaimer</span>
            {result.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}
