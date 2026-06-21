"""Compare the same measurement parsed from different file formats.

When a dataset is saved in several formats (e.g. a DSC run as ``.csv`` *and* ``.txt``), this tells
you whether they hold identical data and, if not, summarizes exactly what differs — signal counts,
point counts, numeric values (within tolerance), and metadata fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .model import Dataset

_SKIP_META = {"extra"}


@dataclass
class Comparison:
    identical: bool
    differences: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return "identical data" if self.identical else f"{len(self.differences)} difference(s)"

    def as_dict(self) -> dict:
        return {"identical": self.identical, "summary": self.summary,
                "differences": self.differences}


def compare_datasets(a: Dataset, b: Dataset, *, rtol: float = 1e-5, atol: float = 1e-8,
                     a_label: str = "A", b_label: str = "B") -> Comparison:
    """Compare two parsed datasets; return an itemized list of any differences."""
    diffs: list[str] = []

    if a.technique != b.technique:
        diffs.append(f"technique: {a.technique} vs {b.technique}")
    if len(a.signals) != len(b.signals):
        diffs.append(f"signal count: {len(a.signals)} ({a_label}) vs {len(b.signals)} ({b_label})")

    for i, (sa, sb) in enumerate(zip(a.signals, b.signals, strict=False)):
        if sa.npoints != sb.npoints:
            diffs.append(f"signal {i} '{sa.name}': {sa.npoints} vs {sb.npoints} points")
            continue
        for col in [c for c in sa.frame.columns if c in sb.frame.columns]:
            ca, cb = sa.frame[col], sb.frame[col]
            if pd.api.types.is_numeric_dtype(ca) and pd.api.types.is_numeric_dtype(cb):
                va, vb = ca.to_numpy(), cb.to_numpy()
                if not np.allclose(va, vb, rtol=rtol, atol=atol, equal_nan=True):
                    diffs.append(f"signal {i} column '{col}': max abs diff "
                                 f"{float(np.nanmax(np.abs(va - vb))):.3g}")
            elif not ca.equals(cb):
                diffs.append(f"signal {i} column '{col}': non-numeric values differ")

    ma, mb = a.metadata.model_dump(), b.metadata.model_dump()
    for key in sorted((set(ma) & set(mb)) - _SKIP_META):
        if ma[key] != mb[key]:
            diffs.append(f"metadata '{key}': {ma[key]!r} vs {mb[key]!r}")

    return Comparison(identical=not diffs, differences=diffs)
