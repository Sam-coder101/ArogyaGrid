"""
ArogyaGrid Data Models
======================
SQLAlchemy ORM models that exactly match the data model in architecture.md §4.
These are the single source of truth for the database schema.
All entities are FHIR-aligned (see architecture.md §4 comments).
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PHC(Base):
    """Primary Health Centre — FHIR Organization resource."""
    __tablename__ = "phc"

    id          = Column(String, primary_key=True)   # e.g. "MH-PUN-001"
    name        = Column(String, nullable=False)
    district    = Column(String, nullable=False)
    state       = Column(String, nullable=False)
    latitude    = Column(Float)
    longitude   = Column(Float)
    category    = Column(String)                     # Type A / B / C
    population_covered = Column(Integer)

    inventory   = relationship("InventoryItem", back_populates="phc")
    bed_status  = relationship("BedStatus",     back_populates="phc")
    staff       = relationship("StaffAttendance", back_populates="phc")
    alerts      = relationship("Alert",          back_populates="phc")


class Medicine(Base):
    """Drug / medicine reference — FHIR Medication resource."""
    __tablename__ = "medicine"

    drug_id           = Column(String, primary_key=True)   # e.g. "MED-0001"
    generic_name      = Column(String, nullable=False)
    brand_names       = Column(JSON)                       # list of strings
    molecule_composition = Column(String)
    therapeutic_class = Column(String)
    manufacturer      = Column(String)
    essential_drug_flag = Column(Boolean, default=True)
    dosage_form       = Column(String)                     # Tablet / Syrup / Injection
    unit              = Column(String)                     # strips / vials / bottles
    side_effects      = Column(JSON)                       # list of strings
    common_alternatives = Column(JSON)                     # list of drug_ids
    typical_indication  = Column(String)                   # plain-language "why prescribed"
    restock_lead_days   = Column(Integer, default=7)       # supply lead time

    inventory = relationship("InventoryItem", back_populates="medicine")


class InventoryItem(Base):
    """Current stock level at a PHC — FHIR SupplyDelivery resource."""
    __tablename__ = "inventory_item"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    phc_id       = Column(String, ForeignKey("phc.id"), nullable=False)
    drug_id      = Column(String, ForeignKey("medicine.drug_id"), nullable=False)
    batch        = Column(String)
    quantity     = Column(Integer, nullable=False, default=0)
    unit         = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_date  = Column(DateTime, nullable=True)

    phc      = relationship("PHC",      back_populates="inventory")
    medicine = relationship("Medicine", back_populates="inventory")


class BedStatus(Base):
    """Bed occupancy snapshot — FHIR Location resource."""
    __tablename__ = "bed_status"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    phc_id    = Column(String, ForeignKey("phc.id"), nullable=False)
    ward_type = Column(String)    # General / Maternity / Emergency
    total     = Column(Integer)
    occupied  = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    phc = relationship("PHC", back_populates="bed_status")


class StaffAttendance(Base):
    """Staff attendance record — FHIR Practitioner resource."""
    __tablename__ = "staff_attendance"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    phc_id          = Column(String, ForeignKey("phc.id"), nullable=False)
    role            = Column(String)    # Doctor / Nurse / Pharmacist / ANM
    present_count   = Column(Integer)
    sanctioned_count = Column(Integer)
    timestamp       = Column(DateTime, default=datetime.utcnow)

    phc = relationship("PHC", back_populates="staff")


class PrescriptionEvent(Base):
    """De-identified prescription event — feeds Epidemiological Signal Agent."""
    __tablename__ = "prescription_event"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    anonymized_patient_hash = Column(String)
    phc_id                = Column(String, ForeignKey("phc.id"))
    drug_ids              = Column(JSON)      # list of drug_ids
    diagnosis_class       = Column(String)    # optional
    geo_block             = Column(String)    # block-level geography
    state                 = Column(String)
    district              = Column(String)
    timestamp             = Column(DateTime, default=datetime.utcnow)
    consented             = Column(Boolean, default=True)


class DispensationHistory(Base):
    """Historical stock dispensation — feeds Demand Forecast Agent."""
    __tablename__ = "dispensation_history"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    phc_id       = Column(String, ForeignKey("phc.id"), nullable=False)
    drug_id      = Column(String, ForeignKey("medicine.drug_id"), nullable=False)
    qty_dispensed = Column(Integer, nullable=False)
    date         = Column(DateTime, nullable=False)
    month        = Column(Integer)
    is_monsoon   = Column(Boolean, default=False)   # seasonal feature


class Alert(Base):
    """Stock-out / bed / staff alert — raised by Early Warning Agent."""
    __tablename__ = "alert"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    alert_type          = Column(String)    # stock-out / bed / staff
    phc_id              = Column(String, ForeignKey("phc.id"), nullable=False)
    drug_id             = Column(String, ForeignKey("medicine.drug_id"), nullable=True)
    predicted_date      = Column(DateTime)
    confidence          = Column(Float)
    severity            = Column(String)    # HIGH / MEDIUM / LOW
    status              = Column(String, default="OPEN")   # OPEN / ACKNOWLEDGED / RESOLVED
    recommended_action  = Column(Text)
    created_at          = Column(DateTime, default=datetime.utcnow)

    phc = relationship("PHC", back_populates="alerts")


class RedistributionRecommendation(Base):
    """Cross-district redistribution suggestion — raised by Redistribution Agent."""
    __tablename__ = "redistribution_recommendation"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    from_phc_id  = Column(String, ForeignKey("phc.id"), nullable=False)
    to_phc_id    = Column(String, ForeignKey("phc.id"), nullable=False)
    drug_id      = Column(String, ForeignKey("medicine.drug_id"), nullable=False)
    qty          = Column(Integer)
    distance_km  = Column(Float)
    rationale    = Column(Text)
    status       = Column(String, default="PENDING")   # PENDING / APPROVED / REJECTED
    created_at   = Column(DateTime, default=datetime.utcnow)


class ForecastResult(Base):
    """Demand forecast output — produced by Demand Forecast Agent."""
    __tablename__ = "forecast_result"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    phc_id         = Column(String, ForeignKey("phc.id"), nullable=False)
    drug_id        = Column(String, ForeignKey("medicine.drug_id"), nullable=False)
    forecast_date  = Column(DateTime)           # when the forecast was generated
    horizon_days   = Column(Integer)             # how many days ahead
    predicted_qty  = Column(Integer)
    confidence     = Column(Float)
    explanation    = Column(Text)               # Gemini plain-language annotation
    created_at     = Column(DateTime, default=datetime.utcnow)


class DiseaseSignal(Base):
    """Epidemiological signal — produced by Epi Signal Agent."""
    __tablename__ = "disease_signal"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    geo_block           = Column(String)
    state               = Column(String)
    district            = Column(String)
    disease_hypothesis  = Column(String)    # e.g. "dengue-consistent pattern"
    confidence          = Column(Float)
    trend               = Column(String)    # RISING / STABLE / FALLING
    contributing_case_count = Column(Integer)
    alert_threshold_crossed = Column(Boolean, default=False)
    created_at          = Column(DateTime, default=datetime.utcnow)


class AwarenessPoster(Base):
    """Awareness poster output — produced by Poster Agent."""
    __tablename__ = "awareness_poster"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    disease_signal_id = Column(Integer, ForeignKey("disease_signal.id"))
    language         = Column(String)
    geo_target       = Column(String)
    image_url        = Column(String)    # path or URL to poster image
    caption_text     = Column(Text)
    fact_template_used = Column(String)
    created_at       = Column(DateTime, default=datetime.utcnow)
