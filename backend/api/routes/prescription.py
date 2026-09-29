"""
ArogyaGrid — Prescription Explainer Routes
POST /api/prescription/explain   — upload image, get explanation
GET  /api/prescription/medicines — list medicine catalog
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from data.database import get_db
from data.models import Medicine
import agents.prescription_explainer as prescription_agent

router = APIRouter()


@router.post("/explain")
async def explain_prescription(
    file: UploadFile = File(...),
    language: str = Form("en"),
    db: Session = Depends(get_db),
):
    """
    Upload a prescription image and get a plain-language explanation.
    Supports: image/jpeg, image/png, image/webp
    """
    image_bytes = await file.read()
    mime_type   = file.content_type or "image/jpeg"

    result = prescription_agent.run(db, image_bytes, mime_type, language)
    db.commit()
    return result


@router.get("/medicines")
def list_medicines(
    therapeutic_class: Optional[str] = None,
    essential_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Medicine)
    if therapeutic_class:
        q = q.filter(Medicine.therapeutic_class.ilike(f"%{therapeutic_class}%"))
    if essential_only:
        q = q.filter(Medicine.essential_drug_flag == True)
    meds = q.all()
    return [
        {
            "drug_id": m.drug_id,
            "generic_name": m.generic_name,
            "molecule_composition": m.molecule_composition,
            "therapeutic_class": m.therapeutic_class,
            "manufacturer": m.manufacturer,
            "essential": m.essential_drug_flag,
            "dosage_form": m.dosage_form,
            "side_effects": m.side_effects,
            "typical_indication": m.typical_indication,
        }
        for m in meds
    ]
