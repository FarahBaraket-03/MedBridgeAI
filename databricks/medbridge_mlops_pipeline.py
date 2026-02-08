# Databricks notebook source
# type: ignore
# NOTE: This file is designed to run inside a Databricks notebook runtime.
# Globals like `spark`, `display`, `dbutils` and packages like `mlflow`
# are provided by the Databricks cluster -- they are NOT available locally.
# MAGIC %md
# MAGIC # MedBridge AI - MLOps Vectorization Pipeline
# MAGIC
# MAGIC **Databricks-native pipeline** that migrates data from Qdrant Cloud into Delta tables,
# MAGIC tracks the embedding model with MLflow, and creates a serving-ready vector search function.
# MAGIC
# MAGIC ### Architecture
# MAGIC ```
# MAGIC CSV (Ghana Facilities)
# MAGIC   |-> Preprocessing (clean, dedup, geocode)
# MAGIC   |-> Embedding (all-MiniLM-L6-v2, 3 named vectors)
# MAGIC   |-> Delta Table (embeddings + metadata)
# MAGIC   |-> MLflow (model registry, experiment tracking)
# MAGIC   |-> Vector Search (cosine similarity on Delta)
# MAGIC ```
# MAGIC
# MAGIC **Requirements** (install in first cell):
# MAGIC - `sentence-transformers`, `qdrant-client`, `mlflow`

# COMMAND ----------

# MAGIC %pip install sentence-transformers qdrant-client mlflow
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

import os
import json
import time
import uuid
import numpy as np
import pandas as pd
from typing import List, Dict, Optional

# -- Qdrant Cloud credentials (set via Databricks Secrets or env vars) --
# Option A: Databricks Secrets (recommended)
# QDRANT_CLOUD_URL = dbutils.secrets.get(scope="medbridge", key="qdrant_url")
# QDRANT_API_KEY   = dbutils.secrets.get(scope="medbridge", key="qdrant_api_key")

# Option B: Direct (for quick testing -- replace with your values)
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL", "YOUR_QDRANT_URL")
QDRANT_API_KEY   = os.getenv("QDRANT_API_KEY", "YOUR_QDRANT_API_KEY")

# -- Model & Collection config --
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
COLLECTION_NAME = "ghana_medical_facilities"

# -- Delta table paths --
CATALOG = "hive_metastore"  # Change to your catalog (run: SHOW CATALOGS)
SCHEMA  = "medbridge_ai"
EMBEDDINGS_TABLE = f"{CATALOG}.{SCHEMA}.facility_embeddings"
METADATA_TABLE   = f"{CATALOG}.{SCHEMA}.facility_metadata"

# -- MLflow experiment --
EXPERIMENT_NAME = "/MedBridge-AI/vectorization-pipeline"

