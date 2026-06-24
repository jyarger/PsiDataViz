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
  FTIR (`.dpt`, JCAMP, PerkinElmer `.asc`), Raman, XRD (1D `.xy` / PANalytical `.csv` / `.dat` / `.asc`),
  UV-Vis (`.txt` / Thorlabs `.csv`).
- **Sources** — keyless **GitHub** and **Google Drive** connectors behind one `make_source()` factory;
  technique-folder normalization (e.g. `IR` → `FTIR`).
- **PsiDataViz app** — FastAPI backend + React/TS frontend, single-image deploy. **QUICK** tab
  (scan → filter → overlay → compare → convert) and **DATA** tab (multi-source workspace).
- **Open source** — public repo, Apache-2.0, CI (lint + tests + build), issue/PR templates.

## Prioritized plan

### 1 — Parsing breadth & robustness  ·  *highest priority*

The core mission. PsiDataViz is only as useful as the formats it can read.

- **Parse-diagnostics framework** — surface, in the app, the files that were *unrecognized* or *failed to
  load*, **with the reason** (best-guess reader + confidence, or the error). Makes coverage gaps visible
  and prioritizable, and feeds the data-format issue tracker.
- **Honest detection** — `sniff()` should never claim a format it can't actually decode (a scan must not
  flag a file "supported" that then fails to load).
- **Close known gaps** — e.g. most `.zip` NMR datasets aren't recognized yet.
- **New techniques** — XRD 1D, UV-Vis ASCII, and zipped Bruker/SpinSolve NMR readers are in; still to do:
  2D XRD detector images (`.tif`/`.edf`/`.img`/`.h5`) and structured XRD (`.xrdml`/`.udf`), computational
  outputs (Gaussian / ORCA / Psi4 / …), TGA, and more — each a `psidata` reader.

### 2 — Sample-centric catalog  ·  *the north star*

- **More sources** — keyless **Box** and **Dropbox** public-folder connectors.
- **Organize by sample.** Some sources are organized by instrument (GitHub, Drive); others by chemical
  (Box/Dropbox folders named `Aspirin`, `CBD`, …). Deep-parse headers/notes to determine the **sample**
  and **instrument** for every dataset regardless of folder layout, then let users **browse by sample**.
- Introduces the project's first **database** + tags/labels for a searchable catalog.

### 3 — Advanced per-technique analysis & visualization

Lives in the **ANALYSIS / VISUALIZATION** tabs (QUICK stays simple):

- **NMR** — NMRium-grade interactivity: referencing, peak picking, integration, phasing.
- **DSC** — select heating/cooling scans; glass transition; peak integration (enthalpy).
- **IR / Raman** — overlay experimental spectra with **computed** spectra (from Gaussian/ORCA/Psi4 …).
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
