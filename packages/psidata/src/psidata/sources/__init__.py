"""Data sources: where files come from. GitHub first; the interface is source-agnostic."""

from __future__ import annotations

from .base import DataSource, FileRef
from .catalog import Catalog, CatalogEntry, build_entry, scan
from .github import GitHubError, GitHubSource, RepoRef, parse_repo_url
from .records import (
    DataRecord,
    FormatInfo,
    FormatVariant,
    build_records,
    classify_format,
    record_key,
)

__all__ = [
    "Catalog",
    "CatalogEntry",
    "DataRecord",
    "DataSource",
    "FileRef",
    "FormatInfo",
    "FormatVariant",
    "GitHubError",
    "GitHubSource",
    "RepoRef",
    "build_entry",
    "build_records",
    "classify_format",
    "parse_repo_url",
    "record_key",
    "scan",
]
