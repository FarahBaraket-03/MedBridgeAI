"""
MedBridge AI — Local Evaluation Runner
========================================
Run this locally (not on Databricks) while your backend is running on localhost:8000.
Results are logged to Databricks MLflow via your .env credentials.

Usage:
    python run_evaluation.py
"""

import os
import sys
import time
import json

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv()

import requests
import pandas as pd

# ── MLflow setup (logs to Databricks) ────────────────────────────────────────
try:
    import mlflow
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)
    MLFLOW_AVAILABLE = True
    print(f"MLflow tracking: {tracking_uri or 'local'}")
except ImportError:
    MLFLOW_AVAILABLE = False
    print("MLflow not installed — results will only print to console")

# ── Config ────────────────────────────────────────────────────────────────────
API_URL = os.getenv("MEDBRIDGE_API_URL", "http://localhost:8000")
EXPERIMENT_NAME = "/MedBridge-AI/evaluation-pipeline"

# ── Evaluation Dataset ────────────────────────────────────────────────────────
EVAL_DATASET = [
    {
        "id": "eval_001",
        "query": "How many hospitals offer cardiology services?",
        "expected_intent": "service_search",
        "expected_agents": ["genie"],
        "expected_min_results": 5,
        "difficulty": "easy",
        "category": "service_search",
    },
    {
        "id": "eval_002",
        "query": "Where are the medical deserts in Ghana?",
        "expected_intent": "medical_desert",
        "expected_agents": ["geospatial"],
        "expected_min_results": 3,
        "difficulty": "medium",
        "category": "geospatial",
    },
    {
        "id": "eval_003",
        "query": "Which facilities can handle trauma patients near Kumasi?",
        "expected_intent": "distance_query",
        "expected_agents": ["geospatial"],
        "expected_min_results": 3,
        "difficulty": "medium",
        "category": "geospatial",
    },
    {
        "id": "eval_004",
        "query": "Find suspicious facility capability claims",
        "expected_intent": "validation",
        "expected_agents": ["medical_reasoning"],
        "expected_min_results": 1,
        "difficulty": "hard",
        "category": "validation",
    },
    {
        "id": "eval_005",
        "query": "Which regions lack emergency care?",
        "expected_intent": "coverage_gap",
        "expected_agents": ["medical_reasoning", "geospatial"],
        "expected_min_results": 1,
        "difficulty": "medium",
        "category": "coverage_gap",
    },
    {
        "id": "eval_006",
        "query": "Compare healthcare access: Accra vs Northern Region",
        "expected_intent": "comparison",
        "expected_agents": ["genie"],
        "expected_min_results": 2,
        "difficulty": "medium",
        "category": "comparison",
    },
    {
        "id": "eval_007",
        "query": "Find hospitals with CT scanners",
        "expected_intent": "service_search",
        "expected_agents": ["vector_search"],
        "expected_min_results": 1,
        "difficulty": "easy",
        "category": "equipment_search",
    },
    {
        "id": "eval_008",
        "query": "Where should we deploy mobile eye care units?",
        "expected_intent": "planning",
        "expected_agents": ["planning"],
        "expected_min_results": 1,
        "difficulty": "hard",
        "category": "planning",
    },
    {
        "id": "eval_009",
        "query": "Find coverage gaps for maternal health services",
        "expected_intent": "coverage_gap",
        "expected_agents": ["medical_reasoning"],
        "expected_min_results": 1,
        "difficulty": "medium",
        "category": "coverage_gap",
    },
    {
        "id": "eval_010",
        "query": "List all dental clinics in Accra",
        "expected_intent": "service_search",
        "expected_agents": ["genie"],
        "expected_min_results": 3,
        "difficulty": "easy",
        "category": "service_search",
    },
    {
        "id": "eval_011",
        "query": "Which hospitals have the most beds?",
        "expected_intent": "aggregation",
        "expected_agents": ["genie"],
        "expected_min_results": 5,
        "difficulty": "easy",
        "category": "aggregation",
    },
    {
        "id": "eval_012",
        "query": "Are there any neurosurgery capabilities outside Accra?",
        "expected_intent": "service_search",
        "expected_agents": ["genie", "vector_search"],
        "expected_min_results": 0,
        "difficulty": "hard",
        "category": "service_search",
    },
]


