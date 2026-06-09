# NetGenix Architecture

NetGenix is organised around a React operator UI and a FastAPI backend. The core product is the AI telco optimizer; every other module should support optimisation evidence, safety, execution control, or operator insight.

## Flow

1. The React dashboard loads sites, KPIs, parameters, status, activity, and NBI diagnostics from FastAPI.
2. FastAPI routes delegate to backend services under `backend/netgenix/services`.
3. Local historical/demo values come from SQLite databases under `data/`.
4. The optimisation route bridges into the copied agent workflow under `agents/`.
5. If the LLM workflow cannot run, the optimisation service falls back to deterministic safe-mode rules that use local KPI evidence, conservative recommendations, risk scoring, and dry-run MML generation.
6. Huawei Access/Evaluation checks are read-only diagnostics inspired by the iMaster MAE NBI documentation.
7. v2 reporting formulas live under `backend/netgenix/reports` and support file import, audit trail, Excel output, and PDF output.
8. Report history, column-mapping preview, and multi-file report production are exposed through the Reports API so operators can validate raw exports before generation.
9. The first v3 topology view is a lightweight NOC panel using MAE-derived site inventory and KPI overlays; it should evolve into an optimizer launch surface, not a standalone map toy.

## Optimizer Core

- Primary endpoint: `POST /api/optimize`.
- Execution endpoint: `POST /api/optimize/execute`.
- Preferred path: copied multi-agent workflow under `agents/` using LangGraph/LangChain and NVIDIA-compatible LLM configuration.
- Safe fallback path: deterministic rules in `backend/netgenix/services/optimization.py`.
- Safety invariant: generated MML is dry-run unless the request explicitly asks for live execution and `NETGENIX_ALLOW_LIVE_MML=true` is set.
- Evidence sources should expand from local demo SQLite to MAE raw KPI exports, live Access NBI queries, alarms, topology, and historical baselines.

## Current API Contract

- `/health`
- `/api/status`
- `/api/sites`
- `/api/sites/{site}`
- `/api/sites/{site}/params`
- `/api/kpi/{site}`
- `/api/kpi/{site}/history`
- `/api/optimize`
- `/api/optimize/execute`
- `/api/activity`
- `/api/diagnostics/nbi`
- `/api/reports/formulas/preview`
- `/api/reports/preview`
- `/api/reports/imports`
- `/api/reports/cook`
- `/api/reports/runs`
- `/api/reports/runs/{run_id}/download`
- `/api/reports/runs/{run_id}/pdf`
- `/api/topology/sites`

## Roadmap Interpretation

- v2 is treated as reporting automation: deterministic formulas, imports, rankings, audit trail, Excel output, then dashboard preview.
- v3 is treated as NOC visualisation and intelligence: topology/map first, then anomaly/capacity/forecasting after data quality is proven.
- The saved phased plan lives in `docs/NETGENIX_CONSOLIDATION_PLAN.md`.
