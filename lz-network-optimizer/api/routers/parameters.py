"""
Parameters Router - Endpoints for live parameter fetching from Huawei API
"""

import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.database_helper import (
    get_live_parameters,
    get_site_parameters
)

router = APIRouter()


@router.get("/{site_name}")
async def get_live_params(site_name: str, fallback: bool = True):
    """
    Get LIVE parameter values from Huawei iMaster MAE API.
    
    This endpoint queries the actual network equipment for current values.
    
    - **site_name**: Name of the site (e.g., MSH-0014-Chipadze)
    - **fallback**: If True, falls back to database values when API fails (default: True)
    
    Returns the 5 key optimization parameters:
    - reference_signal_power_pdschcfg (dBm)
    - a3_event_offset (dB)
    - t310_timer (ms)
    - p0_nominal_pusch (dBm)
    - pdcch_aggregation_level
    """
    try:
        # Try live fetch from Huawei API
        params = get_live_parameters(site_name)
        
        # Check if we got actual values (not all None)
        param_keys = ["reference_signal_power_pdschcfg", "a3_event_offset", "t310_timer", 
                      "p0_nominal_pusch", "pdcch_aggregation_level"]
        has_valid_values = params and any(params.get(k) is not None for k in param_keys)
        
        if has_valid_values:
            return {
                "status": "success",
                "source": "huawei_api",
                "site_name": site_name,
                "parameters": {
                    "reference_signal_power_pdschcfg": {
                        "value": params.get("reference_signal_power_pdschcfg"),
                        "unit": "dBm",
                        "description": "Reference Signal Power (PDSCH)"
                    },
                    "a3_event_offset": {
                        "value": params.get("a3_event_offset"),
                        "unit": "dB",
                        "description": "A3 Event Offset for handover"
                    },
                    "t310_timer": {
                        "value": params.get("t310_timer"),
                        "unit": "ms",
                        "description": "T310 Timer (RLF detection)"
                    },
                    "p0_nominal_pusch": {
                        "value": params.get("p0_nominal_pusch"),
                        "unit": "dBm",
                        "description": "P0 Nominal PUSCH (uplink power)"
                    },
                    "pdcch_aggregation_level": {
                        "value": params.get("pdcch_aggregation_level"),
                        "unit": "",
                        "description": "PDCCH Aggregation Level"
                    }
                }
            }
        
        # Determine fallback reason
        site_offline = params.get("site_offline", False) if params else False
        
        # Fallback to database if requested (or if API returned no valid values)
        if fallback:
            db_params = get_site_parameters(site_name)
            if db_params:
                # Use specific message based on reason
                if site_offline:
                    fallback_message = "Site is unavailable"
                else:
                    fallback_message = "Huawei API unavailable, using database values"
                
                return {
                    "status": "fallback",
                    "source": "database",
                    "site_offline": site_offline,
                    "message": fallback_message,
                    "site_name": site_name,
                    "parameters": {
                        "reference_signal_power_pdschcfg": {
                            "value": db_params.get("reference_signal_power_pdschcfg"),
                            "unit": "dBm",
                            "description": "Reference Signal Power (PDSCH)"
                        },
                        "a3_event_offset": {
                            "value": db_params.get("a3_event_offset"),
                            "unit": "dB",
                            "description": "A3 Event Offset for handover"
                        },
                        "t310_timer": {
                            "value": db_params.get("t310_timer"),
                            "unit": "ms",
                            "description": "T310 Timer (RLF detection)"
                        },
                        "p0_nominal_pusch": {
                            "value": db_params.get("p0_nominal_pusch"),
                            "unit": "dBm",
                            "description": "P0 Nominal PUSCH (uplink power)"
                        },
                        "pdcch_aggregation_level": {
                            "value": db_params.get("pdcch_aggregation_level"),
                            "unit": "",
                            "description": "PDCCH Aggregation Level"
                        }
                    }
                }
        
        raise HTTPException(
            status_code=503,
            detail=f"Unable to fetch parameters for site '{site_name}'. Huawei API unavailable."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{site_name}/simple")
async def get_live_params_simple(site_name: str):
    """
    Get LIVE parameter values in a simplified format.
    
    Returns just the parameter name and value pairs, ideal for UI consumption.
    """
    try:
        params = get_live_parameters(site_name)
        
        if params:
            return {
                "status": "success",
                "source": "huawei_api",
                "site_name": site_name,
                "data": params
            }
        
        # Fallback
        db_params = get_site_parameters(site_name)
        if db_params:
            return {
                "status": "fallback",
                "source": "database",
                "site_name": site_name,
                "data": db_params
            }
        
        raise HTTPException(status_code=503, detail="Unable to fetch parameters")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
