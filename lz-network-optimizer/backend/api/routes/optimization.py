"""
Optimization API endpoints
"""

import sys
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.models.schemas import (
    OptimizationRequest, OptimizationResult, ParameterRecommendation,
    ExecutionRequest, ExecutionResult, ExecutionDetail
)

# Import existing workflow interface
from ui.workflow_interface import run_optimization, execute_optimization
from ui.database_helper import get_site_info

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=OptimizationResult)
async def run_optimization_api(request: OptimizationRequest):
    """
    Run optimization workflow for a site.

    This triggers the full AI agent workflow:
    1. Network Connector Agent - queries live parameters
    2. KPI Analytics Agent - analyzes network KPIs
    3. Monitoring Agent - detects issues
    4. Config Agent - builds recommendations & MML commands
    5. Validation Agent - risk assessment
    """
    # Verify site exists
    site_info = get_site_info(request.site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{request.site_name}' not found")

    logger.info(f"Running optimization for {request.site_name}: {request.query}")

    # Run the optimization workflow
    result = run_optimization(
        site_name=request.site_name,
        cell_id=request.cell_id,
        user_query=request.query
    )

    # Convert to API response format
    if result.get("status") == "error":
        return OptimizationResult(
            status="error",
            error_message=result.get("error_message", "Unknown error"),
            issue="",
            recommendations=[],
            risk_level="HIGH",
            risk_score=10.0,
            expected_impact="",
            mml_commands=[]
        )

    if result.get("status") == "rejected":
        return OptimizationResult(
            status="rejected",
            issue=result.get("issue", ""),
            message=result.get("message", "Optimization rejected"),
            recommendations=[],
            risk_level="HIGH",
            risk_score=9.0,
            expected_impact="",
            mml_commands=[]
        )

    # Parse recommendations into structured format
    recommendations = []
    for rec in result.get("recommendations", []):
        recommendations.append(ParameterRecommendation(
            parameter=rec.get("parameter", ""),
            current_value=rec.get("current_value", "N/A"),
            recommended_value=rec.get("recommended_value", rec.get("change", "")),
            unit=rec.get("unit", ""),
            description=rec.get("description", "")
        ))

    return OptimizationResult(
        status="success",
        issue=result.get("issue", ""),
        detailed_issue=result.get("detailed_issue"),
        recommendations=recommendations,
        detailed_recommendations=result.get("detailed_recommendations"),
        risk_level=result.get("risk_level", "LOW"),
        risk_score=result.get("risk_score", 0.0),
        detailed_risk=result.get("detailed_risk"),
        expected_impact=result.get("expected_impact", ""),
        detailed_impact=result.get("detailed_impact"),
        mml_commands=result.get("mml_commands", []),
        kpi_issue=result.get("kpi_issue")
    )


@router.post("/execute", response_model=ExecutionResult)
async def execute_optimization_api(request: ExecutionRequest):
    """
    Execute approved optimization recommendations.

    This applies the MML commands to the network via Huawei API.
    """
    # Verify site exists
    site_info = get_site_info(request.site_name)
    if not site_info:
        raise HTTPException(status_code=404, detail=f"Site '{request.site_name}' not found")

    if not request.mml_commands:
        raise HTTPException(status_code=400, detail="No MML commands provided")

    logger.info(f"Executing optimization for {request.site_name}")
    logger.info(f"Commands: {len(request.mml_commands)}")

    # Execute the optimization
    result = execute_optimization(
        site_name=request.site_name,
        recommendations=request.recommendations,
        mml_commands=request.mml_commands
    )

    # Convert to API response format
    details = []
    for detail in result.get("details", []):
        details.append(ExecutionDetail(
            command=detail.get("command", ""),
            status=detail.get("status", "unknown"),
            message=detail.get("message")
        ))

    return ExecutionResult(
        status=result.get("status", "error"),
        message=result.get("message", ""),
        dry_run=result.get("dry_run", False),
        details=details
    )
