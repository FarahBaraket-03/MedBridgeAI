# Databricks notebook source
# type: ignore
# NOTE: This file is designed to run inside a Databricks notebook runtime.

# MAGIC %md
# MAGIC # MedBridge AI — Trace Analysis Dashboard
# MAGIC
# MAGIC Analyze MLflow traces from the MedBridge backend to understand:
# MAGIC - LLM call patterns (which models, token usage, latency)
# MAGIC - Agent routing decisions
# MAGIC - End-to-end query performance
# MAGIC - Error patterns and failure modes
# MAGIC
# MAGIC ### Prerequisites:
# MAGIC Your backend must have MLflow tracing enabled (see `backend/core/llm.py`
# MAGIC and `backend/orchestration/graph.py`).

# COMMAND ----------

# MAGIC %pip install mlflow

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import mlflow
import pandas as pd
import json
from datetime import datetime, timedelta

# Use the experiment ID from your .env
EXPERIMENT_ID = "3370740690349778"

print(f"Experiment ID: {EXPERIMENT_ID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Fetch Recent Traces

# COMMAND ----------

def fetch_traces(experiment_id: str, max_results: int = 100) -> pd.DataFrame:
    """Fetch MLflow traces from the experiment."""
    client = mlflow.tracking.MlflowClient()

    # Search for runs with traces
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        max_results=max_results,
        order_by=["start_time DESC"],
    )

    trace_data = []
    for run in runs:
        run_id = run.info.run_id
        start_time = run.info.start_time
        end_time = run.info.end_time

        # Get metrics
        metrics = run.data.metrics
        params = run.data.params
        tags = run.data.tags

        trace_data.append({
            "run_id": run_id,
            "start_time": datetime.fromtimestamp(start_time / 1000) if start_time else None,
            "end_time": datetime.fromtimestamp(end_time / 1000) if end_time else None,
            "duration_s": (end_time - start_time) / 1000 if end_time and start_time else None,
            "status": run.info.status,
            "pipeline": tags.get("pipeline", "unknown"),
            **metrics,
            **{f"param_{k}": v for k, v in params.items()},
        })

    return pd.DataFrame(trace_data)


