"""
LangChain tools for Huawei iMaster MAE API operations.

These tools provide a standardized interface for agents to interact
with the Huawei network management system.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from cassava_optimizer.domain.exceptions import HuaweiAPIError
from cassava_optimizer.infrastructure.huawei_client import HuaweiMAEClient

logger = structlog.get_logger(__name__)

# Module-level client reference (set during initialization)
_huawei_client: Optional[HuaweiMAEClient] = None


def set_huawei_client(client: HuaweiMAEClient) -> None:
    """Set the Huawei client for tools to use."""
    global _huawei_client
    _huawei_client = client
    logger.info("Huawei client set for tools")


def get_client() -> HuaweiMAEClient:
    """Get the configured Huawei client."""
    if _huawei_client is None:
        raise HuaweiAPIError("Huawei client not initialized. Call set_huawei_client first.")
    return _huawei_client


# Pydantic models for tool inputs
class SiteKPIsInput(BaseModel):
    """Input for get_site_kpis tool."""
    
    site_name: str = Field(description="Name of the site to get KPIs for")
    kpi_names: Optional[list[str]] = Field(
        default=None,
        description="Optional list of specific KPI names to retrieve"
    )
    start_time: Optional[str] = Field(
        default=None,
        description="Start time for KPI data in ISO format"
    )
    end_time: Optional[str] = Field(
        default=None,
        description="End time for KPI data in ISO format"
    )


class CellConfigInput(BaseModel):
    """Input for get_cell_configuration tool."""
    
    site_name: str = Field(description="Name of the site")
    cell_id: Optional[str] = Field(
        default=None,
        description="Specific cell ID, or None for all cells"
    )
    parameter_names: Optional[list[str]] = Field(
        default=None,
        description="Optional list of specific parameters to retrieve"
    )


class MMLCommandInput(BaseModel):
    """Input for execute_mml_command tool."""
    
    command: str = Field(description="MML command to execute")
    target_ne: str = Field(description="Target network element ID")
    dry_run: bool = Field(
        default=True,
        description="If True, validate command without executing"
    )


class AlarmListInput(BaseModel):
    """Input for get_alarm_list tool."""
    
    site_name: Optional[str] = Field(
        default=None,
        description="Site name to filter alarms"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Filter by severity: critical, major, minor, warning"
    )
    active_only: bool = Field(
        default=True,
        description="Only return active alarms"
    )


class SiteListInput(BaseModel):
    """Input for get_site_list tool."""
    
    region: Optional[str] = Field(
        default=None,
        description="Filter by region name"
    )
    technology: Optional[str] = Field(
        default="LTE",
        description="Filter by technology type"
    )


@tool(args_schema=SiteKPIsInput)
async def get_site_kpis(
    site_name: str,
    kpi_names: Optional[list[str]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retrieve KPI data for a specific site from Huawei iMaster MAE.
    
    Returns current and historical KPI values including:
    - RRC Setup Success Rate
    - E-RAB Setup Success Rate  
    - Handover Success Rate
    - PRB Utilization
    - CQI Distribution
    - Traffic Volume
    - RSRP/RSRQ/SINR measurements
    
    Args:
        site_name: Name of the site to get KPIs for
        kpi_names: Optional list of specific KPI names
        start_time: Start time for historical data
        end_time: End time for historical data
        
    Returns:
        Dictionary containing KPI values and metadata
    """
    logger.info(
        "Getting site KPIs",
        site_name=site_name,
        kpi_names=kpi_names,
    )
    
    client = get_client()
    
    # Parse time range
    if end_time:
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    else:
        end_dt = datetime.utcnow()
    
    if start_time:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    else:
        start_dt = end_dt - timedelta(hours=1)
    
    try:
        # Get KPI data from Huawei API
        kpi_data = await client.get_kpis(
            site_name=site_name,
            start_time=start_dt,
            end_time=end_dt,
        )
        
        # Filter KPIs if specific names requested
        if kpi_names and kpi_data.get("kpis"):
            kpi_data["kpis"] = {
                k: v for k, v in kpi_data["kpis"].items()
                if k in kpi_names
            }
        
        logger.info(
            "Retrieved site KPIs",
            site_name=site_name,
            kpi_count=len(kpi_data.get("kpis", {})),
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "timestamp": datetime.utcnow().isoformat(),
            "time_range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
            "data": kpi_data,
        }
        
    except HuaweiAPIError as e:
        logger.error(
            "Failed to get site KPIs",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=CellConfigInput)
