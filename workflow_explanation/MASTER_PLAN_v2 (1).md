# 🏥 MedBridge AI: Intelligent Healthcare Coordination System
## Hackathon Master Plan v2.0 — Ambitious, Practical, Innovative

---

## 📋 Executive Summary

**Mission**: Build an agentic AI system that extracts, verifies, and reasons over medical facility data to reduce patient-to-treatment time by 100× — transforming the Virtue Foundation's Ghana dataset into actionable healthcare intelligence.

**Key Differentiators**:
1. **Confidence-Aware IDP** — Not just extraction, but uncertainty quantification
2. **Unified Medical Knowledge Graph** — Single graph, multiple reasoning modes
3. **Progressive Quantum Enhancement** — Classical-first, quantum where it outperforms
4. **Citation-Traced Agentic Reasoning** — Full transparency at every step

---

## 🎯 Challenge Alignment Matrix

| Evaluation Criteria | Weight | Our Approach | Innovation Level |
|---------------------|--------|--------------|------------------|
| **Technical Accuracy** | 35% | Constraint validation + anomaly detection + confidence scoring | ⭐⭐⭐⭐⭐ |
| **IDP Innovation** | 30% | Multi-pass extraction + evidence weighting + semantic normalization | ⭐⭐⭐⭐⭐ |
| **Social Impact** | 25% | Medical desert mapping + accessibility analysis + resource gap identification | ⭐⭐⭐⭐⭐ |
| **User Experience** | 10% | Natural language interface + interactive map + plain-language explanations | ⭐⭐⭐⭐ |

---

## 📊 VF Agent Requirements Mapping (MoSCoW Analysis)

### Agent Architecture Components (From VF Spec)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REQUIRED AGENT COMPONENTS                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. SUPERVISOR AGENT
   └── Simple router that recognizes intent and delegates to sub-agents

2. GENIE CHAT (Text2SQL)
   └── Databricks agent converting plaintext → SQL queries

3. GEOSPATIAL CALCULATION
   └── Non-standard calculations (geodesic distance, travel time)

4. MEDICAL REASONING AGENT
   └── Adds context, modifies queries, performs reasoning on results

5. VECTOR SEARCH WITH FILTERING
   └── Semantic lookup on plaintext + metadata filtering

6. EXTERNAL DATA INTEGRATION
   └── Data not in FDR, queried in real-time or added to workspace
```

### MUST HAVE Questions (Critical for 35% Technical Accuracy)

| ID | Question | Architecture | Our Implementation |
|----|----------|--------------|-------------------|
| **1.1** | How many hospitals have cardiology? | Genie Chat | Text2SQL → facility_capabilities table |
| **1.2** | How many hospitals in [region] can perform [procedure]? | Genie Chat | Text2SQL with parameterized filters |
| **1.3** | What services does [Facility Name] offer? | Vector Search + Filtering | Semantic search on extracted capabilities |
| **1.4** | Are there any clinics in [Area] that do [Service]? | Vector Search + Filtering | Geo-filtered semantic search |
| **1.5** | Which region has the most [Type] hospitals? | Genie Chat | Aggregation SQL query |
| **2.1** | Hospitals treating [condition] within [X] km of [location]? | Genie + Geospatial | PostGIS/Haversine distance calculation |
| **2.3** | Largest geographic "cold spots" where procedure absent? | Genie + Geospatial | Voronoi analysis + coverage gaps |
| **4.4** | Facilities claiming unrealistic procedures for size? | Medical Reasoning + Genie | Constraint validation engine |
| **4.7** | Correlations between facility characteristics? | Genie Chat | Statistical correlation queries |
| **4.8** | High procedure breadth vs minimal infrastructure? | Medical Reasoning + Genie | Anomaly detection: claims vs signals |
| **4.9** | Things that shouldn't move together? | Medical Reasoning + Genie | Constraint violation detection |
| **6.1** | Where is workforce for [subspecialty] practicing? | Medical Reasoning + Genie | Staffing extraction + aggregation |
| **7.5** | Procedures depending on very few facilities? | Medical Reasoning + Genie | Single-point-of-failure analysis |
| **7.6** | Oversupply concentration vs scarcity? | Medical Reasoning + Genie | Distribution analysis |
| **8.3** | Gaps where no organizations working despite need? | Medical Reasoning + Genie + Geo + External | Desert detection + NGO overlay |

### SHOULD HAVE Questions (High Priority)

| ID | Question | Architecture | Our Implementation |
|----|----------|--------------|-------------------|
| **3.1** | Facilities claiming subspecialty but lacking equipment? | Genie + Completeness | Constraint graph: capability → requirements |
| **3.4** | % facilities with procedure + minimum equipment? | Medical Reasoning + VS + Genie | Equipment-procedure correlation |
| **3.5** | Procedures corroborated by multiple sources? | Genie + Unknown | Evidence aggregation scoring |
| **4.1** | Website quality vs actual capabilities correlation? | Medical Reasoning + Genie | Quality signal extraction |
| **4.2** | High bed-to-OR ratios indicating misrepresentation? | Genie Chat | Ratio anomaly detection |
| **4.3** | Abnormal patterns where features don't match? | Medical Reasoning + Genie | Multi-feature consistency check |
| **4.5** | Physical features correlating with advanced capabilities? | Medical Reasoning + Genie | Feature importance analysis |
| **4.6** | Subspecialty claims vs supporting infrastructure? | Medical Reasoning + Genie | Claim validation engine |
| **6.4** | Evidence of visiting vs permanent specialists? | Medical Reasoning + Genie | Language pattern extraction |
| **6.5** | Surgical camps vs temporary missions? | Medical Reasoning + VS | "Camp", "mission", "visiting" detection |
| **6.6** | Services tied to individuals vs institutions? | Medical Reasoning + VS | Named entity extraction |
| **8.1** | NGOs providing overlapping services? | Medical Reasoning + Genie | Organization deduplication |
| **10.2** | "Sweet spot" facilities for intervention? | Medical Reasoning + Genie + External | Multi-criteria optimization |
| **10.3** | High-impact intervention site probability? | Medical Reasoning + Genie | Impact scoring model |

### COULD HAVE Questions (Stretch Goals)

| ID | Question | Architecture | Our Implementation |
|----|----------|--------------|-------------------|
| **2.2** | Disease prevalence areas with no treating facilities? | Genie + Geo + Medical + External | External disease data integration |
| **2.4** | Urban vs rural service gap for subspecialty? | Genie + Geo + Medical + External | Population-weighted coverage |
| **3.2** | Temporary vs permanently installed equipment? | VS Index Point Lookup | Language pattern: "mobile", "portable" |
| **3.3** | Permanent vs traveling services evidence? | Genie + Unknown | Service continuity scoring |
| **5.1-5.4** | Service classification & inference questions | Medical Reasoning + VS | Advanced NLP patterns |
| **7.1-7.4** | Resource distribution analysis | Medical Reasoning + Genie + External | Gap analysis with external data |
| **9.1-9.6** | Unmet needs & demand analysis | Medical Reasoning + Genie + External | Demographic integration |
| **10.1, 10.4** | WHO benchmarking comparisons | Medical Reasoning + Genie + External | Standards database integration |

---

## 🏗️ System Architecture (Aligned with VF Agent Spec)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MEDBRDIGE AI - SYSTEM OVERVIEW                       │
│                    (Mapped to VF Agent Components)                          │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────┐
                    │   USER INTERFACE LAYER          │
                    │  • Natural Language Queries     │
                    │  • Interactive Map Dashboard    │
                    │  • Plain-Language Reports       │
                    └───────────────┬─────────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │   SUPERVISOR AGENT (Router)     │  ← VF Spec Component
                    │  • Intent Recognition           │
                    │  • Query Classification         │
                    │  • Sub-Agent Delegation         │
                    │  • MLflow Tracing (Citations)   │
                    └───────────────┬─────────────────┘
                                    │
        ┌───────────────┬───────────┼───────────┬───────────────┐
        │               │           │           │               │
┌───────▼───────┐ ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐ ┌───────▼───────┐
│ GENIE CHAT    │ │ VECTOR    │ │ GEO   │ │ MEDICAL   │ │ EXTERNAL DATA │
│ (Text2SQL)    │ │ SEARCH    │ │ CALC  │ │ REASONING │ │ INTEGRATION   │
│               │ │           │ │       │ │ AGENT     │ │               │
│ • SQL Gen     │ │ • Semantic│ │• Dist │ │ • Context │ │ • WHO Data    │
│ • Aggregation │ │ • Filter  │ │• Time │ │ • Validate│ │ • Demographics│
│ • Joins       │ │ • Ranking │ │• Cover│ │ • Anomaly │ │ • Disease Prev│
└───────┬───────┘ └─────┬─────┘ └───┬───┘ └─────┬─────┘ └───────┬───────┘
        │               │           │           │               │
        └───────────────┴───────────┴─────┬─────┴───────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   REASONING & VALIDATION ENGINE           │
                    │  • Unified Knowledge Graph                │
                    │  • Constraint Propagation                 │
                    │  • Confidence Inference                   │
                    │  • Anomaly Detection                      │
                    └─────────────────────┬─────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
┌───────▼───────┐              ┌──────────▼──────────┐              ┌───────▼───────┐
│ VECTOR STORE  │              │ KNOWLEDGE GRAPH     │              │ QUANTUM MODULE│
│ (FAISS/Lance) │              │ (NetworkX)          │              │ (Qiskit)      │
│               │              │                     │              │               │
│ • Embeddings  │              │ • Facilities        │              │ • QAOA        │
│ • Similarity  │              │ • Capabilities      │              │ • Hybrid Opt  │
│ • Filtering   │              │ • Requirements      │              │ • Allocation  │
└───────┬───────┘              └──────────┬──────────┘              └───────┬───────┘
        │                                 │                                 │
        └─────────────────────────────────┼─────────────────────────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   IDP ENGINE (Core Innovation)            │
                    │  • Multi-Pass Extraction                  │
                    │  • Schema Validation                      │
                    │  • Evidence Scoring                       │
                    │  • Semantic Normalization                 │
                    └─────────────────────┬─────────────────────┘
                                          │
                    ┌─────────────────────▼─────────────────────┐
                    │   DATA LAYER (Databricks)                 │
                    │  • Virtue Foundation Ghana Dataset        │
                    │  • Delta Lake Tables                      │
                    │  • Schema Registry                        │
                    └───────────────────────────────────────────┘
```

