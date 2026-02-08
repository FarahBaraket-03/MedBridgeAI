"""
MedBridge AI — Vector Store (Qdrant Multi-Representation)
==========================================================
Handles embedding, Qdrant collection management, and multi-vector search.
Three named vectors per facility:
  - full_document:  broad semantic search
  - clinical_detail: procedures + equipment queries
  - specialties_context: specialty/capability matching
"""

import uuid
from typing import Dict, List, Optional

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, MatchAny, MatchValue,
    PayloadSchemaType, PointStruct, VectorParams,
)
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from backend.core.config import (
    COLLECTION_FACILITIES, EMBED_BATCH_SIZE, EMBEDDING_DIM,
    EMBEDDING_MODEL_NAME, QDRANT_API_KEY, QDRANT_CLOUD_URL,
    VEC_CLINICAL, VEC_FULL, VEC_SPECIALTIES,
)
from backend.core.preprocessing import run_preprocessing


# ── Singleton holders ────────────────────────────────────────────────────────
_model_cache: Optional[SentenceTransformer] = None
_client_cache: Optional[QdrantClient] = None


def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    global _model_cache
    if _model_cache is None:
        print(f"  Loading embedding model: {model_name} ...")
        _model_cache = SentenceTransformer(model_name)
        print(f"  Model loaded - dimension: {_model_cache.get_sentence_embedding_dimension()}")
    return _model_cache


def get_qdrant_client() -> QdrantClient:
    global _client_cache
    if _client_cache is None:
        if not QDRANT_CLOUD_URL or not QDRANT_API_KEY:
            raise ConnectionError(
                "Qdrant credentials not configured. "
                "Set QDRANT_CLOUD_URL and QDRANT_API_KEY in your .env file. "
                "Vector search will be unavailable."
            )
        print("  Qdrant Cloud: connecting...")
        _client_cache = QdrantClient(url=QDRANT_CLOUD_URL, api_key=QDRANT_API_KEY)
    return _client_cache


# ── Embedding helpers ────────────────────────────────────────────────────────

def embed_texts(texts: List[str], model: Optional[SentenceTransformer] = None, batch_size: int = EMBED_BATCH_SIZE) -> List[List[float]]:
    model = model or load_embedding_model()
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=False,
                              convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.tolist()


def embed_single(text: str, model: Optional[SentenceTransformer] = None) -> List[float]:
    model = model or load_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()


# ── Multi-representation text building ───────────────────────────────────────

def build_multi_representations(df: pd.DataFrame) -> pd.DataFrame:
    clinical_texts, specialty_texts = [], []
    for _, row in df.iterrows():
        meta = row["metadata"]
        parts = []
        procs = meta.get("procedure", [])
        if procs:
            parts.append("Procedures: " + "; ".join(procs))
        equip = meta.get("equipment", [])
        if equip:
            parts.append("Equipment: " + "; ".join(equip))
        caps = meta.get("capability", [])
        if caps:
            parts.append("Capabilities: " + "; ".join(caps))
        clinical = " | ".join(parts) if parts else f"{meta.get('name', 'Unknown')} medical facility"
        clinical_texts.append(clinical)

        specs = meta.get("specialties", [])
        name = meta.get("name", "Unknown")
        org = meta.get("organization_type", "facility")
        ftype = meta.get("facilityTypeId", "")
        spec_str = ", ".join(specs) if specs else "general"
        specialty_texts.append(f"{name} is a {org} ({ftype}) with specialties: {spec_str}")

    df = df.copy()
    df["clinical_text"] = clinical_texts
    df["specialty_text"] = specialty_texts
    return df


# ── Qdrant collection management ────────────────────────────────────────────

