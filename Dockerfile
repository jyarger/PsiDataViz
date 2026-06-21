# PsiDataViz v2 — single image: build the React frontend, serve it + the API from FastAPI/uvicorn.
# (The interim Dash app's Dockerfile is in git history; this is the primary deployment.)

# ---- stage 1: build the React frontend ----
FROM node:22-slim AS frontend
WORKDIR /fe
COPY apps/frontend/package.json apps/frontend/package-lock.json ./
RUN npm ci
COPY apps/frontend/ ./
RUN npm run build

# ---- stage 2: Python backend serving /api + the built static frontend ----
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    PSIDATA_STATIC_DIR=/app/static

WORKDIR /app

# Library first, then the backend (its `psidata` dependency is already satisfied locally).
COPY packages/psidata ./packages/psidata
RUN pip install ./packages/psidata
COPY apps/backend ./apps/backend
RUN pip install ./apps/backend

# Drop in the built SPA; FastAPI mounts it at / (see psidata_backend.main).
COPY --from=frontend /fe/dist ./static

EXPOSE 8000
CMD ["uvicorn", "psidata_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
