"""
Sites Router - Endpoints for network site operations
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.database_helper import (
    get_all_sites,
    get_site_info,
    get_site_parameters
)

router = APIRouter()


@router.get("")
async def list_sites():
    """
    Get all network sites.
    
    Returns a list of all sites with basic information.
    """
    try:
        sites = get_all_sites()
        return {
            "status": "success",
            "count": len(sites) if sites else 0,
            "sites": sites or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_name}")
async def get_site(site_name: str):
    """
    Get detailed information for a specific site.
    
    - **site_name**: Name of the site (e.g., MSH-0014-Chipadze)
    """
    try:
        site_info = get_site_info(site_name)
        if not site_info:
            raise HTTPException(status_code=404, detail=f"Site '{site_name}' not found")
        
        return {
            "status": "success",
            "site": site_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_name}/parameters/database")
async def get_site_params_db(site_name: str):
    """
    Get parameter values from the database for a site.
    
    Returns the stored/default parameter values, not live values.
    Use /api/params/{site_name} for live values from Huawei API.
    """
    try:
        params = get_site_parameters(site_name)
        if not params:
            raise HTTPException(status_code=404, detail=f"No parameters found for site '{site_name}'")
        
        return {
            "status": "success",
            "source": "database",
            "site_name": site_name,
            "parameters": params
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
