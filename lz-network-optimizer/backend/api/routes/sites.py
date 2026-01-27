"""
Sites API endpoints
"""

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
from ui.database_helper import (
    get_all_sites,
    get_site_info,
    get_site_parameters,
    get_live_parameters,
    check_api_status
)

router = APIRouter()


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
async def get_site_params(site_name: str, live: bool = True):
    """
    Get current parameter values for a site.

    Query params:
        live: If true, fetch from Huawei API; otherwise use database
    """
    # First check if site exists
    site_info = get_site_info(site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")

    # Parameter units mapping
    units = {
        "reference_signal_power_pdschcfg": "dBm",
        "a3_event_offset": "dB",
        "t310_timer": "ms",
        "p0_nominal_pusch": "dBm",
        "pdcch_aggregation_level": ""
    }

    if live:
        # Try live API first
        live_params = get_live_parameters(site_name)

        if live_params:
            errors = live_params.get("errors", [])
            site_offline = live_params.get("site_offline", False)

            # Build parameters dict
            params = {}
            for key in ["reference_signal_power_pdschcfg", "a3_event_offset",
                       "t310_timer", "p0_nominal_pusch", "pdcch_aggregation_level"]:
                value = live_params.get(key)
                params[key] = ParameterValue(
                    value=value,
                    unit=units.get(key, ""),
                    source="live_api" if value is not None and not errors else "database"
                )

            # If we have errors or site is offline, fall back to database for missing values
            if errors or site_offline:
                db_params = get_site_parameters(site_name)
                for key in params:
                    if params[key].value is None and db_params:
                        params[key] = ParameterValue(
                            value=db_params.get(key),
                            unit=units.get(key, ""),
                            source="database"
                        )

            return SiteParameters(
                site_name=site_name,
                parameters=params,
                status="success" if not errors else "fallback",
                site_offline=site_offline,
                last_updated=live_params.get("last_modified"),
                errors=errors
            )

    # Fall back to database
    db_params = get_site_parameters(site_name)

    if not db_params:
        raise HTTPException(status_code=404, detail=f"No parameters found for site '{site_name}'")

    params = {}
    for key in ["reference_signal_power_pdschcfg", "a3_event_offset",
               "t310_timer", "p0_nominal_pusch", "pdcch_aggregation_level"]:
        params[key] = ParameterValue(
            value=db_params.get(key),
            unit=units.get(key, ""),
            source="database"
        )

    return SiteParameters(
        site_name=site_name,
        parameters=params,
        status="fallback",
        site_offline=False,
        last_updated=db_params.get("last_modified"),
        errors=[]
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
