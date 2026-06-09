"""
MAE GUI Collector — headless Playwright bot that exports KPI CSVs from
Huawei iMaster MAE-Evaluation and loads them into TimescaleDB.

Two extract modes
-----------------
hourly  : last 1 hour   — feeds the live NetGenix dashboard
weekly  : last 7 days   — feeds the weekly report generator

CAPTCHA
-------
Login CAPTCHA is solved via Gemini Vision:
  1. Screenshot the CAPTCHA element
  2. POST to Gemini Vision API
  3. Type the returned text into the CAPTCHA field

Environment variables
---------------------
MAE_GUI_URL      e.g. http://41.174.191.211:31943
MAE_USERNAME
MAE_PASSWORD
GEMINI_API_KEY
DATABASE_URL     (or DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD)
MAE_DOWNLOAD_DIR (optional, default: data/downloads)
"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import pandas as pd
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from playwright.sync_api import Page, sync_playwright

load_dotenv()

log = logging.getLogger(__name__)

REPO_ROOT    = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = Path(os.getenv("MAE_DOWNLOAD_DIR", str(REPO_ROOT / "data" / "downloads")))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAE_URL      = os.getenv("MAE_GUI_URL", "http://41.174.191.211:31943")
MAE_USER     = os.getenv("MAE_USERNAME", "")
MAE_PASS     = os.getenv("MAE_PASSWORD", "")

ExtractMode  = Literal["hourly", "weekly"]


# ─────────────────────────────────────────────────────────────────────────────
# CAPTCHA solver
# ─────────────────────────────────────────────────────────────────────────────

def _solve_captcha_with_gemini(screenshot_bytes: bytes) -> str:
    """Send CAPTCHA screenshot to Gemini Vision and return the solved text."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash")

    img_b64 = base64.b64encode(screenshot_bytes).decode()
    response = model.generate_content([
        {
            "parts": [
                {"text": "This is a CAPTCHA image from a network management system login page. "
                         "Read the alphanumeric characters exactly as shown. "
                         "Return ONLY the characters, no spaces, no explanation."},
                {"inline_data": {"mime_type": "image/png", "data": img_b64}},
            ]
        }
    ])
    text = response.text.strip()
    # Strip any accidental whitespace or punctuation the model might add
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    log.info("CAPTCHA solved: %s", text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Login flow
# ─────────────────────────────────────────────────────────────────────────────

def _login(page: Page, max_attempts: int = 3) -> None:
    """Navigate to MAE and log in, solving the CAPTCHA."""
    page.goto(MAE_URL, wait_until="domcontentloaded", timeout=30_000)

    for attempt in range(1, max_attempts + 1):
        log.info("Login attempt %d/%d", attempt, max_attempts)

        # Fill credentials
        page.fill("input[name='username'], input#username", MAE_USER)
        page.fill("input[name='password'], input#password", MAE_PASS)

        # Locate CAPTCHA image and screenshot it
        captcha_img = page.locator("img.captcha, img[alt*='captcha'], img[alt*='CAPTCHA'], #captchaImg").first
        captcha_img.wait_for(state="visible", timeout=10_000)
        captcha_bytes = captcha_img.screenshot()

        # Solve and fill
        captcha_text = _solve_captcha_with_gemini(captcha_bytes)
        captcha_input = page.locator(
            "input[name='captcha'], input#captcha, input[placeholder*='aptcha']"
        ).first
        captcha_input.fill(captcha_text)

        # Submit
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle", timeout=15_000)

        # Check whether login succeeded
        if page.url != MAE_URL and "login" not in page.url.lower():
            log.info("Login successful on attempt %d", attempt)
            return

        log.warning("Login failed — CAPTCHA may be wrong, refreshing …")
        page.goto(MAE_URL, wait_until="domcontentloaded", timeout=30_000)
        time.sleep(1)

    raise RuntimeError(f"MAE login failed after {max_attempts} attempts")


# ─────────────────────────────────────────────────────────────────────────────
# Export flow  (adapt selectors once the actual GUI has been inspected)
# ─────────────────────────────────────────────────────────────────────────────

def _navigate_to_kpi_report(page: Page) -> None:
    """Click through the MAE GUI to reach the KPI report export page."""
    # Example path — adjust to match the actual MAE menu structure
    page.click("text=Performance")
    page.wait_for_load_state("networkidle", timeout=10_000)
    page.click("text=KPI Report")
    page.wait_for_load_state("networkidle", timeout=10_000)


def _set_time_range(page: Page, mode: ExtractMode) -> tuple[datetime, datetime]:
    """Set the report time range and return (period_start, period_end)."""
    now = datetime.now(tz=timezone.utc)
    if mode == "hourly":
        start = now - timedelta(hours=1)
    else:  # weekly
        start = now - timedelta(days=7)

    # Format for MAE date/time pickers (adjust format if needed)
    fmt = "%Y-%m-%d %H:%M"
    page.fill("input#startTime, input[placeholder*='Start']", start.strftime(fmt))
    page.fill("input#endTime,   input[placeholder*='End']",   now.strftime(fmt))
    return start, now


def _trigger_export_and_download(page: Page, mode: ExtractMode) -> Path:
    """Click Export / Query, wait for the ZIP download, return the local path."""
    with page.expect_download(timeout=120_000) as dl_info:
        page.click("button:has-text('Export'), button:has-text('Query')")
    download = dl_info.value

    dest = DOWNLOAD_DIR / f"mae_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    download.save_as(str(dest))
    log.info("Downloaded: %s", dest)
    return dest


def _extract_csv_from_zip(zip_path: Path) -> list[tuple[str, pd.DataFrame]]:
    """Extract all CSVs from the ZIP, parse and return [(filename, DataFrame)]."""
    results = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as fh:
                raw = fh.read()
            # Try utf-8-sig first (Huawei MAE standard), fall back to gbk
            for enc in ("utf-8-sig", "gbk", "utf-8"):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            df = pd.read_csv(io.StringIO(text), skiprows=5)
            # Drop footer
            if not df.empty:
                last = df.iloc[-1]
                if pd.isna(last.iloc[2]) or str(last.iloc[0]).strip().lower().startswith("end"):
                    df = df.iloc[:-1]
            results.append((name, df))
            log.info("  Parsed %s: %d rows", name, len(df))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers  (identical column mapping as ingest_csv_to_timescaledb.py)
# ─────────────────────────────────────────────────────────────────────────────

def _get_conn():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5433)),
        dbname=os.getenv("DB_NAME", "netgenix"),
        user=os.getenv("DB_USER", "netgenix"),
        password=os.getenv("DB_PASSWORD", "netgenix_secure_2026"),
    )