def create_collection(client: Optional[QdrantClient] = None, recreate: bool = True) -> None:
    client = client or get_qdrant_client()
    if recreate:
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION_FACILITIES in existing:
            client.delete_collection(COLLECTION_FACILITIES)
            print(f"  Deleted existing collection: {COLLECTION_FACILITIES}")

    client.create_collection(
        collection_name=COLLECTION_FACILITIES,
        vectors_config={
            VEC_FULL: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            VEC_CLINICAL: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            VEC_SPECIALTIES: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        },
    )
    print(f"  Created collection: {COLLECTION_FACILITIES} (3 named vectors, dim={EMBEDDING_DIM})")

    for field in ["organization_type", "facilityTypeId", "address_city",
                  "address_stateOrRegion", "specialties", "name"]:
        client.create_payload_index(
            collection_name=COLLECTION_FACILITIES,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print("  Created payload indexes for filtering")


def _clean_payload(meta: Dict) -> Dict:
    clean = {}
    for k, v in meta.items():
        if v is None:
            clean[k] = None
        elif isinstance(v, float) and pd.isna(v):
            clean[k] = None
        elif isinstance(v, list):
            clean[k] = [str(item) for item in v]
        else:
            clean[k] = v
    return clean


def upsert_to_qdrant(
    client: QdrantClient,
    documents: List[str], clinical_texts: List[str], specialty_texts: List[str],
    emb_full: List[List[float]], emb_clinical: List[List[float]], emb_specialties: List[List[float]],
    metadata_list: List[Dict], batch_size: int = 100,
) -> None:
    points = []
    for idx in range(len(documents)):
        meta = metadata_list[idx]
        point_id = meta.get("unique_id") or str(uuid.uuid4())
        payload = _clean_payload(meta)
        payload["document_text"] = documents[idx]
        payload["clinical_text"] = clinical_texts[idx]
        payload["specialty_text"] = specialty_texts[idx]
        points.append(PointStruct(
            id=point_id,
            vector={VEC_FULL: emb_full[idx], VEC_CLINICAL: emb_clinical[idx], VEC_SPECIALTIES: emb_specialties[idx]},
            payload=payload,
        ))

    for i in tqdm(range(0, len(points), batch_size), desc="  Upserting to Qdrant"):
        client.upsert(collection_name=COLLECTION_FACILITIES, points=points[i:i + batch_size])
    print(f"  Upserted {len(points)} points to '{COLLECTION_FACILITIES}'")


# ── Search ───────────────────────────────────────────────────────────────────

def search_facilities(
    query: str,
    vector_name: str = VEC_FULL,
    top_k: int = 10,
    org_type: Optional[str] = None,
    facility_type: Optional[str] = None,
    city: Optional[str] = None,
    specialties_filter: Optional[List[str]] = None,
    client: Optional[QdrantClient] = None,
    model: Optional[SentenceTransformer] = None,
) -> List[Dict]:
    client = client or get_qdrant_client()
    model = model or load_embedding_model()

    # Transform query text to match the indexed document format for the
    # target vector.  The clinical_detail vector was built from structured
    # text like "Procedures: X | Equipment: Y", so embedding the raw
    # natural-language query directly causes a semantic gap.
    _QUERY_TEMPLATES = {
        VEC_CLINICAL: "Procedures: {q} | Equipment: {q}",
        VEC_SPECIALTIES: "facility with specialties: {q}",
        VEC_FULL: "{q}",
    }
    query_text = _QUERY_TEMPLATES.get(vector_name, "{q}").format(q=query)
    query_vector = model.encode(query_text, normalize_embeddings=True).tolist()

    conditions = []
    if org_type:
        conditions.append(FieldCondition(key="organization_type", match=MatchValue(value=org_type)))
    if facility_type:
        conditions.append(FieldCondition(key="facilityTypeId", match=MatchValue(value=facility_type)))
    if city:
        # Use OR logic: the user might type a city name that is actually a
        # region (e.g. "Greater Accra"), or vice-versa.  Matching both
        # fields avoids false-zero results.
        conditions.append(Filter(should=[
            FieldCondition(key="address_city", match=MatchValue(value=city)),
            FieldCondition(key="address_stateOrRegion", match=MatchValue(value=city)),
        ]))
    if specialties_filter:
        conditions.append(FieldCondition(key="specialties", match=MatchAny(any=specialties_filter)))

    search_filter = Filter(must=conditions) if conditions else None

    results = client.query_points(
        collection_name=COLLECTION_FACILITIES,
        query=query_vector,
        using=vector_name,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True,
    )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            "name": hit.payload.get("name"),
            "organization_type": hit.payload.get("organization_type"),
            "facilityTypeId": hit.payload.get("facilityTypeId"),
            "city": hit.payload.get("address_city"),
            "region": hit.payload.get("address_stateOrRegion"),
            "specialties": hit.payload.get("specialties", []),
            "procedure": hit.payload.get("procedure", []),
            "equipment": hit.payload.get("equipment", []),
            "capability": hit.payload.get("capability", []),
            "capacity": hit.payload.get("capacity"),
            "numberDoctors": hit.payload.get("numberDoctors"),
            "latitude": hit.payload.get("latitude"),
            "longitude": hit.payload.get("longitude"),
            "source_url": hit.payload.get("source_url"),
            "document_text": hit.payload.get("document_text", ""),
        }
        for hit in results.points
    ]


# ── Full pipeline ────────────────────────────────────────────────────────────

def run_vectorization_pipeline() -> tuple:
    print("=== MedBridge AI - Vectorization Pipeline ===\n")
    df = run_preprocessing()
    df = build_multi_representations(df)
    model = load_embedding_model()

    documents = df["document"].tolist()
    clinical_texts = df["clinical_text"].tolist()
    specialty_texts = df["specialty_text"].tolist()

    print("  Embedding full documents...")
    emb_full = embed_texts(documents, model)
    print("  Embedding clinical details...")
    emb_clinical = embed_texts(clinical_texts, model)
    print("  Embedding specialties context...")
    emb_specialties = embed_texts(specialty_texts, model)

    client = get_qdrant_client()
    create_collection(client)

    upsert_to_qdrant(client, documents, clinical_texts, specialty_texts,
                     emb_full, emb_clinical, emb_specialties, df["metadata"].tolist())

    info = client.get_collection(COLLECTION_FACILITIES)
    print(f"\n  Collection '{COLLECTION_FACILITIES}' has {info.points_count} points")
    print("=== Vectorization complete ===\n")
    return client, model


if __name__ == "__main__":
    run_vectorization_pipeline()
