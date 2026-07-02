"""Persistent asynchronous Evaluation-to-report workflow."""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from backend.netgenix.reports.engine import run_report_from_rows
from backend.netgenix.services.evaluation_ingestion import ingest_evaluation_zip
from network.evaluation_exporter import (
    EvaluationSessionError,
    export_evaluation_report,
    mark_session_invalid,
    session_status,
    validate_period,
)
from scripts.ingest_csv_to_timescaledb import get_conn


log = logging.getLogger(__name__)
AUTOMATION_LOCK_ID = 733_641_007


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS report_automation_jobs (
    job_id UUID PRIMARY KEY,
    status TEXT NOT NULL,
    refresh_requested BOOLEAN NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    exclusions JSONB NOT NULL DEFAULT '[]'::jsonb,
    stage TEXT NOT NULL DEFAULT 'queued',
    error_message TEXT,
    report_run_id TEXT,
    source_freshness TIMESTAMPTZ,
    rows_ingested INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_report_automation_jobs_created
    ON report_automation_jobs (created_at DESC);

CREATE TABLE IF NOT EXISTS report_exclusions (
    site_name TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def ensure_automation_schema() -> None:
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
        connection.commit()
    finally:
        connection.close()


def _row_to_job(row: tuple, columns: list[str]) -> dict[str, object]:
    payload = dict(zip(columns, row))
    for key in ("job_id", "period_start", "period_end"):
        if payload.get(key) is not None:
            payload[key] = str(payload[key])
    for key in ("source_freshness", "created_at", "started_at", "completed_at"):
        if payload.get(key) is not None:
            payload[key] = payload[key].isoformat()
    if isinstance(payload.get("exclusions"), str):
        payload["exclusions"] = json.loads(str(payload["exclusions"]))
    run_id = payload.get("report_run_id")
    payload["download_url"] = f"/api/reports/runs/{run_id}/download" if run_id else None
    payload["pdf_download_url"] = f"/api/reports/runs/{run_id}/download/pdf" if run_id else None
    return payload


def get_job(job_id: str) -> dict[str, object] | None:
    ensure_automation_schema()
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM report_automation_jobs WHERE job_id = %s", (job_id,))
            row = cursor.fetchone()
            return _row_to_job(row, [item.name for item in cursor.description]) if row else None
    finally:
        connection.close()


def list_jobs(limit: int = 10) -> list[dict[str, object]]:
    ensure_automation_schema()
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM report_automation_jobs ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()
            columns = [item.name for item in cursor.description]
            return [_row_to_job(row, columns) for row in rows]
    finally:
        connection.close()


def get_exclusions() -> list[str]:
    ensure_automation_schema()
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT site_name FROM report_exclusions ORDER BY lower(site_name)")
            return [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()


def replace_exclusions(sites: Iterable[str]) -> list[str]:
    normalized = sorted({site.strip() for site in sites if site.strip()}, key=str.lower)
    ensure_automation_schema()
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM report_exclusions")
            if normalized:
                cursor.executemany(
                    "INSERT INTO report_exclusions (site_name) VALUES (%s)",
                    [(site,) for site in normalized],
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return normalized


def _set_job(job_id: str, **updates: object) -> None:
    if not updates:
        return
    columns = ", ".join(f"{key} = %s" for key in updates)
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE report_automation_jobs SET {columns} WHERE job_id = %s",
                (*updates.values(), job_id),
            )
        connection.commit()
    finally:
        connection.close()


def _database_report_rows(start: date, end: date) -> tuple[list[dict[str, object]], datetime | None]:
    start_at = datetime.combine(start, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc)
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT time, enodeb_name, total_traffic_gbit, dl_prb_usage_rate,
                       call_drop_rate, radio_net_availability_rate,
                       user_dl_pdcp_avg_throughput
                FROM kpi_cell
                WHERE granularity = 'daily' AND time >= %s AND time < %s
                ORDER BY time, enodeb_name, cell_name
                """,
                (start_at, end_at),
            )
            rows = [
                {
                    "Date": row[0].date().isoformat(),
                    "eNodeB Name": row[1],
                    "Total Traffic (Gbit)": row[2],
                    "DL PRB Usage Rate(%)": row[3],
                    "Call Drop Rate (All)(%)": row[4],
                    "Radio Net Availability Rate(%)": row[5],
                    "User DL PDCP Average Throughput": row[6],
                }
                for row in cursor.fetchall()
            ]
            cursor.execute(
                """
                SELECT MAX(run_at) FROM ingestion_log
                WHERE status = 'ok'
                  AND period_start::date <= %s
                  AND period_end::date >= %s
                """,
                (start, end),
            )
            freshness = cursor.fetchone()[0]
    finally:
        connection.close()
    if not rows:
        raise ValueError(f"No daily Evaluation data exists for {start} through {end}")
    return rows, freshness


def _execute_job(job_id: str) -> None:
    job = get_job(job_id)
    if not job:
        return
    lock_connection = get_conn()
    try:
        with lock_connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", (AUTOMATION_LOCK_ID,))
            if not cursor.fetchone()[0]:
                raise RuntimeError("Another Evaluation automation job is already running")

        _set_job(job_id, status="running", stage="preparing", started_at=datetime.now(timezone.utc))
        start = date.fromisoformat(str(job["period_start"]))
        end = date.fromisoformat(str(job["period_end"]))
        rows_ingested = 0
        if job["refresh_requested"]:
            _set_job(job_id, stage="downloading")
            exported = export_evaluation_report(start, end, headless=True)
            _set_job(job_id, stage="ingesting")
            counts = ingest_evaluation_zip(
                exported.zip_path,
                period_start=start,
                period_end=end,
                source=f"mae_gui_job_{job_id}",
            )
            rows_ingested = counts["cell_rows"] + counts["network_rows"]

        _set_job(job_id, stage="generating", rows_ingested=rows_ingested)
        rows, freshness = _database_report_rows(start, end)
        result = run_report_from_rows(
            rows,
            source_label=f"Evaluation database {start} to {end}",
            exclusions=list(job.get("exclusions") or []),
            user_context=f"automation:{job_id}",
            evaluation_only=True,
        )
        _set_job(
            job_id,
            status="completed",
            stage="completed",
            report_run_id=result["run_id"],
            source_freshness=freshness,
            completed_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        log.exception("Evaluation report job %s failed", job_id)
        if isinstance(exc, EvaluationSessionError):
            mark_session_invalid(str(exc))
        _set_job(
            job_id,
            status="failed",
            stage="failed",
            error_message=str(exc),
            completed_at=datetime.now(timezone.utc),
        )
    finally:
        try:
            with lock_connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", (AUTOMATION_LOCK_ID,))
        finally:
            lock_connection.close()


def create_job(
    start: date,
    end: date,
    *,
    refresh: bool,
    exclusion_overrides: Iterable[str] = (),
) -> dict[str, object]:
    validate_period(start, end, allowed_days=(7,))
    exclusions = sorted(set(get_exclusions()) | {site.strip() for site in exclusion_overrides if site.strip()})
    job_id = str(uuid.uuid4())
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO report_automation_jobs
                    (job_id, status, refresh_requested, period_start, period_end, exclusions)
                VALUES (%s, 'queued', %s, %s, %s, %s::jsonb)
                """,
                (job_id, refresh, start, end, json.dumps(exclusions)),
            )
        connection.commit()
    finally:
        connection.close()
    threading.Thread(target=_execute_job, args=(job_id,), daemon=True, name=f"report-{job_id[:8]}").start()
    return get_job(job_id) or {"job_id": job_id, "status": "queued"}


def evaluation_status() -> dict[str, object]:
    state = session_status()
    ensure_automation_schema()
    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT run_at, period_start, period_end, rows_inserted
                FROM ingestion_log
                WHERE status = 'ok'
                  AND (source LIKE 'mae_gui_%' OR source LIKE 'evaluation_gui_%')
                ORDER BY run_at DESC LIMIT 1
                """
            )
            latest = cursor.fetchone()
    finally:
        connection.close()
    state["last_successful_extraction"] = latest[0].isoformat() if latest else None
    state["last_period_start"] = str(latest[1]) if latest else None
    state["last_period_end"] = str(latest[2]) if latest else None
    state["last_rows_ingested"] = latest[3] if latest else 0
    return state