### Agent Routing Logic (Supervisor Agent)

```python
ROUTING_RULES = {
    # Basic Queries (1.x) → Genie Chat or Vector Search
    "count_facilities": "genie_chat",
    "list_services": "vector_search",
    "find_clinics": "vector_search",
    "region_comparison": "genie_chat",
    
    # Geospatial (2.x) → Genie + Geo Calculation
    "distance_query": ["genie_chat", "geospatial_calc"],
    "coverage_gaps": ["genie_chat", "geospatial_calc"],
    "cold_spots": ["genie_chat", "geospatial_calc"],
    
    # Validation (3.x) → Medical Reasoning + Genie
    "equipment_verification": ["medical_reasoning", "genie_chat"],
    "claim_validation": ["medical_reasoning", "vector_search"],
    
    # Anomaly Detection (4.x) → Medical Reasoning + Genie
    "suspicious_claims": ["medical_reasoning", "genie_chat"],
    "ratio_anomalies": "genie_chat",
    "correlation_check": ["medical_reasoning", "genie_chat"],
    
    # Workforce (6.x) → Medical Reasoning + Genie
    "specialist_location": ["medical_reasoning", "genie_chat"],
    "visiting_vs_permanent": ["medical_reasoning", "vector_search"],
    
    # Resource Gaps (7.x) → Medical Reasoning + Genie
    "single_provider": ["medical_reasoning", "genie_chat"],
    "oversupply_analysis": ["medical_reasoning", "genie_chat"],
    
    # NGO Analysis (8.x) → Medical Reasoning + Genie + External
    "ngo_gaps": ["medical_reasoning", "genie_chat", "geospatial_calc", "external_data"],
    
    # Optimization → Quantum Module (when beneficial)
    "resource_allocation": ["medical_reasoning", "quantum_optimizer"],
    "deployment_planning": ["medical_reasoning", "quantum_optimizer"],
}
```

---

## 📦 Module Breakdown (Aligned with VF Agent Components)

### Module 1: Data Ingestion & Preparation
**Purpose**: Load, validate, and prepare the Virtue Foundation Ghana dataset

```
Priority: 🔴 CRITICAL (Foundation)
Time Estimate: 2-3 hours

Components:
├── data_loader.py
│   ├── load_ghana_facilities()      # Load CSV/JSON from VF dataset
│   ├── validate_schema()            # Check against provided schema
│   └── detect_data_quality_issues() # Missing values, inconsistencies
│
├── schema_registry.py
│   ├── FacilitySchema (Pydantic)    # Core facility model
│   ├── CapabilitySchema             # Medical capabilities
│   ├── StaffingSchema               # Personnel data
│   └── EquipmentSchema              # Equipment inventory
│
└── delta_lake_setup.py              # Databricks Delta Lake tables
    ├── raw_facilities               # Original data
    ├── processed_facilities         # Cleaned & enriched
    └── extraction_results           # IDP outputs
```

**Key Innovation**: Schema-aware ingestion with automatic type inference and quality scoring

---

### Module 2: Intelligent Document Parsing (IDP) Engine
**Purpose**: Extract structured information from unstructured text with confidence awareness

```
Priority: 🔴 CRITICAL (30% of score)
Time Estimate: 6-8 hours

Pipeline Architecture:
┌─────────────────────────────────────────────────────────────────────┐
│                    MULTI-PASS IDP PIPELINE                          │
└─────────────────────────────────────────────────────────────────────┘

Pass 1: RAPID EXTRACTION
├── Input: Raw free-form text fields
├── Method: Few-shot LLM prompting with Pydantic output
├── Output: Initial structured extraction
└── Confidence: Base confidence from LLM

Pass 2: SEMANTIC ENRICHMENT
├── Input: Pass 1 output + Medical ontology
├── Method: Embedding similarity to canonical terms
├── Output: Normalized medical terminology
└── Confidence: Adjusted by semantic match score

Pass 3: CROSS-REFERENCE VALIDATION
├── Input: Pass 2 output + Facility metadata
├── Method: Constraint checking (equipment → procedures possible)
├── Output: Validated claims with flags
└── Confidence: Penalized for constraint violations

Pass 4: EVIDENCE AGGREGATION
├── Input: All passes + Source documents
├── Method: Evidence graph construction
├── Output: Final extraction with citations
└── Confidence: Weighted by evidence strength

Output Schema:
{
  "facility_id": "GH_014",
  "extracted_capabilities": [
    {
      "capability": "cesarean_section",
      "normalized_term": "SURGICAL_OBSTETRIC_EMERGENCY",
      "status": "available",
      "confidence": 0.87,
      "evidence": {
        "direct_mentions": ["row_102", "row_118"],
        "supporting_context": ["row_45"],
        "required_equipment_present": true,
        "required_staff_present": false,
        "constraint_violations": ["missing_anesthetist"]
      },
      "extraction_trace": {
        "pass_1_confidence": 0.92,
        "pass_2_adjustment": -0.02,
        "pass_3_adjustment": -0.03,
        "pass_4_adjustment": 0.00
      }
    }
  ]
}
```

