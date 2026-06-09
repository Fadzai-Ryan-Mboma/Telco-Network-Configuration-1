"""
System Status API endpoints
"""

import sys
from pathlib import Path
from fastapi import APIRouter

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.models.schemas import SystemStatus, DatabaseStats

# Import existing database helpers
from backend.netgenix.services.database import check_api_status, get_database_stats

router = APIRouter()


@router.get("", response_model=SystemStatus)
async def get_system_status():
    """
    Get overall system health status.

    Checks connectivity to:
    - Huawei iMaster MAE API
    - Network Elements (NEs)
    - Database
    """
    status = check_api_status()

    return SystemStatus(
        api_connected="Connected" in status.get("api", ""),
        ne_connected="Connected" in status.get("ne", ""),
        db_connected="Connected" in status.get("db", ""),
        api_status=status.get("api", "Unknown"),
        ne_status=status.get("ne", "Unknown"),
        db_status=status.get("db", "Unknown")
    )


@router.get("/database", response_model=DatabaseStats)
async def get_db_stats():
    """
    Get database statistics.
    """
    stats = get_database_stats()

    return DatabaseStats(
        total_sites=stats.get("total_sites", 0),
        total_records=stats.get("total_records", 0),
        latest_update=stats.get("latest_update")
    )
