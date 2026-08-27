#!/usr/bin/env bash
set -eEuo pipefail

# Persistent, TLS-transparent MAE edge relay.
#
# This process runs on a host that can reach Huawei MAE. It opens four reverse
# SSH listeners on the VM's Docker host-gateway address. Backend and collector
# containers connect to the hostname `mae-edge`; firewall access is restricted
# to the NetGenix Compose subnet and no MAE listener is exposed on public or
# LAN interfaces.

SSH_TARGET="${NETGENIX_EDGE_SSH_TARGET:-fmboma@10.169.39.39}"
SOURCE_DOCKER_NETWORK="${NETGENIX_EDGE_DOCKER_NETWORK:-netgenix_default}"
LISTENER_DOCKER_NETWORK="${NETGENIX_EDGE_LISTENER_DOCKER_NETWORK:-bridge}"
RETRY_SECONDS="${NETGENIX_EDGE_RETRY_SECONDS:-10}"

ACCESS_HOST="${NETGENIX_EDGE_ACCESS_HOST:-41.174.191.214}"
EVALUATION_HOST="${NETGENIX_EDGE_EVALUATION_HOST:-41.174.191.211}"

ACCESS_NBI_REMOTE_PORT="${NETGENIX_EDGE_ACCESS_NBI_PORT:-33127}"
ACCESS_GUI_REMOTE_PORT="${NETGENIX_EDGE_ACCESS_GUI_PORT:-33143}"
EVALUATION_GUI_REMOTE_PORT="${NETGENIX_EDGE_EVALUATION_GUI_PORT:-33243}"
EVALUATION_NBI_REMOTE_PORT="${NETGENIX_EDGE_EVALUATION_NBI_PORT:-33217}"

log() {
  printf '[mae-edge] %s\n' "$*"
}

resolve_listener_gateway() {
  ssh \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    "${SSH_TARGET}" \
    "docker network inspect '${LISTENER_DOCKER_NETWORK}' --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'"
}

prepare_vm_listener() {
  ssh \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    "${SSH_TARGET}" \
    "sudo -n /usr/local/sbin/netgenix-mae-edge-firewall '${SOURCE_DOCKER_NETWORK}' '${LISTENER_DOCKER_NETWORK}'"
}

valid_ipv4() {
  local address="$1"
  [[ "${address}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]
}

while true; do
  if ! prepare_vm_listener >/dev/null 2>&1; then
    log "VM relay firewall preparation failed; retrying in ${RETRY_SECONDS}s"
    sleep "${RETRY_SECONDS}"
    continue
  fi

  gateway="$(resolve_listener_gateway 2>/dev/null || true)"
  if ! valid_ipv4 "${gateway}"; then
    log "Docker gateway for ${LISTENER_DOCKER_NETWORK} is unavailable; retrying in ${RETRY_SECONDS}s"
    sleep "${RETRY_SECONDS}"
    continue
  fi

  log "Connecting ${SSH_TARGET}; private listener address ${gateway}"
  set +e
  ssh \
    -NT \
    -o BatchMode=yes \
    -o ConnectTimeout=10 \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -R "${gateway}:${ACCESS_NBI_REMOTE_PORT}:${ACCESS_HOST}:31127" \
    -R "${gateway}:${ACCESS_GUI_REMOTE_PORT}:${ACCESS_HOST}:31943" \
    -R "${gateway}:${EVALUATION_GUI_REMOTE_PORT}:${EVALUATION_HOST}:31943" \
    -R "${gateway}:${EVALUATION_NBI_REMOTE_PORT}:${EVALUATION_HOST}:27417" \
    "${SSH_TARGET}"
  exit_code=$?
  set -e

  log "Tunnel exited with code ${exit_code}; retrying in ${RETRY_SECONDS}s"
  sleep "${RETRY_SECONDS}"
done
