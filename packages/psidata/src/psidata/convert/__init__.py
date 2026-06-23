"""Convert a parsed :class:`~psidata.Dataset` to standard scientific formats.

* **HDF5** and **Zarr** — array containers (one group per signal, x/y datasets + axis/metadata attrs).
  Need the optional ``[convert]`` extra (``pip install 'psidata[convert]'``).
* **CSDM** (``.csdf``) — the Core Scientific Dataset Model. Written directly as its lightweight JSON
  form, so it needs no extra dependency. Signals sharing the x-grid become dependent variables.
* **CSV / Parquet / Feather** — the dataset's signals as one tidy (long-form) table; Parquet/Feather
  need ``pyarrow`` (in the ``[convert]`` extra). **CSV-zip** is one CSV per signal in a ``.zip``.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

from ..model import Dataset

__all__ = ["convert", "to_csdm", "to_csv", "to_csv_zip", "to_feather", "to_hdf5", "to_parquet",
           "to_zarr"]


def _meta_attrs(dataset: Dataset) -> dict[str, Any]:
    attrs: dict[str, Any] = {"technique": dataset.technique}
    if dataset.source.filename:
        attrs["filename"] = dataset.source.filename
    if dataset.source.reader:
        attrs["reader"] = dataset.source.reader
    for key, value in dataset.metadata.model_dump().items():
        if value is None or value == [] or value == {}:
            continue
        attrs[key] = value if isinstance(value, (str, int, float, bool)) \
            else json.dumps(value, default=str)
    return attrs


def _signal_attrs(sig) -> dict[str, str]:
    return {
        "name": sig.name, "segment": sig.segment or "",
        "x_label": sig.x.label, "x_unit": sig.x.unit or "", "x_quantity": sig.x.quantity or "",
        "y_label": sig.y.label, "y_unit": sig.y.unit or "", "y_quantity": sig.y.quantity or "",
    }


def to_hdf5(dataset: Dataset, path: str | Path) -> str:
    try:
        import h5py
    except ImportError as exc:  # pragma: no cover
        raise ImportError("to_hdf5 needs the [convert] extra: pip install 'psidata[convert]'") from exc
    with h5py.File(str(path), "w") as f:
        for key, value in _meta_attrs(dataset).items():
            f.attrs[key] = value
        signals = f.create_group("signals")
        for i, sig in enumerate(dataset.signals):
            group = signals.create_group(f"signal_{i}")
            for key, value in _signal_attrs(sig).items():
                group.attrs[key] = value
            group.create_dataset("x", data=sig.frame[sig.x.label].to_numpy())
            group.create_dataset("y", data=sig.frame[sig.y.label].to_numpy())
    return str(path)


def to_zarr(dataset: Dataset, path: str | Path) -> str:
    try:
        import zarr
    except ImportError as exc:  # pragma: no cover
        raise ImportError("to_zarr needs the [convert] extra: pip install 'psidata[convert]'") from exc
    root = zarr.open_group(str(path), mode="w")
    for key, value in _meta_attrs(dataset).items():
        root.attrs[key] = value
    signals = root.create_group("signals")
    for i, sig in enumerate(dataset.signals):
        group = signals.create_group(f"signal_{i}")
        for key, value in _signal_attrs(sig).items():
            group.attrs[key] = value
        _zarr_write(group, "x", sig.frame[sig.x.label].to_numpy())
        _zarr_write(group, "y", sig.frame[sig.y.label].to_numpy())
    return str(path)


def _zarr_write(group, name: str, data) -> None:
    data = np.asarray(data)
    if hasattr(group, "create_array"):       # zarr v3
        arr = group.create_array(name, shape=data.shape, dtype=data.dtype)
    else:                                     # zarr v2
        arr = group.create_dataset(name, shape=data.shape, dtype=data.dtype)
    arr[:] = data


# --- CSDM (lightweight JSON) -------------------------------------------------------------------
_CSDM_UNITS = {"cm⁻¹": "1/cm", "°c": "deg_C", "a.u.": "", "arbitrary units": "", "": ""}


def _csdm_unit(unit: str | None) -> str:
    return _CSDM_UNITS.get((unit or "").lower(), unit or "")


def _csdm_dimension(x: np.ndarray, axis) -> dict:
    n = len(x)
    unit = _csdm_unit(axis.unit)
    diffs = np.diff(x)
    if n >= 2 and np.allclose(diffs, diffs[0], rtol=1e-4, atol=0) and diffs[0] != 0:
        return {
            "type": "linear", "count": int(n),
            "increment": f"{float(diffs[0])} {unit}".strip(),
            "coordinates_offset": f"{float(x[0])} {unit}".strip(),
            "label": axis.label,
        }
    return {"type": "monotonic",
            "coordinates": [f"{float(v)} {unit}".strip() for v in x],
            "label": axis.label}


def to_csdm(dataset: Dataset, path: str | Path | None = None) -> str:
    """Serialize to CSDM JSON. Returns the path if given, else the JSON text."""
    sig0 = dataset.signals[0]
    x = np.asarray(sig0.frame[sig0.x.label].to_numpy(), dtype=float)
    n = len(x)
    dependent = []
    for sig in dataset.signals:
        y = np.asarray(sig.frame[sig.y.label].to_numpy(), dtype=float)
        if len(y) != n:
            continue  # only signals sharing this x-grid become dependent variables
        dependent.append({
            "type": "internal", "numeric_type": "float64", "quantity_type": "scalar",
            "name": sig.segment or sig.name, "unit": _csdm_unit(sig.y.unit),
            "components": [y.tolist()],
        })
    doc = {"csdm": {
        "version": "1.0",
        "description": f"{dataset.technique} {dataset.source.filename or ''}".strip(),
        "dimensions": [_csdm_dimension(x, sig0.x)],
        "dependent_variables": dependent,
    }}
    text = json.dumps(doc)
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
        return str(path)
    return text


# --- tabular formats (one tidy/long-form table over all signals) ------------------------------
def _require_pyarrow(fn: str) -> None:
    try:
        import pyarrow  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        raise ImportError(f"{fn} needs the [convert] extra: pip install 'psidata[convert]'") from exc


def to_csv(dataset: Dataset, path: str | Path) -> str:
    dataset.to_tidy_df().to_csv(str(path), index=False)
    return str(path)


def to_parquet(dataset: Dataset, path: str | Path) -> str:
    _require_pyarrow("to_parquet")
    dataset.to_tidy_df().to_parquet(str(path), index=False)
    return str(path)


def to_feather(dataset: Dataset, path: str | Path) -> str:
    _require_pyarrow("to_feather")
    dataset.to_tidy_df().reset_index(drop=True).to_feather(str(path))
    return str(path)


def to_csv_zip(dataset: Dataset, path: str | Path) -> str:
    """One CSV per signal, bundled into a ``.zip`` (useful for multi-segment / multi-row datasets)."""
    with zipfile.ZipFile(str(path), "w", zipfile.ZIP_DEFLATED) as zf:
        for i, sig in enumerate(dataset.signals):
            label = re.sub(r"[^A-Za-z0-9._-]+", "_", sig.segment or sig.name)[:60] or "signal"
            zf.writestr(f"signal_{i}_{label}.csv", sig.frame.to_csv(index=False))
    return str(path)


def convert(dataset: Dataset, path: str | Path, fmt: str | None = None) -> str:
    """Dispatch by ``fmt`` (or path suffix): hdf5/h5 · zarr · csdf/csdm · csv · parquet · feather · zip."""
    fmt = (fmt or Path(str(path)).suffix.lstrip(".")).lower()
    dispatch = {
        "h5": to_hdf5, "hdf5": to_hdf5, "zarr": to_zarr, "csdf": to_csdm, "csdm": to_csdm,
        "csv": to_csv, "parquet": to_parquet, "feather": to_feather, "zip": to_csv_zip,
    }
    if fmt not in dispatch:
        raise ValueError(f"unknown convert format {fmt!r} "
                         "(use hdf5, zarr, csdf, csv, parquet, feather, or zip)")
    return dispatch[fmt](dataset, path)
