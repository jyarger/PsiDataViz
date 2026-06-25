# PsiDataViz — Roadmap

## Vision

Scientific data is scattered across instruments, formats, and cloud drives. PsiDataViz aims to:

1. **Read everything.** Parse and visualize *all* major kinds of experimental and computational
   scientific data — not just the four techniques supported today.
2. **Organize by sample, not just by instrument.** Let a researcher browse their data by the
   **chemical/compound/sample**, gathering every measurement of a molecule in one place — sourced from
   many public locations.
3. **Stay frictionless and open.** Public data scans with **no account and no API key**; the whole thing
   is open source (Apache-2.0) and self-hostable.

## Built so far

- **`psidata` library** — universal `Dataset`/`Signal`/`Axis`/`Metadata` model; a confidence-scored
  reader **registry**; file → `DataRecord` grouping (one dataset, many format variants) with format
  comparison; conversion to CSDM/HDF5/Zarr/CSV/Parquet/Feather.
- **Readers** — DSC, NMR (JCAMP-DX + ASDF, Nanalysis NMReady NTUPLES/FID→spectrum, `.tsv`, 2D `totxt`),
  FTIR (`.dpt`, JCAMP, PerkinElmer `.asc`, **Bruker OPUS `.0`** via brukeropusreader), Raman, XRD (1D —
  `.xy`, PANalytical `.csv`/`.xrdml`/`.udf`, `.dat`/`.asc`; 2D detector images via FabIO), UV-Vis
  (`.txt` / Thorlabs `.csv`), **Computational** (`.log`/`.out` via **cclib** → IR/Raman, plus GaussView
  `_ir.txt`/`_raman.txt`).
- **Sources** — keyless **GitHub**, **Google Drive**, and **Codeberg** connectors behind one
  `make_source()` factory; technique-folder normalization (e.g. `IR` → `FTIR`) and, for sample-organized
  sources, technique **inferred from the filename**.
- **PsiDataViz app** — FastAPI backend + React/TS frontend, single-image deploy. **QUICK** tab
  (scan → filter → overlay → compare → convert) and **DATA** tab (multi-source workspace).
- **Open source** — public repo, Apache-2.0, CI (lint + tests + build), issue/PR templates.

## Prioritized plan

### 1 — Parsing breadth & robustness  ·  *highest priority*

The core mission. PsiDataViz is only as useful as the formats it can read.

- **Parse-diagnostics framework** ✅ — the scan reports a **coverage %** and the **formats present but
  unread, ranked by count** (a "Parsing coverage" panel in QUICK), with a one-click data-format request.
  Makes coverage gaps visible and prioritizable. *Next:* per-file load-failure reasons, not just unread
  extensions.
- **Honest detection** — `sniff()` should never claim a format it can't actually decode (a scan must not
  flag a file "supported" that then fails to load).
- **Close known gaps** — e.g. most `.zip` NMR datasets aren't recognized yet.
- **New techniques** — XRD 1D (ASCII + PANalytical `.xrdml`/`.udf`), **2D XRD/SAXS detector images**
  (`.edf`, `.img` ADSC, `.mccd` MarCCD, `.tif`/`.raw.tif` via **FabIO**, NeXus `.h5` via h5py — shown as
  heatmaps), UV-Vis ASCII, and zipped Bruker/SpinSolve NMR readers are in. Calibrated detector frames are
  also **azimuthally integrated to a 1D pattern I(2θ)** from the header geometry (distance/centre/pixel/λ),
  shown alongside the heatmap. **Computed IR/Raman spectra** (GaussView `_ir.txt`/`_raman.txt` exports from
  Gaussian/ORCA/Psi4 frequency jobs, with the DFT method from the filename) read on a wavenumber axis for
  overlay on experiment. **Quantum-chemistry outputs** (`.log`/`.out`) are now parsed directly with
  **cclib** (Gaussian/ORCA/Q-Chem/NWChem/Psi4): vibrational frequencies + IR/Raman intensities are
  Lorentzian-broadened into spectra. Still to do: structures (`.xyz`/`.mol`/`.gjf`) + a 3D viewer
  ([#5](https://github.com/jyarger/PsiDataViz/issues/5)), TGA, proper pyFAI corrections + arbitrary
  `.poni` calibration, and more.

### 2 — Sample-centric catalog  ·  *the north star*

- **More sources** — **Codeberg** (Gitea) is in; keyless **Box**, **Dropbox**, and **Proton Drive**
  public-folder connectors next ([#4](https://github.com/jyarger/PsiDataViz/issues/4)).
- **Organize by sample.** Some sources are organized by instrument (GitHub, Drive); others by chemical
  (Codeberg/Box/Dropbox folders named `Aspirin`, `CBD`, …). A first step is in — when the top folder is a
  compound (no instrument reader), the technique is **inferred from the filename**. Next: deep-parse
  headers/notes to determine the **sample** *and* **instrument** for every dataset regardless of folder
  layout, then let users **browse by sample**.
- Introduces the project's first **database** + tags/labels for a searchable catalog.

### 3 — Advanced per-technique analysis & visualization

Lives in the **ANALYSIS / VISUALIZATION** tabs (QUICK stays simple):

- **NMR** — NMRium-grade interactivity: referencing, peak picking, integration, phasing.
- **DSC** — select heating/cooling scans; glass transition; peak integration (enthalpy).
- **IR / Raman** — overlay experimental spectra with **computed** spectra (from Gaussian/ORCA/Psi4 …,
  now read via cclib).
- **3D structure viewer** (**3Dmol.js**) — visualize the molecule / compound / crystal alongside its
  data: render a computational job's optimized geometry, then animate vibrational **normal modes** from a
  frequency calc so an IR/Raman peak maps to a molecular motion; cube files (MOs/density) and `.cif`
  crystals to follow. Mol\* behind a thin abstraction for large biomolecules/crystallography. Tracked in
  [#5](https://github.com/jyarger/PsiDataViz/issues/5).
- Multiple datasets per plot, and series/grids of subplots.

### 4 — Documentation & feedback

- Wiki-style docs with a table of contents (this `docs/` set is the start).
- An in-app **feedback form** (routed to the maintainer or stored for review).

### 5 — Large-dataset handling

Big NMR and image-based techniques (XRD/TEM/SEM produce large 2D arrays) need a strategy:
server-side downsampling, tiling/streaming, lazy loading, and Arrow/Parquet transport.

### 6 — Deployment

Reserve the **PsiDataViz** domain and deploy on a cloud VPS so anyone can use it for their own public
data, with clear install directions (see [deploy.md](deploy.md)).

## Principles

- **Keyless first** — public links should work with no credentials.
- **QUICK is simple, DATA/ANALYSIS/VISUALIZATION are advanced.**
- **Source- and format-agnostic core** — new sources and readers slot in without touching the app.
- **Honest about failure** — show what didn't parse and why, and iterate.
