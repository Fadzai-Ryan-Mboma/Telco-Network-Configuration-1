"""Huawei parameter snapshot collection and retrieval."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime
from typing import Any

from .database import get_all_sites, get_db_connection, get_live_parameters
from .parameter_catalog import (
    DISCOVERY_COMMANDS,
    TOP_15_PARAMETERS,
    coerce_parameter_value,
    command_key,
)

logger = logging.getLogger(__name__)


FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _/\-\(\)%\.]+?)\s*=\s*(.+?)\s*$")


def load_dotenv_if_present() -> None:
    env_path = os.getenv("NETGENIX_ENV_FILE")
    candidates = [env_path] if env_path else []
    candidates.append(str(__import__("pathlib").Path(__file__).resolve().parents[3] / ".env"))
    for candidate in candidates:
        if not candidate:
            continue
        path = __import__("pathlib").Path(candidate)
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def init_parameter_snapshot_tables() -> None:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS huawei_parameter_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                site_name TEXT NOT NULL,
                command_name TEXT NOT NULL,
                command TEXT NOT NULL,
                ret_code TEXT,
                success BOOLEAN DEFAULT 0,
                raw_report TEXT,
                error_message TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS huawei_parameter_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                site_name TEXT NOT NULL,
                command_name TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                parameter_value TEXT,
                value_json TEXT,
                source TEXT DEFAULT 'live_api',
                FOREIGN KEY(snapshot_id) REFERENCES huawei_parameter_snapshots(id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_huawei_param_site_time ON huawei_parameter_values(site_name, timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_huawei_param_site_name ON huawei_parameter_values(site_name, parameter_name)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_huawei_snapshot_site_time ON huawei_parameter_snapshots(site_name, timestamp)"
        )
        conn.commit()
    finally:
        conn.close()


def response_text(response: Any) -> str:
    if isinstance(response, dict):
        reports = [
            item.get("report")
            for item in response.get("results", [])
            if isinstance(item, dict) and isinstance(item.get("report"), str)
        ]
        if reports:
            return "\n".join(reports)
        return json.dumps(response, ensure_ascii=False)
    return str(response)


def response_ret_code(response: Any) -> str | None:
    if not isinstance(response, dict):
        return None
    result_codes = [
        str(item.get("retCode"))
        for item in response.get("results", [])
        if isinstance(item, dict) and item.get("retCode") is not None
    ]
    return result_codes[0] if result_codes else str(response.get("retCode"))


def parse_report_fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if not match:
            continue
        field = " ".join(match.group(1).split())
        value = match.group(2).strip()
        if len(field) > 100 or not value:
            continue
        fields.setdefault(field, [])
        if value not in fields[field]:
            fields[field].append(value[:300])

    # Huawei table outputs often put headers and values in columns instead of
    # key/value rows. Pull only the top-15 fields from those tables.
    top_fields = {parameter.field for parameter in TOP_15_PARAMETERS}
    lines = text.splitlines()
    for index, line in enumerate(lines[:-1]):
        header = line.strip()
        row = lines[index + 2].strip() if index + 2 < len(lines) else ""
        if not header or "=" in header or not row:
            continue
        columns = [part.strip() for part in re.split(r"\s{2,}", header) if part.strip()]
        values = [part.strip() for part in re.split(r"\s{2,}", row) if part.strip()]
        if len(columns) < 3 or len(values) < 3:
            continue
        for column, value in zip(columns, values):
            if column in top_fields:
                fields.setdefault(column, [])
                if value not in fields[column]:
                    fields[column].append(value[:300])
    return fields


def get_huawei_client():
    from network.huawei_api_client import HuaweiAPIClient

    load_dotenv_if_present()
    return HuaweiAPIClient(
        {
            "base_url": os.getenv("HUAWEI_API_URL") or os.getenv("NETGENIX_HUAWEI_ACCESS_NBI_URL"),
            "username": os.getenv("HUAWEI_USERNAME") or os.getenv("NETGENIX_HUAWEI_USERNAME"),
            "password": os.getenv("HUAWEI_PASSWORD") or os.getenv("NETGENIX_HUAWEI_PASSWORD"),
            "timeout": int(os.getenv("NETGENIX_HUAWEI_PARAM_TIMEOUT", "20")),
            "retry_attempts": int(os.getenv("NETGENIX_HUAWEI_PARAM_RETRIES", "0")),
            "retry_delay": 1,
            "ssl_verify": False,
        }
    )


def collect_huawei_parameter_snapshot(
    site_name: str,
    commands: dict[str, str] | None = None,
) -> dict[str, Any]:
    init_parameter_snapshot_tables()
    commands = commands or DISCOVERY_COMMANDS
    client = get_huawei_client()
    if not client.connect():
        raise RuntimeError("Failed to authenticate with Huawei API")

    conn = get_db_connection()
    attempted = 0
    successful = 0
    values_inserted = 0
    try:
        cursor = conn.cursor()
        for command_name, command in commands.items():
            attempted += 1
            success = False
            error = None
            ret_code = None
            report = ""
            values: dict[str, list[str]] = {}
            try:
                response = client.execute_mml_command(command, [site_name])
                report = response_text(response)
                ret_code = response_ret_code(response)
                success = "RETCODE = 0" in report or "Operation succeeded" in report
                if success:
                    successful += 1
                    values = parse_report_fields(report)
            except Exception as exc:
                error = str(exc)

            cursor.execute(
                """
                INSERT INTO huawei_parameter_snapshots
                (site_name, command_name, command, ret_code, success, raw_report, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (site_name, command_name, command, ret_code, int(success), report, error),
            )
            snapshot_id = cursor.lastrowid
            for field, field_values in values.items():
                value = field_values[0] if field_values else None
                cursor.execute(
                    """
                    INSERT INTO huawei_parameter_values
                    (snapshot_id, site_name, command_name, parameter_name, parameter_value, value_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        site_name,
                        command_name,
                        field,
                        value,
                        json.dumps(field_values, ensure_ascii=False),
                    ),
                )
                values_inserted += 1
        conn.commit()
    finally:
        conn.close()
        client.disconnect()

    return {
        "site_name": site_name,
        "commands_attempted": attempted,
        "commands_successful": successful,
        "values_inserted": values_inserted,
    }


def collect_all_site_huawei_parameter_snapshots() -> list[dict[str, Any]]:
    results = []
    for site in get_all_sites():
        site_name = site["site_name"]
        try:
            results.append(collect_huawei_parameter_snapshot(site_name))
        except Exception as exc:
            logger.exception("Parameter snapshot collection failed for %s", site_name)
            results.append({"site_name": site_name, "error": str(exc)})
    return results


def get_latest_huawei_field_values(site_name: str) -> dict[str, str]:
    init_parameter_snapshot_tables()
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT parameter_name, parameter_value
            FROM huawei_parameter_values
            WHERE site_name = ?
            AND id IN (
                SELECT MAX(id)
                FROM huawei_parameter_values
                WHERE site_name = ?
                GROUP BY parameter_name
            )
            """,
            (site_name, site_name),
        ).fetchall()
        return {row["parameter_name"]: row["parameter_value"] for row in rows}
    finally:
        conn.close()


