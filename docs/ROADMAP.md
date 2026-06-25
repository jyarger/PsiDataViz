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
- **3D structure viewer** — **3Dmol.js** renders structure files and a computational job's optimized
  geometry beside the data; **vibrational normal modes animate** (pick a mode, or click the spectrum peak).
- **PsiDataViz app** — FastAPI backend + React/TS frontend, single-image deploy. **QUICK** tab
  (scan → filter → overlay → compare → convert) and **DATA** tab (multi-source workspace).
- **Open source** — public repo, Apache-2.0, CI (lint + tests + build), issue/PR templates.

## Next up  ·  *immediate sequence*

1. **More public-source connectors** ([#4](https://github.com/jyarger/PsiDataViz/issues/4)) — **Dropbox**
   and **Box** keyless public folders (sample-organized data); **Proton Drive** is E2E-encrypted and may
   not allow a keyless server-side scan (investigate / likely defer).
2. **More parsing breadth & robustness** (§1) — close the highest-count gaps from the live coverage panel:
   **TGA**, `.gjf`/`.inp` geometries, per-file load-failure reasons, and additional proprietary-format
   guidance; keep `sniff()` honest.
3. **Sample-centric catalog** (§2) — deep-parse headers to recover sample *and* instrument regardless of
   folder layout; browse by compound. (Introduces the first database.)
4. Then the **advanced ANALYSIS / VISUALIZATION tabs** (§3), **large-dataset handling** (§5), and
   **VPS deploy + domain** (§6).

## Prioritized plan

### 1 — Parsing breadth & robustness  ·  *highest priority*

The core mission. PsiDataViz is only as useful as the formats it can read.

- **Parse-diagnostics framework** ✅ — the scan reports a **coverage %** and the **formats present but
  unread, ranked by count** (a "Parsing coverage" panel in QUICK), with a one-click data-format request.
  Makes coverage gaps visible and prioritizable. *Next:* per-file load-failure reasons, not just unread
  extensions.
- **Honest detection** — `sniff()` should never claim a format it can't actually decode (a scan must not
  flag a file "supported" that then fails to load).
- **Zip bundles** — a `.zip` is read as one dataset: vendor multi-file exports (Bruker TopSpin,
  SpinSolve) are assembled, otherwise the **most-confidently-parseable member is chosen via the full
  reader registry** (so an OPUS-`.0`-only or structure-only zip works), and **nested zips** are unwrapped.
  Zipping each dataset (all its formats together) is the recommended upload pattern — see
  [data-sources](data-sources.md#packaging-datasets-as-zip-recommended). *Next:* expand a zip that holds
  **several distinct datasets** into separate records (treat the zip as a mini-source).
- **New techniques** — XRD 1D (ASCII + PANalytical `.xrdml`/`.udf`), **2D XRD/SAXS detector images**
  (`.edf`, `.img` ADSC, `.mccd` MarCCD, `.tif`/`.raw.tif` via **FabIO**, NeXus `.h5` via h5py — shown as
  heatmaps), UV-Vis ASCII, and zipped Bruker/SpinSolve NMR readers are in. Calibrated detector frames are
  also **azimuthally integrated to a 1D pattern I(2θ)** from the header geometry (distance/centre/pixel/λ),
  shown alongside the heatmap. **Computed IR/Raman spectra** (GaussView `_ir.txt`/`_raman.txt` exports from
  Gaussian/ORCA/Psi4 frequency jobs, with the DFT method from the filename) read on a wavenumber axis for
  overlay on experiment. **Quantum-chemistry outputs** (`.log`/`.out`) are now parsed directly with
  **cclib** (Gaussian/ORCA/Q-Chem/NWChem/Psi4): vibrational frequencies + IR/Raman intensities are
  Lorentzian-broadened into spectra, and the optimized geometry + normal modes feed the 3D viewer (§3).
  Molecular **structure files** (`.xyz`/`.mol`/`.sdf`/`.pdb`/`.cif`) read too. Still to do: **TGA**,
  Gaussian/ORCA input files (`.gjf`/`.inp` geometry), per-file load-failure reasons in diagnostics, proper
  **pyFAI** corrections + arbitrary `.poni` calibration, more proprietary-binary export guidance, and more.

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

**QUICK stays simple** — scan, basic overlay/plot, basic 3D view, convert. The rich, **interactive,
linked-view** experiences live in **DATA / ANALYSIS / VISUALIZATION / ADVANCED**, where panels sync:
clicking a spectral feature drives the structure/other panels, and vice-versa (the QUICK
spectrum-peak → vibration animation is the simplest taste of this).

**Viewer strategy:** **3Dmol.js** is the default everywhere (lightweight; great for molecules + computed
normal modes). **Mol\*** is introduced in **ADVANCED/VISUALIZATION** specifically for **MD trajectories**
(the example data includes NAMD/GROMACS runs) and large/crystal structures, behind the existing viewer
abstraction — so we add the heavyweight tool only where it earns its keep, not as a wholesale swap.

Lives in the **ANALYSIS / VISUALIZATION** tabs (QUICK stays simple):

- **NMR** — NMRium-grade interactivity: referencing, peak picking, integration, phasing.
- **DSC** — select heating/cooling scans; glass transition; peak integration (enthalpy).
- **IR / Raman** — overlay experimental spectra with **computed** spectra (from Gaussian/ORCA/Psi4 …,
  now read via cclib).
- **3D structure viewer** (**3Dmol.js**) ✅ — molecular/crystal structure files
  (`.xyz`/`.mol`/`.sdf`/`.pdb`/`.cif`) and a computational job's **optimized geometry** (from cclib) render
  in an interactive viewer beside the data, so a Gaussian/ORCA `.log` shows its IR/Raman spectra *and* its
  molecule. **Vibrational normal modes animate** — pick a mode (frequency + IR strength, from cclib
  `vibdisps`) and the atoms oscillate along it, **or click the peak on the spectrum** to animate its mode.
  *Next:* cube files (MOs/density) and crystal unit cells; Mol\* behind a thin abstraction for large
  biomolecules. Tracked in [#5](https://github.com/jyarger/PsiDataViz/issues/5).
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