**Key Innovations**:
1. **Multi-pass confidence decay** — Each validation step adjusts confidence
2. **Constraint-aware extraction** — Claims validated against medical logic
3. **Full citation trail** — Every claim traceable to source rows

---

### Module 3: Vector Intelligence Layer
**Purpose**: Semantic search and similarity-based reasoning

```
Priority: 🟡 HIGH
Time Estimate: 3-4 hours

Components:
├── embedding_generator.py
│   ├── embed_facilities()           # Facility-level embeddings
│   ├── embed_capabilities()         # Capability descriptions
│   ├── embed_procedures()           # Medical procedure terms
│   └── embed_equipment()            # Equipment mentions
│
├── vector_store.py (FAISS/LanceDB)
│   ├── facility_index               # For facility similarity search
│   ├── capability_index             # For capability matching
│   └── medical_ontology_index       # For term normalization
│
└── semantic_search.py
    ├── find_similar_facilities()    # "Facilities like X"
    ├── match_capability_to_ontology() # Normalize free-form → standard
    └── detect_semantic_anomalies()  # Outlier embeddings
```

**Integration with IDP**: Embeddings power Pass 2 (semantic normalization) of the IDP pipeline

---

### Module 3.5: VF Agent Sub-Components (NEW - Per Spec)
**Purpose**: Implement the exact agent components specified in VF requirements

```
Priority: 🔴 CRITICAL (Core Architecture)
Time Estimate: 8-10 hours total

┌─────────────────────────────────────────────────────────────────────────────┐
│              VF AGENT COMPONENT IMPLEMENTATIONS                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 3.5.1 Supervisor Agent (Router)
```python
# agents/supervisor.py
Purpose: Intent recognition and query routing to appropriate sub-agents

Implementation:
├── IntentClassifier
│   ├── classify_query(text) → QueryIntent
│   ├── extract_parameters(text, intent) → Dict
│   └── route_to_agents(intent) → List[Agent]
│
├── QueryIntent (Enum)
│   ├── COUNT_FACILITIES     # → Genie Chat
│   ├── FIND_SERVICES        # → Vector Search
│   ├── DISTANCE_QUERY       # → Genie + Geo
│   ├── VALIDATE_CLAIMS      # → Medical Reasoning + Genie
│   ├── DETECT_ANOMALIES     # → Medical Reasoning + Genie
│   ├── WORKFORCE_ANALYSIS   # → Medical Reasoning + Genie
│   ├── COVERAGE_GAPS        # → Genie + Geo + Medical
│   └── RESOURCE_ALLOCATION  # → Medical Reasoning + Quantum
│
└── OrchestrationEngine
    ├── execute_pipeline(query, agents) → Result
    ├── merge_results(results: List) → FinalResult
    └── attach_citations(result) → CitedResult

VF Questions Handled:
- ALL questions routed through supervisor
- Intent maps directly to question categories 1.x-10.x
```

#### 3.5.2 Genie Chat (Text2SQL Agent)
```python
# agents/genie_chat.py
Purpose: Convert natural language to SQL queries on Delta Lake tables

Implementation:
├── Text2SQLEngine
│   ├── parse_question(text) → SQLQuery
│   ├── execute_query(sql) → DataFrame
│   └── format_response(df, question) → NaturalLanguageResponse
│
├── SchemaContext
│   ├── facilities_table          # Core facility data
│   ├── capabilities_table        # Extracted capabilities
│   ├── equipment_table           # Equipment inventory
│   ├── staffing_table            # Personnel data
│   └── regions_table             # Geographic regions
│
├── QueryTemplates
│   ├── count_by_filter()         # Q1.1, Q1.2, Q1.5
│   ├── aggregate_by_region()     # Q1.5, Q7.5, Q7.6
│   ├── ratio_calculations()      # Q4.2, Q4.7
│   └── correlation_queries()     # Q4.7, Q4.8
│
└── SQLValidation
    ├── validate_syntax()
    ├── check_table_access()
    └── sanitize_inputs()

VF Questions Handled:
- 1.1: "How many hospitals have cardiology?" → SELECT COUNT(*) FROM facilities WHERE...
- 1.2: "Hospitals in [region] with [procedure]?" → JOIN + WHERE + COUNT
- 1.5: "Which region has most [Type]?" → GROUP BY region ORDER BY COUNT DESC
- 4.2: "High bed-to-OR ratios?" → SELECT facility, beds/operating_rooms AS ratio...
- 4.7: "Correlations between characteristics?" → Statistical SQL functions
```

#### 3.5.3 Geospatial Calculation Module
```python
# agents/geospatial.py
Purpose: Non-standard geospatial calculations (distance, travel time, coverage)

Implementation:
├── DistanceCalculator
│   ├── geodesic_distance(coord1, coord2) → km
│   ├── travel_time_estimate(coord1, coord2, mode) → minutes
│   └── facilities_within_radius(center, radius_km) → List[Facility]
│
├── CoverageAnalyzer
│   ├── voronoi_partition(facilities) → Regions
│   ├── identify_cold_spots(capability, max_distance) → List[ColdSpot]
│   ├── coverage_radius(facility, capability) → km
│   └── population_coverage(facility) → PopulationCount
│
├── AccessibilityScorer
│   ├── travel_time_to_nearest(location, capability) → minutes
│   ├── accessibility_index(region) → Score
│   └── medical_desert_detection(capability, threshold_km) → List[Desert]
│
└── GeoVisualization
    ├── generate_heatmap(metric) → FoliumMap
    ├── add_facility_markers(facilities) → FoliumMap
    └── overlay_coverage_zones(zones) → FoliumMap

VF Questions Handled:
- 2.1: "Hospitals within [X] km of [location]?" → geodesic_distance filter
- 2.3: "Largest cold spots?" → voronoi_partition + identify_cold_spots
- 2.2: "Disease areas with no treating facilities?" → coverage overlay
- 8.3: "Gaps where no organizations working?" → desert_detection

Algorithms:
- Haversine formula for geodesic distance
- Voronoi diagrams for coverage partitioning
- Travel time estimation (road network or euclidean approximation)
- K-center problem for optimal facility placement
```

#### 3.5.4 Medical Reasoning Agent
```python
# agents/medical_reasoning.py
Purpose: Add medical context, validate claims, detect anomalies, perform reasoning

