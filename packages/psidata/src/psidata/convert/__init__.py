"""Convert a parsed :class:`~psidata.Dataset` to standard scientific formats.

* **HDF5** and **Zarr** — array containers (one group per signal, x/y datasets + axis/metadata attrs).
  Need the optional ``[convert]`` extra (``pip install 'psidata[convert]'``).
* **CSDM** (``.csdf``) — the Core Scientific Dataset Model. Written directly as its lightweight JSON
  form, so it needs no extra dependency. Signals sharing the x-grid become dependent variables.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..model import Dataset

__all__ = ["convert", "to_csdm", "to_hdf5", "to_zarr"]


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


def convert(dataset: Dataset, path: str | Path, fmt: str | None = None) -> str:
    """Dispatch by ``fmt`` (or the path suffix): ``hdf5``/``h5`` · ``zarr`` · ``csdf``/``csdm``."""
    fmt = (fmt or Path(str(path)).suffix.lstrip(".")).lower()
    if fmt in ("h5", "hdf5"):
        return to_hdf5(dataset, path)
    if fmt == "zarr":
        return to_zarr(dataset, path)
    if fmt in ("csdf", "csdm"):
        return to_csdm(dataset, path)
    raise ValueError(f"unknown convert format {fmt!r} (use hdf5, zarr, or csdf)")