# ── Scoring ───────────────────────────────────────────────────────────────────

def query_api(query: str, timeout: int = 120) -> dict:
    try:
        resp = requests.post(
            f"{API_URL}/api/query",
            json={"query": query},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "query": query}


def score_result(result: dict, expected: dict) -> dict:
    scores = {}
    actual_intent = result.get("intent", "")

    # Intent exact match
    scores["intent_match"] = 1.0 if actual_intent == expected["expected_intent"] else 0.0

    # Intent category match (relaxed)
    intent_groups = {
        "service_search": ["service_search", "aggregation", "equipment_search"],
        "coverage_gap": ["coverage_gap", "medical_desert"],
        "geospatial": ["distance_query", "medical_desert", "coverage_gap"],
        "validation": ["validation", "anomaly_detection", "red_flag"],
        "planning": ["planning", "deployment"],
    }
    scores["intent_category_match"] = 0.0
    for group in intent_groups.values():
        if actual_intent in group and expected["expected_intent"] in group:
            scores["intent_category_match"] = 1.0
            break

    # Agent routing
    actual_agents = set(result.get("agents_used", []))
    expected_agents = set(expected["expected_agents"])
    if expected_agents:
        scores["agent_precision"] = len(actual_agents & expected_agents) / len(actual_agents) if actual_agents else 0.0
        scores["agent_recall"] = len(actual_agents & expected_agents) / len(expected_agents)
        denom = scores["agent_precision"] + scores["agent_recall"]
        scores["agent_f1"] = 2 * scores["agent_precision"] * scores["agent_recall"] / denom if denom > 0 else 0.0
    else:
        scores["agent_precision"] = scores["agent_recall"] = scores["agent_f1"] = 0.0

    # Facilities
    response = result.get("response", {})
    map_fac = response.get("_map_facilities", []) if isinstance(response, dict) else []
    scores["facility_count"] = len(map_fac)
    scores["has_results"] = 1.0 if len(map_fac) > 0 else 0.0
    scores["enough_results"] = 1.0 if len(map_fac) >= expected["expected_min_results"] else 0.0

    # Summary
    summary = result.get("summary", "") or ""
    scores["has_summary"] = 1.0 if len(summary) > 20 else 0.0
    scores["summary_length"] = len(summary)

    # Latency & errors
    scores["latency_ms"] = result.get("total_duration_ms", 0)
    scores["no_error"] = 0.0 if "error" in result else 1.0

    return scores


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. Check API connectivity
    print(f"Checking API at {API_URL}...")
    try:
        health = requests.get(f"{API_URL}/api/health", timeout=10)
        health.raise_for_status()
        print(f"  API is UP: {health.json()}\n")
    except Exception as e:
        print(f"\n  ERROR: Cannot reach {API_URL}/api/health")
        print(f"  {e}")
        print(f"\n  Make sure your backend is running:")
        print(f"    cd medbridge")
        print(f"    .venv\\Scripts\\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)

    eval_df = pd.DataFrame(EVAL_DATASET)

    # 2. Run evaluations
    print(f"Running {len(eval_df)} evaluation queries...\n")
    print(f"{'#':>3}  {'Status':6}  {'Time':>6}  {'Intent':15}  {'Agents':25}  Query")
    print("-" * 100)

    all_results = []
    for i, row in eval_df.iterrows():
        t0 = time.time()
        result = query_api(row["query"])
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
            "summary_preview": (result.get("summary", "") or "")[:150],
            **scores,
        })

        ok = scores["no_error"] == 1.0
        intent_ok = "MATCH" if scores["intent_match"] else "miss"
        agents_str = ",".join(result.get("agents_used", []))
        status = "  OK  " if ok else " FAIL "
        print(f"{i+1:>3}  {status}  {elapsed:>5.1f}s  {result.get('intent','?'):15}  {agents_str:25}  {row['query'][:40]}")

    results_df = pd.DataFrame(all_results)

    # 3. Print summary
    print(f"\n{'=' * 70}")
    print(f"  EVALUATION SUMMARY  ({len(results_df)} queries)")
    print(f"{'=' * 70}")

    metrics = {
        "Intent Accuracy (exact)": results_df["intent_match"].mean(),
        "Intent Accuracy (category)": results_df["intent_category_match"].mean(),
        "Agent Precision": results_df["agent_precision"].mean(),
        "Agent Recall": results_df["agent_recall"].mean(),
        "Agent F1": results_df["agent_f1"].mean(),
        "Result Hit Rate": results_df["has_results"].mean(),
        "Enough Results Rate": results_df["enough_results"].mean(),
        "Summary Rate": results_df["has_summary"].mean(),
        "Avg Latency (ms)": results_df["latency_ms"].mean(),
        "Avg Facility Count": results_df["facility_count"].mean(),
        "Error Rate": 1.0 - results_df["no_error"].mean(),
    }

    for k, v in metrics.items():
        bar = "█" * int(v * 30) + "░" * (30 - int(v * 30)) if v <= 1.0 else ""
        print(f"  {k:30s}  {v:>8.1%}  {bar}" if v <= 1.0 else f"  {k:30s}  {v:>8.1f}")

    # 4. Failure analysis
    failed = results_df[results_df["intent_match"] == 0]
    if len(failed) > 0:
        print(f"\n  Intent Mismatches ({len(failed)}):")
        for _, row in failed.iterrows():
            print(f"    {row['query'][:50]:50}  expected={row['expected_intent']:20}  actual={row['actual_intent']}")

    # 5. Log to MLflow (Databricks)
    if MLFLOW_AVAILABLE:
        try:
            mlflow.set_experiment(EXPERIMENT_NAME)
            with mlflow.start_run(run_name=f"eval-local-{time.strftime('%Y%m%d-%H%M')}"):
                eval_dataset = mlflow.data.from_pandas(eval_df, name="medbridge-eval-v1")
                mlflow.log_input(eval_dataset, context="evaluation")

                mlflow_metrics = {
                    "intent_accuracy": results_df["intent_match"].mean(),
                    "intent_category_accuracy": results_df["intent_category_match"].mean(),
                    "agent_precision": results_df["agent_precision"].mean(),
                    "agent_recall": results_df["agent_recall"].mean(),
                    "agent_f1": results_df["agent_f1"].mean(),
                    "result_hit_rate": results_df["has_results"].mean(),
                    "enough_results_rate": results_df["enough_results"].mean(),
                    "summary_rate": results_df["has_summary"].mean(),
                    "avg_latency_ms": results_df["latency_ms"].mean(),
                    "error_rate": 1.0 - results_df["no_error"].mean(),
                    "total_queries": float(len(results_df)),
                }
                for k, v in mlflow_metrics.items():
                    mlflow.log_metric(k, round(v, 4))

                # Per-category
                for cat in results_df["category"].unique():
                    cat_df = results_df[results_df["category"] == cat]
                    mlflow.log_metric(f"intent_acc_{cat}", round(cat_df["intent_match"].mean(), 4))

                # Log results table
                log_df = results_df.copy()
                log_df["actual_agents"] = log_df["actual_agents"].apply(str)
                log_df["expected_agents"] = log_df["expected_agents"].apply(str)
                mlflow.log_table(log_df, artifact_file="evaluation_results.json")

                mlflow.log_param("api_url", API_URL)
                mlflow.log_param("eval_version", "v1")
                mlflow.set_tag("pipeline", "evaluation")
                mlflow.set_tag("run_location", "local")

            print(f"\n  ✓ Results logged to MLflow ({tracking_uri or 'local'})")
        except Exception as e:
            print(f"\n  ✗ MLflow logging failed: {e}")
            print(f"    (Results were still printed above)")

    print(f"\n{'=' * 70}")
    print("  Done!")


if __name__ == "__main__":
    main()
