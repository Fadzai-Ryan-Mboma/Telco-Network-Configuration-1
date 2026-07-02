# Codex Context

## Current Goal

Use `netgenix/` as the new canonical product home. NetGenix is an AI telco optimisation product first; reporting, topology, NBI diagnostics, and file imports exist to feed evidence into the optimizer and make optimisation safer, clearer, and more operationally useful.

## Current State

- This workspace contains multiple generations of the same telco optimization effort.
- `netgenix/` is now the canonical product folder.
- Product priority: the AI Optimizer / optimisation assistant is the core function.
- `lz-network-optimizer/` remains the proven source base/reference for current behavior.
- `cassava-4g-network-optimiser/` remains a cleaner architecture/reference source, but it currently has implementation drift.
- `legacy/`, `rebuild-assets/`, and `nvidia-reference/` are reference sources only unless a task explicitly lifts something from them.
- The VM is shared and already running several unrelated containers and occupied ports.
- Git history access is currently unreliable because a packfile appears corrupted.

## System Overview

- Current canonical runtime shape:
  - React/Vite frontend in `netgenix/frontend/`
  - FastAPI backend in `netgenix/backend/`
  - backend services under `netgenix/backend/netgenix/services/`
  - reporting formulas under `netgenix/backend/netgenix/reports/`
- Long-term architectural reference:
  - package-style branch in `cassava-4g-network-optimiser/src/cassava_optimizer/`
- Key integrations:
  - Huawei iMaster MAE / PM APIs
  - NVIDIA NIM or similar LLM endpoint
  - local SQLite databases
  - Docker

## Recent Decisions

- 2026-04-29: Use `lz-network-optimizer/` as the current working base because it is more operationally coherent.
- 2026-04-29: Treat `cassava-4g-network-optimiser/` as an architectural reference and future migration candidate, not the immediate runtime base.
- 2026-04-29: Treat `legacy/` and related side-work folders as reference-only unless a later task explicitly extracts from them.
- 2026-04-29: Treat the VM as a shared environment and avoid assuming common local ports are free.
- 2026-04-30: Created `netgenix/` as the canonical consolidated product folder.
- 2026-04-30: Preserved the existing React + FastAPI API contract while moving backend coupling away from old `ui/*` imports into `backend/netgenix/services`.
- 2026-04-30: Added read-only Huawei Access/Evaluation NBI diagnostics and initial v2 deterministic reporting formula preview.
- 2026-05-01: Re-centered NetGenix around the telco AI Optimizer. The assistant must produce useful optimisation recommendations first; topology/reporting/NBI are support layers.
- 2026-05-01: Added a deterministic optimizer safe mode so `/api/optimize` does not fail when the LLM path is unavailable. It uses local KPI evidence, conservative rules, risk scoring, and generated dry-run MML.
- 2026-05-01: Updated the top live-status banner to follow the current Access NBI config names instead of old `HUAWEI_*` variables, and changed the UI wording from generic `DISCONNECTED` to Access NBI state.

## Known Risks

- Git object store appears damaged; `git log` failed on 2026-04-29 with a truncated packfile error.
- Shared VM has active unrelated containers and bound ports.
- `netgenix/` has reduced the backend-to-UI coupling, but deeper service/domain cleanup is still needed.
- The refactor branch has mismatches between code, tests, imports, and docs.
- Live Access/Evaluation reachability can change depending on VPN/network path. Do not infer credential failure from timeout alone.
- The deterministic optimizer fallback is not a replacement for full AI reasoning; it is a safety net until the LLM workflow is fully validated.

## Useful Commands

- `docker ps`
- `lsof -iTCP -sTCP:LISTEN -n -P`
- `find docs -maxdepth 2 -type f | sort`
- `find lz-network-optimizer -maxdepth 2 -type f | sort`
- `find cassava-4g-network-optimiser/src/cassava_optimizer -maxdepth 2 -type f | sort`
- `cd netgenix && python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8510`
- `cd netgenix/frontend && VITE_API_URL=http://localhost:8510 npm run dev -- --host 0.0.0.0 --port 8511`
- `curl -i http://localhost:8510/health`
- `curl -s http://localhost:8510/api/diagnostics/nbi`
- `curl -s -X POST http://localhost:8510/api/optimize -H 'Content-Type: application/json' -d '{"site_name":"MSH-0014-Chipadze","cell_id":1,"query":"Optimize download speed and explain evidence"}'`
- `curl -s http://localhost:8510/api/status`

## Open Tasks

- [ ] Repair or safely back up the repo because Git history is not trustworthy right now
- [x] Create `netgenix/` canonical product folder from `lz-network-optimizer/`
- [x] Verify the actual run path for the consolidated React + FastAPI app
- [ ] Classify tests by safety and dependency level
- [x] Identify and implement the first extraction seam from `lz-network-optimizer/ui/` into a backend/service layer
- [ ] Decide which idea, if any, should be selectively lifted from `cassava-4g-network-optimiser/`
- [ ] Turn v2 reporting scaffolding into file imports, audit trail persistence, and Excel output
- [x] Add v2 reporting file import, audit JSON, top/bottom rankings, and Excel output structure
- [ ] Turn v3 roadmap into topology/map view using the four known sites first
- [x] Restore AI Optimizer endpoint usefulness with deterministic safe-mode recommendations and dry-run MML
- [ ] Validate full LLM agent workflow with configured `NVIDIA_API_KEY` and real optimizer prompts
- [ ] Feed raw MAE cell/site KPI exports into optimizer evidence, not only reports/topology
- [ ] Redesign topology drilldown so site/cell cards launch useful optimizer actions

