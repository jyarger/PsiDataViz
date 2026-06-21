# ΨData — Scientific Data

**ΨData** is a toolkit for **organizing, parsing, converting, and visualizing experimental &
computational scientific data**. Point it at a public repository of instrument/computational data
(e.g. [`github.com/yargerlab/Data`](https://github.com/yargerlab/Data)), and it makes sense of the
sprawl of formats every lab accumulates.

The name: *sci* and *psi* are homophones, and **Ψ** is a science-coded Greek letter — so the project,
library, and apps share the **Psi** prefix and the **Ψ** mark.

- **`psidata`** — the framework-agnostic Python library (parsing / model / conversion). Standalone and
  pip-installable; works in marimo / Jupyter. *"Scientific Data."*
- **ΨDataViz** — the visualization web app on top of it. *"Scientific Data Visualization."*

## Monorepo layout (uv workspace)

```
psidata/
├── packages/
│   └── psidata/              # ★ the standalone, pip-installable science library
│       └── src/psidata/      # model · registry · readers/ · sources/ · export · convert/
├── apps/
│   └── psidataviz-dash/      # interim Dash app (retired once the FastAPI + React UI lands)
│   # backend/ (FastAPI) and frontend/ (React+TS) arrive in a later phase
├── docs/                     # ROADMAP, adding-a-reader, deploy
├── serve.py                  # run the interim app locally
└── Dockerfile, docker-compose.yml, deploy/
```

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full v2 direction (dashboard UX, multi-format dataset
grouping, HDF5/Zarr/CSDM conversion, deeper NMR, FastAPI + React, an embedded 3D molecular viewer, and
more data types).

## Supported formats (today)
- **DSC** — TA Trios exports, `.txt` (tab) **and** `.csv` (comma); delimiter auto-detected.
- **NMR** — JCAMP-DX (`.jdx`/`.dx`/Agilent-Varian `.txt`), plain `(XY..XY)` data. Compressed
  `(X++(Y..Y))` ASDF is detected and rejected with a clear message (decoder is on the roadmap).
- **FTIR** — Bruker `.dpt` data-point tables (and `.csv`/`.txt`/`.asc`).
- **Raman** — `.csv` spectra (`shift, intensity[, …]`); extra intensity columns become separate traces.

Headerless formats (Raman/FTIR `.csv`) are disambiguated by the instrument folder they live in.

## Quick start (development)

```bash
uv sync --all-packages --all-extras     # creates .venv, installs both packages
python serve.py                          # ΨDataViz at http://127.0.0.1:8050  (dark mode)
```

Run the tests:

```bash
uv run pytest packages/psidata/tests apps/psidataviz-dash/tests
```

Use the library on its own (e.g. in a notebook):

```python
import psidata
ds = psidata.read(psidata.Candidate(filename="run.txt", text=open("run.txt").read()))
print(ds.technique, ds.summary())
```

> On machines whose interpreter doesn't reliably honor editable installs (some Anaconda setups),
> `serve.py` injects the workspace `src/` dirs so the app runs regardless; tests set `pythonpath`.

## Deploy

`docker compose up -d --build` runs ΨDataViz behind Caddy (automatic HTTPS). See
[`docs/deploy.md`](docs/deploy.md).

## Adding a new data reader

See [`docs/adding-a-reader.md`](docs/adding-a-reader.md): subclass `BaseReader`, implement `sniff()`
(0–1 confidence) and `read()` (return a `Dataset`), decorate with `@register_reader`. The registry and
app pick it up automatically.
