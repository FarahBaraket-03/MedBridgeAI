# MedBridge AI

> Multi-Agent Healthcare Intelligence Platform for Ghana

MedBridge AI analyses **797 medical facilities and NGOs** across Ghana using a coordinated team of AI agents. Users ask natural-language questions and receive structured answers, interactive maps, and data-driven insights — all powered by a LangGraph orchestration pipeline.

---

## Quick Start

```bash
# 1. Backend
pip install -r requirements.txt          # inside a virtual environment
uvicorn backend.api.main:app --reload    # starts on http://localhost:8000

# 2. Frontend
cd frontend
npm install
npm run dev                              # starts on http://localhost:5173
```

Open the frontend URL and start asking questions.

---

## User Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. USER TYPES A QUESTION                                       │
│     "Which facilities handle trauma near Kumasi?"               │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. SUPERVISOR CLASSIFIES INTENT                                │
│     Regex patterns match → distance_query                       │
│     Routes to: [Geospatial]                                     │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. AGENT(S) EXECUTE                                            │
│     Geospatial geocodes "Kumasi" → (6.69, -1.62)               │
│     Finds 8 facilities within 50 km offering trauma care        │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. AGGREGATOR MERGES RESULTS                                   │
│     Collects facilities with coordinates for the map            │
│     LLM generates a plain-language summary                      │
└──────────────────────┬──────────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. FRONTEND RENDERS                                            │
│     Results tab  → structured data cards                        │
│     Map tab      → Leaflet markers for the 8 facilities         │
│     Explain tab  → step-by-step agent reasoning trace           │
└─────────────────────────────────────────────────────────────────┘
```

### What the user sees

| Tab | Content |
|-----|---------|
| **Results** | Facility cards, counts, tables, planning details |
| **Map** | Interactive Leaflet map with markers, routes, desert zones |
| **Explain** | Agent trace with timing, actions taken, and citations |

---

## The 6 Agents

### 1. Supervisor — *The Router*

| | |
|---|---|
| **Role** | Classifies the user's intent and decides which agents to call |
| **How** | 14 regex pattern sets scored by match count; falls back to LLM for ambiguous queries |
| **Output** | Execution plan: intent, agent list, sequential or parallel flow |

**Example intents it detects:**

| Intent | Trigger words | Routed to |
|--------|---------------|-----------|
| `count` | "how many", "total" | Genie |
| `distance_query` | "near", "within km", "closest" | Geospatial |
| `validation` | "suspicious claims", "really offer" | Vector Search → Medical Reasoning |
| `planning` | "deploy", "where should we build" | Planning |
| `coverage_gap` | "medical desert", "underserved" | Geospatial → Medical Reasoning |
| `comparison` | "compare", "vs", "urban rural" | Genie + Geospatial |

---

### 2. Genie — *The Analyst*

| | |
|---|---|
| **Role** | Structured data queries using Pandas DataFrame operations |
| **Data** | Flat table of 797 facilities with specialties, procedures, equipment, capacity, coordinates |
| **Strengths** | Counting, filtering, aggregating, region breakdowns |

**What it can do:**

- Count facilities by specialty, type, or region
- List facilities matching complex filters (specialty + region + type)
- Aggregate statistics per region (facility counts, specialty coverage)
- Find rare specialties and procedures with limited availability
- Return facility records **with lat/lng** for map display

**Example queries:**
- *"How many hospitals offer cardiology?"* → 12 facilities
- *"Which region has the most clinics?"* → Greater Accra (309)
- *"Facilities in Ashanti that perform orthopedic surgery"*

---

### 3. Vector Search — *The Finder*

| | |
|---|---|
| **Role** | Semantic similarity search across facility descriptions |
| **Data** | Qdrant Cloud vector database with 3 named vectors per facility |
| **Strengths** | Finding facilities when the user describes needs in natural language |

**Three vector representations:**

| Vector | Dimension | Content |
|--------|-----------|---------|
| `full_document` | 384 | Complete facility profile |
| `clinical_detail` | 384 | Specialties, procedures, equipment, capabilities |
| `specialties_context` | 384 | Specialty names in medical context |

Automatically selects the best vector based on query content. Returns ranked results with similarity scores and citations.

**Example queries:**
- *"Tell me about Korle Bu Teaching Hospital"*
- *"Facilities that can handle complex cardiac procedures"*
- *"Organizations working on maternal health in rural Ghana"*

---

### 4. Medical Reasoning — *The Validator*

| | |
|---|---|
| **Role** | Validates facility claims and detects anomalies using medical domain knowledge |
| **How** | Rule-based constraints, Isolation Forest statistical anomaly detection, pattern analysis |
| **Strengths** | Catching implausible data, identifying coverage gaps, flagging red flags |

**Five analysis modes:**

| Mode | What it checks |
|------|----------------|
| **Constraint Validation** | Does a facility claiming neurosurgery have CT/MRI/ICU? |
| **Anomaly Detection** | Statistical outliers in bed count, doctor numbers, procedure breadth |
| **Red Flag Detection** | Language patterns suggesting exaggerated or implausible claims |
| **Coverage Gap Analysis** | Regions with zero or very few facilities for a given specialty |
| **Single Point of Failure** | Specialties depending on only 1–2 facilities nationwide |

**Example queries:**
- *"Find suspicious facility capability claims"*
- *"Which specialties depend on a single facility?"*
- *"Are there regions without access to emergency care?"*

---

### 5. Geospatial — *The Navigator*

| | |
|---|---|
| **Role** | Distance calculations, coverage mapping, medical desert detection |
| **How** | Geodesic distance (geopy), grid-based analysis over Ghana's bounding box |
| **Strengths** | Proximity search, geographic gap analysis, regional equity comparison |

**Six capabilities:**

| Capability | Description |
|------------|-------------|
| **Radius Search** | Find all facilities within X km of a point |
| **Nearest Facilities** | K closest facilities to a location |
| **Coverage Gap Analysis** | Grid-based cold-spot detection (cells >50 km from nearest facility) |
| **Medical Desert Detection** | Regions where citizens travel >75 km to reach a specialty |
| **Regional Equity** | Per-region facility density, doctor/bed ratios, specialty counts |
| **City Distance** | Distance between two Ghana cities |

Geocodes city names from queries automatically (e.g., "near Kumasi" → 6.69°N, 1.62°W).

**Example queries:**
- *"Hospitals within 30 km of Tamale"*
- *"Where are the medical deserts for cardiology?"*
- *"Compare healthcare distribution across regions"*

---

### 6. Planning — *The Strategist*

| | |
|---|---|
| **Role** | Generates actionable deployment, routing, and resource allocation plans |
| **How** | Scenario-based algorithms using facility data + geospatial calculations |
| **Strengths** | Turning analysis into concrete action steps |

**Five planning scenarios:**

| Scenario | Output |
|----------|--------|
| **Emergency Routing** | Primary facility, backup, alternatives with distance/travel time |
| **Specialist Deployment** | Multi-stop rotation route for visiting specialists |
| **Equipment Distribution** | Priority list for distributing equipment to underserved facilities |
| **New Facility Placement** | GPS coordinates for optimal new facility locations |
| **Capacity Planning** | Region-by-region capacity status and expansion priorities |

**Example queries:**
- *"Plan an emergency route for a cardiac patient near Tamale"*
- *"Where should we build new maternal health facilities?"*
- *"Deploy mobile eye care units across Northern Ghana"*

---

## Multi-Agent Orchestration

The agents are wired together using **LangGraph StateGraph**. The Supervisor decides the plan, then agents run sequentially or in parallel:

```
                    ┌──────────┐
          ┌────────►│  Genie   │────────┐
          │         └──────────┘        │
          │         ┌──────────┐        │
          ├────────►│ Vector   │────────┤
          │         │ Search   │        │
