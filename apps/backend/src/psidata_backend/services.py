"""Data-access + serialization glue for the API. Thin wrappers over the psidata library."""

from __future__ import annotations

import os
from dataclasses import asdict

import httpx
import numpy as np
from psidata import Candidate, Dataset, read, read_zip
from psidata.sources import Catalog, FileRef, make_source
from psidata.sources.catalog import build_entry
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


def load_dataset(name: str, url: str, *, technique: str | None = None) -> Dataset:
    content = _fetch_bytes(url)
    if name.lower().endswith(".zip") or url.lower().endswith(".zip"):
        return read_zip(name, content, technique_hint=technique)
    return read(Candidate(filename=name, content=content, uri=url, technique_hint=technique))


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
    }


def record_row(record) -> dict:
    data_exts = sorted({v.ext for v in record.data_variants})
    extras = []
    if record.sidecars:
        extras.append("params")
    if any(v.info.role == IMAGE for v in record.variants):
        extras.append("img")
    return {
        "key": record.key,
        "technique": record.technique,
        "date": record.parsed.date.isoformat() if record.parsed.date else None,
        "description": record.parsed.description,
        "formats": data_exts,
        "extras": extras,
        "primary": record.primary.ext,
        "name": record.primary.file.name,
        "url": record.primary.file.download_url,
    }


def dataset_json(dataset: Dataset, max_points: int = 4000) -> dict:
    return {
        "technique": dataset.technique,
        "filename": dataset.source.filename,
        "reader": dataset.source.reader,
        "metadata": {k: v for k, v in dataset.metadata.model_dump().items() if v not in (None, [], {})},
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