traces_df = fetch_traces(EXPERIMENT_ID)
print(f"Found {len(traces_df)} traced runs")
if len(traces_df) > 0:
    display(traces_df.head(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Search Traces via MLflow API

# COMMAND ----------

def search_traces_api(experiment_id: str, max_results: int = 50):
    """Search for MLflow traces using the traces API."""
    client = mlflow.tracking.MlflowClient()

    try:
        # Use the search_traces API (MLflow 2.14+)
        traces = client.search_traces(
            experiment_ids=[experiment_id],
            max_results=max_results,
        )

        trace_records = []
        for trace in traces:
            info = trace.info
            trace_records.append({
                "trace_id": info.request_id,
                "timestamp": datetime.fromtimestamp(info.timestamp_ms / 1000) if info.timestamp_ms else None,
                "status": info.status.value if hasattr(info.status, 'value') else str(info.status),
                "execution_time_ms": info.execution_time_ms,
                "tags": {t.key: t.value for t in (trace.info.tags or [])},
            })

        return pd.DataFrame(trace_records)

    except AttributeError:
        print("search_traces not available in this MLflow version. Using run-based search.")
        return pd.DataFrame()
    except Exception as e:
        print(f"Trace search failed: {e}")
        return pd.DataFrame()


trace_search_df = search_traces_api(EXPERIMENT_ID)
if len(trace_search_df) > 0:
    print(f"Found {len(trace_search_df)} traces")
    display(trace_search_df.head(20))
else:
    print("No traces found via search API. Traces will appear after running queries with tracing enabled.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Analyze LLM Call Patterns

# COMMAND ----------

def analyze_llm_metrics(traces_df: pd.DataFrame) -> dict:
    """Analyze LLM-related metrics from traced runs."""
    analysis = {}

    # Check for token-related metrics
    token_cols = [c for c in traces_df.columns if "token" in c.lower()]
    latency_cols = [c for c in traces_df.columns if "latency" in c.lower() or "duration" in c.lower()]

    if token_cols:
        for col in token_cols:
            valid = traces_df[col].dropna()
            if len(valid) > 0:
                analysis[f"{col}_avg"] = valid.mean()
                analysis[f"{col}_max"] = valid.max()
                analysis[f"{col}_total"] = valid.sum()

    if "duration_s" in traces_df.columns:
        valid = traces_df["duration_s"].dropna()
        if len(valid) > 0:
            analysis["avg_duration_s"] = valid.mean()
            analysis["p50_duration_s"] = valid.median()
            analysis["p95_duration_s"] = valid.quantile(0.95)
            analysis["max_duration_s"] = valid.max()

    # Count by pipeline type
    if "pipeline" in traces_df.columns:
        analysis["pipeline_counts"] = traces_df["pipeline"].value_counts().to_dict()

    # Success rate
    if "status" in traces_df.columns:
        total = len(traces_df)
        success = len(traces_df[traces_df["status"] == "FINISHED"])
        analysis["success_rate"] = success / total if total > 0 else 0

    return analysis


if len(traces_df) > 0:
    llm_analysis = analyze_llm_metrics(traces_df)
    print("LLM Call Analysis:")
    for k, v in llm_analysis.items():
        print(f"  {k}: {v}")
else:
    print("No traces to analyze yet. Run some queries with tracing enabled first.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Performance Dashboard Metrics

# COMMAND ----------

def create_performance_summary(traces_df: pd.DataFrame):
    """Create a performance summary for the dashboard."""
    if len(traces_df) == 0:
        print("No data for performance summary")
        return

    summary = {
        "total_traced_queries": len(traces_df),
        "time_range": f"{traces_df['start_time'].min()} to {traces_df['start_time'].max()}" if "start_time" in traces_df else "N/A",
    }

    if "duration_s" in traces_df.columns:
        valid = traces_df["duration_s"].dropna()
        if len(valid) > 0:
            summary["avg_response_time_s"] = round(valid.mean(), 2)
            summary["p50_response_time_s"] = round(valid.median(), 2)
            summary["p95_response_time_s"] = round(valid.quantile(0.95), 2)
            summary["fastest_query_s"] = round(valid.min(), 2)
            summary["slowest_query_s"] = round(valid.max(), 2)

    if "status" in traces_df.columns:
        status_counts = traces_df["status"].value_counts().to_dict()
        summary["status_distribution"] = status_counts

    # Log to MLflow
    with mlflow.start_run(run_name=f"perf-summary-{datetime.now().strftime('%Y%m%d')}"):
        for k, v in summary.items():
            if isinstance(v, (int, float)):
                mlflow.log_metric(k, v)
            else:
                mlflow.log_param(k, str(v))
        mlflow.set_tag("pipeline", "performance_analysis")
        print("Performance summary logged to MLflow")

    print("\nPerformance Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


create_performance_summary(traces_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. How to View Traces in Databricks UI
# MAGIC
# MAGIC ### Viewing Traces:
# MAGIC 1. Go to **Experiments** in the left sidebar
# MAGIC 2. Open your experiment (ID: `3370740690349778`)
# MAGIC 3. Click the **Traces** tab to see all traced calls
# MAGIC 4. Click any trace to see the full span tree:
# MAGIC    ```
# MAGIC    medbridge_query (root span)
# MAGIC      ├── groq_llm_openai/gpt-oss-120b (intent classification)
# MAGIC      ├── groq_llm_openai/gpt-oss-120b (synthesis)
# MAGIC      └── groq_llm_llama-3.3-70b-versatile (fallback, if primary fails)
# MAGIC    ```
# MAGIC
# MAGIC ### What Each Trace Shows:
# MAGIC - **Inputs**: Query, messages sent to LLM
# MAGIC - **Outputs**: LLM response, intent, agents used, facility count
# MAGIC - **Attributes**: Token usage (prompt_tokens, completion_tokens, total_tokens)
# MAGIC - **Duration**: Time taken for each span
# MAGIC
# MAGIC ### Generating Traces:
# MAGIC Traces are automatically created when your backend handles queries.
# MAGIC Just run queries through the frontend or API — they'll appear here.
