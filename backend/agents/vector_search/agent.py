"""
MedBridge AI — AGENT 3: Vector Search (Semantic Search)
========================================================
Semantic search on unstructured text (procedures, equipment, capabilities).
Auto-selects the best named vector based on query type:
  - full_document:  broad / general queries
  - clinical_detail: procedure/equipment queries
  - specialties_context: specialty matching queries

Applies metadata filters extracted from query text.
"""

import re
import time
from typing import Dict, List, Optional

from backend.core.config import (
    COLLECTION_FACILITIES, MEDICAL_SPECIALTIES_MAP,
    VEC_CLINICAL, VEC_FULL, VEC_SPECIALTIES,
)
from backend.core.vectorstore import get_qdrant_client, load_embedding_model, search_facilities


class VectorSearchAgent:
    """Semantic search agent with auto vector selection and metadata filtering."""

    def __init__(self):
        # Clients are lazy-loaded via singletons in vectorstore module
        pass

    # ── Vector selection ─────────────────────────────────────────────────────

    def _select_vector(self, query: str) -> str:
        ql = query.lower()
        clinical = [
            "procedure", "equipment", "surgery", "operation", "device",
            "machine", "scanner", "theater", "operating", "diagnostic",
            "ct scan", "mri", "x-ray", "ultrasound", "laboratory",
            "icu", "nicu", "ventilator", "oxygen", "bed capacity",
        ]
        if any(kw in ql for kw in clinical):
            return VEC_CLINICAL

        specialty = [
            "specialty", "specialties", "speciali",
            "cardiology", "ophthalmology", "orthopedic", "pediatric",
            "obstetric", "gynecology", "neurology", "oncology",
            "dermatology", "psychiatry", "radiology", "anesthesia",
            "dentistry", "dental",
        ]
        if any(kw in ql for kw in specialty):
            return VEC_SPECIALTIES

        return VEC_FULL

    # ── Filter extraction ────────────────────────────────────────────────────

    def _extract_filters(self, query: str) -> Dict:
        filters = {}
        ql = query.lower()

        if "ngo" in ql or "non-governmental" in ql:
            filters["org_type"] = "ngo"
        elif "facility" in ql and "ngo" not in ql:
            filters["org_type"] = "facility"

        for ftype in ["hospital", "clinic", "pharmacy", "dentist"]:
            if ftype in ql:
                filters["facility_type"] = ftype
                break

        # Cities — longer names first, word-boundary matching
        cities = [
            "Cape Coast", "Accra", "Kumasi", "Tamale", "Takoradi",
            "Sunyani", "Bolgatanga", "Koforidua", "Tema", "Wa", "Ho",
        ]
        for city in cities:
            if re.search(r'\b' + re.escape(city.lower()) + r'\b', ql):
                filters["city"] = city
                break

        for spec_id, keywords in MEDICAL_SPECIALTIES_MAP.items():
            for kw in keywords:
                if kw in ql:
                    filters.setdefault("specialties_filter", []).append(spec_id)
                    break

        return filters

    # ── Main search ──────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> Dict:
        t0 = time.time()
        vector_name = self._select_vector(query)
        filters = self._extract_filters(query)

        results = search_facilities(
            query=query,
            vector_name=vector_name,
            top_k=top_k,
            org_type=filters.get("org_type"),
            facility_type=filters.get("facility_type"),
            city=filters.get("city"),
            specialties_filter=filters.get("specialties_filter"),
        )

        duration = (time.time() - t0) * 1000

        # Build citations from results
        citations = [
            {"facility_id": r["id"], "name": r["name"], "score": r["score"],
             "matched_text": r.get("document_text", "")[:200]}
            for r in results
        ]

        return {
            "query": query,
            "agent": "vector_search",
            "vector_used": vector_name,
            "filters_applied": filters,
            "count": len(results),
            "results": results,
            "citations": citations,
            "duration_ms": round(duration, 2),
        }

    def search_for_service(self, service: str, region: Optional[str] = None, top_k: int = 10) -> Dict:
        q = f"facility offering {service}"
        if region:
            q += f" in {region}"
        t0 = time.time()
        results = search_facilities(query=q, vector_name=VEC_CLINICAL, top_k=top_k, city=region)
        return {
            "query": q, "agent": "vector_search", "service": service,
            "vector_used": VEC_CLINICAL, "count": len(results), "results": results,
            "duration_ms": round((time.time() - t0) * 1000, 2),
        }