Implementation:
├── MedicalContextEngine
│   ├── enrich_query(query) → EnrichedQuery
│   │   └── "cardiology" → includes: ECG, echo, cath lab, interventional...
│   ├── expand_procedure(procedure) → RequiredResources
│   │   └── "cesarean" → requires: surgeon, anesthetist, OR, blood bank...
│   └── medical_synonyms(term) → List[Synonym]
│
├── ClaimValidator
│   ├── validate_capability_claim(facility, capability) → ValidationResult
│   │   └── Check: Does facility have required equipment + staff?
│   ├── check_procedure_requirements(procedure) → RequirementCheck
│   │   └── Q3.1: "Claims subspecialty but lacks equipment?"
│   ├── detect_unrealistic_claims(facility) → List[SuspiciousClaim]
│   │   └── Q4.4: "Unrealistic procedures for size?"
│   └── verify_equipment_procedure_match(facility) → MatchScore
│       └── Q3.4: "% with procedure + minimum equipment?"
│
├── AnomalyDetector
│   ├── detect_ratio_anomalies(facility) → List[Anomaly]
│   │   └── Q4.2: Bed-to-OR ratio outliers
│   ├── detect_correlation_breaks(facility) → List[Anomaly]
│   │   └── Q4.9: "Things that shouldn't move together"
│   ├── detect_claim_infrastructure_mismatch(facility) → List[Mismatch]
│   │   └── Q4.8: "200 procedures + minimal equipment"
│   └── score_overall_credibility(facility) → CredibilityScore
│
├── WorkforceAnalyzer
│   ├── extract_staffing_signals(text) → StaffingInfo
│   │   └── Q6.1: "Where is workforce practicing?"
│   ├── classify_service_permanence(text) → PermanenceClassification
│   │   └── Q6.4: "Visiting vs permanent specialists?"
│   ├── detect_surgical_camps(text) → List[CampIndicator]
│   │   └── Q6.5: "Surgical camps or temporary missions?"
│   └── identify_individual_dependency(text) → List[IndividualService]
│       └── Q6.6: "Services tied to individuals?"
│
└── ResourceGapAnalyzer
    ├── identify_single_providers(capability) → List[SingleProviderRisk]
    │   └── Q7.5: "Procedures depending on very few facilities?"
    ├── analyze_supply_distribution(capability) → DistributionAnalysis
    │   └── Q7.6: "Oversupply vs scarcity?"
    └── classify_gap_type(region) → GapType
        └── Q7.1: "Lack of equipment, training, or practitioners?"

CONSTRAINT KNOWLEDGE BASE:
```python
PROCEDURE_REQUIREMENTS = {
    "cesarean_section": {
        "hard_requirements": ["surgeon", "anesthetist", "operating_room", "blood_bank"],
        "soft_requirements": ["nicu", "icu"],
        "equipment": ["surgical_instruments", "anesthesia_machine", "monitors"]
    },
    "cataract_surgery": {
        "hard_requirements": ["ophthalmologist", "operating_microscope"],
        "soft_requirements": ["phaco_machine"],
        "equipment": ["surgical_microscope", "phaco_unit", "iol_inventory"]
    },
    # ... 50+ procedures with requirements
}

FACILITY_SIZE_EXPECTATIONS = {
    "small_clinic": {"max_procedures": 20, "max_beds": 20, "max_specialties": 3},
    "district_hospital": {"max_procedures": 50, "max_beds": 100, "max_specialties": 8},
    "regional_hospital": {"max_procedures": 100, "max_beds": 300, "max_specialties": 15},
    "teaching_hospital": {"max_procedures": 200, "max_beds": 1000, "max_specialties": 30}
}
```

#### 3.5.5 Vector Search with Filtering
```python
# agents/vector_search.py
Purpose: Semantic lookup on plaintext fields + metadata filtering

Implementation:
├── SemanticSearchEngine
│   ├── search_capabilities(query, filters) → List[FacilityCapability]
│   │   └── Q1.3: "What services does [Facility] offer?"
│   ├── search_equipment(query, region_filter) → List[Equipment]
│   ├── search_procedures(query, facility_type_filter) → List[Procedure]
│   └── search_free_text(query, metadata_filters) → List[Match]
│       └── Q1.4: "Clinics in [Area] that do [Service]?"
│
├── FilterEngine
│   ├── apply_region_filter(results, region) → FilteredResults
│   ├── apply_facility_type_filter(results, type) → FilteredResults
│   ├── apply_capability_filter(results, capability) → FilteredResults
│   └── apply_confidence_threshold(results, min_conf) → FilteredResults
│
├── IndexPointLookup (For specific pattern matching)
│   ├── find_visiting_surgeon_mentions() → List[Match]
│   │   └── Q6.4, Q6.5: "visiting surgeon", "camp", "twice a year"
│   ├── find_temporary_equipment_mentions() → List[Match]
│   │   └── Q3.2: "brought in", "mobile", "temporary"
│   ├── find_referral_language() → List[Match]
│   │   └── Q5.2: "we arrange", "we collaborate", "we send to"
│   └── find_individual_names() → List[Match]
│       └── Q6.6: "Dr. [Name]", "visiting consultant"
│
└── RankingEngine
    ├── rank_by_relevance(results) → RankedResults
    ├── rank_by_confidence(results) → RankedResults
    └── rank_by_recency(results) → RankedResults

VF Questions Handled:
- 1.3: "Services at [Facility]?" → Vector search on capability embeddings
- 1.4: "Clinics in [Area] with [Service]?" → Semantic search + geo filter
- 3.2: "Temporary equipment?" → Pattern search: "mobile", "portable", "temporary"
- 5.1-5.2: Service classification → Pattern search on service language
- 6.4-6.6: Workforce patterns → Pattern search on staffing language
```

#### 3.5.6 External Data Integration
```python
# agents/external_data.py
Purpose: Integrate data not in FDR (real-time or pre-loaded)

Implementation:
├── ExternalDataSources
│   ├── WHOStandardsDB
│   │   └── Q10.1: Specialist ratios, guidelines
│   ├── PopulationData
│   │   └── Q2.2, Q9.x: Demographics, disease prevalence
│   ├── NGORegistry
│   │   └── Q8.1, Q8.3: Active organizations, coverage areas
│   └── DiseasePrevalenceDB
│       └── Q2.2: Condition prevalence by region
│
├── DataLoaders
│   ├── load_who_standards() → WHOStandards
│   ├── load_population_data(country) → PopulationGrid
│   ├── load_ngo_registry() → NGOList
│   └── load_disease_prevalence(country) → DiseaseMap
│
└── DataJoiner
    ├── join_population_to_facilities(facilities, population) → EnrichedFacilities
    ├── join_disease_to_regions(regions, disease) → RiskRegions
    └── join_ngo_to_gaps(gaps, ngos) → CoverageAnalysis

VF Questions Handled:
- 2.2: "Disease prevalence areas with no facilities?" → Disease data + coverage
- 8.3: "Gaps where no organizations working?" → NGO registry + desert detection
- 9.x: "Unmet needs analysis" → Population + demographics
- 10.1: "Compare to WHO guidelines" → WHO standards lookup

COULD HAVE - External Data Sources to Consider:
- Ghana Health Service facility registry
- World Bank population data
- WHO Global Health Observatory
- Humanitarian OpenStreetMap (travel time)
```

---

### Module 4: Unified Medical Knowledge Graph
**Purpose**: Structured reasoning over facility capabilities, constraints, and geography

