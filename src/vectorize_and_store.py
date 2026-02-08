"""
MedBridge AI — Enhanced Vectorization & Qdrant Ingestion
=========================================================
Multi-representation embedding strategy:
  1. Full document embedding  — for broad semantic search
  2. Specialties embedding    — for capability-specific queries
  3. Procedures+Equipment     — for clinical detail queries

All stored as named vectors in a single Qdrant collection for
flexible hybrid search.
"""

import uuid
from typing import Dict, List, Optional

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from src.config import (
    COLLECTION_FACILITIES,
    EMBED_BATCH_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_MODEL_NAME,
    QDRANT_API_KEY,
    QDRANT_CLOUD_URL,
)
from src.data_preprocessing import run_preprocessing

# Named vector keys
VEC_FULL = "full_document"
VEC_CLINICAL = "clinical_detail"
VEC_SPECIALTIES = "specialties_context"


# ─────────────────────────────────────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────────────────────────────────────


def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    print(f"  Loading embedding model: {model_name} ...")
    model = SentenceTransformer(model_name)
    print(f"  Model loaded — dimension: {model.get_sentence_embedding_dimension()}")
    return model


def _embed_batch(texts: List[str], model: SentenceTransformer, batch_size: int = EMBED_BATCH_SIZE) -> List[List[float]]:
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


def build_multi_representations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build 3 text representations per facility for multi-vector embedding:
      1. full_document — the complete document text (already built)
      2. clinical_detail — procedures + equipment + capabilities concatenated
      3. specialties_context — specialties + name + type for capability matching
    """
    clinical_texts = []
    specialty_texts = []

    for _, row in df.iterrows():
        meta = row["metadata"]

        # Clinical detail text
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

        # Specialties context text
        specs = meta.get("specialties", [])
        name = meta.get("name", "Unknown")
        org = meta.get("organization_type", "facility")
        ftype = meta.get("facilityTypeId", "")
        spec_str = ", ".join(specs) if specs else "general"
        specialty_texts.append(
            f"{name} is a {org} ({ftype}) with specialties: {spec_str}"
        )

    df = df.copy()
    df["clinical_text"] = clinical_texts
    df["specialty_text"] = specialty_texts
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Qdrant
# ─────────────────────────────────────────────────────────────────────────────


def get_qdrant_client() -> QdrantClient:
    print(f"  Qdrant Cloud: connecting...")
    return QdrantClient(url=QDRANT_CLOUD_URL, api_key=QDRANT_API_KEY)


def create_collection(client: QdrantClient, recreate: bool = True) -> None:
    """Create collection with named vectors for multi-representation search."""
    collection_name = COLLECTION_FACILITIES

    if recreate:
        existing = [c.name for c in client.get_collections().collections]
        if collection_name in existing:
            client.delete_collection(collection_name)
            print(f"  Deleted existing collection: {collection_name}")

    client.create_collection(
        collection_name=collection_name,
        vectors_config={
            VEC_FULL: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            VEC_CLINICAL: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            VEC_SPECIALTIES: VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        },
    )
    print(f"  Created collection: {collection_name} (3 named vectors, dim={EMBEDDING_DIM})")

    # Create payload indexes for filterable fields
    from qdrant_client.models import PayloadSchemaType

    for field in ["organization_type", "facilityTypeId", "address_city",
                  "address_stateOrRegion", "specialties", "name"]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print(f"  Created payload indexes for filtering")


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
    documents: List[str],
    clinical_texts: List[str],
    specialty_texts: List[str],
    emb_full: List[List[float]],
    emb_clinical: List[List[float]],
    emb_specialties: List[List[float]],
    metadata_list: List[Dict],
    batch_size: int = 100,
) -> None:
    points = []
    for idx in range(len(documents)):
        meta = metadata_list[idx]
        point_id = meta.get("unique_id") or str(uuid.uuid4())

        payload = _clean_payload(meta)
        payload["document_text"] = documents[idx]
        payload["clinical_text"] = clinical_texts[idx]
        payload["specialty_text"] = specialty_texts[idx]

        points.append(
            PointStruct(
                id=point_id,
                vector={
                    VEC_FULL: emb_full[idx],
                    VEC_CLINICAL: emb_clinical[idx],
                    VEC_SPECIALTIES: emb_specialties[idx],
                },
                payload=payload,
            )
        )

    total = len(points)
    for i in tqdm(range(0, total, batch_size), desc="  Upserting to Qdrant"):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=COLLECTION_FACILITIES, points=batch)

    print(f"  Upserted {total} points to '{COLLECTION_FACILITIES}'")


# ─────────────────────────────────────────────────────────────────────────────
# Search helpers
# ─────────────────────────────────────────────────────────────────────────────


def search_facilities(
    client: QdrantClient,
    model: SentenceTransformer,
    query: str,
    vector_name: str = VEC_FULL,
    top_k: int = 10,
    org_type: Optional[str] = None,
    facility_type: Optional[str] = None,
    city: Optional[str] = None,
    specialties_filter: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Semantic search with optional metadata filtering.
    vector_name controls which representation is queried:
      - 'full_document' for broad queries
      - 'clinical_detail' for procedure/equipment queries
      - 'specialties_context' for specialty matching
    """
    query_vector = model.encode(query, normalize_embeddings=True).tolist()

    conditions = []
    if org_type:
        conditions.append(FieldCondition(key="organization_type", match=MatchValue(value=org_type)))
    if facility_type:
        conditions.append(FieldCondition(key="facilityTypeId", match=MatchValue(value=facility_type)))
    if city:
        conditions.append(FieldCondition(key="address_city", match=MatchValue(value=city)))
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
            "source_url": hit.payload.get("source_url"),
            "document_text": hit.payload.get("document_text", ""),
        }
        for hit in results.points
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────


