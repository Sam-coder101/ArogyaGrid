"""
ArogyaGrid — Stock Routes
GET  /api/stock/phcs              — list all PHCs
GET  /api/stock/{phc_id}          — PHC stock summary
GET  /api/stock/{phc_id}/beds     — bed status
GET  /api/stock/{phc_id}/staff    — staff attendance
POST /api/stock/{phc_id}/update   — update stock level (PHC pharmacist PWA)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from data.database import get_db
from data.models import PHC, InventoryItem, BedStatus, StaffAttendance, Medicine

router = APIRouter()


@router.get("/phcs")
def list_phcs(state: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(PHC)
    if state:
        q = q.filter(PHC.state == state)
    phcs = q.all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "district": p.district,
            "state": p.state,
            "category": p.category,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "population_covered": p.population_covered,
        }
        for p in phcs
    ]


@router.get("/{phc_id}")
def get_phc_stock(phc_id: str, db: Session = Depends(get_db)):
    phc = db.get(PHC, phc_id)
    if not phc:
        raise HTTPException(404, f"PHC {phc_id} not found")

    items = (
        db.query(InventoryItem)
        .filter(InventoryItem.phc_id == phc_id)
        .all()
    )
    inventory = []
    for item in items:
        med = db.get(Medicine, item.drug_id)
        inventory.append({
            "drug_id": item.drug_id,
            "drug_name": med.generic_name if med else item.drug_id,
            "therapeutic_class": med.therapeutic_class if med else None,
            "quantity": item.quantity,
            "unit": item.unit,
            "essential": med.essential_drug_flag if med else None,
            "last_updated": item.last_updated.isoformat() if item.last_updated else None,
        })

    return {
        "phc_id": phc_id,
        "phc_name": phc.name,
        "district": phc.district,
        "state": phc.state,
        "category": phc.category,
        "inventory": inventory,
    }


@router.get("/{phc_id}/beds")
def get_bed_status(phc_id: str, db: Session = Depends(get_db)):
    beds = db.query(BedStatus).filter(BedStatus.phc_id == phc_id).all()
    return [
        {
            "ward_type": b.ward_type,
            "total": b.total,
            "occupied": b.occupied,
            "available": b.total - b.occupied,
            "occupancy_pct": round(b.occupied / b.total * 100, 1) if b.total else 0,
            "timestamp": b.timestamp.isoformat() if b.timestamp else None,
        }
        for b in beds
    ]


@router.get("/{phc_id}/staff")
def get_staff(phc_id: str, db: Session = Depends(get_db)):
    staff = db.query(StaffAttendance).filter(StaffAttendance.phc_id == phc_id).all()
    return [
        {
            "role": s.role,
            "present": s.present_count,
            "sanctioned": s.sanctioned_count,
            "attendance_pct": round(s.present_count / s.sanctioned_count * 100, 1) if s.sanctioned_count else 0,
        }
        for s in staff
    ]


class StockUpdateRequest(BaseModel):
    drug_id: str
    quantity: int
    batch: Optional[str] = None


@router.post("/{phc_id}/update")
def update_stock(phc_id: str, req: StockUpdateRequest, db: Session = Depends(get_db)):
    item = (
        db.query(InventoryItem)
        .filter(InventoryItem.phc_id == phc_id, InventoryItem.drug_id == req.drug_id)
        .first()
    )
    if item:
        item.quantity    = req.quantity
        item.last_updated = datetime.utcnow()
        if req.batch:
            item.batch = req.batch
    else:
        item = InventoryItem(
            phc_id=phc_id, drug_id=req.drug_id,
            quantity=req.quantity, batch=req.batch,
            last_updated=datetime.utcnow()
        )
        db.add(item)
    db.commit()
    return {"status": "updated", "phc_id": phc_id, "drug_id": req.drug_id, "quantity": req.quantity}
