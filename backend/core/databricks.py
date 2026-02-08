"""
MedBridge AI -- Databricks Model Serving Integration
=====================================================
Routes vector search queries through Databricks Model Serving REST API
instead of direct Qdrant calls. Falls back to Qdrant if Databricks is
unavailable.

The served model was registered in the Databricks MLOps notebook:
  databricks/medbridge_mlops_pipeline.py  (Section 6)
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from backend.core.config import (
    DATABRICKS_HOST,
    DATABRICKS_TOKEN,
    DATABRICKS_SERVING_ENDPOINT,
    VECTOR_SEARCH_BACKEND,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Databricks Model Serving client
# ---------------------------------------------------------------------------

_serving_url: Optional[str] = None


def _get_serving_url() -> str:
    """Build the Databricks Model Serving invocation URL."""
    global _serving_url
    if _serving_url is None:
        host = (DATABRICKS_HOST or "").rstrip("/")
        endpoint = DATABRICKS_SERVING_ENDPOINT or "medbridge-vector-search"
        _serving_url = f"{host}/serving-endpoints/{endpoint}/invocations"
    return _serving_url


def _is_databricks_configured() -> bool:
    """Check whether Databricks credentials are available."""
    return bool(
        DATABRICKS_HOST
        and DATABRICKS_TOKEN
        and DATABRICKS_HOST != "https://your-workspace.cloud.databricks.com"
        and DATABRICKS_TOKEN != "your_databricks_token_here"
    )


def is_databricks_backend() -> bool:
    """Should the app route vector search through Databricks?"""
    return VECTOR_SEARCH_BACKEND == "databricks" and _is_databricks_configured()


# ---------------------------------------------------------------------------
#  Search via Databricks Model Serving
# ---------------------------------------------------------------------------

# Map short vector names to Delta column names
_VEC_MAP = {
    "full_document": "vec_full_document",
    "clinical_detail": "vec_clinical_detail",
    "specialties_context": "vec_specialties_context",
}


def search_via_databricks(
    query: str,
    vector_name: str = "full_document",
    top_k: int = 10,
) -> List[Dict]:
    """
    Call the Databricks Model Serving endpoint for vector search.

    Returns the same schema as ``vectorstore.search_facilities()``
    so the vector-search agent can swap transparently.
    """
    t0 = time.time()
    url = _get_serving_url()
    mapped_vec = _VEC_MAP.get(vector_name, f"vec_{vector_name}")

    payload = {
        "dataframe_records": [
            {
                "query": query,
                "vector_name": mapped_vec,
                "top_k": top_k,
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Model Serving returns {"predictions": [{"results": "..."}]}
        predictions = data.get("predictions", [])
        if not predictions:
            logger.warning("Databricks returned empty predictions for query: %s", query[:80])
            return []

        raw = predictions[0] if isinstance(predictions, list) else predictions
        results_json = raw.get("results", "[]") if isinstance(raw, dict) else raw
        results = json.loads(results_json) if isinstance(results_json, str) else results_json

        duration = (time.time() - t0) * 1000
        logger.info(
            "Databricks search: %d results in %.0fms (vec=%s)",
            len(results), duration, mapped_vec,
        )
        return results

    except requests.exceptions.ConnectionError:
        logger.warning("Databricks serving endpoint unreachable at %s", url)
        return []
    except requests.exceptions.HTTPError as e:
        logger.warning("Databricks serving error %s: %s", e.response.status_code, e.response.text[:200])
        return []
    except Exception as e:
        logger.warning("Databricks search failed: %s", e)
        return []


# ---------------------------------------------------------------------------
#  MLflow Run Metadata  (read-only, for the /mlops/status API)
# ---------------------------------------------------------------------------

def get_mlflow_run_info() -> Optional[Dict[str, Any]]:
    """
    Fetch the latest MLflow run metadata from the Databricks workspace.
    Returns experiment/run info for the MLOps status dashboard.
    """
    if not _is_databricks_configured():
        return None

    host = (DATABRICKS_HOST or "").rstrip("/")
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        # Search for the latest run in our experiment
        resp = requests.post(
            f"{host}/api/2.0/mlflow/runs/search",
            json={
                "experiment_ids": [],
                "filter": "tags.pipeline = 'vectorization'",
                "max_results": 1,
                "order_by": ["start_time DESC"],
            },
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        runs = resp.json().get("runs", [])
        if not runs:
            return {"status": "no_runs", "message": "No MLflow runs found"}

        run = runs[0]
        info = run.get("info", {})
        data = run.get("data", {})

        # Extract metrics
        metrics = {}
        for m in data.get("metrics", []):
            metrics[m["key"]] = m["value"]

        # Extract params
        params = {}
        for p in data.get("params", []):
            params[p["key"]] = p["value"]

        return {
            "status": "ok",
            "run_id": info.get("run_id"),
            "experiment_id": info.get("experiment_id"),
            "start_time": info.get("start_time"),
            "end_time": info.get("end_time"),
            "lifecycle_stage": info.get("lifecycle_stage"),
            "params": params,
            "metrics": metrics,
        }

    except Exception as e:
        logger.warning("Failed to fetch MLflow run info: %s", e)
        return {"status": "error", "message": str(e)}


def get_serving_endpoint_status() -> Dict[str, Any]:
    """Check the health/status of the Databricks Model Serving endpoint."""
    if not _is_databricks_configured():
        return {
            "status": "not_configured",
            "message": "Databricks credentials not set in .env",
        }

    host = (DATABRICKS_HOST or "").rstrip("/")
    endpoint = DATABRICKS_SERVING_ENDPOINT or "medbridge-vector-search"
    headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

    try:
        resp = requests.get(
            f"{host}/api/2.0/serving-endpoints/{endpoint}",
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        state = data.get("state", {})
        return {
            "status": "ok",
            "endpoint_name": endpoint,
            "state": state.get("ready", "UNKNOWN"),
            "config_update": state.get("config_update"),
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"status": "not_deployed", "message": f"Endpoint '{endpoint}' not found. Deploy the model first."}
        return {"status": "error", "message": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
