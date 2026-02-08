# MedBridge AI — Architecture & Flow Plan
## Coherent End-to-End System Design

---

## Current State (What's Built)

```
src/
├── config.py                    # Shared config (Qdrant, model, medical constants)
├── data_preprocessing.py        # CSV → clean → dedup → document builder
├── vectorize_and_store.py       # Multi-representation embeddings → Qdrant Cloud
├── api.py                       # FastAPI backend (routes queries to agents)
├── test_queries.py              # 18 test queries covering MUST HAVE requirements
└── agents/
    ├── __init__.py              # SupervisorAgent (intent classification + routing)
    ├── supervisor.py            # Re-export
    ├── genie_chat.py            # Text2SQL agent (Pandas operations)
    └── vector_search.py         # Semantic search (3 named vectors + filtering)

frontend/
└── index.html                   # Unified dashboard (query + map + charts + reasoning)

data/
└── Virtue Foundation Ghana v0.3 - Sheet1.csv   # 987 rows → 797 unique

output/
├── virtue_ai_interface.html     # Original query interface (reference)
└── virtue_ai_routing_map.html   # Original routing map (reference)
```

### Data Pipeline Flow
```
CSV (987 rows) → clean_and_parse() → deduplicate(797) → build_documents()
    → build_multi_representations() → embed(3 vectors × 797) → Qdrant Cloud
          ↓                                    ↓                     ↓
    full_document (384d)    clinical_detail (384d)    specialties_context (384d)
```

### Query Flow
```
User Query → FastAPI /api/query
    → keyword heuristic (genie_signals check)
        ├── Genie Chat  → Pandas DataFrame operations → structured result
        └── Vector Search → Qdrant multi-vector search → ranked results
    → JSON response → Frontend renders (steps + metrics + results)
```

---

## Suggested Modifications for Coherent Flow

### 1. Supervisor Agent Should Be the Single Router

**Current**: `api.py` duplicates routing logic with simple keyword matching.
**Fix**: Route through `SupervisorAgent.classify_intent()` instead.

```python
# In api.py, replace keyword heuristic with:
from src.agents import SupervisorAgent
supervisor = SupervisorAgent()
intent = supervisor.classify_intent(query)
agent_type = supervisor.ROUTING_TABLE[intent]
# Then dispatch to appropriate agent
```

### 2. Add Medical Reasoning Agent (Priority: HIGH)

This agent handles the hackathon's "anomaly detection" and "constraint validation" questions (35% of scoring). It should:

- **Claim validation**: Does a facility claiming neurosurgery have the required equipment (CT, MRI, ICU)?
- **Bed-doctor ratio anomalies**: Flag facilities with implausible ratios
- **Procedure-equipment consistency**: Cross-check procedures against equipment lists
- **Infrastructure gap detection**: Identify regions missing critical specialties

```python
# src/agents/medical_reasoning.py
class MedicalReasoningAgent:
    def validate_facility_claims(self, facility_id) -> Dict  # constraint check
    def detect_anomalies(self) -> List[Dict]                  # bulk scan
    def identify_medical_deserts(self, specialty) -> Dict     # gap analysis
    def single_point_of_failure(self, procedure) -> Dict      # resilience
```

### 3. Add Geospatial Agent (Priority: MEDIUM)

The dataset has `latitude`/`longitude` columns. Use them for:

- **Distance queries**: "Hospitals within 50km of Tamale"
- **Coverage analysis**: Which areas have >100km to nearest hospital?
- **Medical desert mapping**: Geographic cold spots per specialty

```python
# src/agents/geospatial.py
from math import radians, sin, cos, sqrt, atan2

class GeospatialAgent:
    def facilities_within_radius(self, lat, lng, radius_km, specialty=None)
    def coverage_gaps(self, specialty) -> List[Dict]  # Voronoi-style
    def nearest_facility(self, lat, lng, specialty=None)
```

### 4. Citation Tracing (Stretch Goal — Worth 5-10% Bonus)

Every agent response should include `citations` linking back to specific CSV rows:

```python
@dataclass
class Citation:
    pk_unique_id: str      # row identity
    field_used: str        # which column was read
    value: Any             # what value was extracted
    confidence: float      # 0-1 certainty
    agent_step: int        # which reasoning step used this
```

This is already partially in the `SupervisorAgent` (`TraceStep` dataclass). Extend it.

### 5. Frontend Improvements

| Feature | Priority | Description |
|---------|----------|-------------|
| Real map markers from API | HIGH | Load actual facility lat/lng from Qdrant instead of hardcoded |
| Route planning | MEDIUM | Add Leaflet Routing Machine for patient routing scenarios |
| Medical desert visualization | MEDIUM | Red circles on map for coverage gaps |
| Result → Map highlighting | HIGH | Click a result card → zoom to that facility |
| Export to PDF/CSV | LOW | Download analysis results |

### 6. MLflow Integration (If Using Databricks)

The challenge mentions MLflow for experiment tracking. Add tracing:

```python
import mlflow

@mlflow.trace
def handle_query(query: str):
    with mlflow.start_span("supervisor"):
        intent = supervisor.classify(query)
    with mlflow.start_span(f"agent_{intent}"):
        result = dispatch(intent, query)
    return result
```

---

## Recommended Implementation Order

| Step | Task | Time | Impact |
|------|------|------|--------|
| 1 | Wire Supervisor as real router in api.py | 30 min | Coherence |
| 2 | Build Medical Reasoning agent | 2 hr | 35% scoring |
| 3 | Build Geospatial agent (haversine) | 1 hr | Social Impact |
| 4 | Add citation tracing to all agents | 1 hr | Stretch bonus |
| 5 | Load real lat/lng markers on map | 30 min | UX |
| 6 | Add medical desert map overlay | 30 min | Social Impact |
| 7 | MLflow tracing integration | 1 hr | Databricks bonus |

---

## MUST HAVE Coverage Checklist

| ID | Question | Agent | Status |
|----|----------|-------|--------|
| 1.1 | How many hospitals have cardiology? | Genie ✓ | ✅ Working |
| 1.2 | Hospitals in [region] performing [procedure]? | Genie ✓ | ✅ Working |
| 1.3 | What services does [Facility] offer? | Vector ✓ | ✅ Working |
| 1.4 | Clinics in [Area] that do [Service]? | Vector ✓ | ✅ Working |
| 1.5 | Which region has most [Type] hospitals? | Genie ✓ | ✅ Working |
| 2.1 | Hospitals treating [X] within [Y] km? | Geospatial | ⬜ Needs Geo agent |
| 2.3 | Geographic cold spots? | Geospatial | ⬜ Needs Geo agent |
| 4.4 | Unrealistic procedure claims? | Medical Reasoning | ⬜ Needs MR agent |
| 4.7 | Facility characteristic correlations? | Genie ✓ | ✅ Working |
| 4.8 | High procedure breadth vs minimal infra? | Medical Reasoning | ⬜ Needs MR agent |
| 4.9 | Things that shouldn't move together? | Medical Reasoning | ⬜ Needs MR agent |
| 6.1 | Where is specialist workforce? | Vector ✓ | ✅ Working |
| 7.5 | Procedures depending on few facilities? | Genie ✓ | ✅ Working |
| 7.6 | Oversupply vs scarcity? | Genie ✓ | ✅ Working (region_aggregation) |
| 8.3 | Gaps with no organizations despite need? | Medical Reasoning + Geo | ⬜ Needs both |

**Current coverage: 9/15 MUST HAVEs (60%)**
**With Medical Reasoning + Geospatial: 15/15 (100%)**

---

## Key Architectural Principle

> **Route, don't duplicate.**
> The Supervisor classifies intent ONCE, dispatches to the right agent,
> and the agent returns structured results with citations.
> The frontend renders based on `agent_type`, not query content.
