<h1 align="center">Ψ PsiDataViz</h1>

<p align="center">
  <b>Organize, parse, convert, and visualize experimental &amp; computational scientific data —
  from any public link, no account or API key required.</b>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: Apache-2.0" src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"></a>
  <img alt="Tests" src="https://img.shields.io/badge/tests-96%20passing-success">
  <img alt="Python" src="https://img.shields.io/badge/python-3.12-blue">
</p>

---

Every lab accumulates a sprawl of instrument and computational data in dozens of formats, scattered
across folders and cloud drives. **PsiDataViz** points at a *public* data location — a GitHub repo, a
Google Drive folder, (soon) Box and Dropbox — scans it, makes sense of the formats, and lets you
filter, overlay, compare, and convert datasets in your browser.

The name: *sci* and *psi* are homophones, and **Ψ** is a science-coded Greek letter — so the project,
library, and app share the **Psi** prefix and the **Ψ** mark.

- **`psidata`** — a framework-agnostic, pip-installable Python library: the universal data model,
  a confidence-scored reader registry, source connectors, and format conversion. Works standalone in
  scripts, marimo, or Jupyter. *“ΨData — Scientific Data.”*
- **PsiDataViz** — the web app (FastAPI + React) on top of it. *“ΨDataViz — Scientific Data Visualization.”*

## Highlights

- **Point-and-scan, keyless.** Public **GitHub** repos and **Google Drive** folders scan with no
  credentials. Files that share a base name across formats collapse into one *dataset*.
- **Readers today:** DSC (TA Trios), NMR (JCAMP-DX incl. ASDF & Nanalysis NMReady FID→spectrum, `.tsv`,
  2D TopSpin `totxt`, **zipped Bruker & SpinSolve** datasets), FTIR (Bruker `.dpt`, JCAMP, PerkinElmer
  `.asc`), Raman, XRD (1D `.xy` + PANalytical `.csv`/`.dat`/`.asc`), UV-Vis (`.txt` + Thorlabs `.csv`).
  *(More formats — 2D XRD detector images, computational outputs — are the active focus; see the
  [roadmap](docs/ROADMAP.md).)*
- **QUICK tab** — one source: scan → filter by technique → overlay → compare formats → convert/download.
- **DATA tab** — a multi-source *workspace*: add several public sources, then filter and overlay datasets
  across all of them.
- **Convert** any dataset to **CSDM, HDF5, CSV, Parquet, Feather,** or per-signal **CSV (zip)**.
- **Single-image deploy.** One container serves the React UI and the API together.

## Quickstart

### Run with Docker (the whole app)

```bash
git clone https://github.com/jyarger/PsiDataViz.git
cd PsiDataViz
docker build -t psidataviz . && docker run --rm -p 8070:8000 psidataviz
# open http://localhost:8070
```

### Develop locally

Prerequisites: [`uv`](https://docs.astral.sh/uv/) (Python) and Node 20+.

```bash
# Python library + backend (installs the uv workspace into .venv)
uv sync --all-packages --all-extras

# Backend API on :8000
uv run --package psidata-backend psidata-api

# Frontend dev server on :5173 (in another terminal), proxying /api -> :8000
cd apps/frontend && npm install && npm run dev
```

### Use the library on its own

```python
from psidata import read, Candidate
ds = read(Candidate(filename="spectrum.dx", content=open("spectrum.dx", "rb").read()))
print(ds.technique, ds.signals[0].x.label, ds.signals[0].npoints)
```

## Repository layout (uv workspace monorepo)

```
PsiDataViz/
├── packages/psidata/        # ★ the standalone, pip-installable science library
│   └── src/psidata/         #   model · registry · readers/ · sources/ · convert/ · export
├── apps/
│   ├── backend/             # FastAPI service (scan, records, dataset, catalog, convert, compare)
│   ├── frontend/            # React + TypeScript + Plotly UI
│   └── psidataviz-dash/     # interim Dash app (being retired)
├── docs/                    # ROADMAP, adding-a-reader, deploy
└── Dockerfile, docker-compose.yml, deploy/
```

## Documentation

Full docs live in **[`docs/`](docs/README.md)** — a wiki-style index covering the
[roadmap](docs/ROADMAP.md), [architecture](docs/architecture.md), [data sources](docs/data-sources.md),
[adding a reader](docs/adding-a-reader.md), [design decisions](docs/design-decisions.md), and
[deployment](docs/deploy.md).

## Contributing

PsiDataViz is open source under **Apache-2.0** — contributions, forks, and reuse are welcome. The most
valuable contributions right now are **new readers** for scientific data formats we don't yet cover.
See **[CONTRIBUTING.md](CONTRIBUTING.md)** and **[docs/adding-a-reader.md](docs/adding-a-reader.md)**, and
open a [data-format request](.github/ISSUE_TEMPLATE) for any format that fails to parse.

## License

Copyright © 2026 Jeffery L. Yarger (Yarger Lab). Licensed under the [Apache License 2.0](LICENSE) — free
to use, modify, and distribute, including commercially.
