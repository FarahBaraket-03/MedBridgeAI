"""
MedBridge AI — LangGraph Orchestration
========================================
Defines the multi-agent workflow as a LangGraph StateGraph.

Flow:
  1. Supervisor classifies intent → creates execution plan
  2. Conditional routing → one or more agent nodes
  3. Aggregator combines results + citations
  4. END → return final response
"""

from __future__ import annotations

import logging
import operator
import time
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.agents.supervisor.agent import SupervisorAgent
from backend.agents.genie.agent import GenieChatAgent
from backend.agents.vector_search.agent import VectorSearchAgent
from backend.agents.medical_reasoning.agent import MedicalReasoningAgent
from backend.agents.geospatial.agent import GeospatialAgent
from backend.agents.planning.agent import PlanningAgent
from backend.core.llm import synthesize_response, classify_intent_llm

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  STATE SCHEMA
# ═══════════════════════════════════════════════════════════════════════════

class MedBridgeState(TypedDict):
    """Shared state flowing through the LangGraph workflow."""
    query: str
    context: Dict[str, Any]
    intent: str
    required_agents: List[str]
    execution_flow: str
    current_agent_index: int
    plan_steps: List[str]
    agent_results: Annotated[list, operator.add]
    trace: Annotated[list, operator.add]
    citations: Annotated[list, operator.add]
    final_response: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
#  SINGLETON AGENTS (avoid re-loading data on every call)
# ═══════════════════════════════════════════════════════════════════════════

_agent_cache: Dict[str, Any] = {}


def _get_supervisor() -> SupervisorAgent:
    if "supervisor" not in _agent_cache:
        _agent_cache["supervisor"] = SupervisorAgent()
    return _agent_cache["supervisor"]


def _get_genie() -> GenieChatAgent:
    if "genie" not in _agent_cache:
        _agent_cache["genie"] = GenieChatAgent()
    return _agent_cache["genie"]


def _get_vector_search() -> VectorSearchAgent:
    if "vector_search" not in _agent_cache:
        _agent_cache["vector_search"] = VectorSearchAgent()
    return _agent_cache["vector_search"]


def _get_medical_reasoning() -> MedicalReasoningAgent:
    if "medical_reasoning" not in _agent_cache:
        _agent_cache["medical_reasoning"] = MedicalReasoningAgent()
    return _agent_cache["medical_reasoning"]


def _get_geospatial() -> GeospatialAgent:
    if "geospatial" not in _agent_cache:
        _agent_cache["geospatial"] = GeospatialAgent()
    return _agent_cache["geospatial"]


def _get_planning() -> PlanningAgent:
    if "planning" not in _agent_cache:
        _agent_cache["planning"] = PlanningAgent()
    return _agent_cache["planning"]


# ═══════════════════════════════════════════════════════════════════════════
#  GRAPH NODES
# ═══════════════════════════════════════════════════════════════════════════

def supervisor_node(state: MedBridgeState) -> dict:
    """Entry node: classify intent and create execution plan.
    Uses regex first, falls back to LLM for ambiguous queries.
    """
    t0 = time.time()
    supervisor = _get_supervisor()
    plan = supervisor.create_execution_plan(state["query"])

    # If supervisor returned a generic/fallback result, try LLM classification
    llm_used = False
    if plan.primary_intent in ("general", "unknown") or not plan.required_agents:
        llm_result = classify_intent_llm(state["query"])
        if llm_result and llm_result.get("agents"):
            plan.required_agents = llm_result["agents"]
            plan.primary_intent = llm_result.get("intent", plan.primary_intent)
            plan.steps = [llm_result.get("reasoning", "LLM-classified intent")]
            llm_used = True

    trace_entry = {
        "agent": "supervisor",
        "action": "classify_intent",
        "intent": plan.primary_intent,
        "confidence": plan.confidence,
        "agents": plan.required_agents,
        "flow": plan.execution_flow,
        "steps": plan.steps,
        "llm_enhanced": llm_used,
        "duration_ms": round((time.time() - t0) * 1000, 2),
    }

    return {
        "intent": plan.primary_intent,
        "required_agents": plan.required_agents,
        "execution_flow": plan.execution_flow,
        "current_agent_index": 0,
        "plan_steps": plan.steps,
        "trace": [trace_entry],
    }


