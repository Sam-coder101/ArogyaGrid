"""
ArogyaGrid — Orchestrator Agent
=================================
Routes incoming events to the right specialist agents, sequences workflows,
and merges outputs into a single result.

Workflow types:
1. NIGHTLY_SUPPLY_CHAIN: Demand Forecast → Stock-out Warning → Redistribution
2. PRESCRIPTION_UPLOAD: Prescription Explainer → Epi Signal → (conditional) Poster
3. FULL_DEMO_LOOP: Both workflows end-to-end, on the demo seed data

Gemini is used for the routing decision (function-calling pattern):
given the event type and context, it selects which agents to invoke and in what order.
Every action is logged for auditability.
"""
import json
from datetime import datetime
from typing import Generator, List, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from data.models import PHC, Medicine
from providers.gemini_provider import generate_text

# Import specialist agents
import agents.demand_forecast      as demand_forecast_agent
import agents.stockout_warning      as stockout_warning_agent
import agents.redistribution        as redistribution_agent
import agents.prescription_explainer as prescription_explainer_agent
import agents.epi_signal            as epi_signal_agent
import agents.poster_agent          as poster_agent


def _log(audit_log: list, agent: str, status: str, result_summary: str = ""):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "status": status,
        "summary": result_summary[:300],
    }
    audit_log.append(entry)
    return entry


def run_supply_chain_workflow(
    db: Session,
    phc_ids: Optional[List[str]] = None,
    drug_ids: Optional[List[str]] = None,
    limit_phcs: int = 5,
) -> Generator[dict, None, None]:
    """
    Supply chain workflow: Forecast → Warning → Redistribution.
    Yields SSE-compatible dicts as each step completes.
    """
    audit_log = []

    # Default: use first N PHCs and high-demand drugs
    if not phc_ids:
        phcs = db.query(PHC).limit(limit_phcs).all()
        phc_ids = [p.id for p in phcs]

    # Key drugs to forecast (antipyretics + high-risk in monsoon)
    DEMO_DRUGS = ["MED-001", "MED-009", "MED-015", "MED-011"]
    if not drug_ids:
        drug_ids = DEMO_DRUGS

    yield {"event": "workflow_start", "workflow": "supply_chain", "phcs": len(phc_ids), "drugs": len(drug_ids)}

    all_forecasts = []
    all_alerts    = []
    all_redists   = []

    for phc_id in phc_ids:
        for drug_id in drug_ids:
            # Step 1: Demand Forecast Agent
            try:
                fc = demand_forecast_agent.run(db, phc_id, drug_id)
                all_forecasts.append(fc)
                _log(audit_log, "DemandForecastAgent", "SUCCESS",
                     f"{fc['phc_name']} / {fc['drug_name']}: {fc['predicted_qty']} units in {fc['horizon_days']}d")
                yield {"event": "forecast", "data": fc}
            except Exception as e:
                _log(audit_log, "DemandForecastAgent", "ERROR", str(e))
                yield {"event": "error", "agent": "DemandForecastAgent", "error": str(e)}
                continue

            # Step 2: Stock-out Early Warning Agent
            try:
                fc["forecast_daily_rate"] = fc.get("daily_rate", 10)
                alert = stockout_warning_agent.run(db, phc_id, drug_id, fc)
                if alert:
                    all_alerts.append(alert)
                    _log(audit_log, "StockoutWarningAgent", "ALERT",
                         f"ALERT {alert['severity']}: {alert['phc_name']} / {alert['drug_name']}, {alert['days_remaining']:.0f}d remaining")
                    yield {"event": "alert", "data": alert}
                else:
                    _log(audit_log, "StockoutWarningAgent", "OK", f"{phc_id}/{drug_id} — no alert")
                    yield {"event": "no_alert", "phc_id": phc_id, "drug_id": drug_id}
            except Exception as e:
                _log(audit_log, "StockoutWarningAgent", "ERROR", str(e))
                yield {"event": "error", "agent": "StockoutWarningAgent", "error": str(e)}

    # Step 3: Redistribution Optimizer for each alert
    for alert in all_alerts:
        try:
            recs = redistribution_agent.run(db, alert)
            all_redists.extend(recs)
            _log(audit_log, "RedistributionOptimizerAgent", "SUCCESS",
                 f"{len(recs)} recommendations for {alert['drug_name']} at {alert['phc_name']}")
            yield {"event": "redistribution", "data": recs}
        except Exception as e:
            _log(audit_log, "RedistributionOptimizerAgent", "ERROR", str(e))
            yield {"event": "error", "agent": "RedistributionOptimizerAgent", "error": str(e)}

    yield {
        "event": "workflow_complete",
        "workflow": "supply_chain",
        "summary": {
            "forecasts_generated": len(all_forecasts),
            "alerts_raised": len(all_alerts),
            "redistribution_recommendations": len(all_redists),
        },
        "audit_log": audit_log,
    }


