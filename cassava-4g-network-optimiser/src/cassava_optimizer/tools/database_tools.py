"""
LangChain tools for database operations.

These tools provide agents with access to the local SQLite database
for storing and retrieving network data, KPIs, and recommendations.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from cassava_optimizer.domain.exceptions import DatabaseError
from cassava_optimizer.infrastructure.repository import NetworkRepository

logger = structlog.get_logger(__name__)

# Module-level repository reference (set during initialization)
_repository: Optional[NetworkRepository] = None


def set_repository(repo: NetworkRepository) -> None:
    """Set the repository for tools to use."""
    global _repository
    _repository = repo
    logger.info("Repository set for database tools")


def get_repository() -> NetworkRepository:
    """Get the configured repository."""
    if _repository is None:
        raise DatabaseError("Repository not initialized. Call set_repository first.")
    return _repository


# Pydantic models for tool inputs
class SaveKPIInput(BaseModel):
    """Input for save_kpi_values tool."""
    
    site_name: str = Field(description="Name of the site")
    kpis: dict[str, float] = Field(
        description="Dictionary of KPI names to values"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp in ISO format, defaults to now"
    )


class HistoricalKPIInput(BaseModel):
    """Input for get_historical_kpis tool."""
    
    site_name: str = Field(description="Name of the site")
    kpi_names: Optional[list[str]] = Field(
        default=None,
        description="Specific KPI names to retrieve"
    )
    hours: int = Field(
        default=24,
        description="Number of hours of history to retrieve"
    )


class SaveRecommendationInput(BaseModel):
    """Input for save_recommendation tool."""
    
    site_name: str = Field(description="Name of the site")
    optimization_type: str = Field(
        description="Type of optimization: coverage, capacity, interference, full"
    )
    recommendations: list[dict[str, Any]] = Field(
        description="List of recommendation objects"
    )
    analysis_summary: str = Field(
        description="Summary of the analysis that led to recommendations"
    )


class SiteInfoInput(BaseModel):
    """Input for get_site_info tool."""
    
    site_name: str = Field(description="Name of the site to get info for")


class CommandLogInput(BaseModel):
    """Input for log_command_execution tool."""
    
    site_name: str = Field(description="Name of the site")
    command: str = Field(description="MML command that was executed")
    target_ne: str = Field(description="Target network element")
    success: bool = Field(description="Whether execution succeeded")
    result: Optional[str] = Field(
        default=None,
        description="Result or error message"
    )
    recommendation_id: Optional[str] = Field(
        default=None,
        description="ID of associated recommendation"
    )


@tool(args_schema=SaveKPIInput)
async def save_kpi_values(
    site_name: str,
    kpis: dict[str, float],
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """
    Save KPI values to the local database for historical tracking.
    
    Use this tool after collecting KPI data from the Huawei API
    to maintain a local history for trend analysis.
    
    Args:
        site_name: Name of the site
        kpis: Dictionary of KPI name -> value pairs
        timestamp: Optional ISO timestamp, defaults to now
        
    Returns:
        Confirmation of saved data
    """
    logger.info(
        "Saving KPI values",
        site_name=site_name,
        kpi_count=len(kpis),
    )
    
    repo = get_repository()
    
    # Parse timestamp
    if timestamp:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        ts = datetime.utcnow()
    
    try:
        # Save each KPI value
        saved_count = 0
        for kpi_name, value in kpis.items():
            await repo.save_kpi_value(
                site_name=site_name,
                kpi_name=kpi_name,
                value=value,
                timestamp=ts,
            )
            saved_count += 1
        
        logger.info(
            "Saved KPI values",
            site_name=site_name,
            saved_count=saved_count,
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "saved_count": saved_count,
            "timestamp": ts.isoformat(),
        }
        
    except DatabaseError as e:
        logger.error(
            "Failed to save KPI values",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=HistoricalKPIInput)
async def get_historical_kpis(
    site_name: str,
    kpi_names: Optional[list[str]] = None,
    hours: int = 24,
) -> dict[str, Any]:
    """
    Retrieve historical KPI data from the local database.
    
    Use this tool to analyze KPI trends over time
    and compare current values against historical baselines.
    
    Args:
        site_name: Name of the site
        kpi_names: Specific KPI names to retrieve (None for all)
        hours: Number of hours of history to retrieve
        
    Returns:
        Historical KPI data with timestamps
    """
    logger.info(
        "Getting historical KPIs",
        site_name=site_name,
        hours=hours,
    )
    
    repo = get_repository()
    
    start_time = datetime.utcnow() - timedelta(hours=hours)
    end_time = datetime.utcnow()
    
    try:
        historical_data = await repo.get_kpi_history(
            site_name=site_name,
            start_time=start_time,
            end_time=end_time,
            kpi_names=kpi_names,
        )
        
        # Organize by KPI name for easier analysis
        organized_data: dict[str, list[dict[str, Any]]] = {}
        for record in historical_data:
            kpi_name = record.get("kpi_name", "unknown")
            if kpi_name not in organized_data:
                organized_data[kpi_name] = []
            organized_data[kpi_name].append({
                "value": record.get("value"),
                "timestamp": record.get("timestamp"),
            })
        
        # Calculate statistics for each KPI
        statistics: dict[str, dict[str, float]] = {}
        for kpi_name, values in organized_data.items():
            if values:
                nums = [v["value"] for v in values if v["value"] is not None]
                if nums:
                    statistics[kpi_name] = {
                        "min": min(nums),
                        "max": max(nums),
                        "avg": sum(nums) / len(nums),
                        "latest": nums[-1],
                        "count": len(nums),
                    }
        
        logger.info(
            "Retrieved historical KPIs",
            site_name=site_name,
            kpi_count=len(organized_data),
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours,
            },
            "data": organized_data,
            "statistics": statistics,
        }
        
    except DatabaseError as e:
        logger.error(
            "Failed to get historical KPIs",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=SaveRecommendationInput)
async def save_recommendation(
    site_name: str,
    optimization_type: str,
    recommendations: list[dict[str, Any]],
    analysis_summary: str,
) -> dict[str, Any]:
    """
    Save optimization recommendations to the database.
    
    Use this tool to persist recommendations for:
    - Audit trail and compliance
    - User review before execution
    - Historical analysis of optimization effectiveness
    
    Args:
        site_name: Name of the site
        optimization_type: Type of optimization
        recommendations: List of recommendation objects
        analysis_summary: Summary of analysis
        
    Returns:
        Confirmation with recommendation IDs
    """
    logger.info(
        "Saving recommendations",
        site_name=site_name,
        optimization_type=optimization_type,
        count=len(recommendations),
    )
    
    repo = get_repository()
    
    try:
        recommendation_ids = []
        
        for rec in recommendations:
            rec_id = await repo.save_recommendation(
                site_name=site_name,
                optimization_type=optimization_type,
                parameter_name=rec.get("parameter_name", ""),
                current_value=rec.get("current_value"),
                recommended_value=rec.get("recommended_value"),
                expected_improvement=rec.get("expected_improvement", 0.0),
                confidence=rec.get("confidence", 0.0),
                reasoning=rec.get("reasoning", ""),
                risk_level=rec.get("risk_level", "medium"),
                analysis_summary=analysis_summary,
            )
            recommendation_ids.append(rec_id)
        
        logger.info(
            "Saved recommendations",
            site_name=site_name,
            count=len(recommendation_ids),
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "optimization_type": optimization_type,
            "recommendation_ids": recommendation_ids,
            "count": len(recommendation_ids),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except DatabaseError as e:
        logger.error(
            "Failed to save recommendations",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=SiteInfoInput)
async def get_site_info(
    site_name: str,
) -> dict[str, Any]:
    """
    Retrieve comprehensive site information from the database.
    
    Returns:
    - Site metadata (location, technology, status)
    - Cell information
    - Recent KPI summary
    - Recent optimization history
    - Active alarms
    
    Args:
        site_name: Name of the site
        
    Returns:
        Comprehensive site information
    """
    logger.info(
        "Getting site info",
        site_name=site_name,
    )
    
    repo = get_repository()
    
    try:
        # Get site details
        site = await repo.get_site(site_name)
        
        if not site:
            return {
                "success": False,
                "site_name": site_name,
                "error": f"Site not found: {site_name}",
            }
        
        # Get cells
        cells = await repo.get_cells(site_name)
        
        # Get recent KPIs (last hour)
        recent_kpis = await repo.get_kpi_history(
            site_name=site_name,
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
        )
        
        # Get recent optimizations
        recent_opts = await repo.get_optimization_history(
            site_name=site_name,
            limit=5,
        )
        
        logger.info(
            "Retrieved site info",
            site_name=site_name,
            cell_count=len(cells),
        )
        
        return {
            "success": True,
            "site_name": site_name,
            "site": site,
            "cells": cells,
            "cell_count": len(cells),
            "recent_kpis": recent_kpis,
            "recent_optimizations": recent_opts,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except DatabaseError as e:
        logger.error(
            "Failed to get site info",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }


@tool(args_schema=CommandLogInput)
async def log_command_execution(
    site_name: str,
    command: str,
    target_ne: str,
    success: bool,
    result: Optional[str] = None,
    recommendation_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Log command execution for audit trail and rollback capability.
    
    Use this tool after executing MML commands to:
    - Maintain audit trail
    - Enable rollback if needed
    - Track optimization effectiveness
    
    Args:
        site_name: Name of the site
        command: MML command that was executed
        target_ne: Target network element
        success: Whether execution succeeded
        result: Result or error message
        recommendation_id: Associated recommendation ID
        
    Returns:
        Confirmation with log ID
    """
    logger.info(
        "Logging command execution",
        site_name=site_name,
        command=command[:50],
        success=success,
    )
    
    repo = get_repository()
    
    try:
        log_id = await repo.log_command(
            site_name=site_name,
            command=command,
            target_ne=target_ne,
            success=success,
            result=result,
            recommendation_id=recommendation_id,
            executed_at=datetime.utcnow(),
        )
        
        logger.info(
            "Logged command execution",
            log_id=log_id,
        )
        
        return {
            "success": True,
            "log_id": log_id,
            "site_name": site_name,
            "command_success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
    except DatabaseError as e:
        logger.error(
            "Failed to log command",
            site_name=site_name,
            error=str(e),
        )
        return {
            "success": False,
            "site_name": site_name,
            "error": str(e),
        }
