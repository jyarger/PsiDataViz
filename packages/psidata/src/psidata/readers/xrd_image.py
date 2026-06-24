"""Reader for **2D X-ray detector images** (area-detector frames): ESRF ``.edf`` and NeXus/HDF5 ``.h5``.

These are large 2D intensity arrays (SAXS / WAXS / GIWAXS frames), not 1D patterns, so they come back
as a :class:`~psidata.model.Image2D` (rendered as a heatmap) rather than a 1D ``Signal``.

* ``.edf`` — ESRF Data Format: an ASCII ``{ … }`` header (``Dim_1``/``Dim_2``/``DataType``/``ByteOrder``)
  followed by the raw binary array. Parsed with no extra dependency.
* ``.h5`` / ``.hdf5`` — read via ``h5py`` (the ``[convert]`` extra); the largest 2D dataset is used.

``.tif``/``.mccd``/``.img`` detector formats need an imaging library and are not handled yet.
"""

from __future__ import annotations

import io
import re

import numpy as np

from ..model import Axis, Dataset, Image2D, Metadata, SourceInfo
from ..registry import register_reader
from .base import BaseReader, Candidate

# ESRF EDF DataType -> numpy type code
_EDF_DTYPES = {
    "UnsignedByte": "u1", "SignedByte": "i1",
    "UnsignedShort": "u2", "SignedShort": "i2",
    "UnsignedInteger": "u4", "SignedInteger": "i4",
    "UnsignedLong": "u4", "SignedLong": "i4",
    "Unsigned64": "u8", "Signed64": "i8",
    "FloatValue": "f4", "Float": "f4", "DoubleValue": "f8", "Double": "f8",
}


@register_reader
class XRDImageReader(BaseReader):
    technique = "XRD"
    name = "xrd_image"
    version = "0.1.0"
    extensions = (".edf", ".h5", ".hdf5")

    def sniff(self, candidate: Candidate) -> float:
        if candidate.ext not in self.extensions:
            return 0.0
        magic = (candidate.content or b"")[:8]
        if candidate.ext == ".edf":
            return 0.9 if magic.lstrip()[:1] == b"{" else 0.0
        return 0.85 if magic[:4] == b"\x89HDF" else 0.0  # .h5 / .hdf5

    def read(self, candidate: Candidate) -> Dataset:
        if candidate.content is None:
            raise ValueError(f"{candidate.filename}: detector images need raw bytes")
        data, meta = (_read_edf(candidate.content) if candidate.ext == ".edf"
                      else _read_h5(candidate.content))
        meta.setdefault("sample_name", candidate.stem)
        image = Image2D(
            name="detector image",
            data=data,
            x=Axis(label="x", unit="px", quantity="detector_x"),
            y=Axis(label="y", unit="px", quantity="detector_y"),
            z=Axis(label="Intensity", unit="counts", quantity="intensity"),
        )
        return Dataset(
            technique=self.technique,
            source=SourceInfo(uri=candidate.uri, filename=candidate.filename,
                              reader=self.name, reader_version=self.version),
            metadata=Metadata(**meta),
            images=[image],
        )


def _read_edf(content: bytes) -> tuple[np.ndarray, dict]:
    end = content.index(b"}")
    kv = {k.strip(): v.strip()
          for k, v in re.findall(r"(\w+)\s*=\s*([^;]*);", content[:end].decode("latin1"))}
    dim1, dim2 = int(kv["Dim_1"]), int(kv["Dim_2"])
    dt = np.dtype(("<" if "low" in kv.get("ByteOrder", "LowByteFirst").lower() else ">")
                  + _EDF_DTYPES.get(kv.get("DataType", "FloatValue"), "f4"))
    nbytes = dim1 * dim2 * dt.itemsize
    data = np.frombuffer(content[-nbytes:], dtype=dt).reshape(dim2, dim1).astype(np.float32)
    meta = {}
    if kv.get("BIO_SAMPLE_NAME") and kv["BIO_SAMPLE_NAME"] not in ("", "NoName"):
        meta["sample_name"] = kv["BIO_SAMPLE_NAME"]
    return data, meta


def _read_h5(content: bytes) -> tuple[np.ndarray, dict]:
    try:
        import h5py
    except ImportError as exc:
        raise ImportError("reading .h5 detector images needs h5py: "
                          "pip install 'psidata[convert]'") from exc
    try:
        import hdf5plugin  # noqa: F401  registers blosc/lz4/bitshuffle/... compression filters
    except ImportError:
        pass  # only needed for plugin-compressed datasets
    f = h5py.File(io.BytesIO(content), "r")
    best = None
    for obj in _datasets(f):
        if obj.ndim == 2 and obj.size > 1 and (best is None or obj.size > best.size):
            best = obj
    if best is None:
        raise ValueError("no 2D image dataset found in HDF5 file")
    try:
        data = np.asarray(best[()], dtype=np.float32)
    except OSError as exc:
        raise ValueError("HDF5 dataset uses a compression filter that isn't available; "
                         "install 'hdf5plugin' (in the [convert] extra)") from exc
    return data, _h5_meta(f)


def _datasets(group):
    import h5py
    out = []
    group.visititems(lambda _n, o: out.append(o) if isinstance(o, h5py.Dataset) else None)
    return out


def _h5_meta(f) -> dict:
    def text(path: str) -> str | None:
        try:
            v = f[path][()]
        except (KeyError, OSError):
            return None
        if hasattr(v, "__len__") and not isinstance(v, (bytes, str)):
            v = v[0] if len(v) else b""
        if isinstance(v, bytes):
            v = v.decode("latin1", "replace")
        s = str(v).strip()
        return s if s and s.lower() not in ("nan", "none", "null", "0.0") else None

    meta = {}
    sample = text("entry/Metadata/Sample_Description") or text("entry/sample/name")
    if sample:
        meta["sample_name"] = sample
    instrument = text("entry/instrument/name")
    if instrument:
        meta["instrument"] = instrument
    return meta
