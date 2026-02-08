"""
MedBridge AI — FastAPI Application
=====================================
Main FastAPI app with CORS, lifespan events, and route mounting.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up agent singletons on startup."""
    print("[*] MedBridge AI - warming up agents...")
    # Pre-load the orchestration workflow (loads data + models once)
    from backend.orchestration.graph import build_workflow
    build_workflow()
    print("[+] Agents ready")
    yield
    print("[*] Shutting down MedBridge AI")


app = FastAPI(
    title="MedBridge AI",
    description="Multi-Agent Healthcare Intelligence for Ghana",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
