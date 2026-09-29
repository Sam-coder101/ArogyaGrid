"""
ArogyaGrid — Epidemiological Signal Agent
==========================================
Agent inputs:  recent PrescriptionEvent records (de-identified, consented)
Agent tools:   aggregate_events (BigQuery/SQLite), k_anonymity_check,
               pattern_match (rule-based disease signatures),
               spike_detect (rate-of-change vs. baseline)
Agent output:  DiseaseSignal list

Privacy guardrails:
- k-anonymity check: no signal emitted if cohort < MIN_COHORT_SIZE
- Only drug-class + block-level geo + time bucket exposed, never patient IDs
- Cloud DLP de-identification is assumed upstream (real GCP) / simulated here
"""
from datetime import datetime, timedelta
from typing import List, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func
from data.models import PrescriptionEvent, DiseaseSignal, Medicine
from providers.gemini_provider import generate_text

MIN_COHORT_SIZE = 5  # k-anonymity floor: minimum events per geo-block signal

# Disease pattern rules: drug class combinations → disease hypothesis
DISEASE_PATTERNS = [
    {
        "hypothesis": "dengue-consistent pattern",
        "trigger_classes": ["Analgesic / Antipyretic", "Antihistamine — H1 blocker", "Rehydration Salt"],
        "min_classes": 2,
        "season_months": {7, 8, 9, 10, 11},
    },
    {
        "hypothesis": "malaria-consistent pattern",
        "trigger_classes": ["Antimalarial — 4-aminoquinoline", "Antimalarial — ACT (Artemisinin Combination Therapy)", "Analgesic / Antipyretic"],
        "min_classes": 2,
        "season_months": {7, 8, 9, 10},
    },
    {
        "hypothesis": "acute gastroenteritis / diarrhoeal outbreak pattern",
        "trigger_classes": ["Rehydration Salt", "Antibiotic / Antiprotozoal — Nitroimidazole", "Micronutrient / Antidiarrhoeal adjunct"],
        "min_classes": 2,
        "season_months": None,   # year-round
    },
    {
        "hypothesis": "respiratory illness / viral fever pattern",
        "trigger_classes": ["Analgesic / Antipyretic", "Antibiotic — Aminopenicillin", "H2 Receptor Antagonist — GI acid reducer"],
        "min_classes": 2,
        "season_months": {11, 12, 1, 2},
    },
]


# ── Tool: aggregate_events ────────────────────────────────────────────────────
def tool_aggregate_events(db: Session, days_back: int = 14) -> List[dict]:
    """
    Aggregates recent prescription events by geo_block × drug_class × time bucket.
    STUB → BigQuery aggregation query at scale.
    Returns list of {geo_block, state, district, drug_class, event_count, dates}.
    """
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    events = (
        db.query(PrescriptionEvent)
        .filter(
            PrescriptionEvent.timestamp >= cutoff,
            PrescriptionEvent.consented == True,
        )
        .all()
    )

    # Group by geo_block
    geo_groups: dict = {}
    for evt in events:
        key = (evt.geo_block or "unknown", evt.state or "", evt.district or "")
        if key not in geo_groups:
            geo_groups[key] = {"drug_ids": [], "count": 0, "dates": []}
        geo_groups[key]["drug_ids"].extend(evt.drug_ids or [])
        geo_groups[key]["count"] += 1
        geo_groups[key]["dates"].append(evt.timestamp)

    # Resolve drug classes
    aggregated = []
    for (geo_block, state, district), data in geo_groups.items():
        drug_classes = set()
        for drug_id in data["drug_ids"]:
            med = db.get(Medicine, drug_id)
            if med:
                drug_classes.add(med.therapeutic_class)
        aggregated.append({
            "geo_block": geo_block,
            "state": state,
            "district": district,
            "drug_classes": list(drug_classes),
            "event_count": data["count"],
            "drug_ids": list(set(data["drug_ids"])),
        })

    return aggregated


# ── Tool: k_anonymity_check ───────────────────────────────────────────────────
def tool_k_anonymity_check(event_count: int) -> bool:
    """Returns True if the cohort meets the minimum k-anonymity threshold."""
    return event_count >= MIN_COHORT_SIZE