def get_top_15_parameters_from_db(site_name: str) -> dict[str, dict[str, Any]]:
    values = get_latest_huawei_field_values(site_name)
    params = {}
    for parameter in TOP_15_PARAMETERS:
        value = values.get(parameter.field)
        params[parameter.key] = {
            "value": coerce_parameter_value(value, parameter.value_type),
            "unit": parameter.unit,
            "source": "database",
            "label": parameter.label,
            "category": parameter.category,
            "priority": parameter.priority,
            "description": parameter.description,
        }
    return params


def get_top_15_parameters_live(site_name: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    command_names = {
        f"top15_{index}": command
        for index, command in enumerate(
            {command_key(parameter.command): parameter.command for parameter in TOP_15_PARAMETERS}.values(),
            start=1,
        )
    }
    errors: list[str] = []
    try:
        collect_huawei_parameter_snapshot(site_name, commands=command_names)
    except Exception as exc:
        errors.append(str(exc))

    params = get_top_15_parameters_from_db(site_name)
    has_live_values = any(param["value"] is not None for param in params.values())
    if has_live_values:
        for param in params.values():
            param["source"] = "live_api" if param["value"] is not None else "database"
        return params, errors

    # Fall back to the older site-level Huawei query path when the newer
    # snapshot/MML collector is denied by the Access NBI account.
    legacy_live = get_live_parameters(site_name)
    if legacy_live:
        for parameter in TOP_15_PARAMETERS:
            value = legacy_live.get(parameter.key)
            if value is None:
                continue
            params[parameter.key] = {
                "value": coerce_parameter_value(value, parameter.value_type),
                "unit": parameter.unit,
                "source": "live_api",
                "label": parameter.label,
                "category": parameter.category,
                "priority": parameter.priority,
                "description": parameter.description,
            }
        if any(param["value"] is not None for param in params.values()):
            live_errors = legacy_live.get("errors") or []
            site_offline = legacy_live.get("site_offline")
            if live_errors:
                errors.extend(str(error) for error in live_errors)
            if site_offline:
                errors.append("Huawei live parameter query reported the site offline.")
            return params, errors

    if not errors:
        errors.append("No live parameter values were returned for this site.")
    return params, errors
