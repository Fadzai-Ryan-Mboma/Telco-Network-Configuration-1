#!/usr/bin/env python3
"""Read-only Huawei MML configuration discovery.

This probes a site with LST/DSP commands only, extracts returned field names,
and writes a local catalog. It never issues ADD/MOD/RMV/ACT/DEA commands.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from domain.mml_commands import GENERAL_COMMANDS, MML_COMMANDS  # noqa: E402
from network.huawei_api_client import HuaweiAPIClient  # noqa: E402


KNOWN_SITES = [
    "MSH-0014-Chipadze",
    "MSH-0112-Bindura Hospital",
    "MSH-0331-Chiwaridzo 2",
    "MSH0013-Bindura-Zaoga",
]

SAFE_EXTRA_COMMANDS = {
    # Identity, software, hardware, and operational state
    "version": "LST VER:;",
    "cell_all": "LST CELL:;",
    "cell_1": "LST CELL: LOCALCELLID=1;",
    "enodeb_function": "DSP ENODEBFUNCTION:;",
    "active_alarms": "DSP ALM:;",
    "patch": "DSP PATCH:;",
    "license": "DSP LICENSE:;",
    "board": "DSP BRD:;",
    "clock_status": "DSP CLKSTAT:;",
    "sctp_link": "LST SCTPLNK:;",
    "ip_path": "LST IPPATH:;",
    "route": "LST IPRT:;",
    "vlan": "LST VLANMAP:;",
    # LTE cell/channel/radio config. Some may be version or permission dependent.
    "cell_op": "DSP CELL:;",
    "cell_dl_pc": "LST CELLDLPCPDSCHPA: LOCALCELLID=1;",
    "cell_ul_pc_common": "LST CELLULPCCOMM: LOCALCELLID=1;",
    "pdsch_cfg": "LST PDSCHCFG: LOCALCELLID=1;",
    "cell_pdcch_algo": "LST CELLPDCCHALGO: LOCALCELLID=1;",
    "prach_cfg": "LST PRACHCFG: LOCALCELLID=1;",
    "pucch_cfg": "LST PUCCHCFG: LOCALCELLID=1;",
    "srs_cfg": "LST SRSCFG: LOCALCELLID=1;",
    "phich_cfg": "LST PHICHCFG: LOCALCELLID=1;",
    "drx_cfg": "LST DRX:;",
    "rrc_conn_ctrl": "LST RRCCONNSTATETIMER:;",
    "ue_timer_const": "LST UETIMERCONST:;",
    "ue_cooperation": "LST UECOOPERATIONPARA:;",
    # Mobility and neighbor relations
    "intra_freq_ho": "LST INTRAFREQHOGROUP:;",
    "inter_freq_ho": "LST INTERFREQHOGROUP:;",
    "eutran_intra_neighbor": "LST EUTRANINTRAFREQNCELL:;",
    "eutran_inter_neighbor": "LST EUTRANINTERFREQNCELL:;",
    "external_eutran_cell": "LST EUTRANEXTERNALCELL:;",
    "anr": "LST ANR:;",
    "x2": "LST X2:;",
    # SON/load/interference features
    "mlb": "LST MLB:;",
    "mro": "LST MRO:;",
    "icic": "LST ICIC:;",
    "load_control": "LST LOADCTRL:;",
    "admission_control": "LST ADMISSIONCTRL:;",
}


FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 _/\-\(\)%]+?)\s*=\s*(.+?)\s*$")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def safe_command(command: str) -> bool:
    command = command.strip().upper()
    return command.startswith(("LST ", "DSP ")) and ";" in command


def response_text(response: Any) -> str:
    if isinstance(response, dict):
        reports = []
        for item in response.get("results", []):
            if isinstance(item, dict) and isinstance(item.get("report"), str):
                reports.append(item["report"])
        if reports:
            return "\n".join(reports)

        candidates = [
            response.get("result"),
            response.get("data"),
            response.get("body"),
            response.get("message"),
            response.get("response"),
        ]
        for candidate in candidates:
            if isinstance(candidate, str):
                return candidate
            if isinstance(candidate, list):
                return "\n".join(str(item) for item in candidate)
        return json.dumps(response, ensure_ascii=False)
    return str(response)


def parse_fields(text: str) -> dict[str, list[str]]:
    fields: dict[str, set[str]] = {}
    lines = text.splitlines()
    for line in lines:
        match = FIELD_RE.match(line)
        if not match:
            continue
        field = " ".join(match.group(1).split())
        value = match.group(2).strip()
        if len(field) > 80 or not value:
            continue
        fields.setdefault(field, set()).add(value[:120])

    table_columns: set[str] = set()
    for index, line in enumerate(lines[:-1]):
        stripped = line.strip()
        next_line = lines[index + 1].strip()
        if not stripped or "=" in stripped or not re.search(r"[A-Za-z]", stripped):
            continue
        if not next_line or next_line.startswith("---") or next_line.startswith("++"):
            continue
        columns = [part.strip() for part in re.split(r"\s{2,}", stripped) if part.strip()]
        if len(columns) >= 3 and any("cell" in column.lower() for column in columns):
            table_columns.update(columns)

    if table_columns:
        fields["__table_columns__"] = table_columns
    return {field: sorted(values)[:8] for field, values in sorted(fields.items())}


def command_catalog() -> dict[str, str]:
    commands: dict[str, str] = {}
    for name, info in MML_COMMANDS.items():
        query = info.get("query")
        if query:
            commands[f"mapped_{name}"] = query.format(cell_id=1)
    for name, info in GENERAL_COMMANDS.items():
        command = info.get("command")
        if command:
            commands[f"general_{name}"] = command.format(cell_id=1)
    commands.update(SAFE_EXTRA_COMMANDS)
    return {name: command for name, command in commands.items() if safe_command(command)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default=KNOWN_SITES[0])
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--output-dir", default=str(ROOT / "data" / "discovery"))
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")

    base_url = (
        os.getenv("HUAWEI_API_URL")
        or os.getenv("NETGENIX_HUAWEI_ACCESS_NBI_URL")
        or ""
    )
    username = os.getenv("HUAWEI_USERNAME") or os.getenv("NETGENIX_HUAWEI_USERNAME") or ""
    password = os.getenv("HUAWEI_PASSWORD") or os.getenv("NETGENIX_HUAWEI_PASSWORD") or ""
    if not base_url or not username or not password:
        print("Missing Huawei API credentials in environment/.env", file=sys.stderr)
        return 2

    client = HuaweiAPIClient(
        {
            "base_url": base_url,
            "username": username,
            "password": password,
            "timeout": args.timeout,
            "retry_attempts": 0,
            "retry_delay": 1,
            "ssl_verify": False,
        }
    )
    if not client.connect():
        print("Failed to authenticate to Huawei API", file=sys.stderr)
        return 1

    started = datetime.now().isoformat(timespec="seconds")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    try:
        for name, command in command_catalog().items():
            record: dict[str, Any] = {
                "name": name,
                "command": command,
                "safe_read_only": safe_command(command),
                "success": False,
                "fields": {},
                "error": None,
            }
            try:
                raw = client.execute_mml_command(command, [args.site])
                text = response_text(raw)
                record["success"] = "RETCODE = 0" in text or "Operation succeeded" in text
                record["fields"] = parse_fields(text)
                record["raw_preview"] = text[:2000]
            except Exception as exc:
                record["error"] = str(exc)
            records.append(record)
            print(f"{'OK' if record['success'] else 'MISS'} {name}: {command}")
    finally:
        client.disconnect()

    catalog = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "started_at": started,
        "site": args.site,
        "notes": [
            "Read-only discovery only. Commands are limited to LST/DSP.",
            "A failed command can mean unsupported command, insufficient permission, wrong RAT/version, or different Huawei syntax.",
            "raw_preview is truncated and may contain NE configuration values, but no credentials/tokens.",
        ],
        "summary": {
            "commands_attempted": len(records),
            "commands_successful": sum(1 for record in records if record["success"]),
            "fields_discovered": sum(len(record["fields"]) for record in records),
        },
        "commands": records,
    }

    json_path = output_dir / f"huawei_config_catalog_{args.site.replace(' ', '_')}.json"
    md_path = output_dir / f"huawei_config_catalog_{args.site.replace(' ', '_')}.md"
    json_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        f"# Huawei Config Discovery - {args.site}",
        "",
        f"Generated: {catalog['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Commands attempted: {catalog['summary']['commands_attempted']}",
        f"- Commands successful: {catalog['summary']['commands_successful']}",
        f"- Field groups discovered: {catalog['summary']['fields_discovered']}",
        "",
        "## Successful Commands",
        "",
    ]
    for record in records:
        if not record["success"]:
            continue
        lines.extend(
            [
                f"### {record['name']}",
                "",
                f"`{record['command']}`",
                "",
            ]
        )
        if record["fields"]:
            for field, values in record["fields"].items():
                sample = ", ".join(values[:3])
                lines.append(f"- `{field}`: {sample}")
        else:
            lines.append("- No key/value fields parsed from response preview.")
        lines.append("")

    lines.extend(["## Failed / Unsupported Commands", ""])
    for record in records:
        if record["success"]:
            continue
        lines.append(f"- `{record['name']}`: `{record['command']}`")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
