# MedBridge AI — System Architecture

> A multi-agent AI platform that helps humanitarian organizations (like Virtue Foundation) understand Ghana's healthcare landscape — finding gaps, planning routes, and detecting data anomalies across **797 medical facilities**.

---

## The Problem We Solve

Ghana has nearly 800 healthcare facilities spread across 16 regions, but the data about them is messy, incomplete, and hard to act on. An NGO planner trying to answer "Where should we send a cardiologist?" or "Which regions have no access to surgery?" would need to manually sift through spreadsheets for hours.

**MedBridge AI answers these questions in seconds** using 6 specialized AI agents that collaborate automatically.

---

## How It Works — At a Glance

```
  User asks a question in plain English
          │
          ▼
  ┌────────────────────┐
  │   Supervisor Agent  │  ← Understands the question's intent
  │   (Intent Router)   │     and picks the right expert agents
  └────────┬───────────┘
           │
     ┌─────┼─────────────────────────────────┐
     ▼     ▼         ▼         ▼             ▼
  ┌──────┐ ┌────────┐ ┌──────────┐ ┌──────┐ ┌────────┐
  │ Data │ │Facility│ │ Medical  │ │ Map  │ │ Action │
  │Analyst││ Finder ││ Validator ││Analyst││ Planner│
  └──┬───┘ └───┬────┘ └────┬─────┘ └──┬───┘ └───┬───┘
     └─────────┴──────┬────┴──────────┴─────────┘
                      ▼
              ┌──────────────┐
              │  Aggregator   │ ← Combines all results and
              │  + LLM Summary│   generates a plain-English answer
              └──────┬───────┘
                     ▼
              Final answer + interactive map
```

---

## The 6 AI Agents

Each agent is a specialist. The Supervisor reads the user's question and decides which agents to activate — sometimes one, sometimes multiple in sequence.

### 1. Supervisor Agent — The Brain

**What it does:** Reads the user's question and figures out what kind of help is needed.

**How:** Uses a 3-tier classification system:
1. **Embedding similarity** — Converts the question to a 384-dimension vector and compares it against known question patterns using cosine similarity
2. **Regex pattern matching** — Keyword-based fallback with 13 pattern sets
3. **LLM fallback** — If still uncertain (confidence below 45%), asks the Groq LLM to classify

**Understands 14 types of questions:** counting, comparisons, anomaly detection, validation, distance queries, coverage gaps, medical deserts, single points of failure, facility lookup, service search, specialty search, planning, and more.

**Smart routing:** Some questions need multiple agents working in sequence. For example, "find medical deserts" activates both the **Map Analyst** (to compute distances) and the **Medical Validator** (to check which specialties are missing).

---

### 2. Data Analyst Agent (Genie)

**What it does:** Answers structured data questions — counts, aggregations, distributions, and statistical outliers.

**Example questions:**
- "How many hospitals are in Northern Region?"
- "Which region has the most facilities?"
- "Show the specialty distribution across Ghana"

**Key capabilities:**
- Filters by **15 medical specialties**, 4 facility types, 16 regions, and 13 equipment types
- Detects **negation** — "facilities without surgery" correctly returns facilities that lack surgery
- Finds **statistical outliers** using IQR (Interquartile Range) method — flags facilities with suspiciously high bed-to-doctor ratios
- Identifies **single points of failure** — specialties served by only 1–3 facilities nationwide

---

### 3. Facility Finder Agent (Vector Search)

**What it does:** Finds the most relevant facilities for any natural-language query using AI-powered semantic search.

**Example questions:**
- "Facilities that handle trauma near Kumasi"
- "Clinics with cardiac catheterization equipment"

**How it works:**
- Each facility is represented by **3 different vector embeddings** (384 dimensions each):
  - Full facility profile
  - Clinical details (procedures, equipment, capabilities)
  - Specialty context
- All 3 vectors are searched simultaneously, and results are combined using **Reciprocal Rank Fusion (RRF)** — a proven information retrieval technique that produces better rankings than any single search alone
- **Self-correction:** If a search returns 0 results (e.g., too-narrow location filter), the system automatically retries with relaxed filters

**Powered by:** Qdrant Cloud vector database with 797 facilities × 3 vectors = 2,391 indexed vectors

---

### 4. Medical Validator Agent (Medical Reasoning)

**What it does:** Checks whether facility claims are realistic and flags suspicious data.

**Five analysis capabilities:**

| Analysis | What It Checks | Example Finding |
|----------|---------------|-----------------|
| **Constraint Validation** | Does a facility claiming "neurosurgery" actually have a CT scanner, MRI, and ICU? | "Facility X claims cardiac surgery but has no ICU — confidence: 35%" |
| **Anomaly Detection** | Two-stage ML pipeline: Isolation Forest + Mahalanobis distance | "Facility Y claims 15 procedures but lists only 1 piece of equipment" |
| **Red Flag Detection** | Pattern matching for vague claims, visiting specialist dependencies, temporary services | "Facility Z's capabilities mention 'visiting specialist' — service may not be permanent" |
| **Coverage Gap Analysis** | Which regions lack specific specialties? | "Northern Region has 0 facilities offering dialysis — Critical gap" |
| **Single Point of Failure** | Which specialties depend on just 1–2 facilities? | "If Facility A closes, the entire region loses oncology access" |

