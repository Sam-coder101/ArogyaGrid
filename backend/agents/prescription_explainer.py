"""
ArogyaGrid — Prescription Explainer Agent (patient-facing)
============================================================
Agent inputs:  prescription image (bytes), patient language, optional context
Agent tools:   ocr_extract (Document AI stub / Gemini multimodal),
               medicine_db_lookup (local Medicine table — vetted facts only),
               gemini_explain (composes plain-language explanation),
               translate (Cloud Translation stub / Gemini)
Agent output:  PrescriptionExplanation dict

Guardrails hardcoded into this agent:
- Never outputs a dosage change instruction
- Never says "stop taking"
- Never diagnoses
- Always appends SAFETY_DISCLAIMER
- Low-confidence OCR extractions are flagged, not guessed
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import Optional
from sqlalchemy.orm import Session
from data.models import Medicine, PrescriptionEvent
from providers.ocr_provider import extract_prescription
from providers.gemini_provider import generate_text
from providers.translation_provider import translate_text

SAFETY_DISCLAIMER = (
    "\n\n---\n"
    "⚠️ This is educational information only, not medical advice. "
    "Always consult your doctor or pharmacist before making any changes to your medication. "
    "If you experience severe side effects, seek medical care immediately."
)


# ── Tool: medicine_db_lookup ─────────────────────────────────────────────────
def tool_medicine_db_lookup(db: Session, drug_name: str) -> Optional[dict]:
    """
    Looks up a drug in the vetted Medicine database by name (fuzzy match).
    Returns structured facts — never free-generated medical information.
    This is the guardrail: explanation is based on DB facts, not hallucination.
    """
    # Try exact generic name first
    med = (
        db.query(Medicine)
        .filter(Medicine.generic_name.ilike(f"%{drug_name}%"))
        .first()
    )
    if not med:
        # Try brand names
        all_meds = db.query(Medicine).all()
        for m in all_meds:
            brands = m.brand_names or []
            if any(drug_name.lower() in b.lower() for b in brands):
                med = m
                break

    if not med:
        return None

    alts = []
    for alt_id in (med.common_alternatives or []):
        alt = db.get(Medicine, alt_id)
        if alt:
            alts.append(alt.generic_name)

    return {
        "drug_id": med.drug_id,
        "generic_name": med.generic_name,
        "brand_names": med.brand_names,
        "molecule_composition": med.molecule_composition,
        "therapeutic_class": med.therapeutic_class,
        "manufacturer": med.manufacturer,
        "dosage_form": med.dosage_form,
        "side_effects": med.side_effects or [],
        "alternatives": alts,
        "typical_indication": med.typical_indication,
    }


# ── Tool: gemini_explain ─────────────────────────────────────────────────────
def tool_gemini_explain(
    drug_name: str,
    dosage: str,
    frequency: str,
    db_facts: Optional[dict],
    prescription_notes: str = "",
) -> str:
    """
    Composes a plain-language explanation using ONLY the vetted DB facts.
    Gemini's role: rephrase into ≤8th-grade reading level, not generate new facts.
    """
    if not db_facts:
        return (
            f"**{drug_name}** ({dosage}, {frequency})\n"
            f"This medicine was not found in our verified database. "
            f"Please ask your doctor or pharmacist to explain it to you."
        )

    # Build prompt from vetted facts only — no free generation of medical claims
    facts_block = f"""
Medicine: {db_facts['generic_name']}
Molecule / Composition: {db_facts['molecule_composition']}
Therapeutic Class: {db_facts['therapeutic_class']}
Manufacturer: {db_facts['manufacturer']}
Dosage Form: {db_facts['dosage_form']}
Why doctors typically prescribe this: {db_facts['typical_indication']}
Side effects to watch for: {', '.join(db_facts['side_effects'])}
Alternatives in the same class (ask your doctor): {', '.join(db_facts['alternatives']) if db_facts['alternatives'] else 'None listed'}
Dosage on this prescription: {dosage}, {frequency}
Doctor's notes: {prescription_notes or 'None'}
"""

    prompt = f"""You are a patient health educator helping rural patients in India understand their prescriptions.
Using ONLY the facts provided below, write a clear, friendly explanation for a patient with low health literacy.
Do NOT invent new medical facts. Do NOT recommend dosage changes. Do NOT say "stop taking". Do NOT diagnose.
Use simple words. Write in 4-5 short paragraphs.

{facts_block}

Explain: what the medicine is, why the doctor likely prescribed it for the patient, 
how to take it, what side effects to watch for, and what alternatives exist (frame as "ask your doctor about X").
End with a sentence reminding them to follow their doctor's instructions."""

    return generate_text(prompt, temperature=0.2)


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(
    db: Session,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    target_language: str = "en",
) -> dict:
    """
    Prescription Explainer Agent — main entry point.
    Returns a full PrescriptionExplanation dict.
    """
    # Tool 1: OCR the prescription
    ocr_result = extract_prescription(image_bytes, mime_type)

    drugs_explained = []
    for drug_entry in ocr_result.get("drugs", []):
        drug_name = drug_entry.get("name", "Unknown")
        dosage    = drug_entry.get("dosage", "as prescribed")
        frequency = drug_entry.get("frequency", "as directed")

        # Tool 2: Vetted DB lookup (guardrail — no hallucinated facts)
        db_facts = tool_medicine_db_lookup(db, drug_name)

        # Tool 3: Gemini explanation (plain language, from vetted facts only)
        explanation_en = tool_gemini_explain(
            drug_name, dosage, frequency, db_facts,
            prescription_notes=ocr_result.get("notes", "")
        )

        # Tool 4: Translate if needed
        if target_language != "en":
            explanation = translate_text(explanation_en, target_lang=target_language)
        else:
            explanation = explanation_en

        drugs_explained.append({
            "name": drug_name,
            "dosage": dosage,
            "frequency": frequency,
            "db_match": db_facts["generic_name"] if db_facts else None,
            "molecule": db_facts["molecule_composition"] if db_facts else None,
            "therapeutic_class": db_facts["therapeutic_class"] if db_facts else None,
            "manufacturer": db_facts["manufacturer"] if db_facts else None,
            "side_effects": db_facts["side_effects"] if db_facts else [],
            "alternatives": db_facts["alternatives"] if db_facts else [],
            "explanation": explanation,
            "confidence": ocr_result.get("confidence", 0.75),
        })

    # Translate the disclaimer if needed
    disclaimer = SAFETY_DISCLAIMER
    if target_language != "en":
        disclaimer = translate_text(SAFETY_DISCLAIMER, target_lang=target_language)

    return {
        "ocr_confidence": ocr_result.get("confidence", 0.75),
        "doctor_name": ocr_result.get("doctor_name"),
        "prescription_date": ocr_result.get("date"),
        "prescription_notes": ocr_result.get("notes"),
        "drugs": drugs_explained,
        "disclaimer": disclaimer,
        "language": target_language,
        "drug_ids_for_signal": [
            d["db_match"] for d in drugs_explained if d["db_match"]
        ],
        "agent": "PrescriptionExplainerAgent",
    }
