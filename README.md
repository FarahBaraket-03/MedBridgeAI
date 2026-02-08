# 💊 MedBridge AI

> **Multi-Agent Healthcare Intelligence Platform for Ghana**
> Virtue Foundation × Databricks × AI Tinkerers Hackathon — *Bridging Medical Deserts*

MedBridge AI analyses **797 medical facilities and NGOs** across Ghana through **6 coordinated AI agents**. Users ask natural-language questions and receive structured answers, interactive maps, and actionable insights — powered by a LangGraph orchestration pipeline with self-correcting feedback loops, optional **quantum-optimised routing**, and a cyberpunk-styled React frontend.

---

## Quick Start

```bash
# Clone & install
git clone <repo-url> && cd MedBridgeAI
python -m venv .venv && .venv\Scripts\activate   # source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt

# Configure
cp .env.example .env    # add GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY

# Run
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
cd frontend && npm install && npm run dev        # → http://localhost:5173
```

---

## How It Works

```
  User Question
       │
       ▼
 ┌───────────┐    ┌────────┐ ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐
 │ Supervisor │───►│ Genie  │ │  Vector    │ │  Medical  │ │Geospatial│ │Planning│
 │  (Router)  │    │Analyst │ │  Search    │ │ Reasoning │ │Navigator │ │Strategy│
 └───────────┘    └───┬────┘ └─────┬──────┘ └─────┬─────┘ └────┬─────┘ └───┬────┘
                      │            │              │             │            │
                      └────────────┴──────────────┴─────────────┴────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐     ┌───────────┐
                                          │  Aggregator  │────►│  Frontend  │
                                          │ + LLM Summary│     │  Results   │
                                          └──────┬───────┘     └───────────┘
                                                 │ retry if 0 results
                                                 └──────► (self-correction)
```

**Flow modes:** Sequential (e.g. Vector Search → Medical Reasoning) · Parallel (e.g. Genie + Geospatial) · Single agent

---

## The 6 Agents

### 1 · Supervisor — *The Router*

Classifies user intent and decides which agents to call.

- **Top-2-mean embedding pooling** — averages the 2 best similarities per intent (more robust than max-pool)
- **Sigmoid confidence gating** — `1/(1+exp(-20*(gap-0.05)))` for sharp clear/ambiguous discrimination
- **Multi-intent expansion** — detects secondary intents (similarity > 0.40) and merges agent sets
- **LLM fallback** — when embedding confidence < 0.45, Groq classifies with agent-name validation

| Intent | Example trigger | Routed to |
|--------|----------------|-----------|
| `count` | "how many hospitals…" | Genie |
| `distance_query` | "near Kumasi", "within 30 km" | Geospatial |
| `validation` | "suspicious claims" | Vector Search → Medical Reasoning |
| `planning` | "deploy", "where should we build" | Planning |
| `coverage_gap` | "medical desert", "underserved" | Geospatial + Medical Reasoning |
| `comparison` | "compare Accra vs Northern" | Genie + Geospatial |

### 2 · Genie — *The Analyst*

Structured Pandas queries over the full facility dataset.

- Counting, filtering, aggregation, region breakdowns
- **Negation detection** — "facilities *without* cardiology" correctly inverts filter masks
- **IQR anomaly detection** — adaptive `Q75 + 1.5×IQR` thresholds for bed/doctor ratios
- Returns records with lat/lng for map display

### 3 · Vector Search — *The Finder*

Semantic similarity search across Qdrant Cloud (384-dim, 3 named vectors per facility).

| Vector | Content | Query template |
|--------|---------|---------------|
| `full_document` | Complete facility profile | Raw query |
| `clinical_detail` | Specialties, procedures, equipment | `"Procedures: {q} \| Equipment: {q}"` |
| `specialties_context` | Specialty names | `"facility with specialties: {q}"` |

- **Reciprocal Rank Fusion (RRF)** — merges results across all 3 vectors with normalised weights (sum = 3.0)
- City/region OR-filter for location-scoped queries
- Dual backend: Qdrant Cloud or Databricks Vector Search

### 4 · Medical Reasoning — *The Validator*

Validates facility claims and detects data anomalies using medical domain knowledge.

