"""Search and read published records from **Zenodo** (https://zenodo.org) — the CERN-operated open
repository and a flagship of FAIR data. The public REST API needs no key (an optional ``ZENODO_TOKEN``
just raises the rate limit). ``search`` queries ``/api/records``; ``record_source`` exposes one record's
files (each a keyless download URL) as a :class:`FileListSource` for the normal scan/catalog pipeline.

A record's files are arbitrary (often ``.zip`` archives) — PsiDataViz parses what it recognizes and the
diagnostics surface the rest, which is the honest FAIR contract: *find & access everything, visualize
what's interoperable.*
"""

from __future__ import annotations

import os
import re

import httpx

from .base import DataSource, FileRef
from .repository import FileListSource, RepoRecord, RepoSearchResult, Repository

API = "https://zenodo.org/api"
_TAG_RE = re.compile(r"<[^>]+>")


class ZenodoError(RuntimeError):
    """Raised when a Zenodo API call fails."""


def _strip_html(text: str | None, limit: int = 280) -> str | None:
    if not text:
        return None
    clean = _TAG_RE.sub(" ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:limit] + ("…" if len(clean) > limit else "")


class ZenodoRepository(Repository):
    scheme = "zenodo"
    name = "Zenodo"

    def __init__(self, *, token: str | None = None, client: httpx.Client | None = None,
                 timeout: float = 30.0):
        self.token = token or os.environ.get("ZENODO_TOKEN")
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True,
                                              headers={"User-Agent": "psidata"})
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _get(self, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        if self.token:
            params["access_token"] = self.token
        try:
            resp = self._client.get(API + path, params=params, headers={"Accept": "application/json"})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise ZenodoError(f"Zenodo API request failed ({path}): {exc}") from exc

    def search(self, query: str, *, page: int = 1, per_page: int = 20) -> RepoSearchResult:
        data = self._get("/records", {"q": query, "page": page, "size": per_page, "sort": "bestmatch"})
        hits = data.get("hits", {})
        total = hits.get("total", 0)
        if isinstance(total, dict):  # newer Elasticsearch shape: {"value": N, "relation": "eq"}
            total = total.get("value", 0)
        records = [self._record(h) for h in hits.get("hits", [])]
        return RepoSearchResult(records=records, total=int(total), page=page, per_page=per_page)

    def record_source(self, record_id: str) -> DataSource:
        data = self._get(f"/records/{record_id}")
        meta = data.get("metadata", {})
        files = [
            FileRef(path=f["key"], size=f.get("size"), download_url=(f.get("links") or {}).get("self"))
            for f in data.get("files", [])
            if (f.get("links") or {}).get("self")
        ]
        label = f"zenodo:{record_id} — {(meta.get('title') or '')[:50]}".rstrip(" —")
        return FileListSource(label, files)  # own client; Zenodo file downloads are keyless

    def _record(self, hit: dict) -> RepoRecord:
        meta = hit.get("metadata", {})
        links = hit.get("links", {}) or {}
        return RepoRecord(
            id=str(hit.get("id")),
            title=meta.get("title", "") or "(untitled)",
            authors=[c.get("name", "") for c in meta.get("creators", [])],
            doi=hit.get("doi") or meta.get("doi"),
            published=meta.get("publication_date"),
            description=_strip_html(meta.get("description")),
            url=links.get("self_html") or hit.get("doi_url"),
            n_files=len(hit.get("files", [])),
            keywords=meta.get("keywords", []) or [],
            resource_type=(meta.get("resource_type") or {}).get("type"),
        )