def _to_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _parse_ts(val) -> datetime:
    dt = pd.to_datetime(val, dayfirst=False, errors="coerce")
    if pd.isna(dt):
        raise ValueError(f"Bad timestamp: {val!r}")
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


CELL_INSERT = """
INSERT INTO kpi_cell (
    time, enodeb_name, cell_name, local_cell_id, enodeb_function_name, cell_fdd_tdd,
    integrity, radio_net_availability_rate,
    rrc_setup_success_rate_all, rrc_setup_success_rate_service, rrc_setup_success_rate_signal,
    erab_setup_success_rate, call_drop_rate,
    ho_success_rate_intra_freq, ho_success_rate_s1, paging_transfer_success_rate,
    total_traffic_gbit, dl_traffic_volume_gbit, ul_traffic_volume_gbit,
    l_traffic_user_avg, l_traffic_user_max,
    user_dl_pdcp_avg_throughput, user_ul_pdcp_avg_throughput,
    dl_ibler, ul_ibler, dl_retrans_rate, dl_packet_loss_rate, ul_packet_loss_rate,
    dl_prb_usage_rate, ul_prb_usage_rate, pucch_usage_rate, pdcch_cce_usage_rate,
    average_cqi, average_pdsch_mcs, data_access_time_ms, total_cell_unavail_duration_s,
    granularity, data_source
) VALUES %s
ON CONFLICT (time, cell_name, granularity) DO NOTHING
"""


