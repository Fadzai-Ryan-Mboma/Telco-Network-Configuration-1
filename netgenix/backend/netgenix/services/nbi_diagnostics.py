"""
Huawei iMaster MAE NBI diagnostics.

The checks are deliberately read-only. They validate GUI reachability, NBI
endpoint reachability, and optional login behavior without exposing secrets in
responses or writing credentials into the repo.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


TOKEN_PATH = "/api/rest/securityManagement/v1/oauth/token"
REACHABLE_STATUS_CODES = {200, 301, 302, 401, 403, 405}


@dataclass(frozen=True)
class NBIEnvironment:
    name: str
    gui_url: str
    nbi_base_url: str


def _ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _request(
    url: str,
    *,
    method: str = "GET",
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": response.status in REACHABLE_STATUS_CODES,
                "status_code": response.status,
                "body": body,
                "error": None,
            }
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return {
            "ok": error.code in REACHABLE_STATUS_CODES,
            "status_code": error.code,
            "body": body,
            "error": None,
        }
    except (TimeoutError, socket.timeout) as error:
        return {"ok": False, "status_code": None, "body": "", "error": f"timeout: {error}"}
    except URLError as error:
        reason = getattr(error, "reason", error)
        if isinstance(reason, socket.timeout):
            return {"ok": False, "status_code": None, "body": "", "error": f"timeout: {reason}"}
        return {"ok": False, "status_code": None, "body": "", "error": str(reason)}
    except Exception as error:
        return {"ok": False, "status_code": None, "body": "", "error": str(error)}


def _parse_json(body: str) -> Dict[str, Any]:
    if not body:
        return {}
    try:
        parsed = json.loads(body)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _classify(
    *,
    reachability: Dict[str, Any],
    login: Optional[Dict[str, Any]],
    login_json: Dict[str, Any],
) -> str:
    if login:
        if login.get("error") and "timeout" in login["error"].lower():
            return "timeout"

        if login_json.get("accessSession") or login_json.get("access_token"):
            return "success"

        ret_code = str(login_json.get("retCode", ""))
        ret_message = str(login_json.get("retMessage", ""))
        if ret_code == "90055" or "login failed" in ret_message.lower():
            return "auth_failed"

        if login.get("status_code") == 404:
            return "endpoint_missing"
        if login.get("status_code") == 405:
            return "method_wrong"

    if reachability.get("error") and "timeout" in reachability["error"].lower():
        return "timeout"

    status_code = reachability.get("status_code")
    if status_code == 404:
        return "endpoint_missing"
    if status_code == 405:
        return "method_wrong"

    return "unknown"


def get_default_environments() -> list[NBIEnvironment]:
    return [
        NBIEnvironment(
            name="Access",
            gui_url=os.getenv(
                "NETGENIX_HUAWEI_ACCESS_GUI_URL",
                "https://41.174.191.214:31943/ossfacewebsite/index.html",
            ),
            nbi_base_url=os.getenv(
                "NETGENIX_HUAWEI_ACCESS_NBI_URL",
                "https://41.174.191.214:31127",
            ),
        ),
        NBIEnvironment(
            name="Evaluation",
            gui_url=os.getenv(
                "NETGENIX_HUAWEI_EVALUATION_GUI_URL",
                "https://41.174.191.211:31943/ossfacewebsite/index.html",
            ),
            nbi_base_url=os.getenv(
                "NETGENIX_HUAWEI_EVALUATION_NBI_URL",
                "https://41.174.191.211:27417",
            ),
        ),
    ]


def run_environment_check(environment: NBIEnvironment, timeout: float = 10.0) -> Dict[str, Any]:
    username = os.getenv("NETGENIX_HUAWEI_USERNAME") or os.getenv("HUAWEI_USERNAME")
    password = os.getenv("NETGENIX_HUAWEI_PASSWORD") or os.getenv("HUAWEI_PASSWORD")
    token_url = urljoin(environment.nbi_base_url.rstrip("/") + "/", TOKEN_PATH.lstrip("/"))

    gui = _request(environment.gui_url, method="GET", timeout=timeout)
    reachability = _request(token_url, method="GET", timeout=timeout)

    login = None
    login_json: Dict[str, Any] = {}
    if username and password:
        login = _request(
            token_url,
            method="PUT",
            timeout=timeout,
            payload={
                "grantType": "password",
                "userName": username,
                "value": password,
            },
        )
        login_json = _parse_json(login.get("body", ""))

    classification = _classify(
        reachability=reachability,
        login=login,
        login_json=login_json,
    )

    return {
        "name": environment.name,
        "gui_url": environment.gui_url,
        "nbi_base_url": environment.nbi_base_url,
        "token_url": token_url,
        "gui_reachable": bool(gui["ok"]),
        "gui_status_code": gui.get("status_code"),
        "nbi_reachable": bool(reachability["ok"] or (login and login["ok"])),
        "nbi_status_code": (login or reachability).get("status_code"),
        "classification": classification,
        "ret_code": login_json.get("retCode"),
        "ret_message": login_json.get("retMessage"),
        "error": (login or reachability).get("error"),
        "credentials_supplied": bool(username and password),
    }


def run_nbi_diagnostics(timeout: float = 10.0) -> Dict[str, Any]:
    environments = [run_environment_check(env, timeout=timeout) for env in get_default_environments()]
    return {
        "environments": environments,
        "summary": {
            "success": sum(1 for env in environments if env["classification"] == "success"),
            "auth_failed": sum(1 for env in environments if env["classification"] == "auth_failed"),
            "timeout": sum(1 for env in environments if env["classification"] == "timeout"),
            "unavailable": sum(1 for env in environments if env["classification"] != "success"),
        },
    }
