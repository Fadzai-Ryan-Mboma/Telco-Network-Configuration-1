"""Authenticated Playwright exporter for Huawei MAE Evaluation reports."""

from __future__ import annotations

import csv
import io
import json
import os
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv
from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Frame,
    FrameLocator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
DEFAULT_LOGIN_URL = (
    "https://41.174.191.211:31943/unisso/login.action?"
    "service=%2Funisess%2Fv1%2Fauth%3Fservice%3D%252Fossfacewebsite%252Findex.html&decision=1"
)
DEFAULT_REPORT_URL = (
    "https://41.174.191.211:31943/ossfacewebsite/index.html#"
    "Evaluation/prs_reportmanagement_reportList"
)
DEFAULT_REPORT_NAME = "LTZIM LTE Main KPIs Report_2"
SESSION_PATH = Path(os.getenv("EVALUATION_SESSION_PATH", PROJECT_ROOT / "data" / "evaluation-session.enc"))
SESSION_INVALID_PATH = SESSION_PATH.with_suffix(SESSION_PATH.suffix + ".invalid")
SESSION_KEY_PATH = Path(
    os.getenv("EVALUATION_SESSION_KEY_PATH", PROJECT_ROOT / "data" / "evaluation-session.key")
)
DOWNLOAD_ROOT = Path(os.getenv("MAE_DOWNLOAD_DIR", PROJECT_ROOT / "data" / "downloads"))


class EvaluationSessionError(RuntimeError):
    """The saved Evaluation browser session is missing, invalid, or expired."""


@dataclass(frozen=True)
class EvaluationExport:
    zip_path: Path
    period_start: date
    period_end: date
    downloaded_at: datetime


def default_week_period(today: date | None = None) -> tuple[date, date]:
    """Return the most recently completed Thursday-Wednesday period."""
    today = today or datetime.now().astimezone().date()
    days_since_wednesday = (today.weekday() - 2) % 7
    end = today - timedelta(days=days_since_wednesday or 7)
    return end - timedelta(days=6), end


def default_daily_rolling_period(today: date | None = None) -> tuple[date, date]:
    """Return the most recently completed 7-day window ending yesterday."""
    today = today or datetime.now().astimezone().date()
    end = today - timedelta(days=1)
    return end - timedelta(days=6), end


def validate_period(start: date, end: date, *, allowed_days: tuple[int, ...] = (7, 14)) -> int:
    days = (end - start).days + 1
    if days not in allowed_days:
        allowed = " or ".join(str(value) for value in allowed_days)
        raise ValueError(f"Evaluation period must contain exactly {allowed} days")
    if end >= datetime.now().astimezone().date():
        raise ValueError("Evaluation period must end before today")
    return days


def _fernet(*, create: bool = False) -> Fernet:
    key = ""
    if SESSION_KEY_PATH.exists():
        key = SESSION_KEY_PATH.read_text(encoding="ascii").strip()
    elif os.getenv("EVALUATION_SESSION_KEY", "").strip():
        key = os.getenv("EVALUATION_SESSION_KEY", "").strip()
    elif create:
        SESSION_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key().decode("ascii")
        SESSION_KEY_PATH.write_text(key, encoding="ascii")
        SESSION_KEY_PATH.chmod(0o600)
    else:
        raise EvaluationSessionError("Evaluation session encryption key is not configured")
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError) as exc:
        raise EvaluationSessionError("EVALUATION_SESSION_KEY is not a valid Fernet key") from exc