def genie_node(state: MedBridgeState) -> dict:
    """Text2SQL agent node."""
    t0 = time.time()
    genie = _get_genie()
    result = genie.execute_query(state["query"])
    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    # Advance agent index
    idx = state.get("current_agent_index", 0)
    return {
        "agent_results": [{"agent": "genie", "data": result}],
        "trace": [{
            "agent": "genie",
            "action": result.get("action", "text2sql"),
            "duration_ms": result["duration_ms"],
            "summary": f"Found {result.get('count', len(result.get('results', [])))} results",
        }],
        "citations": result.get("citations", []),
        "current_agent_index": idx + 1,
    }


def vector_search_node(state: MedBridgeState) -> dict:
    """Semantic search agent node.

    Includes a self-correction loop: if the first search returns zero
    results (likely because metadata filters were too restrictive), a
    second search is run *without* filters to ensure the user gets
    meaningful output.
    """
    t0 = time.time()
    vs = _get_vector_search()
    result = vs.search(state["query"])

    # ── Feedback loop: retry without filters if zero results ──
    retried = False
    if result.get("count", 0) == 0 and result.get("filters_applied"):
        logger.info("Vector search returned 0 results with filters %s — retrying unfiltered",
                     result["filters_applied"])
        # Retry with the raw query (no metadata filters)
        result_retry = vs.search(state["query"].split(" in ")[0].split(" near ")[0])
        if result_retry.get("count", 0) > 0:
            result = result_retry
            result["_note"] = "Retried without location filter (original returned 0 results)"
            retried = True

    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    idx = state.get("current_agent_index", 0)
    return {
        "agent_results": [{"agent": "vector_search", "data": result}],
        "trace": [{
            "agent": "vector_search",
            "action": result.get("action", "semantic_search"),
            "search_method": result.get("search_method", "single_vector"),
            "vectors_queried": result.get("vectors_queried", []),
            "vector_weights": result.get("vector_weights", {}),
            "vector_used": result.get("primary_vector", result.get("vector_used", "full_document")),
            "duration_ms": result["duration_ms"],
            "retried_unfiltered": retried,
            "summary": f"Found {len(result.get('results', []))} matching facilities" + (" (retried)" if retried else ""),
        }],
        "citations": result.get("citations", []),
        "current_agent_index": idx + 1,
    }


def medical_reasoning_node(state: MedBridgeState) -> dict:
    """Medical reasoning & validation node."""
    t0 = time.time()
    mr = _get_medical_reasoning()

    # Build context from prior agent results so medical reasoning can use them
    prior_context = {}
    for ar in state.get("agent_results", []):
        agent_name = ar.get("agent", "")
        data = ar.get("data", {})
        if agent_name == "geospatial":
            # Pass geospatial findings for medical reasoning to incorporate
            prior_context["geospatial_action"] = data.get("action", "")
            prior_context["geospatial_specialty"] = data.get("specialty")
            if data.get("deserts"):
                prior_context["deserts"] = data["deserts"]
            if data.get("worst_cold_spots"):
                prior_context["cold_spots"] = data["worst_cold_spots"]
        elif agent_name == "genie":
            prior_context["genie_count"] = data.get("count")
            prior_context["genie_facilities"] = data.get("facilities", [])[:10]

    result = mr.execute_query(state["query"], context=prior_context)
    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    idx = state.get("current_agent_index", 0)
    return {
        "agent_results": [{"agent": "medical_reasoning", "data": result}],
        "trace": [{
            "agent": "medical_reasoning",
            "action": result.get("action", "analysis"),
            "duration_ms": result["duration_ms"],
            "summary": _summarize_medical(result),
        }],
        "citations": result.get("citations", []),
        "current_agent_index": idx + 1,
    }


def _summarize_medical(result: dict) -> str:
    action = result.get("action", "")
    if action == "constraint_validation":
        return f"Validated {result.get('total_checked', 0)} facilities, {result.get('facilities_with_issues', 0)} flagged"
    if action == "anomaly_detection":
        return f"Scanned {result.get('total_checked', 0)} facilities, {result.get('anomalies_found', 0)} anomalies"
    if action == "red_flag_detection":
        return f"Scanned {result.get('total_scanned', 0)} facilities, {result.get('facilities_flagged', 0)} flagged"
    if action == "coverage_gap_analysis":
        return f"Found {result.get('gaps_found', 0)} coverage gaps for {result.get('specialty', 'all')}"
    if action == "single_point_of_failure":
        return f"Found {result.get('critical_specialties', 0)} critical specialties"
    return "Analysis complete"


