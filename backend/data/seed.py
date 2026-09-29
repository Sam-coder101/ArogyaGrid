"""
ArogyaGrid — Synthetic Seed Data Generator
============================================
Seeds 2 states (Maharashtra, Rajasthan), 3 districts each, 5 PHCs per district,
25 medicines across realistic therapeutic classes, 6 months of dispensation history
(with a seeded dengue spike in October for Maharashtra/Pune), and prescription events.

Run:  python backend/data/seed.py
"""
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.database import init_db, get_db_session
from data.models import (
    PHC, Medicine, InventoryItem, BedStatus, StaffAttendance,
    DispensationHistory, PrescriptionEvent, Alert, ForecastResult,
    DiseaseSignal, AwarenessPoster, RedistributionRecommendation
)

random.seed(42)

# ── Medicine Catalog ─────────────────────────────────────────────────────────
MEDICINES = [
    {
        "drug_id": "MED-001",
        "generic_name": "Paracetamol (Acetaminophen)",
        "brand_names": ["Crocin", "Dolo 650", "Calpol"],
        "molecule_composition": "Paracetamol 500 mg",
        "therapeutic_class": "Analgesic / Antipyretic",
        "manufacturer": "GSK Pharmaceuticals",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Nausea (rare)", "Liver damage (overdose)", "Skin rash (rare)"],
        "common_alternatives": ["MED-002"],
        "typical_indication": "Fever, mild to moderate pain relief. Commonly prescribed for viral fever, dengue, and post-vaccination fever.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-002",
        "generic_name": "Ibuprofen",
        "brand_names": ["Brufen", "Combiflam", "Ibugesic"],
        "molecule_composition": "Ibuprofen 400 mg",
        "therapeutic_class": "NSAID / Analgesic / Antipyretic",
        "manufacturer": "Abbott India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Gastric irritation", "Peptic ulcer risk", "Kidney stress (prolonged use)"],
        "common_alternatives": ["MED-001"],
        "typical_indication": "Pain, fever, inflammation. Often used for muscle pain, toothache, and menstrual cramps.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-003",
        "generic_name": "Amoxicillin",
        "brand_names": ["Amoxil", "Novamox", "Mox"],
        "molecule_composition": "Amoxicillin trihydrate 500 mg",
        "therapeutic_class": "Antibiotic — Aminopenicillin",
        "manufacturer": "Cipla Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Capsule",
        "unit": "strips",
        "side_effects": ["Diarrhoea", "Allergic rash (stop and consult doctor)", "Nausea"],
        "common_alternatives": ["MED-004"],
        "typical_indication": "Bacterial infections of ear, throat, chest, urinary tract. Prescribed when a bacterial cause is suspected.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-004",
        "generic_name": "Azithromycin",
        "brand_names": ["Azithral", "Zithromax", "Atm"],
        "molecule_composition": "Azithromycin dihydrate 500 mg",
        "therapeutic_class": "Antibiotic — Macrolide",
        "manufacturer": "Alembic Pharmaceuticals",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Nausea", "Abdominal pain", "Diarrhoea", "QT prolongation (rare)"],
        "common_alternatives": ["MED-003"],
        "typical_indication": "Community-acquired pneumonia, typhoid, skin infections. Used when Amoxicillin is not suitable.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-005",
        "generic_name": "Metformin",
        "brand_names": ["Glycomet", "Glucophage", "Cetapin"],
        "molecule_composition": "Metformin hydrochloride 500 mg",
        "therapeutic_class": "Antidiabetic — Biguanide",
        "manufacturer": "USV Pvt Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["GI upset (take with food)", "Lactic acidosis (very rare)", "Vitamin B12 deficiency (long-term)"],
        "common_alternatives": ["MED-006"],
        "typical_indication": "Type 2 diabetes management. First-line drug for blood sugar control.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-006",
        "generic_name": "Glibenclamide",
        "brand_names": ["Daonil", "Glynase", "Semi-Daonil"],
        "molecule_composition": "Glibenclamide 5 mg",
        "therapeutic_class": "Antidiabetic — Sulfonylurea",
        "manufacturer": "Sanofi India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Hypoglycaemia", "Weight gain", "GI disturbance"],
        "common_alternatives": ["MED-005"],
        "typical_indication": "Type 2 diabetes, used when Metformin alone is insufficient.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-007",
        "generic_name": "Amlodipine",
        "brand_names": ["Amlip", "Stamlo", "Amlopres"],
        "molecule_composition": "Amlodipine besylate 5 mg",
        "therapeutic_class": "Antihypertensive — Calcium Channel Blocker",
        "manufacturer": "Cipla Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Ankle swelling", "Flushing", "Headache"],
        "common_alternatives": ["MED-008"],
        "typical_indication": "High blood pressure and angina. Relaxes blood vessels to lower BP.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-008",
        "generic_name": "Enalapril",
        "brand_names": ["Enam", "Envas", "Enalapril"],
        "molecule_composition": "Enalapril maleate 5 mg",
        "therapeutic_class": "Antihypertensive — ACE Inhibitor",
        "manufacturer": "Cadila Healthcare",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Dry cough (common)", "Dizziness", "Hyperkalemia"],
        "common_alternatives": ["MED-007"],
        "typical_indication": "Hypertension, heart failure, diabetic nephropathy.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-009",
        "generic_name": "Oral Rehydration Salts (ORS)",
        "brand_names": ["Electral", "Pedialyte", "ORS-IP"],
        "molecule_composition": "Sodium chloride 2.6g, Potassium chloride 1.5g, Sodium citrate 2.9g, Glucose 13.5g per sachet",
        "therapeutic_class": "Rehydration Salt",
        "manufacturer": "Pharmalab India",
        "essential_drug_flag": True,
        "dosage_form": "Sachet",
        "unit": "sachets",
        "side_effects": ["Nausea if taken too fast", "Hypernatremia (excess sodium, rare)"],
        "common_alternatives": [],
        "typical_indication": "Diarrhoea and dehydration. First-line treatment for acute gastroenteritis.",
        "restock_lead_days": 3,
    },
    {
        "drug_id": "MED-010",
        "generic_name": "Zinc Sulfate",
        "brand_names": ["ZincKit", "Zincovit", "Zinctab"],
        "molecule_composition": "Zinc sulfate monohydrate 20 mg elemental zinc",
        "therapeutic_class": "Micronutrient / Antidiarrhoeal adjunct",
        "manufacturer": "Lupin Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Nausea (take with food)", "Vomiting in high doses"],
        "common_alternatives": [],
        "typical_indication": "Adjunct to ORS in childhood diarrhoea. Reduces duration and severity.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-011",
        "generic_name": "Chloroquine Phosphate",
        "brand_names": ["Lariago", "Resochin", "Malarex"],
        "molecule_composition": "Chloroquine phosphate 250 mg",
        "therapeutic_class": "Antimalarial — 4-aminoquinoline",
        "manufacturer": "IPCA Laboratories",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Nausea", "Headache", "Vision disturbance (long-term)", "Pruritus"],
        "common_alternatives": ["MED-012"],
        "typical_indication": "Malaria (P. vivax, sensitive P. falciparum). Monsoon-peak demand.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-012",
        "generic_name": "Artemether + Lumefantrine",
        "brand_names": ["Coartem", "Lumether", "AL Combo"],
        "molecule_composition": "Artemether 20 mg + Lumefantrine 120 mg",
        "therapeutic_class": "Antimalarial — ACT (Artemisinin Combination Therapy)",
        "manufacturer": "Novartis India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Headache", "Dizziness", "Nausea", "Palpitations (rare)"],
        "common_alternatives": ["MED-011"],
        "typical_indication": "Uncomplicated falciparum malaria. Preferred ACT for drug-resistant strains.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-013",
        "generic_name": "Iron + Folic Acid",
        "brand_names": ["Fersolate", "Dexorange", "Fefol"],
        "molecule_composition": "Ferrous sulphate 200 mg + Folic acid 0.5 mg",
        "therapeutic_class": "Haematinic — Iron supplement",
        "manufacturer": "Sun Pharmaceutical",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Constipation", "Dark stools (normal)", "Nausea (take with food)"],
        "common_alternatives": [],
        "typical_indication": "Iron-deficiency anaemia, pregnancy supplementation. Take on empty stomach for best absorption.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-014",
        "generic_name": "Albendazole",
        "brand_names": ["Zentel", "Bandy", "Noworm"],
        "molecule_composition": "Albendazole 400 mg",
        "therapeutic_class": "Anthelmintic — Benzimidazole",
        "manufacturer": "GSK Pharmaceuticals",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "tablets",
        "side_effects": ["Abdominal pain", "Nausea", "Dizziness", "Elevated liver enzymes (rare)"],
        "common_alternatives": [],
        "typical_indication": "Intestinal worms (roundworm, hookworm, tapeworm). Mass drug administration in schools.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-015",
        "generic_name": "Cetirizine",
        "brand_names": ["Zyrtec", "Cetzine", "Alerid"],
        "molecule_composition": "Cetirizine dihydrochloride 10 mg",
        "therapeutic_class": "Antihistamine — H1 blocker",
        "manufacturer": "Sun Pharmaceutical",
        "essential_drug_flag": False,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Drowsiness", "Dry mouth", "Headache"],
        "common_alternatives": [],
        "typical_indication": "Allergic rhinitis, urticaria, hay fever. Monsoon-season spikes.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-016",
        "generic_name": "Omeprazole",
        "brand_names": ["Omez", "Ocid", "Prilosec"],
        "molecule_composition": "Omeprazole 20 mg",
        "therapeutic_class": "Proton Pump Inhibitor — GI acid reducer",
        "manufacturer": "Dr Reddy's Laboratories",
        "essential_drug_flag": True,
        "dosage_form": "Capsule",
        "unit": "strips",
        "side_effects": ["Headache", "Diarrhoea", "Hypomagnesaemia (long-term)"],
        "common_alternatives": ["MED-017"],
        "typical_indication": "Acid peptic disease, GERD, prevention of NSAID-induced ulcers.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-017",
        "generic_name": "Ranitidine",
        "brand_names": ["Aciloc", "Zinetac", "Rantac"],
        "molecule_composition": "Ranitidine hydrochloride 150 mg",
        "therapeutic_class": "H2 Receptor Antagonist — GI acid reducer",
        "manufacturer": "Cadila Healthcare",
        "essential_drug_flag": False,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Headache", "Constipation", "Dizziness"],
        "common_alternatives": ["MED-016"],
        "typical_indication": "Acid peptic disease, gastric and duodenal ulcers.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-018",
        "generic_name": "Atenolol",
        "brand_names": ["Tenormin", "Aten", "Betacard"],
        "molecule_composition": "Atenolol 50 mg",
        "therapeutic_class": "Antihypertensive — Beta-1 Blocker",
        "manufacturer": "AstraZeneca India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Bradycardia", "Fatigue", "Cold extremities", "Bronchospasm (avoid in asthma)"],
        "common_alternatives": ["MED-007"],
        "typical_indication": "Hypertension, angina, arrhythmias. Slows heart rate to reduce cardiac workload.",
        "restock_lead_days": 10,
    },
    {
        "drug_id": "MED-019",
        "generic_name": "Doxycycline",
        "brand_names": ["Doxt-SL", "Vibrox", "Doxinate"],
        "molecule_composition": "Doxycycline hyclate 100 mg",
        "therapeutic_class": "Antibiotic — Tetracycline",
        "manufacturer": "Pfizer India",
        "essential_drug_flag": True,
        "dosage_form": "Capsule",
        "unit": "strips",
        "side_effects": ["Photosensitivity (avoid sun)", "Nausea", "Oesophagitis (take with plenty of water)"],
        "common_alternatives": ["MED-004"],
        "typical_indication": "Rickettsial infections, leptospirosis, atypical pneumonia, cholera.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-020",
        "generic_name": "Vitamin A (Retinol Palmitate)",
        "brand_names": ["Arovit", "Aquasol A"],
        "molecule_composition": "Retinol palmitate 200,000 IU per capsule",
        "therapeutic_class": "Fat-soluble Vitamin / Micronutrient",
        "manufacturer": "Wyeth Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Capsule",
        "unit": "capsules",
        "side_effects": ["Headache (high dose)", "Nausea", "Hypervitaminosis A (prolonged high dose)"],
        "common_alternatives": [],
        "typical_indication": "Vitamin A deficiency, prevention of night blindness in children. ASHA distribution programme.",
        "restock_lead_days": 14,
    },
    {
        "drug_id": "MED-021",
        "generic_name": "Cotrimoxazole (Trimethoprim + Sulphamethoxazole)",
        "brand_names": ["Bactrim", "Septran", "Cosutrin"],
        "molecule_composition": "Trimethoprim 80 mg + Sulphamethoxazole 400 mg",
        "therapeutic_class": "Antibiotic — Sulphonamide combination",
        "manufacturer": "Roche India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Rash (stop if severe — Steven-Johnson risk)", "Nausea", "Photosensitivity"],
        "common_alternatives": ["MED-003"],
        "typical_indication": "UTI, pneumocystis pneumonia (PCP prophylaxis in HIV), some diarrhoeal diseases.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-022",
        "generic_name": "Metronidazole",
        "brand_names": ["Flagyl", "Metrogyl", "Aristogyl"],
        "molecule_composition": "Metronidazole 400 mg",
        "therapeutic_class": "Antibiotic / Antiprotozoal — Nitroimidazole",
        "manufacturer": "Abbott India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Metallic taste", "Nausea", "Avoid alcohol (severe reaction)"],
        "common_alternatives": [],
        "typical_indication": "Amoebic dysentery, giardiasis, bacterial vaginosis, anaerobic infections.",
        "restock_lead_days": 5,
    },
    {
        "drug_id": "MED-023",
        "generic_name": "Prednisolone",
        "brand_names": ["Wysolone", "Omnacortil", "Deltacortril"],
        "molecule_composition": "Prednisolone 5 mg",
        "therapeutic_class": "Corticosteroid — Systemic",
        "manufacturer": "Pfizer India",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "strips",
        "side_effects": ["Weight gain", "Immunosuppression", "Hyperglycaemia", "Osteoporosis (long-term)"],
        "common_alternatives": [],
        "typical_indication": "Severe asthma, allergic reactions, autoimmune conditions, anti-inflammatory.",
        "restock_lead_days": 7,
    },
    {
        "drug_id": "MED-024",
        "generic_name": "Salbutamol (Albuterol)",
        "brand_names": ["Asthalin", "Ventolin", "Salbetol"],
        "molecule_composition": "Salbutamol sulfate 100 mcg per puff",
        "therapeutic_class": "Bronchodilator — Beta-2 Agonist",
        "manufacturer": "Cipla Ltd",
        "essential_drug_flag": True,
        "dosage_form": "Inhaler",
        "unit": "inhalers",
        "side_effects": ["Tremors", "Tachycardia", "Headache", "Hypokalaemia (high dose)"],
        "common_alternatives": [],
        "typical_indication": "Asthma and COPD. Relieves acute bronchospasm. Use as needed.",
        "restock_lead_days": 14,
    },
    {
        "drug_id": "MED-025",
        "generic_name": "Misoprostol",
        "brand_names": ["Cytotec", "Misoprost", "Cytolog"],
        "molecule_composition": "Misoprostol 200 mcg",
        "therapeutic_class": "Prostaglandin analogue — uterotonic",
        "manufacturer": "Ferring Pharmaceuticals",
        "essential_drug_flag": True,
        "dosage_form": "Tablet",
        "unit": "tablets",
        "side_effects": ["Uterine cramping", "Shivering", "Diarrhoea", "Fever"],
        "common_alternatives": [],
        "typical_indication": "Prevention and treatment of postpartum haemorrhage (PPH). Essential for maternal health programmes.",
        "restock_lead_days": 10,
    },
]

