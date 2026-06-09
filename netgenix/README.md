# NetGenix

NetGenix is the canonical consolidated network optimisation product for the Cassava/Liquid Zimbabwe 4G work.

It starts from the runnable `lz-network-optimizer` React + FastAPI flow, while progressively moving toward the cleaner architecture ideas from `cassava-4g-network-optimiser`. Streamlit remains reference/lab material only.

## Current Shape

- `frontend/`: React/Vite operator dashboard.
- `backend/`: FastAPI backend preserving the existing optimisation API contract.
- `backend/netgenix/services/`: backend services for database, optimisation workflow, and Huawei NBI diagnostics.
- `backend/netgenix/reports/`: deterministic v2 reporting formulas.
- `agents/`, `domain/`, `network/`, `tools/`, `prompts/`: copied optimisation engine material.
- `data/`: required local historical/demo database assets.
- `docs/`: iMaster MAE, v2, v3, assessment, and operating context docs.

## Local Ports

- Backend: `8510`
- Frontend: `8511`

## Start Backend

```bash
cd netgenix
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8510
```

## Start Frontend

```bash
cd netgenix/frontend
npm ci
VITE_API_URL=http://localhost:8510 npm run dev -- --host 0.0.0.0 --port 8511
```

## Verify

```bash
curl -i http://localhost:8510/health
curl -s http://localhost:8510/api/sites
curl -s http://localhost:8510/api/status
curl -s http://localhost:8510/api/diagnostics/nbi
curl -i http://localhost:8511/
```

Known local historical/demo sites:

- `MSH-0014-Chipadze`
- `MSH-0112-Bindura Hospital`
- `MSH-0331-Chiwaridzo 2`
- `MSH0013-Bindura-Zaoga`

## Safety Defaults

MML execution remains dry-run first. Live Huawei credentials are loaded only from environment variables and must not be committed.

## Reporting

The v2 reporting path is file-first:

- Upload CSV/XLSX exports through the dashboard Reports tab.
- Backend computes deterministic site metrics and top/bottom rankings.
- Generated Excel and audit JSON are written under ignored `runtime/reports/`.
- API endpoints:
  - `POST /api/reports/imports`
  - `GET /api/reports/runs/{run_id}/download`
