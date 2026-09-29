"""
ArogyaGrid — Stock-out Early Warning Agent
===========================================
Agent inputs:  ForecastResult dict, current InventoryItem, lead_time_days
Agent tools:   get_current_stock, threshold_check (ML + rule-based dual check),
               create_alert
Agent output:  Alert (persisted to DB + returned as dict, or None if no risk)

Key design: combines ML forecast with deterministic safety-stock floor.
If EITHER signal predicts a breach, an alert fires — never relies on ML alone
for a safety-critical decision.
"""
from datetime import datetime, timedelta
from typing import Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data.models import InventoryItem, Alert, Medicine, PHC
from providers.gemini_provider import generate_text
import config


# ── Tool: get_current_stock ──────────────────────────────────────────────────
def tool_get_current_stock(db: Session, phc_id: str, drug_id: str) -> dict:
    """Reads the live inventory level for a PHC x drug combination."""
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.phc_id == phc_id, InventoryItem.drug_id == drug_id)
        .first()
    )
    if not item:
        return {"quantity": 0, "unit": "units", "last_updated": None}
    return {
        "quantity": item.quantity,
        "unit": item.unit,
        "last_updated": item.last_updated.isoformat() if item.last_updated else None,
    }


# ── Tool: threshold_check ────────────────────────────────────────────────────
def tool_threshold_check(
    current_qty: int,
    forecast: dict,
    lead_time_days: int,
    safety_stock_days: int = None,
) -> dict:
    """
    Dual-signal threshold check:
    1. ML forecast path: will predicted demand exceed current stock within lead_time window?
    2. Rule-based floor: is current stock below safety_stock_days × daily_rate?

    Returns: {alert_needed, severity, predicted_stockout_date, reason, days_remaining}
    """
    safety_stock_days = safety_stock_days or config.SAFETY_STOCK_DAYS

    daily_rate   = forecast.get("daily_rate", 1.0)
    predicted_qty = forecast.get("predicted_qty", 0)
    horizon_days  = forecast.get("horizon_days", 28)

    # Days of stock remaining at forecast daily_rate
    days_remaining = (current_qty / daily_rate) if daily_rate > 0 else 999

    # ML path: will we stock-out within lead_time + safety_stock window?
    ml_alert    = days_remaining < (lead_time_days + safety_stock_days)
    # Rule path: is current qty below the safety floor?
    rule_alert  = current_qty < (daily_rate * safety_stock_days)

    if not (ml_alert or rule_alert):
        return {"alert_needed": False, "days_remaining": round(days_remaining, 1)}

    # Determine severity
    if days_remaining < lead_time_days:
        severity = "HIGH"   # Already can't restock in time
    elif days_remaining < (lead_time_days + safety_stock_days):
        severity = "MEDIUM"
    else:
        severity = "LOW"

    predicted_stockout = datetime.utcnow() + timedelta(days=days_remaining)
    reason = (
        f"ML forecast: {days_remaining:.0f} days of stock remaining at projected "
        f"daily rate of {daily_rate:.1f} units/day. "
        f"Lead time: {lead_time_days} days. "
        f"{'Rule-based floor also triggered. ' if rule_alert else ''}"
        f"Predicted stock-out: {predicted_stockout.strftime('%d %b %Y')}."
    )

    return {
        "alert_needed": True,
        "severity": severity,
        "days_remaining": round(days_remaining, 1),
        "predicted_stockout_date": predicted_stockout,
        "reason": reason,
        "ml_triggered": ml_alert,
        "rule_triggered": rule_alert,
    }


# ── Tool: create_alert ───────────────────────────────────────────────────────
def tool_create_alert(
    db: Session,
    phc_id: str,
    drug_id: str,
    threshold_result: dict,
    forecast: dict,
) -> Alert:
    """Creates and persists an Alert record."""
    # Use Gemini to write the recommended action in plain language
    medicine = db.get(Medicine, drug_id)
    phc      = db.get(PHC, phc_id)
    drug_name = medicine.generic_name if medicine else drug_id
    phc_name  = phc.name if phc else phc_id

    prompt = f"""You are an alert system for India's Primary Health Centre supply chain.

Alert details:
- PHC: {phc_name} ({phc_id})
- Medicine: {drug_name}
- Severity: {threshold_result['severity']}
- Days of stock remaining: {threshold_result['days_remaining']:.0f} days
- Predicted stock-out: {threshold_result.get('predicted_stockout_date', 'soon')}

Write a 1-sentence recommended action for the District Health Officer.
Be specific and actionable. Example: "Initiate emergency transfer of at least 200 strips from a nearby PHC within 5 days." """

    recommended_action = generate_text(prompt, temperature=0.2)

    alert = Alert(
        alert_type="stock-out",
        phc_id=phc_id,
        drug_id=drug_id,
        predicted_date=threshold_result.get("predicted_stockout_date"),
        confidence=forecast.get("confidence", 0.7),
        severity=threshold_result["severity"],
        status="OPEN",
        recommended_action=recommended_action,
        created_at=datetime.utcnow(),
    )
    db.add(alert)
    db.flush()
    return alert


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(
    db: Session,
    phc_id: str,
    drug_id: str,
    forecast: dict,
) -> Optional[dict]:
    """
    Stock-out Early Warning Agent — main entry point.
    Returns an Alert dict if a risk is detected, else None.
    """
    # Tool 1: Get current stock
    stock = tool_get_current_stock(db, phc_id, drug_id)

    # Determine lead time
    medicine     = db.get(Medicine, drug_id)
    lead_time    = medicine.restock_lead_days if medicine else config.STOCKOUT_LEAD_DAYS

    # Tool 2: Dual-signal threshold check
    check = tool_threshold_check(
        current_qty=stock["quantity"],
        forecast=forecast,
        lead_time_days=lead_time,
    )

    if not check.get("alert_needed"):
        return None

    # Tool 3: Create and persist alert
    alert = tool_create_alert(db, phc_id, drug_id, check, forecast)

    medicine = db.get(Medicine, drug_id)
    phc      = db.get(PHC, phc_id)

    return {
        "id": alert.id,
        "phc_id": phc_id,
        "phc_name": phc.name if phc else phc_id,
        "drug_id": drug_id,
        "drug_name": medicine.generic_name if medicine else drug_id,
        "severity": alert.severity,
        "days_remaining": check["days_remaining"],
        "predicted_stockout_date": check.get("predicted_stockout_date", {}).isoformat() if check.get("predicted_stockout_date") else None,
        "current_stock": stock["quantity"],
        "recommended_action": alert.recommended_action,
        "ml_triggered": check.get("ml_triggered", False),
        "rule_triggered": check.get("rule_triggered", False),
        "agent": "StockoutEarlyWarningAgent",
    }
