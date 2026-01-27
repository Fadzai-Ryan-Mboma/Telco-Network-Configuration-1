"""
Activity Log API endpoints
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.models.schemas import ActivityRecord, ActivityList

# Import existing database helpers
from ui.database_helper import get_recent_activity

router = APIRouter()


@router.get("", response_model=ActivityList)
async def get_activity(
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    site_name: Optional[str] = Query(None, description="Filter by site name")
):
    """
    Get recent optimization activity log.
    """
    # Get all recent activity
    activities = get_recent_activity(limit=limit * 2)  # Get extra to filter

    # Filter by site if specified
    if site_name:
        activities = [a for a in activities if a.get("site_name") == site_name]

    # Limit results
    activities = activities[:limit]

    # Convert to response format
    records = [
        ActivityRecord(
            site_name=a.get("site_name", ""),
            timestamp=a.get("timestamp", ""),
            action_type=a.get("action_type", ""),
            description=a.get("description", ""),
            changes=a.get("changes"),
            result=a.get("result"),
            status=a.get("status", "info")
        )
        for a in activities
    ]

    return ActivityList(
        activities=records,
        total=len(records)
    )


@router.get("/{site_name}", response_model=ActivityList)
async def get_site_activity(
    site_name: str,
    limit: int = Query(10, ge=1, le=100, description="Number of records to return")
):
    """
    Get activity log for a specific site.
    """
    # Get all recent activity
    activities = get_recent_activity(limit=limit * 3)  # Get extra to filter

    # Filter by site
    activities = [a for a in activities if a.get("site_name") == site_name]

    # Limit results
    activities = activities[:limit]

    # Convert to response format
    records = [
        ActivityRecord(
            site_name=a.get("site_name", ""),
            timestamp=a.get("timestamp", ""),
            action_type=a.get("action_type", ""),
            description=a.get("description", ""),
            changes=a.get("changes"),
            result=a.get("result"),
            status=a.get("status", "info")
        )
        for a in activities
    ]

    return ActivityList(
        activities=records,
        total=len(records)
    )