print(f"Qdrant URL: {QDRANT_CLOUD_URL[:30]}..." if len(QDRANT_CLOUD_URL) > 30 else f"Qdrant URL: {QDRANT_CLOUD_URL}")
print(f"Model: {EMBEDDING_MODEL_NAME} (dim={EMBEDDING_DIM})")
print(f"Delta: {EMBEDDINGS_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Pull Data from Qdrant into Pandas

# COMMAND ----------

from qdrant_client import QdrantClient

def pull_all_from_qdrant(url: str, api_key: str, collection: str, batch_size: int = 100) -> pd.DataFrame:
    """Scroll through entire Qdrant collection and return as DataFrame."""
    client = QdrantClient(url=url, api_key=api_key)
    
    info = client.get_collection(collection)
    total_points = info.points_count
    print(f"Collection '{collection}' has {total_points} points")
    
    records = []
    offset = None
    batch_num = 0
    
    while True:
        result = client.scroll(
            collection_name=collection,
            limit=batch_size,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        points, next_offset = result
        
        if not points:
            break
            
        for point in points:
            record = {
                "point_id": str(point.id),
                # Payload fields
                **{k: v for k, v in (point.payload or {}).items()},
            }
            # Extract named vectors
            if isinstance(point.vector, dict):
                for vec_name, vec_data in point.vector.items():
                    record[f"vec_{vec_name}"] = vec_data
            else:
                record["vec_full_document"] = point.vector
                
            records.append(record)
        
        batch_num += 1
        print(f"  Batch {batch_num}: pulled {len(points)} points (total: {len(records)}/{total_points})")
        
        if next_offset is None:
            break
        offset = next_offset
    
    df = pd.DataFrame(records)
    print(f"\nPulled {len(df)} records with {len(df.columns)} columns")
    return df

# Pull data
qdrant_df = pull_all_from_qdrant(QDRANT_CLOUD_URL, QDRANT_API_KEY, COLLECTION_NAME)
display(qdrant_df.head())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Store in Delta Tables (Lakehouse)
# MAGIC
# MAGIC Split into two Delta tables:
# MAGIC - **facility_embeddings**: point_id + 3 vector arrays (for search)
# MAGIC - **facility_metadata**: point_id + all payload fields (for filtering/display)

# COMMAND ----------

# Create schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

# -- Metadata table --
meta_cols = [c for c in qdrant_df.columns if not c.startswith("vec_")]
meta_df = qdrant_df[meta_cols].copy()

# Convert list columns to JSON strings for Delta compatibility
list_cols = ["specialties", "procedure", "equipment", "capability", 
             "phone_numbers", "websites", "affiliationTypeIds", "countries"]
for col in list_cols:
    if col in meta_df.columns:
        meta_df[col] = meta_df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)

spark_meta = spark.createDataFrame(meta_df)
spark_meta.write.mode("overwrite").saveAsTable(METADATA_TABLE)
print(f"Saved {len(meta_df)} rows to {METADATA_TABLE}")

# -- Embeddings table --
vec_cols = ["point_id"] + [c for c in qdrant_df.columns if c.startswith("vec_")]
emb_records = []
for _, row in qdrant_df.iterrows():
    rec = {"point_id": row["point_id"]}
    for vc in vec_cols:
        if vc == "point_id":
            continue
        vec = row.get(vc)
        if vec is not None and isinstance(vec, list):
            rec[vc] = json.dumps(vec)  # Store as JSON string
    emb_records.append(rec)

emb_df = pd.DataFrame(emb_records)
spark_emb = spark.createDataFrame(emb_df)
spark_emb.write.mode("overwrite").saveAsTable(EMBEDDINGS_TABLE)
print(f"Saved {len(emb_df)} embedding rows to {EMBEDDINGS_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. MLflow Experiment Tracking
# MAGIC
# MAGIC Track the vectorization pipeline as an MLflow experiment:
# MAGIC - Log embedding model parameters
# MAGIC - Log data quality metrics
# MAGIC - Register the embedding model as an MLflow artifact

# COMMAND ----------

import mlflow
from sentence_transformers import SentenceTransformer

# Set experiment
mlflow.set_experiment(EXPERIMENT_NAME)

# Load embedding model
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

with mlflow.start_run(run_name="vectorization-pipeline") as run:
    # -- Log parameters --
    mlflow.log_param("embedding_model", EMBEDDING_MODEL_NAME)
    mlflow.log_param("embedding_dim", EMBEDDING_DIM)
    mlflow.log_param("collection_name", COLLECTION_NAME)
    mlflow.log_param("vector_names", "full_document,clinical_detail,specialties_context")
    mlflow.log_param("distance_metric", "cosine")
    mlflow.log_param("source", "qdrant_cloud")
    mlflow.log_param("target", "delta_lakehouse")
    
    # -- Log data quality metrics --
    total_facilities = len(qdrant_df)
    with_coords = qdrant_df["latitude"].notna().sum() if "latitude" in qdrant_df.columns else 0
    with_specialties = qdrant_df["specialties"].apply(
        lambda x: len(json.loads(x)) > 0 if isinstance(x, str) and x.startswith("[") else (len(x) > 0 if isinstance(x, list) else False)
    ).sum() if "specialties" in qdrant_df.columns else 0
    
    unique_regions = qdrant_df["address_stateOrRegion"].nunique() if "address_stateOrRegion" in qdrant_df.columns else 0
    
    mlflow.log_metric("total_facilities", total_facilities)
    mlflow.log_metric("facilities_with_coordinates", int(with_coords))
    mlflow.log_metric("facilities_with_specialties", int(with_specialties))
    mlflow.log_metric("coordinate_coverage_pct", round(with_coords / total_facilities * 100, 1) if total_facilities > 0 else 0)
    mlflow.log_metric("unique_regions", int(unique_regions))
    
    # -- Verify embeddings are valid --
    vec_col = "vec_full_document"
    if vec_col in qdrant_df.columns:
        sample_vecs = qdrant_df[vec_col].head(10).apply(
            lambda x: np.array(x) if isinstance(x, list) else np.zeros(EMBEDDING_DIM)
        )
        avg_norm = np.mean([np.linalg.norm(v) for v in sample_vecs])
        avg_dim = np.mean([len(v) for v in sample_vecs])
        mlflow.log_metric("avg_embedding_norm", round(avg_norm, 4))
        mlflow.log_metric("avg_embedding_dim", avg_dim)
    
    # -- Log the embedding model as artifact --
    # Save model info (not the full weights -- those are on HuggingFace)
    model_info = {
        "model_name": EMBEDDING_MODEL_NAME,
        "dimension": EMBEDDING_DIM,
        "max_seq_length": model.max_seq_length,
        "normalize_embeddings": True,
        "vector_names": ["full_document", "clinical_detail", "specialties_context"],
        "vector_descriptions": {
            "full_document": "Complete facility description for broad semantic search",
            "clinical_detail": "Procedures + equipment for clinical queries",
            "specialties_context": "Specialty + capability for specialty matching",
        },
    }
    mlflow.log_dict(model_info, "model_config.json")
    
    # -- Log Delta table locations --
    mlflow.log_param("embeddings_table", EMBEDDINGS_TABLE)
    mlflow.log_param("metadata_table", METADATA_TABLE)
    
    # -- Tag the run --
    mlflow.set_tag("pipeline", "vectorization")
    mlflow.set_tag("data_source", "virtue_foundation_ghana")
    mlflow.set_tag("stage", "production")
    
    run_id = run.info.run_id
    print(f"MLflow Run ID: {run_id}")
    print(f"Experiment: {EXPERIMENT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Vector Search on Delta (Databricks-Native)
# MAGIC
# MAGIC Cosine similarity search directly on the Delta table embeddings.
# MAGIC This replaces direct Qdrant queries with a Databricks-native path.

# COMMAND ----------

from sentence_transformers import SentenceTransformer
import numpy as np
import json

class DatabricksVectorSearch:
    """
    Vector search over Delta table embeddings.
    Mirrors the Qdrant search_facilities() interface so the backend
    can swap between Qdrant and Databricks transparently.
    """
    
    def __init__(self, spark_session, model_name: str = EMBEDDING_MODEL_NAME):
        self.spark = spark_session
        self.model = SentenceTransformer(model_name)
        self._embeddings_cache = None
        self._metadata_cache = None
    
    def _load_data(self):
        """Load embeddings + metadata from Delta into memory (cached)."""
        if self._embeddings_cache is not None:
            return
        
        t0 = time.time()
        # Load embeddings
        emb_df = self.spark.table(EMBEDDINGS_TABLE).toPandas()
        # Load metadata
        meta_df = self.spark.table(METADATA_TABLE).toPandas()
        
        # Parse vector JSON strings back to numpy arrays
        self._point_ids = emb_df["point_id"].values
        
        vec_names = ["vec_full_document", "vec_clinical_detail", "vec_specialties_context"]
        self._vectors = {}
        for vn in vec_names:
            if vn in emb_df.columns:
                vecs = emb_df[vn].apply(
                    lambda x: np.array(json.loads(x)) if isinstance(x, str) else np.zeros(EMBEDDING_DIM)
                ).values
                self._vectors[vn] = np.stack(vecs)
        
        # Build metadata lookup
        self._metadata_cache = meta_df.set_index("point_id").to_dict("index")
        
        elapsed = time.time() - t0
        print(f"Loaded {len(emb_df)} embeddings + metadata in {elapsed:.1f}s")
    
    def search(
        self,
        query: str,
        vector_name: str = "vec_full_document",
        top_k: int = 10,
        org_type: Optional[str] = None,
        facility_type: Optional[str] = None,
        city: Optional[str] = None,
        specialties_filter: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Cosine similarity search -- same interface as Qdrant search_facilities()."""
        self._load_data()
        
        if vector_name not in self._vectors:
            # Try with vec_ prefix
            prefixed = f"vec_{vector_name}"
            if prefixed in self._vectors:
                vector_name = prefixed
            else:
                return []
        
        # Encode query
        query_vec = self.model.encode(query, normalize_embeddings=True)
        
        # Cosine similarity (vectors are already normalized)
        doc_vecs = self._vectors[vector_name]
        scores = doc_vecs @ query_vec  # dot product = cosine for normalized vectors
        
        # Apply metadata filters
        mask = np.ones(len(scores), dtype=bool)
        for i, pid in enumerate(self._point_ids):
            meta = self._metadata_cache.get(pid, {})
            if org_type and meta.get("organization_type") != org_type:
                mask[i] = False
            if facility_type and meta.get("facilityTypeId") != facility_type:
                mask[i] = False
            if city and meta.get("address_city") != city:
                mask[i] = False
            if specialties_filter:
                specs = meta.get("specialties", "[]")
                if isinstance(specs, str):
                    specs = json.loads(specs) if specs.startswith("[") else []
                if not any(s in specs for s in specialties_filter):
                    mask[i] = False
        
        # Mask out filtered results
        scores[~mask] = -1.0
        
        # Top-k
        top_indices = np.argsort(-scores)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] < 0:
                break
            pid = self._point_ids[idx]
            meta = self._metadata_cache.get(pid, {})
            
            # Parse list fields
            def _parse_list(val):
                if isinstance(val, list):
                    return val
                if isinstance(val, str) and val.startswith("["):
                    try:
                        return json.loads(val)
                    except:
                        return []
                return []
            
            results.append({
                "id": pid,
                "score": float(scores[idx]),
                "name": meta.get("name"),
                "organization_type": meta.get("organization_type"),
                "facilityTypeId": meta.get("facilityTypeId"),
                "city": meta.get("address_city"),
                "region": meta.get("address_stateOrRegion"),
                "specialties": _parse_list(meta.get("specialties", "[]")),
                "procedure": _parse_list(meta.get("procedure", "[]")),
                "equipment": _parse_list(meta.get("equipment", "[]")),
                "capability": _parse_list(meta.get("capability", "[]")),
                "capacity": meta.get("capacity"),
                "numberDoctors": meta.get("numberDoctors"),
                "latitude": meta.get("latitude"),
                "longitude": meta.get("longitude"),
                "source_url": meta.get("source_url"),
                "document_text": meta.get("document_text", ""),
            })
        
        return results

# -- Test the search --
searcher = DatabricksVectorSearch(spark)
results = searcher.search("hospitals with cardiology services in Accra", top_k=5)
for r in results:
    print(f"  {r['score']:.3f} | {r['name']} | {r['city']} | {r.get('specialties', [])}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Register Search Model in MLflow
# MAGIC
# MAGIC Register the `DatabricksVectorSearch` as an MLflow pyfunc model
# MAGIC so it can be served via Databricks Model Serving as a REST API.

# COMMAND ----------

import mlflow.pyfunc

class MedBridgeSearchModel(mlflow.pyfunc.PythonModel):
    """
    MLflow-compatible wrapper for the vector search model.
    Input:  DataFrame with columns: query, vector_name (optional), top_k (optional)
    Output: DataFrame with search results
    """
    
    def load_context(self, context):
        """Load the embedding model and Delta data on model startup."""
        from sentence_transformers import SentenceTransformer
        import json, numpy as np
        
        # Load model config from artifact
        config_path = context.artifacts.get("model_config")
        if config_path:
            with open(config_path) as f:
                self.config = json.load(f)
        else:
            self.config = {"model_name": "all-MiniLM-L6-v2", "dimension": 384}
        
        self.model = SentenceTransformer(self.config["model_name"])
        
        # Load cached embeddings from artifact
        data_path = context.artifacts.get("search_data")
        if data_path:
            import pickle
            with open(data_path, "rb") as f:
                data = pickle.load(f)
            self._point_ids = data["point_ids"]
            self._vectors = data["vectors"]
            self._metadata = data["metadata"]
        
    def predict(self, context, model_input):
        """Run vector search for each query in the input DataFrame."""
        import numpy as np, json
        
        results_list = []
        for _, row in model_input.iterrows():
            query = row["query"]
            vec_name = row.get("vector_name", "vec_full_document")
            top_k = int(row.get("top_k", 10))
            
            # Encode query
            q_vec = self.model.encode(query, normalize_embeddings=True)
            
            # Cosine search
            if vec_name in self._vectors:
                scores = self._vectors[vec_name] @ q_vec
            else:
                scores = np.zeros(len(self._point_ids))
            
            top_idx = np.argsort(-scores)[:top_k]
            
            hits = []
            for idx in top_idx:
                if scores[idx] < 0:
                    break
                pid = self._point_ids[idx]
                meta = self._metadata.get(pid, {})
                hits.append({
                    "id": pid,
                    "score": round(float(scores[idx]), 4),
                    "name": meta.get("name"),
                    "city": meta.get("address_city"),
                    "region": meta.get("address_stateOrRegion"),
                    "latitude": meta.get("latitude"),
                    "longitude": meta.get("longitude"),
                })
            
            results_list.append(json.dumps(hits))
        
        return pd.DataFrame({"results": results_list})

# -- Save search data as artifact --
import pickle

search_data = {
    "point_ids": searcher._point_ids,
    "vectors": searcher._vectors,
    "metadata": searcher._metadata_cache,
}

artifacts_dir = "/tmp/medbridge_artifacts"
os.makedirs(artifacts_dir, exist_ok=True)

data_path = f"{artifacts_dir}/search_data.pkl"
with open(data_path, "wb") as f:
    pickle.dump(search_data, f)

config_path = f"{artifacts_dir}/model_config.json"
with open(config_path, "w") as f:
    json.dump({
        "model_name": EMBEDDING_MODEL_NAME,
        "dimension": EMBEDDING_DIM,
    }, f)

# -- Register with MLflow --
with mlflow.start_run(run_name="search-model-registration"):
    mlflow.log_param("model_type", "vector_search")
    mlflow.log_param("embedding_model", EMBEDDING_MODEL_NAME)
    mlflow.log_metric("indexed_facilities", len(searcher._point_ids))
    
    model_info = mlflow.pyfunc.log_model(
        artifact_path="medbridge_search",
        python_model=MedBridgeSearchModel(),
        artifacts={
            "search_data": data_path,
            "model_config": config_path,
        },
        pip_requirements=["sentence-transformers", "numpy", "pandas"],
        registered_model_name="medbridge-vector-search",
    )
    
    print(f"Model registered: {model_info.model_uri}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Validate: Test the Registered Model

# COMMAND ----------

# Load the registered model and test
loaded_model = mlflow.pyfunc.load_model(model_info.model_uri)

test_queries = pd.DataFrame({
    "query": [
        "hospitals with cardiology services",
        "eye care clinics in Kumasi",
        "facilities with MRI equipment",
    ],
    "vector_name": ["vec_full_document", "vec_specialties_context", "vec_clinical_detail"],
    "top_k": [5, 5, 5],
})

predictions = loaded_model.predict(test_queries)
for i, row in predictions.iterrows():
    results = json.loads(row["results"])
    q = test_queries.iloc[i]["query"]
    print(f"\nQuery: {q}")
    for r in results[:3]:
        print(f"  {r['score']:.3f} | {r['name']} | {r.get('city', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Pipeline Summary & Serving Endpoint
# MAGIC
# MAGIC ### What was done:
# MAGIC 1. **Data Migration**: Pulled all 797 facility records from Qdrant Cloud into Delta tables
# MAGIC 2. **MLflow Tracking**: Logged model params, data quality metrics, embedding stats
# MAGIC 3. **Model Registry**: Registered `medbridge-vector-search` in MLflow Model Registry
# MAGIC 4. **Delta Lakehouse**: Embeddings + metadata stored in `hive_metastore.medbridge_ai`
# MAGIC
# MAGIC ### To serve as REST API:
# MAGIC 1. Go to **Serving** in the Databricks sidebar
# MAGIC 2. Click **Create serving endpoint**
# MAGIC 3. Select model: `medbridge-vector-search` (latest version)
# MAGIC 4. The endpoint will accept POST requests with:
# MAGIC ```json
# MAGIC {
# MAGIC   "dataframe_records": [
# MAGIC     {"query": "hospitals near Kumasi", "vector_name": "vec_full_document", "top_k": 10}
# MAGIC   ]
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC ### Backend Integration:
# MAGIC Set these in your `.env`:
# MAGIC ```
# MAGIC DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
# MAGIC DATABRICKS_TOKEN=dapi...
# MAGIC DATABRICKS_SERVING_ENDPOINT=medbridge-vector-search
# MAGIC ```
