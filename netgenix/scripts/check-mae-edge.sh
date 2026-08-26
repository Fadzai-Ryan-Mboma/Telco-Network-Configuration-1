#!/usr/bin/env bash
set -euo pipefail

SSH_TARGET="${NETGENIX_EDGE_SSH_TARGET:-fmboma@10.169.39.39}"
CONTAINER="${NETGENIX_EDGE_TEST_CONTAINER:-netgenix-backend}"

ssh "${SSH_TARGET}" "docker exec -i '${CONTAINER}' python -" <<'PY'
import socket
import ssl
import sys

checks = {
    "access_nbi": ("mae-edge", 33127),
    "access_gui": ("mae-edge", 33143),
    "evaluation_gui": ("mae-edge", 33243),
    "evaluation_nbi": ("mae-edge", 33217),
}

failed = False
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

for name, (host, port) in checks.items():
    try:
        with socket.create_connection((host, port), timeout=8) as raw:
            with context.wrap_socket(raw, server_hostname=host) as secure:
                print(f"{name}: connected ({secure.version()})")
    except Exception as error:
        failed = True
        print(f"{name}: failed ({error})", file=sys.stderr)

raise SystemExit(1 if failed else 0)
PY
