# NetGenix Operations

## Runtime

- Backend: FastAPI on port `8510`.
- Frontend: Vite dev server on port `8511`.
- Local data source: `data/lz_network.db` and `data/liquid_zimbabwe.db`.
- Live NBI source: Huawei iMaster MAE Access/Evaluation when credentials and network reachability are available.
- Optimizer mode: full LLM workflow when configured; deterministic safe mode when the LLM workflow is unavailable.

## Environment Variables

- `NETGENIX_HUAWEI_ACCESS_NBI_URL`: defaults to `https://41.174.191.214:31127`.
- `NETGENIX_HUAWEI_ACCESS_GUI_URL`: defaults to the Access GUI home URL.
- `NETGENIX_HUAWEI_EVALUATION_NBI_URL`: defaults to `https://41.174.191.211:27417`.
- `NETGENIX_HUAWEI_EVALUATION_GUI_URL`: defaults to the Evaluation report-management URL.
- `NETGENIX_HUAWEI_USERNAME`: optional live NBI username.
- `NETGENIX_HUAWEI_PASSWORD`: optional live NBI password.
- `NETGENIX_HUAWEI_GUI_USERNAME`: optional GUI username for future browser/UI automation.
- `NETGENIX_HUAWEI_GUI_PASSWORD`: optional GUI password for future browser/UI automation.
- `NVIDIA_API_KEY`: enables the full LLM-backed optimizer workflow.
- `NETGENIX_ALLOW_LIVE_MML`: must be `true` before any live MML execution can occur.

## Data Source States

- `historical/demo data`: local SQLite/CSV data powers the current dashboard and known sites.
- `live Access NBI`: reachable/authenticated only when network and credentials work.
- `live Evaluation NBI`: configured for `https://41.174.191.211:27417`.
- `unavailable/auth-failed/timeout`: classified by `/api/diagnostics/nbi`.

## Safety

- Treat all optimisation execution as dry-run unless an operator explicitly approves live execution.
- Live MML requires both `execute_live=true` in the request and `NETGENIX_ALLOW_LIVE_MML=true` in the environment.
- Keep rollback/history visible before enabling non-dry-run MML changes.
- Do not commit `.env` files or real Huawei credentials.

## Optimizer Operations

- Smoke test optimizer:
  `curl -s -X POST http://localhost:8510/api/optimize -H 'Content-Type: application/json' -d '{"site_name":"MSH-0014-Chipadze","cell_id":1,"query":"Optimize download speed and explain evidence"}'`
- Smoke test execution gate:
  `POST /api/optimize/execute` should return `dry_run: true` unless live execution is explicitly unlocked.
- If `/api/optimize` reports that the LLM workflow is unavailable, safe mode should still return KPI evidence, recommendations, risk, expected impact, and MML commands.
- Do not enable live MML until rollback capture, post-change monitoring, and operator approval flow have been reviewed.

## Reporting Operations

- Single-file report imports accept CSV/XLSX files through `POST /api/reports/imports`.
- Multi-file Brighton-style report cooking accepts raw exports through `POST /api/reports/cook`.
- Column mapping preview is available through `POST /api/reports/preview`.
- Report history is available through `GET /api/reports/runs`.
- Generated workbooks and audit files are stored under `runtime/reports/`, which is intentionally ignored by git.
- Ranking exclusions are provided as comma-separated site names.
- The reporting structure uses uploaded raw export files; live platform automation should come later after source exports and access are stable.
- Section definitions and testing notes live in `docs/REPORTING.md`.
- Sample report files for UI testing are served from `frontend/public/samples/reports/`.

## Topology Operations

- The first topology endpoint is `GET /api/topology/sites`.
- It uses the four known local sites and approximate coordinates for the initial NOC-style view.
- The topology panel is not a full RF simulation; it is a drilldown/status visual for KPIs, recommendations, and future alarm/NBI overlays.

## MAE Diagnostics Operations

- `/api/diagnostics/nbi` is ready for retry once Access/Evaluation endpoints, credentials, and network path are confirmed.
- Credentials stay in local `.env`; never move them into tracked docs or source files.
- Current implementation classifies `success`, `auth_failed`, `timeout`, `endpoint_missing`, `method_wrong`, and `unknown`.
- `/api/status` checks Access NBI reachability using `NETGENIX_HUAWEI_ACCESS_NBI_URL` and falls back to legacy `HUAWEI_API_URL` only for compatibility.
- On 2026-05-01, Access GUI `:31943` and Access NBI `:31127` timed out from this machine; treat that as network path unavailable unless credentials produce a concrete MAE `retCode`.
