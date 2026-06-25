"""Data-access + serialization glue for the API. Thin wrappers over the psidata library."""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import asdict

import httpx
import numpy as np
from psidata import Candidate, Dataset, read, read_zip, zip_datasets
from psidata.readers.raman_text import parse_spec_sidecar
from psidata.sources import Catalog, FileRef, make_source
from psidata.sources.catalog import _technique_has_reader, build_entry
from psidata.sources.records import IMAGE

_listing_cache: dict[str, dict] = {}  # url -> {"label", "files"} (process-lifetime cache)


def scan_repo(url: str, *, use_cache: bool = True) -> Catalog:
    payload = _listing_cache.get(url) if use_cache else None
    if payload is None:
        src = make_source(url)
        try:
            payload = {"label": src.label, "files": [asdict(r) for r in src.list_files()]}
        finally:
            getattr(src, "close", lambda: None)()
        _listing_cache[url] = payload
    refs = [FileRef(**f) for f in payload["files"]]
    return Catalog(source_label=payload["label"], entries=[build_entry(r) for r in refs])


def _fetch_bytes(url: str) -> bytes:
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "githubusercontent" in url:
        headers["Authorization"] = f"Bearer {token}"
    resp = httpx.get(url, follow_redirects=True, timeout=120.0, headers=headers)
    resp.raise_for_status()
    return resp.content


def load_dataset(name: str, url: str, *, technique: str | None = None,
                 sidecar_url: str | None = None, member: str | None = None) -> Dataset:
    content = _fetch_bytes(url)
    if name.lower().endswith(".zip") or url.lower().endswith(".zip"):
        ds = read_zip(name, content, technique_hint=technique, member=member)
    else:
        ds = read(Candidate(filename=name, content=content, uri=url, technique_hint=technique))
    if sidecar_url:  # merge a Raman *_spec.txt companion (laser/power/spectrometer) into metadata
        try:
            ds.metadata.extra.update(parse_spec_sidecar(_fetch_bytes(sidecar_url).decode("utf-8", "replace")))
        except Exception:  # noqa: BLE001  a missing/odd sidecar must never break the dataset
            pass
    return ds


def zip_bundle(name: str, url: str, *, technique: str | None = None) -> list[dict]:
    """The distinct datasets inside a zip (empty for a non-zip or single-dataset zip). Cheap: the bytes
    are already cached by ``_fetch_bytes`` from the dataset load."""
    if not (name.lower().endswith(".zip") or url.lower().endswith(".zip")):
        return []
    members = zip_datasets(name, _fetch_bytes(url), technique_hint=technique)
    return members if len(members) > 1 else []


# --- JSON serialization -----------------------------------------------------------------------
def scan_summary(catalog: Catalog) -> dict:
    summary = catalog.summary()
    groups = catalog.record_groups()
    techniques = [
        {
            "technique": tech,
            "n_datasets": sum(r.is_data_record for r in recs),
            "n_supported": sum(r.supported for r in recs),
        }
        for tech, recs in groups.items()
        if any(r.is_data_record for r in recs)
    ]
    techniques.sort(key=lambda t: (-t["n_supported"], t["technique"]))
    return {
        "source": summary["source"],
        "n_files": summary["n_files"],
        "n_records": summary["n_records"],
        "n_data_records": summary["n_data_records"],
        "n_supported_records": summary["n_supported_records"],
        "techniques": techniques,
        "diagnostics": _diagnostics(groups, summary),
    }


# Recognized formats we can't (or won't) parse directly, with guidance. (note, how-to-convert).
_FORMAT_NOTES: dict[str, tuple[str, str | None]] = {
    ".tri": ("TA Instruments Trios proprietary binary (DSC)",
             "Export to .txt or .xls from Trios — PsiDataViz reads those."),
    ".sp": ("PerkinElmer FTIR proprietary binary", "Export to .dpt or .csv from Spectrum."),
    ".spa": ("Thermo OMNIC proprietary binary (IR)", "Export to JCAMP (.dx) or .csv from OMNIC."),
    ".spc": ("Galactic/Thermo SPC proprietary binary", "Export to ASCII / .csv."),
    ".spf2": ("Spectrometer proprietary binary (UV-Vis)", "Export to .csv or .txt."),
    ".chk": ("Gaussian checkpoint (binary state, not a spectrum)",
             "Use the .log, or the exported _ir.txt / _raman.txt."),
    ".gbw": ("ORCA binary wavefunction (not a spectrum)", "Use the ORCA .out."),
    ".densities": ("Computational density data (not a spectrum)", None),
    ".densitiesinfo": ("Computational density metadata", None),
    ".itp": ("GROMACS topology (molecular dynamics)", None),
    ".gro": ("GROMACS coordinates (molecular dynamics)", None),
    ".bibtex": ("Bibliography / references (not data)", None),
}


def _diagnostics(groups: dict, summary: dict) -> dict:
    """What didn't parse and why — coverage plus the formats present but unread, ranked by count.

    Drives the iterate-on-coverage loop: the highest-count unread extensions are where adding a reader
    helps most. ``unread_formats`` counts the data-variant extensions of datasets with no usable reader,
    annotated with guidance for formats we recognize as proprietary/binary (e.g. ``.tri``).
    """
    unread: Counter[str] = Counter()
    unread_techniques: Counter[str] = Counter()
    unread_items: list[dict] = []
    for tech, recs in groups.items():
        for r in recs:
            if r.is_data_record and not r.supported:
                unread_techniques[tech] += 1
                for v in r.data_variants:
                    unread[v.ext] += 1
                unread_items.append(_unread_item(r, tech))
    n_data = summary["n_data_records"]
    n_ok = summary["n_supported_records"]
    return {
        "coverage": round(100 * n_ok / n_data, 1) if n_data else 0.0,
        "n_supported": n_ok,
        "n_unsupported": n_data - n_ok,
        "unread_formats": [_unread_entry(ext, n) for ext, n in unread.most_common(14)],
        "unread_by_technique": [{"technique": t, "count": n}
                                for t, n in unread_techniques.most_common()],
        "unread_items": unread_items[:60],  # per-dataset breakdown (which files, and why)
    }