```
Priority: 🟡 HIGH
Time Estimate: 4-5 hours

Graph Schema (Single Graph, Multiple Edge Types):
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED KNOWLEDGE GRAPH                          │
└─────────────────────────────────────────────────────────────────────┘

NODE TYPES:
├── Facility          {id, name, location, type, coordinates}
├── Capability        {id, name, category, criticality}
├── Requirement       {id, type: staff|equipment|infrastructure}
├── Region            {id, name, population, coordinates}
├── Evidence          {id, source_row, text_snippet, timestamp}
└── Population_Center {id, name, population, coordinates}

EDGE TYPES:
├── HAS_CAPABILITY         (Facility) → (Capability)
│   └── properties: {confidence, status, evidence_ids}
│
├── REQUIRES               (Capability) → (Requirement)
│   └── properties: {type: hard|soft, criticality}
│
├── HAS_RESOURCE           (Facility) → (Requirement)
│   └── properties: {quantity, status, last_verified}
│
├── SUPPORTED_BY           (HAS_CAPABILITY) → (Evidence)
│   └── properties: {strength, recency}
│
├── LOCATED_IN             (Facility) → (Region)
│   └── properties: {coordinates}
│
├── SERVES_POPULATION      (Facility) → (Population_Center)
│   └── properties: {travel_time_minutes, distance_km}
│
└── CONTRADICTS            (Evidence) → (Evidence)
    └── properties: {contradiction_type}

REASONING QUERIES:
1. Capability Verification:
   "Does facility X truly have capability Y?"
   → Traverse HAS_CAPABILITY → check REQUIRES → verify HAS_RESOURCE

2. Medical Desert Detection:
   "Which population centers lack access to capability Y within T minutes?"
   → Query SERVES_POPULATION with travel_time constraint

3. Anomaly Detection:
   "Which facilities claim capabilities without required resources?"
   → Pattern match: HAS_CAPABILITY but NOT (REQUIRES → HAS_RESOURCE)

4. Evidence Strength:
   "How confident are we in facility X's claimed capabilities?"
   → Aggregate SUPPORTED_BY edge strengths
```

**Key Innovation**: Single graph supports all three original graph functions through edge-type filtering

---

### Module 5: Analysis & Anomaly Detection Agent
**Purpose**: Identify medical deserts, data anomalies, and infrastructure gaps

```
Priority: 🔴 CRITICAL (35% Technical Accuracy + 25% Social Impact)
Time Estimate: 5-6 hours

VF QUESTIONS DIRECTLY ADDRESSED BY THIS MODULE:
├── 2.3: Largest geographic cold spots (MUST HAVE)
├── 3.1: Facilities claiming subspecialty but lacking equipment (SHOULD HAVE)
├── 4.2: High bed-to-OR ratios (SHOULD HAVE)
├── 4.3: Abnormal patterns (SHOULD HAVE)
├── 4.4: Unrealistic procedures for size (MUST HAVE)
├── 4.7: Facility characteristic correlations (MUST HAVE)
├── 4.8: High procedure breadth vs minimal infrastructure (MUST HAVE)
├── 4.9: Things that shouldn't move together (MUST HAVE)
├── 7.5: Procedures depending on few facilities (MUST HAVE)
├── 7.6: Oversupply vs scarcity (MUST HAVE)
└── 8.3: Gaps where no organizations working (MUST HAVE)

Analysis Functions:
├── medical_desert_detector.py
│   ├── compute_coverage_radius()     # Voronoi-based coverage
│   ├── identify_underserved()        # Population vs. capability gaps
│   ├── calculate_accessibility()     # Travel time analysis
│   ├── rank_desert_severity()        # Prioritized intervention list
│   └── find_cold_spots(capability, max_km) → Q2.3
│
├── anomaly_detector.py
│   ├── detect_capability_mismatch()  # Q3.1: Claims vs. resources
│   ├── detect_ratio_anomalies()      # Q4.2: Bed-to-OR outliers
│   ├── detect_correlation_breaks()   # Q4.9: Things that shouldn't move together
│   ├── detect_size_claim_mismatch()  # Q4.4, Q4.8: Procedures vs infrastructure
│   ├── detect_outlier_facilities()   # Statistical anomalies
│   └── detect_suspicious_claims()    # Too-good-to-be-true patterns
│
├── gap_analyzer.py
│   ├── identify_single_providers()   # Q7.5: Single-point-of-failure
│   ├── analyze_supply_distribution() # Q7.6: Oversupply vs scarcity
│   ├── identify_ngo_gaps()           # Q8.3: Unserved despite need
│   ├── compute_referral_chains()     # Where must patients go?
│   └── estimate_coverage_impact()    # If facility X added capability Y
│
├── correlation_analyzer.py
│   ├── compute_feature_correlations() # Q4.7: What moves together
│   ├── detect_abnormal_patterns()     # Q4.3: Expected features don't match
│   └── build_correlation_matrix()     # Statistical analysis
│
└── confidence_aggregator.py
    ├── facility_confidence_score()   # Overall trust in facility data
    ├── regional_data_quality()       # Data completeness by region
    └── temporal_confidence_decay()   # Older data = lower confidence
```

**Anomaly Detection Algorithms (Mapped to VF Questions)**:
```python
# Q4.4 + Q4.8: Unrealistic Claims Detection
def detect_size_claim_mismatch(facility):
    """
    MUST HAVE: Facilities claiming unrealistic procedures for size
    MUST HAVE: High procedure breadth vs minimal infrastructure
    """
    size_category = classify_facility_size(facility)
    expected = FACILITY_SIZE_EXPECTATIONS[size_category]
    
    anomalies = []
    if facility.procedure_count > expected["max_procedures"]:
        anomalies.append({
            "type": "excessive_procedures",
            "claimed": facility.procedure_count,
            "expected_max": expected["max_procedures"],
            "severity": "HIGH"
        })
    if facility.specialty_count > expected["max_specialties"]:
        anomalies.append({
            "type": "excessive_specialties", 
            "claimed": facility.specialty_count,
            "expected_max": expected["max_specialties"],
            "severity": "MEDIUM"
        })
    return anomalies

# Q4.9: Things That Shouldn't Move Together
def detect_correlation_breaks(facility, correlation_rules):
    """
    MUST HAVE: Detect unexpected combinations
    Examples:
    - Large bed count + minimal surgical equipment
    - Advanced subspecialties + no supporting infrastructure
    """
    breaks = []
    
    # Rule: Beds should correlate with OR count
    if facility.bed_count > 100 and facility.or_count < 2:
        breaks.append({
            "rule": "beds_or_correlation",
            "observed": f"{facility.bed_count} beds, {facility.or_count} ORs",
            "expected": "100+ beds should have 2+ ORs",
            "severity": "HIGH"
        })
    
    # Rule: Subspecialties need supporting equipment
    for subspecialty in facility.subspecialties:
        required_equipment = SUBSPECIALTY_REQUIREMENTS[subspecialty]
        present = set(facility.equipment)
        missing = required_equipment - present
        if len(missing) > len(required_equipment) * 0.5:
            breaks.append({
                "rule": "subspecialty_equipment",
                "subspecialty": subspecialty,
                "missing_equipment": list(missing),
                "severity": "HIGH"
            })
    
    return breaks

# Q4.2: Ratio Anomaly Detection
def detect_ratio_anomalies(facility):
    """
    SHOULD HAVE: High bed-to-OR ratios indicating misrepresentation
    """
    anomalies = []
    
    if facility.or_count > 0:
        bed_or_ratio = facility.bed_count / facility.or_count
        if bed_or_ratio > 100:  # Typical is 20-50
            anomalies.append({
                "type": "bed_or_ratio",
                "ratio": bed_or_ratio,
                "threshold": 100,
                "interpretation": "May indicate inflated bed count or underreported ORs"
            })
    
    if facility.specialist_count > 0:
        procedure_specialist_ratio = facility.procedure_count / facility.specialist_count
        if procedure_specialist_ratio > 30:
            anomalies.append({
                "type": "procedure_specialist_ratio",
                "ratio": procedure_specialist_ratio,
                "threshold": 30,
                "interpretation": "More procedures claimed than specialists can support"
            })
    
    return anomalies

# Q3.1: Capability-Equipment Mismatch
def detect_capability_without_requirements(graph):
    """
    SHOULD HAVE: Facilities claiming subspecialty but lacking equipment
    Example: Claims "emergency surgery" but no surgeon on staff
    """
    violations = []
    for facility in graph.get_facilities():
        for capability in facility.capabilities:
            required = graph.get_requirements(capability)
            available = graph.get_resources(facility)
            missing = required - available
            if missing:
                violations.append({
                    "facility": facility.id,
                    "capability": capability,
                    "missing": list(missing),
                    "confidence_penalty": calculate_penalty(missing),
                    "vf_question": "3.1"
                })
    return violations

# Q7.5: Single Provider Risk Analysis
def identify_single_providers(capabilities, region=None):
    """
    MUST HAVE: Procedures depending on very few facilities
    """
    risks = []
    for capability in capabilities:
        providers = get_providers(capability, region)
        if len(providers) <= 2:
            risks.append({
                "capability": capability,
                "provider_count": len(providers),
                "providers": [p.id for p in providers],
                "risk_level": "CRITICAL" if len(providers) == 1 else "HIGH",
                "population_at_risk": sum(p.served_population for p in providers),
                "vf_question": "7.5"
            })
    return risks

# Q7.6: Supply Distribution Analysis
def analyze_supply_distribution(capability, regions):
    """
    MUST HAVE: Oversupply concentration vs scarcity
    """
    distribution = {}
    for region in regions:
        providers = get_providers(capability, region)
        population = region.population
        ratio = len(providers) / (population / 100000) if population > 0 else 0
        distribution[region.id] = {
            "providers": len(providers),
            "population": population,
            "ratio_per_100k": ratio,
            "classification": classify_supply(ratio)  # "oversupply", "adequate", "undersupply", "desert"
        }
    
    return {
        "capability": capability,
        "distribution": distribution,
        "oversupply_regions": [r for r, d in distribution.items() if d["classification"] == "oversupply"],
        "desert_regions": [r for r, d in distribution.items() if d["classification"] == "desert"],
        "vf_question": "7.6"
    }
```