# ── PHC Catalog ──────────────────────────────────────────────────────────────
PHC_DATA = [
    # Maharashtra
    {"id": "MH-PUN-001", "name": "PHC Ambegaon", "district": "Pune", "state": "Maharashtra", "lat": 18.72, "lon": 73.60, "category": "Type B", "population": 28000},
    {"id": "MH-PUN-002", "name": "PHC Khed",    "district": "Pune", "state": "Maharashtra", "lat": 18.84, "lon": 73.79, "category": "Type A", "population": 35000},
    {"id": "MH-PUN-003", "name": "PHC Junnar",  "district": "Pune", "state": "Maharashtra", "lat": 19.21, "lon": 73.88, "category": "Type B", "population": 22000},
    {"id": "MH-PUN-004", "name": "PHC Shirur",  "district": "Pune", "state": "Maharashtra", "lat": 18.83, "lon": 74.37, "category": "Type A", "population": 40000},
    {"id": "MH-PUN-005", "name": "PHC Haveli",  "district": "Pune", "state": "Maharashtra", "lat": 18.54, "lon": 73.92, "category": "Type C", "population": 18000},
    {"id": "MH-NAS-001", "name": "PHC Dindori", "district": "Nashik", "state": "Maharashtra", "lat": 20.21, "lon": 73.83, "category": "Type B", "population": 31000},
    {"id": "MH-NAS-002", "name": "PHC Niphad",  "district": "Nashik", "state": "Maharashtra", "lat": 20.08, "lon": 74.11, "category": "Type A", "population": 38000},
    {"id": "MH-NAS-003", "name": "PHC Igatpuri","district": "Nashik", "state": "Maharashtra", "lat": 19.70, "lon": 73.56, "category": "Type B", "population": 25000},
    {"id": "MH-NAS-004", "name": "PHC Baglan",  "district": "Nashik", "state": "Maharashtra", "lat": 20.68, "lon": 74.10, "category": "Type A", "population": 42000},
    {"id": "MH-NAS-005", "name": "PHC Yeola",   "district": "Nashik", "state": "Maharashtra", "lat": 20.04, "lon": 74.49, "category": "Type C", "population": 20000},
    {"id": "MH-AMR-001", "name": "PHC Achalpur","district": "Amravati", "state": "Maharashtra", "lat": 21.26, "lon": 77.51, "category": "Type B", "population": 27000},
    {"id": "MH-AMR-002", "name": "PHC Anjangaon","district": "Amravati", "state": "Maharashtra", "lat": 21.17, "lon": 77.30, "category": "Type A", "population": 33000},
    {"id": "MH-AMR-003", "name": "PHC Daryapur","district": "Amravati", "state": "Maharashtra", "lat": 20.92, "lon": 77.32, "category": "Type B", "population": 24000},
    {"id": "MH-AMR-004", "name": "PHC Morshi",  "district": "Amravati", "state": "Maharashtra", "lat": 21.32, "lon": 77.98, "category": "Type A", "population": 37000},
    {"id": "MH-AMR-005", "name": "PHC Warud",   "district": "Amravati", "state": "Maharashtra", "lat": 21.47, "lon": 78.27, "category": "Type C", "population": 19000},
    # Rajasthan
    {"id": "RJ-JAI-001", "name": "PHC Sanganer","district": "Jaipur", "state": "Rajasthan", "lat": 26.82, "lon": 75.78, "category": "Type A", "population": 45000},
    {"id": "RJ-JAI-002", "name": "PHC Bassi",   "district": "Jaipur", "state": "Rajasthan", "lat": 26.88, "lon": 76.03, "category": "Type B", "population": 29000},
    {"id": "RJ-JAI-003", "name": "PHC Amber",   "district": "Jaipur", "state": "Rajasthan", "lat": 26.99, "lon": 75.85, "category": "Type B", "population": 26000},
    {"id": "RJ-JAI-004", "name": "PHC Chaksu",  "district": "Jaipur", "state": "Rajasthan", "lat": 26.61, "lon": 75.96, "category": "Type A", "population": 38000},
    {"id": "RJ-JAI-005", "name": "PHC Shahpura","district": "Jaipur", "state": "Rajasthan", "lat": 27.39, "lon": 75.96, "category": "Type C", "population": 21000},
    {"id": "RJ-JOD-001", "name": "PHC Bilara",  "district": "Jodhpur", "state": "Rajasthan", "lat": 26.17, "lon": 73.70, "category": "Type B", "population": 30000},
    {"id": "RJ-JOD-002", "name": "PHC Luni",    "district": "Jodhpur", "state": "Rajasthan", "lat": 26.19, "lon": 73.05, "category": "Type A", "population": 36000},
    {"id": "RJ-JOD-003", "name": "PHC Shergarh","district": "Jodhpur", "state": "Rajasthan", "lat": 27.12, "lon": 72.31, "category": "Type B", "population": 23000},
    {"id": "RJ-JOD-004", "name": "PHC Bhopalgarh","district": "Jodhpur", "state": "Rajasthan", "lat": 26.83, "lon": 73.56, "category": "Type A", "population": 41000},
    {"id": "RJ-JOD-005", "name": "PHC Pipar",   "district": "Jodhpur", "state": "Rajasthan", "lat": 26.38, "lon": 73.52, "category": "Type C", "population": 17000},
    {"id": "RJ-UDA-001", "name": "PHC Salumbar","district": "Udaipur", "state": "Rajasthan", "lat": 24.12, "lon": 74.01, "category": "Type B", "population": 28000},
    {"id": "RJ-UDA-002", "name": "PHC Gogunda","district": "Udaipur", "state": "Rajasthan", "lat": 24.77, "lon": 73.49, "category": "Type A", "population": 34000},
    {"id": "RJ-UDA-003", "name": "PHC Mavli",  "district": "Udaipur", "state": "Rajasthan", "lat": 24.68, "lon": 73.80, "category": "Type B", "population": 22000},
    {"id": "RJ-UDA-004", "name": "PHC Girwa",  "district": "Udaipur", "state": "Rajasthan", "lat": 24.57, "lon": 73.77, "category": "Type A", "population": 39000},
    {"id": "RJ-UDA-005", "name": "PHC Kherwara","district": "Udaipur", "state": "Rajasthan", "lat": 23.97, "lon": 73.88, "category": "Type C", "population": 19000},
]

