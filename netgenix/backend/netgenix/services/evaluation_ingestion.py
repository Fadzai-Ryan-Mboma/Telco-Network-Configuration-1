"""Evaluation ZIP parsing and corrective TimescaleDB ingestion."""

from __future__ import annotations

import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg2.extras

from scripts.ingest_csv_to_timescaledb import (
    CELL_INSERT,
    NETWORK_INSERT,
    _cell_rows,
    _network_rows,
    _read_csv,
    get_conn,
)


def _extract_csvs(zip_path: Path, target: Path) -> list[Path]:
    paths: list[Path] = []
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if not member.filename.lower().endswith(".csv"):
                continue
            safe_name = Path(member.filename).name
            destination = target / safe_name
            destination.write_bytes(archive.read(member))
            paths.append(destination)
    if not paths:
        raise ValueError("Evaluation ZIP contains no CSV files")
    return paths


def ingest_evaluation_zip(
    zip_path: Path,
    *,
    period_start: date,
    period_end: date,
    source: str = "mae_gui_automation",
) -> dict[str, int]:
    """Parse both Evaluation report sections and upsert corrected values."""
    with TemporaryDirectory(prefix="netgenix-evaluation-") as temp_dir:
        csv_paths = _extract_csvs(zip_path, Path(temp_dir))
        cell_rows: list[tuple] = []
        network_rows: list[tuple] = []
        for csv_path in csv_paths:
            frame = _read_csv(csv_path)
            if "Cell Name" in frame.columns:
                cell_rows.extend(_cell_rows(frame, source))
            elif "Date" in frame.columns:
                network_rows.extend(_network_rows(frame, source))

    if not cell_rows:
        raise ValueError("Evaluation export did not contain cell-level KPI rows")
    if not network_rows:
        raise ValueError("Evaluation export did not contain whole-network KPI rows")

    connection = get_conn()
    try:
        with connection.cursor() as cursor:
            for offset in range(0, len(cell_rows), 2000):
                psycopg2.extras.execute_values(
                    cursor,
                    CELL_INSERT,
                    cell_rows[offset : offset + 2000],
                    page_size=2000,
                )
            psycopg2.extras.execute_values(cursor, NETWORK_INSERT, network_rows, page_size=500)
            cursor.execute(
                """
                INSERT INTO ingestion_log
                    (run_at, source, granularity, period_start, period_end,
                     rows_inserted, rows_skipped, status)
                VALUES (%s, %s, 'daily', %s, %s, %s, 0, 'ok')
                """,
                (
                    datetime.now(timezone.utc),
                    source,
                    period_start,
                    period_end,
                    len(cell_rows) + len(network_rows),
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {"cell_rows": len(cell_rows), "network_rows": len(network_rows)}
