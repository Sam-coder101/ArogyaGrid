"""
ArogyaGrid — Disease Awareness Poster Agent
=============================================
Agent inputs:  DiseaseSignal dict, target language, geo_target
Agent tools:   select_fact_template (from pre-approved health-authority sheets),
               gemini_localize_copy (rephrase only — no new medical facts),
               imagen_generate (Imagen 3 stub / Pillow fallback)
Agent output:  AwarenessPoster dict (image base64 + caption)

Guardrail: agent is explicitly restricted to pre-approved fact templates.
Gemini rewrites tone/language — never generates new medical claims.
"""
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data.models import AwarenessPoster, DiseaseSignal
from providers.imagen_provider import generate_poster
from providers.gemini_provider import generate_text
from providers.translation_provider import translate_text, LANGUAGE_NAMES

# Pre-approved health-authority fact templates (MoHFW / NVBDCP sourced)
FACT_TEMPLATES = {
    "dengue": {
        "disease_name": "Dengue Fever",
        "symptoms": ["High fever (sudden onset)", "Severe headache", "Pain behind the eyes", "Joint and muscle pain", "Skin rash", "Mild bleeding (nose, gums)"],
        "prevention": ["Use mosquito repellent (especially dawn and dusk)", "Wear long-sleeved clothing", "Use mosquito nets while sleeping", "Remove standing water from containers, coolers, pots", "Cover water storage containers"],
        "when_to_seek_care": "Go to your nearest PHC or hospital IMMEDIATELY if you have high fever for more than 2 days, severe stomach pain, vomiting blood, or bleeding from nose or gums.",
        "hotline": "National Vector Borne Disease Control Programme: 1800-11-4419",
    },
    "malaria": {
        "disease_name": "Malaria",
        "symptoms": ["Cyclical high fever with chills and sweating", "Headache", "Muscle pain", "Nausea and vomiting", "Fatigue"],
        "prevention": ["Sleep under an insecticide-treated mosquito net", "Use mosquito repellent", "Take malaria prophylaxis if prescribed", "Drain and clean stagnant water weekly", "Keep surroundings clean"],
        "when_to_seek_care": "See a health worker immediately if fever recurs every 2-3 days or if you feel very weak or confused.",
        "hotline": "NVBDCP Malaria Helpline: 1800-11-4419",
    },
    "diarrhoea": {
        "disease_name": "Diarrhoea / Gastroenteritis",
        "symptoms": ["Frequent loose or watery stools", "Stomach cramps", "Nausea", "Vomiting", "Mild fever"],
        "prevention": ["Wash hands with soap before eating and after using toilet", "Drink only clean, boiled, or purified water", "Eat freshly cooked food", "Avoid street food during outbreak periods", "Cover cooked food"],
        "when_to_seek_care": "Seek care immediately for infants, elderly, or anyone who cannot keep fluids down, shows signs of dehydration (dry mouth, sunken eyes, no urination for 6+ hours), or has blood in stools.",
        "hotline": "Integrated Disease Surveillance: 11-23061914",
    },
    "viral_fever": {
        "disease_name": "Viral Fever / Respiratory Illness",
        "symptoms": ["Fever", "Body ache and fatigue", "Sore throat", "Runny nose", "Cough", "Loss of appetite"],
        "prevention": ["Cover your mouth when coughing or sneezing", "Wash hands frequently", "Avoid close contact with sick people", "Stay home when unwell", "Keep surroundings ventilated"],
        "when_to_seek_care": "See a doctor if fever is above 103°F (39.4°C), if breathing is difficult, or if fever does not improve in 3 days.",
        "hotline": "State Health Helpline: 104",
    },
}

DISEASE_TO_TEMPLATE = {
    "dengue-consistent pattern": "dengue",
    "malaria-consistent pattern": "malaria",
    "acute gastroenteritis / diarrhoeal outbreak pattern": "diarrhoea",
    "respiratory illness / viral fever pattern": "viral_fever",
}


# ── Tool: select_fact_template ────────────────────────────────────────────────
def tool_select_fact_template(disease_hypothesis: str) -> Optional[dict]:
    """Maps a DiseaseSignal hypothesis to the correct pre-approved fact sheet."""
    template_key = DISEASE_TO_TEMPLATE.get(disease_hypothesis)
    if template_key:
        return FACT_TEMPLATES[template_key]
    # Fuzzy fallback
    for k, v in DISEASE_TO_TEMPLATE.items():
        if k.split("-")[0] in disease_hypothesis.lower():
            return FACT_TEMPLATES[v]
    return None


