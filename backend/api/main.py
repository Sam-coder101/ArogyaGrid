"""
ArogyaGrid — FastAPI Application Entry Point
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import config
from data.database import init_db
from api.routes import demo, stock, alerts, forecast, redistribution, prescription, dashboard

app = FastAPI(
    title="ArogyaGrid API",
    description="Federated AI Platform for National PHC Resource Intelligence",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount poster images directory
posters_dir = Path(__file__).resolve().parent.parent.parent / "data" / "posters"
posters_dir.mkdir(parents=True, exist_ok=True)
app.mount("/posters", StaticFiles(directory=str(posters_dir)), name="posters")

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "ArogyaGrid API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }

app.include_router(demo.router,           prefix="/api/demo",           tags=["Demo"])
app.include_router(stock.router,          prefix="/api/stock",          tags=["Stock"])
app.include_router(alerts.router,         prefix="/api/alerts",         tags=["Alerts"])
app.include_router(forecast.router,       prefix="/api/forecast",       tags=["Forecast"])
app.include_router(redistribution.router, prefix="/api/redistribution", tags=["Redistribution"])
app.include_router(prescription.router,   prefix="/api/prescription",   tags=["Prescription"])
app.include_router(dashboard.router,      prefix="/api/dashboard",      tags=["Dashboard"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