def _unread_item(record, technique: str) -> dict:
    """Why one dataset isn't readable: its data extensions plus the most specific reason we can give
    without downloading it (a known proprietary/binary note, else 'no reader yet')."""
    exts = sorted({v.ext for v in record.data_variants})
    noted = next((e for e in exts if e in _FORMAT_NOTES), exts[0] if exts else "")
    note = _FORMAT_NOTES.get(noted)
    name = record.data_variants[0].file.name if record.data_variants else record.key
    if note:  # a known proprietary/binary/non-data format -> the specific guidance
        reason, hint = note[0], note[1]
    elif not _technique_has_reader(technique):  # the whole technique has no reader yet
        reason, hint = f"No reader for {technique} data yet", None
    else:  # technique is read, but not this particular format
        reason, hint = f"No reader for {noted or 'this format'} yet", None
    return {"name": name, "technique": technique, "formats": exts, "reason": reason, "hint": hint}


def _unread_entry(ext: str, count: int) -> dict:
    entry = {"ext": ext, "count": count}
    note = _FORMAT_NOTES.get(ext)
    if note:
        entry["note"] = note[0]
        if note[1]:
            entry["hint"] = note[1]
    return entry


def record_row(record) -> dict:
    data_exts = sorted({v.ext for v in record.data_variants})
    extras = []
    if record.sidecars:
        extras.append("params")
    if any(v.info.role == IMAGE for v in record.variants):
        extras.append("img")
    spec = next((v for v in record.sidecars if v.file.name.lower().endswith("_spec.txt")), None)
    return {
        "key": record.key,
        "uid": record.uid,
        "technique": record.technique,
        "date": record.parsed.date.isoformat() if record.parsed.date else None,
        "description": record.parsed.description,
        "formats": data_exts,
        "extras": extras,
        "primary": record.primary.ext,
        "name": record.primary.file.name,
        "url": record.primary.file.download_url,
        "sidecar_url": spec.file.download_url if spec else None,
    }


def dataset_json(dataset: Dataset, max_points: int = 4000) -> dict:
    meta = {k: v for k, v in dataset.metadata.model_dump().items() if v not in (None, [], {})}
    meta.update(meta.pop("extra", {}))  # surface sidecar fields (laser/power/…) at the top level
    return {
        "technique": dataset.technique,
        "filename": dataset.source.filename,
        "reader": dataset.source.reader,
        "metadata": meta,
        "signals": [
            {
                "name": sig.name,
                "segment": sig.segment,
                "x": {"label": sig.x.label, "unit": sig.x.unit, "quantity": sig.x.quantity},
                "y": {"label": sig.y.label, "unit": sig.y.unit, "quantity": sig.y.quantity},
                "points": _downsample(sig.frame[sig.x.label].to_numpy(),
                                      sig.frame[sig.y.label].to_numpy(), max_points),
            }
            for sig in dataset.signals
        ],
        "images": [_image_json(im) for im in dataset.images],
        "structure": (
            {
                "data": dataset.structure.data,
                "format": dataset.structure.fmt,
                "title": dataset.structure.title,
                "n_atoms": dataset.structure.n_atoms,
                "modes": [
                    {"freq": m.freq, "ir": m.ir, "raman": m.raman, "disps": m.disps}
                    for m in dataset.structure.modes
                ],
            }
            if dataset.structure else None
        ),
    }


def _image_json(image, max_side: int = 240) -> dict:
    """Downsample a 2D image (block max-pool) and log-scale it for compact, viewable transport."""
    a = image.data
    rows, cols = a.shape
    step = max(1, -(-max(rows, cols) // max_side))  # ceil division -> longest side <= max_side
    if step > 1:  # block max-pool keeps diffraction peaks/rings visible
        r, c = (rows // step) * step, (cols // step) * step
        a = a[:r, :c].reshape(r // step, step, c // step, step).max(axis=(1, 3))
    z = np.log1p(np.clip(np.nan_to_num(a, nan=0.0), 0, None))
    return {
        "name": image.name,
        "x": {"label": image.x.label, "unit": image.x.unit},
        "y": {"label": image.y.label, "unit": image.y.unit},
        "z": {"label": image.z.label, "unit": image.z.unit, "scale": "log1p"},
        "shape": [int(rows), int(cols)],
        "values": np.round(z, 3).tolist(),
    }


def _downsample(x: np.ndarray, y: np.ndarray, max_points: int) -> list[list[float]]:
    """Min/max decimation — preserves spectral peaks while bounding transport size."""
    n = len(x)
    if n <= max_points:
        return [[float(xi), float(yi)] for xi, yi in zip(x, y, strict=False)]
    bucket = max(1, n // (max_points // 2))
    points: list[list[float]] = []
    for i in range(0, n, bucket):
        xs, ys = x[i:i + bucket], y[i:i + bucket]
        if len(ys) == 0:
            continue
        lo, hi = int(np.argmin(ys)), int(np.argmax(ys))
        for j in sorted({lo, hi}):
            points.append([float(xs[j]), float(ys[j])])
    return points
