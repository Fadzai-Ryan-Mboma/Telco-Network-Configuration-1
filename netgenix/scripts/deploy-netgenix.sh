#!/usr/bin/env bash
set -eEuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETGENIX_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${NETGENIX_DIR}/.." && pwd)"

DRY_RUN=0
PREFLIGHT_ONLY=0
SYNC_ENV=1
RUN_LOCAL_SMOKE="${NETGENIX_RUN_LOCAL_SMOKE:-0}"

NETGENIX_DEPLOY_BRANCH="${NETGENIX_DEPLOY_BRANCH:-netgenix}"
NETGENIX_DEPLOY_REMOTE="${NETGENIX_DEPLOY_REMOTE:-origin}"
NETGENIX_VM_SSH_TARGET="${NETGENIX_VM_SSH_TARGET:-}"
NETGENIX_VM_REPO_ROOT="${NETGENIX_VM_REPO_ROOT:-~/Cassava AI/Telco-Network-Configuration}"
NETGENIX_VM_DATA_DIR="${NETGENIX_VM_DATA_DIR:-~/netgenix-data}"
NETGENIX_REMOTE_APP_SUBDIR="${NETGENIX_REMOTE_APP_SUBDIR:-netgenix}"
NETGENIX_LOCAL_ENV_FILE="${NETGENIX_LOCAL_ENV_FILE:-${NETGENIX_DIR}/.env}"
NETGENIX_TEST_TIMEOUT="${NETGENIX_TEST_TIMEOUT:-180}"
NETGENIX_TEST_COMMAND="${NETGENIX_TEST_COMMAND:-python3 -m unittest tests.test_evaluation_automation}"
NETGENIX_REMOTE_BACKEND_URL="${NETGENIX_REMOTE_BACKEND_URL:-http://127.0.0.1:8510}"
NETGENIX_REMOTE_FRONTEND_URL="${NETGENIX_REMOTE_FRONTEND_URL:-http://127.0.0.1:8511}"
RELEASE_PATHS=(netgenix Makefile)

usage() {
  cat <<'EOF'
Usage: ./scripts/deploy-netgenix.sh [options]

Options:
  --dry-run         Validate and print the deployment plan without push/SSH changes
  --preflight-only  Run local release checks only
  --skip-env-sync   Do not upload the local .env to the VM
  -h, --help        Show this help

Required environment:
  NETGENIX_VM_SSH_TARGET   SSH target in user@host form for the deployment VM

Optional environment:
  NETGENIX_DEPLOY_REMOTE        Git remote to push to (default: origin)
  NETGENIX_DEPLOY_BRANCH        Branch to push/deploy (default: netgenix)
  NETGENIX_VM_REPO_ROOT         VM repo root (default: ~/Cassava AI/Telco-Network-Configuration)
  NETGENIX_VM_DATA_DIR          VM runtime data root (default: ~/netgenix-data)
  NETGENIX_REMOTE_APP_SUBDIR    App directory under repo root (default: netgenix)
  NETGENIX_LOCAL_ENV_FILE       Local env file to sync (default: netgenix/.env)
  NETGENIX_RUN_LOCAL_SMOKE      Set to 1 to run local curl smoke checks
  NETGENIX_TEST_TIMEOUT         Seconds before the local test command times out
  NETGENIX_TEST_COMMAND         Local test command to run from netgenix/
EOF
}

log() {
  printf '[deploy] %s\n' "$*"
}

fail() {
  printf '[deploy] ERROR: %s\n' "$*" >&2
  exit 1
}

run_cmd() {
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --preflight-only)
      PREFLIGHT_ONLY=1
      ;;
    --skip-env-sync)
      SYNC_ENV=0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
  shift
done

if [[ "${PREFLIGHT_ONLY}" -eq 1 ]]; then
  DRY_RUN=0
fi

cd "${REPO_ROOT}"

current_branch="$(git rev-parse --abbrev-ref HEAD)"
release_sha="$(git rev-parse HEAD)"

if [[ "${current_branch}" != "${NETGENIX_DEPLOY_BRANCH}" ]]; then
  fail "Current branch is '${current_branch}', expected '${NETGENIX_DEPLOY_BRANCH}'."
fi

