#!/usr/bin/env python3
"""Read-only probe for Huawei MAE Access NBI capabilities.

The script intentionally redacts tokens and credentials from output. It only
performs login plus read/query operations against documented MAE APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = "/api/rest/securityManagement/v1/oauth/token"
KNOWN_SITES = [
    "MSH-0014-Chipadze",
    "MSH-0112-Bindura Hospital",
    "MSH-0331-Chiwaridzo 2",
    "MSH0013-Bindura-Zaoga",
]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/" + path.lstrip("/")
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["X-Auth-Token"] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout, context=ssl_context()) as response:
            body = response.read().decode("utf-8", errors="replace")
            return parse_response(response.status, body, None)
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return parse_response(error.code, body, None)
    except (TimeoutError, URLError, OSError) as error:
        return {"status": None, "json": {}, "body_preview": "", "error": str(error)}


def parse_response(status: int, body: str, error: str | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    try:
        loaded = json.loads(body) if body else {}
        if isinstance(loaded, dict):
            parsed = loaded
    except json.JSONDecodeError:
        parsed = {}
    return {
        "status": status,
        "json": parsed,
        "body_preview": body[:500],
        "error": error,
    }


def summarize(name: str, response: dict[str, Any]) -> dict[str, Any]:
    body = response.get("json") or {}
    result = body.get("result")
    if isinstance(result, list):
        result_count: int | None = len(result)
    else:
        result_count = None

    alarms = body.get("alarmInformationList")
    if isinstance(alarms, list):
        alarm_count: int | None = len(alarms)
    else:
        alarm_count = None

    results = body.get("results")
    if isinstance(results, list):
        results_count: int | None = len(results)
        result_names = [
            item.get("name")
            for item in results
            if isinstance(item, dict) and item.get("name")
        ][:10]
    else:
        results_count = None
        result_names = []

    topology_results = body.get("results")
    topology_cell_count = None
    if isinstance(topology_results, list):
        topology_cell_count = sum(
            len(item.get("cellInfos", []))
            for item in topology_results
            if isinstance(item, dict) and isinstance(item.get("cellInfos"), list)
        )

    return {
        "test": name,
        "http_status": response.get("status"),
        "retCode": body.get("retCode"),
        "retMessage": body.get("retMessage"),
        "status": body.get("status"),
        "taskId": body.get("taskId"),
        "totalSize": body.get("totalSize"),
        "result_count": result_count,
        "results_count": results_count,
        "result_names": result_names,
        "topology_cell_count": topology_cell_count,
        "alarm_count": alarm_count,
        "marker_present": bool(body.get("marker") and body.get("marker") != "null"),
        "error": response.get("error"),
        "sample_keys": sorted(body.keys())[:12],
        "body_preview": "" if body else response.get("body_preview", "")[:220],
    }


def summarize_alarm_records(response: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    alarms = (response.get("json") or {}).get("alarmInformationList")
    if not isinstance(alarms, list):
        return []

    summaries = []
    for alarm in alarms[:limit]:
        if not isinstance(alarm, dict):
            continue
        summaries.append(
            {
                "alarmId": alarm.get("alarmId"),
                "alarmName": alarm.get("alarmName"),
                "objectInstance": alarm.get("objectInstance"),
                "nativeMoName": alarm.get("nativeMoName"),
                "perceivedSeverity": alarm.get("perceivedSeverity"),
                "probableCause": alarm.get("probableCause"),
                "notificationType": alarm.get("notificationType"),
                "alarmRaisedTime": alarm.get("alarmRaisedTime"),
                "alarmClearedTime": alarm.get("alarmClearedTime"),
                "specialAlarmStatus": alarm.get("specialAlarmStatus"),
                "comments": alarm.get("comments"),
            }
        )
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="MSH-0112-Bindura Hospital")
    parser.add_argument("--all-known-sites", action="store_true")
    parser.add_argument("--include-alarm-details", action="store_true")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    base_url = os.getenv("NETGENIX_HUAWEI_ACCESS_NBI_URL", "https://41.174.191.214:31127")
    username = os.getenv("NETGENIX_HUAWEI_USERNAME") or os.getenv("HUAWEI_USERNAME")
    password = os.getenv("NETGENIX_HUAWEI_PASSWORD") or os.getenv("HUAWEI_PASSWORD")
    if not username or not password:
        print(json.dumps({"error": "NBI credentials are not configured"}, indent=2))
        return 2

    login = request(
        base_url,
        TOKEN_PATH,
        method="PUT",
        payload={"grantType": "password", "userName": username, "value": password},
        timeout=args.timeout,
    )
    token = (login.get("json") or {}).get("accessSession") or (login.get("json") or {}).get("access_token")

    output: dict[str, Any] = {
        "base_url": base_url,
        "login": {
            "http_status": login.get("status"),
            "retCode": (login.get("json") or {}).get("retCode"),
            "retMessage": (login.get("json") or {}).get("retMessage"),
            "token_received": bool(token),
            "error": login.get("error"),
        },
        "probes": [],
        "notes": [],
    }

    if not token:
        print(json.dumps(output, indent=2))
        return 1

    for name, method, path in [
        ("system_connection_status", "POST", "/api/rest/oss-info/v1/connection-status"),
        ("system_omc_id", "GET", "/api/rest/oss-info/v1/omcid"),
        ("system_mae_version", "GET", "/api/rest/oss-info/v1/mae-version"),
    ]:
        output["probes"].append(
            summarize(
                name,
                request(base_url, path, method=method, token=token, payload={} if method == "POST" else None),
            )
        )

    alarm_path = "/api/rest/faultSupervisonManagement/v1/alarms?" + urlencode(
        {"dataType": "CURRENT", "limit": 5}
    )
    current_alarm_response = request(base_url, alarm_path, token=token)
    output["probes"].append(summarize("current_alarms_limit_5", current_alarm_response))

    historical_alarm_path = "/api/rest/faultSupervisonManagement/v1/alarms?" + urlencode(
        {"dataType": "HISTORY", "limit": 5}
    )
    historical_alarm_response = request(base_url, historical_alarm_path, token=token)
    output["probes"].append(
        summarize("historical_alarms_limit_5", historical_alarm_response)
    )
    if args.include_alarm_details:
        output["alarm_samples"] = {
            "current": summarize_alarm_records(current_alarm_response),
            "historical": summarize_alarm_records(historical_alarm_response),
        }

    sites = KNOWN_SITES if args.all_known_sites else [args.site]
    for site in sites:
        mml_payload = {"command": "LST UECOOPERATIONPARA:;", "neNames": [site]}
        output["probes"].append(
            summarize(
                f"single_mml_read_{site}",
                request(base_url, "/api/rest/mmlManagement/v1/command", method="POST", token=token, payload=mml_payload),
            )
        )

    topology_payloads = [
        ("topology_empty_fdns", {"fdns": []}),
        ("topology_site_name_as_fdn", {"fdns": [args.site]}),
    ]
    for name, payload in topology_payloads:
        output["probes"].append(
            summarize(
                name,
                request(base_url, "/api/rest/resourceManagement/v1/topocellsinfo", method="POST", token=token, payload=payload),
            )
        )

    now = datetime.now().replace(second=0, microsecond=0)
    start = now - timedelta(minutes=60)
    pm_payload = {
        "timeFormat": "timeString",
        "startTime": start.strftime("%Y-%m-%d %H:%M:%S"),
        "endTime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "period": 60,
        "counterIds": [1526749447, 1526743671],
        "isQueryAllNe": 0,
        "neTypeName": "eNodeB",
        "neNames": sites,
    }
    pm_response = request(
        base_url,
        "/api/rest/performanceManagement/v1/measurementResults",
        method="POST",
        token=token,
        payload=pm_payload,
    )
    output["probes"].append(
        summarize(
            "pm_query_known_sites_sample_counters_last_hour",
            pm_response,
        )
    )
    task_id = (pm_response.get("json") or {}).get("taskId")
    if task_id:
        output["probes"].append(
            summarize(
                "pm_query_cleanup_delete_task",
                request(
                    base_url,
                    f"/api/rest/performanceManagement/v1/measurementResults/{task_id}",
                    method="DELETE",
                    token=token,
                ),
            )
        )

    output["notes"].append("PM probe uses sample counter IDs from the MAE guide, not yet validated Cassava KPI counter IDs.")
    output["notes"].append("All probes are read-only; no MML modify commands are issued.")
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
