"""
MedBridge AI — Supervisor Agent
=================================
Intent recognition + routing to sub-agents.
Classifies user queries and delegates to the appropriate agent(s):
  - Genie Chat (Text2SQL) for structured/aggregate queries
  - Vector Search for semantic/unstructured queries
  - Medical Reasoning for validation/anomaly detection
  - Geospatial for distance/coverage queries

Produces a trace log (citations) for every step.
"""

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(Enum):
    GENIE_CHAT = "genie_chat"
    VECTOR_SEARCH = "vector_search"
    MEDICAL_REASONING = "medical_reasoning"
    GEOSPATIAL = "geospatial"


class IntentType(Enum):
    # Category 1: Basic facility lookup
    COUNT_FACILITIES = "count_facilities"
    FACILITY_SERVICES = "facility_services"
    REGION_QUERY = "region_query"

    # Category 2: Geospatial
    NEARBY_FACILITIES = "nearby_facilities"
    COLD_SPOT_ANALYSIS = "cold_spot_analysis"

    # Category 3: Completeness / verification
    EQUIPMENT_VERIFICATION = "equipment_verification"

    # Category 4: Anomaly detection
    SUSPICIOUS_CLAIMS = "suspicious_claims"
    CORRELATION_ANALYSIS = "correlation_analysis"

    # Category 6: Workforce
    WORKFORCE_QUERY = "workforce_query"

    # Category 7-8: Resource distribution
    RESOURCE_DISTRIBUTION = "resource_distribution"
    DESERT_DETECTION = "desert_detection"

    # General
    GENERAL_SEARCH = "general_search"
    NGO_QUERY = "ngo_query"


@dataclass
class TraceStep:
    """One step in the agent reasoning trace (for citations)."""
    step_number: int
    agent: str
    action: str
    input_data: str
    output_summary: str
    data_sources: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0


@dataclass
class AgentResponse:
    """Response from the supervisor orchestration."""
    query: str
    intent: IntentType
    agents_used: List[AgentType]
    results: Dict[str, Any]
    trace: List[TraceStep]
    confidence: float = 0.0
    summary: str = ""


# ── Intent classification patterns ──────────────────────────────────────────

INTENT_PATTERNS = {
    IntentType.COUNT_FACILITIES: [
        r"how many (hospitals?|clinics?|facilities?)",
        r"count.*(hospitals?|clinics?|facilities?)",
        r"number of.*(hospitals?|clinics?|facilities?)",
        r"which region has the most",
    ],
    IntentType.FACILITY_SERVICES: [
        r"what services does .+ offer",
        r"what (can|does) .+ (do|provide|offer)",
        r"services (at|of|in) .+",
        r"capabilities of",
    ],
    IntentType.REGION_QUERY: [
        r"(hospitals?|clinics?|facilities?) in .+ (region|area|city|district)",
        r"in .+ (that|which) (can|do|have|perform)",
        r"(clinics?|hospitals?) .+ in .+",
    ],
    IntentType.NEARBY_FACILITIES: [
        r"within \d+ ?km",
        r"nearest|closest",
        r"near (me|here|location)",
        r"distance",
        r"travel time",
    ],
    IntentType.COLD_SPOT_ANALYSIS: [
        r"cold spot",
        r"gap.*(coverage|service|care)",
        r"medical desert",
        r"no (facility|hospital|clinic) (for|within|near)",
        r"underserved",
        r"lack of (access|coverage)",
    ],
    IntentType.EQUIPMENT_VERIFICATION: [
        r"equipment.*(match|verify|check)",
        r"claiming .+ but (lack|missing|without)",
        r"subspecialty .+ equipment",
        r"minimum equipment",
    ],
    IntentType.SUSPICIOUS_CLAIMS: [
        r"suspicious|unrealistic|fraud",
        r"claiming .+ but",
        r"anomal(y|ies|ous)",
        r"mismatch|inconsisten",
        r"shouldn'?t move together",
        r"high.*breadth.*minimal",
    ],
    IntentType.CORRELATION_ANALYSIS: [
        r"correlat(e|ion)",
        r"relationship between",
        r"pattern",
        r"bed.to.*ratio",
    ],
    IntentType.WORKFORCE_QUERY: [
        r"workforce|doctors?|staff|specialist",
        r"(where|which).*(practicing|working)",
        r"anesthetist|surgeon|ophthalmologist",
        r"visiting.*permanent",
    ],
    IntentType.RESOURCE_DISTRIBUTION: [
        r"distribution|concentration",
        r"oversupply|scarcity",
        r"single.point.*failure",
        r"depend.*few facilit",
    ],
    IntentType.DESERT_DETECTION: [
        r"desert|gap.*need",
        r"no organiz.* working",
        r"where.*need.*but",
        r"unmet need",
    ],
    IntentType.NGO_QUERY: [
        r"\bngo\b",
        r"non.?governmental",
        r"(foundation|organization|charity)",
        r"volunteer",
        r"overlap.*service",
    ],
}

# ── Routing table: intent → agents ──────────────────────────────────────────