def save_session(context: BrowserContext, path: Path = SESSION_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = json.dumps(context.storage_state()).encode("utf-8")
    path.write_bytes(_fernet(create=True).encrypt(state))
    path.chmod(0o600)
    SESSION_INVALID_PATH.unlink(missing_ok=True)


def mark_session_invalid(reason: str) -> None:
    SESSION_INVALID_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSION_INVALID_PATH.write_text(reason, encoding="utf-8")
    SESSION_INVALID_PATH.chmod(0o600)


def load_session(path: Path = SESSION_PATH) -> dict[str, object]:
    if not path.exists():
        raise EvaluationSessionError("Evaluation is not connected; run connect-evaluation first")
    try:
        return json.loads(_fernet().decrypt(path.read_bytes()).decode("utf-8"))
    except (InvalidToken, OSError, json.JSONDecodeError) as exc:
        raise EvaluationSessionError("Saved Evaluation session cannot be decrypted") from exc


def _evaluation_frame(page: Page) -> FrameLocator:
    return page.frame_locator('iframe[title="Evaluation"]').frame_locator("#maos_main iframe")


def _login_form_visible(page: Page) -> bool:
    username = page.get_by_role("textbox", name="Username")
    return bool(username.count() and username.is_visible())


def _find_visible_frame(page: Page, selector: str, *, timeout: float = 10) -> Frame:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for frame in page.frames:
            try:
                match = frame.locator(selector)
                if match.count() and match.first.is_visible():
                    return frame
            except PlaywrightError:
                continue
        page.wait_for_timeout(200)
    raise RuntimeError(f"Evaluation frame containing {selector!r} was not found")


def _find_visible_text_frame(page: Page, text: str, *, timeout: float = 10) -> Frame:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for frame in page.frames:
            try:
                match = frame.get_by_text(text, exact=True)
                if match.count() and match.first.is_visible():
                    return frame
            except PlaywrightError:
                continue
        page.wait_for_timeout(200)
    raise RuntimeError(f"Evaluation frame containing visible text {text!r} was not found")


def _open_report(page: Page, report_name: str) -> Frame:
    report_list = _evaluation_frame(page)
    search = report_list.get_by_role("textbox", name="Enter a report name")
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if _login_form_visible(page):
            raise EvaluationSessionError("Evaluation session expired; reconnect before refreshing")
        try:
            if search.count() and search.is_visible():
                break
        except PlaywrightError:
            pass
        page.wait_for_timeout(500)
    else:
        raise RuntimeError("Evaluation report list did not finish loading")
    search.click()
    search.fill("")
    search.type(report_name, delay=25)
    search.press("Enter")
    report_name_cell = report_list.get_by_text(report_name, exact=True)
    report_name_cell.wait_for(state="attached", timeout=30_000)
    report_row = report_name_cell.locator("xpath=ancestor::*[@role='row' or self::tr][1]")
    query_action = report_row.locator("#query_by_condition")
    action_count = query_action.count()
    if action_count != 1:
        raise RuntimeError(
            "Evaluation report query action was not uniquely identified "
            f"(report cells: {report_name_cell.count()}, actions: {action_count})"
        )
    # Huawei reveals this action only while its result row is hovered.
    report_name_cell.hover(force=True)
    query_action.wait_for(state="visible", timeout=5_000)
    query_action.click()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        for frame in page.frames:
            if frame.get_by_text("Whole Network Main KPIs", exact=True).count():
                return frame
        page.wait_for_timeout(250)
    raise RuntimeError("Evaluation report query frame did not open")


def _set_section_period(report: Frame, section_name: str, start: date, end: date) -> None:
    """Set an exact fixed period in one report section's time dialog."""
    section = report.locator("span").filter(has_text=section_name)
    if section.count() != 1:
        raise RuntimeError(f"Evaluation section {section_name!r} was not uniquely identified")
    section.click()
    expected_count = 1 if section_name == "Whole Network Main KPIs" else 2
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        section_iframes = report.locator("iframe[src*='/new-report/sub-report.html']")
        if section_iframes.count() >= expected_count:
            break
        report.page.wait_for_timeout(200)
    frame_count = section_iframes.count()
    if frame_count not in (1, 2):
        raise RuntimeError(
            f"Expected loaded frame for {section_name}, found {frame_count}"
        )
    section_index = 0 if frame_count == 1 or section_name == "Whole Network Main KPIs" else 1
    frame_handle = section_iframes.nth(section_index).element_handle()
    section_frame = frame_handle.content_frame() if frame_handle else None
    if section_frame is None:
        raise RuntimeError(f"Evaluation frame for {section_name} is not attached")
    section_frame.get_by_text("Select Time", exact=True).evaluate("element => element.click()")
    report.page.wait_for_timeout(500)

    dialog = _find_visible_frame(report.page, "#continuousSelectTime")
    absolute_period = dialog.locator("#SAbsoluteTime")
    if absolute_period.count() != 1:
        raise RuntimeError(f"Evaluation absolute-period mode was not found in {section_name}")
    absolute_period.check()

    date_inputs = dialog.locator(".eui-datepicker-input")
    if date_inputs.count() < 2:
        raise RuntimeError("Evaluation fixed-period date inputs were not found")
    set_date = """(element, value) => {
        element.value = value;
        element.title = value;
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
    }"""
    date_inputs.nth(0).evaluate(set_date, start.strftime("%Y-%m-%d"))
    date_inputs.nth(1).evaluate(set_date, end.strftime("%Y-%m-%d"))
    _find_visible_frame(report.page, "#okBtn").locator("#okBtn").evaluate(
        "element => element.click()"
    )


def _download_report(page: Page, report: Frame, destination: Path) -> Path:
    query_button = report.locator("#query-report-button")
    result_page = None
    for direct in (False, True):
        try:
            with page.expect_popup(timeout=60_000) as popup_info:
                if direct:
                    query_button.evaluate("element => element.click()")
                else:
                    query_button.click()
            result_page = popup_info.value
            break
        except PlaywrightTimeoutError:
            continue
    if result_page is None:
        raise RuntimeError("Evaluation query did not open a result window after retry")
    result = result_page.frame_locator('iframe[title="ReportQuery-Report Query"]')
    export_action = result.locator("a.exportRpt")
    export_action.wait_for(state="visible", timeout=30_000)
    export_action.hover()
    page.wait_for_timeout(500)
    try:
        export_action.click()
    except PlaywrightTimeoutError:
        export_action.evaluate("element => element.click()")
    page.wait_for_timeout(2_000)

    export_panels = result.locator(".prs_export_list")
    if export_panels.count() < 2:
        export_action.evaluate("element => element.click()")
        page.wait_for_timeout(2_000)
        if export_panels.count() < 2:
            raise RuntimeError("Evaluation export dialog did not render the expected panel set")
    export_panel = export_panels.last

    file_type_picker = export_panel.locator(".combox").first
    if file_type_picker.count() != 1:
        raise RuntimeError("Evaluation export file-type picker was not found")
    try:
        file_type_picker.click(force=True)
    except PlaywrightTimeoutError:
        file_type_picker.evaluate("element => element.click()")
    page.wait_for_timeout(500)

    csv_options = export_panel.locator('.popdiv .item[title="CSV File(*.csv)"]')
    if csv_options.count() < 1:
        raise RuntimeError("Evaluation CSV export option was not found")
    csv_option = csv_options.first
    for index in range(csv_options.count()):
        candidate = csv_options.nth(index)
        try:
            if candidate.is_visible(timeout=1_000):
                csv_option = candidate
                break
        except PlaywrightTimeoutError:
            continue
    csv_label = csv_option.locator("label")
    target = csv_label.first if csv_label.count() else csv_option
    try:
        target.click(force=True)
    except PlaywrightTimeoutError:
        target.evaluate("element => element.click()")
    ok_frame = _find_visible_text_frame(result_page, "OK")
    ok_frame.get_by_text("OK", exact=True).click()

    zip_link = result_page.get_by_text(re.compile(r"LTZIM.*\.zip$", re.I)).last
    # Huawei generates the export asynchronously. Large cell-level periods can
    # take longer than Playwright's default 30-second action timeout before the
    # ZIP link appears, even though the download itself already allows 180s.
    zip_link.wait_for(state="visible", timeout=180_000)
    with result_page.expect_download(timeout=180_000) as download_info:
        zip_link.click(timeout=180_000)
    destination.parent.mkdir(parents=True, exist_ok=True)
    download_info.value.save_as(str(destination))
    result_page.close()
    return destination


def _validate_downloaded_period(zip_path: Path, start: date, end: date) -> None:
    ranges: dict[str, tuple[date, date]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            name = member.filename
            section = next(
                (value for value in ("Whole Network Main KPIs", "Cell Level KPIs") if value in name),
                None,
            )
            if section is None or not name.lower().endswith(".csv"):
                continue
            dates: list[date] = []
            with archive.open(member) as raw, io.TextIOWrapper(
                raw, encoding="utf-8-sig", errors="replace", newline=""
            ) as stream:
                rows = csv.reader(stream)
                for row in rows:
                    if not row or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row[0].strip()):
                        continue
                    dates.append(date.fromisoformat(row[0].strip()))
            if dates:
                ranges[section] = (min(dates), max(dates))
    expected = (start, end)
    for section in ("Whole Network Main KPIs", "Cell Level KPIs"):
        if ranges.get(section) != expected:
            raise RuntimeError(
                f"Evaluation {section} export period was {ranges.get(section)}, expected {expected}"
            )


def export_evaluation_report(
    start: date,
    end: date,
    *,
    headless: bool = True,
    report_name: str | None = None,
    download_root: Path = DOWNLOAD_ROOT,
) -> EvaluationExport:
    """Export whole-network and cell-level CSVs in one Evaluation ZIP."""
    validate_period(start, end)
    report_name = report_name or os.getenv("EVALUATION_REPORT_NAME", DEFAULT_REPORT_NAME)
    report_url = os.getenv(
        "NETGENIX_HUAWEI_EVALUATION_GUI_URL",
        os.getenv("MAE_GUI_URL", DEFAULT_REPORT_URL),
    )
    timestamp = datetime.now(timezone.utc)
    run_dir = download_root / timestamp.strftime("%Y%m%dT%H%M%SZ")
    destination = run_dir / f"evaluation_{start.isoformat()}_{end.isoformat()}.zip"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            ignore_https_errors=True,
            storage_state=load_session(),
        )
        page = context.new_page()
        try:
            page.goto(report_url, wait_until="domcontentloaded", timeout=60_000)
            if _login_form_visible(page):
                raise EvaluationSessionError("Evaluation session expired; reconnect before refreshing")
            report_navigation = page.locator("#ModifyAppEntryWidthEvaluation").get_by_text(
                "Report Management"
            )
            if report_navigation.count() and report_navigation.is_visible():
                report_navigation.click()
            report = _open_report(page, report_name)
            _set_section_period(report, "Whole Network Main KPIs", start, end)
            _set_section_period(report, "Cell Level KPIs", start, end)
            _download_report(page, report, destination)
            _validate_downloaded_period(destination, start, end)
            save_session(context)
        finally:
            context.close()
            browser.close()
    return EvaluationExport(destination, start, end, timestamp)