if git ls-files --error-unmatch netgenix/.env >/dev/null 2>&1; then
  fail "netgenix/.env is tracked by git. Remove it from version control before deploying."
fi

if [[ ! -f "${NETGENIX_LOCAL_ENV_FILE}" ]]; then
  fail "Local env file not found at ${NETGENIX_LOCAL_ENV_FILE}."
fi

is_allowed_local_artifact() {
  local path="$1"
  case "${path}" in
    netgenix/.env|netgenix/.env.*)
      return 0
      ;;
    netgenix/.venv/*|netgenix/.pytest_cache/*|netgenix/frontend/node_modules/*|netgenix/frontend/dist/*)
      return 0
      ;;
    netgenix/logs/*|netgenix/runtime/*)
      return 0
      ;;
    netgenix/data/report_runs/*|netgenix/data/discovery/*|netgenix/data/rollback/*)
      return 0
      ;;
    netgenix/data/evaluation-session.enc|netgenix/data/evaluation-session.enc.invalid|netgenix/data/evaluation-session.key)
      return 0
      ;;
    *.DS_Store|*/__pycache__/*|*.pyc|*.pyo)
      return 0
      ;;
  esac
  return 1
}

validate_worktree() {
  local status lines=()

  while IFS= read -r status; do
    [[ -z "${status}" ]] && continue

    local path="${status:3}"
    if [[ "${path}" == *" -> "* ]]; then
      path="${path##* -> }"
    fi

    if is_allowed_local_artifact "${path}"; then
      continue
    fi

    lines+=("${status}")
  done < <(git status --porcelain=v1 --untracked-files=all -- "${RELEASE_PATHS[@]}")

  if (( ${#lines[@]} > 0 )); then
    printf '[deploy] Disallowed git changes detected:\n' >&2
    printf '  %s\n' "${lines[@]}" >&2
    fail "Commit or clean these changes before deploying."
  fi
}

ensure_not_staged() {
  local path="$1"
  if git diff --cached --name-only -- "${path}" | grep -q .; then
    fail "${path} is staged. Secrets and runtime artifacts must not be part of a release."
  fi
}

ensure_not_staged "netgenix/.env"
ensure_not_staged "netgenix/data/discovery"
ensure_not_staged "netgenix/data/rollback"

validate_worktree

run_test_command() {
  local timeout_seconds="$1"
  shift
  python3 - "$timeout_seconds" "$@" <<'PY'
import subprocess
import sys

timeout = int(sys.argv[1])
command = sys.argv[2:]

try:
    completed = subprocess.run(command, timeout=timeout, check=False)
except subprocess.TimeoutExpired:
    print(f"[deploy] ERROR: test command timed out after {timeout}s", file=sys.stderr)
    sys.exit(124)

sys.exit(completed.returncode)
PY
}

log "Running local preflight checks from ${NETGENIX_DIR}"
(
  cd "${NETGENIX_DIR}"
  run_test_command "${NETGENIX_TEST_TIMEOUT}" bash -lc "${NETGENIX_TEST_COMMAND}"
  docker compose config >/dev/null

  if [[ "${RUN_LOCAL_SMOKE}" == "1" ]]; then
    curl --fail --silent --show-error "http://127.0.0.1:8510/health" >/dev/null
    curl --fail --silent --show-error "http://127.0.0.1:8510/api/sites" >/dev/null
    curl --fail --silent --show-error --head "http://127.0.0.1:8511/" >/dev/null
  fi
)

log "Local preflight checks passed for ${release_sha}"

if [[ "${PREFLIGHT_ONLY}" -eq 1 ]]; then
  log "Preflight-only mode complete."
  exit 0
fi

if [[ -z "${NETGENIX_VM_SSH_TARGET}" ]]; then
  fail "NETGENIX_VM_SSH_TARGET must be set for VM deployment."
fi

log "Pushing ${release_sha} to ${NETGENIX_DEPLOY_REMOTE}/${NETGENIX_DEPLOY_BRANCH}"
run_cmd git push "${NETGENIX_DEPLOY_REMOTE}" "HEAD:${NETGENIX_DEPLOY_BRANCH}"

remote_head="$(git ls-remote --heads "${NETGENIX_DEPLOY_REMOTE}" "${NETGENIX_DEPLOY_BRANCH}" | awk '{print $1}')"
if [[ -z "${remote_head}" ]]; then
  fail "Could not resolve remote branch ${NETGENIX_DEPLOY_REMOTE}/${NETGENIX_DEPLOY_BRANCH} after push."
fi
if [[ "${remote_head}" != "${release_sha}" ]]; then
  fail "Remote head ${remote_head} does not match local release SHA ${release_sha}."
fi

remote_env_path="${NETGENIX_VM_REPO_ROOT}/${NETGENIX_REMOTE_APP_SUBDIR}/.env"

if [[ "${SYNC_ENV}" -eq 1 ]]; then
  log "Uploading ${NETGENIX_LOCAL_ENV_FILE} to ${NETGENIX_VM_SSH_TARGET}:${remote_env_path}"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '[dry-run] sync %s -> %s:%s\n' "${NETGENIX_LOCAL_ENV_FILE}" "${NETGENIX_VM_SSH_TARGET}" "${remote_env_path}"
  else
    ssh "${NETGENIX_VM_SSH_TARGET}" \
      "set -euo pipefail; target=\"${remote_env_path}\"; case \"\$target\" in ~) target=\"\$HOME\" ;; ~/*) target=\"\$HOME/\${target#~/}\" ;; esac; mkdir -p \"\$(dirname \"\$target\")\"; umask 077; cat > \"\$target\"; chmod 600 \"\$target\";" \
      < "${NETGENIX_LOCAL_ENV_FILE}"
  fi
fi

log "Starting staged VM deploy on ${NETGENIX_VM_SSH_TARGET}"
if [[ "${DRY_RUN}" -eq 1 ]]; then
  printf '[dry-run] ssh %s bash -s -- %q %q %q %q %q %q %q\n' \
    "${NETGENIX_VM_SSH_TARGET}" \
    "${release_sha}" \
    "${NETGENIX_DEPLOY_BRANCH}" \
    "${NETGENIX_VM_REPO_ROOT}" \
    "${NETGENIX_VM_DATA_DIR}" \
    "${NETGENIX_REMOTE_APP_SUBDIR}" \
    "${NETGENIX_REMOTE_BACKEND_URL}" \
    "${NETGENIX_REMOTE_FRONTEND_URL}"
  exit 0
fi

ssh "${NETGENIX_VM_SSH_TARGET}" bash -s -- \
  "${release_sha}" \
  "${NETGENIX_DEPLOY_REMOTE}" \
  "${NETGENIX_DEPLOY_BRANCH}" \
  "${NETGENIX_VM_REPO_ROOT}" \
  "${NETGENIX_VM_DATA_DIR}" \
  "${NETGENIX_REMOTE_APP_SUBDIR}" \
  "${NETGENIX_REMOTE_BACKEND_URL}" \
  "${NETGENIX_REMOTE_FRONTEND_URL}" <<'REMOTE_SCRIPT'
set -eEuo pipefail

release_sha="$1"
remote_name="$2"
branch="$3"
repo_root_input="$4"
data_root_input="$5"
app_subdir="$6"
backend_url="$7"
frontend_url="$8"

expand_home() {
  case "$1" in
    "~")
      printf '%s\n' "$HOME"
      ;;
    "~/"*)
      printf '%s/%s\n' "$HOME" "${1#~/}"
      ;;
    *)
      printf '%s\n' "$1"
      ;;
  esac
}

repo_root="$(expand_home "${repo_root_input}")"
data_root="$(expand_home "${data_root_input}")"
app_dir="${repo_root}/${app_subdir}"

previous_sha=""
rollback_needed=0

log() {
  printf '[remote-deploy] %s\n' "$*"
}

fail() {
  printf '[remote-deploy] ERROR: %s\n' "$*" >&2
  exit 1
}

is_allowed_remote_artifact() {
  local path="$1"
  case "${path}" in
    .env|.env.*)
      return 0
      ;;
    logs/*|runtime/*)
      return 0
      ;;
    .venv/*|.pytest_cache/*|frontend/node_modules/*|frontend/dist/*)
      return 0
      ;;
    data/report_runs/*|data/discovery/*|data/rollback/*)
      return 0
      ;;
    data/evaluation-session.enc|data/evaluation-session.enc.invalid|data/evaluation-session.key)
      return 0
      ;;
    *.DS_Store|*/__pycache__/*|*.pyc|*.pyo)
      return 0
      ;;
  esac
  return 1
}

validate_remote_worktree() {
  local status lines=()

  while IFS= read -r status; do
    [[ -z "${status}" ]] && continue

    local path="${status:3}"
    if [[ "${path}" == *" -> "* ]]; then
      path="${path##* -> }"
    fi

    if is_allowed_remote_artifact "${path}"; then
      continue
    fi

    lines+=("${status}")
  done < <(git status --porcelain=v1)

  if (( ${#lines[@]} > 0 )); then
    printf '[remote-deploy] Disallowed git changes detected:\n' >&2
    printf '  %s\n' "${lines[@]}" >&2
    fail "Remote repo is not clean enough to deploy safely."
  fi
}

capture_debug_evidence() {
  docker compose ps || true
  docker compose logs --tail=120 netgenix-backend || true
  docker compose logs --tail=120 netgenix-collector || true
}

rollback() {
  if [[ "${rollback_needed}" -ne 1 || -z "${previous_sha}" ]]; then
    return
  fi

  log "Rolling back to ${previous_sha}"
  git reset --hard "${previous_sha}" || true
  docker compose up -d netgenix-db netgenix-backend netgenix-frontend netgenix-collector || true
  capture_debug_evidence
}

on_error() {
  local line="$1"
  printf '[remote-deploy] ERROR: deployment failed at line %s\n' "${line}" >&2
  rollback
}

trap 'on_error ${LINENO}' ERR

command -v git >/dev/null || fail "git is not installed on the VM."
command -v docker >/dev/null || fail "docker is not installed on the VM."
docker compose version >/dev/null || fail "docker compose plugin is not available on the VM."
command -v curl >/dev/null || fail "curl is required on the VM for health checks."

mkdir -p "${data_root}/data" "${data_root}/logs" "${data_root}/runtime"
[[ -d "${app_dir}" ]] || fail "NetGenix app directory not found at ${app_dir}"

cd "${app_dir}"
validate_remote_worktree

[[ -f ".env" ]] || fail "VM env file missing at ${app_dir}/.env"

previous_sha="$(git rev-parse HEAD)"
log "Current VM SHA: ${previous_sha}"

git fetch --prune "${remote_name}" "${branch}"
git checkout "${branch}"
git reset --hard "${release_sha}"
rollback_needed=1

current_sha="$(git rev-parse HEAD)"
[[ "${current_sha}" == "${release_sha}" ]] || fail "VM SHA ${current_sha} does not match release SHA ${release_sha}"

docker compose config >/dev/null
docker compose build

wait_for_container_state() {
  local container="$1"
  local expected_state="$2"
  local timeout="$3"
  local deadline=$((SECONDS + timeout))
  local state=""

  while (( SECONDS < deadline )); do
    state="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container}" 2>/dev/null || true)"
    if [[ "${state}" == "${expected_state}" ]]; then
      return 0
    fi
    sleep 2
  done

  fail "Container ${container} did not reach state ${expected_state} within ${timeout}s"
}

check_http() {
  local url="$1"
  local timeout="$2"
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if curl --fail --silent --show-error "${url}" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  fail "HTTP check failed for ${url} within ${timeout}s"
}

check_http_head() {
  local url="$1"
  local timeout="$2"
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if curl --fail --silent --show-error --head "${url}" >/dev/null; then
      return 0
    fi
    sleep 2
  done
  fail "HTTP HEAD check failed for ${url} within ${timeout}s"
}

docker compose up -d netgenix-db
wait_for_container_state "netgenix-db" "healthy" 180

docker compose up -d netgenix-backend
check_http "${backend_url}/health" 180
check_http "${backend_url}/api/sites" 180

docker compose up -d netgenix-frontend
check_http_head "${frontend_url}/" 120

docker compose up -d netgenix-collector
sleep 10
wait_for_container_state "netgenix-collector" "running" 60

docker compose ps
docker compose logs --tail=80 netgenix-backend
docker compose logs --tail=80 netgenix-collector

rollback_needed=0
log "Deployment succeeded at ${release_sha}"
REMOTE_SCRIPT

log "Netgenix deploy completed successfully at ${release_sha}"