**The anomaly detection pipeline** is particularly noteworthy:
- **Stage 1:** Isolation Forest (unsupervised ML) screens all facilities using 6 features
- **Stage 2:** Mahalanobis Distance confirms outliers using multivariate statistical analysis
- Only facilities flagged by **both** methods are reported — reducing false positives

---

### 5. Map Analyst Agent (Geospatial)

**What it does:** Spatial analysis — finds nearby facilities, identifies medical deserts, and measures healthcare equity across regions.

**Six capabilities:**
- **Radius search** — "Find all facilities within 50 km of Tamale"
- **Nearest facilities** — "What are the 5 closest hospitals to Bolgatanga?"
- **Coverage gap detection** — Divides Ghana into a grid (~468 cells) and finds areas where the nearest facility is more than 55 km away
- **Medical desert identification** — Checks each of Ghana's 16 region centers for access to specific specialties. Flags regions where the nearest facility is 75+ km away
- **Regional equity analysis** — Compares facility counts, doctor counts, beds, and specialties per region using Mahalanobis distance to find statistically underserved regions
- **City-to-city distance** — "How far is Accra from Tamale?"

**Powered by:** BallTree spatial index (O(log n) queries) with 767 geocoded facilities. Coordinates for **220+ Ghana cities** are built into the system.

---

### 6. Action Planner Agent (Planning)

**What it does:** Generates concrete, actionable plans for emergency response, specialist deployment, equipment distribution, and new facility placement.

**Five planning scenarios:**

| Scenario | What It Does | Key Algorithm |
|----------|-------------|---------------|
| **Emergency Routing** | Finds the nearest capable facility for a patient, with backup options | Capability scoring (0–100%) + geodesic distance |
| **Specialist Deployment** | Plans an optimal multi-stop tour for a visiting specialist | 2-opt local search (TSP optimization) |
| **Equipment Distribution** | Recommends where to place new equipment (e.g., CT scanners) based on regional need | Region-level need ranking |
| **New Facility Placement** | Suggests optimal GPS coordinates for new facilities to maximize coverage | Maximin algorithm over geographic grid |
| **Capacity Planning** | Identifies regions with critically low beds-per-facility or doctors-per-facility | Statistical threshold analysis |

**Capability scoring** evaluates each facility on a 0–100 scale:
- Does it have the right specialty? (+35 points)
- Does it have ICU/operating theater? (+20 points)
- Sufficient capacity? (+10 points)
- Has doctors on staff? (+10 points)

**Quantum computing integration:** For specialist deployment routing, MedBridge can optionally compare the classical 2-opt route against a **quantum-computed route** using Qiskit's QUBO (Quadratic Unconstrained Binary Optimization) formulation — demonstrating quantum advantage for combinatorial optimization.

---

## Orchestration — How Agents Collaborate

