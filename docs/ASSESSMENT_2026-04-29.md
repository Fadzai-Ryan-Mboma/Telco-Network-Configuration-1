# Telco Network Configuration Assessment

Date: 2026-04-29
Assessor: Codex
Mode: Read-first assessment with targeted VM/runtime inspection

## Executive Summary

This workspace is not a single clean application repo. It is a multi-generation project workspace containing:

- `lz-network-optimizer/`: the most operationally concrete branch, with a FastAPI backend, Vite/React frontend, Streamlit-derived helpers, Docker definitions, data files, and project-specific docs.
- `cassava-4g-network-optimiser/`: a more structured package-style refactor with cleaner architecture, async services, SQLAlchemy models, and LangGraph workflow modules, but with clear drift between code, tests, docs, and some imports.
- `legacy/`: earlier implementations and experiments that are useful as references, not as a direct merge target.
- `rebuild-assets/` and `nvidia-reference/`: extraction/reference material that explains the intended domain and the NVIDIA-inspired architecture.

Recommended near-term base:

- Use `lz-network-optimizer/` as the current execution base for practical work.
- Use `cassava-4g-network-optimiser/` as an architectural reference and refactor candidate, not as the immediate runtime base.
- Keep `legacy/` and related side-work folders as reference-only unless a later task explicitly lifts a specific idea or module.

Why:

- `lz-network-optimizer/` has the clearest runtime shape today: backend routes, frontend pages, API client wiring, Docker setup, docs, data files, and operational assumptions are more aligned with one another.
- `cassava-4g-network-optimiser/` has better boundaries and naming in several places, but there is enough implementation drift that switching to it now would likely turn today's work into refactor repair rather than product progress.

## Workspace Map

### 1. Current Candidate: `lz-network-optimizer/`

Observed structure:

- `backend/`: FastAPI app and route modules
- `frontend/`: Vite + React UI
- `ui/`: legacy/bridging helpers and workflow wrappers reused by backend routes
- `agents/`, `tools/`, `network/`, `domain/`, `prompts/`: optimization logic and support layers
- `data/`: SQLite DB, historical CSVs, rollback files
- `docker-compose.yml` and `docker/`: deployment variants
- `docs/`: internal guides, architecture notes, test guides, prior assessment docs

Strengths:

- Strongest evidence of runnable full-stack flow
- Frontend API client expects backend endpoints that exist under `backend/api/routes`
- Rich domain and operational docs
- Real project data artifacts present
- Clearer local deployment story than other branches

Weak points:

- Layer coupling remains high
- Backend routes import from `ui/` helpers and workflow adapters rather than a clean service layer
- Multiple app styles coexist in one tree
- Some docs appear optimistic or historical rather than current
- Test suite includes many live/integration-oriented scripts rather than a stable unit/integration pyramid

### 2. Refactor Candidate: `cassava-4g-network-optimiser/`

Observed structure:

- `src/cassava_optimizer/`: package layout for config, domain, infrastructure, services, workflow, tools, and UI
- `tests/`: unit and integration folders
- `Dockerfile`, `docker-compose.yml`, `.env.example`, `pyproject.toml`
- `docs/`: limited docs compared with `lz-network-optimizer/`

Strengths:

- Better package organization
- Async SQLAlchemy database layer
- Explicit settings model with Pydantic
- More intentional repository/service/workflow split
- Better long-term shape if repaired

Weak points and drift:

- Some code paths reference modules that are not present under the current layout, including `cassava_optimizer.utils.logger`, `cassava_optimizer.tools.mae_tools`, and `cassava_optimizer.network.mae_client`
- Test expectations do not consistently match actual settings fields and env vars
- `README.md`, `.env.example`, runtime code, and tests are not fully aligned on canonical names
- Entry scripts and workflow plumbing appear partially evolved but not fully reconciled

Assessment:

- Promising as the long-term architecture
- Not the best immediate base for today's implementation work unless the next task is specifically a refactor stabilization effort

### 3. Reference Areas

`legacy/` contains several prior implementations:

- `liquid-4g-core`
- `liquid-4g-demo`
- `liquid-4g-prod`
- archived experiments, docs, and cleanup snapshots

These are valuable for:

- recovering business logic intent
- comparing older optimization flows
- extracting operational lessons
- reusing docs, prompts, or domain mappings selectively

They should not be treated as canonical runtime code.

`rebuild-assets/` contains extracted production-adjacent assets:

- Huawei API client material
- prompt architecture
- domain knowledge
- config and branding assets

`nvidia-reference/` is best understood as upstream conceptual inspiration, not application code to run directly.

## Architecture and Flow

### Current Practical Flow: `lz-network-optimizer`

Likely user/runtime path:

1. React frontend on port `8502` calls backend API on port `8503`
2. Backend routes under `backend/api/routes` expose:
   - sites
   - optimization
   - KPI
   - activity
   - status
3. Backend route handlers reuse logic from `ui/database_helper.py` and `ui/workflow_interface.py`
4. Underlying optimization logic pulls from project modules such as:
   - `agents/`
   - `network/`
   - `tools/`
   - local SQLite/history files
5. External integrations include Huawei MAE and NVIDIA/NIM-style LLM access where configured

Architectural note:

- The backend is not fully independent. It acts as an API shell over logic that still lives partly in Streamlit-era helper modules. This is functional, but it means future backend work should gradually extract service-layer code out of `ui/`.

### Intended Long-Term Flow: `cassava-4g-network-optimiser`

The refactor branch suggests this target architecture:

