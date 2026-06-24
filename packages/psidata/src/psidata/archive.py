"""Read datasets packaged inside a ``.zip`` archive.

Cases handled (no ``nmrglue`` dependency):

* **Magritek SpinSolve** export — contains ``spectrum_processed.csv`` (``Frequency(ppm),Intensity``),
  a ready processed spectrum.
* **Bruker TopSpin** dataset — ``…/pdata/N/1r`` (int32 processed real spectrum) + ``procs``; the ppm
  axis is rebuilt from ``SI`` / ``SW_p`` / ``SF`` / ``OFFSET`` and intensities scaled by ``2**NC_proc``.
* **Zipped single data file** (e.g. ``…CPMG.txt.zip``) — extract the data member and route it to the
  normal reader registry.

macOS ``__MACOSX`` resource-fork entries are ignored.
"""

from __future__ import annotations

import io
import os
import re
import zipfile

import numpy as np
import pandas as pd

from .model import Axis, Dataset, Signal, SourceInfo
from .readers._tabular import parse_numeric_table
from .readers.base import Candidate
from .readers.nmr_jcamp import NMRMetadata
from .registry import read

_TEXT_DATA_EXTS = {".txt", ".csv", ".dx", ".jdx", ".dpt", ".asc", ".dat", ".tsv"}
_BRUKER_MARKERS = {"acqus", "acqu", "fid", "ser", "pulseprogram", "procs"}


class ArchiveError(Exception):
    """Raised when an archive can't be turned into a dataset (empty, unknown, or unreadable)."""


def _members(zf: zipfile.ZipFile) -> list[str]:
    return [m for m in zf.namelist() if not m.endswith("/") and "__MACOSX" not in m]


def looks_like_bruker(members: list[str]) -> bool:
    return bool({os.path.basename(m) for m in members} & _BRUKER_MARKERS)


def _find(members: list[str], suffix: str) -> str | None:
    return next((m for m in members if m.endswith(suffix)), None)


def read_zip(filename: str, content: bytes, *, technique_hint: str | None = None) -> Dataset:
    """Parse the dataset contained in a zip archive's bytes into the universal model."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ArchiveError(f"{filename}: not a valid zip archive ({exc})") from exc

    members = _members(zf)
    if not members:
        raise ArchiveError(f"{filename}: archive is empty")

    spinsolve = _find(members, "spectrum_processed.csv") or _find(members, "spectrum.csv")
    if spinsolve:
        return _read_spinsolve(zf, spinsolve, filename, technique_hint)

    if looks_like_bruker(members):
        oner = _find(members, "pdata/1/1r") or _find(members, "/1r")
        if oner and _sibling(oner, "procs") in members:
            return _read_bruker(zf, oner, filename, technique_hint)
        raise ArchiveError(
            f"{filename}: Bruker archive without processed data (expected pdata/1/1r + procs)."
        )

    data_members = [m for m in members if os.path.splitext(m)[1].lower() in _TEXT_DATA_EXTS]
    if not data_members:
        raise ArchiveError(f"{filename}: no recognized data file inside (members: {members[:5]})")
    member = max(data_members, key=lambda m: zf.getinfo(m).file_size)
    return read(Candidate(filename=os.path.basename(member), content=zf.read(member),
                          uri=filename, technique_hint=technique_hint))


# --- SpinSolve ---------------------------------------------------------------------------------
def _read_spinsolve(zf: zipfile.ZipFile, member: str, filename: str,
                    technique_hint: str | None) -> Dataset:
    table = parse_numeric_table(zf.read(member).decode("utf-8", "replace"))
    if table.empty or table.shape[1] < 2:
        raise ArchiveError(f"{filename}: SpinSolve spectrum CSV had no (ppm, intensity) data")
    par = _member_text(zf, "acqu.par")
    kv = dict(re.findall(r'(\w+)\s*=\s*"?([^"\n]+?)"?\s*$', par, re.M)) if par else {}
    meta = NMRMetadata(sample_name=kv.get("Sample") or _stem(filename), solvent=kv.get("Solvent"),
                       frequency_mhz=_float(kv.get("b1Freq")),
                       data_type="NMR processed spectrum (SpinSolve)", npoints=len(table))
    return _nmr_dataset(filename, technique_hint, "nmr_spinsolve_zip",
                        _nmr_signal(table["col0"], table["col1"]), meta)


# --- Bruker ------------------------------------------------------------------------------------
def _read_bruker(zf: zipfile.ZipFile, oner: str, filename: str,
                 technique_hint: str | None) -> Dataset:
    procs = zf.read(_sibling(oner, "procs")).decode("latin1")
    si = int(float(_par(procs, "SI") or 0))
    raw = zf.read(oner)
    if not si:
        si = len(raw) // 4
    bytord = int(float(_par(procs, "BYTORDP") or 0))
    nc = int(float(_par(procs, "NC_proc") or 0))
    y = np.frombuffer(raw[: si * 4], dtype=(">" if bytord else "<") + "i4").astype(float) * 2.0**nc

    sw_p, sf, offset = _float(_par(procs, "SW_p")), _float(_par(procs, "SF")), _float(_par(procs, "OFFSET"))
    if sw_p and sf and offset is not None and si:
        ppm = offset - np.arange(si) * (sw_p / sf) / si  # point 0 = left edge (OFFSET), decreasing
    else:
        ppm = np.arange(si)[::-1].astype(float)

    title = _member_text_exact(zf, _sibling(oner, "title"))
    sample = (title.strip().splitlines()[0].strip() if title and title.strip() else "") or _stem(filename)
    meta = NMRMetadata(sample_name=sample, frequency_mhz=sf,
                       data_type="NMR processed spectrum (Bruker)", npoints=len(y))
    return _nmr_dataset(filename, technique_hint, "nmr_bruker_zip", _nmr_signal(ppm, y), meta)


# --- shared helpers ----------------------------------------------------------------------------
def _nmr_signal(ppm, intensity) -> Signal:
    frame = pd.DataFrame({"Chemical shift": np.asarray(ppm, float),
                          "Intensity": np.asarray(intensity, float)})
    return Signal(name="spectrum",
                  x=Axis(label="Chemical shift", unit="ppm", quantity="chemical_shift"),
                  y=Axis(label="Intensity", unit="a.u.", quantity="intensity"),
                  frame=frame)


def _nmr_dataset(filename: str, technique_hint: str | None, reader: str, signal: Signal,
                 meta: NMRMetadata) -> Dataset:
    return Dataset(
        technique=technique_hint or "NMR",
        source=SourceInfo(uri=filename, filename=os.path.basename(filename),
                          reader=reader, reader_version="0.1.0"),
        metadata=meta, signals=[signal],
    )


def _sibling(member: str, name: str) -> str:
    return member.rsplit("/", 1)[0] + "/" + name if "/" in member else name


def _member_text(zf: zipfile.ZipFile, basename: str) -> str | None:
    m = _find(_members(zf), basename)
    return zf.read(m).decode("latin1") if m else None


def _member_text_exact(zf: zipfile.ZipFile, path: str) -> str | None:
    try:
        return zf.read(path).decode("latin1")
    except KeyError:
        return None


def _par(text: str, key: str) -> str | None:
    m = re.search(rf"##\$\s*{key}=\s*(.*)", text)
    return m.group(1).strip() if m else None


def _float(s: str | None) -> float | None:
    try:
        return float(s) if s not in (None, "") else None
    except (ValueError, TypeError):
        return None


def _stem(filename: str) -> str:
    return os.path.splitext(os.path.basename(filename))[0]