# Monsoon months — dengue season
MONSOON_MONTHS = {7, 8, 9, 10}

# Base consumption rates (strips/month) per PHC category per drug
BASE_RATES = {
    "MED-001": {"Type A": 400, "Type B": 250, "Type C": 150},  # Paracetamol — high demand
    "MED-002": {"Type A": 200, "Type B": 120, "Type C":  70},
    "MED-003": {"Type A": 180, "Type B": 110, "Type C":  60},
    "MED-004": {"Type A":  90, "Type B":  55, "Type C":  30},
    "MED-005": {"Type A": 300, "Type B": 180, "Type C": 100},  # Metformin — chronic
    "MED-006": {"Type A": 200, "Type B": 120, "Type C":  70},
    "MED-007": {"Type A": 280, "Type B": 170, "Type C":  95},  # Amlodipine — chronic
    "MED-008": {"Type A": 150, "Type B":  90, "Type C":  50},
    "MED-009": {"Type A": 500, "Type B": 300, "Type C": 180},  # ORS — monsoon spike
    "MED-010": {"Type A": 250, "Type B": 150, "Type C":  90},
    "MED-011": {"Type A": 200, "Type B": 120, "Type C":  70},  # Chloroquine — monsoon spike
    "MED-012": {"Type A": 100, "Type B":  60, "Type C":  35},
    "MED-013": {"Type A": 350, "Type B": 210, "Type C": 120},  # Iron+FA — maternal
    "MED-014": {"Type A": 400, "Type B": 240, "Type C": 140},  # Albendazole — mass drug
    "MED-015": {"Type A": 160, "Type B":  95, "Type C":  55},
    "MED-016": {"Type A": 220, "Type B": 130, "Type C":  75},
    "MED-017": {"Type A": 140, "Type B":  85, "Type C":  48},
    "MED-018": {"Type A": 190, "Type B": 115, "Type C":  65},
    "MED-019": {"Type A":  80, "Type B":  48, "Type C":  28},
    "MED-020": {"Type A": 300, "Type B": 180, "Type C": 100},  # Vit A — programme
    "MED-021": {"Type A": 120, "Type B":  72, "Type C":  42},
    "MED-022": {"Type A": 140, "Type B":  84, "Type C":  48},
    "MED-023": {"Type A":  70, "Type B":  42, "Type C":  24},
    "MED-024": {"Type A":  45, "Type B":  27, "Type C":  15},
    "MED-025": {"Type A":  60, "Type B":  36, "Type C":  20},  # Misoprostol
}

