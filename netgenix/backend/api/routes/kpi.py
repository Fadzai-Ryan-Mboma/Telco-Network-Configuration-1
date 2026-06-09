"""
KPI API endpoints — served from TimescaleDB (kpi_cell / kpi_network).

Legacy endpoints (/kpi/{site}, /kpi/{site}/history, /kpi/thresholds) are
kept intact for backward compatibility with the existing frontend.

New endpoints:
  GET /kpi/v2/{enodeb_name}              — latest 30 KPIs per cell
  GET /kpi/v2/{enodeb_name}/summary      — averaged across all cells & window
  GET /kpi/v2/{enodeb_name}/history      — daily time-series for one KPI
  GET /kpi/v2/{enodeb_name}/cells        — list of cells
  GET /kpi/network/latest                — whole-network KPI snapshot
  GET /kpi/network/history               — daily network KPI time-series
  GET /kpi/meta/columns                  — list of all valid KPI column names
  GET /kpi/meta/stats                    — ingestion audit stats
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# ── legacy helpers (SQLite) ───────────────────────────────────────────────────
from backend.models.schemas import (
    KPIHistory, KPIHistoryPoint, KPIThresholds, KPIValues,
)
from backend.netgenix.services.database import (
    get_kpi_history,
    get_kpi_threshold,
    get_site_info,
    get_site_kpis,
)

# ── TimescaleDB helpers ───────────────────────────────────────────────────────
from backend.netgenix.services.db_timescale import (
    KPI_COLUMNS,
    NETWORK_KPI_COLUMNS,
    get_cell_kpi_history,
    get_enodeb_summary,
    get_ingestion_stats,
    get_latest_cell_kpis,
    get_latest_network_kpis,
    get_network_kpi_history,
    is_timescale_available,
    list_cells,
    list_enodebs,
)

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
# Legacy endpoints (unchanged)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/thresholds", response_model=KPIThresholds)
async def get_thresholds():
    return KPIThresholds(
        network_access_success=get_kpi_threshold("network_access_success"),
        download_speed=get_kpi_threshold("download_speed"),
        upload_speed=get_kpi_threshold("upload_speed"),
        download_quality=get_kpi_threshold("download_quality"),
        upload_quality=get_kpi_threshold("upload_quality"),
        control_channel_load=get_kpi_threshold("control_channel_load"),
        feedback_channel_load=get_kpi_threshold("feedback_channel_load"),
    )


@router.get("/{site_name}/history", response_model=KPIHistory)
async def get_kpi_history_api(
    site_name: str,
    kpi_name: str = Query(...),
    days: int = Query(7, ge=1, le=180),
):
    valid_kpis = [
        "network_access_success", "download_speed", "download_quality",
        "upload_speed", "upload_quality", "control_channel_load", "feedback_channel_load",
    ]
    if kpi_name not in valid_kpis:
        raise HTTPException(400, detail=f"Invalid KPI. Choose from: {', '.join(valid_kpis)}")
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(404, detail=f"Site '{site_name}' not found")
    history = get_kpi_history(site_name, kpi_name, days)
    threshold = get_kpi_threshold(kpi_name)
    data = [KPIHistoryPoint(date=str(d), value=v) for d, v in history]
    return KPIHistory(site_name=site_name, kpi_name=kpi_name, days=days, data=data, threshold=threshold)


@router.get("/{site_name}", response_model=KPIValues)
async def get_current_kpis(site_name: str):
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(404, detail=f"Site '{site_name}' not found")
    kpis = get_site_kpis(site_name)
    if not kpis:
        raise HTTPException(404, detail=f"No KPI data for site '{site_name}'")
    return KPIValues(
        site_name=site_name,
        network_access_success=kpis.get("network_access_success"),
        download_speed=kpis.get("download_speed"),
        download_quality=kpis.get("download_quality"),
        upload_speed=kpis.get("upload_speed"),
        upload_quality=kpis.get("upload_quality"),
        control_channel_load=kpis.get("control_channel_load"),
        feedback_channel_load=kpis.get("feedback_channel_load"),
        timestamp=kpis.get("timestamp"),
    )


# ═════════════════════════════════════════════════════════════════════════════
# Metadata helpers
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/meta/columns")
async def list_kpi_columns():
    """List all valid KPI column names for cell and network tables."""
    return {"cell_kpis": KPI_COLUMNS, "network_kpis": NETWORK_KPI_COLUMNS}


@router.get("/meta/stats")
async def get_db_stats():
    """TimescaleDB ingestion audit stats."""
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    return get_ingestion_stats()


@router.get("/meta/enodebs")
async def get_enodebs():
    """List all eNodeBs in TimescaleDB."""
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    return {"enodebs": list_enodebs()}


# ═════════════════════════════════════════════════════════════════════════════
# v2 — Cell-level endpoints (TimescaleDB)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/v2/{enodeb_name}/cells")
async def get_cells(enodeb_name: str):
    """List all cells for an eNodeB."""
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    cells = list_cells(enodeb_name)
    if not cells:
        raise HTTPException(404, detail=f"eNodeB '{enodeb_name}' not found")
    return {"enodeb_name": enodeb_name, "cells": cells}


@router.get("/v2/{enodeb_name}/summary")
async def get_enodeb_kpi_summary(
    enodeb_name: str,
    days: int = Query(7, ge=1, le=180, description="Rolling window in days"),
):
    """
    Average of all 30 KPIs across all cells for the rolling window.
    Useful for site-level health cards on the dashboard.
    """
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    summary = get_enodeb_summary(enodeb_name, days)
    if not summary:
        raise HTTPException(404, detail=f"No data for eNodeB '{enodeb_name}'")
    return {"enodeb_name": enodeb_name, "window_days": days, "kpis": summary}


@router.get("/v2/{enodeb_name}/history")
async def get_enodeb_kpi_history(
    enodeb_name: str,
    kpi: str = Query(..., description=f"KPI column name. Valid: {', '.join(KPI_COLUMNS)}"),
    days: int = Query(30, ge=1, le=365),
    granularity: Optional[str] = Query(None, description="'daily' or 'hourly'"),
):
    """
    Daily time-series for one KPI, averaged across all cells of an eNodeB.
    """
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    if kpi not in KPI_COLUMNS:
        raise HTTPException(400, detail=f"Unknown KPI '{kpi}'. Valid: {', '.join(KPI_COLUMNS)}")
    data = get_cell_kpi_history(enodeb_name, kpi, days, granularity)
    return {"enodeb_name": enodeb_name, "kpi": kpi, "days": days, "data": data}


@router.get("/v2/{enodeb_name}")
async def get_enodeb_latest_kpis(enodeb_name: str):
    """
    Most-recent row per cell for an eNodeB — all 30 KPIs.
    """
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    rows = get_latest_cell_kpis(enodeb_name)
    if not rows:
        raise HTTPException(404, detail=f"No data for eNodeB '{enodeb_name}'")
    return {
        "enodeb_name": enodeb_name,
        "cell_count": len(rows),
        "cells": rows,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Network-level endpoints (TimescaleDB)
# ═════════════════════════════════════════════════════════════════════════════

@router.get("/network/latest")
async def get_network_latest():
    """Most-recent whole-network KPI snapshot."""
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    row = get_latest_network_kpis()
    if not row:
        raise HTTPException(404, detail="No network-level KPI data found")
    return row


@router.get("/network/history")
async def get_network_kpi_history_api(
    kpi: str = Query(..., description=f"KPI column. Valid: {', '.join(NETWORK_KPI_COLUMNS)}"),
    days: int = Query(30, ge=1, le=365),
):
    """Daily time-series for one KPI at whole-network level."""
    if not is_timescale_available():
        raise HTTPException(503, detail="TimescaleDB not available")
    if kpi not in NETWORK_KPI_COLUMNS:
        raise HTTPException(400, detail=f"Unknown KPI '{kpi}'")
    data = get_network_kpi_history(kpi, days)
    return {"kpi": kpi, "days": days, "data": data}
