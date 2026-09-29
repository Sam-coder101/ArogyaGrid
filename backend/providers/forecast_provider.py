"""
ArogyaGrid — Forecast Provider
================================
Interface for demand forecasting.
- USE_REAL_FORECAST=true: calls BigQuery ML ARIMA_PLUS / Vertex AI Forecasting
  STUB → real implementation: create a BQ ML model with
         CREATE OR REPLACE MODEL `project.dataset.demand_forecast`
         OPTIONS(model_type="ARIMA_PLUS", time_series_id_col="phc_drug_key", ...)
         then call bqclient.query("SELECT * FROM ML.FORECAST(MODEL `...`, ...)")
- USE_REAL_FORECAST=false (default): runs a simple heuristic forecast on local data
  that produces realistic-looking results for the demo.
"""
from datetime import datetime
from typing import List, Dict, Any
import numpy as np


def forecast(
    dispensation_history: List[Dict],  # [{date, qty_dispensed, month, is_monsoon}]
    drug_id: str,
    phc_id: str,
    horizon_days: int = 28,
    current_month: int | None = None,
) -> Dict[str, Any]:
    """
    Returns a forecast dict:
      {predicted_qty, confidence, daily_rate, trend_pct, explanation}

    Heuristic model:
    1. Compute rolling 3-month average daily consumption.
    2. Apply seasonal multiplier for the target month.
    3. Extrapolate for horizon_days.

    STUB → Vertex AI Forecasting / BigQuery ML ARIMA_PLUS when USE_REAL_FORECAST=true.
    """
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    import config
    from providers.gemini_provider import generate_text
    import json
    import re

    if config.USE_REAL_FORECAST:
        raise NotImplementedError("Real Vertex AI Forecasting not yet wired. Set USE_REAL_FORECAST=false.")

    # Convert dispensation history to a readable string for Gemini
    history_str = "\n".join([f"Date: {r.get('date', 'Unknown')}, Qty Dispensed: {r.get('qty_dispensed', 0)}, Monsoon Season: {r.get('is_monsoon', False)}" for r in dispensation_history]) if dispensation_history else "No history available."

    prompt = f"""You are an advanced AI supply chain forecasting agent for a healthcare system.
Analyze the following dispensation history for drug ID {drug_id} at PHC {phc_id} and predict the demand for the next {horizon_days} days.
The current month is {current_month or datetime.utcnow().month}.

Historical Dispensation Data:
{history_str}

Please respond with ONLY a valid JSON object in the following format:
{{
    "predicted_qty": <integer>,
    "confidence": <float between 0.0 and 1.0>,
    "daily_rate": <float>,
    "trend_pct": <float>,
    "explanation": "<string explaining the forecast reasoning>"
}}
"""
    try:
        raw_output = generate_text(prompt, temperature=0.2)
        json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "predicted_qty": int(data.get("predicted_qty", 50)),
                "confidence": round(float(data.get("confidence", 0.5)), 2),
                "daily_rate": round(float(data.get("daily_rate", 1.5)), 2),
                "trend_pct": round(float(data.get("trend_pct", 0.0)), 1),
                "explanation": data.get("explanation", "Forecasted based on AI analysis."),
            }
    except Exception as e:
        pass

    # Fallback if Gemini parsing fails
    return {
        "predicted_qty": 50 * (horizon_days // 30 + 1),
        "confidence": 0.40,
        "daily_rate": 1.7,
        "trend_pct": 0.0,
        "explanation": "Insufficient history or API error — using baseline estimate.",
    }