# ── Tool: gemini_localize_copy ────────────────────────────────────────────────
def tool_gemini_localize_copy(
    template: dict,
    geo_target: str,
    disease_signal: dict,
) -> dict:
    """
    Uses Gemini to write localized poster copy from the APPROVED template only.
    Gemini rewrites tone and local references — it does NOT generate new medical facts.
    """
    symptoms_str   = "\n".join(f"• {s}" for s in template["symptoms"])
    prevention_str = "\n".join(f"• {p}" for p in template["prevention"])

    prompt = f"""You are a public health communication writer for India's National Health Mission.
Using ONLY the approved facts below, write concise, clear poster copy for a health awareness poster.
Target region: {geo_target}
Disease alert level: {disease_signal.get('confidence', 0.7):.0%} confidence signal, trend: {disease_signal.get('trend', 'RISING')}

APPROVED FACTS (use only these — do NOT invent new medical claims):
Disease: {template['disease_name']}
Symptoms:
{symptoms_str}
Prevention:
{prevention_str}
When to seek care: {template['when_to_seek_care']}

Write:
1. A short headline (max 10 words, alarming but not panic-inducing)
2. A 1-sentence alert message mentioning the region
3. Symptoms section (use approved list, max 4 items for poster readability)
4. Prevention section (use approved list, max 4 items)
5. Call-to-action sentence (use the approved "when to seek care" text)

Format as JSON: {{"headline": "", "alert_msg": "", "symptoms": [], "prevention": [], "cta": ""}}
Return ONLY valid JSON."""

    result_text = generate_text(prompt, temperature=0.3)

    import json, re
    try:
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback if JSON parse fails
    return {
        "headline": f"{template['disease_name']} Alert — {geo_target}",
        "alert_msg": f"A {template['disease_name'].lower()} pattern has been detected in {geo_target}. Take precautions.",
        "symptoms": template["symptoms"][:4],
        "prevention": template["prevention"][:4],
        "cta": template["when_to_seek_care"],
    }


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(
    db: Session,
    disease_signal: dict,
    target_language: str = "en",
    geo_target: Optional[str] = None,
    output_dir: str = "data/posters",
) -> dict:
    """
    Awareness Poster Agent — main entry point.
    Returns an AwarenessPoster dict including base64-encoded image.
    """
    geo = geo_target or disease_signal.get("geo_block", disease_signal.get("district", "your area"))

    # Tool 1: Select pre-approved fact template
    template = tool_select_fact_template(disease_signal.get("disease_hypothesis", ""))
    if not template:
        return {
            "error": f"No approved fact template for disease hypothesis: {disease_signal.get('disease_hypothesis')}",
            "agent": "AwarenessPosterAgent",
        }

    # Tool 2: Gemini localizes copy from approved template
    copy = tool_gemini_localize_copy(template, geo, disease_signal)

    # Build Imagen prompt from the localized copy (facts only, no hallucination risk)
    imagen_prompt = (
        f"Public health awareness poster for {template['disease_name']} prevention in rural India. "
        f"Headline: '{copy['headline']}'. "
        f"Simple, clean design. Shows a family at a health centre. Government of India style. "
        f"Text includes prevention tips: {'; '.join(copy['prevention'][:3])}. "
        f"Warm, reassuring colour palette (blues and greens). Text in large readable font."
    )

    # Tool 3: Generate poster image (Imagen 3 stub / Pillow fallback)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = f"{output_dir}/poster_{disease_signal.get('id', 'demo')}_{target_language}.png"
    image_result = generate_poster(imagen_prompt, output_path=output_path)

    # Translate caption if needed
    caption_en = (
        f"{copy['headline']} | {copy['alert_msg']} | "
        f"Prevention: {'; '.join(copy['prevention'][:2])} | "
        f"{copy['cta']} | Hotline: {template['hotline']}"
    )
    caption = caption_en
    if target_language != "en":
        caption = translate_text(caption_en, target_lang=target_language)

    # Persist poster record
    poster = AwarenessPoster(
        disease_signal_id=disease_signal.get("id"),
        language=target_language,
        geo_target=geo,
        image_url=output_path,
        caption_text=caption,
        fact_template_used=DISEASE_TO_TEMPLATE.get(disease_signal.get("disease_hypothesis", ""), "unknown"),
        created_at=datetime.utcnow(),
    )
    db.add(poster)
    db.flush()

    return {
        "id": poster.id,
        "disease_hypothesis": disease_signal.get("disease_hypothesis"),
        "geo_target": geo,
        "language": target_language,
        "language_name": LANGUAGE_NAMES.get(target_language, target_language),
        "copy": copy,
        "caption": caption,
        "image_base64": image_result.get("image_base64", ""),
        "image_path": output_path,
        "stub_mode": image_result.get("stub_mode", True),
        "fact_template": template["disease_name"],
        "agent": "AwarenessPosterAgent",
    }
