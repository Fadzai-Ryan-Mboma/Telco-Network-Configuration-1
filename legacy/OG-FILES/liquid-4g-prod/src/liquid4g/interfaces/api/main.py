"""
FastAPI REST API

Provides HTTP endpoints for the network optimization system.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from liquid4g.core.config import get_settings
from liquid4g.core.logging import get_logger
from liquid4g.agents.orchestrator import AgentOrchestrator
from liquid4g.infrastructure.repositories import (
    NetworkRepository,
    KPIRepository,
    ParameterRepository,
    OperationRepository,
    AgentRepository
)
from liquid4g.infrastructure.database.migrations import get_migration_manager
from liquid4g.infrastructure.api.huawei_client import HuaweiAPIClient

logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Liquid 4G Network Optimizer",
    description="AI-powered network optimization system",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repositories
network_repo = NetworkRepository()
kpi_repo = KPIRepository()
param_repo = ParameterRepository()
operation_repo = OperationRepository()
agent_repo = AgentRepository()

# Orchestrator
orchestrator = AgentOrchestrator()

# Huawei client (lazy initialization)
_huawei_client = None

def get_huawei_client() -> HuaweiAPIClient:
    """Get or create Huawei client instance"""
    global _huawei_client
    if _huawei_client is None:
        _huawei_client = HuaweiAPIClient()
    return _huawei_client


# === Request/Response Models ===

class OptimizeRequest(BaseModel):
    """Request to optimize a cell"""
    cell_id: str
    auto_execute: bool = False


class SiteOptimizeRequest(BaseModel):
    """Request to optimize a site"""
    site_id: str
    auto_execute: bool = False


# === Health & Status ===

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Liquid 4G Network Optimizer",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    migration_mgr = get_migration_manager()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "initialized": migration_mgr.is_initialized(),
            "version": migration_mgr.get_current_version()
        }
    }


# === Huawei API ===

@app.get("/api/v1/huawei/health")
def huawei_health_check():
    """Check Huawei API health and connectivity"""
    try:
        client = get_huawei_client()
        
        # Perform health check using the client
        health_result = client.health_check()
        
        return {
            "status": "healthy" if health_result else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "authenticated": health_result
        }
        
    except Exception as e:
        logger.error(f"Huawei health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Huawei API health check failed: {str(e)}"
        )


@app.get("/api/v1/huawei/status")
def huawei_connection_status():
    """Get detailed Huawei API connection status"""
    try:
        client = get_huawei_client()
        
        # Get configuration status
        config_status = client.get_configuration_status()
        
        return {
            "connected": config_status.get("is_connected", False),
            "authenticated": config_status.get("is_authenticated", False),
            "network_elements": config_status.get("network_elements_count", 0),
            "parameters": config_status.get("parameter_configs_count", 0),
            "last_check": config_status.get("last_check"),
            "api_health": config_status.get("api_health", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Failed to get Huawei connection status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Huawei connection status: {str(e)}"
        )


@app.get("/huawei/health")
def huawei_health_legacy():
    """Legacy Huawei health endpoint for UI compatibility"""
    return huawei_health_check()


# === Network Sites ===
from liquid4g.infrastructure.api.huawei_client import HuaweiAPIClient

logger = get_logger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Liquid 4G Network Optimizer",
    description="AI-powered network optimization system",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repositories
network_repo = NetworkRepository()
kpi_repo = KPIRepository()
param_repo = ParameterRepository()
operation_repo = OperationRepository()
agent_repo = AgentRepository()

# Orchestrator
orchestrator = AgentOrchestrator()

# Huawei client (lazy initialization)
_huawei_client = None

def get_huawei_client() -> HuaweiAPIClient:
    """Get or create Huawei client instance"""
    global _huawei_client
    if _huawei_client is None:
        _huawei_client = HuaweiAPIClient()
    return _huawei_client


# === Request/Response Models ===

class OptimizeRequest(BaseModel):
    """Request to optimize a cell"""
    cell_id: str
    auto_execute: bool = False


class SiteOptimizeRequest(BaseModel):
    """Request to optimize a site"""
    site_id: str
    auto_execute: bool = False


# === Health & Status ===

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Liquid 4G Network Optimizer",
        "version": "2.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    migration_mgr = get_migration_manager()

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "initialized": migration_mgr.is_initialized(),
            "version": migration_mgr.get_current_version()
        }
    }


# === Network Resources ===

@app.get("/api/v1/sites")
def list_sites(limit: Optional[int] = 100, offset: int = 0):
    """List all network sites"""
    sites = network_repo.list_all(limit=limit, offset=offset)
    return {
        "total": len(sites),
        "sites": [
            {
                "id": s.id,
                "site_id": s.site_id,
                "site_name": s.site_name,
                "location": s.location,
                "status": s.status,
                "region": s.region
            }
            for s in sites
        ]
    }


@app.get("/api/v1/sites/{site_id}")
def get_site(site_id: str):
    """Get site details"""
    site = network_repo.get_by_site_id(site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    cells = network_repo.list_cells_by_site(site_id)

    return {
        "site": {
            "id": site.id,
            "site_id": site.site_id,
            "site_name": site.site_name,
            "location": site.location,
            "status": site.status,
            "region": site.region
        },
        "cells": [
            {
                "id": c.id,
                "cell_id": c.cell_id,
                "cell_name": c.cell_name,
                "technology": c.technology,
                "status": c.status,
                "pci": c.pci,
                "sector": c.sector
            }
            for c in cells
        ]
    }


@app.get("/api/v1/cells/{cell_id}")
def get_cell(cell_id: str):
    """Get cell details"""
    cell = network_repo.get_cell_by_id(cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    return {
        "id": cell.id,
        "cell_id": cell.cell_id,
        "site_id": cell.site_id,
        "cell_name": cell.cell_name,
        "technology": cell.technology,
        "status": cell.status,
        "pci": cell.pci,
        "sector": cell.sector,
        "azimuth": cell.azimuth
    }


# === KPIs ===

@app.get("/api/v1/cells/{cell_id}/kpis")
def get_cell_kpis(cell_id: str, kpi_key: Optional[str] = None):
    """Get KPIs for a cell"""
    if kpi_key:
        kpi = kpi_repo.get_latest_for_cell(cell_id, kpi_key)
        if not kpi:
            raise HTTPException(status_code=404, detail="KPI not found")
        return {
            "kpi_key": kpi.kpi_key,
            "value": kpi.value,
            "measurement_time": kpi.measurement_time.isoformat()
        }
    else:
        # Get latest for all KPI types
        kpi_keys = ["network_access_success", "drop_rate", "handover_success_rate", "average_rsrp"]
        kpis = []
        for key in kpi_keys:
            kpi = kpi_repo.get_latest_for_cell(cell_id, key)
            if kpi:
                kpis.append({
                    "kpi_key": kpi.kpi_key,
                    "value": kpi.value,
                    "measurement_time": kpi.measurement_time.isoformat()
                })
        return {"kpis": kpis}


@app.get("/api/v1/cells/{cell_id}/kpis/{kpi_key}/history")
def get_kpi_history(cell_id: str, kpi_key: str, limit: int = 100):
    """Get KPI time series"""
    from datetime import timedelta
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    kpis = kpi_repo.get_time_series(cell_id, kpi_key, start_time, end_time, limit=limit)

    return {
        "cell_id": cell_id,
        "kpi_key": kpi_key,
        "data_points": len(kpis),
        "data": [
            {
                "value": kpi.value,
                "timestamp": kpi.measurement_time.isoformat()
            }
            for kpi in kpis
        ]
    }


# === Parameters ===

@app.get("/api/v1/cells/{cell_id}/parameters")
def get_cell_parameters(cell_id: str):
    """Get parameters for a cell"""
    params = param_repo.get_all_for_cell(cell_id)

    return {
        "cell_id": cell_id,
        "parameters": [
            {
                "param_key": p.param_key,
                "value": p.value,
                "measured_at": p.measured_at.isoformat()
            }
            for p in params
        ]
    }


# === Optimization ===

@app.post("/api/v1/optimize/cell")
def optimize_cell(request: OptimizeRequest, background_tasks: BackgroundTasks):
    """Optimize a specific cell"""
    # Validate cell exists
    cell = network_repo.get_cell_by_id(request.cell_id)
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")

    # Run optimization in background
    background_tasks.add_task(
        orchestrator.optimize_cell,
        request.cell_id,
        request.auto_execute
    )

    return {
        "status": "started",
        "cell_id": request.cell_id,
        "message": "Optimization started in background"
    }


@app.post("/api/v1/optimize/site")
def optimize_site(request: SiteOptimizeRequest, background_tasks: BackgroundTasks):
    """Optimize all cells in a site"""
    # Validate site exists
    site = network_repo.get_by_site_id(request.site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Run optimization in background
    background_tasks.add_task(
        orchestrator.optimize_site,
        request.site_id,
        request.auto_execute
    )

    return {
        "status": "started",
        "site_id": request.site_id,
        "message": "Site optimization started in background"
    }


# === Operations ===

@app.get("/api/v1/operations")
def list_operations(status: Optional[str] = None, limit: int = 100):
    """List operations"""
    if status:
        operations = operation_repo.list_by_status(status, limit=limit)
    else:
        operations = operation_repo.list_all(limit=limit)

    return {
        "total": len(operations),
        "operations": [
            {
                "operation_id": op.operation_id,
                "operation_type": op.operation_type,
                "stage": op.stage,
                "status": op.status,
                "target_cell": op.target_cell,
                "started_at": op.started_at.isoformat(),
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "duration_seconds": op.duration_seconds
            }
            for op in operations
        ]
    }


@app.get("/api/v1/operations/{operation_id}")
def get_operation(operation_id: str):
    """Get operation details"""
    operation = operation_repo.get_by_operation_id(operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    # Get logs
    logs = operation_repo.get_logs(operation_id)

    return {
        "operation_id": operation.operation_id,
        "operation_type": operation.operation_type,
        "stage": operation.stage,
        "status": operation.status,
        "target_cell": operation.target_cell,
        "started_at": operation.started_at.isoformat(),
        "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
        "duration_seconds": operation.duration_seconds,
        "results": operation.results,
        "logs": [
            {
                "timestamp": log.log_time.isoformat(),
                "level": log.log_level,
                "message": log.message
            }
            for log in logs
        ]
    }


# === Agents ===

@app.get("/api/v1/agents")
def list_agents():
    """List all agents and their status"""
    agents = agent_repo.list_all()

    agent_statuses = []
    for agent in agents:
        metrics = agent_repo.get_metrics(agent.agent_id)
        agent_statuses.append({
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "display_name": agent.display_name,
            "status": agent.status,
            "metrics": {
                "total_executions": metrics.total_executions if metrics else 0,
                "success_rate": metrics.success_rate() if metrics else 0,
                "llm_usage_rate": metrics.llm_usage_rate() if metrics else 0
            }
        })

    return {"agents": agent_statuses}


# === Statistics ===

@app.get("/api/v1/statistics/operations")
def get_operation_statistics():
    """Get operation statistics"""
    stats = operation_repo.get_operation_statistics()
    return stats


@app.get("/api/v1/statistics/kpis")
def get_kpi_statistics():
    """Get KPI statistics"""
    # Count total KPIs
    total_kpis = kpi_repo.count("kpi_measurements")

    # Count active alerts
    active_alerts = len(kpi_repo.list_active_alerts())

    return {
        "total_kpi_measurements": total_kpis,
        "active_alerts": active_alerts
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