def _build_cell_rows(df: pd.DataFrame, granularity: str, source: str) -> list[tuple]:
    rows = []
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    for _, r in df.iterrows():
        try:
            ts = _parse_ts(r[date_col])
        except ValueError:
            continue
        rows.append((
            ts,
            str(r.get("eNodeB Name", "")).strip(),
            str(r.get("Cell Name", "")).strip(),
            _to_int(r.get("LocalCell Id")),
            str(r.get("eNodeB Function Name", "")).strip() or None,
            str(r.get("Cell FDD TDD Indication", "")).strip() or None,
            str(r.get("Integrity", "")).strip() or None,
            _to_float(r.get("Radio Net Availability Rate(%)")),
            _to_float(r.get("RRC Setup Success Rate(all)")),
            _to_float(r.get("RRC Setup Success Rate(Service)[%]")),
            _to_float(r.get("RRC Setup Success Rate(Signal)[%]")),
            _to_float(r.get("E-RAB Setup Success Rate (ALL)(%)")),
            _to_float(r.get("Call Drop Rate (All)(%)")),
            _to_float(r.get("HO Success Rate(Intra Freqency)")),
            _to_float(r.get("HO Success Rate(S1)[%]")),
            _to_float(r.get("Paging Transfer Success Rate")),
            _to_float(r.get("Total Traffic (Gbit)")),
            _to_float(r.get("DL Traffic Volume(Gbit)")),
            _to_float(r.get("UL Traffic Volume(Gbit)")),
            _to_float(r.get("L.Traffic.User.Avg")),
            _to_float(r.get("L.Traffic.User.Max")),
            _to_float(r.get("User DL PDCP Average Throughput")),
            _to_float(r.get("User UL PDCP Average Throughput")),
            _to_float(r.get("DL IBLER[%]")),
            _to_float(r.get("UL IBLER[%]")),
            _to_float(r.get("DL ReTrans Rate[%]")),
            _to_float(r.get("DL Packet Loss Rate(all)")),
            _to_float(r.get("UL Packet Loss Rate(all)")),
            _to_float(r.get("DL PRB Usage Rate(%)")),
            _to_float(r.get("UL PRB Usage Rate(%)")),
            _to_float(r.get("PUCCHUsage Rate[%]")),
            _to_float(r.get("PDCCH CCE Usage Rate[%]")),
            _to_float(r.get("Average CQI")),
            _to_float(r.get("Average PDSCH MCS")),
            _to_float(r.get("Data Access Time (ms)")),
            _to_float(r.get("Total Cell Unavail Duration(s)")),
            granularity,
            source,
        ))
    return rows


def _upsert_to_db(rows: list[tuple], period_start: datetime, period_end: datetime,
                  mode: ExtractMode, source: str) -> None:
    if not rows:
        log.warning("No rows to insert")
        return

    conn = _get_conn()
    cur  = conn.cursor()
    BATCH = 2000
    inserted = 0
    for i in range(0, len(rows), BATCH):
        psycopg2.extras.execute_values(cur, CELL_INSERT, rows[i : i + BATCH], page_size=BATCH)
        conn.commit()
        inserted += cur.rowcount if cur.rowcount >= 0 else len(rows[i : i + BATCH])

    cur.execute(
        """INSERT INTO ingestion_log
               (source, granularity, period_start, period_end, rows_inserted, rows_skipped, status)
           VALUES (%s, %s, %s, %s, %s, %s, 'ok')""",
        (source, mode, period_start, period_end, inserted, len(rows) - inserted),
    )
    conn.commit()
    cur.close()
    conn.close()
    log.info("Upserted %d rows (mode=%s)", inserted, mode)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_collection(mode: ExtractMode = "hourly", headless: bool = True) -> None:
    """
    Full collect cycle:
      login → navigate → set time range → export → download → parse → upsert
    """
    source = f"mae_bot_{mode}"
    log.info("Starting MAE collection — mode=%s headless=%s", mode, headless)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()

        try:
            _login(page)
            _navigate_to_kpi_report(page)
            period_start, period_end = _set_time_range(page, mode)
            zip_path = _trigger_export_and_download(page, mode)
        finally:
            browser.close()

    csvs = _extract_csv_from_zip(zip_path)
    granularity = "hourly" if mode == "hourly" else "daily"

    all_rows: list[tuple] = []
    for _name, df in csvs:
        # Skip network-aggregate CSVs (no cell_name column)
        if "Cell Name" not in df.columns:
            continue
        all_rows.extend(_build_cell_rows(df, granularity, source))

    _upsert_to_db(all_rows, period_start, period_end, mode, source)
    log.info("Collection complete — mode=%s  rows=%d", mode, len(all_rows))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
    )
    parser = argparse.ArgumentParser(description="MAE GUI KPI collector")
    parser.add_argument("--mode", choices=["hourly", "weekly"], default="hourly")
    parser.add_argument("--no-headless", action="store_true")
    args = parser.parse_args()

    run_collection(mode=args.mode, headless=not args.no_headless)