| Mode | What it checks |
|------|---------------|
| Constraint Validation | Does a facility claiming neurosurgery have CT/MRI/ICU? |
| Anomaly Detection | Two-stage Isolation Forest + Mahalanobis outlier detection |
| Red Flag Detection | Language patterns suggesting exaggerated capabilities |
| Coverage Gap Analysis | Regions with zero or few providers for a specialty |
| Single Point of Failure | Specialties relying on only 1–2 facilities nationwide |

### 5 · Geospatial — *The Navigator*

Distance calculations, coverage mapping, and medical desert detection.

- **BallTree spatial index** (Haversine) over 767 geocoded facilities — O(log n) radius/k-nearest queries
- **Grid-based cold-spot detection** — 0.25° grid across Ghana, flags cells > 50 km from any facility
- **Medical desert detection** — regions where citizens travel > 75 km to reach a specialty
- **Mahalanobis distance** — multivariate regional equity anomaly detection
- **3-stage geocoding** — exact match → boundary check → fuzzy Levenshtein (handles "Kumase" → Kumasi)

### 6 · Planning — *The Strategist*

Generates actionable deployment, routing, and resource allocation plans.

- **Capability scoring** — specialty match +35, ICU/theater +20, equipment +15 → routes by medical need
- **2-opt TSP** — iteratively swaps edges to shorten specialist deployment tours (~15-20% reduction)
- **Quantum QUBO routing** *(opt-in)* — TSP as Quadratic Unconstrained Binary Optimisation via Qiskit; ≤4 cities use `NumPyMinimumEigensolver` (exact), 5–10 use QUBO-aware brute-force; returns side-by-side comparison
- **Maximin placement** — new facility GPS coordinates maximising minimum distance to existing facilities

| Scenario | Output |
|----------|--------|
| Emergency Routing | Primary + backup facility with distance/travel time |
| Specialist Deployment | Multi-stop optimised rotation route |
| Equipment Distribution | Priority list for underserved facilities |
| New Facility Placement | GPS coordinates for optimal new locations |
| Capacity Planning | Region-by-region status and expansion priorities |

---

## Frontend

**React 19 · Vite 6 · Tailwind CSS v4 · DaisyUI 5 · Leaflet 1.9** — cyberpunk dark theme

| Tab | Content |
|-----|---------|
| **◈ Results** | Colour-coded agent sections, facility tables with pagination, planning cards |
| **📋 Explain** | Plain-language step-by-step explanation for NGO planners |
| **⟐ Trace** | Agent timing, actions, confidence scores, LLM enhancement indicators |
| **◎ Map** | Interactive Leaflet — colour-coded markers, dashed route lines, desert zones, proposed facility diamonds |
| **⚙ MLOps** | Databricks pipeline status, MLflow tracking, model serving |

**Key features:**
- **Markdown-rendered AI Summary** — LLM output (bold, bullets, headings) rendered as formatted JSX via shared `renderMarkdown` utility
- **Auto-tab-switch** — geo/planning queries open the Map tab automatically
- **Planning sidebar** — 5 one-click scenario buttons (Emergency, Deployment, Equipment, Placement, Capacity)
- **CSV export** — one-click download of structured results
- **Dynamic map legend** — adapts to show facility types, desert severity, and proposed locations

---

## Algorithmic Highlights

| Component | Algorithm | Impact |
|-----------|-----------|--------|
| Supervisor | Top-2-mean pooling + sigmoid confidence | ~15% fewer misroutes vs max-pool |
| Supervisor | Multi-intent expansion (> 0.40 threshold) | Complex queries activate all relevant agents |
| Geospatial | BallTree Haversine spatial index | O(log n) vs O(n) brute-force |
| Geospatial | Mahalanobis regional anomaly detection | Catches multivariate outliers z-scores miss |
| Planning | 2-opt TSP + QUBO quantum routing | Optimal specialist deployment tours |
| Planning | Maximin facility placement | Maximises geographic dispersion |
| Vector Search | RRF with normalised weights (sum = 3.0) | Balanced fusion across 3 vector types |
| Genie | Negation detection + IQR anomaly threshold | Handles "without" queries; adaptive cutoffs |
| Geocoding | 3-stage lookup (exact → boundary → fuzzy) | Handles typos safely |
| LLM | Token-aware truncation (binary-search slicing) | Prevents context overflow |
| Graph | Empty-result self-correction loop | Auto-retries without filters on 0 results |

