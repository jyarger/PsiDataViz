"""Data sources: where files come from. GitHub first; the interface is source-agnostic."""

from __future__ import annotations

from .base import DataSource, FileRef
from .catalog import Catalog, CatalogEntry, build_entry, scan
from .github import GitHubError, GitHubSource, RepoRef, parse_repo_url

__all__ = [
    "Catalog",
    "CatalogEntry",
    "DataSource",
    "FileRef",
    "GitHubError",
    "GitHubSource",
    "RepoRef",
    "build_entry",
    "parse_repo_url",
    "scan",
]