---

### Module 6: Agentic Orchestrator with MLflow Tracing
**Purpose**: Coordinate multi-step reasoning with full citation tracing

```
Priority: 🔴 CRITICAL (Stretch Goal for Maximum Points)
Time Estimate: 4-5 hours

Agent Architecture (LangGraph):
┌─────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH STATE MACHINE                          │
└─────────────────────────────────────────────────────────────────────┘

STATES:
├── UNDERSTAND_QUERY      # Parse user intent
├── RETRIEVE_CONTEXT      # RAG + Graph lookup
├── EXTRACT_IF_NEEDED     # Run IDP on new text
├── REASON_OVER_DATA      # Graph traversal + analysis
├── OPTIMIZE_IF_COMPLEX   # Quantum/classical optimization
├── GENERATE_EXPLANATION  # Plain-language output
└── VISUALIZE_RESULTS     # Map + charts

TRANSITIONS:
understand_query → retrieve_context → [extract_if_needed] → reason_over_data
                                                                    ↓
                                           [optimize_if_complex] ←──┘
                                                    ↓
                                           generate_explanation
                                                    ↓
                                           visualize_results

MLflow Tracing Integration:
┌─────────────────────────────────────────────────────────────────────┐
│                    CITATION TRACING SYSTEM                          │
└─────────────────────────────────────────────────────────────────────┘

Every agent step logs:
{
  "step_id": "uuid-xxx",
  "step_name": "retrieve_context",
  "inputs": {
    "query": "Which facilities can perform C-sections?",
    "filters": {"region": "Greater Accra"}
  },
  "outputs": {
    "facilities_found": 12,
    "facility_ids": ["GH_001", "GH_014", ...]
  },
  "data_used": {
    "rows_accessed": ["row_45", "row_102", "row_118"],
    "graph_nodes_traversed": ["facility:GH_001", "capability:cesarean"],
    "embeddings_compared": 156
  },
  "confidence": 0.89,
  "duration_ms": 234
}

Final output includes citation rollup:
{
  "answer": "12 facilities can perform C-sections in Greater Accra...",
  "citations": {
    "row_level": ["row_45", "row_102", "row_118", ...],
    "step_level": [
      {"step": "retrieve_context", "contribution": "identified candidates"},
      {"step": "reason_over_data", "contribution": "verified capabilities"},
      {"step": "generate_explanation", "contribution": "synthesized answer"}
    ]
  },
  "confidence": 0.89,
  "data_quality_warnings": ["Facility GH_003 data is 18 months old"]
}
```

**Key Innovation**: Step-level citations with contribution explanations — judges can trace exactly how each answer was derived

---

### Module 7: Quantum-Enhanced Optimization (Progressive)
**Purpose**: Apply quantum computing ONLY where it demonstrably outperforms classical

```
Priority: 🟢 ENHANCEMENT (Use strategically)
Time Estimate: 3-4 hours

Philosophy: Classical-First, Quantum-When-Better
┌─────────────────────────────────────────────────────────────────────┐
│                    HYBRID OPTIMIZATION STRATEGY                     │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: Identify Optimization Problems
├── Resource Allocation: Which doctors to which facilities?
├── Coverage Optimization: Where to place new clinics?
├── Routing: Optimal patient referral paths?
└── Scheduling: How to coordinate mobile health units?

STEP 2: Classical Baseline
├── Hungarian Algorithm (assignment)
├── Greedy Set Cover (coverage)
├── Dijkstra/A* (routing)
└── Constraint Programming (scheduling)

STEP 3: Quantum Enhancement (Only if beneficial)
├── QAOA for combinatorial subproblems
├── Quantum annealing simulation
└── Hybrid variational methods

IMPLEMENTATION:
optimizer.py
├── class HybridOptimizer:
│   ├── solve_classical(problem) → solution, time, quality
│   ├── solve_quantum(problem) → solution, time, quality
│   ├── compare_methods(problem) → recommendation
│   └── solve_best(problem) → auto-selects optimal method
│
└── quantum_module.py (Qiskit)
    ├── formulate_qubo(problem)     # Convert to quantum form
    ├── run_qaoa(qubo, depth)       # Execute QAOA
    ├── run_vqe(qubo)               # Alternative variational
    └── decode_solution(result)     # Extract classical answer

USE CASE: Doctor-Facility Assignment
┌─────────────────────────────────────────────────────────────────────┐
│ PROBLEM: Assign 20 doctors to 50 facilities                         │
│ CONSTRAINTS: Skills must match needs, travel time < 2 hours        │
│ OBJECTIVE: Maximize population coverage, minimize gaps             │
└─────────────────────────────────────────────────────────────────────┘

Classical Solution:
- Hungarian algorithm: O(n³) → ~100ms for n=50
- Quality: Optimal for bipartite matching

Quantum Enhancement Opportunity:
- When constraints make problem non-bipartite
- When multiple objectives create Pareto frontier
- When solution space has many local optima

QAOA Application:
- Encode as Max-Cut variant on constraint graph
- Run low-depth QAOA (p=2-3) on Qiskit Aer simulator
- Compare solution quality to classical heuristics
- Use quantum result if demonstrably better

OUTPUT:
{
  "problem": "doctor_facility_assignment",
  "classical_solution": {...},
  "classical_time_ms": 87,
  "quantum_solution": {...},
  "quantum_time_ms": 2340,
  "quantum_advantage": false,  // Honest assessment
  "recommendation": "use_classical",
  "note": "Quantum showed advantage for >100 facilities with complex constraints"
}
```