ROUTING_TABLE = {
    IntentType.COUNT_FACILITIES: [AgentType.GENIE_CHAT],
    IntentType.FACILITY_SERVICES: [AgentType.VECTOR_SEARCH],
    IntentType.REGION_QUERY: [AgentType.GENIE_CHAT, AgentType.VECTOR_SEARCH],
    IntentType.NEARBY_FACILITIES: [AgentType.GENIE_CHAT, AgentType.GEOSPATIAL],
    IntentType.COLD_SPOT_ANALYSIS: [AgentType.GENIE_CHAT, AgentType.GEOSPATIAL, AgentType.MEDICAL_REASONING],
    IntentType.EQUIPMENT_VERIFICATION: [AgentType.VECTOR_SEARCH, AgentType.MEDICAL_REASONING],
    IntentType.SUSPICIOUS_CLAIMS: [AgentType.GENIE_CHAT, AgentType.MEDICAL_REASONING],
    IntentType.CORRELATION_ANALYSIS: [AgentType.GENIE_CHAT],
    IntentType.WORKFORCE_QUERY: [AgentType.GENIE_CHAT, AgentType.VECTOR_SEARCH],
    IntentType.RESOURCE_DISTRIBUTION: [AgentType.GENIE_CHAT, AgentType.MEDICAL_REASONING],
    IntentType.DESERT_DETECTION: [AgentType.GENIE_CHAT, AgentType.GEOSPATIAL, AgentType.MEDICAL_REASONING],
    IntentType.NGO_QUERY: [AgentType.VECTOR_SEARCH, AgentType.GENIE_CHAT],
    IntentType.GENERAL_SEARCH: [AgentType.VECTOR_SEARCH],
}


class SupervisorAgent:
    """
    Routes user queries to the appropriate sub-agents.
    Maintains a trace log for citation transparency.
    """

    def __init__(self):
        self.trace: List[TraceStep] = []
        self._step_counter = 0

    def reset_trace(self):
        self.trace = []
        self._step_counter = 0

    def add_trace_step(
        self,
        agent: str,
        action: str,
        input_data: str,
        output_summary: str,
        data_sources: Optional[List[str]] = None,
        duration_ms: float = 0.0,
    ) -> TraceStep:
        self._step_counter += 1
        step = TraceStep(
            step_number=self._step_counter,
            agent=agent,
            action=action,
            input_data=input_data,
            output_summary=output_summary,
            data_sources=data_sources or [],
            duration_ms=duration_ms,
        )
        self.trace.append(step)
        return step

    def classify_intent(self, query: str) -> IntentType:
        """Classify the user's query into an intent type using pattern matching."""
        query_lower = query.lower().strip()

        scores: Dict[IntentType, int] = {}
        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            if score > 0:
                scores[intent] = score

        if not scores:
            return IntentType.GENERAL_SEARCH

        # Return highest-scoring intent
        return max(scores, key=scores.get)

    def get_routing(self, intent: IntentType) -> List[AgentType]:
        """Get the list of agents to invoke for a given intent."""
        return ROUTING_TABLE.get(intent, [AgentType.VECTOR_SEARCH])

    def route_query(self, query: str) -> tuple:
        """
        Main entry point: classify intent and determine routing.
        Returns (intent, agents_to_invoke).
        """
        self.reset_trace()

        t0 = time.time()
        intent = self.classify_intent(query)
        agents = self.get_routing(intent)
        duration = (time.time() - t0) * 1000

        self.add_trace_step(
            agent="supervisor",
            action="classify_intent_and_route",
            input_data=query,
            output_summary=f"Intent: {intent.value} → Agents: {[a.value for a in agents]}",
            duration_ms=duration,
        )

        return intent, agents

    def get_trace_report(self) -> List[Dict]:
        """Return trace as a list of dicts for serialization."""
        return [
            {
                "step": s.step_number,
                "agent": s.agent,
                "action": s.action,
                "input": s.input_data[:200],
                "output": s.output_summary[:300],
                "sources": s.data_sources,
                "duration_ms": round(s.duration_ms, 2),
            }
            for s in self.trace
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Convenience
# ─────────────────────────────────────────────────────────────────────────────

def create_supervisor() -> SupervisorAgent:
    return SupervisorAgent()


if __name__ == "__main__":
    supervisor = create_supervisor()

    test_queries = [
        "How many hospitals have cardiology?",
        "What services does Korle Bu Teaching Hospital offer?",
        "Are there any clinics in Kumasi that do cataract surgery?",
        "Hospitals treating malaria within 50km of Tamale?",
        "Largest cold spots where emergency surgery is absent?",
        "Facilities claiming neurosurgery but lacking CT scanner?",
        "Which NGOs are working on HIV/AIDS in Ghana?",
        "Where is the workforce for anesthesia practicing?",
        "Procedures depending on very few facilities?",
        "Where are the medical deserts in Northern Ghana?",
    ]

    print("═══ Supervisor Agent — Intent Classification & Routing ═══\n")
    for q in test_queries:
        intent, agents = supervisor.route_query(q)
        agent_names = [a.value for a in agents]
        print(f"  Q: {q}")
        print(f"  → Intent: {intent.value}")
        print(f"  → Route:  {agent_names}\n")
