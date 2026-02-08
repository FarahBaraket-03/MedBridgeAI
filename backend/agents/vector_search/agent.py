"""
MedBridge AI — AGENT 3: Vector Search (Semantic Search)
========================================================
Semantic search on unstructured text (procedures, equipment, capabilities).
Queries ALL three named vectors simultaneously and fuses results using
Reciprocal Rank Fusion (RRF) for robust multi-representation retrieval:
  - full_document:  broad / general queries
  - clinical_detail: procedure/equipment queries
  - specialties_context: specialty matching queries

Applies metadata filters extracted from query text.
"""

import re
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional

from backend.core.config import (
    COLLECTION_FACILITIES, MEDICAL_SPECIALTIES_MAP,
    VEC_CLINICAL, VEC_FULL, VEC_SPECIALTIES,
)
from backend.core.vectorstore import get_qdrant_client, load_embedding_model, search_facilities
from backend.core.databricks import is_databricks_backend, search_via_databricks

# RRF constant (standard value from the original RRF paper, Cormack+ 2009)
RRF_K = 60

logger = logging.getLogger(__name__)


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

    # ── RRF fusion search ──────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> Dict:
        """
        Multi-vector Reciprocal Rank Fusion search.
        Queries all 3 named vectors, fuses with RRF, and returns top_k.
        """
        t0 = time.time()
        filters = self._extract_filters(query)

        filter_kwargs = {
            "org_type": filters.get("org_type"),
            "facility_type": filters.get("facility_type"),
            "city": filters.get("city"),
            "specialties_filter": filters.get("specialties_filter"),
        }

        # Determine per-vector weights based on query content
        weights = self._compute_vector_weights(query)

        # Query all 3 named vectors (fetch more candidates for fusion)
        fetch_k = min(top_k * 3, 30)
        results_by_vector: Dict[str, List[Dict]] = {}
        use_databricks = is_databricks_backend()

        for vec_name in [VEC_FULL, VEC_CLINICAL, VEC_SPECIALTIES]:
            try:
                if use_databricks:
                    results_by_vector[vec_name] = search_via_databricks(
                        query=query,
                        vector_name=vec_name,
                        top_k=fetch_k,
                    )
                else:
                    results_by_vector[vec_name] = search_facilities(
                        query=query,
                        vector_name=vec_name,
                        top_k=fetch_k,
                        **filter_kwargs,
                    )
            except Exception as e:
                logger.warning("Vector search failed for %s: %s", vec_name, e)
                results_by_vector[vec_name] = []

        search_backend = "databricks_model_serving" if use_databricks else "qdrant_cloud"

        # ── Reciprocal Rank Fusion ──
        rrf_scores: Dict[str, float] = defaultdict(float)
        doc_map: Dict[str, Dict] = {}

        for vec_name, results in results_by_vector.items():
            w = weights.get(vec_name, 1.0)
            for rank, doc in enumerate(results):
                doc_id = str(doc["id"])
                rrf_scores[doc_id] += w / (RRF_K + rank + 1)
                # Keep the richest payload version
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc

        # Sort by fused score and take top_k
        ranked_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
        fused_results = []
        for doc_id in ranked_ids:
            doc = doc_map[doc_id].copy()
            doc["rrf_score"] = round(rrf_scores[doc_id], 4)
            fused_results.append(doc)

        duration = (time.time() - t0) * 1000

        # Determine primary vector for citation purposes
        primary_vector = max(weights, key=weights.get)

        citations = [
            {
                "facility_id": r["id"], "name": r["name"],
                "rrf_score": r["rrf_score"],
                "matched_text": r.get("document_text", "")[:200],
            }
            for r in fused_results
        ]

        return {
            "query": query,
            "agent": "vector_search",
            "search_method": "reciprocal_rank_fusion",
            "search_backend": search_backend,
            "vectors_queried": list(results_by_vector.keys()),
            "vector_weights": weights,
            "primary_vector": primary_vector,
            "filters_applied": filters,
            "count": len(fused_results),
            "results": fused_results,
            "citations": citations,
            "duration_ms": round(duration, 2),
        }

    def _compute_vector_weights(self, query: str) -> Dict[str, float]:
        """Assign per-vector weights based on query content.

        All vectors always contribute.  Raw affinity scores are computed from
        keyword hits, then **normalised so the three weights always sum to 3.0**.
        This prevents a single vector from drowning out the others in the RRF
        fusion (the old bug: a query with 5 clinical keywords gave the
        clinical vector 3x the weight of full_document, making broad matches
        almost invisible).
        """
        ql = query.lower()

        clinical_kws = [
            "procedure", "equipment", "surgery", "operation", "device",
            "machine", "scanner", "theater", "operating", "diagnostic",
            "ct scan", "mri", "x-ray", "ultrasound", "laboratory",
            "icu", "nicu", "ventilator", "oxygen", "bed capacity",
        ]
        specialty_kws = [
            "specialty", "specialties", "speciali",
            "cardiology", "ophthalmology", "orthopedic", "pediatric",
            "obstetric", "gynecology", "neurology", "oncology",
            "dermatology", "psychiatry", "radiology", "anesthesia",
            "dentistry", "dental",
        ]

        clinical_hits = sum(1 for kw in clinical_kws if kw in ql)
        specialty_hits = sum(1 for kw in specialty_kws if kw in ql)

        # Raw affinity: 1 (base) + hits (capped at 3)
        raw_full = 1.0
        raw_clinical = 1.0 + min(clinical_hits, 3)
        raw_specialty = 1.0 + min(specialty_hits, 3)

        # Normalise so weights always sum to 3.0
        total = raw_full + raw_clinical + raw_specialty
        weights = {
            VEC_FULL: round(raw_full / total * 3.0, 3),
            VEC_CLINICAL: round(raw_clinical / total * 3.0, 3),
            VEC_SPECIALTIES: round(raw_specialty / total * 3.0, 3),
        }
        return weights

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
