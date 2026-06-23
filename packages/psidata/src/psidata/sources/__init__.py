"""Data sources: where files come from. GitHub first; the interface is source-agnostic."""

from __future__ import annotations

from .base import DataSource, FileRef
from .catalog import Catalog, CatalogEntry, build_entry, canonical_technique, scan
from .gdrive import GoogleDriveError, GoogleDriveSource, parse_drive_url
from .github import GitHubError, GitHubSource, RepoRef, parse_repo_url
from .records import (
    DataRecord,
    FormatInfo,
    FormatVariant,
    build_records,
    classify_format,
    record_key,
)


def make_source(url: str, **kwargs) -> DataSource:
    """Pick the right :class:`DataSource` for a URL — Google Drive folder vs. GitHub repo."""
    if "drive.google.com" in url:
        return GoogleDriveSource(url, **kwargs)
    return GitHubSource(url, **kwargs)


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
    "GoogleDriveError",
    "GoogleDriveSource",
    "RepoRef",
    "build_entry",
    "build_records",
    "canonical_technique",
    "classify_format",
    "make_source",
    "parse_drive_url",
    "parse_repo_url",
    "record_key",
    "scan",
]
