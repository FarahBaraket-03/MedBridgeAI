"""
MedBridge AI — API Routes
===========================
REST endpoints for the React frontend.
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.orchestration.graph import run_query
from backend.core.preprocessing import run_preprocessing
from backend.agents.planning.agent import PlanningAgent
from backend.core.databricks import (
    is_databricks_backend,
    get_mlflow_run_info,
    get_serving_endpoint_status,
)

router = APIRouter()

# ── Cached agent singletons (avoid re-processing CSV per request) ────────────
_planning_agent: Optional[PlanningAgent] = None
_geospatial_agent = None  # lazy-imported
_medical_reasoning_agent = None  # lazy-imported


def _get_planning_agent() -> PlanningAgent:
    global _planning_agent
    if _planning_agent is None:
        _planning_agent = PlanningAgent()
    return _planning_agent


def _get_geospatial_agent():
    global _geospatial_agent
    if _geospatial_agent is None:
        from backend.agents.geospatial.agent import GeospatialAgent
        _geospatial_agent = GeospatialAgent()
    return _geospatial_agent


# ── Request / Response Models ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    query: str
    intent: str
    response: Any
    summary: str = ""
    trace: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    agents_used: List[str]
    total_duration_ms: float


class FacilityListItem(BaseModel):
    name: str
    city: Optional[str] = None
    region: Optional[str] = None
    org_type: Optional[str] = None
    facility_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    specialties: List[str] = []
    capacity: Optional[float] = None
    doctors: Optional[float] = None


# ── Cached data ──────────────────────────────────────────────────────────────
_facilities_cache: Optional[List[Dict]] = None


def _get_facilities() -> List[Dict]:
    global _facilities_cache
    if _facilities_cache is not None:
        return _facilities_cache

    df = run_preprocessing()
    facilities = []
    for _, row in df.iterrows():
        m = row["metadata"]
        lat = m.get("latitude")
        lng = m.get("longitude")
        try:
            lat = float(lat) if lat else None
            lng = float(lng) if lng else None
        except (ValueError, TypeError):
            lat, lng = None, None

        cap = m.get("capacity")
        docs = m.get("numberDoctors")
        try:
            cap = float(cap) if cap else None
        except (ValueError, TypeError):
            cap = None
        try:
            docs = float(docs) if docs else None
        except (ValueError, TypeError):
            docs = None

        facilities.append({
            "name": m.get("name", "Unknown"),
            "city": m.get("address_city"),
            "region": m.get("address_stateOrRegion"),
            "org_type": m.get("organization_type"),
            "facility_type": m.get("facilityTypeId"),
            "latitude": lat,
            "longitude": lng,
            "specialties": m.get("specialties", []),
            "capacity": cap,
            "doctors": docs,
        })

    _facilities_cache = facilities
    return facilities


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "service": "MedBridge AI", "version": "2.0.0"}


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    """Run a natural language query through the LangGraph multi-agent workflow."""
    # Guard: reject empty or excessively long queries
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if len(req.query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long (max 2000 characters)")

    t0 = time.time()
    try:
        result = run_query(req.query, req.context)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal processing error. Please try again.")

    return QueryResponse(
        query=result.get("query", req.query),
        intent=result.get("intent", "general"),
        response=result.get("response", {}),
        summary=result.get("summary", ""),
        trace=result.get("trace", []),
        citations=result.get("citations", []),
        agents_used=result.get("agents_used", []),
        total_duration_ms=result.get("total_duration_ms", round((time.time() - t0) * 1000, 2)),
    )


@router.get("/facilities")
async def list_facilities():
    """Return all facilities (for map markers and stats)."""
    facilities = _get_facilities()
    return {"total": len(facilities), "facilities": facilities}


@router.get("/stats")
async def get_stats():
    """Aggregate statistics for the dashboard."""
    facilities = _get_facilities()

    total = len(facilities)
    with_coords = sum(1 for f in facilities if f["latitude"] is not None)
    org_types = {}
    regions = {}
    all_specialties = set()
    total_beds = 0
    total_docs = 0

    for f in facilities:
        # Org type
        ot = f.get("org_type", "Unknown")
        org_types[ot] = org_types.get(ot, 0) + 1

        # Region
        reg = f.get("region") or "Unknown"
        regions[reg] = regions.get(reg, 0) + 1

        # Specialties
        for s in f.get("specialties", []):
            all_specialties.add(s)

        # Capacity
        if f.get("capacity"):
            total_beds += f["capacity"]
        if f.get("doctors"):
            total_docs += f["doctors"]

    # Top 10 regions
    sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_facilities": total,
        "with_coordinates": with_coords,
        "total_beds": int(total_beds),
        "total_doctors": int(total_docs),
        "organization_types": org_types,
        "unique_specialties": len(all_specialties),
        "top_regions": sorted_regions[:10],
        "all_regions": sorted_regions,
    }


@router.get("/specialties")
async def list_specialties():
    """List all unique specialties with their counts."""
    facilities = _get_facilities()
    spec_counts = {}
    for f in facilities:
        for s in f.get("specialties", []):
            spec_counts[s] = spec_counts.get(s, 0) + 1

    sorted_specs = sorted(spec_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "total_unique": len(sorted_specs),
        "specialties": [{"name": s, "count": c} for s, c in sorted_specs],
    }


# ── Planning endpoints ──────────────────────────────────────────────
@router.get("/planning/scenarios")
async def list_planning_scenarios():
    """Return available planning scenarios."""
    return {
        "scenarios": [
            {
                "id": "emergency_routing",
                "name": "Emergency Routing",
                "icon": "🚑",
                "description": "Find nearest capable facility for emergency cases",
                "params": ["specialty", "origin_city"],
            },
            {
                "id": "specialist_deployment",
                "name": "Specialist Deployment",
                "icon": "👨‍⚕️",
                "description": "Optimal deployment route for specialist teams",
                "params": ["specialty"],
            },
            {
                "id": "equipment_distribution",
                "name": "Equipment Distribution",
                "icon": "🏥",
                "description": "Priority regions for equipment distribution",
                "params": ["equipment_type"],
            },
            {
                "id": "new_facility_placement",
                "name": "New Facility Placement",
                "icon": "📍",
                "description": "Optimal locations for new healthcare facilities",
                "params": ["specialty"],
            },
            {
                "id": "capacity_planning",
                "name": "Capacity Planning",
                "icon": "📊",
                "description": "Regional capacity analysis and expansion priorities",
                "params": [],
            },
        ]
    }


class PlanningRequest(BaseModel):
    scenario: str
    specialty: str | None = None
    equipment_type: str | None = None
    origin_city: str | None = None
    use_quantum: bool = False


class RoutingMapRequest(BaseModel):
    scenario: str = "emergency_routing"
    specialty: str | None = None
    origin_city: str | None = None


@router.post("/routing-map")
async def get_routing_map_data(req: RoutingMapRequest):
    """Generate full routing map data with facilities, route, and reasoning steps."""
    try:
        planning = _get_planning_agent()
        geo = _get_geospatial_agent()

        # Geocode origin city if provided
        origin_lat, origin_lng = None, None
        if req.origin_city:
            city_match = geo.valid_coords[
                geo.valid_coords["address_city"].str.contains(req.origin_city, case=False, na=False)
            ]
            if not city_match.empty:
                origin_lat = float(city_match["latitude"].mean())
                origin_lng = float(city_match["longitude"].mean())

        # Execute the planning scenario
        query_parts = [req.scenario.replace("_", " ")]
        if req.specialty:
            query_parts.append(f"for {req.specialty}")
        if req.origin_city:
            query_parts.append(f"from {req.origin_city}")
        query = " ".join(query_parts)

        ctx = {}
        if origin_lat is not None:
            ctx["lat"] = origin_lat
            ctx["lng"] = origin_lng

        plan_result = planning.execute_query(query, context=ctx)

        # Get all facilities for map background
        facilities = _get_facilities()
        with_coords = [f for f in facilities if f["latitude"] is not None]

        # Get medical deserts
        deserts = geo.identify_medical_deserts(req.specialty)

        # Build route waypoints from plan result
        route = []
        if plan_result.get("primary_facility"):
            pf = plan_result["primary_facility"]
            route.append({
                "name": pf.get("facility", "Origin"),
                "lat": pf.get("latitude"),
                "lng": pf.get("longitude"),
                "city": pf.get("city"),
                "type": "destination",
                "distance_km": pf.get("distance_km"),
                "capability_match": pf.get("capability_match"),
            })
        if plan_result.get("stops"):
            for stop in plan_result["stops"]:
                route.append({
                    "name": stop.get("facility"),
                    "lat": stop.get("latitude"),
                    "lng": stop.get("longitude"),
                    "city": stop.get("city"),
                    "type": "stop",
                    "distance_from_prev_km": stop.get("distance_from_prev_km"),
                })
        if plan_result.get("placements"):
            for p in plan_result["placements"]:
                route.append({
                    "name": p.get("recommended_facility"),
                    "lat": p.get("latitude"),
                    "lng": p.get("longitude"),
                    "city": p.get("city"),
                    "type": "placement",
                    "facilities_served": p.get("facilities_served"),
                })
        if plan_result.get("suggestions"):
            for s in plan_result["suggestions"]:
                if s.get("suggested_lat"):
                    route.append({
                        "name": f"New facility ({s.get('region', 'Unknown')})",
                        "lat": s.get("suggested_lat"),
                        "lng": s.get("suggested_lng"),
                        "city": s.get("region"),
                        "type": "suggestion",
                        "priority": s.get("priority"),
                    })

        # Reasoning steps for the sidebar
        reasoning = [
            {"step": 1, "title": "Query Analysis", "content": f"Scenario: {req.scenario}", "data": f"Specialty: {req.specialty or 'all'}"},
            {"step": 2, "title": "Facility Search", "content": f"Searched {len(with_coords)} geo-located facilities", "data": f"Filter: {req.specialty or 'none'}"},
            {"step": 3, "title": "Route Calculation", "content": f"Generated {len(route)} waypoints", "data": plan_result.get("title", "")},
            {"step": 4, "title": "Desert Detection", "content": f"Found {deserts.get('deserts_found', 0)} medical deserts", "data": f"Threshold: {deserts.get('threshold_km', 75)} km"},
        ]

        return {
            "status": "ok",
            "plan": plan_result,
            "facilities": with_coords[:200],
            "route": route,
            "deserts": deserts.get("deserts", []),
            "reasoning": reasoning,
            "stats": {
                "distance_km": plan_result.get("total_distance_km", sum(r.get("distance_km", 0) or r.get("distance_from_prev_km", 0) or 0 for r in route)),
                "time_min": plan_result.get("primary_facility", {}).get("est_travel_min", 0) or len(route) * 30,
                "facilities_count": len(route),
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/planning/execute")
async def execute_planning(req: PlanningRequest):
    """Execute a planning scenario directly."""
    try:
        agent = _get_planning_agent()
        # Build a natural-language query from the scenario params
        query_parts = [req.scenario.replace("_", " ")]
        if req.specialty:
            query_parts.append(f"for {req.specialty}")
        if req.equipment_type:
            query_parts.append(f"{req.equipment_type}")
        if req.origin_city:
            query_parts.append(f"from {req.origin_city}")
        query = " ".join(query_parts)

        # Build context with coordinates if origin_city provided
        context = {"use_quantum": req.use_quantum}
        if req.origin_city:
            geo = _get_geospatial_agent()
            city_match = geo.valid_coords[
                geo.valid_coords["address_city"].str.contains(req.origin_city, case=False, na=False)
            ]
            if not city_match.empty:
                context["lat"] = float(city_match["latitude"].mean())
                context["lng"] = float(city_match["longitude"].mean())

        result = agent.execute_query(query, context=context)
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── MLOps / Databricks endpoints ─────────────────────────────────────────────

@router.get("/mlops/status")
async def mlops_status():
    """
    Return the current MLOps pipeline status:
    - Which vector search backend is active (qdrant / databricks)
    - Databricks Model Serving endpoint health
    - Latest MLflow run metrics
    """
    backend = "databricks" if is_databricks_backend() else "qdrant"

    return {
        "vector_search_backend": backend,
        "serving_endpoint": get_serving_endpoint_status(),
        "latest_mlflow_run": get_mlflow_run_info(),
    }


@router.get("/mlops/pipeline")
async def mlops_pipeline_info():
    """
    Return the full MLOps pipeline configuration for the dashboard.
    Shows the data flow: CSV -> Preprocessing -> Embedding -> Delta/Qdrant -> Search
    """
    from backend.core.config import (
        EMBEDDING_MODEL_NAME, EMBEDDING_DIM, COLLECTION_FACILITIES,
        DATABRICKS_HOST, DATABRICKS_SERVING_ENDPOINT, VECTOR_SEARCH_BACKEND,
    )

    facilities = _get_facilities()
    with_coords = sum(1 for f in facilities if f["latitude"] is not None)

    return {
        "pipeline": {
            "data_source": "Virtue Foundation Ghana CSV",
            "preprocessing": {
                "total_facilities": len(facilities),
                "with_coordinates": with_coords,
                "steps": ["load_csv", "clean_parse", "deduplicate", "geocode", "build_documents"],
            },
            "embedding": {
                "model": EMBEDDING_MODEL_NAME,
                "dimension": EMBEDDING_DIM,
                "vectors": ["full_document", "clinical_detail", "specialties_context"],
                "normalization": "L2 (cosine-ready)",
            },
            "vector_store": {
                "active_backend": VECTOR_SEARCH_BACKEND,
                "collection": COLLECTION_FACILITIES,
                "databricks_host": DATABRICKS_HOST[:40] + "..." if DATABRICKS_HOST and len(DATABRICKS_HOST) > 40 else DATABRICKS_HOST,
                "serving_endpoint": DATABRICKS_SERVING_ENDPOINT,
            },
            "search": {
                "method": "reciprocal_rank_fusion",
                "rrf_k": 60,
                "multi_vector": True,
                "metadata_filtering": True,
            },
        },
    }