async def get_cell_configuration(
    site_name: str,
    cell_id: Optional[str] = None,
    parameter_names: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Retrieve cell configuration parameters from Huawei iMaster MAE.
    
    Returns parameters including:
    - Transmit Power settings
    - Antenna tilt values
    - Frequency/EARFCN configuration
    - PCI settings
    - TAC configuration
    - Neighbor lists
    - Handover parameters
    
    Args:
        site_name: Name of the site
        cell_id: Specific cell ID or None for all cells
        parameter_names: Optional list of specific parameters
        
    Returns:
        Dictionary containing cell configuration data
    """
    logger.info(
        "Getting cell configuration",
        site_name=site_name,
        cell_id=cell_id,
    )
    
    client = get_client()
    
    try:
        config_data = await client.get_cell_config(
            site_name=site_name,
            cell_id=cell_id,
        )
        
        # Filter parameters if specific names requested
        if parameter_names and config_data.get("cells"):
            for cell in config_data["cells"]:
                if "parameters" in cell:
                    cell["parameters"] = {
                        k: v for k, v in cell["parameters"].items()
                        if k in parameter_names
                    }
        
        logger.info(
            "Retrieved cell configuration",
            site_name=site_name,
            cell_count=len(config_data.get("cells", [])),
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": config_data,
        }
        
    except HuaweiAPIError as e:
        logger.error(
            "Failed to get cell configuration",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=MMLCommandInput)
async def execute_mml_command(
    command: str,
    target_ne: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Execute an MML command on the Huawei network element.
    
    WARNING: This tool can modify network configuration.
    Use dry_run=True to validate commands before execution.
    
    Common MML commands:
    - MOD CELLALGOSWITCH: Modify algorithm switches
    - MOD CELLPDSCHCFG: Modify PDSCH configuration
    - MOD CELLPUSCHCFG: Modify PUSCH configuration
    - MOD ENODEBALGOPARA: Modify algorithm parameters
    - DSP CELL: Display cell information
    
    Args:
        command: MML command to execute
        target_ne: Target network element ID
        dry_run: If True, validate without executing
        
    Returns:
        Dictionary containing execution result
    """
    logger.info(
        "Executing MML command",
        command=command[:100],
        target_ne=target_ne,
        dry_run=dry_run,
    )
    
    client = get_client()
    
    try:
        if dry_run:
            # Validate command syntax
            result = await client.validate_command(command=command)
            return {
                "success": True,
                "mode": "dry_run",
                "command": command,
                "target_ne": target_ne,
                "validation": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            # Execute command
            result = await client.execute_command(
                command=command,
                ne_id=target_ne,
            )
            
            logger.info(
                "MML command executed",
                command=command[:100],
                target_ne=target_ne,
                success=result.get("success", False),
            )
            
            return {
                "success": result.get("success", False),
                "mode": "execute",
                "command": command,
                "target_ne": target_ne,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
    except HuaweiAPIError as e:
        logger.error(
            "MML command failed",
            command=command[:100],
            error=str(e),
        )
        return {
            "success": False,
            "command": command,
            "target_ne": target_ne,
            "error": str(e),
        }


@tool(args_schema=AlarmListInput)
async def get_alarm_list(
    site_name: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
) -> dict[str, Any]:
    """
    Retrieve active alarms from Huawei iMaster MAE.
    
    Alarm severity levels:
    - critical: Service affecting, immediate action required
    - major: Significant degradation, urgent attention needed
    - minor: Potential issue, scheduled attention
    - warning: Informational, monitoring recommended
    
    Args:
        site_name: Optional site name to filter alarms
        severity: Optional severity filter
        active_only: Only return active alarms
        
    Returns:
        Dictionary containing alarm list
    """
    logger.info(
        "Getting alarm list",
        site_name=site_name,
        severity=severity,
    )
    
    client = get_client()
    
    try:
        alarms = await client.get_alarms(
            site_name=site_name,
            severity=severity,
            active_only=active_only,
        )
        
        logger.info(
            "Retrieved alarms",
            alarm_count=len(alarms.get("alarms", [])),
        )
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "site_name": site_name,
                "severity": severity,
                "active_only": active_only,
            },
            "data": alarms,
        }
        
    except HuaweiAPIError as e:
        logger.error(
            "Failed to get alarms",
            error=str(e),
        )
        return {
            "success": False,
            "error": str(e),
        }


@tool(args_schema=SiteListInput)
async def get_site_list(
    region: Optional[str] = None,
    technology: Optional[str] = "LTE",
) -> dict[str, Any]:
    """
    Retrieve list of sites from Huawei iMaster MAE.
    
    Returns site information including:
    - Site name and ID
    - Location (latitude, longitude)
    - Technology type
    - Cell count
    - Status
    
    Args:
        region: Optional region filter
        technology: Technology type filter (default: LTE)
        
    Returns:
        Dictionary containing site list
    """
    logger.info(
        "Getting site list",
        region=region,
        technology=technology,
    )
    
    client = get_client()
    
    try:
        sites = await client.get_sites(
            region=region,
            technology=technology,
        )
        
        logger.info(
            "Retrieved sites",
            site_count=len(sites.get("sites", [])),
        )
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "filters": {
                "region": region,
                "technology": technology,
            },
            "data": sites,
        }
        
    except HuaweiAPIError as e:
        logger.error(
            "Failed to get site list",
            error=str(e),
        )
        return {
            "success": False,
            "error": str(e),
        }