def run_vectorization_pipeline() -> tuple:
    """
    Full pipeline:
      1. Preprocess data
      2. Build multi-representations
      3. Embed all 3 representations
      4. Create Qdrant collection with named vectors
      5. Upsert everything
    Returns (client, model) for downstream use.
    """
    print("═══ MedBridge AI — Enhanced Vectorization Pipeline ═══\n")

    # Step 1: Preprocess
    df = run_preprocessing()

    # Step 2: Multi-representation texts
    df = build_multi_representations(df)

    # Step 3: Load model & embed
    model = load_embedding_model()

    documents = df["document"].tolist()
    clinical_texts = df["clinical_text"].tolist()
    specialty_texts = df["specialty_text"].tolist()

    print("  Embedding full documents...")
    emb_full = _embed_batch(documents, model)
    print("  Embedding clinical details...")
    emb_clinical = _embed_batch(clinical_texts, model)
    print("  Embedding specialties context...")
    emb_specialties = _embed_batch(specialty_texts, model)

    # Step 4: Qdrant
    client = get_qdrant_client()
    create_collection(client)

    # Step 5: Upsert
    metadata_list = df["metadata"].tolist()
    upsert_to_qdrant(
        client, documents, clinical_texts, specialty_texts,
        emb_full, emb_clinical, emb_specialties, metadata_list,
    )

    info = client.get_collection(COLLECTION_FACILITIES)
    print(f"\n  Collection '{COLLECTION_FACILITIES}' has {info.points_count} points")
    print("═══ Vectorization complete ═══\n")

    return client, model


if __name__ == "__main__":
    client, model = run_vectorization_pipeline()

    print("── Demo: Multi-Vector Search ──\n")

    # Broad search (full document vector)
    print("1) Full document search: 'hospitals with cardiology'")
    for r in search_facilities(client, model, "hospitals with cardiology", VEC_FULL, top_k=3):
        print(f"   [{r['score']:.3f}] {r['name']} — {r['city']}")

    # Clinical detail search
    print("\n2) Clinical search: 'cataract surgery phacoemulsification'")
    for r in search_facilities(client, model, "cataract surgery phacoemulsification", VEC_CLINICAL, top_k=3):
        print(f"   [{r['score']:.3f}] {r['name']} — procs: {r['procedure'][:2]}")

    # Specialty search with filter
    print("\n3) Specialty search: 'emergency trauma' (hospitals only)")
    for r in search_facilities(client, model, "emergency trauma center", VEC_SPECIALTIES, top_k=3, facility_type="hospital"):
        print(f"   [{r['score']:.3f}] {r['name']} — specs: {r['specialties'][:3]}")