# Seasonal multipliers by month for specific drugs
SEASONAL_MULTIPLIERS = {
    "MED-001": {7: 1.4, 8: 1.6, 9: 1.8, 10: 2.2, 11: 1.3},  # Paracetamol — dengue/fever
    "MED-009": {7: 1.6, 8: 2.0, 9: 2.2, 10: 1.8, 11: 1.2},  # ORS — monsoon diarrhoea
    "MED-011": {7: 1.5, 8: 1.8, 9: 2.0, 10: 1.6, 11: 1.1},  # Chloroquine — malaria
    "MED-012": {7: 1.3, 8: 1.5, 9: 1.8, 10: 1.4, 11: 1.0},
    "MED-015": {4: 1.3, 5: 1.5, 6: 1.3, 7: 1.2},             # Cetirizine — allergy/spring
    "MED-019": {7: 1.4, 8: 1.5, 9: 1.3},                     # Doxycycline — leptospirosis
}

# PHCs with artificially low stock (to trigger stockout alerts in demo)
LOW_STOCK_PHCS = {"MH-PUN-001", "MH-NAS-003"}
SURPLUS_PHCS   = {"MH-PUN-004", "MH-NAS-004"}  # candidates for redistribution


def _monthly_qty(drug_id, category, month, phc_id):
    base = BASE_RATES.get(drug_id, {}).get(category, 50)
    mult = SEASONAL_MULTIPLIERS.get(drug_id, {}).get(month, 1.0)
    # Dengue spike in Oct for Pune PHCs (seeded)
    if month == 10 and "PUN" in phc_id and drug_id in ("MED-001", "MED-009", "MED-015"):
        mult *= 1.5
    noise = random.uniform(0.88, 1.12)
    return max(1, int(base * mult * noise))


