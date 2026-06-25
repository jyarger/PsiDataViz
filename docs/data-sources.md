# Data sources

PsiDataViz reads data from **public** locations with **no account and no API key**. You give it a public
link; it lists the files, groups them into datasets, and parses them on demand.

## Supported today

### GitHub repositories

Paste a repo URL or `owner/repo`. Two cheap REST calls (resolve the default branch, then one recursive
git-tree listing) enumerate every file; contents are fetched lazily from `raw.githubusercontent.com`.
Setting a read-only `GITHUB_TOKEN` raises the API rate limit but is optional.

### Google Drive folders (keyless)

Share a folder as **"Anyone with the link"** and paste its URL. PsiDataViz walks the folder's
`embeddedfolderview` HTML — no Drive API key required — recursing into sub-folders (concurrently) and
downloading file bytes from `uc?export=download`. The large-file virus-scan interstitial is handled
automatically.

**How to share a Drive folder:**
1. Right-click the folder → **Share**.
2. Under *General access*, choose **Anyone with the link**.
3. Copy the link and paste it into PsiDataViz.

## Planned

- **Dropbox**, **Box**, and **Proton Drive** public shares (Codeberg is supported)
  (tracked in [#4](https://github.com/jyarger/PsiDataViz/issues/4)).
- Provider buttons in the connect-helper; generalist research repositories (Zenodo, Figshare, Dryad,
  OSF, Mendeley Data); drag-and-drop and private/authenticated sources.

`make_source(url)` routes a URL to the right connector, and every connector implements the same
`DataSource` interface, so the catalog, app, and conversions work identically across sources.

## Example data (the PsiData collection)

The Yarger Lab publishes the same example data in several public locations:

| Location | Organized by | Status |
| --- | --- | --- |
| [GitHub `yargerlab/Data`](https://github.com/yargerlab/Data) | technique | ✅ supported |
| [Google Drive `Psi_Data`](https://drive.google.com/drive/folders/16VQhcRbCHkzhH2cq8T5DwyhTUBj2BrO4) | technique | ✅ supported |
| Proton Drive | technique | planned |
| Dropbox | sample / compound | planned |
| Box | sample / compound | planned |
| [Codeberg `jyarger/PsiData`](https://codeberg.org/jyarger/PsiData) | sample / compound | ✅ supported |

The *technique*-organized sources have top-level folders per instrument (`DSC/`, `NMR/`, …); the
*sample*-organized ones have a folder per compound (`Aspirin/`, `CBD/`, …) — see
[the roadmap](ROADMAP.md)'s sample-centric phase.

## From files to datasets

Scanning is **metadata-only** (no downloads). For each discovered file:

1. **Group by base name.** Files that share a stem across extensions become one **`DataRecord`** with
   several **format variants** — e.g. `…_DSC.csv` + `…_DSC.tri` + `…_DSC.xls` is *one* dataset available
   in three formats. Variants are classified as data, binary-original, spreadsheet, sidecar, or image.
2. **Assign a technique.** Taken from the top-level folder and normalized to a canonical label
   (`canonical_technique()` maps `IR`/`FT-IR`/`infrared` → `FTIR`, `UV_Vis` → `UV-Vis`, …) so the same
   technique from different sources merges into one group.
3. **Flag support.** A record is `supported` when a registered reader is likely to handle it. Opening it
   later fetches the bytes and fully parses them.

## Two ways labs organize data

PsiDataViz handles both — and aims to unify them:

- **By instrument / technique** — top-level folders like `DSC/`, `NMR/`, `FTIR/`, `Raman/` (how the
  example GitHub repo and Google Drive folder are arranged).
- **By sample / compound** — top-level folders named for the chemical (`Aspirin/`, `CBD/`, …), each
  holding mixed instrument and computational data for that molecule (how the example Box and Dropbox
  folders are arranged).

The [roadmap](ROADMAP.md)'s sample-centric phase deep-parses headers to recover the **sample** and
**instrument** for every dataset regardless of folder layout — so you can browse a molecule's complete
data picture across many sources.
