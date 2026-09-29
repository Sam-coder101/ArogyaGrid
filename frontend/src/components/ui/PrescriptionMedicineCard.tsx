'use client';
import { useState } from 'react';

type MedicineCardProps = {
  name: string;
  purpose: string;
  sideEffects: string[];
  alternatives: string[];
};

export function PrescriptionMedicineCard({ name, purpose, sideEffects, alternatives }: MedicineCardProps) {
  const [expandedSection, setExpandedSection] = useState<'none' | 'sideEffects' | 'alternatives'>('none');

  const toggleSection = (section: 'sideEffects' | 'alternatives') => {
    setExpandedSection(prev => prev === section ? 'none' : section);
  };

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-line)] rounded-[6px] overflow-hidden mb-4 shadow-sm">
      <div className="p-4 flex items-start justify-between">
        <div className="flex gap-3">
          <div>
            <h3 className="patient-text-h2 text-[var(--color-ink)] font-bold mb-1">{name}</h3>
            <p className="patient-text-body text-[var(--color-ink)]/80 leading-snug max-w-[60ch]">{purpose}</p>
          </div>
        </div>
        {/* 44x44 touch target for accessibility */}
        <button 
          className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-full bg-[var(--color-canvas)] text-[var(--color-primary)] hover:bg-[var(--color-line)] transition-colors flex-shrink-0"
          aria-label="Listen to explanation"
        >
          {/* Replace emoji with text icon for now */}
          Vol
        </button>
      </div>

      <div className="border-t border-[var(--color-line)]">
        <button 
          onClick={() => toggleSection('sideEffects')}
          className="w-full text-left px-4 py-3 min-h-[44px] patient-text-body font-medium flex justify-between items-center hover:bg-[var(--color-canvas)] transition-colors text-[var(--color-ink)]"
          aria-expanded={expandedSection === 'sideEffects'}
        >
          <span>साइड इफ़ेक्ट देखें (View Side Effects)</span>
          <span className={`transform transition-transform ${expandedSection === 'sideEffects' ? 'rotate-180' : ''}`}>▾</span>
        </button>
        
        {expandedSection === 'sideEffects' && (
          <div className="px-4 pb-4 pt-1 patient-text-body text-[var(--color-ink)]/80 bg-[var(--color-canvas)]">
            <ul className="list-disc pl-5 space-y-1">
              {sideEffects.map((effect, idx) => (
                <li key={idx} className="max-w-[70ch]">{effect}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="border-t border-[var(--color-line)]">
        <button 
          onClick={() => toggleSection('alternatives')}
          className="w-full text-left px-4 py-3 min-h-[44px] patient-text-body font-medium flex justify-between items-center hover:bg-[var(--color-canvas)] transition-colors text-[var(--color-ink)]"
          aria-expanded={expandedSection === 'alternatives'}
        >
          <span>विकल्प के बारे में पूछें (Ask about alternatives)</span>
          <span className={`transform transition-transform ${expandedSection === 'alternatives' ? 'rotate-180' : ''}`}>▾</span>
        </button>
        
        {expandedSection === 'alternatives' && (
          <div className="px-4 pb-4 pt-1 patient-text-body text-[var(--color-ink)]/80 bg-[var(--color-canvas)]">
            <ul className="list-disc pl-5 space-y-1">
              {alternatives.map((alt, idx) => (
                <li key={idx} className="max-w-[70ch]">{alt}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
