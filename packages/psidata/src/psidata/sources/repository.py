"""Open **data repositories** — searchable catalogs of *published* records (Zenodo, nmrXiv, …).

A repository is different from a :class:`~psidata.sources.base.DataSource`: you don't scan a whole file
tree, you **search** for records (each a published deposit with a DOI + files) and then **fetch** a
chosen record's files. So the contract is two methods — :meth:`Repository.search` returns lightweight
record summaries *without downloading anything*, and :meth:`Repository.record_source` hands back a normal
``DataSource`` for one record so the existing scan → catalog → dataset pipeline takes over unchanged.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from .base import DataSource, FileRef


@dataclass
class RepoRecord:
    """A search hit: one published record/deposit, described without downloading its files."""

    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    doi: str | None = None
    published: str | None = None  # ISO date
    description: str | None = None
    url: str | None = None  # landing page
    n_files: int = 0
    keywords: list[str] = field(default_factory=list)
    resource_type: str | None = None

    def summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "doi": self.doi,
            "published": self.published,
            "description": self.description,
            "url": self.url,
            "n_files": self.n_files,
            "keywords": self.keywords,
            "resource_type": self.resource_type,
        }


@dataclass
class RepoSearchResult:
    records: list[RepoRecord]
    total: int
    page: int
    per_page: int

    def summary(self) -> dict:
        return {
            "total": self.total,
            "page": self.page,
            "per_page": self.per_page,
            "records": [r.summary() for r in self.records],
        }


class Repository(ABC):
    """A searchable open data repository."""

    #: short id used to route ``<scheme>:<record-id>`` URLs and pick the repository in the UI
    scheme: str = "repo"
    #: human-readable name
    name: str = "repository"

    @abstractmethod
    def search(self, query: str, *, page: int = 1, per_page: int = 20) -> RepoSearchResult:
        """Search the repository and return lightweight record summaries (no file downloads)."""

    @abstractmethod
    def record_source(self, record_id: str) -> DataSource:
        """A :class:`DataSource` exposing one record's files, for the normal scan/catalog pipeline."""


class FileListSource(DataSource):
    """A :class:`DataSource` over an explicit list of files (no tree to walk) — the natural shape of a
    repository record, whose files are a flat set of download URLs. Reused by every repository."""

    def __init__(self, label: str, files: list[FileRef], *, client: httpx.Client | None = None,
                 timeout: float = 180.0, headers: dict | None = None):
        self.label = label
        self._files = files
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True,
                                              headers=headers or {"User-Agent": "psidata"})
        self._owns_client = client is None

    def __enter__(self) -> FileListSource:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def list_files(self) -> list[FileRef]:
        return self._files

    def open_bytes(self, ref: FileRef) -> bytes:
        resp = self._client.get(ref.download_url)
        resp.raise_for_status()
        return resp.content

    def open_text(self, ref: FileRef) -> str:
        resp = self._client.get(ref.download_url)
        resp.encoding = resp.encoding or "utf-8"
        return resp.text
