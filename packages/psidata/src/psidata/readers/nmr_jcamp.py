"""Reader for NMR spectra in JCAMP-DX format (``.jdx``, ``.dx``, and Agilent/Varian ``.txt``).

JCAMP-DX is a labeled-text standard: ``##LABEL= value`` header records (LDRs) followed by a data
section. Validated against real files in ``github.com/yargerlab/Data/NMR``:

* **Agilent/Varian** exports (the bulk of the repo) use ``##XYDATA= (XY..XY)`` — plain
  ``x, y`` pairs already in ppm.
* **Bruker/TopSpin** exports use ``##XYDATA= (X++(Y..Y))`` — ASDF-compressed (SQZ/DIF/DUP); decoded
  by :mod:`psidata.readers._asdf` and emitted only after validating against the header (NPOINTS,
  FIRSTY), so a mis-decode never produces a silently-wrong spectrum.

Abscissa is reported in the file's ``XUNITS`` (Hz for many Bruker exports, ppm for others);
absolute Hz→ppm referencing is a future refinement.
"""

from __future__ import annotations

import re

import pandas as pd

from ..model import Axis, Dataset, Metadata, Signal, SourceInfo
from ..registry import register_reader
from .base import BaseReader, Candidate

_LDR_RE = re.compile(r"^##\$?([^=]+)=(.*)$")
_XY_FORM = "(XY..XY)"
_ASDF_FORM = "(X++(Y..Y))"


class NMRMetadata(Metadata):
    """NMR-specific metadata layered on the common fields."""

    nucleus: str | None = None
    frequency_mhz: float | None = None
    solvent: str | None = None
    pulse_sequence: str | None = None
    temperature_k: float | None = None
    data_type: str | None = None
    npoints: int | None = None


@register_reader
class JcampNmrReader(BaseReader):
    technique = "NMR"
    name = "nmr_jcamp"
    version = "0.1.0"
    extensions = (".jdx", ".dx", ".txt")

    def sniff(self, candidate: Candidate) -> float:
        head = candidate.head(4096)
        if "##JCAMP-DX" not in head.upper():
            return 0.0
        score = 0.1 if candidate.ext in self.extensions else 0.0
        score += 0.5  # it's JCAMP-DX
        upper = head.upper()
        if "NMR SPECTRUM" in upper or "OBSERVE NUCLEUS" in upper or "OBSERVE FREQUENCY" in upper:
            score += 0.35
        return min(score, 1.0)

    def read(self, candidate: Candidate) -> Dataset:
        lines = candidate.as_text().splitlines()
        ldrs, data_marker, data_lines = _split_ldrs_and_data(lines)

        form = _data_form(ldrs.get("XYDATA") or ldrs.get("XYPOINTS") or data_marker or "")
        xfactor = _as_float(ldrs.get("XFACTOR"), 1.0)
        yfactor = _as_float(ldrs.get("YFACTOR"), 1.0)
        if form == _ASDF_FORM:
            x, y = _read_asdf(ldrs, data_lines, xfactor, yfactor)
        else:
            x, y = _parse_xy_pairs(data_lines, xfactor, yfactor)

        x_unit = (ldrs.get("XUNITS") or "ppm").strip().lower()
        x_label, x_unit_disp = ("Frequency", "Hz") if x_unit in ("hz", "hertz") \
            else ("Chemical shift", "ppm")
        frame = pd.DataFrame({x_label: x, "Intensity": y})

        signal = Signal(
            name="spectrum",
            x=Axis(label=x_label, unit=x_unit_disp, quantity="chemical_shift"),
            y=Axis(label="Intensity", unit="a.u.", quantity="intensity"),
            frame=frame,
        )
        return Dataset(
            technique=self.technique,
            source=SourceInfo(uri=candidate.uri, filename=candidate.filename,
                              reader=self.name, reader_version=self.version,
                              raw_header="\n".join(lines[: data_marker_index(lines)])),
            metadata=_build_metadata(ldrs, candidate, npoints=len(frame)),
            signals=[signal],
        )


