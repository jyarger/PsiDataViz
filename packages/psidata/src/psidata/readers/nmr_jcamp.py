"""Reader for **NMR** spectra in JCAMP-DX (``.jdx``, ``.dx``, and Agilent/Varian ``.txt``).

Shared JCAMP parsing lives in :mod:`._jcamp`; this reader adds NMR-specific detection (it declines
INFRARED/RAMAN/UV JCAMP, which the FTIR reader handles), axes, and metadata. Both plain ``(XY..XY)``
and ASDF-compressed ``(X++(Y..Y))`` data are supported. Abscissa is reported in the file's
``XUNITS`` (Hz for many Bruker exports, ppm for others); absolute Hz→ppm referencing is future work.
"""

from __future__ import annotations

import pandas as pd

from ..model import Axis, Dataset, Metadata, Signal, SourceInfo
from ..registry import register_reader
from ._jcamp import decode_data, header_index, ldr_float, parse_ldrs_and_data
from .base import BaseReader, Candidate

_NON_NMR = ("INFRARED", "RAMAN", "UV/VIS", "UV-VIS", "UVVIS", "MASS SPECTRUM")


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
    version = "0.2.0"
    extensions = (".jdx", ".dx", ".txt")

    def sniff(self, candidate: Candidate) -> float:
        head = candidate.head(4096).upper()
        if "##JCAMP-DX" not in head:
            return 0.0
        if any(marker in head for marker in _NON_NMR):
            return 0.0  # belongs to FTIR / another technique's JCAMP reader
        score = 0.1 if candidate.ext in self.extensions else 0.0
        score += 0.5
        if "NMR SPECTRUM" in head or "OBSERVE NUCLEUS" in head or "OBSERVE FREQUENCY" in head:
            score += 0.35
        elif (candidate.technique_hint or "").upper() == "NMR":
            score += 0.2
        return min(score, 1.0)

    def read(self, candidate: Candidate) -> Dataset:
        lines = candidate.as_text().splitlines()
        ldrs, marker, data_lines = parse_ldrs_and_data(lines)
        x, y = decode_data(ldrs, marker, data_lines)

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
                              raw_header="\n".join(lines[: header_index(lines)])),
            metadata=_build_metadata(ldrs, candidate, npoints=len(frame)),
            signals=[signal],
        )


def _build_metadata(ldrs: dict[str, str], candidate: Candidate, npoints: int) -> NMRMetadata:
    return NMRMetadata(
        sample_name=ldrs.get("TITLE") or candidate.stem,
        instrument=ldrs.get("SPECTROMETER/DATASYSTEM") or ldrs.get("ORIGIN"),
        nucleus=_clean_nucleus(ldrs.get(".OBSERVENUCLEUS")),
        frequency_mhz=ldr_float(ldrs, ".OBSERVEFREQUENCY"),
        solvent=ldrs.get(".SOLVENT") or ldrs.get("SOLVENT"),
        pulse_sequence=ldrs.get("PULSESEQUENCE"),
        temperature_k=ldr_float(ldrs, "TEMPERATURE"),
        data_type=ldrs.get("DATATYPE"),
        npoints=npoints,
    )


def _clean_nucleus(value: str | None) -> str | None:
    return value.replace("^", "").strip() if value else None
