"""PsiData (Ψ Data) — a framework-agnostic library for ingesting, parsing, and converting
experimental & computational scientific data into one universal model.
"""

from __future__ import annotations

from . import readers as _readers  # noqa: F401  (import registers all built-in readers)
from .filename import ParsedName, parse_filename
from .model import Axis, Dataset, Metadata, Signal, SourceInfo
from .readers.base import BaseReader, Candidate
from .registry import (
    UnknownFormatError,
    detect,
    get_readers,
    read,
    register_reader,
    score_readers,
)

__version__ = "0.2.0"

__all__ = [
    "Axis",
    "BaseReader",
    "Candidate",
    "Dataset",
    "Metadata",
    "ParsedName",
    "Signal",
    "SourceInfo",
    "UnknownFormatError",
    "detect",
    "get_readers",
    "parse_filename",
    "read",
    "register_reader",
    "score_readers",
    "__version__",
]
