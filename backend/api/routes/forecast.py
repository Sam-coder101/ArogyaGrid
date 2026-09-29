"""
ArogyaGrid — Forecast Routes
POST /api/forecast/run         — run Demand Forecast Agent for a PHC x drug
GET  /api/forecast/results     — list recent forecast results
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from data.database import get_db
from data.models import ForecastResult, Medicine, PHC
import agents.demand_forecast as demand_forecast_agent

router = APIRouter()


class ForecastRequest(BaseModel):
    phc_id: str
    drug_id: str
    horizon_days: int = 28


@router.post("/run")
def run_forecast(req: ForecastRequest, db: Session = Depends(get_db)):
    result = demand_forecast_agent.run(db, req.phc_id, req.drug_id, req.horizon_days)
    db.commit()
    return result


@router.get("/results")
def list_forecast_results(
    phc_id: str = None,
    drug_id: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(ForecastResult)
    if phc_id:
        q = q.filter(ForecastResult.phc_id == phc_id)
    if drug_id:
        q = q.filter(ForecastResult.drug_id == drug_id)
    rows = q.order_by(ForecastResult.created_at.desc()).limit(limit).all()

    results = []
    for r in rows:
        phc = db.get(PHC, r.phc_id)
        med = db.get(Medicine, r.drug_id)
        results.append({
            "id": r.id,
            "phc_id": r.phc_id,
            "phc_name": phc.name if phc else r.phc_id,
            "drug_id": r.drug_id,
            "drug_name": med.generic_name if med else r.drug_id,
            "horizon_days": r.horizon_days,
            "predicted_qty": r.predicted_qty,
            "confidence": r.confidence,
            "explanation": r.explanation,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return results
