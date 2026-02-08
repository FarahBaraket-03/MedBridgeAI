"""
MedBridge AI — FastAPI Backend
===============================
Serves the unified frontend and exposes API endpoints
for the Supervisor → Agent pipeline.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.agents.genie_chat import GenieChatAgent
from src.agents.vector_search import VectorSearchAgent
from src.vectorize_and_store import get_qdrant_client, load_embedding_model

# ── Init FastAPI ─────────────────────────────────────────────────────────────
app = FastAPI(title="MedBridge AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy-load agents (singletons) ────────────────────────────────────────────
_client = None
_model = None
_genie: Optional[GenieChatAgent] = None
_vector: Optional[VectorSearchAgent] = None


def _ensure_agents():
    global _client, _model, _genie, _vector
    if _genie is None:
        _client = get_qdrant_client()
        _model = load_embedding_model()
        _genie = GenieChatAgent()
        _vector = VectorSearchAgent(client=_client, model=_model)


# ── Request / Response models ────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    top_k: int = 10


class QueryResponse(BaseModel):
    agent: str
    result: dict


# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    """Serve the unified frontend."""
    html_path = Path(__file__).resolve().parent.parent / "frontend" / "index.html"
    if not html_path.exists():
        raise HTTPException(404, "Frontend not found")
    return FileResponse(html_path, media_type="text/html")


@app.post("/api/query")
def handle_query(req: QueryRequest):
    """
    Main query endpoint — routes to appropriate agent.
    Simple keyword heuristic (like the Supervisor):
      - aggregation / count / how many → Genie
      - else → Vector Search
    """
    _ensure_agents()

    q = req.query.lower()
    genie_signals = [
        "how many", "count", "region", "aggregate", "distribution",
        "which region", "anomal", "ratio", "single point",
        "depend on very few", "oversupply", "correlation",
    ]

    if any(sig in q for sig in genie_signals):
        result = _genie.execute_query(req.query)
        return QueryResponse(agent="genie_chat", result=result if isinstance(result, dict) else {"raw": str(result)})
    else:
        result = _vector.search(req.query, top_k=req.top_k)
        return QueryResponse(agent="vector_search", result=result)


@app.post("/api/genie")
def genie_query(req: QueryRequest):
    """Direct Genie Chat endpoint."""
    _ensure_agents()
    result = _genie.execute_query(req.query)
    return {"agent": "genie_chat", "result": result if isinstance(result, dict) else {"raw": str(result)}}


@app.post("/api/vector")
def vector_query(req: QueryRequest):
    """Direct Vector Search endpoint."""
    _ensure_agents()
    result = _vector.search(req.query, top_k=req.top_k)
    return {"agent": "vector_search", "result": result}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
