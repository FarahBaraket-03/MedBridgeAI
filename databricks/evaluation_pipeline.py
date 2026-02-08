# Databricks notebook source
# type: ignore
# NOTE: This file is designed to run inside a Databricks notebook runtime.
# Globals like `spark`, `display`, `dbutils` are provided by the cluster.

# MAGIC %md
# MAGIC # MedBridge AI — Evaluation & Labeling Pipeline
# MAGIC
# MAGIC Evaluate the MedBridge multi-agent system against a labeled dataset.
# MAGIC Tracks **intent accuracy**, **agent routing accuracy**, **result quality**,
# MAGIC and **LLM summary relevance** via MLflow.
# MAGIC
# MAGIC ### What this notebook does:
# MAGIC 1. Defines a labeled evaluation dataset (ground truth)
# MAGIC 2. Runs each query through the MedBridge API
# MAGIC 3. Scores results against ground truth
# MAGIC 4. Logs all metrics + artifacts to MLflow
# MAGIC 5. Creates a labeling schema for continuous improvement

# COMMAND ----------

# MAGIC %pip install requests mlflow

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import os
import json
import time
import requests
import pandas as pd
import mlflow

# -- MedBridge API endpoint (your backend) --
# Using ngrok tunnel to reach the local backend from Databricks
MEDBRIDGE_API_URL = os.getenv("MEDBRIDGE_API_URL", "https://nonunified-maxwell-noisome.ngrok-free.dev")

# Option B: If deployed (replace with your actual URL)
# MEDBRIDGE_API_URL = "https://your-medbridge-api.com"

# -- MLflow experiment --
EXPERIMENT_NAME = "/MedBridge-AI/evaluation-pipeline"
mlflow.set_experiment(EXPERIMENT_NAME)

