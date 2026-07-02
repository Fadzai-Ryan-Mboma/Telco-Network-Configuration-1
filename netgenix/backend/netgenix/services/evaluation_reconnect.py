"""Remote-viewable Evaluation login (noVNC + Xvfb) for the Reconnect flow.

Huawei's Evaluation SSO login requires an interactive CAPTCHA, so credentials
alone can never complete authentication server-side. This module reuses the
existing headed-browser login sequence from network.evaluation_exporter
(connect_evaluation) but instead of blocking on a terminal input() prompt, it
points Chromium at a virtual X display (Xvfb) that a human can watch and
control remotely through noVNC in their own browser tab, then polls for login
completion instead of waiting on a synchronous prompt.

Session state (job status, subprocess handles) lives in-memory only: a live
Xvfb/Chromium subprocess tree does not survive a backend restart, so
persisting job rows across restarts would not help recover a session anyway.
Only one reconnect session is supported at a time, which keeps port/display
allocation static and simple — this is a rare, single-operator action, not a
concurrent multi-user feature.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from network.evaluation_exporter import (
    DEFAULT_LOGIN_URL,
    DEFAULT_REPORT_URL,
    _login_form_visible,
    save_session,
)

log = logging.getLogger(__name__)

DISPLAY_NUM = ":99"
VNC_PORT = 5999
WEBSOCKIFY_PORT = 6080
SESSION_TIMEOUT_SECONDS = 10 * 60
LOGIN_POLL_INTERVAL_SECONDS = 1.5
LOGIN_CONFIRM_DELAY_SECONDS = 2.0

_lock = threading.Lock()
_current: Optional["ReconnectSession"] = None


@dataclass
class ReconnectSession:
    session_id: str
    status: str = "starting"  # starting|awaiting_login|session_saved|failed|timeout|cancelled
    error_message: Optional[str] = None
    started_at: float = field(default_factory=time.monotonic)
    _procs: list[subprocess.Popen] = field(default_factory=list)
    _cancel_requested: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "error_message": self.error_message,
            "started_at": self.started_at,
        }


def _spawn(cmd: list[str], **kwargs) -> subprocess.Popen:
    log.info("Starting reconnect subprocess: %s", " ".join(cmd))
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )


def _terminate(proc: subprocess.Popen, *, grace_seconds: float = 3.0) -> None:
    if proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        proc.kill()
    except ProcessLookupError:
        pass


def _kill_chromium_on_display() -> None:
    # Playwright's Browser object doesn't expose the underlying OS process (it
    # drives Chromium over CDP through its own Node driver subprocess), and
    # browser.close()'s graceful CDP shutdown does not reliably reap every
    # renderer/gpu/crashpad-handler child under Xvfb + --no-sandbox. Since
    # nothing else in this container uses DISPLAY=:99, it's safe to force-kill
    # anything still attached to it as a teardown safety net. No `pkill`
    # binary is installed in this image, so match against /proc directly.
    try:
        proc_root = "/proc"
        for entry in os.listdir(proc_root):
            if not entry.isdigit():
                continue
            pid = int(entry)
            try:
                with open(f"{proc_root}/{entry}/environ", "rb") as fh:
                    environ = fh.read()
                if f"DISPLAY={DISPLAY_NUM}".encode() not in environ.split(b"\0"):
                    continue
                with open(f"{proc_root}/{entry}/comm") as fh:
                    comm = fh.read().strip()
                if comm in {"Xvfb", "fluxbox", "x11vnc", "websockify"}:
                    continue  # already terminated via their tracked Popen handles above
                os.kill(pid, signal.SIGKILL)
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
    except OSError as exc:
        log.warning("Could not scan /proc for stray Chromium processes: %s", exc)


def _teardown(session: ReconnectSession) -> None:
    for proc in reversed(session._procs):
        _terminate(proc)
    session._procs.clear()
    _kill_chromium_on_display()


def _start_display_stack(session: ReconnectSession) -> None:
    session._procs.append(
        _spawn(["Xvfb", DISPLAY_NUM, "-screen", "0", "1280x800x24"])
    )
    time.sleep(1.0)  # let the X socket appear before anything connects to it

    session._procs.append(
        _spawn(["fluxbox"], env={**os.environ, "DISPLAY": DISPLAY_NUM})
    )
    session._procs.append(
        _spawn(
            [
                "x11vnc",
                "-display", DISPLAY_NUM,
                "-forever",
                "-shared",
                "-rfbport", str(VNC_PORT),
                "-nopw",
            ]
        )
    )
    session._procs.append(
        _spawn(
            [
                "websockify",
                "--web", "/usr/share/novnc",
                str(WEBSOCKIFY_PORT),
                f"localhost:{VNC_PORT}",
            ]
        )
    )
    time.sleep(1.0)  # let x11vnc/websockify bind before Chromium connects


def _run_login_flow(session: ReconnectSession) -> None:
    from playwright.sync_api import sync_playwright

    login_url = os.getenv("MAE_GUI_LOGIN_URL", DEFAULT_LOGIN_URL)
    report_url = os.getenv(
        "NETGENIX_HUAWEI_EVALUATION_GUI_URL",
        os.getenv("MAE_GUI_URL", DEFAULT_REPORT_URL),
    )
    deadline = time.monotonic() + SESSION_TIMEOUT_SECONDS

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=False,
                env={**os.environ, "DISPLAY": DISPLAY_NUM},
            )
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)
            session.status = "awaiting_login"

            # Wait for the login form to disappear (SSO redirected away),
            # then re-check after a short delay to guard against a transient
            # blip, then confirm on the report page — the same confirmation
            # connect_evaluation() already performs today, just polled
            # instead of gated behind a single human keypress.
            login_done = False
            while time.monotonic() < deadline and not session._cancel_requested:
                if not _login_form_visible(page):
                    page.wait_for_timeout(int(LOGIN_CONFIRM_DELAY_SECONDS * 1000))
                    if not _login_form_visible(page):
                        login_done = True
                        break
                page.wait_for_timeout(int(LOGIN_POLL_INTERVAL_SECONDS * 1000))

            if session._cancel_requested:
                session.status = "cancelled"
                context.close()
                browser.close()
                return

            if not login_done:
                session.status = "timeout"
                session.error_message = "Login was not completed within the time limit."
                context.close()
                browser.close()
                return

            page.goto(report_url, wait_until="domcontentloaded", timeout=60_000)
            if _login_form_visible(page):
                session.status = "failed"
                session.error_message = "Evaluation login was not completed."
                context.close()
                browser.close()
                return

            save_session(context)
            context.close()
            browser.close()
            session.status = "session_saved"
    except Exception as exc:  # noqa: BLE001 - surface any Playwright/browser error to the UI
        log.exception("Evaluation reconnect login flow failed")
        session.status = "failed"
        session.error_message = str(exc)
    finally:
        _teardown(session)


def start_reconnect_session() -> dict[str, object]:
    global _current
    with _lock:
        if _current is not None and _current.status in ("starting", "awaiting_login"):
            raise RuntimeError("A reconnect session is already running.")
        session = ReconnectSession(session_id=str(uuid.uuid4()))
        _current = session

    try:
        _start_display_stack(session)
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to start reconnect display stack")
        session.status = "failed"
        session.error_message = str(exc)
        _teardown(session)
        return session.to_dict()

    thread = threading.Thread(
        target=_run_login_flow,
        args=(session,),
        daemon=True,
        name=f"reconnect-{session.session_id[:8]}",
    )
    thread.start()
    return {**session.to_dict(), "novnc_url": "/vnc/vnc.html?path=vnc&autoconnect=true&resize=scale"}


def get_reconnect_status(session_id: str) -> Optional[dict[str, object]]:
    if _current is None or _current.session_id != session_id:
        return None
    return _current.to_dict()


def cancel_reconnect_session(session_id: str) -> Optional[dict[str, object]]:
    if _current is None or _current.session_id != session_id:
        return None
    _current._cancel_requested = True
    return _current.to_dict()
