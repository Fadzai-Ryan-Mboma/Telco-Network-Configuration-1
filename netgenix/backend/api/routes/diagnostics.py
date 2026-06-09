"""Diagnostics API endpoints."""

from fastapi import APIRouter, Query

from backend.models.schemas import NBIDiagnosticsResponse
from backend.netgenix.services.nbi_diagnostics import run_nbi_diagnostics

router = APIRouter()


@router.get("/nbi", response_model=NBIDiagnosticsResponse)
async def get_nbi_diagnostics(
    timeout: float = Query(10.0, ge=1.0, le=30.0, description="Connection timeout in seconds")
):
    """Run read-only Huawei iMaster MAE Access/Evaluation diagnostics."""
    return run_nbi_diagnostics(timeout=timeout)
