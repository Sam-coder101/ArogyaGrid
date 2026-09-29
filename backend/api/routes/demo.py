"""
ArogyaGrid — Demo Routes
POST /api/demo/run-full-loop   — triggers the orchestrator full demo loop via SSE
POST /api/demo/seed            — (re)seeds the database
GET  /api/demo/status          — checks DB + provider status
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from data.database import get_db, init_db
from data.seed import seed
import agents.orchestrator as orchestrator
import config

router = APIRouter()


def _sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/run-full-loop")
async def run_full_demo_loop(db: Session = Depends(get_db)):
    """Triggers the full ArogyaGrid demo loop via Server-Sent Events."""
    def event_stream():
        try:
            for event in orchestrator.run_full_demo_loop(db):
                yield _sse_event(event)
            db.commit()
        except Exception as e:
            db.rollback()
            yield _sse_event({"event": "error", "message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/seed")
async def seed_database(db: Session = Depends(get_db)):
    """Seeds (or re-seeds) the synthetic dataset."""
    try:
        init_db()
        seed(db)
        db.commit()
        return {"status": "success", "message": "Database seeded with synthetic ArogyaGrid data."}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Returns system status: DB record counts and provider configuration."""
    from data.models import PHC, Medicine, InventoryItem, Alert, DispensationHistory
    return {
        "database": {
            "phcs": db.query(PHC).count(),
            "medicines": db.query(Medicine).count(),
            "inventory_items": db.query(InventoryItem).count(),
            "alerts": db.query(Alert).count(),
            "dispensation_records": db.query(DispensationHistory).count(),
        },
        "providers": {
            "gemini": "REAL" if (config.GOOGLE_API_KEY and config.USE_REAL_GEMINI) else "STUB",
            "forecast": "REAL" if config.USE_REAL_FORECAST else "STUB (local heuristic)",
            "ocr": "REAL" if config.USE_REAL_OCR else "STUB (Gemini multimodal)",
            "imagen": "REAL" if config.USE_REAL_IMAGEN else "STUB (Pillow render)",
            "translation": "REAL" if config.USE_REAL_TRANSLATE else "STUB (Gemini translation)",
        },
        "gemini_model": config.GEMINI_MODEL,
    }
