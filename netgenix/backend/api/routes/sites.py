"""
Sites API endpoints
"""

import logging
import sys
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.models.schemas import (
    SiteBasic, SiteInfo, SiteStatus, SiteParameters, ParameterValue
)

# Import existing database helpers
from backend.netgenix.services.database import (
    get_all_sites,
    get_site_info,
    get_site_parameters,
    check_api_status
)
from backend.netgenix.services.huawei_parameter_snapshots import (
    get_top_15_parameters_from_db,
    get_top_15_parameters_live,
)
from backend.netgenix.services.parameter_catalog import TOP_15_PARAMETERS

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_catalog_parameters(site_name: str):
    try:
        return get_top_15_parameters_from_db(site_name)
    except Exception as exc:
        logger.warning("Parameter snapshot fallback for %s: %s", site_name, exc)
        return {
            parameter.key: {
                "value": None,
                "unit": parameter.unit,
                "source": "unavailable",
                "label": parameter.label,
                "category": parameter.category,
                "priority": parameter.priority,
                "description": parameter.description,
            }
            for parameter in TOP_15_PARAMETERS
        }


@router.get("", response_model=List[SiteBasic])
async def list_sites():
    """
    Get list of all available sites.
    """
    sites = get_all_sites()
    return [SiteBasic(site_name=site["site_name"]) for site in sites]


@router.get("/{site_name}", response_model=SiteInfo)
async def get_site(site_name: str):
    """
    Get detailed information for a specific site.
    """
    site_info = get_site_info(site_name)

    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")

    return SiteInfo(
        site_name=site_info["site_name"],
        location=site_info["location"],
        cell_count=site_info["cell_count"],
        cell_id=site_info["cell_id"],
        status=site_info["status"],
        last_updated=site_info.get("last_updated")
    )


@router.get("/{site_name}/params", response_model=SiteParameters)
async def get_site_params(site_name: str, live: bool = False):
    """
    Get current parameter values for a site.

    Query params:
        live: If true, fetch from Huawei API; otherwise use database
    """
    # First check if site exists
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")

    live_errors: list[str] = []
    if live:
        params, errors = get_top_15_parameters_live(site_name)
        live_errors = errors
        if params:
            fallback_params = _get_catalog_parameters(site_name) if errors else {}
            for key, parameter in params.items():
                if parameter.get("value") is None and key in fallback_params:
                    params[key] = fallback_params[key]

            return SiteParameters(
                site_name=site_name,
                parameters={key: ParameterValue(**value) for key, value in params.items()},
                status="success" if not errors else "fallback",
                site_offline=False,
                last_updated=None,
                errors=errors
            )

    # Fall back to database
    params = _get_catalog_parameters(site_name)
    if not params:
        raise HTTPException(status_code=404, detail=f"No parameters found for site '{site_name}'")

    has_values = any(parameter.get("value") is not None for parameter in params.values())
    return SiteParameters(
        site_name=site_name,
        parameters={key: ParameterValue(**value) for key, value in params.items()},
        status="fallback" if has_values else "error",
        site_offline=not has_values,
        last_updated=None,
        errors=live_errors or ([] if has_values else ["No real parameter snapshot is available for this site."])
    )


@router.get("/{site_name}/status", response_model=SiteStatus)
async def get_site_status(site_name: str):
    """
    Get connectivity status for a site.
    """
    status = check_api_status(site_name)

    return SiteStatus(
        api_connected="Connected" in status.get("api", ""),
        ne_connected="Connected" in status.get("ne", ""),
        db_connected="Connected" in status.get("db", ""),
        api_status=status.get("api", "Unknown"),
        ne_status=status.get("ne", "Unknown"),
        db_status=status.get("db", "Unknown")
    )