---

## Project Structure

```
MedBridgeAI/
├── backend/
│   ├── api/
│   │   ├── main.py                    # FastAPI app, CORS, lifespan
│   │   └── routes.py                 # /api endpoints
│   ├── agents/
│   │   ├── supervisor/agent.py       # Embedding intent + multi-intent detection
│   │   ├── genie/agent.py            # Pandas queries + negation + IQR anomalies
│   │   ├── vector_search/agent.py    # RRF multi-vector search
│   │   ├── medical_reasoning/agent.py # Validation + Isolation Forest
│   │   ├── geospatial/agent.py       # BallTree spatial + Mahalanobis equity
│   │   └── planning/agent.py         # Capability scoring + 2-opt + QAOA + maximin
│   ├── core/
│   │   ├── config.py                 # Constants, specialty maps, API keys
│   │   ├── geocoding.py              # 3-stage geocoding (exact/boundary/fuzzy)
│   │   ├── llm.py                    # Groq LLM + token truncation
│   │   ├── preprocessing.py          # CSV → clean → dedup → geocode → documents
│   │   ├── vectorstore.py            # Qdrant multi-vector + query templates
│   │   ├── quantum.py                # QUBO TSP solver (Qiskit eigensolver)
│   │   └── databricks.py             # Databricks Vector Search dual-backend
│   └── orchestration/
│       └── graph.py                  # LangGraph StateGraph + self-correction
├── frontend/src/
│   ├── App.jsx                       # Layout, tabs, query handling, data extraction
│   ├── utils/renderMarkdown.jsx      # Shared markdown → JSX renderer
│   ├── api/client.js                 # API client
│   └── components/                   # ResultsPanel, MapView, ExplainPanel, etc.
├── databricks/
│   └── medbridge_mlops_pipeline.py   # MLflow + Delta tables notebook
└── data/
    └── Virtue Foundation Ghana v0.3 - Sheet1.csv
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Run a query through the full agent pipeline |
| `GET` | `/api/facilities` | All facilities (for map markers) |
| `GET` | `/api/stats` | Dataset statistics |
| `GET` | `/api/specialties` | Available medical specialties |
| `GET/POST` | `/api/planning/*` | Planning scenarios and execution |
| `GET/POST` | `/api/mlops/*` | Databricks MLOps pipeline status and triggers |

---

## Example Queries

| Category | Query |
|----------|-------|
| Counting | How many hospitals offer cardiology? |
| Negation | Facilities in Ashanti without orthopedic services |
| Proximity | Which facilities handle trauma near Kumasi? |
| Coverage | Where are the medical deserts in Ghana? |
| Validation | Find suspicious facility capability claims |
| Planning | Where should we deploy mobile eye care units? |
| Comparison | Compare Accra vs Northern Region healthcare |
| Resilience | Which specialties depend on a single facility? |
| Emergency | Plan an emergency route for a cardiac patient near Tamale |
| Quantum | Deploy a cardiologist near Accra *(with use_quantum: true)* |

---

## Environment Variables

```env
GROQ_API_KEY=your_groq_api_key              # Required — LLM synthesis
QDRANT_URL=your_qdrant_cluster_url          # Required — vector search
QDRANT_API_KEY=your_qdrant_api_key

# Optional — Databricks MLOps
DATABRICKS_HOST=your_databricks_host
DATABRICKS_TOKEN=your_databricks_token
VECTOR_SEARCH_BACKEND=qdrant                # or "databricks"
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite 6, Tailwind CSS v4, DaisyUI 5, Leaflet 1.9 |
| Backend | Python 3.11+, FastAPI, LangGraph |
| Vector DB | Qdrant Cloud (384-dim, 3 named vectors) / Databricks Vector Search |
| Embeddings | SentenceTransformer `all-MiniLM-L6-v2` |
| LLM | Groq Cloud |
| ML | scikit-learn (Isolation Forest, BallTree), rapidfuzz |
| Quantum | Qiskit 2.3 + qiskit-optimization 0.7 |
| MLOps | Databricks (MLflow, Delta tables, Model Serving) |
| Data | Virtue Foundation Ghana CSV — 987 rows → 797 unique facilities |

---

*MIT License*
