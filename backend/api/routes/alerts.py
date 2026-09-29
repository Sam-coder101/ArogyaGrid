"""
ArogyaGrid — Alert Routes
GET  /api/alerts/          — list all open alerts
GET  /api/alerts/{id}      — get single alert
POST /api/alerts/{id}/ack  — acknowledge alert
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from data.database import get_db
from data.models import Alert, PHC, Medicine

router = APIRouter()


@router.get("/")
def list_alerts(
    state: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = "OPEN",
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    alerts = q.order_by(Alert.created_at.desc()).limit(100).all()

    result = []
    for a in alerts:
        phc  = db.get(PHC, a.phc_id)
        med  = db.get(Medicine, a.drug_id) if a.drug_id else None
        if state and phc and phc.state != state:
            continue
        result.append({
            "id": a.id,
            "alert_type": a.alert_type,
            "phc_id": a.phc_id,
            "phc_name": phc.name if phc else a.phc_id,
            "district": phc.district if phc else None,
            "state": phc.state if phc else None,
            "drug_id": a.drug_id,
            "drug_name": med.generic_name if med else a.drug_id,
            "severity": a.severity,
            "predicted_date": a.predicted_date.isoformat() if a.predicted_date else None,
            "confidence": a.confidence,
            "status": a.status,
            "recommended_action": a.recommended_action,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })
    return result


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, f"Alert {alert_id} not found")
    phc = db.get(PHC, a.phc_id)
    med = db.get(Medicine, a.drug_id) if a.drug_id else None
    return {
        "id": a.id,
        "alert_type": a.alert_type,
        "phc_id": a.phc_id,
        "phc_name": phc.name if phc else a.phc_id,
        "drug_name": med.generic_name if med else a.drug_id,
        "severity": a.severity,
        "predicted_date": a.predicted_date.isoformat() if a.predicted_date else None,
        "recommended_action": a.recommended_action,
        "status": a.status,
    }


@router.post("/{alert_id}/ack")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, f"Alert {alert_id} not found")
    a.status = "ACKNOWLEDGED"
    db.commit()
    return {"status": "acknowledged", "alert_id": alert_id}
