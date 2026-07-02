# Docker Image Optimisation Plan

**Status:** Deferred — implement after core platform is stable  
**Recorded:** 2026-06-09

---

## Current State

| Image | Estimated Size | Main Blocker |
|---|---|---|
| `netgenix-backend` | ~1.5–2 GB | langchain ecosystem |
| `netgenix-collector` | ~2–3 GB | Playwright + Chromium + google-generativeai |
| `netgenix-frontend` | ~50–100 MB | Already optimal |
| `netgenix-db` | 476 MB | TimescaleDB base — nothing to do |

Total stack: ~4–5 GB on disk.

---

## Optimisation 1 — Collector: Switch to Official Playwright Base Image

**Saving: ~300–400 MB, faster builds, more stable**

**Current (`collector/Dockerfile`):**
```dockerfile
FROM python:3.11-slim
RUN apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 ...
RUN playwright install chromium && playwright install-deps chromium
```

**Proposed:**
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy
# Chromium + all system deps already baked in
# No apt-get dep hunting, no playwright install step
```

**Why:** The official Microsoft Playwright image ships with a tested Chromium build and all system libraries pre-installed. Eliminates the fragile manual `apt-get` dep list and the `playwright install` layer (~300 MB download at build time).

---

## Optimisation 2 — Backend: Split API from Agent Worker

**Saving: ~500 MB–1 GB on the API image**

**Problem:** The backend image carries the full langchain stack (`langchain`, `langchain-core`, `langchain-community`, `langgraph`, + 3 provider packages) even though the FastAPI routes themselves don't import langchain at startup — only the optimizer workflow does.

**Proposed: two backend images**

`backend/Dockerfile.api` — lightweight, fast-starting:
```
fastapi, uvicorn, pydantic, psycopg2-binary, requests, PyYAML, openpyxl
```
~200 MB

`backend/Dockerfile.agents` — full LLM stack, used only when optimization runs:
```
everything above + langchain, langgraph, langchain-nvidia-ai-endpoints,
langchain-google-genai, langchain-mistralai
```
~1.5–2 GB

The agent worker could run as a separate service or be lazy-imported only when the `/api/optimize` endpoint is hit.

**Alternative (simpler):** Keep one image but audit and remove `langchain-community` if unused. It adds ~300 MB and most of its integrations are not used by the NetGenix agent chain.

---

## Optimisation 3 — Backend: Remove google-generativeai

**Saving: ~150–200 MB from the backend image**

`google-generativeai` (used for Gemini Vision CAPTCHA solving) is only needed in the **collector**, not the backend API. It currently gets pulled into the backend via `langchain-google-genai` which brings in `google-generativeai` as a transitive dep.

**Fix:** Pin `langchain-google-genai` to its minimal install in the backend requirements, or move CAPTCHA-specific deps entirely to `requirements-collector.txt`.

---

## Optimisation 4 — Multi-Stage Backend Build

**Saving: ~100–200 MB by excluding build tools from the final image**

```dockerfile
# Stage 1: build
FROM python:3.11-slim AS builder
RUN pip install --no-cache-dir -r requirements.txt --target /install

# Stage 2: runtime (no gcc, no libpq-dev)
FROM python:3.11-slim
COPY --from=builder /install /usr/local/lib/python3.11/site-packages
```

Removes `gcc` and `libpq-dev` from the final image layer.

---

## Implementation Order (when ready)

1. **Opt 1** (Playwright base image) — biggest bang, lowest risk, collector only
2. **Opt 3** (remove google-generativeai from backend) — straightforward dep split
3. **Opt 4** (multi-stage backend) — standard pattern, low risk
4. **Opt 2** (split API/agent images) — most impactful but requires refactoring the optimizer import path; do last

---

## Target State After Optimisation

| Image | Current | Target |
|---|---|---|
| `netgenix-backend` | ~1.5–2 GB | ~300–500 MB (API only) |
| `netgenix-collector` | ~2–3 GB | ~1.5–2 GB |
| `netgenix-frontend` | ~50–100 MB | ~50–100 MB (no change) |
| `netgenix-db` | 476 MB | 476 MB (no change) |
| **Total** | **~4–5 GB** | **~2.5–3 GB** |
