# NetGenix Consolidation Plan

## Product Principle

NetGenix is an AI telco optimizer first. Reporting, topology, NBI diagnostics, file imports, and visualisation are support systems that provide evidence, confidence, and operational control for optimisation decisions.

## Phase 0: Canonical Product Folder

- `netgenix/` is the actual product home.
- `lz-network-optimizer/` remains the runnable source/reference base.
- `cassava-4g-network-optimiser/` remains the cleaner architecture/reference source.
- Generated clutter, local secrets, caches, build output, and runtime files must stay out of the product source.

## Phase 1: Optimizer-First Stabilisation

- Keep React/Vite as the canonical UI and FastAPI as the canonical backend.
- Keep `/api/optimize` and `/api/optimize/execute` as first-class product APIs.
- Preserve dry-run by default for generated MML.
- Full AI workflow should use LangGraph/LangChain/NVIDIA when configured.
- Deterministic safe mode must continue to return KPI evidence, recommendations, risk, expected impact, and dry-run MML when the LLM workflow is unavailable.
- Next improvement: feed imported MAE cell/site KPI evidence into the optimizer context.

## Phase 2: NBI Diagnostics

- Access NBI default: `https://41.174.191.214:31127`.
- Evaluation NBI default: `https://41.174.191.211:27417`.
- Diagnostics classify GUI reachability, NBI reachability, login result, MAE `retCode`/`retMessage`, timeout, missing endpoint, wrong method, and unknown failures.
- Do not self-escalate NBI permissions; admin must grant NBI/user/NE/MML groups in MAE.

## Phase 3: v2 Reporting Automation

- Use file-first automation while Evaluation NBI remains unreliable.
- Inputs include MAE/Evaluation raw KPI exports, Telrad exports, subscriber extracts, EPC values, and templates.
- Produce Excel reports first, then PDF reports and dashboard previews.
- Keep deterministic formulas auditable: traffic totals, GB/TB conversion, PRB busy-hour average, code-drop average, penetration rate, GB per active user, throughput per active user, top/bottom rankings, and exclusions.
- Every report run should store raw input references, computed metrics, output files, timestamp, and context.

## Phase 4: v3 NOC / Topology

- Start with practical topology and site inventory from raw MAE pulls.
- Scale toward roughly 250-350 sites.
- Use approximate coverage/status visuals, not full RF simulation yet.
- Site/cell drilldown should show KPIs, alarms when available, parameters, recommendations, NBI state, and a direct path to optimizer actions.
- Defer full 3D/digital twin tooling until topology and data quality are trustworthy.

## Phase 5: Intelligence Layer

- Add AI operational summaries after deterministic data is reliable.
- Add anomaly detection from historical KPI baselines.
- Add capacity alerts from PRB/load trends.
- Add forecasting after enough clean history exists.
- Defer Kafka, Redis, InfluxDB, WebSockets, and streaming architecture until real-time scale requires them.

## Immediate Next Steps

- Validate full LLM-backed optimizer workflow now that `NVIDIA_API_KEY` is present locally.
- Connect raw MAE 341-site inventory/KPI exports to optimizer evidence.
- Redesign topology drilldown as an optimizer launch and investigation surface.
- Keep report production useful, but do not let it outrank optimizer core work.
