#!/usr/bin/env python3
"""
LZ Network Optimizer - FastAPI Main Application
================================================
REST API backend for network optimization operations.
Provides endpoints for sites, parameters, KPIs, and system status.
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import routers
from api.routers import sites, parameters, kpis, system


# ============================================================================
# Lifespan Context Manager
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    print("🚀 LZ Network Optimizer API starting...")
    print(f"   Environment: {os.getenv('APP_ENV', 'development')}")
    yield
    # Shutdown
    print("👋 LZ Network Optimizer API shutting down...")


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="LZ Network Optimizer API",
    description="""
## Liquid Zimbabwe 4G Network Optimizer REST API

Provides programmatic access to network optimization operations:

- **Sites**: List and query network sites
- **Parameters**: Get live parameter values from Huawei API
- **KPIs**: Access real-time and historical KPI data
- **System**: Health checks and status monitoring

### Authentication
Currently open for internal use. API key authentication planned for external access.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================================
# CORS Middleware
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",      # Streamlit default
        "http://localhost:8502",      # Streamlit alternate
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8502",
        "http://0.0.0.0:8501",
        "http://0.0.0.0:8502",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Include Routers
# ============================================================================
app.include_router(sites.router, prefix="/api/sites", tags=["Sites"])
app.include_router(parameters.router, prefix="/api/params", tags=["Parameters"])
app.include_router(kpis.router, prefix="/api/kpis", tags=["KPIs"])
app.include_router(system.router, prefix="/api", tags=["System"])


# ============================================================================
# Root Endpoint
# ============================================================================
@app.get("/", tags=["Root"])
async def root():
    """API root - returns basic info and links to documentation."""
    return {
        "name": "LZ Network Optimizer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health"
    }


# ============================================================================
# Run with Uvicorn (for development)
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
