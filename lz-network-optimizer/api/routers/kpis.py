"""
KPIs Router - Endpoints for KPI data access
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.database_helper import (
    get_site_kpis,
    get_kpi_history,
    get_kpi_threshold
)

router = APIRouter()


# KPI definitions with units and descriptions
KPI_METADATA = {
    "network_access_success": {
        "unit": "%",
        "description": "Network Access Success Rate",
        "higher_is_better": True
    },
    "download_speed": {
        "unit": "Mbps",
        "description": "Average Download Speed",
        "higher_is_better": True
    },
    "upload_speed": {
        "unit": "Mbps",
        "description": "Average Upload Speed",
        "higher_is_better": True
    },
    "download_quality": {
        "unit": "%",
        "description": "Download Quality Rate",
        "higher_is_better": True
    },
    "upload_quality": {
        "unit": "%",
        "description": "Upload Quality Rate",
        "higher_is_better": True
    },
    "control_channel_load": {
        "unit": "%",
        "description": "Control Channel Load",
        "higher_is_better": False
    },
    "feedback_channel_load": {
        "unit": "%",
        "description": "Feedback Channel Load",
        "higher_is_better": False
    }
}


@router.get("/{site_name}")
async def get_kpis(site_name: str):
    """
    Get current KPI values for a site.
    
    Returns all KPIs with their values, units, thresholds, and status.
    """
    try:
        kpis = get_site_kpis(site_name)
        if not kpis:
            raise HTTPException(status_code=404, detail=f"No KPIs found for site '{site_name}'")
        
        # Enrich with metadata and status
        enriched_kpis = {}
        for kpi_name, value in kpis.items():
            if kpi_name in KPI_METADATA:
                metadata = KPI_METADATA[kpi_name]
                threshold = get_kpi_threshold(kpi_name)
                
                # Determine status based on threshold
                if metadata["higher_is_better"]:
                    status = "healthy" if value >= threshold else "degraded"
                else:
                    status = "healthy" if value <= threshold else "degraded"
                
                enriched_kpis[kpi_name] = {
                    "value": value,
                    "unit": metadata["unit"],
                    "description": metadata["description"],
                    "threshold": threshold,
                    "status": status
                }
            else:
                enriched_kpis[kpi_name] = {"value": value}
        
        return {
            "status": "success",
            "site_name": site_name,
            "kpis": enriched_kpis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_name}/history/{kpi_name}")
async def get_kpi_history_data(
    site_name: str,
    kpi_name: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days of history")
):
    """
    Get historical KPI data for trending and analysis.
    
    - **site_name**: Name of the site
    - **kpi_name**: KPI to retrieve (e.g., download_speed, network_access_success)
    - **days**: Number of days of history (1-90, default: 7)
    """
    try:
        # Validate KPI name
        valid_kpis = list(KPI_METADATA.keys())
        if kpi_name not in valid_kpis:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid KPI name '{kpi_name}'. Valid options: {valid_kpis}"
            )
        
        history = get_kpi_history(site_name, kpi_name, days)
        
        if not history:
            return {
                "status": "success",
                "site_name": site_name,
                "kpi_name": kpi_name,
                "days": days,
                "data_points": 0,
                "history": []
            }
        
        # Format history data
        formatted_history = [
            {"timestamp": h[0], "value": h[1]}
            for h in history
        ]
        
        # Calculate basic stats
        values = [h[1] for h in history]
        stats = {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else None
        }
        
        return {
            "status": "success",
            "site_name": site_name,
            "kpi_name": kpi_name,
            "metadata": KPI_METADATA.get(kpi_name, {}),
            "threshold": get_kpi_threshold(kpi_name),
            "days": days,
            "data_points": len(history),
            "statistics": stats,
            "history": formatted_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_name}/summary")
async def get_kpi_summary(site_name: str):
    """
    Get a summary of KPI health for a site.
    
    Returns overall health status and count of healthy/degraded KPIs.
    """
    try:
        kpis = get_site_kpis(site_name)
        if not kpis:
            raise HTTPException(status_code=404, detail=f"No KPIs found for site '{site_name}'")
        
        healthy_count = 0
        degraded_count = 0
        degraded_kpis = []
        
        for kpi_name, value in kpis.items():
            if kpi_name in KPI_METADATA:
                metadata = KPI_METADATA[kpi_name]
                threshold = get_kpi_threshold(kpi_name)
                
                if metadata["higher_is_better"]:
                    is_healthy = value >= threshold
                else:
                    is_healthy = value <= threshold
                
                if is_healthy:
                    healthy_count += 1
                else:
                    degraded_count += 1
                    degraded_kpis.append({
                        "kpi": kpi_name,
                        "value": value,
                        "threshold": threshold,
                        "description": metadata["description"]
                    })
        
        # Determine overall status
        if degraded_count == 0:
            overall_status = "healthy"
        elif degraded_count <= 2:
            overall_status = "warning"
        else:
            overall_status = "critical"
        
        return {
            "status": "success",
            "site_name": site_name,
            "overall_status": overall_status,
            "healthy_kpis": healthy_count,
            "degraded_kpis": degraded_count,
            "total_kpis": healthy_count + degraded_count,
            "issues": degraded_kpis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
