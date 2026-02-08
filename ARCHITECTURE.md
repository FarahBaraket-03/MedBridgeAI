# MedBridge AI — Architecture

> Complete technical architecture of the multi-agent healthcare intelligence platform.

---

## Table of Contents

1. [Global Architecture](#global-architecture)
2. [Request Lifecycle](#request-lifecycle)
3. [Orchestration Layer](#orchestration-layer)
4. [Supervisor Agent](#supervisor-agent)
5. [Genie Agent](#genie-agent)
6. [Vector Search Agent](#vector-search-agent)
7. [Medical Reasoning Agent](#medical-reasoning-agent)
8. [Geospatial Agent](#geospatial-agent)
9. [Planning Agent](#planning-agent)
10. [Core Services](#core-services)
11. [Data Pipeline](#data-pipeline)
12. [Frontend Architecture](#frontend-architecture)
13. [API Layer](#api-layer)

---

## Global Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React 19)                             │
│  App.jsx ─── QueryInput ─── ResultsPanel ─── MapView ─── ExplainPanel       │
│     │            │               │              │             │              │
│     └────── api/client.js ──────────────────────┘             │              │
│                  │  POST /api/query                            │              │
└──────────────────┼────────────────────────────────────────────┘──────────────┘
                   │
┌──────────────────┼──────────────────────────────────────────────────────────┐
│                  ▼           API LAYER (FastAPI)                             │
│  main.py ──► routes.py ──► /api/query, /api/facilities, /api/stats, ...    │
│     │           │                                                           │
│     │           ▼                                                           │
│     │    ┌─────────────────────────────────────────────────────────┐        │
│     │    │           ORCHESTRATION (LangGraph StateGraph)          │        │
│     │    │                                                         │        │
│     │    │   ┌────────────┐     ┌──────────────────────┐          │        │
│     │    │   │ Supervisor │────►│   Router (Conditional │          │        │
│     │    │   │   Node     │     │   edges to agents)    │          │        │
│     │    │   └────────────┘     └──────────┬───────────┘          │        │
│     │    │                                  │                      │        │
│     │    │        ┌─────────────────────────┼─────────────┐       │        │
│     │    │        ▼         ▼         ▼     ▼       ▼     │       │        │
│     │    │   ┌───────┐ ┌────────┐ ┌─────┐ ┌────┐ ┌─────┐ │       │        │
│     │    │   │ Genie │ │Vector  │ │Med  │ │Geo │ │Plan │ │       │        │
│     │    │   │       │ │Search  │ │Reas.│ │    │ │ning │ │       │        │
│     │    │   └───┬───┘ └───┬────┘ └──┬──┘ └─┬──┘ └──┬──┘ │       │        │
│     │    │       └─────────┴────┬────┴──────┴───────┘     │       │        │
│     │    │                      ▼                          │       │        │
│     │    │              ┌──────────────┐   retry if       │       │        │
│     │    │              │  Aggregator  │◄──0 results      │       │        │
│     │    │              │  + LLM Synth │                   │       │        │
│     │    │              └──────┬───────┘                   │       │        │
│     │    └─────────────────────┼───────────────────────────┘       │        │
│     │                          ▼                                    │        │
│     │                    JSON Response                               │        │
└─────┼───────────────────────────────────────────────────────────────┘        │
      │                                                                        │
┌─────┼────────────────────────────────────────────────────────────────────────┘
│     │                     CORE SERVICES                                      │
│     │                                                                        │
│  config.py ── llm.py ── vectorstore.py ── geocoding.py ── preprocessing.py  │
│                              │                                               │
│                     quantum.py ── databricks.py                              │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────┐           │
│  │ Qdrant Cloud    │  │ Groq Cloud      │  │ SentenceTransformer│           │
│  │ (384d × 3 vecs) │  │ (LLM synthesis) │  │ (all-MiniLM-L6-v2)│           │
│  └─────────────────┘  └─────────────────┘  └────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| Orchestration | `orchestration/graph.py` | 544 | LangGraph StateGraph with 7 nodes, conditional routing, self-correction |
| Supervisor | `agents/supervisor/agent.py` | 550 | Intent classification via embeddings + regex + LLM fallback |
| Genie | `agents/genie/agent.py` | 310 | Structured Pandas queries with negation and IQR anomalies |
| Vector Search | `agents/vector_search/agent.py` | 220 | 3-vector RRF semantic search with Qdrant |
| Medical Reasoning | `agents/medical_reasoning/agent.py` | 572 | Constraint validation, Isolation Forest + Mahalanobis anomalies |
| Geospatial | `agents/geospatial/agent.py` | 543 | BallTree spatial index, grid-based deserts, Mahalanobis equity |
| Planning | `agents/planning/agent.py` | 722 | Capability scoring, 2-opt TSP, QUBO quantum routing, maximin |
| LLM | `core/llm.py` | 347 | Groq client, synthesis prompt, token-aware truncation |
| Vectorstore | `core/vectorstore.py` | 260 | Qdrant collection management, query templates |
| Geocoding | `core/geocoding.py` | 500 | 220 Ghana cities, 3-stage lookup (exact/boundary/fuzzy) |
| Preprocessing | `core/preprocessing.py` | 210 | CSV → clean → dedup → documents (987 → 797 rows) |
| Config | `core/config.py` | 140 | Constants, specialty maps, API keys, vector names |
| Quantum | `core/quantum.py` | 260 | QUBO TSP formulation, Qiskit eigensolver, brute-force |
| Routes | `api/routes.py` | 494 | 10 FastAPI endpoints |
| Main | `api/main.py` | 45 | CORS, lifespan, app init |

---

## Request Lifecycle

```
1. POST /api/query { query: "Which facilities handle trauma near Kumasi?" }
       │
2.     ▼  routes.py validates (max 2000 chars), calls run_graph(query)
       │
3.     ▼  graph.py builds initial GraphState:
       │     query="...", agents_to_run=[], current_agent_index=0,
       │     agent_results={}, all_facilities=[], plan={}, summary="",
       │     intent="", confidence=0.0, trace=[]
       │
4.     ▼  supervisor_node: classifies intent → "distance_query" (conf: 0.92)
       │     ROUTING_TABLE maps → agents: [geospatial], flow: single
       │     Writes trace step, updates state
       │
5.     ▼  route_first_agent: conditional edge → geospatial_node
       │
6.     ▼  geospatial_node: geocodes "Kumasi" → (6.69, -1.62)
       │     BallTree radius search within 50km
       │     Returns {action, results[], count, radius_km, center}
       │
7.     ▼  route_next_agent: index exhausted → aggregator
       │
8.     ▼  aggregator_node: merges facilities with coordinates
       │     Calls synthesize_response() → Groq LLM generates summary
       │     Builds final response with all_facilities[], summary, trace
       │
9.     ▼  Returns QueryResponse to frontend with 200ms+ timing
```

---

## Orchestration Layer

**File:** `backend/orchestration/graph.py` (544 lines)

### State Schema

```python
class GraphState(TypedDict):
    query: str                    # Original user query
    intent: str                   # Classified intent label
    confidence: float             # Classification confidence [0, 1]
    agents_to_run: list[str]      # Ordered agent execution plan
    current_agent_index: int      # Pointer into agents_to_run
    agent_results: dict           # {agent_name: result_dict}
    all_facilities: list[dict]    # Merged facilities with coordinates
    plan: dict                    # Execution plan metadata
    summary: str                  # LLM-generated synthesis
    trace: list[dict]             # Reasoning steps for ExplainPanel
    response: dict                # Final structured response
```

### Graph Topology

7 nodes connected by conditional edges:

```
START → supervisor → route_first_agent → [agent_node] → route_next_agent → ...
                                                                          ↓
                                                                    aggregator → END
```

| Node | Function | Role |
|------|----------|------|
| `supervisor` | `supervisor_node()` | Classifies intent, sets `agents_to_run` |
| `genie` | `genie_node()` | Pandas DataFrame queries |
| `vector_search` | `vector_search_node()` | Semantic search with self-correction |
| `medical_reasoning` | `medical_reasoning_node()` | Validation and anomaly detection |
| `geospatial` | `geospatial_node()` | Spatial analysis |
| `planning` | `planning_node()` | Action plan generation |
| `aggregator` | `aggregator_node()` | Merges results, calls LLM, builds response |

### Conditional Routing

- **`route_first_agent()`**: Reads `agents_to_run[0]` → routes to that agent node, or `aggregator` if list is empty
- **`route_next_agent()`**: Increments `current_agent_index` → routes to next agent or `aggregator` when exhausted
- Each agent node has outgoing edges to all 5 agents + aggregator (flexible chaining)

### Self-Correction Loop

Inside `vector_search_node()`: if the search returns 0 results and filters were applied, it automatically:
1. Strips ` in <city>` and ` near <city>` from the query
2. Re-runs the search without location filters
3. Uses the retry results if any are found

### Aggregator

The aggregator scans all `agent_results` for facility-bearing keys:
`results`, `facilities`, `flagged_facilities`, `stops`, `placements`, `suggestions`, `alternatives`, `regions`, `flagged`, `validated`, `deserts`, `cold_spots`, `primary_facility`, `backup_facility`

Each facility with valid `latitude`/`longitude` is added to `all_facilities[]` for map display.

### Agent Caching

A singleton `AgentCache` class lazily initialises each agent via `_get_*()` methods. Agents are created once and reused across requests.

---

## Supervisor Agent

**File:** `backend/agents/supervisor/agent.py` (550 lines)

### Purpose

Classifies the user's natural-language query into one of 14 intent categories and determines which agents to invoke.

### Intent Categories (14)

```
COUNT, AGGREGATE, ANOMALY_DETECTION, VALIDATION, DISTANCE_QUERY,
COVERAGE_GAP, MEDICAL_DESERT, SINGLE_POINT_FAILURE, FACILITY_LOOKUP,
SERVICE_SEARCH, SPECIALTY_SEARCH, COMPARISON, PLANNING, GENERAL
```

### Routing Table

| Intent | Agents | Flow |
|--------|--------|------|
| COUNT | genie | single |
| AGGREGATE | genie | single |
| ANOMALY_DETECTION | genie → medical_reasoning | sequential |
| VALIDATION | vector_search → medical_reasoning | sequential |
| DISTANCE_QUERY | geospatial | single |
| COVERAGE_GAP | geospatial → medical_reasoning | sequential |
| MEDICAL_DESERT | geospatial → medical_reasoning | sequential |
| SINGLE_POINT_FAILURE | genie → medical_reasoning | sequential |
| FACILITY_LOOKUP | vector_search | single |
| SERVICE_SEARCH | vector_search → genie | sequential |
| SPECIALTY_SEARCH | vector_search | single |
| COMPARISON | genie + geospatial | parallel |
| PLANNING | planning | single |
| GENERAL | vector_search + genie | parallel |

### Classification Pipeline

```
Query → classify_intent()
           │
           ├── 1. _classify_embedding()     ← primary (if model loaded)
           │      │
           │      ├── Encode query → 384d vector
           │      ├── Cosine similarity vs all exemplar embeddings
           │      ├── Top-2-mean pooling per intent
           │      ├── Sigmoid confidence: 1/(1+exp(-20*(gap-0.05)))
           │      └── If confidence < 0.45 → LLM fallback
           │
           ├── 2. _classify_regex()          ← fallback
           │      └── 13 regex pattern sets, count matches per intent
           │
           └── 3. _expand_multi_intent()     ← post-processing
                  └── If secondary intent similarity > 0.40
                      → merge its agents into the plan
```

### Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| Embedding dimension | 384 | `all-MiniLM-L6-v2` output |
| Exemplars per intent | 4–7 | Training queries for similarity |
| Sigmoid steepness | 20 | Sharp discrimination curve |
| Sigmoid centre | 0.05 | Gap at which confidence ≈ 50% |
| LLM fallback threshold | 0.45 | Below this → ask Groq to classify |
| Multi-intent threshold | 0.40 | Secondary intent inclusion |
| Min confidence floor | 0.10 | Returned when no match at all |

### Top-2-Mean Pooling

Instead of taking the maximum similarity per intent (which overweights single-keyword matches), the supervisor averages the **top 2 similarities** for each intent. This is more robust: an intent must match on multiple exemplars to score highly.

---

## Genie Agent

**File:** `backend/agents/genie/agent.py` (310 lines)

### Purpose

Structured data queries over a flat Pandas DataFrame of 797 facilities.

### Data Shape

20 columns per facility. Numeric columns (`numberDoctors`, `capacity`, `latitude`, `longitude`) are coerced to float at init.

### Extraction Pipeline

Every query passes through extractors that pull structured filters:

```
Query → _extract_specialty()    → MEDICAL_SPECIALTIES_MAP (15 specialties)
      → _extract_facility_type() → hospital, clinic, pharmacy, dentist
      → _extract_region()        → 15 regions + 11 cities (word-boundary match)
      → _extract_equipment()     → 13 equipment keywords
```

### Negation Detection

`_is_negated()` checks whether a specialty mention is preceded by negation words:

```
Pattern: (not|without|no|lacking|absence|absent|missing|don't|doesn't|do not|does not)
         \s+.*{specialty}
```

When negated, the filter mask is **inverted**: returns facilities that do NOT have the specialty.

### Action Methods

| Method | Trigger | Output |
|--------|---------|--------|
| `count_facilities()` | "how many", "count", "total" | Count + facility list |
| `region_aggregation()` | "which region", "per region" | Per-region stats |
| `specialty_distribution()` | "distribution", "breakdown" | Specialty → count map |
| `anomaly_bed_doctor_ratio()` | "anomal", "ratio", "outlier" | IQR-flagged facilities |
| `single_point_of_failure()` | "single point", "depend on" | Specialties with ≤3 facilities |
| `find_by_specialty()` | specialty detected | Filtered facility list |
| `overview()` | fallback | Top-level dataset stats |

### IQR Anomaly Detection

```python
Q25, Q75 = percentile(ratios, [25, 75])
IQR = Q75 - Q25
threshold = max(Q75 + 1.5 * IQR, 20)   # floor of 20 to avoid noise
flagged = facilities where bed_doctor_ratio > threshold
```

---

## Vector Search Agent

**File:** `backend/agents/vector_search/agent.py` (220 lines)

### Purpose

Semantic similarity search across Qdrant Cloud using 3 named vectors per facility.

### Three Vector Representations

| Name | Dimension | Content | Query Template |
|------|-----------|---------|---------------|
| `full_document` | 384 | Complete facility profile | `"{query}"` |
| `clinical_detail` | 384 | Procedures, equipment, capabilities | `"Procedures: {q} \| Equipment: {q}"` |
| `specialties_context` | 384 | Specialty names in context | `"facility with specialties: {q}"` |

### Vector Selection Logic

`_pick_vector()` analyses the query text:
- Contains any of 20 clinical keywords → `clinical_detail`
- Contains any of 14 specialty keywords → `specialties_context`
- Default → `full_document`

### Reciprocal Rank Fusion (RRF)

```
For each document d appearing at rank r in vector v:
    score(d) += weight(v) / (k + r)

where k = 60 (from Cormack+ 2009)
```

All 3 vectors are queried simultaneously with `search_limit = 30` candidates each. Results are fused into a single ranked list.

### Weight Normalisation

Raw affinity per vector is `1.0 + min(clinical_or_specialty_hits, 3)`. Weights are then **normalised so they always sum to 3.0**:

```python
total = sum(raw_weights)
normalised = [w * 3.0 / total for w in raw_weights]
```

This prevents any single vector from dominating the fusion.

### Filter Construction

- **Type filter**: "ngo" → `organization_type`, otherwise `facilityTypeId`
- **Facility type**: hospital / clinic / pharmacy / dentist
- **City**: 11 Ghana cities (Cape Coast first for longest-match priority)
- **Region**: from `MEDICAL_SPECIALTIES_MAP` keys

City filter uses Qdrant's OR logic: matches `address_city` OR `address_stateOrRegion`.

---

## Medical Reasoning Agent

**File:** `backend/agents/medical_reasoning/agent.py` (572 lines)

### Purpose

Validates facility capability claims and detects data anomalies using medical domain knowledge.

### Five Analysis Modes

#### 1. Constraint Validation

Checks each facility's claimed specialties against `ADVANCED_PROCEDURE_REQUIREMENTS`:

| Procedure | Required Equipment | Min Beds |
|-----------|-------------------|----------|
| Neurosurgery | CT, MRI, ICU, operating theater | 50 |
| Cardiac surgery | cardiac catheterization, ICU, ventilators | 100 |
| Cataract surgery | ophthalmoscope, surgical microscope | 5 |
| Dialysis | dialysis machine | 10 |
| Orthopedic surgery | X-ray, operating theater | 30 |
| Oncology | CT, radiation therapy, laboratory | 50 |

**Confidence model** (diminishing penalty):
- No issues: `conf = min(0.95, 0.65 + (specialties × 0.03))`
- High-severity issues: 1st = −15%, 2nd = −10%, 3rd+ = −5% each
- Medium-severity issues: 1st = −8%, rest = −4% each
- Floor = 0.10

#### 2. Anomaly Detection (Two-Stage)

```
Stage 1: Isolation Forest
    Features: [num_specialties, num_procedures, num_equipment,
               num_capabilities, capacity, doctors]    (6 features)
    contamination = 0.05
    ↓
Stage 2: Mahalanobis Distance
    Threshold: chi² at p=0.975, df=6
    ↓
Flagged: intersection of both stages (AND logic)
```

Anomaly reasons include: `procedures > 10 && equipment < 2`, `bed/doctor ratio > 50`, `specialties > 8`, `procedures > 15 && capacity < 20`.

#### 3. Red Flag Detection

3 pattern categories with regex patterns:
- **Visiting specialist** (3 patterns): suggests services depend on visiting doctors
- **Temporary service** (4 patterns): hints at non-permanent capabilities
- **Vague claim** (4 patterns): imprecise language about capabilities

Specialty matching uses **rapidfuzz** `token_set_ratio ≥ 75` with a sliding window of 5 words.

#### 4. Coverage Gap Analysis

For each specialty, counts facilities per region. Severity:
- `critical` = 0 facilities in a region
- `high` = 1 facility in a region

#### 5. Single Point of Failure

Specialties with ≤3 facilities nationwide:
- Risk `critical` = 1 facility
- Risk `high` = 2 facilities
- Risk `medium` = 3 facilities

---

## Geospatial Agent

**File:** `backend/agents/geospatial/agent.py` (543 lines)

### Purpose

Spatial analysis using BallTree indexing, grid-based desert detection, and Mahalanobis regional equity analysis.

### BallTree Construction

```python
coords_radians = np.radians(facilities[['latitude', 'longitude']].values)
tree = BallTree(coords_radians, metric='haversine')
# Earth radius = 6371.0 km for distance conversion
```

767 geocoded facilities indexed. Specialty-filtered trees are built on demand and cached.

### Six Capabilities

#### 1. Radius Search (`find_within_radius`)
- Default radius: 50 km
- Max results: 30
- Converts radius to radians: `radius_km / 6371.0`
- O(log n) query via BallTree

#### 2. K-Nearest Facilities (`find_nearest`)
- Default k: 5
- Returns sorted by distance

#### 3. Coverage Gap Analysis (`coverage_gaps`)
- **Ghana bounding box**: south=4.74, north=11.17, west=−3.26, east=1.20
- Grid: `np.arange(step=0.25)` → ~26 × 18 = ~468 grid cells
- For each cell: nearest facility distance via BallTree
- Threshold: 55 km (default)
- Returns: top 15 cold spots sorted by distance descending

#### 4. Medical Desert Detection (`medical_deserts`)
- Uses `GHANA_REGION_COORDS` for authoritative region centroids
- For each region: nearest facility with the queried specialty
- Severity: `critical` (>150 km), `high` (>100 km), `medium` (>75 km)

#### 5. Regional Equity Analysis (`regional_equity`)
- Per-region metrics: facility count, unique specialties, doctor sum, bed sum
- **Mahalanobis distance** for multivariate anomaly detection
- Features: `[facility_density, specialty_count, doctor_total, bed_total]`

#### 6. City Distance (`city_distance`)
- Extracts two city names from query
- Geocodes both → geodesic distance via `geopy`

### Geocoding Integration

21 known city coordinates hardcoded. Falls back to averaging facility coordinates in the city.

---

## Planning Agent

**File:** `backend/agents/planning/agent.py` (722 lines)

### Purpose

Generates actionable deployment, routing, and resource allocation plans with optional quantum optimisation.

### Capability Scoring

```python
score = 20                           # base
score += 35 if specialty_match       # dominant factor
score += 20 if has_ICU or theater
score += 10 if capacity > 20
score += 10 if has_doctors
score += 5  if has_CT_MRI_scanner
# max = 100
```

### Five Scenario Architectures

#### 1. Emergency Routing

```
Input: patient location (or Ghana center: 7.9465, -1.0232)
  → BallTree finds facilities within 100km
  → Score each by capability
  → Sort by (score DESC, distance ASC)
  → Return: primary_facility, backup_facility, alternatives[2:5]
  → Travel time = distance / 60 * 60 (minutes, ~60 km/h)
```

#### 2. Specialist Deployment (TSP)

```
Input: specialty, max_stops (default 8)
  → Filter facilities by specialty
  → Score by capability, take top max_stops
  → Start from Accra (5.6037, -0.1870)

Stage 1: Greedy nearest-neighbour initial tour
Stage 2: 2-opt local search
           max_iterations = 1000
           O(n²) per iteration
           epsilon = 1e-9 (convergence)
Stage 3 (optional): QUBO quantum comparison
           if use_quantum flag → call compare_routes()
           Returns side-by-side: classical vs quantum
```

#### 3. Equipment Distribution

```
Input: equipment type (default "CT scanner")
  → Split facilities: have_it vs need_it
  → Rank regions by need count
  → Pick highest-capacity facility per region
  → Return top 5 placements with facilities_served count
```

#### 4. New Facility Placement (Maximin)

```
Input: specialty
  → Grid resolution: 0.3° over Ghana bounding box
  → For each grid point: BallTree distance to nearest existing facility
  → Sort by distance DESC (farthest = best location)
  → Priority: critical (>100km), high (>50km), medium (≤50km)
  → Return top 10 with GPS coordinates
```

#### 5. Capacity Planning

```
  → Per-region: beds_per_facility, doctors_per_facility
  → Status: critical (bed_ratio < 5 AND total > 3)
            warning (bed_ratio < 15)
            adequate (otherwise)
  → Sort: critical first
```

### Quantum Integration

When `use_quantum=True` or "quantum" appears in the query:

```
Classical 2-opt route → compare_routes(stops, classical_route)
                              │
                              ▼
                     quantum.py: solve_tsp_qubo()
                              │
                     ┌────────┴────────┐
                     │ n ≤ 4           │ 5 ≤ n ≤ 10
                     ▼                 ▼
              NumPyMinimumEigen   Brute-force
              solver (exact        all n! permutations
              QUBO ground state)   evaluate cyclic cost
                     │                 │
                     └────────┬────────┘
                              ▼
                     Winner = cheaper route
                     Savings = |classical - quantum|
```

---

## Core Services

### LLM Service (`core/llm.py`, 347 lines)

- **Primary model**: `openai/gpt-oss-120b` (configurable via `GROQ_MODEL`)
- **Fallback model**: `llama-3.3-70b-versatile`
- **Client**: `groq.Groq` singleton

**Functions:**
| Function | Params | Purpose |
|----------|--------|---------|
| `chat()` | model, messages, max_tokens=512, temperature=0.3 | Raw Groq chat |
| `synthesize_response()` | query, results, intent | LLM summary for users |
| `classify_intent_llm()` | query | Fallback intent classification |
| `truncate_for_context()` | data, max_chars=3000 | Binary-search character budget |
| `_fallback_synthesis()` | query, results | Non-LLM text summary |

**Token-aware truncation**: Uses binary search to find the largest JSON slice of agent results that fits within `max_chars`. Handles lists (slice), dicts (subset keys), and scalars.

**Synthesis prompt rules**: Non-technical language, lead with key finding, use specific numbers, 3–8 sentences max 200 words, bullet points for clarity.

### Vectorstore (`core/vectorstore.py`, 260 lines)

- **Collection**: `ghana_medical_facilities`
- **3 named vectors**: all 384 dimensions, cosine distance
- **Payload indexes**: `address_city`, `address_stateOrRegion`, `facilityTypeId`, `organization_type` (keyword type)
- **Query templates** transform user queries to match indexed format per vector type

### Geocoding (`core/geocoding.py`, 500 lines)

**220 Ghana city coordinates** across all 16 regions, plus **46 region/alias entries**.

**3-stage geocode pipeline:**
```
1. Exact match: normalised city/region key lookup → O(1)
2. Word-boundary partial: sorted by key length (shorter=more specific)
   Only accepts whole-word matches → avoids "wa" matching "nkawkaw"
3. Fuzzy Levenshtein: rapidfuzz ratio ≥ 80 → handles typos
```

### Quantum (`core/quantum.py`, 260 lines)

**QUBO formulation**: `n²` binary variables via Qiskit `QuadraticProgram`. Distance matrix provides objective weights. Penalty constraint ensures valid TSP permutation.

| City count | Method | Time |
|------------|--------|------|
| n ≤ 4 | `NumPyMinimumEigensolver` (exact) | ~2s |
| 5 ≤ n ≤ 10 | Brute-force over n! permutations | <1s |
| n > 10 | Refused (too many permutations) | — |

### Config (`core/config.py`, 140 lines)

- **15 medical specialties** with 3–5 keywords each
- **6 advanced procedure requirements** with equipment, staff, capability, min_beds
- **3 red flag pattern categories** (visiting_specialist, temporary_service, vague_claim)
- **Ghana bounding box**: center=(7.9465, −1.0232), bounds=(4.74–11.17°N, −3.26–1.20°E)

---

## Data Pipeline

**File:** `backend/core/preprocessing.py` (210 lines)

```
CSV (987 rows, 20 columns)
     │
     ▼  load_csv(): read with UTF-8
     │
     ▼  clean_and_parse():
     │    Strip whitespace on all string columns
     │    Replace "null"/"None"/"" with NaN
     │    Parse JSON list columns (specialties, procedures, equipment, capabilities)
     │       tries: json.loads → ast.literal_eval → raw string
     │    Fix "farmacy" → "pharmacy"
     │
     ▼  deduplicate():
     │    Richness score = count of non-empty columns per row
     │    Sort by richness DESC
     │    Group by pk_unique_id
     │    Merge JSON list columns (union with dedup)
     │    Fill missing columns from secondary rows
     │    → 797 unique facilities
     │
     ▼  build_documents():
          Composite text per facility:
          "Name: X | Type: Y | Location: Z | Specialties: A, B, C |
           Procedures: D, E | Equipment: F, G | ..."
          Geocodes via geocode_facility() if lat/lng missing
          → List[dict] with 20+ fields each
```

Cached via `get_flat_df()` singleton — pipeline runs once, returns DataFrame thereafter.

---

## Frontend Architecture

**Stack:** React 19, Vite 6, Tailwind CSS v4, DaisyUI 5, Leaflet 1.9

### Component Tree

```
App.jsx
├── Header.jsx                  # Title, branding
├── StatsBar.jsx                # Facility/specialty/region counts
├── QueryInput.jsx              # Search bar with 8 example queries
├── PlanningPanel.jsx           # Sidebar with 5 scenario buttons
├── ResultsPanel.jsx            # Action-specific result renderers
│   ├── AgentResult             # Dispatches by action type
│   ├── PlanningResult          # 5 scenario-specific layouts
│   ├── FacilityTable           # Paginated table (20/page)
│   ├── StatBlock               # Numeric stat display
│   ├── ConfidenceBadge         # Color-coded confidence
│   └── Citations               # Collapsible citation list
├── MapView.jsx                 # Leaflet map (5 layer groups)
├── ExplainPanel.jsx            # Plain-language agent explanations
├── ReasoningTrace.jsx          # Step-by-step trace display
├── MLOpsDashboard.jsx          # Databricks pipeline status
└── utils/
    └── renderMarkdown.jsx      # Shared markdown → JSX renderer
```

### State Management (App.jsx)

| State | Type | Purpose |
|-------|------|---------|
| `stats` | object | Dashboard statistics from `/api/stats` |
| `facilities` | array | All facilities for default map |
| `result` | object | Current query response |
| `loading` | boolean | Request in progress |
| `error` | string | Error message |
| `activeTab` | string | Current tab: results/explain/trace/map/mlops |
| `sidebarOpen` | boolean | Planning sidebar visibility |

### Tab System

5 tabs rendered conditionally based on `activeTab`:

| Tab | Component | Content |
|-----|-----------|---------|
| ◈ Results | `ResultsPanel` | Agent-specific structured data, colour-coded by agent |
| 📋 Explain | `ExplainPanel` | Plain-language explanation for NGO planners |
| ⟐ Trace | `ReasoningTrace` | Agent timing, actions, confidence, LLM indicators |
| ◎ Map | `MapView` | Interactive Leaflet with facilities/routes/deserts |
| ⚙ MLOps | `MLOpsDashboard` | Databricks pipeline dashboard |

### Auto-Tab-Switch Logic

```javascript
const geoIntents = ['distance_query', 'coverage_gap', 'medical_desert', 'planning']
if (geoIntents.includes(intent) || agents_used.includes('geospatial') || agents_used.includes('planning'))
    → switch to 'map' tab
else
    → switch to 'results' tab
```

### Data Extraction Helpers

5 functions extract map-ready data from the raw API response:

| Helper | Scans | Produces |
|--------|-------|---------|
| `extractMapFacilities()` | `map_facilities`, agent results, all facilities | Marker array with lat/lng |
| `extractRouteData()` | `stops`, `route` keys across all agents | Route polyline points |
| `extractDesertData()` | `deserts`, `cold_spots`, `medical_deserts` | Desert circles + cold spot dots |
| `extractPlacementSuggestions()` | `new_facility_placement` action with `suggestions` | Diamond markers |
| `exportResultsCSV()` | First found facility list | CSV blob download |

### MapView Layer Architecture (5 Layers)

```
┌─────────────────────────────────────────────────────┐
│  CARTO Dark Basemap (z-index: base)                 │
│                                                      │
│  Layer 1: Facility Markers (CircleMarker r=5)        │
│    Colors: hospital=#00f3ff, clinic=#06ffa5,         │
│            health_center=#8338ec, pharmacy=#ffd60a,  │
│            ngo=#ff006e, laboratory=#ff8500            │
│                                                      │
│  Layer 2: Route Polylines                            │
│    Glow: weight=8, opacity=0.15                      │
│    Main: weight=3, dashArray="8,6"                   │
│    Stops: green(first) → cyan(mid) → pink(last)     │
│                                                      │
│  Layer 3: Medical Deserts                            │
│    L.circle: critical=45km, high=35km, medium=25km   │
│    Cold spots: CircleMarker r=4, pink                │
│                                                      │
│  Layer 4: Placement Suggestions                      │
│    Diamond DivIcon: 16×16px, rotated 45°             │
│    Colors by priority: critical=pink, high=orange    │
│                                                      │
│  Layer 5: Dynamic Legend + Route Info Overlay         │
└─────────────────────────────────────────────────────┘
```

### Markdown Rendering (`utils/renderMarkdown.jsx`)

Shared utility converting LLM markdown output to styled JSX:

| Pattern | Output |
|---------|--------|
| `**bold**` | `<strong>` with configurable `boldColor` |
| `- item` / `• item` / `* item` | `<ul><li>` bullet list |
| `1. item` / `2. item` | `<ol><li>` ordered list |
| `#` / `##` / `###` | Headings (0.95 / 0.85 / 0.8rem) |
| Blank line | Paragraph break (6px spacer) |
| Normal text | `<p>` with configurable `textColor` |

---

## API Layer

**File:** `backend/api/main.py` (45 lines), `backend/api/routes.py` (494 lines)

### Server Configuration

- **CORS origins**: `http://localhost:5173`, `http://localhost:3000`
- **Lifespan**: On startup calls `warm_up_agents()` to pre-load all agents and models
- **App**: `FastAPI(title="MedBridge AI", version="2.0.0")`
- **Routes**: Mounted at prefix `/api`

### Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/health` | — | `{status, version, timestamp}` |
| POST | `/api/query` | `{query: str}` (max 2000 chars) | `QueryResponse` (10 fields) |
| GET | `/api/facilities` | — | `{facilities: [...], count}` |
| GET | `/api/stats` | — | Aggregated dataset statistics |
| GET | `/api/specialties` | — | `{specialties: [{name, count}]}` |
| GET | `/api/planning/scenarios` | — | 5 scenario definitions |
| POST | `/api/planning/execute` | `{scenario, query, params}` | Direct planning agent result |
| POST | `/api/routing-map` | `{query, scenario}` | Plan + facilities + deserts + reasoning |
| GET | `/api/mlops/status` | — | Vector search backend, serving endpoint, MLflow |
| GET | `/api/mlops/pipeline` | — | Full pipeline config for dashboard |

### QueryResponse Shape

```python
class QueryResponse:
    query: str                  # Echo of input
    intent: str                 # Classified intent
    confidence: float           # Classification confidence
    agents_used: list[str]      # Which agents ran
    response: dict              # Structured agent results
    summary: str                # LLM-generated plain-language summary
    total_duration_ms: float    # End-to-end timing
    map_facilities: list[dict]  # Facilities with coordinates for map
    trace: list[dict]           # Reasoning steps
    timestamp: str              # ISO timestamp
```