def geospatial_node(state: MedBridgeState) -> dict:
    """Geospatial analysis node."""
    t0 = time.time()
    geo = _get_geospatial()
    context = state.get("context") or {}
    result = geo.execute_query(state["query"], context=context)
    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    idx = state.get("current_agent_index", 0)
    return {
        "agent_results": [{"agent": "geospatial", "data": result}],
        "trace": [{
            "agent": "geospatial",
            "action": result.get("action", "geospatial"),
            "duration_ms": result["duration_ms"],
            "summary": _summarize_geospatial(result),
        }],
        "citations": [],
        "current_agent_index": idx + 1,
    }


def _summarize_geospatial(result: dict) -> str:
    action = result.get("action", "")
    if action == "facilities_within_radius":
        return f"Found {result.get('total_found', 0)} facilities within {result.get('radius_km', 0)} km"
    if action == "nearest_facilities":
        return f"Found {len(result.get('facilities', []))} nearest facilities"
    if action == "coverage_gap_analysis":
        return f"Coverage: {result.get('coverage_percentage', 0)}%, {result.get('cold_spots_found', 0)} cold spots"
    if action == "medical_desert_detection":
        return f"Found {result.get('deserts_found', 0)} medical deserts"
    if action == "regional_equity_analysis":
        return f"Analyzed {result.get('total_regions', 0)} regions"
    return "Geospatial analysis complete"


def planning_node(state: MedBridgeState) -> dict:
    """Planning & coordination node."""
    t0 = time.time()
    planner = _get_planning()
    context = state.get("context") or {}
    result = planner.execute_query(state["query"], context=context)
    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    idx = state.get("current_agent_index", 0)
    return {
        "agent_results": [{"agent": "planning", "data": result}],
        "trace": [{
            "agent": "planning",
            "action": result.get("scenario", "planning"),
            "duration_ms": result["duration_ms"],
            "summary": result.get("title", "Plan generated"),
        }],
        "citations": [],
        "current_agent_index": idx + 1,
    }