**Key Innovation**: Honest quantum benchmarking — we show WHERE quantum helps, not just that we used it

---

### Module 8: User Interface & Visualization
**Purpose**: Make the system accessible to non-technical NGO planners

```
Priority: 🟡 HIGH (10% of score, but crucial for demo)
Time Estimate: 4-5 hours

Components:
├── streamlit_app.py (Primary Interface)
│   ├── Natural language query input
│   ├── Results display with confidence indicators
│   ├── Citation drill-down panel
│   └── Map visualization integration
│
├── map_visualization.py (Folium/Plotly)
│   ├── Facility locations with capability icons
│   ├── Medical desert heatmap overlay
│   ├── Coverage radius visualization
│   ├── Recommended intervention markers
│   └── Interactive filtering by capability
│
└── report_generator.py
    ├── Plain-language summaries
    ├── Exportable PDF reports
    └── Data quality dashboard

USER EXPERIENCE FLOW:
┌─────────────────────────────────────────────────────────────────────┐
│ NGO Planner: "Where should we deploy 5 mobile surgery units        │
│              to reduce maternal mortality fastest?"                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ System Processing:                                                  │
│ 1. Parse intent → "optimize deployment" + "surgery" + "maternal"   │
│ 2. Retrieve → Facilities with/without surgical capability          │
│ 3. Analyze → Maternal mortality risk zones (medical deserts)       │
│ 4. Optimize → Best 5 locations for maximum impact                  │
│ 5. Explain → Why these locations, with confidence                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ OUTPUT:                                                             │
│                                                                     │
│ 📍 RECOMMENDED DEPLOYMENT LOCATIONS                                 │
│                                                                     │
│ 1. Volta Region - Ho District (Priority: CRITICAL)                 │
│    • Population served: 847,000                                    │
│    • Current travel time to surgery: 3.2 hours                     │
│    • Estimated lives impacted: 120/year                            │
│    • Confidence: 94%                                               │
│    • Citations: [rows 45, 102, 118] [View Evidence]                │
│                                                                     │
│ 2. Northern Region - Tamale Metro (Priority: HIGH)                 │
│    ...                                                              │
│                                                                     │
│ [🗺️ VIEW ON MAP] [📊 DETAILED ANALYSIS] [📄 EXPORT REPORT]         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗓️ Implementation Timeline

### Phase 1: Foundation (Hours 0-8)
```
┌────────────────────────────────────────────────────────────────┐
│ DELIVERABLE: Working data pipeline + basic IDP                 │
└────────────────────────────────────────────────────────────────┘

Hour 0-2: Environment Setup
├── Databricks workspace configuration
├── Python environment + dependencies
├── Load Virtue Foundation Ghana dataset
└── Verify schema alignment

Hour 2-5: IDP Engine Core
├── Implement Pass 1 (LLM extraction)
├── Define Pydantic schemas for all entity types
├── Build extraction prompt templates
└── Initial testing on sample data

Hour 5-8: Vector Store + Embeddings
├── Generate embeddings for facilities
├── Build FAISS/LanceDB index
├── Implement semantic search functions
└── Connect to IDP Pass 2 (normalization)

CHECKPOINT: Can extract structured data from free-form text ✓
```

### Phase 2: Intelligence Layer (Hours 8-18)
```
┌────────────────────────────────────────────────────────────────┐
│ DELIVERABLE: Graph reasoning + anomaly detection               │
└────────────────────────────────────────────────────────────────┘

Hour 8-12: Knowledge Graph
├── Build unified graph schema
├── Populate from IDP outputs
├── Implement constraint checking
└── Build capability verification queries

Hour 12-15: Analysis Agents
├── Medical desert detection algorithm
├── Anomaly detection (3 types)
├── Gap analysis functions
└── Confidence aggregation

Hour 15-18: Agentic Orchestration
├── LangGraph state machine
├── MLflow tracing integration
├── Citation collection system
└── End-to-end query flow

CHECKPOINT: Can answer complex queries with citations ✓
```

### Phase 3: Enhancement & Polish (Hours 18-28)
```
┌────────────────────────────────────────────────────────────────┐
│ DELIVERABLE: Full system with optimization + visualization     │
└────────────────────────────────────────────────────────────────┘

Hour 18-21: Quantum Module (Strategic)
├── Implement classical baseline optimizers
├── Build QAOA formulation for assignment
├── Benchmark classical vs quantum
└── Integrate into orchestrator

Hour 21-25: User Interface
├── Streamlit main application
├── Map visualization with Folium
├── Results display with citations
└── Report generation

Hour 25-28: Integration & Testing
├── End-to-end testing
├── Performance optimization
├── Documentation
└── Demo preparation

CHECKPOINT: Complete system ready for judging ✓
```

### Phase 4: Demo & Submission (Hours 28-30)
```
┌────────────────────────────────────────────────────────────────┐
│ DELIVERABLE: Polished demo + submission materials              │
└────────────────────────────────────────────────────────────────┘

Hour 28-29: Demo Script
├── Prepare compelling use cases
├── Record backup demo video
├── Prepare for judge questions
└── Test on fresh environment

Hour 29-30: Submission
├── Code cleanup
├── README finalization
├── Submission packaging
└── Final verification
```

---

## 📁 Project Structure

```
MED-Challenge/
├── README.md                    # Project overview + setup instructions
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
│
├── config/
│   ├── settings.py              # Configuration management
│   ├── prompts/                 # LLM prompt templates
│   └── schemas/                 # Pydantic model definitions
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/                    # Module 1: Data Layer
│   │   ├── loader.py            # Data ingestion
│   │   ├── validator.py         # Schema validation
│   │   └── delta_setup.py       # Databricks Delta Lake
│   │
│   ├── idp/                     # Module 2: IDP Engine
│   │   ├── extractor.py         # Multi-pass extraction
│   │   ├── normalizer.py        # Semantic normalization
│   │   ├── validator.py         # Constraint validation
│   │   └── confidence.py        # Confidence scoring
│   │
│   ├── vectors/                 # Module 3: Vector Intelligence
│   │   ├── embeddings.py        # Embedding generation
│   │   ├── store.py             # FAISS/LanceDB interface
│   │   └── search.py            # Semantic search
│   │
│   ├── graph/                   # Module 4: Knowledge Graph
│   │   ├── schema.py            # Node/edge definitions
│   │   ├── builder.py           # Graph construction
│   │   ├── queries.py           # Reasoning queries
│   │   └── constraints.py       # Constraint propagation
│   │
│   ├── analysis/                # Module 5: Analysis Agents
│   │   ├── deserts.py           # Medical desert detection
│   │   ├── anomalies.py         # Anomaly detection
│   │   ├── gaps.py              # Gap analysis
│   │   └── confidence.py        # Trust aggregation
│   │
│   ├── agents/                  # Module 6: Orchestration
│   │   ├── orchestrator.py      # LangGraph state machine
│   │   ├── query_agent.py       # Query handling
│   │   ├── analysis_agent.py    # Analysis coordination
│   │   ├── planning_agent.py    # Optimization coordination
│   │   └── tracing.py           # MLflow citation tracing
│   │
│   ├── optimization/            # Module 7: Hybrid Optimization
│   │   ├── classical.py         # Classical algorithms
│   │   ├── quantum.py           # Qiskit QAOA
│   │   └── hybrid.py            # Benchmark + select
│   │
│   └── ui/                      # Module 8: Interface
│       ├── streamlit_app.py     # Main application
│       ├── map_viz.py           # Map visualization
│       └── reports.py           # Report generation
│
├── notebooks/                   # Databricks notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_idp_development.ipynb
│   ├── 03_graph_reasoning.ipynb
│   ├── 04_quantum_experiments.ipynb
│   └── 05_demo_showcase.ipynb
│
├── tests/
│   ├── test_idp.py
│   ├── test_graph.py
│   ├── test_analysis.py
│   └── test_integration.py
│
└── docs/
    ├── architecture.md
    ├── api_reference.md
    └── demo_script.md
