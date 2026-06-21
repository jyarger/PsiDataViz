# PsiData / PsiDataViz — Roadmap

v1 (formerly *MolViz*) proved the core: scan a public GitHub data repo and visualize DSC / NMR /
FTIR / Raman via a Plotly-Dash app + a framework-agnostic Python library. v2 turns this into
**PsiData** (the library + ecosystem) and **PsiDataViz** (a modern visualization app).

## Architecture decision
Decoupled, nmrium-style: an async **FastAPI** backend wrapping the standalone **`psidata`** library
+ a **React/TypeScript (Vite)** frontend. The science stays in Python (pip-installable, notebook-ready);
the UI gets first-class polish, drag-and-drop, websockets/streaming for large data, native 3D molecular
viewers, and WebGL imaging.

## Phases
1. **Foundation & rebrand** ✅ (this phase) — uv-workspace monorepo; extract the standalone `psidata`
   library; rebrand to PsiData / PsiDataViz (Ψ, dark mode); keep the Dash app as an interim demo.
2. **Multi-format dataset intelligence** (in `psidata`) — group files sharing a base name across
   extensions into one *DataRecord* with multiple *FormatVariant*s; classify variants (data vs sidecar,
   e.g. Raman `_spec.txt`); verify equivalence and **diff** what differs between formats; surface in the
   catalog. *The major data-organization feature.*
3. **Standardized conversion** (`psidata.convert`) — export any parsed dataset to **HDF5**, **Zarr**,
   and **CSDM** (Core Scientific Dataset Model, via `csdmpy`). The "messy science data → standard format"
   tool.
4. **NMR depth** — JCAMP **ASDF (X++(Y..Y))** decoder for compressed Bruker `.jdx`; read **`.zip`**
   Bruker datasets (likely `nmrglue`) → ppm spectra; drag-and-drop loading.
5. **New web stack (PsiDataViz)** — FastAPI async backend (Arrow/Parquet transport, websocket streaming,
   server-side downsampling) + React/TS dashboard: nav **QUICK · DATA · ANALYSIS · VISUALIZATION ·
   ADVANCED**, footer **Tools · Resources · Contacts**, dark, animated, drag-and-drop, WebGL plotting
   (uPlot / Plotly.js GL). Defaults to a public example repo (no marketing CTAs). Retire the Dash app at
   parity.
6. **Embedded molecular/materials viewer** — Mol\*/NGL in the frontend; `psidata` parses structures
   (CIF/XYZ/POSCAR/PDB) and computational outputs. Especially for DFT/computational data.
7. **More data types** — XRD (x,y ASCII *and* 2D detector images: TIFF/specialized), DFT/computational,
   TEM/SEM imaging, Acoustic Interferometry. Each is a `psidata` reader (+ viewer where needed).

## Cross-cutting
- **Docs/tutorials** built in throughout (Resources section).
- **Publish `psidata` to PyPI** — fixes the marimo/Colab exports' `pip install psidata`.
- **Viz tech:** for large scientific data, prefer **WebGL/canvas** (uPlot / Plotly.js GL) over
  Vega-Altair as the primary web renderer; keep optional Altair/Plotly helpers in `psidata` for notebooks.