def _read_asdf(ldrs: dict[str, str], data_lines: list[str], xfactor: float, yfactor: float
               ) -> tuple[list[float], list[float]]:
    """Decode compressed ``(X++(Y..Y))`` ordinates into (x, y).

    Emits data only if it validates against the header (NPOINTS, FIRSTY); otherwise raises, so a
    mis-decode can never silently produce a wrong spectrum.
    """
    from ._asdf import decode_xpp_yy

    x0, direction, ordinates = decode_xpp_yy(data_lines)
    if x0 is None or not ordinates:
        raise ValueError("ASDF block contained no decodable ordinates")
    npoints = ldrs.get("NPOINTS")
    if npoints and len(ordinates) != int(float(npoints)):
        raise ValueError(f"ASDF decoded {len(ordinates)} points but NPOINTS={npoints}")
    firsty = ldrs.get("FIRSTY")
    if firsty not in (None, "") and abs(ordinates[0] - float(firsty)) > 0.5:
        raise ValueError(f"ASDF FIRSTY mismatch: decoded {ordinates[0]} != {firsty}")

    x = [(x0 + direction * j) * xfactor for j in range(len(ordinates))]
    y = [v * yfactor for v in ordinates]
    return x, y


def _split_ldrs_and_data(lines: list[str]) -> tuple[dict[str, str], str | None, list[str]]:
    """Parse ``##LABEL= value`` records; return the LDR dict, the data-marker value, data lines."""
    ldrs: dict[str, str] = {}
    data_marker: str | None = None
    data_lines: list[str] = []
    in_data = False
    for line in lines:
        if in_data:
            if line.startswith("##END"):
                break
            data_lines.append(line)
            continue
        m = _LDR_RE.match(line)
        if not m:
            continue
        label = m.group(1).strip().upper().replace(" ", "")
        value = m.group(2).split("$$")[0].strip()
        if label in ("XYDATA", "XYPOINTS", "PEAKTABLE"):
            data_marker = value
            in_data = True
            continue
        ldrs[label] = value
    return ldrs, data_marker, data_lines


def _data_form(marker: str) -> str:
    compact = marker.replace(" ", "")
    if "X++(Y..Y)" in compact:
        return _ASDF_FORM
    return _XY_FORM


def _parse_xy_pairs(data_lines: list[str], xfactor: float, yfactor: float
                    ) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for line in data_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(("##", "$$")):
            continue
        nums = []
        for token in stripped.replace(",", " ").replace(";", " ").split():
            try:
                nums.append(float(token))
            except ValueError:
                continue
        for i in range(0, len(nums) - 1, 2):
            xs.append(nums[i] * xfactor)
            ys.append(nums[i + 1] * yfactor)
    return xs, ys


def _build_metadata(ldrs: dict[str, str], candidate: Candidate, npoints: int) -> NMRMetadata:
    return NMRMetadata(
        sample_name=ldrs.get("TITLE") or candidate.stem,
        instrument=ldrs.get("SPECTROMETER/DATASYSTEM") or ldrs.get("ORIGIN"),
        nucleus=_clean_nucleus(ldrs.get(".OBSERVENUCLEUS")),
        frequency_mhz=_as_float(ldrs.get(".OBSERVEFREQUENCY")),
        solvent=ldrs.get(".SOLVENT") or ldrs.get("SOLVENT"),
        pulse_sequence=ldrs.get("PULSESEQUENCE"),
        temperature_k=_as_float(ldrs.get("TEMPERATURE")),
        data_type=ldrs.get("DATATYPE"),
        npoints=npoints,
    )


def _clean_nucleus(value: str | None) -> str | None:
    return value.replace("^", "").strip() if value else None


def _as_float(value: str | None, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value.split("$$")[0].split()[0])
    except (ValueError, IndexError):
        return default


def data_marker_index(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        upper = line.upper()
        if upper.startswith(("##XYDATA", "##XYPOINTS", "##PEAKTABLE")):
            return i
    return len(lines)
