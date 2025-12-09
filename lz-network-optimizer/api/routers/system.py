"""
System Router - Health checks and system status endpoints
"""

import sys
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, HTTPException

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.database_helper import (
    check_api_status,
    get_database_stats,
    get_recent_activity
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns 200 if the API is running.
    Used by Docker health checks and load balancers.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "lz-network-optimizer-api"
    }


@router.get("/status")
async def system_status():
    """
    Get detailed system status including all components.
    
    Checks connectivity to:
    - NVIDIA API (LLM endpoints)
    - Huawei iMaster MAE API
    - SQLite Database
    """
    try:
        # Get component status
        api_status = check_api_status()
        db_stats = get_database_stats()
        
        # Parse status into structured format
        components = {}
        overall_healthy = True
        
        for component, status_text in api_status.items():
            is_healthy = "✅" in status_text or "Online" in status_text
            components[component] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "message": status_text
            }
            if not is_healthy:
                overall_healthy = False
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": components,
            "database": {
                "site_count": db_stats.get("site_count", 0),
                "record_count": db_stats.get("record_count", 0),
                "latest_update": db_stats.get("latest_update")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_activity(limit: int = 10):
    """
    Get recent optimization activity log.
    
    - **limit**: Maximum number of activities to return (default: 10)
    """
    try:
        activities = get_recent_activity(limit=limit)
        
        return {
            "status": "success",
            "count": len(activities) if activities else 0,
            "activities": activities or []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def api_info():
    """
    Get API information and available endpoints.
    """
    return {
        "name": "LZ Network Optimizer API",
        "version": "1.0.0",
        "description": "REST API for Liquid Zimbabwe 4G Network Optimization",
        "endpoints": {
            "sites": {
                "GET /api/sites": "List all sites",
                "GET /api/sites/{site_name}": "Get site details",
                "GET /api/sites/{site_name}/parameters/database": "Get database parameters"
            },
            "parameters": {
                "GET /api/params/{site_name}": "Get LIVE parameters from Huawei API",
                "GET /api/params/{site_name}/simple": "Get parameters in simple format"
            },
            "kpis": {
                "GET /api/kpis/{site_name}": "Get current KPIs",
                "GET /api/kpis/{site_name}/history/{kpi_name}": "Get KPI history",
                "GET /api/kpis/{site_name}/summary": "Get KPI health summary"
            },
            "system": {
                "GET /api/health": "Health check",
                "GET /api/status": "Detailed system status",
                "GET /api/activity": "Recent activity log",
                "GET /api/info": "This endpoint"
            }
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }
