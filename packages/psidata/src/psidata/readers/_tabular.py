"""Shared helper for headerless / lightly-headed numeric spectral tables (FTIR .dpt, Raman .csv).

Detects the delimiter, skips any non-numeric header/comment lines, and returns the numeric rows
as a DataFrame with positional column names ``col0, col1, ...``.
"""

from __future__ import annotations

import pandas as pd


def detect_delimiter(lines: list[str]) -> str | None:
    """Return ``"\\t"``, ``","``, or ``None`` (whitespace) based on the first data-bearing line."""
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if "\t" in s:
            return "\t"
        if "," in s:
            return ","
        return None  # whitespace-separated
    return None


def parse_numeric_table(text: str) -> pd.DataFrame:
    """Parse a numeric table, ignoring header/comment lines and ragged rows."""
    lines = text.splitlines()
    delimiter = detect_delimiter(lines)
    rows: list[list[float]] = []
    ncols: int | None = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        parts = s.split(delimiter) if delimiter else s.split()
        try:
            values = [float(p) for p in parts]
        except ValueError:
            continue  # header, comment, or non-numeric line
        if ncols is None:
            ncols = len(values)
        if len(values) == ncols and ncols >= 2:
            rows.append(values)
    if not rows or ncols is None:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=[f"col{i}" for i in range(ncols)])