def seed(session):
    print("Seeding medicines...")
    for m in MEDICINES:
        if not session.get(Medicine, m["drug_id"]):
            session.add(Medicine(**{
                "drug_id": m["drug_id"],
                "generic_name": m["generic_name"],
                "brand_names": m["brand_names"],
                "molecule_composition": m["molecule_composition"],
                "therapeutic_class": m["therapeutic_class"],
                "manufacturer": m["manufacturer"],
                "essential_drug_flag": m["essential_drug_flag"],
                "dosage_form": m["dosage_form"],
                "unit": m["unit"],
                "side_effects": m["side_effects"],
                "common_alternatives": m.get("common_alternatives", []),
                "typical_indication": m["typical_indication"],
                "restock_lead_days": m["restock_lead_days"],
            }))

    print("Seeding PHCs...")
    phc_objs = []
    for p in PHC_DATA:
        if not session.get(PHC, p["id"]):
            phc = PHC(
                id=p["id"], name=p["name"], district=p["district"],
                state=p["state"], latitude=p["lat"], longitude=p["lon"],
                category=p["category"], population_covered=p["population"]
            )
            session.add(phc)
            phc_objs.append(phc)

    session.flush()

    print("Seeding inventory (current stock)...")
    now = datetime.utcnow()
    for p in PHC_DATA:
        for m in MEDICINES:
            monthly = _monthly_qty(m["drug_id"], p["category"], now.month, p["id"])
            lead = m["restock_lead_days"]
            # Normal stock = 1.5× monthly rate
            normal_qty = int(monthly * 1.5)
            if p["id"] in LOW_STOCK_PHCS and m["drug_id"] in ("MED-001", "MED-009", "MED-015"):
                # Critically low — will trigger stockout alert
                qty = max(1, int(monthly * lead / 30 * 0.6))
            elif p["id"] in SURPLUS_PHCS and m["drug_id"] in ("MED-001", "MED-009"):
                # Surplus — redistribution source candidate
                qty = int(monthly * 2.8)
            else:
                qty = int(normal_qty * random.uniform(0.7, 1.3))
            session.add(InventoryItem(
                phc_id=p["id"], drug_id=m["drug_id"],
                quantity=qty, unit=m["unit"], last_updated=now,
                batch=f"BT-2026-{random.randint(100,999)}"
            ))

    print("Seeding dispensation history (6 months)...")
    start_date = datetime(2026, 4, 1)
    for month_offset in range(6):
        month_date = start_date + timedelta(days=30 * month_offset)
        month_num  = month_date.month
        for p in PHC_DATA:
            for m in MEDICINES:
                qty = _monthly_qty(m["drug_id"], p["category"], month_num, p["id"])
                session.add(DispensationHistory(
                    phc_id=p["id"], drug_id=m["drug_id"],
                    qty_dispensed=qty, date=month_date,
                    month=month_num,
                    is_monsoon=month_num in MONSOON_MONTHS
                ))

    print("Seeding bed status...")
    for p in PHC_DATA:
        cap = {"Type A": 30, "Type B": 20, "Type C": 10}[p["category"]]
        for ward in ["General", "Maternity"]:
            beds = cap if ward == "General" else cap // 3
            occ  = random.randint(int(beds * 0.3), int(beds * 0.85))
            session.add(BedStatus(
                phc_id=p["id"], ward_type=ward,
                total=beds, occupied=occ, timestamp=now
            ))

    print("Seeding staff attendance...")
    STAFF_ROLES = [
        ("Doctor", 2, 3), ("Nurse", 4, 6), ("Pharmacist", 1, 1), ("ANM", 2, 3)
    ]
    for p in PHC_DATA:
        for role, pres, sanc in STAFF_ROLES:
            actual_sanc = sanc if p["category"] == "Type A" else max(1, sanc - 1)
            actual_pres = min(pres, actual_sanc)
            session.add(StaffAttendance(
                phc_id=p["id"], role=role,
                present_count=actual_pres, sanctioned_count=actual_sanc,
                timestamp=now
            ))

    print("Seeding prescription events (30-day window, dengue spike in Pune)...")
    dengue_drugs = ["MED-001", "MED-009", "MED-015"]
    base_event_date = now - timedelta(days=30)
    for i in range(200):
        phc = random.choice(PHC_DATA)
        # Bias Pune PHCs toward dengue drug combos
        if phc["district"] == "Pune" and random.random() < 0.55:
            drugs = random.sample(dengue_drugs, k=random.randint(2, 3))
            diag  = "Suspected dengue / viral fever"
        else:
            drugs = random.sample([m["drug_id"] for m in MEDICINES], k=random.randint(1, 4))
            diag  = None
        evt_date = base_event_date + timedelta(days=random.randint(0, 30))
        h = hashlib.sha256(f"patient-{i}-{phc['id']}".encode()).hexdigest()[:16]
        session.add(PrescriptionEvent(
            anonymized_patient_hash=h,
            phc_id=phc["id"],
            drug_ids=drugs,
            diagnosis_class=diag,
            geo_block=f"{phc['district']}-Block-{random.randint(1, 5)}",
            state=phc["state"],
            district=phc["district"],
            timestamp=evt_date,
            consented=True
        ))

    session.flush()
    print("Seed complete. Database is ready.")


if __name__ == "__main__":
    init_db()
    with get_db_session() as session:
        seed(session)
    print("Done! Run `python backend/api/main.py` to start the server.")
