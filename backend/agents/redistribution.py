"""
ArogyaGrid — Cross-District Redistribution Optimizer Agent
============================================================
Agent inputs:  Alert dict (active stock-out alert)
Agent tools:   find_surplus_candidates (BigQuery/SQLite query),
               score_candidates (distance × surplus × urgency),
               gemini_rationale
Agent output:  RedistributionRecommendation list (persisted + returned)

Keeps a human in the loop: recommendations go to "PENDING" status —
a DHO must approve/reject, not the system.
"""
from datetime import datetime
from typing import List, Optional
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data.models import InventoryItem, RedistributionRecommendation, PHC, Medicine, Alert
from providers.gemini_provider import generate_text
import config


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Compute distance in km between two lat/lon points."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Tool: find_surplus_candidates ────────────────────────────────────────────
def tool_find_surplus_candidates(
    db: Session,
    drug_id: str,
    needy_phc_id: str,
    min_transfer_qty: int,
    same_state_only: bool = True,
) -> List[dict]:
    """
    Finds PHCs with surplus stock of a given drug.
    Surplus = quantity > 2× average daily_rate × lead_time (a proxy safety floor).
    STUB → BigQuery query when running at scale.
    """
    needy_phc = db.get(PHC, needy_phc_id)
    state_filter = needy_phc.state if (same_state_only and needy_phc) else None

    items = (
        db.query(InventoryItem)
        .join(PHC, InventoryItem.phc_id == PHC.id)
        .filter(
            InventoryItem.drug_id == drug_id,
            InventoryItem.phc_id != needy_phc_id,
        )
        .all()
    )

    medicine = db.get(Medicine, drug_id)
    lead = medicine.restock_lead_days if medicine else 7

    candidates = []
    for item in items:
        phc = db.get(PHC, item.phc_id)
        if state_filter and phc.state != state_filter:
            continue
        # Simple surplus heuristic: qty > 1.8× (lead_time * expected daily)
        # We use 20 units/day as an average — in prod this comes from ForecastResult
        approx_daily = 10
        safety_floor = approx_daily * lead * 1.8
        surplus = item.quantity - safety_floor
        if surplus >= min_transfer_qty:
            dist = _haversine_km(
                needy_phc.latitude or 0, needy_phc.longitude or 0,
                phc.latitude or 0, phc.longitude or 0
            ) if needy_phc else 999
            candidates.append({
                "phc_id": phc.id,
                "phc_name": phc.name,
                "district": phc.district,
                "state": phc.state,
                "current_qty": item.quantity,
                "available_to_transfer": int(surplus),
                "distance_km": round(dist, 1),
            })

    return sorted(candidates, key=lambda x: x["distance_km"])


# ── Tool: score_candidates ───────────────────────────────────────────────────
def tool_score_candidates(candidates: List[dict], needed_qty: int) -> List[dict]:
    """
    Scores candidates: lower is better.
    Score = distance_km × 0.5 + (1 - surplus_ratio) × 100
    This rewards nearby PHCs with large surplus.
    STUB → Google Maps Distance Matrix API for real road distance when USE_REAL_GCP=true.
    """
    scored = []
    for c in candidates:
        surplus_ratio = min(1.0, c["available_to_transfer"] / max(needed_qty, 1))
        score = c["distance_km"] * 0.5 + (1 - surplus_ratio) * 100
        scored.append({**c, "score": round(score, 2), "surplus_ratio": round(surplus_ratio, 2)})
    return sorted(scored, key=lambda x: x["score"])


# ── Tool: gemini_rationale ────────────────────────────────────────────────────
def tool_gemini_rationale(
    needy_phc: PHC,
    source_phc: dict,
    drug_name: str,
    qty: int,
) -> str:
    """Uses Gemini to write a plain-language rationale for the redistribution recommendation."""
    prompt = f"""You are a supply-chain coordinator for India's PHC network.

Redistribution recommendation:
- Needy PHC: {needy_phc.name}, {needy_phc.district} district
- Source PHC: {source_phc['phc_name']}, {source_phc['district']} district
- Distance: {source_phc['distance_km']} km
- Drug: {drug_name}
- Recommended transfer quantity: {qty} units
- Source PHC current stock: {source_phc['current_qty']} units
- After transfer, source will retain: {source_phc['current_qty'] - qty} units

Write 2 sentences explaining why this is the best redistribution option and what the DHO should do.
Be practical and specific about logistics."""

    return generate_text(prompt, temperature=0.25)


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(
    db: Session,
    alert: dict,
    max_recommendations: int = 3,
) -> List[dict]:
    """
    Redistribution Optimizer Agent — main entry point.
    Returns a list of RedistributionRecommendation dicts (top candidates).
    """
    phc_id  = alert["phc_id"]
    drug_id = alert["drug_id"]

    # How much do we need to transfer?
    current_qty    = alert.get("current_stock", 0)
    days_remaining = alert.get("days_remaining", 0)
    # Target: get enough stock for 30 days
    needed_qty = max(50, int(alert.get("forecast_daily_rate", 20) * 30 - current_qty))

    # Tool 1: Find surplus candidates
    candidates = tool_find_surplus_candidates(db, drug_id, phc_id, min_transfer_qty=needed_qty // 2)

    if not candidates:
        return [{
            "message": "No suitable surplus PHC found in the same state. Consider inter-state redistribution or emergency procurement.",
            "agent": "RedistributionOptimizerAgent",
        }]

    # Tool 2: Score candidates
    scored = tool_score_candidates(candidates, needed_qty)
    top    = scored[:max_recommendations]

    needy_phc = db.get(PHC, phc_id)
    medicine  = db.get(Medicine, drug_id)
    drug_name = medicine.generic_name if medicine else drug_id

    recommendations = []
    for candidate in top:
        qty_to_transfer = min(needed_qty, candidate["available_to_transfer"])

        # Tool 3: Gemini rationale
        rationale = tool_gemini_rationale(needy_phc, candidate, drug_name, qty_to_transfer)

        rec = RedistributionRecommendation(
            from_phc_id=candidate["phc_id"],
            to_phc_id=phc_id,
            drug_id=drug_id,
            qty=qty_to_transfer,
            distance_km=candidate["distance_km"],
            rationale=rationale,
            status="PENDING",
            created_at=datetime.utcnow(),
        )
        db.add(rec)
        db.flush()

        recommendations.append({
            "id": rec.id,
            "from_phc_id": candidate["phc_id"],
            "from_phc_name": candidate["phc_name"],
            "from_district": candidate["district"],
            "to_phc_id": phc_id,
            "to_phc_name": needy_phc.name if needy_phc else phc_id,
            "drug_id": drug_id,
            "drug_name": drug_name,
            "qty": qty_to_transfer,
            "distance_km": candidate["distance_km"],
            "score": candidate["score"],
            "source_current_stock": candidate["current_qty"],
            "rationale": rationale,
            "status": "PENDING",
            "agent": "RedistributionOptimizerAgent",
        })

    return recommendations