## Session Log

### 2026-04-29

- Performed a read-first workspace and VM assessment.
- Confirmed the workspace contains two active implementation tracks plus several historical/reference trees.
- Identified `lz-network-optimizer/` as the better near-term execution base.
- Identified `cassava-4g-network-optimiser/` as the cleaner but drifted architectural branch.
- Observed a shared VM with many active containers and occupied ports.
- Detected a Git packfile problem that makes history operations risky.
- Wrote durable assessment and memory docs under `docs/`.

### 2026-04-30

- Implemented Phase 0/1 foundation for NetGenix under `netgenix/`.
- Copied the working `lz-network-optimizer` frontend/backend/domain/network/tools/agents/prompts/data/docs material without copying stale `.env`, build output, caches, or OS clutter.
- Added backend package structure: `backend/netgenix/services`, `infrastructure`, `domain`, and `reports`.
- Moved database and optimization workflow route dependencies into NetGenix backend services.
- Added `/api/diagnostics/nbi` for Access/Evaluation GUI/NBI reachability and login classification.
- Added `/api/reports/formulas/preview` for v2 deterministic reporting formula checks.
- Added frontend Access/Evaluation NBI status cards.
- Added NetGenix README, architecture docs, operations docs, safe `.env.example`, and `scripts/start-dev.sh`.
- Verified backend on fallback port `8510`: `/health` returned 200, `/api/sites` returned the four known sites, `/api/status` showed local DB connected, and KPI history returned populated data.
- Verified frontend build and Vite serving on fallback port `8511`.
- Updated NetGenix canonical dev ports to backend `8510` and frontend `8511`.
- Added Phase 1 safe execution gating: live MML requires request approval and `NETGENIX_ALLOW_LIVE_MML=true`; otherwise execution remains dry-run.
- Added v2 reporting import/generation structure with CSV/XLSX input, audit JSON, top/bottom rankings, and Excel download.
- Expanded v2 reporting workbook sections: Summary, Report Sections, Executive KPI, GCO Report, GCU Report, General Report, Site Performance, traffic/PRB/code-drop rankings, Exceptions, and Audit.
- MAE diagnostics are structurally ready but live retry is deferred until network reachability, endpoints, and credentials are resolved.
- Remapped local demo data dates so the main dashboard KPI history now appears as `2025-12-01` to `2026-04-29` instead of `2025-09-01` to `2026-01-29`. Values were preserved; timestamps only were changed. Backup is under ignored `netgenix/runtime/backups/`.
- Added report column-mapping preview, report run history, sample report CSVs, and the first v3 topology/NOC tab using four known local sites.
- Updated Huawei iMaster MAE endpoint defaults: Access NBI `https://41.174.191.214:31127`, Evaluation NBI `https://41.174.191.211:27417`, with GUI URLs stored separately. Secrets remain local-only in ignored `.env`.
- Live NBI auth test on 2026-04-30: Access NBI authenticated successfully (`classification: success`); Evaluation GUI is reachable but Evaluation NBI on `https://41.174.191.211:27417` timed out before authentication.
- Current reporting model: because Evaluation NBI is not reachable yet, a human downloads raw Excel/CSV exports from MAE/Evaluation, Telrad, EPC, and subscriber systems, then uploads them to NetGenix for Brighton-style Excel cooking. Added multi-file `/api/reports/cook` and Evaluation Gbit-to-GB conversion.

### 2026-05-01

- Confirmed the product intent: NetGenix is built from the telco optimizer blueprint and must excel at optimisation first.
- Fixed the optimizer route so `/api/optimize` returns a useful result instead of failing when the LLM workflow is unavailable.
- Added `netgenix/utils/llm_factory.py` and `netgenix/utils/timeout_handler.py` so copied agents have their expected utility package.
- Added LangChain/LangGraph/NVIDIA packages to backend requirements for the full AI workflow path.
- Added deterministic safe-mode optimisation logic in `backend/netgenix/services/optimization.py`.
- Verified a download-speed optimisation query returns KPI evidence, a Reference Signal Power recommendation, risk score, and generated MML commands for cells 1-6.
- Verified `/api/optimize/execute` remains dry-run even with `execute_live=true` unless `NETGENIX_ALLOW_LIVE_MML=true`.
- Fixed the top live-status banner source to use `NETGENIX_HUAWEI_ACCESS_NBI_URL` / `NETGENIX_HUAWEI_USERNAME` before legacy `HUAWEI_*` names.
- Current network test from this machine: Access GUI `:31943` and Access NBI `:31127` timed out on 2026-05-01, so the UI should show Access NBI unavailable rather than generic disconnected.
- Saved the consolidation and v2/v3 roadmap into `docs/NETGENIX_CONSOLIDATION_PLAN.md` and `netgenix/docs/NETGENIX_CONSOLIDATION_PLAN.md`.

## Handoff

Current branch:
`rebuild/lz-nvidia-hybrid`

What is working:
`netgenix/` now exists as the canonical app. Backend and frontend are verified and documented on ports `8510` and `8511`. The optimizer endpoint now returns safe-mode recommendations and dry-run MML when the LLM workflow cannot run.

What is risky:
Git integrity, shared/occupied ports, live Huawei network reachability, and inherited npm dependency vulnerabilities.

Next recommended step:
Prioritise the AI Optimizer core: validate the full LLM workflow, connect MAE/raw KPI evidence into optimisation context, and make topology/reporting drilldowns feed optimizer actions.
