"""
MedBridge AI — Shared Configuration
=====================================
Central config for Qdrant, embedding models, agent settings, and medical domain constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CSV_PATH = DATA_DIR / "Virtue Foundation Ghana v0.3 - Sheet1.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"

# ── Qdrant Cloud ─────────────────────────────────────────────────────────────
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# ── Groq Cloud LLM ───────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = "llama-3.3-70b-versatile"

# ── Collections ──────────────────────────────────────────────────────────────
COLLECTION_FACILITIES = "ghana_medical_facilities"

# ── Embedding Model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
EMBED_BATCH_SIZE = 64

# Named vector keys
VEC_FULL = "full_document"
VEC_CLINICAL = "clinical_detail"
VEC_SPECIALTIES = "specialties_context"

# ── Ghana Coordinates ────────────────────────────────────────────────────────
GHANA_CENTER_LAT = 7.9465
GHANA_CENTER_LNG = -1.0232
GHANA_BOUNDING_BOX = {
    "north": 11.17,
    "south": 4.74,
    "east": 1.20,
    "west": -3.26,
}

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

# ── Facility Capability Requirements (for Medical Reasoning Agent) ───────────
ADVANCED_PROCEDURE_REQUIREMENTS = {
    "neurosurgery": {
        "required_equipment": ["CT scanner", "MRI", "operating microscope"],
        "required_staff": ["neurosurgeon"],
        "required_capability": ["ICU", "operating theater"],
        "min_beds": 50,
    },
    "cardiac_surgery": {
        "required_equipment": ["cardiac monitor", "bypass machine", "echo", "catheterization lab"],
        "required_staff": ["cardiac surgeon", "perfusionist", "cardiologist"],
        "required_capability": ["ICU", "cardiac care unit", "operating theater"],
        "min_beds": 100,
    },
    "cataract_surgery": {
        "required_equipment": ["operating microscope", "phaco machine", "keratometer"],
        "required_staff": ["ophthalmologist"],
        "required_capability": ["operating theater"],
        "min_beds": 5,
    },
    "dialysis": {
        "required_equipment": ["dialysis machine", "reverse osmosis"],
        "required_staff": ["nephrologist"],
        "required_capability": ["dialysis unit"],
        "min_beds": 10,
    },
    "orthopedic_surgery": {
        "required_equipment": ["C-arm fluoroscopy", "orthopedic instruments", "casting materials"],
        "required_staff": ["orthopedic surgeon"],
        "required_capability": ["operating theater", "recovery ward"],
        "min_beds": 30,
    },
    "oncology": {
        "required_equipment": ["radiotherapy", "chemotherapy unit", "pathology lab"],
        "required_staff": ["oncologist", "radiation therapist"],
        "required_capability": ["isolation rooms", "pharmacy"],
        "min_beds": 50,
    },
}

# ── Red-flag language patterns (for Medical Reasoning Agent) ──────────────────
RED_FLAG_PATTERNS = {
    "visiting_specialist": [
        r"visit(?:ing|s)\s+(?:specialist|surgeon|doctor)",
        r"(?:weekly|monthly|quarterly)\s+(?:clinic|service)",
        r"outreach\s+(?:program|service|clinic)",
    ],
    "temporary_service": [
        r"(?:surgical|medical)\s+camp",
        r"mission\s+(?:trip|team|group)",
        r"temporary\s+(?:service|clinic|facility)",
        r"mobile\s+(?:unit|clinic|service)",
    ],
    "vague_claim": [
        r"(?:all|any|every)\s+(?:type|kind)\s+of\s+(?:surgery|procedure|service)",
        r"comprehensive\s+(?:care|service|treatment)",
        r"world.class",
        r"state.of.the.art",
    ],
}
