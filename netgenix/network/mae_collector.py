"""Scheduled Evaluation collector using an operator-authenticated session."""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.netgenix.services.evaluation_ingestion import ingest_evaluation_zip
from network.evaluation_exporter import export_evaluation_report


def run_collection(mode: str = "daily", headless: bool = True) -> dict[str, int]:
    """Refresh the last seven completed days and correct existing DB rows."""
    if mode not in {"daily", "weekly"}:
        raise ValueError("Evaluation collector mode must be 'daily' or 'weekly'")
    end = datetime.now().astimezone().date() - timedelta(days=1)
    start = end - timedelta(days=6)
    exported = export_evaluation_report(start, end, headless=headless)
    return ingest_evaluation_zip(
        exported.zip_path,
        period_start=start,
        period_end=end,
        source=f"mae_gui_{mode}",
    )
