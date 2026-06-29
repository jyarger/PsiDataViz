from __future__ import annotations

import httpx
import respx

from psidata.sources import make_source
from psidata.sources.zenodo import ZenodoRepository, _strip_html

_SEARCH = {
    "hits": {
        "total": 1234,
        "hits": [
            {
                "id": 42,
                "doi": "10.5281/zenodo.42",
                "links": {"self_html": "https://zenodo.org/records/42"},
                "files": [{"key": "spectra.csv"}, {"key": "data.zip"}],
                "metadata": {
                    "title": "Raman spectra of olivine",
                    "creators": [{"name": "Doe, Jane"}, {"name": "Roe, Sam"}],
                    "publication_date": "2025-03-01",
                    "description": "<p>A <b>nice</b> dataset.</p>",
                    "resource_type": {"type": "dataset"},
                    "keywords": ["raman", "olivine"],
                },
            }
        ],
    }
}

_RECORD = {
    "metadata": {"title": "Raman spectra of olivine"},
    "files": [
        {"key": "spectra.csv", "size": 2048, "links": {"self": "https://zenodo.org/api/records/42/files/spectra.csv"}},
        {"key": "data.zip", "size": 9000, "links": {"self": "https://zenodo.org/api/records/42/files/data.zip"}},
        {"key": "no-link.bin"},  # files without a download link are skipped
    ],
}


def test_strip_html():
    assert _strip_html("<p>hi <b>there</b></p>") == "hi there"
    assert _strip_html(None) is None


@respx.mock
def test_zenodo_search_returns_records():
    respx.get("https://zenodo.org/api/records").mock(return_value=httpx.Response(200, json=_SEARCH))
    res = ZenodoRepository().search("raman", per_page=5)
    assert res.total == 1234 and len(res.records) == 1
    r = res.records[0]
    assert r.id == "42" and r.title == "Raman spectra of olivine"
    assert r.authors == ["Doe, Jane", "Roe, Sam"] and r.n_files == 2
    assert r.doi == "10.5281/zenodo.42" and r.resource_type == "dataset"
    assert r.description == "A nice dataset."  # html stripped


@respx.mock
def test_zenodo_record_source_lists_files_via_make_source():
    respx.get("https://zenodo.org/api/records/42").mock(return_value=httpx.Response(200, json=_RECORD))
    src = make_source("zenodo:42")  # routed through the repository factory
    files = src.list_files()
    assert [f.path for f in files] == ["spectra.csv", "data.zip"]  # the link-less file is dropped
    assert files[0].download_url == "https://zenodo.org/api/records/42/files/spectra.csv"
    assert files[0].size == 2048
