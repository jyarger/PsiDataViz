"""Universal data model returned by every reader, for every technique.

The whole extensibility story rests on this: a DSC run, an FTIR spectrum, and an NMR spectrum
all come back as the same ``Dataset`` container, so the app and exporters never need to know
which technique produced the data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class Axis(BaseModel):
    """A self-describing plot axis: a human label, a unit, and a canonical quantity name."""

    label: str
    unit: str | None = None
    quantity: str | None = None  # canonical, e.g. "temperature", "heat_flow", "wavenumber"

    model_config = ConfigDict(frozen=True)

    @property
    def title(self) -> str:
        return f"{self.label} ({self.unit})" if self.unit else self.label


class SourceInfo(BaseModel):
    """Provenance for a parsed dataset — where it came from and what parsed it."""

    uri: str | None = None
    filename: str | None = None
    reader: str | None = None
    reader_version: str | None = None
    raw_header: str | None = None


class Metadata(BaseModel):
    """Common metadata shared across techniques. Technique-specific subclasses add fields."""

    model_config = ConfigDict(extra="allow")

    sample_name: str | None = None
    date: _date | None = None
    operator: str | None = None
    instrument: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


@dataclass
class Signal:
    """One curve/trace: an x axis, a y axis, and the underlying tabular data.

    ``frame`` may carry additional columns (e.g. Time) beyond x and y; ``x.label`` and ``y.label``
    name the columns to plot by default.
    """

    name: str
    x: Axis
    y: Axis
    frame: pd.DataFrame
    segment: str | None = None

    def __post_init__(self) -> None:
        for axis in (self.x, self.y):
            if axis.label not in self.frame.columns:
                raise ValueError(
                    f"axis column {axis.label!r} not found in frame columns {list(self.frame.columns)}"
                )

    @property
    def npoints(self) -> int:
        return len(self.frame)


@dataclass
class Dataset:
    """A fully parsed measurement: provenance + metadata + one or more signals."""

    technique: str
    source: SourceInfo
    metadata: Metadata
    signals: list[Signal] = field(default_factory=list)

    def to_tidy_df(self) -> pd.DataFrame:
        """Long-form concatenation of every signal, tagged with signal/segment columns."""
        frames = []
        for sig in self.signals:
            f = sig.frame.copy()
            f.insert(0, "signal", sig.name)
            f.insert(1, "segment", sig.segment)
            frames.append(f)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def summary(self) -> dict[str, Any]:
        """A cheap, JSON-friendly overview for catalog listings and UI panels."""
        return {
            "technique": self.technique,
            "sample_name": self.metadata.sample_name,
            "date": self.metadata.date.isoformat() if self.metadata.date else None,
            "instrument": self.metadata.instrument,
            "operator": self.metadata.operator,
            "filename": self.source.filename,
            "n_signals": len(self.signals),
            "signals": [
                {
                    "name": s.name,
                    "segment": s.segment,
                    "x": s.x.title,
                    "y": s.y.title,
                    "npoints": s.npoints,
                }
                for s in self.signals
            ],
        }
