'use client';
import PrescriptionUploader from '@/components/PrescriptionUploader';

export default function PrescriptionTab() {
  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4 tracking-tight">Prescription Explainer</h2>
      <p className="text-sm text-[var(--color-ink)]/70 mb-6">Upload a prescription to run the OCR and Translation agents.</p>
      <PrescriptionUploader />
    </div>
  );
}
