"""
ArogyaGrid — Demand Forecast Agent
=====================================
Agent inputs:  PHC ID, drug ID, horizon days
Agent tools:   get_dispensation_history (data query), run_forecast (ForecastProvider),
               get_seasonal_context, gemini_annotate
Agent output:  ForecastResult (persisted to DB + returned as dict)

This agent has a distinct reasoning job: it calls the forecasting model,
then uses Gemini to annotate the output in plain language for the dashboard.
That annotation step is where the LLM adds genuine value — not in generating
the forecast numbers directly.
"""
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data.models import DispensationHistory, ForecastResult, Medicine, PHC
from providers.forecast_provider import forecast as run_forecast_model
from providers.gemini_provider import generate_text
import config


# ── Tool: get_dispensation_history ──────────────────────────────────────────
def tool_get_dispensation_history(
    db: Session, phc_id: str, drug_id: str, months: int = 6
) -> list:
    """Fetches historical dispensation records for a PHC x drug combination."""
    rows = (
        db.query(DispensationHistory)
        .filter(
            DispensationHistory.phc_id == phc_id,
            DispensationHistory.drug_id == drug_id,
        )
        .order_by(DispensationHistory.date)
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "qty_dispensed": r.qty_dispensed,
            "month": r.month,
            "is_monsoon": r.is_monsoon,
        }
        for r in rows[-months:]
    ]


# ── Tool: get_seasonal_context ───────────────────────────────────────────────
def tool_get_seasonal_context(month: int | None = None) -> dict:
    """Returns the current seasonal context (month, monsoon flag, disease calendar)."""
    m = month or datetime.utcnow().month
    MONSOON = {6, 7, 8, 9, 10}
    DISEASE_CALENDAR = {
        6: "monsoon onset — dengue, malaria, leptospirosis risk rising",
        7: "peak monsoon — dengue, malaria, cholera alerts; ORS demand high",
        8: "peak monsoon — dengue epidemic risk; antipyretic demand highest",
        9: "monsoon tail — dengue cases still high; typhoid risk",
        10: "post-monsoon — dengue cases declining but still elevated; viral fever",
        11: "winter onset — respiratory infections rising",
        12: "winter peak — respiratory, asthma, cold/flu",
        1:  "winter — respiratory peak",
        2:  "spring — reducing seasonality",
        3:  "summer onset",
        4:  "summer — dehydration, heat stroke; ORS demand may rise",
        5:  "peak summer — heat-related illness; allergy season",
    }
    return {
        "current_month": m,
        "is_monsoon_season": m in MONSOON,
        "disease_calendar_note": DISEASE_CALENDAR.get(m, "No major seasonal pattern"),
    }


# ── Tool: gemini_annotate ────────────────────────────────────────────────────
def tool_gemini_annotate(
    drug_name: str,
    phc_name: str,
    forecast_result: dict,
    seasonal_context: dict,
) -> str:
    """Uses Gemini to generate a plain-language annotation of the forecast for the dashboard."""
    prompt = f"""You are a public health supply-chain analyst assistant for India's PHC network.

Drug: {drug_name}
PHC: {phc_name}
Forecast for next {forecast_result.get('horizon_days', 28)} days: {forecast_result['predicted_qty']} units
Confidence: {forecast_result['confidence']:.0%}
Trend vs last month: {forecast_result.get('trend_pct', 0):+.1f}%
Seasonal context: {seasonal_context['disease_calendar_note']}

Write a 1-2 sentence plain-language summary for a District Health Officer dashboard.
Be specific about numbers and the seasonal reason if applicable.
Keep it factual and concise. Do not use bullet points."""

    return generate_text(prompt, temperature=0.2)


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(
    db: Session,
    phc_id: str,
    drug_id: str,
    horizon_days: int = 28,
) -> dict:
    """
    Demand Forecast Agent — main entry point.
    Called by the Orchestrator or directly via the API.
    Returns a ForecastResult dict.
    """
    # Tool 1: Fetch dispensation history
    history = tool_get_dispensation_history(db, phc_id, drug_id)

    # Tool 2: Get seasonal context
    seasonal = tool_get_seasonal_context()

    # Tool 3: Run forecast model
    forecast_raw = run_forecast_model(
        dispensation_history=history,
        drug_id=drug_id,
        phc_id=phc_id,
        horizon_days=horizon_days,
        current_month=seasonal["current_month"],
    )
    forecast_raw["horizon_days"] = horizon_days

    # Resolve names for annotation
    medicine = db.get(Medicine, drug_id)
    phc      = db.get(PHC, phc_id)
    drug_name = medicine.generic_name if medicine else drug_id
    phc_name  = phc.name if phc else phc_id

    # Tool 4: Gemini annotation (plain-language explanation)
    explanation = tool_gemini_annotate(drug_name, phc_name, forecast_raw, seasonal)

    # Persist ForecastResult
    fr = ForecastResult(
        phc_id=phc_id,
        drug_id=drug_id,
        forecast_date=datetime.utcnow(),
        horizon_days=horizon_days,
        predicted_qty=forecast_raw["predicted_qty"],
        confidence=forecast_raw["confidence"],
        explanation=explanation,
    )
    db.add(fr)
    db.flush()

    return {
        "id": fr.id,
        "phc_id": phc_id,
        "phc_name": phc_name,
        "drug_id": drug_id,
        "drug_name": drug_name,
        "horizon_days": horizon_days,
        "predicted_qty": forecast_raw["predicted_qty"],
        "confidence": forecast_raw["confidence"],
        "daily_rate": forecast_raw["daily_rate"],
        "trend_pct": forecast_raw.get("trend_pct", 0),
        "seasonal_context": seasonal,
        "explanation": explanation,
        "agent": "DemandForecastAgent",
    }
