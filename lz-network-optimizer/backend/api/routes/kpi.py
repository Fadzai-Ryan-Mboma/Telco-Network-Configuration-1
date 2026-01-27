"""
KPI API endpoints
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.models.schemas import (
    KPIValues, KPIHistory, KPIHistoryPoint, KPIThresholds
)

# Import existing database helpers
from ui.database_helper import (
    get_site_info,
    get_site_kpis,
    get_kpi_history,
    get_kpi_threshold
)

router = APIRouter()


@router.get("/{site_name}", response_model=KPIValues)
async def get_current_kpis(site_name: str):
    """
    Get current KPI values for a site.
    """
    # Verify site exists
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")

    kpis = get_site_kpis(site_name)

    if not kpis:
        raise HTTPException(status_code=404, detail=f"No KPI data found for site '{site_name}'")

    return KPIValues(
        site_name=site_name,
        network_access_success=kpis.get("network_access_success"),
        download_speed=kpis.get("download_speed"),
        download_quality=kpis.get("download_quality"),
        upload_speed=kpis.get("upload_speed"),
        upload_quality=kpis.get("upload_quality"),
        control_channel_load=kpis.get("control_channel_load"),
        feedback_channel_load=kpis.get("feedback_channel_load"),
        timestamp=kpis.get("timestamp")
    )


@router.get("/{site_name}/history", response_model=KPIHistory)
async def get_kpi_history_api(
    site_name: str,
    kpi_name: str = Query(..., description="KPI name (e.g., network_access_success)"),
    days: int = Query(7, ge=1, le=180, description="Number of days of history")
):
    """
    Get historical KPI data for charting.

    Supported KPI names:
    - network_access_success
    - download_speed
    - download_quality
    - upload_speed
    - upload_quality
    - control_channel_load
    - feedback_channel_load
    """
    # Validate KPI name
    valid_kpis = [
        "network_access_success", "download_speed", "download_quality",
        "upload_speed", "upload_quality", "control_channel_load", "feedback_channel_load"
    ]

    if kpi_name not in valid_kpis:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid KPI name. Must be one of: {', '.join(valid_kpis)}"
        )

    # Verify site exists
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")

    # Get history
    history = get_kpi_history(site_name, kpi_name, days)

    # Get threshold
    threshold = get_kpi_threshold(kpi_name)

    # Convert to response format
    data = [
        KPIHistoryPoint(date=str(date), value=value)
        for date, value in history
    ]

    return KPIHistory(
        site_name=site_name,
        kpi_name=kpi_name,
        days=days,
        data=data,
        threshold=threshold
    )


@router.get("/thresholds", response_model=KPIThresholds)
async def get_thresholds():
    """
    Get operating average thresholds for all KPIs.
    """
    return KPIThresholds(
        network_access_success=get_kpi_threshold("network_access_success"),
        download_speed=get_kpi_threshold("download_speed"),
        upload_speed=get_kpi_threshold("upload_speed"),
        download_quality=get_kpi_threshold("download_quality"),
        upload_quality=get_kpi_threshold("upload_quality"),
        control_channel_load=get_kpi_threshold("control_channel_load"),
        feedback_channel_load=get_kpi_threshold("feedback_channel_load")
    )
