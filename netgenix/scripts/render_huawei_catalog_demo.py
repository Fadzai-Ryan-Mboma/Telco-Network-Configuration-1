#!/usr/bin/env python3
"""Render the Huawei discovery catalog as a static HTML demo."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


IMPORTANT_FIELDS = {
    "Signal / RF Power": [
        "Reference signal power(0.1dBm)",
        "PB",
        "Reference Signal Power Margin(0.1dB)",
        "CRS Power Boosting Amplitude",
        "CRS Power Reduction Amount",
        "Cell Power Limit(0.01W)",
        "PA for even power distribution(dB)",
        "Nominal PDSCH-to-RS-EPRE Offset(dB)",
        "Max transmit power allowed(dBm)",
    ],
    "Cell Identity / Carrier": [
        "Local Cell ID",
        "Cell Name",
        "Cell ID",
        "Physical cell ID",
        "Frequency band",
        "Downlink EARFCN",
        "Uplink EARFCN",
        "Downlink bandwidth",
        "Uplink bandwidth",
        "Cell active state",
        "Cell admin state",
        "Cell FDD TDD indication",
        "Subframe assignment",
        "Special subframe patterns",
        "Root sequence index",
        "Cell radius(m)",
    ],
    "Mobility / Handover": [
        "A3 Handover Threshold Offset",
        "A2 Handover Threshold Offset",
        "Intrafreq handover hysteresis(0.5dB)",
        "Intrafreq handover offset(0.5dB)",
        "Intrafreq handover time to trigger",
        "Interfreq A3 offset(0.5dB)",
        "Interfreq HandOver Time to Trigger(ms)",
        "Cell individual offset(dB)",
        "Cell offset(dB)",
        "No handover indicator",
    ],
    "RLF / RRC Timers": [
        "Timer 300",
        "Timer 301",
        "Timer 310",
        "Timer 311",
        "Constant N310",
        "Constant N311",
        "RRC Connection Release Timer(ms)",
        "No Context Reestablishment Timer Offset(ms)",
        "Extended Wait Time(s)",
    ],
    "Uplink Power / Control": [
        "P0 nominal PUSCH(dBm)",
        "P0 nominal PUCCH(dBm)",
        "Path loss coefficient",
        "DeltaF for PUCCH format 1(dB)",
        "DeltaF for PUCCH format 1b(dB)",
        "DeltaF for PUCCH format 2(dB)",
        "Delta preamble value for msg3(2dB)",
        "Delta Message 2(dB)",
    ],
    "PDCCH / Capacity": [
        "SignalCongregateLevel",
        "CCE use ratio(%)",
        "PDCCH Initial Symbol Number",
        "PDCCH Initial Cce Adjustment Value",
        "PDCCH Aggregation Level CL Switch",
        "PDCCH Capacity Improve Switch",
        "PDCCH Max Code Rate",
        "The Strategy Of PDCCH Aggregation Level Adaptation",
        "CCE Usage Threshold To Enable EPDCCH",
        "CCE Usage Threshold To Disable EPDCCH",
    ],
    "PUCCH / SRS / PHICH": [
        "ACK/SRI Channel Number",
        "CQI RB number",
        "Delta shift",
        "Format1 Channel Allocation Mode",
        "Format2 Channel Allocation Mode",
        "Format3 RB Number",
        "SRS Configuration Indicator",
        "SRS Configure Policy Switch",
        "SRS Interference Avoid Optimization Switch",
        "PHICH duration",
        "PHICH resource",
    ],
    "SON / Neighbors": [
        "ANR delete cell threshold(%)",
        "Fast ANR PCI report amount",
        "Fast ANR measurement RSRP threshold(dBm)",
        "Optimization Mode",
        "MRO optimization period(min)",
        "Pingpong handover threshold(s)",
        "Pingpong ratio threshold(%)",
        "Serving cell RSRP threshold(dBm)",
        "Neighbour cell RSRP threshold(dBm)",
        "Control Mode",
        "ANR flag",
        "Neighbour cell name",
    ],
    "Transport / Backhaul": [
        "X2 ID",
        "Control Plane End Point Group ID",
        "User Plane End Point Group ID",
        "Peer Base Station Release",
        "CN Operator ID",
        "SCTP link",
        "IP path",
        "VLAN",
    ],
}


def classify_command(name: str) -> str:
    lowered = name.lower()
    if any(token in lowered for token in ["pdsch", "power", "dl_pc"]):
        return "Signal / RF Power"
    if "cell_pdcch" in lowered or "pdcch" in lowered:
        return "PDCCH / Capacity"
    if any(token in lowered for token in ["pusch", "pucch", "srs", "phich", "ul_pc"]):
        return "Uplink / Physical Channels"
    if any(token in lowered for token in ["timer", "rrc", "drx"]):
        return "Timers / RRC"
    if any(token in lowered for token in ["ho", "neighbor", "eutran", "anr", "mro", "x2"]):
        return "Mobility / SON / Neighbors"
    if any(token in lowered for token in ["ip", "sctp", "route", "vlan"]):
        return "Transport"
    if "cell" in lowered:
        return "Cell Configuration"
    return "System / Other"


def field_rows(command: dict) -> list[tuple[str, str]]:
    rows = []
    for field, values in command.get("fields", {}).items():
        if field == "RETCODE":
            continue
        label = "Table columns" if field == "__table_columns__" else field
        value = ", ".join(str(value) for value in values[:4])
        rows.append((label, value))
    return rows


def render(catalog: dict) -> str:
    successful = [command for command in catalog["commands"] if command.get("success")]
    failed = [command for command in catalog["commands"] if not command.get("success")]
    unique_fields = sorted(
        {
            field
            for command in successful
            for field in command.get("fields", {})
            if field not in {"RETCODE", "__table_columns__"}
        }
    )
    important_found = {
        group: [field for field in fields if field in unique_fields]
        for group, fields in IMPORTANT_FIELDS.items()
    }

    command_cards = []
    for command in successful:
        rows = field_rows(command)
        category = classify_command(command["name"])
        row_html = "\n".join(
            f"<tr><th>{html.escape(field)}</th><td>{html.escape(value)}</td></tr>"
            for field, value in rows
        ) or "<tr><td colspan='2'>No parsed field rows.</td></tr>"
        command_cards.append(
            f"""
            <section class="command-card" data-category="{html.escape(category)}" data-search="{html.escape((command['name'] + ' ' + command['command'] + ' ' + ' '.join(field for field, _ in rows)).lower())}">
              <div class="command-head">
                <div>
                  <p class="eyebrow">{html.escape(category)}</p>
                  <h3>{html.escape(command['name'])}</h3>
                </div>
                <span>{len(rows)} fields</span>
              </div>
              <code>{html.escape(command['command'])}</code>
              <table>{row_html}</table>
            </section>
            """
        )

    important_cards = []
    for group, fields in important_found.items():
        chips = "".join(f"<span>{html.escape(field)}</span>" for field in fields)
        important_cards.append(
            f"""
            <section class="priority-card" data-search="{html.escape((group + ' ' + ' '.join(fields)).lower())}">
              <h3>{html.escape(group)}</h3>
              <p>{len(fields)} discovered high-value fields</p>
              <div class="chips">{chips or '<em>No exact field match in this scan.</em>'}</div>
            </section>
            """
        )

    failed_items = "\n".join(
        f"<li><code>{html.escape(command['command'])}</code><span>{html.escape(command['name'])}</span></li>"
        for command in failed
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Huawei Config Catalog Demo</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07111f;
      --panel: #101c2d;
      --panel-2: #152339;
      --border: #243653;
      --text: #eef5ff;
      --muted: #9eb0c7;
      --accent: #33e6b1;
      --accent-2: #67a7ff;
      --warn: #ffbe55;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.45 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 5;
      border-bottom: 1px solid var(--border);
      background: rgba(7, 17, 31, .94);
      backdrop-filter: blur(12px);
      padding: 18px 28px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 24px; letter-spacing: 0; }}
    h2 {{ margin: 28px 0 14px; font-size: 18px; }}
    h3 {{ margin: 0; font-size: 15px; }}
    p {{ margin: 0; color: var(--muted); }}
    main {{ padding: 24px 28px 48px; max-width: 1500px; margin: 0 auto; }}
    .topline {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; flex-wrap: wrap; }}
    .controls {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-top: 16px; }}
    input, select {{
      background: #0b1628;
      border: 1px solid var(--border);
      color: var(--text);
      border-radius: 8px;
      padding: 10px 12px;
      min-height: 40px;
    }}
    input {{ min-width: min(420px, 100%); flex: 1; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 12px; margin: 20px 0; }}
    .stat, .priority-card, .command-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .stat {{ padding: 16px; }}
    .stat strong {{ display: block; font-size: 24px; color: var(--accent); }}
    .priority-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .priority-card {{ padding: 16px; }}
    .priority-card p {{ margin-top: 4px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }}
    .chips span {{
      border: 1px solid #295245;
      color: #bffbe9;
      background: #09251f;
      border-radius: 999px;
      padding: 5px 8px;
      font-size: 12px;
    }}
    .command-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 14px; }}
    .command-card {{ overflow: hidden; }}
    .command-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
      padding: 14px 16px;
      background: var(--panel-2);
      border-bottom: 1px solid var(--border);
    }}
    .command-head span {{ color: var(--accent-2); white-space: nowrap; }}
    .eyebrow {{ color: var(--accent); font-size: 11px; text-transform: uppercase; margin-bottom: 4px; }}
    code {{
      display: block;
      margin: 12px 16px;
      padding: 10px;
      background: #071222;
      border: 1px solid #1d304c;
      border-radius: 6px;
      color: #d8e7ff;
      white-space: normal;
      overflow-wrap: anywhere;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; vertical-align: top; padding: 9px 16px; border-top: 1px solid #1c2d47; }}
    th {{ width: 46%; color: #dbe7f7; font-weight: 600; }}
    td {{ color: var(--muted); }}
    .failed {{
      background: #100f16;
      border: 1px solid #3a2f43;
      border-radius: 8px;
      padding: 16px;
      color: var(--muted);
    }}
    .failed li {{ margin: 8px 0; }}
    .failed code {{ display: inline; margin: 0 8px 0 0; padding: 2px 5px; }}
    @media (max-width: 760px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .stats {{ grid-template-columns: repeat(2, 1fr); }}
      .command-grid {{ grid-template-columns: 1fr; }}
      th, td {{ display: block; width: 100%; }}
      td {{ padding-top: 0; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>Huawei Config Catalog</h1>
        <p>{html.escape(catalog['site'])} · generated {html.escape(catalog['generated_at'])}</p>
      </div>
      <p id="visibleCount"></p>
    </div>
    <div class="controls">
      <input id="search" type="search" placeholder="Search parameters, commands, groups...">
      <select id="category">
        <option value="">All categories</option>
        <option>Cell Configuration</option>
        <option>Signal / RF Power</option>
        <option>PDCCH / Capacity</option>
        <option>Uplink / Physical Channels</option>
        <option>Timers / RRC</option>
        <option>Mobility / SON / Neighbors</option>
        <option>Transport</option>
        <option>System / Other</option>
      </select>
    </div>
  </header>
  <main>
    <section class="stats">
      <div class="stat"><strong>{catalog['summary']['commands_successful']}</strong><span>successful commands</span></div>
      <div class="stat"><strong>{len(unique_fields)}</strong><span>unique config fields</span></div>
      <div class="stat"><strong>{catalog['summary']['fields_discovered']}</strong><span>raw field groups</span></div>
      <div class="stat"><strong>{len(failed)}</strong><span>unsupported commands</span></div>
    </section>

    <h2>Most Important Fields</h2>
    <section class="priority-grid">{''.join(important_cards)}</section>

    <h2>All Successful Config Views</h2>
    <section class="command-grid" id="cards">{''.join(command_cards)}</section>

    <h2>Unsupported In This Probe</h2>
    <ul class="failed">{failed_items}</ul>
  </main>
  <script>
    const search = document.querySelector('#search');
    const category = document.querySelector('#category');
    const count = document.querySelector('#visibleCount');
    const cards = [...document.querySelectorAll('.command-card')];
    function applyFilters() {{
      const q = search.value.trim().toLowerCase();
      const cat = category.value;
      let visible = 0;
      cards.forEach(card => {{
        const okSearch = !q || card.dataset.search.includes(q);
        const okCategory = !cat || card.dataset.category === cat;
        const show = okSearch && okCategory;
        card.style.display = show ? '' : 'none';
        if (show) visible += 1;
      }});
      count.textContent = `${{visible}} / ${{cards.length}} views visible`;
    }}
    search.addEventListener('input', applyFilters);
    category.addEventListener('change', applyFilters);
    applyFilters();
  </script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    output = args.output or args.catalog.with_suffix(".demo.html")
    output.write_text(render(catalog), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
