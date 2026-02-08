"""
MedBridge AI — Vector Search Agent
=====================================
Semantic lookup on plaintext + metadata filtering.
Uses the multi-representation vectors in Qdrant to answer
queries that require understanding unstructured text.

Strategy:
  - Broad queries → full_document vector
  - Procedure/equipment queries → clinical_detail vector
  - Specialty matching queries → specialties_context vector
  - Always applies metadata filters when detected
"""

import re
import time
from typing import Dict, List, Optional

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from src.config import COLLECTION_FACILITIES, MEDICAL_SPECIALTIES_MAP
from src.vectorize_and_store import (
    VEC_CLINICAL,
    VEC_FULL,
    VEC_SPECIALTIES,
    get_qdrant_client,
    load_embedding_model,
    search_facilities,
)


class VectorSearchAgent:
    """
    Handles semantic search queries against the Qdrant vector store.
    Automatically selects the best vector representation based on query type.
    """

    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        model: Optional[SentenceTransformer] = None,
    ):
        self.client = client or get_qdrant_client()
        self.model = model or load_embedding_model()

    # ── Vector selection heuristics ──────────────────────────────────────────

    def _select_vector(self, query: str) -> str:
        """Choose the best named vector for this query type."""
        query_lower = query.lower()

        # Clinical detail queries → clinical_detail vector
        clinical_keywords = [
            "procedure", "equipment", "surgery", "operation", "device",
            "machine", "scanner", "theater", "operating", "diagnostic",
            "ct scan", "mri", "x-ray", "ultrasound", "laboratory",
            "icu", "nicu", "ventilator", "oxygen", "bed capacity",
        ]
        if any(kw in query_lower for kw in clinical_keywords):
            return VEC_CLINICAL

        # Specialty queries → specialties_context vector
        specialty_keywords = [
            "specialty", "specialties", "speciali",
            "cardiology", "ophthalmology", "orthopedic", "pediatric",
            "obstetric", "gynecology", "neurology", "oncology",
            "dermatology", "psychiatry", "radiology", "anesthesia",
            "dentistry", "dental",
        ]
        if any(kw in query_lower for kw in specialty_keywords):
            return VEC_SPECIALTIES

        # Default: full document for broad queries
        return VEC_FULL

    # ── Filter extraction ────────────────────────────────────────────────────

    def _extract_filters(self, query: str) -> Dict:
        """Extract metadata filters from the query text."""
        filters = {}
        query_lower = query.lower()

        # Organization type
        if "ngo" in query_lower or "foundation" in query_lower or "non-governmental" in query_lower:
            filters["org_type"] = "ngo"
        elif "facility" in query_lower and "ngo" not in query_lower:
            filters["org_type"] = "facility"

        # Facility type
        for ftype in ["hospital", "clinic", "pharmacy", "dentist"]:
            if ftype in query_lower:
                filters["facility_type"] = ftype
                break

        # City — use word boundary matching to avoid partial matches (e.g. "Ho" in "Hospital")
        cities = [
            "Accra", "Kumasi", "Tamale", "Takoradi", "Cape Coast",
            "Sunyani", "Bolgatanga", "Wa", "Koforidua", "Tema", "Ho",
        ]
        for city in cities:
            pattern = r'\b' + re.escape(city.lower()) + r'\b'
            if re.search(pattern, query_lower):
                filters["city"] = city
                break

        # Specialty filter
        for spec_id, keywords in MEDICAL_SPECIALTIES_MAP.items():
            for kw in keywords:
                if kw in query_lower:
                    filters.setdefault("specialties_filter", []).append(spec_id)
                    break

        return filters

    # ── Main search ──────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 10) -> Dict:
        """
        Execute a semantic search with automatic vector selection and filtering.
        Returns results dict with metadata for tracing.
        """
        t0 = time.time()

        # Select vector and filters
        vector_name = self._select_vector(query)
        filters = self._extract_filters(query)

        # Execute search
        results = search_facilities(
            self.client,
            self.model,
            query,
            vector_name=vector_name,
            top_k=top_k,
            org_type=filters.get("org_type"),
            facility_type=filters.get("facility_type"),
            city=filters.get("city"),
            specialties_filter=filters.get("specialties_filter"),
        )

        duration = (time.time() - t0) * 1000

        return {
            "query": query,
            "vector_used": vector_name,
            "filters_applied": filters,
            "count": len(results),
            "results": results,
            "duration_ms": round(duration, 2),
        }

    def search_for_service(self, service_name: str, region: Optional[str] = None, top_k: int = 10) -> Dict:
        """Search specifically for a medical service/procedure."""
        query = f"facility offering {service_name}"
        if region:
            query += f" in {region}"

        t0 = time.time()
        results = search_facilities(
            self.client, self.model, query,
            vector_name=VEC_CLINICAL, top_k=top_k,
            city=region,
        )
        duration = (time.time() - t0) * 1000

        return {
            "query": query,
            "service": service_name,
            "region": region,
            "vector_used": VEC_CLINICAL,
            "count": len(results),
            "results": results,
            "duration_ms": round(duration, 2),
        }

    def find_similar_facilities(self, facility_doc: str, top_k: int = 5) -> Dict:
        """Find facilities similar to a given facility document."""
        t0 = time.time()
        query_vector = self.model.encode(facility_doc, normalize_embeddings=True).tolist()

        from qdrant_client.models import Filter
        results = self.client.query_points(
            collection_name=COLLECTION_FACILITIES,
            query=query_vector,
            using=VEC_FULL,
            limit=top_k + 1,  # +1 to exclude self
            with_payload=True,
        )

        duration = (time.time() - t0) * 1000

        formatted = [
            {
                "id": hit.id,
                "score": hit.score,
                "name": hit.payload.get("name"),
                "city": hit.payload.get("address_city"),
                "specialties": hit.payload.get("specialties", []),
            }
            for hit in results.points
        ]

        return {
            "query": "similar_facilities",
            "count": len(formatted),
            "results": formatted,
            "duration_ms": round(duration, 2),
        }


def create_vector_search_agent(
    client: Optional[QdrantClient] = None,
    model: Optional[SentenceTransformer] = None,
) -> VectorSearchAgent:
    return VectorSearchAgent(client, model)


if __name__ == "__main__":
    agent = create_vector_search_agent()

    test_queries = [
        "What services does Korle Bu Teaching Hospital offer?",
        "clinics in Accra that do cataract surgery",
        "hospitals with orthopedic surgery equipment",
        "NGOs working on maternal health",
        "facilities with ICU and ventilator support",
        "dental clinics in Kumasi",
        "emergency surgery facilities in Northern Ghana",
    ]

    print("═══ Vector Search Agent — Semantic Search Demo ═══\n")
    for q in test_queries:
        result = agent.search(q, top_k=3)
        print(f"Q: {q}")
        print(f"  Vector: {result['vector_used']}, Filters: {result['filters_applied']}")
        print(f"  Found: {result['count']} results ({result['duration_ms']}ms)")
        for r in result["results"][:3]:
            specs = ", ".join(r["specialties"][:3]) if r["specialties"] else "N/A"
            print(f"    [{r['score']:.3f}] {r['name']} ({r['city']}) — {specs}")
        print()
