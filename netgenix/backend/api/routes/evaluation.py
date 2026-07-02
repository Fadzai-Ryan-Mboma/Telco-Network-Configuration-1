"""Evaluation automation status API."""

from fastapi import APIRouter, HTTPException

from backend.models.schemas import EvaluationStatus, ReconnectSessionStatus
from backend.netgenix.services.evaluation_reconnect import (
    cancel_reconnect_session,
    get_reconnect_status,
    start_reconnect_session,
)
from backend.netgenix.services.report_automation import evaluation_status


router = APIRouter()


@router.get("/status", response_model=EvaluationStatus)
async def get_evaluation_status():
    return evaluation_status()


@router.post("/reconnect/start", response_model=ReconnectSessionStatus)
async def start_reconnect():
    try:
        return start_reconnect_session()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/reconnect/status/{session_id}", response_model=ReconnectSessionStatus)
async def reconnect_status(session_id: str):
    status = get_reconnect_status(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Reconnect session not found")
    return status


@router.post("/reconnect/cancel/{session_id}", response_model=ReconnectSessionStatus)
async def reconnect_cancel(session_id: str):
    status = cancel_reconnect_session(session_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Reconnect session not found")
    return status
