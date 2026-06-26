# Design / scoping — Sample-centric catalog

**Status:** draft for review (not yet implemented). **Owner:** @jyarger + Claude.
This folds in the overnight review comments on metadata, chemical identity, formats, and deployment.

---

## 1. The problem & the goal

Today PsiDataViz organizes data **by instrument/technique folder** (or infers a technique from a
filename). The recurring pain — called out in review — is that **stored datasets rarely carry enough
about *what* was measured**: the exact instrument, the sample/chemical, conditions, date, operator. This
is worst for bare `.csv`/`.txt`.

**Goal (the north star):** let a researcher browse their data **by sample/compound** — every measurement
of, say, *aspirin* (NMR + DSC + FTIR + computed) gathered in one place, across every connected source —
and make each dataset **self-describing** by capturing the missing metadata (interactively if needed) and
writing it back into an open, standard format.

Two concrete uses:
1. **Browse by compound** across sources (needs a catalog/DB + sample/instrument extraction).
2. **Organize & re-save**: point at / drop a pile of data → PsiDataViz parses it, lets the user fill in
   sample/instrument details, and **re-exports each dataset** in a consistent, information-rich format
   (CSDM / JCAMP-DX / tidy CSV) with identifiers embedded.

---

## 2. Sample identity (chemical) — **SMILES-first**

A "sample" is keyed by a **canonical chemical identity**. Priority, per review:

| Identifier | Role | Notes |
| --- | --- | --- |
| **SMILES** | **primary** | canonicalized; the default we read & write |
| **InChI / InChIKey** | strong key | the InChIKey is the dedup/lookup key (hashable, exact) |
| **CAS RN** | cross-reference | `##CAS REGISTRY NO=` in JCAMP |
| **IUPAC name** | human label | recognized on input; not a reliable key |
| **Molecular formula** | coarse group | `##MOLECULAR FORMULA=` in JCAMP |

- **Canonicalization & conversion** (name⇄SMILES⇄InChI⇄formula) needs a cheminformatics toolkit.
  Candidate: **RDKit** (BSD, the standard) — optional dependency, used server-side. Open question:
  RDKit is a heavyweight wheel; acceptable as a `[chem]` extra in the Docker image?
- **Dedup key:** the **InChIKey** (derived from SMILES via RDKit) groups measurements of the same
  molecule even when users type different SMILES/names.
- Where a structure already exists (computational `.xyz`/`.mol`, or a `.cif`), we can derive SMILES from
  the geometry (RDKit) and link it to the sample.

---

## 3. Where metadata comes from (3 tiers)

1. **Parsed from the file** — readers already extract sample_name/instrument/date where the format has it
   (DSC Trios, JCAMP, OPUS, TGA, …). Best case.
2. **Inferred from the filename/folder** — current `infer_technique` + filename date/description parsing.
3. **Interactive user input** — a metadata panel on the loaded dataset where the user fills/cures:
   **sample** (SMILES / name / CAS / InChI), **instrument** (make/model), conditions (solvent, temp,
   atmosphere), operator, date, location, notes. Pre-filled from tiers 1–2; user confirms/edits.

This interactive layer is valuable **even before a database** — it powers the "re-save" use case.

---

## 4. Re-save in an information-rich standard format

Encourage (and make one-click) conversion to a **self-contained** format with all the curated metadata
embedded. Per review, lead with **CSDM** and **JCAMP-DX**, plus a **tidy CSV** fallback.

