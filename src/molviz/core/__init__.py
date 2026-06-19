"""MolViz core: the framework-agnostic ingestion library."""

from __future__ import annotations

# Importing the readers package registers all built-in readers via @register_reader.
from . import readers as _readers  # noqa: E402,F401
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
]
