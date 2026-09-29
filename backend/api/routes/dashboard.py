"""
ArogyaGrid — Dashboard Data Routes
GET /api/dashboard/summary     — high-level KPIs for the dashboard
GET /api/dashboard/map-data    — PHC positions + status for map view
GET /api/dashboard/epi-signals — recent epidemiological signals
GET /api/dashboard/posters     — list generated awareness posters
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from data.database import get_db
from data.models import (
    PHC, Alert, RedistributionRecommendation,
    ForecastResult, DiseaseSignal, AwarenessPoster, InventoryItem, Medicine
)

router = APIRouter()


@router.get("/summary")
def get_summary(state: Optional[str] = None, db: Session = Depends(get_db)):
    phc_q     = db.query(PHC)
    alert_q   = db.query(Alert).filter(Alert.status == "OPEN")
    redist_q  = db.query(RedistributionRecommendation).filter(RedistributionRecommendation.status == "PENDING")
    signal_q  = db.query(DiseaseSignal)
    forecast_q = db.query(ForecastResult)

    if state:
        phc_ids = [p.id for p in phc_q.filter(PHC.state == state).all()]
        alert_q  = alert_q.filter(Alert.phc_id.in_(phc_ids))
        redist_q = redist_q.filter(RedistributionRecommendation.to_phc_id.in_(phc_ids))
        signal_q = signal_q.filter(DiseaseSignal.state == state)

    high_alerts   = alert_q.filter(Alert.severity == "HIGH").count()
    medium_alerts = alert_q.filter(Alert.severity == "MEDIUM").count()

    return {
        "total_phcs": phc_q.count(),
        "open_alerts": alert_q.count(),
        "high_severity_alerts": high_alerts,
        "medium_severity_alerts": medium_alerts,
        "pending_redistributions": redist_q.count(),
        "disease_signals": signal_q.count(),
        "forecasts_generated": forecast_q.count(),
        "posters_generated": db.query(AwarenessPoster).count(),
    }


@router.get("/map-data")
def get_map_data(state: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PHC)
    if state:
        q = q.filter(PHC.state == state)
    phcs = q.all()

    result = []
    for phc in phcs:
        open_alerts = db.query(Alert).filter(
            Alert.phc_id == phc.id, Alert.status == "OPEN"
        ).count()
        high_alerts = db.query(Alert).filter(
            Alert.phc_id == phc.id, Alert.severity == "HIGH", Alert.status == "OPEN"
        ).count()

        status = "ok"
        if high_alerts > 0:
            status = "critical"
        elif open_alerts > 0:
            status = "warning"

        result.append({
            "id": phc.id,
            "name": phc.name,
            "district": phc.district,
            "state": phc.state,
            "latitude": phc.latitude,
            "longitude": phc.longitude,
            "category": phc.category,
            "status": status,
            "open_alerts": open_alerts,
        })
    return result


@router.get("/epi-signals")
def get_epi_signals(db: Session = Depends(get_db), limit: int = 20):
    signals = (
        db.query(DiseaseSignal)
        .order_by(DiseaseSignal.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "geo_block": s.geo_block,
            "state": s.state,
            "district": s.district,
            "disease_hypothesis": s.disease_hypothesis,
            "confidence": s.confidence,
            "trend": s.trend,
            "contributing_case_count": s.contributing_case_count,
            "alert_threshold_crossed": s.alert_threshold_crossed,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in signals
    ]


@router.get("/posters")
def get_posters(db: Session = Depends(get_db), limit: int = 10):
    posters = (
        db.query(AwarenessPoster)
        .order_by(AwarenessPoster.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": p.id,
            "disease_signal_id": p.disease_signal_id,
            "language": p.language,
            "geo_target": p.geo_target,
            "caption_text": p.caption_text,
            "image_url": p.image_url,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in posters
    ]