**JCAMP-DX header block** we would write (IUPAC CPEP labels, http://www.jcamp-dx.org/):
```
##TITLE=        Acetylsalicylic acid
##DATA TYPE=    INFRARED SPECTRUM
##SMILES=       CC(=O)OC1=CC=CC=C1C(=O)O
##CAS REGISTRY NO= 50-78-2
##MOLECULAR FORMULA= C9H8O4
##NAMES=        aspirin
... (existing ##XUNITS / ##YUNITS / data) ...
```
- **CSDM** (`.csdf`) already supported for export; extend its JSON with a structured
  `sample`/`instrument` block (CSDM has a metadata model for this).
- **Tidy CSV**: the curated fields as a header comment block + the long-form data.
- This directly attacks the "sparse csv/txt" problem: re-saved files become future-proof and FAIR-friendly.

> Docs will explain *why* CSDM/JCAMP-DX (standard labels, embedded identifiers) and link the standards.

---

## 5. The catalog & database

- **Before the DB (stateless):** keep the current scan→records flow; add the interactive-metadata +
  re-save layer (no persistence — the user downloads the enriched file). Ships value immediately.
- **The DB phase:** introduce **PostgreSQL** (standard container, per deployment pref) to persist the
  catalog so users can **browse by sample across sessions/sources**, with tags/labels and search.

**Sketch schema** (PostgreSQL):
```
samples(id, inchikey UNIQUE, smiles, iupac_name, cas_rn, formula, names[], created)
instruments(id, make, model, technique, …)
datasets(id, sample_id?, instrument_id?, technique, source_url, member, file_name,
         date, operator, conditions JSONB, params JSONB, created)
sources(id, url, kind, label, last_scanned)
tags(id, name) · dataset_tags(dataset_id, tag_id)
```
- `datasets.conditions/params` as **JSONB** keeps per-technique flexibility without schema churn.
- Sample resolution: on save, RDKit → InChIKey → upsert into `samples`; link the dataset.
- **Auth ties in here** — the `⟨Registration|Ψ|Login⟩` placeholder becomes real so uploads/catalog rows
  are per-user (deferred; the schema leaves room for `owner_id`).

---

## 6. Browse-by-compound UX

- A **"by Sample"** view (lives under **Ψ|Data⟩**): a searchable list/grid of samples (name + structure
  thumbnail via the 3D/2D viewer) → expand to every dataset of that molecule across sources, grouped by
  technique, each openable in the existing viewers.
- Complements the current **by-technique** view (a toggle: *by technique* ⇄ *by sample*).

---

## 7. FAIR repositories as sources (later)

- Add a **Chemotion** / FAIR-repo connector (review idea): point a DATA source at a repository like
  chemotion.net and index its chemical datasets. These repos expose APIs and already carry rich
  metadata + identifiers, so they slot into the same `samples`/`datasets` model.
- fairsharing.org as a directory/reference in the docs.

---

## 8. Deployment & portability (per review)

- **Everything in Docker.** Today: single image (frontend + FastAPI). Add a **`docker-compose`** with the
  app + a **`postgres:16`** container + a volume; `DATABASE_URL` env wires them.
- **Portable** to a self-hosted Linux mini-PC, an AWS account, or a Hostinger VPS — compose is the common
  denominator; no cloud-specific services in the core.
- **Cloudflare** for DNS + reverse proxy / TLS in front of the app (the app stays HTTP on its port behind
  the tunnel/proxy). Document the Cloudflare Tunnel + compose setup for the **PsiDataViz** domain.
- DB migrations via a lightweight tool (Alembic) so schema changes are reproducible across hosts.

---

## 9. Phased rollout (proposed)

1. **Interactive metadata panel** — editable sample/instrument/conditions fields on a loaded dataset
   (pre-filled from parse/inference). *No DB.*
2. **Chemical identity** — RDKit `[chem]` extra; SMILES/InChIKey/CAS/formula resolution + a small
   structure preview. *No DB.*
3. **Enriched re-save** — write the curated metadata into CSDM / JCAMP-DX (`##SMILES=` etc.) / tidy CSV.
   *Delivers the "organize & re-save" use case with zero persistence.*
4. **PostgreSQL catalog + compose** — persist samples/datasets; **browse-by-sample** view; tags/search.
5. **Auth** (`⟨Registration|Ψ|Login⟩`) — per-user catalogs & uploads.
6. **FAIR-repo connector** (Chemotion) + the deployment/Cloudflare playbook.

Phases 1–3 are independently shippable and high-value; 4 is the real "catalog"; 5–6 follow.

---

## 10. Open questions for review

1. **RDKit** as a server-side `[chem]` extra (heavier image) — OK? Or a lighter identifier approach first
   (store SMILES/CAS as given, defer canonicalization)?
2. **Where does enriched re-save write?** Download-only at first (stateless), or also write back to the
   source where possible (e.g., a GitHub PR / a user upload area)?
3. **Browse-by-sample placement** — under **Ψ|Data⟩** (as proposed), or its own area?
4. **Auth scope** for v1 of the DB — single-user/self-host first, or multi-user from the start?
5. **Conditions taxonomy** — fixed common fields (solvent, temperature, atmosphere, …) vs. free-form
   JSONB only?