def aggregator_node(state: MedBridgeState) -> dict:
    """Combine results from all agents into a final response with LLM synthesis."""
    t0 = time.time()
    agent_results = state.get("agent_results", [])
    trace = state.get("trace", [])
    citations = state.get("citations", [])

    # Build a structured final response
    if len(agent_results) == 1:
        primary = agent_results[0]["data"]
    else:
        primary = {
            "multi_agent_response": True,
            "agents_used": [r["agent"] for r in agent_results],
            "results": {r["agent"]: r["data"] for r in agent_results},
        }

    # ── Merge all map-displayable facilities from every agent ──────
    def _first_valid(*values):
        """Return the first non-None value."""
        for v in values:
            if v is not None:
                return v
        return None

    all_map_facilities = []
    seen_names = set()
    for ar in agent_results:
        data = ar.get("data", {})
        # Collect from all known list keys
        for key in ["facilities", "results", "flagged_facilities", "stops",
                     "placements", "suggestions", "worst_cold_spots",
                     "alternatives", "regions", "anomalies", "gaps", "deserts"]:
            items = data.get(key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Normalize coordinate field names (use None-safe check, not or, since 0 is valid)
                lat = _first_valid(item.get("latitude"), item.get("lat"), item.get("center_lat"), item.get("suggested_lat"), item.get("grid_lat"))
                lng = _first_valid(item.get("longitude"), item.get("lng"), item.get("center_lng"), item.get("suggested_lng"), item.get("grid_lng"))
                name = item.get("name") or item.get("facility") or item.get("region") or ""
                if lat is not None and lng is not None and name not in seen_names:
                    seen_names.add(name)
                    all_map_facilities.append({
                        "name": name,
                        "latitude": lat,
                        "longitude": lng,
                        "city": item.get("city") or item.get("address_city"),
                        "region": item.get("region") or item.get("address_stateOrRegion"),
                        "specialties": item.get("specialties", []),
                        "type": item.get("type") or item.get("facilityTypeId"),
                        "distance_km": item.get("distance_km") or item.get("distance_from_prev_km"),
                    })
        # Also grab single-facility fields
        for single_key in ["primary_facility", "backup_facility"]:
            pf = data.get(single_key)
            if isinstance(pf, dict):
                lat = _first_valid(pf.get("latitude"), pf.get("lat"))
                lng = _first_valid(pf.get("longitude"), pf.get("lng"))
                name = pf.get("facility") or pf.get("name") or ""
                if lat is not None and lng is not None and name not in seen_names:
                    seen_names.add(name)
                    all_map_facilities.append({
                        "name": name, "latitude": lat, "longitude": lng,
                        "city": pf.get("city"), "region": pf.get("region"),
                        "specialties": pf.get("specialties", []),
                        "type": pf.get("type"), "distance_km": pf.get("distance_km"),
                    })

    # Attach merged facilities to primary response
    if isinstance(primary, dict):
        primary["_map_facilities"] = all_map_facilities

    # ── LLM Synthesis: generate plain-language summary ──────────
    summary = ""
    try:
        summary = synthesize_response(
            query=state["query"],
            agent_results=agent_results,
            trace=trace,
            citations=citations,
            intent=state.get("intent", ""),
        )
    except Exception as e:
        logger.warning(f"LLM synthesis failed in aggregator: {e}")
        summary = ""

    synthesis_ms = round((time.time() - t0) * 1000, 2)

    # Add synthesis trace entry
    trace_with_synthesis = trace + [{
        "agent": "aggregator",
        "action": "synthesize_response",
        "duration_ms": synthesis_ms,
        "summary": "Generated natural language summary" if summary else "Synthesis skipped",
        "llm_used": bool(summary),
    }]

    final = {
        "query": state["query"],
        "intent": state.get("intent", "general"),
        "response": primary,
        "summary": summary,
        "trace": trace_with_synthesis,
        "citations": citations,
        "agents_used": [r["agent"] for r in agent_results],
        "total_duration_ms": sum(t.get("duration_ms", 0) for t in trace_with_synthesis),
    }

    return {"final_response": final}


# ═══════════════════════════════════════════════════════════════════════════
#  CONDITIONAL ROUTING
# ═══════════════════════════════════════════════════════════════════════════

def _route_after_supervisor(state: MedBridgeState) -> str:
    """Route to the first agent in the execution plan."""
    agents = state.get("required_agents", [])
    if not agents:
        return "aggregator"
    return agents[0]


def _route_next_agent(state: MedBridgeState) -> str:
    """After an agent completes, route to the next one or aggregate."""
    agents = state.get("required_agents", [])
    idx = state.get("current_agent_index", 0)
    if idx < len(agents):
        return agents[idx]
    return "aggregator"


# ═══════════════════════════════════════════════════════════════════════════
#  BUILD THE GRAPH
# ═══════════════════════════════════════════════════════════════════════════

AGENT_NODES = {
    "genie": genie_node,
    "vector_search": vector_search_node,
    "medical_reasoning": medical_reasoning_node,
    "geospatial": geospatial_node,
    "planning": planning_node,
}


def build_workflow() -> Any:
    """Build and compile the LangGraph StateGraph workflow."""
    graph = StateGraph(MedBridgeState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    for name, fn in AGENT_NODES.items():
        graph.add_node(name, fn)
    graph.add_node("aggregator", aggregator_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Supervisor → conditional routing to first agent
    graph.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "genie": "genie",
            "vector_search": "vector_search",
            "medical_reasoning": "medical_reasoning",
            "geospatial": "geospatial",
            "planning": "planning",
            "aggregator": "aggregator",
        },
    )

    # Each agent → router → next agent or aggregator
    for agent_name in AGENT_NODES:
        graph.add_conditional_edges(
            agent_name,
            _route_next_agent,
            {
                "genie": "genie",
                "vector_search": "vector_search",
                "medical_reasoning": "medical_reasoning",
                "geospatial": "geospatial",
                "planning": "planning",
                "aggregator": "aggregator",
            },
        )

    # Aggregator → END
    graph.add_edge("aggregator", END)

    return graph.compile()


# ═══════════════════════════════════════════════════════════════════════════
#  CONVENIENCE RUNNER
# ═══════════════════════════════════════════════════════════════════════════

_workflow = None


def run_query(query: str, context: Optional[Dict] = None) -> Dict:
    """Execute a query through the full LangGraph workflow."""
    global _workflow
    if _workflow is None:
        _workflow = build_workflow()

    initial_state: MedBridgeState = {
        "query": query,
        "context": context or {},
        "intent": "",
        "required_agents": [],
        "execution_flow": "",
        "current_agent_index": 0,
        "plan_steps": [],
        "agent_results": [],
        "trace": [],
        "citations": [],
        "final_response": {},
    }

    result = _workflow.invoke(initial_state)
    return result.get("final_response", result)
