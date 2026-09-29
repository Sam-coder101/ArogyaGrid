"""
ArogyaGrid — Redistribution Routes
GET  /api/redistribution/        — list pending recommendations
POST /api/redistribution/run     — run optimizer for an alert
POST /api/redistribution/{id}/approve — DHO approves
POST /api/redistribution/{id}/reject  — DHO rejects
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from data.database import get_db
from data.models import RedistributionRecommendation, PHC, Medicine
import agents.redistribution as redistribution_agent

router = APIRouter()


@router.get("/")
def list_recommendations(status: str = "PENDING", db: Session = Depends(get_db)):
    recs = (
        db.query(RedistributionRecommendation)
        .filter(RedistributionRecommendation.status == status)
        .order_by(RedistributionRecommendation.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for r in recs:
        from_phc = db.get(PHC, r.from_phc_id)
        to_phc   = db.get(PHC, r.to_phc_id)
        med      = db.get(Medicine, r.drug_id)
        result.append({
            "id": r.id,
            "from_phc": from_phc.name if from_phc else r.from_phc_id,
            "from_district": from_phc.district if from_phc else None,
            "to_phc": to_phc.name if to_phc else r.to_phc_id,
            "to_district": to_phc.district if to_phc else None,
            "drug_name": med.generic_name if med else r.drug_id,
            "qty": r.qty,
            "distance_km": r.distance_km,
            "rationale": r.rationale,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


class RunRedistRequest(BaseModel):
    alert: dict


@router.post("/run")
def run_redistribution(req: RunRedistRequest, db: Session = Depends(get_db)):
    recs = redistribution_agent.run(db, req.alert)
    db.commit()
    return recs


@router.post("/{rec_id}/approve")
def approve(rec_id: int, db: Session = Depends(get_db)):
    r = db.get(RedistributionRecommendation, rec_id)
    if not r:
        raise HTTPException(404)
    r.status = "APPROVED"
    db.commit()
    return {"status": "APPROVED", "id": rec_id}


@router.post("/{rec_id}/reject")
def reject(rec_id: int, db: Session = Depends(get_db)):
    r = db.get(RedistributionRecommendation, rec_id)
    if not r:
        raise HTTPException(404)
    r.status = "REJECTED"
    db.commit()
    return {"status": "REJECTED", "id": rec_id}