**Built with [LangGraph](https://python.langchain.com/docs/langgraph/)** — a framework for building stateful, multi-actor applications.

### The Flow

```
START → Supervisor → Agent 1 → Agent 2 → ... → Aggregator → END
```

1. **Supervisor** classifies the question and selects which agents to run (and in what order)
2. Each agent runs sequentially, contributing its results to a shared state
3. The **Aggregator** merges all results, extracts map-ready facility coordinates, and calls the LLM to generate a plain-English summary
4. The final response includes: structured data, LLM summary, map coordinates, and a reasoning trace

**Self-correction:** If vector search returns 0 results, the system automatically retries with broader filters before giving up.

**Agent caching:** All agents are initialized once at startup and reused across requests — keeping response times fast (typically under 5 seconds).

---

## Technology Stack

### Backend
| Technology | Role |
|-----------|------|
| **Python 3.13** | Core language |
| **FastAPI** | REST API framework (10 endpoints) |
| **LangGraph** | Multi-agent orchestration |
| **Qdrant Cloud** | Vector database for semantic search |
| **Groq Cloud** | LLM inference (GPT-oss-120B primary, Llama 3.3 70B fallback) |
| **SentenceTransformers** | Embedding model (all-MiniLM-L6-v2, 384 dimensions) |
| **scikit-learn** | Isolation Forest, BallTree spatial index |
| **Qiskit** | Quantum computing for route optimization |
| **MLflow** | Experiment tracking and model monitoring |
| **Databricks** | MLOps pipeline (evaluation, serving, trace analysis) |

### Frontend
| Technology | Role |
|-----------|------|
| **React 19** | UI framework |
| **Vite 6** | Build tool |
| **Tailwind CSS v4 + DaisyUI 5** | Styling |
| **Leaflet 1.9** | Interactive maps with 5 visualization layers |
| **Chart.js** | Data visualizations |

### Data
| Metric | Value |
|--------|-------|
| Raw CSV rows | 987 |
| After deduplication | 797 unique facilities |
| Geocoded cities | 220+ across all 16 Ghana regions |
| Vector dimensions | 384 × 3 representations = 2,391 vectors |
| Medical specialties tracked | 15 |
| Equipment types tracked | 13 |

---

## Data Pipeline

The raw Virtue Foundation dataset (987 rows, 20 columns) goes through an automated cleaning pipeline:

```
Raw CSV (987 rows)
    │
    ├─ Clean: strip whitespace, parse JSON list columns, fix typos ("farmacy" → "pharmacy")
    │
    ├─ Deduplicate: score rows by data richness, merge duplicates, keep best data
    │   → 797 unique facilities
    │
    ├─ Geocode: map city names to GPS coordinates using a 220-city lookup table
    │   with 3-stage matching (exact → word-boundary → fuzzy/Levenshtein)
    │
    └─ Vectorize: create 3 semantic embeddings per facility, store in Qdrant Cloud
```

---

## Interactive Map Visualization

The map displays 5 types of overlays simultaneously:

| Layer | What It Shows |
|-------|-------------|
| **Facility markers** | All 797 facilities, color-coded by type (hospital, clinic, pharmacy, NGO, etc.) |
| **Route lines** | Emergency routes or specialist deployment tours with numbered stops |
| **Medical deserts** | Colored circles showing regions with no nearby healthcare (red = critical, orange = high, yellow = moderate) |
| **Coverage cold spots** | Points where the nearest facility is abnormally far away |
| **Placement suggestions** | Diamond markers showing recommended locations for new facilities |

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/query` | Main entry point — accepts any natural-language question |
| `GET /api/facilities` | Returns all 797 facilities with metadata |
| `GET /api/stats` | Dashboard statistics (facility count, specialties, regions) |
| `POST /api/planning/execute` | Direct access to the 5 planning scenarios |
| `POST /api/routing-map` | Route planning with map data |
| `GET /api/mlops/status` | Databricks/MLflow pipeline health |

Every query response includes:
- **Structured results** — agent-specific data (counts, lists, scores)
- **Plain-English summary** — LLM-generated explanation for non-technical users
- **Map data** — facility coordinates ready for visualization
- **Reasoning trace** — step-by-step explanation of which agents ran and why
- **Timing** — end-to-end processing time

---

## What Makes This Architecture Innovative

1. **Multi-agent collaboration** — Unlike a single-model chatbot, MedBridge routes each question to the right specialist agents. A coverage gap question activates geospatial + medical reasoning together.

2. **Three-vector semantic search with RRF** — Each facility has 3 different vector representations (general, clinical, specialty). Searching all 3 and fusing results with Reciprocal Rank Fusion produces better rankings than any single embedding.

3. **Two-stage anomaly detection** — Isolation Forest + Mahalanobis distance with AND logic minimizes false positives. The system doesn't just find outliers — it explains *why* each facility is suspicious.

4. **Self-correcting search** — If a query is too specific and returns nothing, the system automatically broadens the search and retries.

5. **Quantum-classical comparison** — For route optimization, MedBridge can compare a classical 2-opt solution against a quantum QUBO solution, demonstrating real quantum computing applications in healthcare logistics.

6. **Full explainability** — Every query produces a visible reasoning trace showing which agents ran, what they found, how confident the classification was, and how long each step took. This is critical for NGO planners who need to trust the system's recommendations.

7. **220-city geocoding** — The original dataset had no GPS coordinates. We built a comprehensive geocoding system covering 220+ Ghana cities with a 3-stage matching pipeline (exact → word-boundary → fuzzy).

---

## Project Structure

```
medbridge/
├── backend/
│   ├── agents/
│   │   ├── supervisor/        ← Intent classification & routing
│   │   ├── genie/             ← Data analysis (counts, aggregations, outliers)
│   │   ├── vector_search/     ← Semantic facility search (Qdrant + RRF)
│   │   ├── medical_reasoning/ ← Validation, anomaly detection, coverage gaps
│   │   ├── geospatial/        ← Spatial analysis (BallTree, deserts, equity)
│   │   └── planning/          ← Emergency routing, deployment, placement
│   ├── orchestration/         ← LangGraph multi-agent workflow
│   ├── core/                  ← LLM, vectorstore, geocoding, config, quantum
│   └── api/                   ← FastAPI routes & server
├── frontend/
│   └── src/
│       ├── components/        ← React UI (map, results, planning panel)
│       └── api/               ← API client
├── databricks/                ← MLOps notebooks (evaluation, pipeline, traces)
├── data/                      ← Virtue Foundation dataset + prompt configs
└── qdrant_storage/            ← Local vector DB fallback
```

**Total codebase:** ~6,000 lines of Python backend + ~2,000 lines of React frontend