print(f"API: {MEDBRIDGE_API_URL}")
print(f"MLflow Experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Labeled Evaluation Dataset
# MAGIC
# MAGIC Each row has:
# MAGIC - `query`: The user question
# MAGIC - `expected_intent`: What intent the supervisor should classify
# MAGIC - `expected_agents`: Which agents should be routed to
# MAGIC - `expected_min_results`: Minimum number of facilities expected
# MAGIC - `quality_criteria`: What the summary should mention
# MAGIC - `difficulty`: easy / medium / hard

# COMMAND ----------

EVAL_DATASET = [
    {
        "id": "eval_001",
        "query": "How many hospitals offer cardiology services?",
        "expected_intent": "service_search",
        "expected_agents": ["genie"],
        "expected_min_results": 5,
        "quality_criteria": "Should mention specific count of cardiology facilities",
        "difficulty": "easy",
        "category": "service_search",
    },
    {
        "id": "eval_002",
        "query": "Where are the medical deserts in Ghana?",
        "expected_intent": "medical_desert",
        "expected_agents": ["geospatial"],
        "expected_min_results": 3,
        "quality_criteria": "Should identify regions with poor coverage, mention population impact",
        "difficulty": "medium",
        "category": "geospatial",
    },
    {
        "id": "eval_003",
        "query": "Which facilities can handle trauma patients near Kumasi?",
        "expected_intent": "distance_query",
        "expected_agents": ["geospatial"],
        "expected_min_results": 3,
        "quality_criteria": "Should list facilities near Kumasi with emergency/trauma capability",
        "difficulty": "medium",
        "category": "geospatial",
    },
    {
        "id": "eval_004",
        "query": "Find suspicious facility capability claims",
        "expected_intent": "validation",
        "expected_agents": ["medical_reasoning"],
        "expected_min_results": 1,
        "quality_criteria": "Should flag facilities claiming capabilities without required equipment",
        "difficulty": "hard",
        "category": "validation",
    },
    {
        "id": "eval_005",
        "query": "Which regions lack emergency care?",
        "expected_intent": "coverage_gap",
        "expected_agents": ["medical_reasoning", "geospatial"],
        "expected_min_results": 1,
        "quality_criteria": "Should identify regions without emergency medicine facilities",
        "difficulty": "medium",
        "category": "coverage_gap",
    },
    {
        "id": "eval_006",
        "query": "Compare healthcare access: Accra vs Northern Region",
        "expected_intent": "comparison",
        "expected_agents": ["genie"],
        "expected_min_results": 2,
        "quality_criteria": "Should compare facility counts, specialties, bed capacity between regions",
        "difficulty": "medium",
        "category": "comparison",
    },
    {
        "id": "eval_007",
        "query": "Find hospitals with CT scanners",
        "expected_intent": "service_search",
        "expected_agents": ["vector_search"],
        "expected_min_results": 1,
        "quality_criteria": "Should list facilities mentioning CT scanner or imaging equipment",
        "difficulty": "easy",
        "category": "equipment_search",
    },
    {
        "id": "eval_008",
        "query": "Where should we deploy mobile eye care units?",
        "expected_intent": "planning",
        "expected_agents": ["planning"],
        "expected_min_results": 1,
        "quality_criteria": "Should suggest deployment locations based on ophthalmology gaps",
        "difficulty": "hard",
        "category": "planning",
    },
    {
        "id": "eval_009",
        "query": "Find coverage gaps for maternal health services",
        "expected_intent": "coverage_gap",
        "expected_agents": ["medical_reasoning"],
        "expected_min_results": 1,
        "quality_criteria": "Should identify regions lacking obstetric/maternal care",
        "difficulty": "medium",
        "category": "coverage_gap",
    },
    {
        "id": "eval_010",
        "query": "List all dental clinics in Accra",
        "expected_intent": "service_search",
        "expected_agents": ["genie"],
        "expected_min_results": 3,
        "quality_criteria": "Should list dental facilities specifically in Accra",
        "difficulty": "easy",
        "category": "service_search",
    },
    {
        "id": "eval_011",
        "query": "Which hospitals have the most beds?",
        "expected_intent": "aggregation",
        "expected_agents": ["genie"],
        "expected_min_results": 5,
        "quality_criteria": "Should rank hospitals by bed capacity",
        "difficulty": "easy",
        "category": "aggregation",
    },
    {
        "id": "eval_012",
        "query": "Are there any neurosurgery capabilities outside Accra?",
        "expected_intent": "service_search",
        "expected_agents": ["genie", "vector_search"],
        "expected_min_results": 0,
        "quality_criteria": "Should check for neurosurgery outside Greater Accra, may find none",
        "difficulty": "hard",
        "category": "service_search",
    },
]

eval_df = pd.DataFrame(EVAL_DATASET)
print(f"Evaluation dataset: {len(eval_df)} queries")
print(f"Categories: {eval_df['category'].value_counts().to_dict()}")
print(f"Difficulty: {eval_df['difficulty'].value_counts().to_dict()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Pre-flight Check & Run Evaluation
# MAGIC
# MAGIC **IMPORTANT**: The MedBridge API must be reachable from this environment.
# MAGIC - If running on **Databricks**: `localhost` won't work. Use ngrok or a deployed URL.
# MAGIC - If running **locally**: make sure the backend is running on port 8000.
# MAGIC
# MAGIC To expose your local backend from Databricks, run locally:
# MAGIC ```bash
# MAGIC pip install pyngrok
# MAGIC ngrok http 8000
# MAGIC ```
# MAGIC Then set `MEDBRIDGE_API_URL` above to the ngrok URL (e.g. `https://xxxx.ngrok-free.app`).

# COMMAND ----------

# Pre-flight: verify API is reachable
try:
    _health = requests.get(
        f"{MEDBRIDGE_API_URL}/api/health",
        headers={"ngrok-skip-browser-warning": "1"},
        timeout=15,
    )
    _health.raise_for_status()
    print(f"API is reachable: {_health.json()}")
except Exception as _e:
    raise RuntimeError(
        f"Cannot reach MedBridge API at {MEDBRIDGE_API_URL}/api/health\n"
        f"Error: {_e}\n\n"
        f"If running on Databricks, localhost won't work.\n"
        f"Option 1: Run evaluation locally instead:\n"
        f"  python run_evaluation.py\n"
        f"Option 2: Expose your backend with ngrok:\n"
        f"  ngrok http 8000\n"
        f"  Then set MEDBRIDGE_API_URL to the ngrok URL above."
    )

# COMMAND ----------

def query_medbridge(query: str, timeout: int = 120) -> dict:
    """Call the MedBridge API and return the response."""
    try:
        resp = requests.post(
            f"{MEDBRIDGE_API_URL}/api/query",
            json={"query": query},
            headers={"ngrok-skip-browser-warning": "1"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "query": query}


def score_result(result: dict, expected: dict) -> dict:
    """Score a single query result against ground truth."""
    scores = {}

    # 1. Intent accuracy (exact match)
    actual_intent = result.get("intent", "")
    scores["intent_match"] = 1.0 if actual_intent == expected["expected_intent"] else 0.0

    # 2. Intent partial match (same category)
    intent_groups = {
        "service_search": ["service_search", "aggregation", "equipment_search"],
        "coverage_gap": ["coverage_gap", "medical_desert"],
        "geospatial": ["distance_query", "medical_desert", "coverage_gap"],
        "validation": ["validation", "anomaly_detection", "red_flag"],
        "planning": ["planning", "deployment"],
    }
    scores["intent_category_match"] = 0.0
    for group_intents in intent_groups.values():
        if actual_intent in group_intents and expected["expected_intent"] in group_intents:
            scores["intent_category_match"] = 1.0
            break

    # 3. Agent routing accuracy
    actual_agents = set(result.get("agents_used", []))
    expected_agents = set(expected["expected_agents"])
    if expected_agents:
        scores["agent_precision"] = len(actual_agents & expected_agents) / len(actual_agents) if actual_agents else 0.0
        scores["agent_recall"] = len(actual_agents & expected_agents) / len(expected_agents)
        scores["agent_f1"] = (
            2 * scores["agent_precision"] * scores["agent_recall"]
            / (scores["agent_precision"] + scores["agent_recall"])
            if (scores["agent_precision"] + scores["agent_recall"]) > 0 else 0.0
        )
    else:
        scores["agent_precision"] = scores["agent_recall"] = scores["agent_f1"] = 0.0

    # 4. Result count check
    response = result.get("response", {})
    map_facilities = response.get("_map_facilities", []) if isinstance(response, dict) else []
    facility_count = len(map_facilities)
    scores["has_results"] = 1.0 if facility_count > 0 else 0.0
    scores["enough_results"] = 1.0 if facility_count >= expected["expected_min_results"] else 0.0
    scores["facility_count"] = facility_count

    # 5. Summary quality (basic: non-empty and substantial)
    summary = result.get("summary", "")
    scores["has_summary"] = 1.0 if len(summary) > 20 else 0.0
    scores["summary_length"] = len(summary)

    # 6. Latency
    scores["latency_ms"] = result.get("total_duration_ms", 0)

    # 7. Error check
    scores["no_error"] = 0.0 if "error" in result else 1.0

    return scores


# Run all evaluations
print("Running evaluation queries...\n")
all_results = []

for i, row in eval_df.iterrows():
    print(f"[{i+1}/{len(eval_df)}] {row['query'][:60]}...", end=" ")
    t0 = time.time()
    result = query_medbridge(row["query"])
    elapsed = time.time() - t0
    scores = score_result(result, row)

    all_results.append({
        "id": row["id"],
        "query": row["query"],
        "category": row["category"],
        "difficulty": row["difficulty"],
        "actual_intent": result.get("intent", "error"),
        "actual_agents": result.get("agents_used", []),
        "expected_intent": row["expected_intent"],
        "expected_agents": row["expected_agents"],
        "api_latency_s": round(elapsed, 2),
        "summary_preview": (result.get("summary", "") or "")[:200],
        **scores,
    })
    status = "OK" if scores["no_error"] else "FAIL"
    print(f"{status} ({elapsed:.1f}s, intent={'MATCH' if scores['intent_match'] else 'MISS'})")

results_df = pd.DataFrame(all_results)
print(f"\nCompleted {len(results_df)} evaluations")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Score Summary & MLflow Logging

# COMMAND ----------

with mlflow.start_run(run_name=f"eval-{time.strftime('%Y%m%d-%H%M')}") as run:
    # -- Log the evaluation dataset --
    eval_dataset = mlflow.data.from_pandas(eval_df, name="medbridge-eval-v1")
    mlflow.log_input(eval_dataset, context="evaluation")

    # -- Aggregate metrics --
    metrics = {
        "intent_accuracy": results_df["intent_match"].mean(),
        "intent_category_accuracy": results_df["intent_category_match"].mean(),
        "agent_precision": results_df["agent_precision"].mean(),
        "agent_recall": results_df["agent_recall"].mean(),
        "agent_f1": results_df["agent_f1"].mean(),
        "result_hit_rate": results_df["has_results"].mean(),
        "enough_results_rate": results_df["enough_results"].mean(),
        "summary_rate": results_df["has_summary"].mean(),
        "avg_latency_ms": results_df["latency_ms"].mean(),
        "max_latency_ms": results_df["latency_ms"].max(),
        "error_rate": 1.0 - results_df["no_error"].mean(),
        "avg_facility_count": results_df["facility_count"].mean(),
        "avg_summary_length": results_df["summary_length"].mean(),
        "total_queries": len(results_df),
    }

    for k, v in metrics.items():
        mlflow.log_metric(k, round(v, 4))

    # -- Per-category metrics --
    for cat in results_df["category"].unique():
        cat_df = results_df[results_df["category"] == cat]
        mlflow.log_metric(f"intent_acc_{cat}", round(cat_df["intent_match"].mean(), 4))
        mlflow.log_metric(f"result_rate_{cat}", round(cat_df["has_results"].mean(), 4))
        mlflow.log_metric(f"latency_{cat}_ms", round(cat_df["latency_ms"].mean(), 1))

    # -- Per-difficulty metrics --
    for diff in ["easy", "medium", "hard"]:
        diff_df = results_df[results_df["difficulty"] == diff]
        if len(diff_df) > 0:
            mlflow.log_metric(f"intent_acc_{diff}", round(diff_df["intent_match"].mean(), 4))
            mlflow.log_metric(f"result_rate_{diff}", round(diff_df["has_results"].mean(), 4))

    # -- Log the full results table --
    # Convert list columns to strings for MLflow compatibility
    log_df = results_df.copy()
    log_df["actual_agents"] = log_df["actual_agents"].apply(str)
    log_df["expected_agents"] = log_df["expected_agents"].apply(str)
    mlflow.log_table(log_df, artifact_file="evaluation_results.json")

    # -- Log parameters --
    mlflow.log_param("api_url", MEDBRIDGE_API_URL)
    mlflow.log_param("eval_dataset_size", len(eval_df))
    mlflow.log_param("eval_version", "v1")

    # -- Tags --
    mlflow.set_tag("pipeline", "evaluation")
    mlflow.set_tag("data_source", "virtue_foundation_ghana")

    print(f"\nMLflow Run ID: {run.info.run_id}")
    print(f"\n{'='*60}")
    print(f"  EVALUATION SUMMARY")
    print(f"{'='*60}")
    for k, v in metrics.items():
        print(f"  {k:30s} {v:.4f}" if isinstance(v, float) else f"  {k:30s} {v}")
    print(f"{'='*60}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Detailed Results Table

# COMMAND ----------

# Show detailed results
display(results_df[[
    "id", "query", "category", "difficulty",
    "intent_match", "agent_f1", "has_results", "facility_count",
    "latency_ms", "summary_preview",
]])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Failure Analysis

# COMMAND ----------

# Show queries that failed intent classification
failed_intent = results_df[results_df["intent_match"] == 0]
if len(failed_intent) > 0:
    print(f"Failed intent classification: {len(failed_intent)}/{len(results_df)}")
    for _, row in failed_intent.iterrows():
        print(f"\n  Query:    {row['query']}")
        print(f"  Expected: {row['expected_intent']}")
        print(f"  Actual:   {row['actual_intent']}")
else:
    print("All intents classified correctly!")

print("\n" + "="*60)

# Show queries that returned no results
no_results = results_df[(results_df["has_results"] == 0) & (results_df["no_error"] == 1)]
if len(no_results) > 0:
    print(f"\nQueries with no results: {len(no_results)}/{len(results_df)}")
    for _, row in no_results.iterrows():
        print(f"  - {row['query']} (intent: {row['actual_intent']})")
else:
    print("All queries returned results!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Labeling Schema
# MAGIC
# MAGIC Define the schema for human labeling / continuous evaluation.
# MAGIC Export as a DataFrame that evaluators can fill in.

# COMMAND ----------

LABELING_SCHEMA = {
    "query_id": "Unique identifier for the query",
    "query": "The original user question",
    "timestamp": "When the query was run",

    # Intent labels
    "intent_correct": "Is the classified intent correct? (yes/no)",
    "correct_intent": "If wrong, what should the intent be?",

    # Agent routing labels
    "agents_correct": "Were the correct agents used? (yes/no)",
    "correct_agents": "If wrong, which agents should have been used?",

    # Result quality labels
    "results_relevant": "Are the returned facilities relevant? (1-5 scale)",
    "results_complete": "Are important facilities missing? (yes/no)",
    "missing_facilities": "Names of facilities that should have appeared",

    # Summary quality labels
    "summary_accurate": "Is the LLM summary factually correct? (1-5 scale)",
    "summary_actionable": "Is the summary useful for an NGO planner? (1-5 scale)",
    "summary_issues": "Any issues with the summary (hallucination, missing info, etc.)",

    # Map quality labels
    "map_correct": "Do the map markers show the right locations? (yes/no)",
    "map_issues": "Any issues with map display",

    # Overall
    "overall_quality": "Overall response quality (1-5 scale)",
    "notes": "Free-form notes from the evaluator",
}

# Create empty labeling template
labeling_template = pd.DataFrame([
    {
        "query_id": row["id"],
        "query": row["query"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "actual_intent": row.get("actual_intent", ""),
        "actual_agents": str(row.get("actual_agents", [])),
        # Empty fields for human labeling
        "intent_correct": "",
        "correct_intent": "",
        "agents_correct": "",
        "correct_agents": "",
        "results_relevant": "",
        "results_complete": "",
        "missing_facilities": "",
        "summary_accurate": "",
        "summary_actionable": "",
        "summary_issues": "",
        "map_correct": "",
        "map_issues": "",
        "overall_quality": "",
        "notes": "",
    }
    for _, row in results_df.iterrows()
])

# Save labeling template as Delta table
spark_labels = spark.createDataFrame(labeling_template)
spark_labels.write.mode("overwrite").saveAsTable("hive_metastore.medbridge_ai.eval_labeling_template")
print(f"Labeling template saved to hive_metastore.medbridge_ai.eval_labeling_template ({len(labeling_template)} rows)")

# Also log to MLflow
with mlflow.start_run(run_name="labeling-schema"):
    mlflow.log_dict(LABELING_SCHEMA, "labeling_schema.json")
    mlflow.log_table(labeling_template, artifact_file="labeling_template.json")
    mlflow.set_tag("pipeline", "labeling")
    print("Labeling schema logged to MLflow")

# Display the template
display(labeling_template)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Summary
# MAGIC
# MAGIC ### What was logged to MLflow:
# MAGIC | Artifact | Description |
# MAGIC |----------|-------------|
# MAGIC | **Metrics** | intent_accuracy, agent_f1, result_hit_rate, latency, error_rate |
# MAGIC | **Per-category metrics** | Accuracy broken down by query type |
# MAGIC | **Per-difficulty metrics** | Accuracy broken down by easy/medium/hard |
# MAGIC | **evaluation_results.json** | Full results table with all scores |
# MAGIC | **labeling_schema.json** | Schema definition for human evaluation |
# MAGIC | **labeling_template.json** | Pre-filled template for human labeling |
# MAGIC | **Delta table** | `hive_metastore.medbridge_ai.eval_labeling_template` |
# MAGIC
# MAGIC ### Next steps:
# MAGIC 1. **Fill in labeling template** — Have evaluators score each query
# MAGIC 2. **Re-run after changes** — Compare metrics across MLflow runs
# MAGIC 3. **Add more test queries** — Expand the eval dataset
# MAGIC 4. **Set up scheduled runs** — Automate evaluation as a Databricks Job