```

---

## 🏆 Competitive Differentiation

### What Makes Us Stand Out

| Aspect | Typical Solution | Our Approach |
|--------|-----------------|--------------|
| **Extraction** | Single-pass LLM | Multi-pass with confidence decay |
| **Validation** | Trust LLM output | Constraint-based verification |
| **Citations** | Row-level only | Step-level with contribution |
| **Graphs** | Storage only | Reasoning engine |
| **Optimization** | Heuristics | Honest classical-quantum comparison |
| **Confidence** | Binary yes/no | Probabilistic with evidence |
| **UX** | Technical dashboard | Plain-language + maps |

### Innovation Summary

1. **Confidence-Aware IDP** — First to show HOW confident we are, not just answers
2. **Constraint-Propagated Verification** — Medical logic validates data claims
3. **Step-Level Citations** — Unprecedented transparency in agentic reasoning
4. **Honest Quantum Benchmarking** — Show where quantum actually helps
5. **Unified Graph Architecture** — Single graph, multiple reasoning modes

---

## ⚠️ Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data quality issues | High | Medium | Robust validation + confidence scoring |
| LLM extraction errors | Medium | High | Multi-pass validation + constraints |
| Quantum doesn't outperform | Medium | Low | Classical baseline always available |
| Time overrun | Medium | High | Prioritized MVP + stretch goals |
| Demo failure | Low | Critical | Backup video + local fallback |

---

## 📊 Success Metrics

### Technical Accuracy (35%)
- [ ] Extraction F1 > 0.85 on test set
- [ ] Anomaly detection precision > 0.80
- [ ] Constraint violation detection > 0.90

### IDP Innovation (30%)
- [ ] Multi-pass pipeline implemented
- [ ] Confidence scoring functional
- [ ] Evidence weighting demonstrated

### Social Impact (25%)
- [ ] Medical desert identification working
- [ ] Coverage gap analysis functional
- [ ] Resource allocation recommendations

### User Experience (10%)
- [ ] Natural language queries work
- [ ] Map visualization functional
- [ ] Plain-language explanations

---

## ✅ VF Question Coverage Checklist

### MUST HAVE Questions (15 Total) — ALL Must Be Addressed

| ID | Question | Module | Status |
|----|----------|--------|--------|
| 1.1 | How many hospitals have cardiology? | Genie Chat | ⬜ |
| 1.2 | Hospitals in [region] with [procedure]? | Genie Chat | ⬜ |
| 1.3 | What services does [Facility] offer? | Vector Search | ⬜ |
| 1.4 | Clinics in [Area] that do [Service]? | Vector Search | ⬜ |
| 1.5 | Which region has most [Type] hospitals? | Genie Chat | ⬜ |
| 2.1 | Hospitals within [X] km of [location]? | Genie + Geo | ⬜ |
| 2.3 | Largest geographic cold spots? | Genie + Geo | ⬜ |
| 4.4 | Unrealistic procedures for facility size? | Medical Reasoning | ⬜ |
| 4.7 | Correlations between characteristics? | Genie Chat | ⬜ |
| 4.8 | High procedure breadth vs infrastructure? | Medical Reasoning | ⬜ |
| 4.9 | Things that shouldn't move together? | Medical Reasoning | ⬜ |
| 6.1 | Where is workforce practicing? | Medical Reasoning | ⬜ |
| 7.5 | Procedures depending on few facilities? | Medical Reasoning | ⬜ |
| 7.6 | Oversupply vs scarcity distribution? | Medical Reasoning | ⬜ |
| 8.3 | Gaps where no organizations working? | Medical + Geo + External | ⬜ |

### SHOULD HAVE Questions (Priority After MUST HAVE)

| ID | Question | Module | Status |
|----|----------|--------|--------|
| 3.1 | Claims subspecialty but lacks equipment? | Constraint Graph | ⬜ |
| 3.4 | % facilities with procedure + equipment? | Medical Reasoning | ⬜ |
| 3.5 | Procedures corroborated by multiple sources? | Evidence Aggregation | ⬜ |
| 4.1 | Website quality vs capabilities correlation? | Medical Reasoning | ⬜ |
| 4.2 | High bed-to-OR ratios? | Anomaly Detection | ⬜ |
| 4.3 | Abnormal patterns where features don't match? | Correlation Analysis | ⬜ |
| 4.5 | Physical features correlating with capabilities? | Medical Reasoning | ⬜ |
| 4.6 | Subspecialty vs infrastructure mismatch? | Constraint Validation | ⬜ |
| 6.4 | Visiting vs permanent specialists? | Vector Search Patterns | ⬜ |
| 6.5 | Surgical camps or temporary missions? | Vector Search Patterns | ⬜ |
| 6.6 | Services tied to individuals? | NER + Pattern Match | ⬜ |
| 8.1 | NGOs with overlapping services? | Genie + Deduplication | ⬜ |
| 10.2 | Sweet spot facilities for intervention? | Optimization | ⬜ |
| 10.3 | High-impact intervention probability? | Scoring Model | ⬜ |

### Demo Script — VF Questions to Showcase

```
DEMO FLOW (10-15 minutes):

1. BASIC QUERY DEMO (2 min)
   → "How many hospitals in Greater Accra can perform cesarean sections?"
   → Shows: Genie Chat Text2SQL + confidence scores

2. GEOSPATIAL DEMO (3 min)
   → "Where are the largest cold spots for emergency surgery in Ghana?"
   → Shows: Map visualization + coverage gaps + Voronoi partitions

3. ANOMALY DETECTION DEMO (3 min)
   → "Which facilities have suspicious claims about their capabilities?"
   → Shows: Q4.4, Q4.8, Q4.9 — constraint violations, ratio anomalies

4. MEDICAL REASONING DEMO (3 min)
   → "Which facilities claim surgical capabilities but lack required equipment?"
   → Shows: Q3.1 constraint graph + evidence citations

5. OPTIMIZATION DEMO (2 min)
   → "Where should we deploy 3 mobile surgical units for maximum impact?"
   → Shows: Quantum vs classical comparison + map recommendations

6. CITATION TRACE DEMO (2 min)
   → Show full citation trail for any answer
   → Step-level transparency with MLflow
```

---

## 🚀 Final Words

This system doesn't just parse documents — it **reasons about healthcare**.

Every extraction is confidence-aware.
Every claim is constraint-validated.
Every answer is citation-traced.
Every optimization is honestly benchmarked.

We're building the intelligence layer that transforms fragmented medical data into **coordinated, lifesaving action**.

**ALL 15 MUST HAVE questions will be demonstrably answered.**

---

*MedBridge AI — Where Data Becomes Care*
