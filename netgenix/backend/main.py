"""
NetGenix Network Optimizer - FastAPI Backend
Production REST API for the React frontend
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add directories to path for imports
backend_dir = Path(__file__).parent
project_dir = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_dir))

# Load environment variables
load_dotenv(project_dir / ".env")

# Keep copied optimizer tools compatible with NetGenix env names.
os.environ.setdefault("HUAWEI_API_URL", os.getenv("NETGENIX_HUAWEI_ACCESS_NBI_URL", ""))
os.environ.setdefault("HUAWEI_USERNAME", os.getenv("NETGENIX_HUAWEI_USERNAME", ""))
os.environ.setdefault("HUAWEI_PASSWORD", os.getenv("NETGENIX_HUAWEI_PASSWORD", ""))

# Import routers
from backend.api.routes import activity, diagnostics, evaluation, kpi, optimization, reports, sites, status, topology

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    print("NetGenix Backend starting up...")
    yield
    # Shutdown
    print("NetGenix Backend shutting down...")

# Create FastAPI app
app = FastAPI(
    title="NetGenix Network Optimizer API",
    description="AI-Powered 4G Network Optimization Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5180",
        "http://localhost:8502",
        "http://localhost:8507",
        "http://localhost:8511",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5180",
        "http://127.0.0.1:8502",
        "http://127.0.0.1:8507",
        "http://127.0.0.1:8511",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(optimization.router, prefix="/api/optimize", tags=["Optimization"])
app.include_router(kpi.router, prefix="/api/kpi", tags=["KPI"])
app.include_router(activity.router, prefix="/api/activity", tags=["Activity"])
app.include_router(status.router, prefix="/api/status", tags=["Status"])
app.include_router(diagnostics.router, prefix="/api/diagnostics", tags=["Diagnostics"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(topology.router, prefix="/api/topology", tags=["Topology"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "NetGenix Network Optimizer API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
