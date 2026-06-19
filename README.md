# MolViz — Visualize Experimental & Computational Molecular Science Data

A public, deployable web app that lets anyone point at a public repository of molecular-science
data (e.g. [`github.com/yargerlab/Data`](https://github.com/yargerlab/Data)), smartly summarizes
what's there, and visualizes selected datasets with interactive Plotly charts — with one-click
**export to marimo or Google Colab**.

Under the hood is a reusable, framework-agnostic Python library for **ingesting, parsing, reading,
and converting** a wide variety of scientific/computational data formats. The web app is a thin,
swappable layer on top.

## Status: v1 (work in progress)

v1 is deliberately narrow to prove the extensible framework:

- **Source type:** public GitHub repos.
- **Stateless:** no accounts, no database.
- **Supported formats:**
  - **DSC** — TA Instruments Trios exports, both `.txt` (tab-delimited) and `.csv` (comma-delimited);
    delimiter auto-detected.
  - **NMR** — JCAMP-DX spectra (`.jdx` / `.dx` / Agilent-Varian `.txt`) with plain `(XY..XY)` data.
    Compressed `(X++(Y..Y))` ASDF data is detected and rejected with a clear message (not yet decoded).
  - **FTIR** — Bruker `.dpt` data-point tables (and `.csv`/`.txt`/`.asc` in an FTIR folder).
  - **Raman** — `.csv` spectra (`shift, intensity[, …]`); extra intensity columns become separate traces.

Headerless formats (Raman/FTIR `.csv`) are disambiguated by the instrument folder they live in.
Adding a new technique (DFT, XRD, …) means writing one new *reader* and registering it — no changes
to the data model or the app.

## Architecture

```
src/molviz/
├── core/      # the durable, framework-agnostic ingestion library
│   ├── model.py      # Dataset / Signal / Axis / Metadata — universal container
│   ├── registry.py   # reader registry + confidence-scored auto-detection
│   ├── readers/      # one module per technique (dsc_trios.py, ...)
│   ├── filename.py   # YYYY_MM_DD_<desc> filename-convention parser
│   └── export.py     # Dataset(s) -> marimo .py / Colab .ipynb
├── sources/   # where files come from (GitHub first; abstract interface)
└── app/       # Plotly Dash app (Home -> Browse -> Visualize)
```

## Quick start (development)

Using [uv](https://docs.astral.sh/uv/) (recommended — resolves the project on any interpreter):

```bash
uv sync --extra dev --extra app
uv run pytest                  # run the test suite
uv run python -m molviz.app    # run the Dash app at http://127.0.0.1:8050
```

Plain pip/venv works too:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,app]"
pytest
python -m molviz.app
```

If your interpreter doesn't honor editable installs (some Anaconda-based setups don't), run the
app with the bundled launcher, which needs no install:

```bash
python serve.py
```

## Adding a new data reader

See [`docs/adding-a-reader.md`](docs/adding-a-reader.md). In short: subclass `BaseReader`,
implement `sniff()` (return a 0–1 confidence) and `read()` (return a `Dataset`), and decorate the
class with `@register_reader`. The registry and app pick it up automatically.