def connect_evaluation() -> None:
    """Launch an operator-visible login and save its authenticated session."""
    login_url = os.getenv("MAE_GUI_LOGIN_URL", DEFAULT_LOGIN_URL)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)
        input("Complete Evaluation login (including CAPTCHA), then press Enter here: ")
        report_url = os.getenv(
            "NETGENIX_HUAWEI_EVALUATION_GUI_URL",
            os.getenv("MAE_GUI_URL", DEFAULT_REPORT_URL),
        )
        page.goto(report_url, wait_until="domcontentloaded", timeout=60_000)
        if _login_form_visible(page):
            raise EvaluationSessionError("Evaluation login was not completed")
        save_session(context)
        context.close()
        browser.close()


def session_status(path: Path = SESSION_PATH) -> dict[str, object]:
    if not path.exists():
        return {"connected": False, "reason": "not_connected", "updated_at": None}
    if SESSION_INVALID_PATH.exists():
        return {
            "connected": False,
            "reason": SESSION_INVALID_PATH.read_text(encoding="utf-8").strip() or "session_expired",
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        }
    try:
        load_session(path)
    except EvaluationSessionError as exc:
        return {
            "connected": False,
            "reason": str(exc),
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        }
    return {
        "connected": True,
        "reason": None,
        "updated_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
    }
