# Operations Notes

## Environment

Assessment date: 2026-04-29

- Host OS: macOS Darwin 25.4.0 arm64
- Workspace location: OneDrive-backed project directory
- Docker Desktop: running
- Environment type: shared multi-project machine, not a clean single-project VM

## Operational Constraints

Ports already observed in use include:

- `80`
- `8080`
- `8001`
- `3306`
- `3307`
- `54321` to `54327`
- `11434`

Implication:

- Do not assume default ports are free when starting local services.
- Prefer explicit port selection for any new backend, frontend, Streamlit, or DB process.

## Active Container Context

Unrelated project stacks were running during assessment, including:

- `netassurance-staging-*`
- `nce_*`
- `mars_*`
- `kusoma-*`
- local Supabase containers

Implication:

- Verify container names and ports before starting anything new.
- Be careful not to stop or interfere with unrelated services.

## Current Project Runtime Assumption

Canonical working base:

- `netgenix/`

Likely local runtime shape:

- frontend on `8511`
- backend on `8510`
- internal DB files under `netgenix/data/`
- generated report/runtime files under `netgenix/runtime/`

Current optimizer mode:

- Full LLM workflow when dependencies and `NVIDIA_API_KEY` are configured.
- Deterministic safe mode when the LLM workflow is unavailable.
- Live MML remains blocked unless `execute_live=true` and `NETGENIX_ALLOW_LIVE_MML=true`.

## Operational Risks

- Git history operations are unreliable because of a packfile integrity problem.
- Cloud-synced workspace storage may make large DB/log churn noisier or slower.
- Multiple historical branches and folders make accidental edits more likely.

## Recommended Safe Practice

- Confirm ports with `lsof -iTCP -sTCP:LISTEN -n -P`
- Confirm running containers with `docker ps`
- Avoid destructive cleanup unless scope is explicit
- Prefer narrow edits in the selected branch
- Record any new canonical ports or startup commands in this file and `docs/CODEX_CONTEXT.md`

## NetGenix Commands

- Backend: `cd netgenix && python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8510`
- Frontend: `cd netgenix/frontend && VITE_API_URL=http://localhost:8510 npm run dev -- --host 0.0.0.0 --port 8511`
- Health: `curl -s http://localhost:8510/health`
- Status: `curl -s http://localhost:8510/api/status`
- NBI diagnostics: `curl -s http://localhost:8510/api/diagnostics/nbi`
- Optimizer smoke test: `curl -s -X POST http://localhost:8510/api/optimize -H 'Content-Type: application/json' -d '{"site_name":"MSH-0014-Chipadze","cell_id":1,"query":"Optimize download speed and explain evidence"}'`

## Current MAE Status Note

- `/api/status` checks Access NBI reachability using `NETGENIX_HUAWEI_ACCESS_NBI_URL` and falls back to legacy `HUAWEI_API_URL`.
- On 2026-05-01, Access GUI `:31943` and Access NBI `:31127` timed out from this machine; treat that as network path unavailable unless credentials produce a concrete MAE `retCode`.
- Do not commit `.env` files or real Huawei/NVIDIA credentials.
