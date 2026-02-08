"""
MedBridge AI — Shared Configuration
=====================================
Central config for Qdrant, embedding models, and agent settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_PATH = DATA_DIR / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ── Qdrant Cloud ─────────────────────────────────────────────────────────────
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# ── Collections ──────────────────────────────────────────────────────────────
COLLECTION_FACILITIES = "ghana_medical_facilities"

# ── Embedding Model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBED_BATCH_SIZE = 64

# ── Medical Domain Constants ─────────────────────────────────────────────────
MEDICAL_SPECIALTIES_MAP = {
    "cardiology": ["cardiology", "cardiac", "heart", "cardiovascular"],
    "ophthalmology": ["ophthalmology", "eye", "cataract", "retina", "ophthalmic"],
    "orthopedicSurgery": ["orthopedic", "orthopaedic", "bone", "fracture", "joint"],
    "generalSurgery": ["surgery", "surgical", "operation"],
    "pediatrics": ["pediatric", "children", "child", "neonatal"],
    "gynecologyAndObstetrics": ["obstetric", "gynecology", "maternal", "maternity", "women"],
    "emergencyMedicine": ["emergency", "trauma", "accident"],
    "internalMedicine": ["internal medicine", "general medicine"],
    "infectiousDiseases": ["infectious", "hiv", "aids", "malaria", "tuberculosis", "tb"],
    "dentistry": ["dental", "dentist", "tooth", "teeth"],
    "radiology": ["radiology", "x-ray", "imaging", "ct scan", "mri", "ultrasound"],
    "anesthesia": ["anesthesia", "anaesthesia", "anesthesiology"],
    "psychiatry": ["psychiatry", "mental health", "psychiatric"],
    "neurosurgery": ["neurosurgery", "brain surgery", "neuro"],
    "plasticSurgery": ["plastic surgery", "reconstructive", "cleft"],
}

# ── Facility Capability Requirements (for anomaly detection) ─────────────────
ADVANCED_PROCEDURE_REQUIREMENTS = {
    "neurosurgery": {
        "required_equipment": ["CT scanner", "MRI", "specialized OR"],
        "required_staff": ["neurosurgeon"],
        "required_capability": ["ICU"],
    },
    "cardiac_surgery": {
        "required_equipment": ["cardiac monitor", "bypass machine", "echo"],
        "required_staff": ["cardiac surgeon", "perfusionist"],
        "required_capability": ["ICU", "cardiac care unit"],
    },
    "cataract_surgery": {
        "required_equipment": ["operating microscope", "phaco machine"],
        "required_staff": ["ophthalmologist"],
        "required_capability": ["operating theater"],
    },
}