1. UI reads from service layer
2. Service layer uses repository/database layer and infrastructure clients
3. Workflow is orchestrated through LangGraph with explicit state and node modules
4. Config is centralized through settings classes
5. Domain models and exceptions are separated from transport details

This is the cleaner design direction, but the current branch still needs consistency work before it can replace the more runnable implementation.

## Functionality Inventory

### `lz-network-optimizer`

Visible functional areas:

- site discovery and site info
- parameter retrieval
- KPI retrieval and KPI history
- optimization request flow
- MML recommendation and execution flow
- activity and status views
- rollback/history artifacts in `data/rollback/`
- React dashboard components for charts, parameter cards, results, AI assistant, and activity log

### `cassava-4g-network-optimiser`

Visible intended capabilities:

- site service and KPI service
- command service and rollback service
- workflow orchestration with collect/analyze/strategy/validate/execute/review stages
- async Huawei PM/MAE interaction
- Streamlit UI pages for dashboard, optimization, history, and settings

Confidence note:

- Functionality in `cassava-4g-network-optimiser` is partly implemented and partly aspirational because some referenced modules/interfaces do not line up cleanly.

## Dependencies and Integrations

### External/Network Dependencies

- Huawei iMaster MAE / PM APIs
- NVIDIA NIM or similar LLM endpoint
- Local SQLite databases
- Docker runtime

### `lz-network-optimizer` Stack Signals

- FastAPI backend
- Vite + React frontend
- TypeScript
- Axios
- Recharts
- SQLite
- Python agent/tool stack

### `cassava-4g-network-optimiser` Stack Signals

- Python 3.11+
- SQLAlchemy async + `aiosqlite`
- Pydantic Settings
- LangChain / LangGraph
- Streamlit + Plotly
- Structlog
- HTTPX

## VM and Runtime Assessment

Environment observed on 2026-04-29:

- OS: macOS Darwin 25.4.0 arm64
- Workspace path is under OneDrive-backed storage
- Docker Desktop is running
- The machine is shared across multiple active projects

Notable running containers included unrelated stacks such as:

- `netassurance-staging-*`
- `nce_*`
- `mars_*`
- `kusoma-*`
- local Supabase services

Observed listening ports already in use:

- `80`
- `8080`
- `8001`
- `3306`
- `3307`
- `54321` to `54327`
- `11434`
- others unrelated to this project

Implications:

- This VM cannot be treated as a clean single-project sandbox
- New services must avoid assuming standard ports are free
- Local verification steps should explicitly choose non-conflicting ports
- Runtime debugging must account for neighboring containers and nginx processes

Disk snapshot:

- Data volume has usable free space, but it is not a fresh machine
- The workspace being inside cloud-synced storage raises extra caution for large generated files, DB churn, and concurrent file activity

## Git and Repo Health

Branch observed:

- `rebuild/lz-nvidia-hybrid`

Important risk:

- `git log` failed with `pack ... is far too short to be a packfile`

Interpretation:

- The Git object store appears damaged or incomplete
- History-based operations may be unreliable until the repo is repaired or recloned

Practical consequence:

- Avoid depending on Git history for recovery right now
- Treat file-level backups and cautious patching as important
- Plan a repo health check / backup step before any risky refactor or cleanup work

## Risks and Gaps

High priority risks:

- Ambiguous canonical codebase between `lz-network-optimizer/` and `cassava-4g-network-optimiser/`
- Git repository packfile corruption
- Shared VM with live port collisions and unrelated containers
- Tight coupling between backend API and `ui/` helper modules in `lz-network-optimizer/`
- Refactor branch drift between implementation, tests, docs, and imports

Medium priority risks:

- Stale top-level docs that no longer describe the workspace accurately
- Large amount of historical/reference material increases accidental confusion
- Live integration tests may be hard to run safely in this environment
- Credentials and operational assumptions may be spread across multiple historical formats

Lower priority but worth tracking:

- Duplicated domain concepts across generations
- Mixed naming: Liquid Zimbabwe, Cassava, NetGenix, and older internal labels
- Multiple UI paradigms coexisting

## Recommended Decision

### Near-Term Working Base

Use `lz-network-optimizer/` as the working product base for today's feature work and stabilization.

### Role of `cassava-4g-network-optimiser/`

Use it as:

- a source of architecture ideas
- a source of cleaner package/service patterns
- a future migration target only after drift is reduced

Do not switch the main execution path to it yet unless the explicit next task is "repair the refactor branch."

### Role of `legacy/`

Use as reference-only. Pull patterns intentionally, not wholesale.

## Priority Work Queue

### Immediate

1. Establish durable project memory files in `docs/`
2. Normalize the source-of-truth statement:
   - current base
   - reference-only folders
   - current ports
   - known runtime constraints
3. Repair or back up the Git repo before any high-risk cleanup

### High Value Stabilization

1. Audit `lz-network-optimizer` for backend-to-UI coupling and identify extraction seams
2. Verify the actual local run path and document exact commands and ports
3. Classify tests into:
   - safe local
   - live external dependency
   - historical/obsolete

### Next Architectural Work

1. Compare the best patterns in `cassava-4g-network-optimiser` against the current runtime branch
2. Define a selective migration strategy rather than a big-bang switch
3. Start moving shared logic into a real service layer

## Suggested Interpretation for Today's Work

Based on the assessment so far, the most productive path is:

- continue from `lz-network-optimizer/`
- use the new docs as repo memory
- choose today's implementation task from either:
  - runtime stabilization
  - architecture cleanup around service extraction
  - selective lift of a good idea from the refactor branch

