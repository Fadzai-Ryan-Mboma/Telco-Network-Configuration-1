# Architecture Notes

## NetGenix Canonical Architecture

NetGenix is now the canonical product under `netgenix/`. The core product is the AI telco optimizer; every other module should support optimisation evidence, safety, execution control, or operator insight.

- UI: React/Vite in `netgenix/frontend/`.
- Backend: FastAPI in `netgenix/backend/`.
- Backend services: `netgenix/backend/netgenix/services/`.
- Reporting engine: `netgenix/backend/netgenix/reports/`.
- Optimizer endpoint: `POST /api/optimize`.
- Execution endpoint: `POST /api/optimize/execute`.
- Safe fallback path: deterministic optimizer rules in `backend/netgenix/services/optimization.py`.
- Full AI path: copied multi-agent workflow under `agents/` using LangGraph/LangChain/NVIDIA-compatible LLM configuration.
- Safety invariant: generated MML is dry-run unless the request explicitly asks for live execution and `NETGENIX_ALLOW_LIVE_MML=true` is set.

Evidence sources should expand from local demo SQLite to MAE raw KPI exports, live Access NBI queries, alarms, topology, and historical baselines.

## Canonical Interpretation

For now, treat the project as a transition-state architecture with one canonical product branch and two reference branches.

- Canonical product branch: `netgenix/`
- Practical runtime/reference branch: `lz-network-optimizer/`
- Cleaner architectural reference: `cassava-4g-network-optimiser/`

## Current Practical Architecture

Primary application shape appears to be:

1. Vite/React frontend in `lz-network-optimizer/frontend/`
2. FastAPI backend in `lz-network-optimizer/backend/`
3. Shared optimization logic and data helpers under:
   - `agents/`
   - `network/`
   - `tools/`
   - `domain/`
   - `ui/`

Key architectural reality:

- The FastAPI backend is not fully layered.
- Several route handlers depend on helper code inside `ui/`, which means UI-era logic is acting as service logic.

## Intended Long-Term Architecture

The package-style branch suggests the desired end state:

1. `config/` for settings and environment loading
2. `domain/` for models, rules, and exceptions
3. `infrastructure/` for Huawei, database, and LLM clients
4. `services/` for application/business logic
5. `workflow/` for orchestration and state transitions
6. `ui/` as a thin presentation layer

## Recommended Direction

Short term:

- Keep delivering from `netgenix/`
- Extract logic out of `ui/` and into backend-safe service modules
- Tighten the current backend/frontend contract
- Keep topology/reporting/NBI work subordinate to optimizer usefulness

Medium term:

- Reuse good service/repository/config ideas from `cassava-4g-network-optimiser/`
- Migrate incrementally, not by replacing the runtime base in one step
- Feed MAE raw KPI/site inventory data into optimizer context
- Turn topology drilldown into an optimizer launch and investigation surface

## Saved Plan

The phased consolidation and v2/v3 roadmap is saved in `docs/NETGENIX_CONSOLIDATION_PLAN.md`.

## Boundaries

Authoritative now:

- `lz-network-optimizer/` runtime behavior
- new docs in `docs/`

Reference-only unless explicitly selected:

- `legacy/`
- `rebuild-assets/`
- `nvidia-reference/`
- non-selected pieces of `cassava-4g-network-optimiser/`