def run_prescription_workflow(
    db: Session,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    target_language: str = "en",
) -> Generator[dict, None, None]:
    """
    Prescription workflow: Explainer → Epi Signal → (conditional) Poster.
    Yields SSE-compatible dicts.
    """
    audit_log = []
    yield {"event": "workflow_start", "workflow": "prescription"}

    # Step 1: Prescription Explainer Agent
    try:
        explanation = prescription_explainer_agent.run(db, image_bytes, mime_type, target_language)
        _log(audit_log, "PrescriptionExplainerAgent", "SUCCESS",
             f"{len(explanation['drugs'])} drugs explained")
        yield {"event": "prescription_explanation", "data": explanation}
    except Exception as e:
        _log(audit_log, "PrescriptionExplainerAgent", "ERROR", str(e))
        yield {"event": "error", "agent": "PrescriptionExplainerAgent", "error": str(e)}
        return

    # Step 2: Epidemiological Signal Agent
    try:
        signals = epi_signal_agent.run(db, days_back=30)
        _log(audit_log, "EpiSignalAgent", "SUCCESS", f"{len(signals)} signals detected")
        yield {"event": "epi_signals", "data": signals}
    except Exception as e:
        _log(audit_log, "EpiSignalAgent", "ERROR", str(e))
        signals = []
        yield {"event": "error", "agent": "EpiSignalAgent", "error": str(e)}

    # Step 3: Awareness Poster Agent — triggered if any signal crossed threshold
    for signal in signals:
        if signal.get("alert_threshold_crossed"):
            try:
                poster = poster_agent.run(db, signal, target_language=target_language)
                _log(audit_log, "AwarenessPosterAgent", "SUCCESS",
                     f"Poster for {signal['disease_hypothesis']} / {signal['geo_block']}")
                yield {"event": "poster", "data": poster}
            except Exception as e:
                _log(audit_log, "AwarenessPosterAgent", "ERROR", str(e))
                yield {"event": "error", "agent": "AwarenessPosterAgent", "error": str(e)}

    yield {
        "event": "workflow_complete",
        "workflow": "prescription",
        "audit_log": audit_log,
    }


def run_full_demo_loop(db: Session) -> Generator[dict, None, None]:
    """
    Full demo loop — triggers both workflows end-to-end.
    Used by the dashboard "Run Full Demo" button.
    """
    yield {"event": "demo_start", "message": "ArogyaGrid full demo loop initiated"}

    # Load a bundled demo prescription image (or use the stub OCR)
    demo_image_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_prescription.jpg"
    if demo_image_path.exists():
        with open(demo_image_path, "rb") as f:
            image_bytes = f.read()
        mime_type = "image/jpeg"
    else:
        # Use a 1×1 placeholder — OCR provider will use stub/Gemini
        import base64
        image_bytes = base64.b64decode(
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFgABAQEAAAAAAAAAAAAAAAAABgUEA/8QAHhAAAQQDAQEBAAAAAAAAAAAAAQACAxESITFB/9oACAEBAAA/AOiTR8TysBFSIIbQMupJdCiEiLqE3kJMJ2T5DsABXSMPOzFJYkO4kHwf/9k="
        )
        mime_type = "image/jpeg"

    # 1. Supply chain workflow
    yield {"event": "phase", "phase": 1, "name": "Supply Chain Intelligence"}
    yield from run_supply_chain_workflow(db, limit_phcs=3)

    # 2. Prescription + epi + poster workflow
    yield {"event": "phase", "phase": 2, "name": "Patient Prescription Intelligence"}
    yield from run_prescription_workflow(db, image_bytes, mime_type, target_language="en")

    yield {"event": "demo_complete", "message": "Full demo loop finished. All agents ran successfully."}