┌────────┐│         └──────────┘        │  ┌────────────┐   ┌─────┐
│Supervisor├────────►│ Medical  │────────┼─►│ Aggregator │──►│ END │
│        ││         │Reasoning │        │  └────────────┘   └─────┘
└────────┘│         └──────────┘        │
          │         ┌──────────┐        │
          ├────────►│Geospatial│────────┤
          │         └──────────┘        │
          │         ┌──────────┐        │
          └────────►│ Planning │────────┘
                    └──────────┘
```

**Sequential flow** (e.g., Validation: Vector Search finds facilities → Medical Reasoning validates them)  
**Parallel flow** (e.g., Comparison: Genie + Geospatial run simultaneously)  
**Single flow** (e.g., Count: only Genie runs)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, Vite 6, Tailwind CSS v4, DaisyUI v5, Leaflet 1.9 |
| **Backend** | Python 3.13, FastAPI, LangGraph |
| **Vector DB** | Qdrant Cloud (384-dim, 3 named vectors) |
| **Embeddings** | SentenceTransformer `all-MiniLM-L6-v2` |
| **LLM** | Groq Cloud (`llama-3.3-70b-versatile`) |
| **ML** | scikit-learn (Isolation Forest for anomaly detection) |
| **Geospatial** | geopy (geodesic distance), static geocoding for 260+ Ghana cities |
| **Data** | Virtue Foundation Ghana CSV — 987 rows → 797 unique facilities/NGOs |

---

## Project Structure

```
medbridge/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app, CORS, lifespan
│   │   └── routes.py            # All API endpoints
│   ├── agents/
│   │   ├── supervisor/agent.py  # Intent classification + routing
│   │   ├── genie/agent.py       # Text2SQL on Pandas
│   │   ├── vector_search/agent.py # Qdrant semantic search
│   │   ├── medical_reasoning/agent.py # Validation + anomaly detection
│   │   ├── geospatial/agent.py  # Distance + coverage + deserts
│   │   └── planning/agent.py    # Scenario-based planning
│   ├── core/
│   │   ├── config.py            # Constants, specialty maps, API keys
│   │   ├── geocoding.py         # Static city/region → lat/lng lookup
│   │   ├── llm.py               # Groq LLM synthesis + intent fallback
│   │   ├── preprocessing.py     # CSV → clean → dedup → geocode → documents
│   │   └── vectorstore.py       # Qdrant multi-vector search
│   └── orchestration/
│       └── graph.py             # LangGraph StateGraph workflow
├── frontend/
│   └── src/
│       ├── App.jsx              # Main component, query handling, tabs
│       ├── api/client.js        # API client
│       └── components/
│           ├── Header.jsx       # App header with stats
│           ├── QueryInput.jsx   # Search bar
│           ├── ResultsPanel.jsx # Result rendering per action type
│           ├── MapView.jsx      # Leaflet map with markers/routes/deserts
│           ├── ExplainPanel.jsx # Agent reasoning trace
│           ├── StatsBar.jsx     # Quick statistics
│           └── PlanningPanel.jsx # Planning scenario selector
└── data/
    └── Virtue Foundation Ghana v0.3 - Sheet1.csv
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Run a natural-language query through the agent pipeline |
| `GET` | `/api/facilities` | List all facilities (for map markers) |
| `GET` | `/api/stats` | Dataset statistics |
| `GET` | `/api/specialties` | Available medical specialties |
| `GET` | `/api/planning/scenarios` | List planning scenarios |
| `POST` | `/api/planning/execute` | Execute a specific planning scenario |
| `POST` | `/api/routing-map` | Generate a routing map |

---

## Example Queries to Try

| Category | Query |
|----------|-------|
| **Counting** | How many hospitals offer cardiology? |
| **Proximity** | Which facilities handle trauma near Kumasi? |
| **Coverage** | Where are the medical deserts in Ghana? |
| **Validation** | Find suspicious facility capability claims |
| **Planning** | Where should we deploy mobile eye care units? |
| **Comparison** | Compare Accra vs Northern Region healthcare |
| **Lookup** | Tell me about Korle Bu Teaching Hospital |
| **Resilience** | Which specialties depend on a single facility? |