# ── Tool: pattern_match ───────────────────────────────────────────────────────
def tool_pattern_match(drug_classes: List[str]) -> Optional[dict]:
    """
    Rule-based pattern matching against known disease signatures.
    Returns the best-matching disease pattern or None.
    """
    current_month = datetime.utcnow().month
    best_match = None
    best_score = 0

    for pattern in DISEASE_PATTERNS:
        # Check season
        if pattern["season_months"] and current_month not in pattern["season_months"]:
            continue

        # Count matching drug classes
        matches = sum(1 for tc in pattern["trigger_classes"] if tc in drug_classes)
        if matches >= pattern["min_classes"] and matches > best_score:
            best_score = matches
            best_match = {**pattern, "matched_classes": matches}

    return best_match


# ── Tool: spike_detect ────────────────────────────────────────────────────────
def tool_spike_detect(
    db: Session, geo_block: str, current_count: int, days_back: int = 14
) -> dict:
    """
    Compares current event rate vs. 30-day rolling baseline.
    Returns {trend, rate_of_change_pct, is_spike}.
    """
    # Rolling baseline: 30-day window ending 14 days ago
    cutoff_end   = datetime.utcnow() - timedelta(days=days_back)
    cutoff_start = cutoff_end - timedelta(days=30)

    baseline_count = (
        db.query(func.count(PrescriptionEvent.id))
        .filter(
            PrescriptionEvent.geo_block == geo_block,
            PrescriptionEvent.timestamp >= cutoff_start,
            PrescriptionEvent.timestamp < cutoff_end,
            PrescriptionEvent.consented == True,
        )
        .scalar()
    ) or 0

    if baseline_count == 0:
        return {"trend": "UNKNOWN", "rate_of_change_pct": 0.0, "is_spike": False}

    # Normalise: current_count is for `days_back` days, baseline is for 30 days
    normalised_current  = current_count  / days_back
    normalised_baseline = baseline_count / 30

    rate_of_change = (normalised_current - normalised_baseline) / max(normalised_baseline, 0.01) * 100

    if rate_of_change > 40:
        trend = "RISING"
        is_spike = True
    elif rate_of_change > 10:
        trend = "RISING"
        is_spike = False
    elif rate_of_change < -20:
        trend = "FALLING"
        is_spike = False
    else:
        trend = "STABLE"
        is_spike = False

    return {
        "trend": trend,
        "rate_of_change_pct": round(rate_of_change, 1),
        "is_spike": is_spike,
    }


# ── Main Agent Function ───────────────────────────────────────────────────────
def run(db: Session, days_back: int = 14) -> List[dict]:
    """
    Epidemiological Signal Agent — main entry point.
    Returns a list of DiseaseSignal dicts (only those passing k-anonymity).
    """
    # Tool 1: Aggregate events by geo_block
    aggregated = tool_aggregate_events(db, days_back)

    signals = []
    for block_data in aggregated:
        # Tool 2: k-anonymity check — skip if cohort too small
        if not tool_k_anonymity_check(block_data["event_count"]):
            continue

        # Tool 3: Pattern match
        pattern = tool_pattern_match(block_data["drug_classes"])
        if not pattern:
            continue

        # Tool 4: Spike detection
        spike = tool_spike_detect(db, block_data["geo_block"], block_data["event_count"], days_back)

        confidence = min(0.95, 0.5 + block_data["event_count"] * 0.04 + (0.1 if spike["is_spike"] else 0))
        alert_threshold = spike["is_spike"] and pattern["matched_classes"] >= 2

        signal = DiseaseSignal(
            geo_block=block_data["geo_block"],
            state=block_data["state"],
            district=block_data["district"],
            disease_hypothesis=pattern["hypothesis"],
            confidence=round(confidence, 2),
            trend=spike["trend"],
            contributing_case_count=block_data["event_count"],
            alert_threshold_crossed=alert_threshold,
            created_at=datetime.utcnow(),
        )
        db.add(signal)
        db.flush()

        signals.append({
            "id": signal.id,
            "geo_block": block_data["geo_block"],
            "state": block_data["state"],
            "district": block_data["district"],
            "disease_hypothesis": pattern["hypothesis"],
            "confidence": signal.confidence,
            "trend": spike["trend"],
            "rate_of_change_pct": spike["rate_of_change_pct"],
            "contributing_case_count": block_data["event_count"],
            "alert_threshold_crossed": alert_threshold,
            "matched_drug_classes": block_data["drug_classes"],
            "agent": "EpidemiologicalSignalAgent",
        })

    return signals
