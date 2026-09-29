import { PrescriptionMedicineCard } from '@/components/ui/PrescriptionMedicineCard';
import { Camera, Info, ChevronDown } from 'lucide-react';

export default function PatientPrescriptionExplainer() {
  return (
    <div className="min-h-screen bg-transparent py-6 px-4">
      {/* Mobile-first centered container constraint (max-w-md = 448px) */}
      <main className="max-w-md mx-auto w-full flex flex-col gap-6">
        
        {/* Header */}
        <header className="text-center pt-4 pb-2 border-b border-[var(--color-line)] glass-surface rounded-xl p-4">
          <div className="text-[var(--color-primary)] font-bold mb-1 tracking-wide uppercase text-sm">
            ArogyaGrid
          </div>
          <h1 className="patient-text-h1 text-[var(--color-ink)] mb-1">
            आपका प्रिस्क्रिप्शन समझें
          </h1>
          <p className="patient-text-body text-[var(--color-ink)]/70">
            Understand your prescription
          </p>
        </header>

        {/* Controls */}
        <div className="flex flex-col gap-3">
          <button className="w-full min-h-[56px] bg-[var(--color-primary)] text-[var(--color-surface)] rounded-[8px] patient-text-body font-semibold flex items-center justify-center gap-2 btn-primary-anim shadow-sm">
            <Camera size={24} /> Scan prescription
          </button>

          <div className="relative">
            <select className="w-full min-h-[56px] appearance-none glass-surface border border-[var(--color-line)] rounded-[8px] patient-text-body font-medium text-[var(--color-ink)] px-4 hover:border-[var(--color-primary)] transition-colors shadow-sm text-center cursor-pointer">
              <option>Choose language: हिंदी (Hindi)</option>
              <option>Choose language: English</option>
              <option>Choose language: मराठी (Marathi)</option>
              <option>Choose language: বাংলা (Bengali)</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-4 flex items-center px-2 text-[var(--color-ink)]">
              <ChevronDown size={20} />
            </div>
          </div>
        </div>

        {/* Results List */}
        <div className="mt-2">
          <PrescriptionMedicineCard 
            name="Paracetamol 500mg"
            purpose="बुखार और दर्द के लिए (For fever and pain relief)"
            sideEffects={[
              "हल्का पेट दर्द (Mild stomach pain)",
              "मतली महसूस होना (Feeling nauseous)"
            ]}
            alternatives={[
              "यदि आपको लिवर की समस्या है, तो डॉक्टर से पूछें (Ask doctor if you have liver issues)"
            ]}
          />
          
          <PrescriptionMedicineCard 
            name="Cetirizine 10mg"
            purpose="एलर्जी और सर्दी के लक्षणों के लिए (For allergy and cold symptoms)"
            sideEffects={[
              "नींद आना (Drowsiness)",
              "मुंह सूखना (Dry mouth)"
            ]}
            alternatives={[
              "गैर-नींद वाली एलर्जी की दवाएं (Non-drowsy allergy medicines)"
            ]}
          />
        </div>

        {/* Always-visible Disclaimer */}
        <div className="mt-4 p-4 bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/20 rounded-[8px] flex gap-3 items-start premium-shadow">
          <Info className="w-6 h-6 flex-shrink-0 text-[var(--color-accent)] mt-0.5" />
          <p className="patient-text-body text-[var(--color-ink)] font-medium leading-snug">
            यह जानकारी केवल मदद के लिए है। यह डॉक्टर की सलाह का विकल्प नहीं है।<br/>
            <span className="text-sm font-normal opacity-80">(This is not a substitute for professional medical advice.)</span>
          </p>
        </div>
      </main>
    </div>
  );
}
