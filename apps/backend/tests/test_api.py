from __future__ import annotations

import httpx
import respx
from fastapi.testclient import TestClient

from psidata_backend.main import app
from psidata_backend.services import _listing_cache

client = TestClient(app)


def test_health_lists_readers():
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    techniques = {r["technique"] for r in body["readers"]}
    assert {"DSC", "NMR", "FTIR", "Raman"} <= techniques


@respx.mock
def test_dataset_endpoint_serves_downsampled_points():
    raw = "https://raw.githubusercontent.com/o/r/main/Raman/2026_01_01_x.csv"
    respx.get(raw).mock(return_value=httpx.Response(200, text="10,100\n9,200\n8,150\n"))
    resp = client.get("/api/dataset", params={"url": raw, "name": "2026_01_01_x.csv",
                                              "technique": "Raman"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["technique"] == "Raman"
    assert data["signals"][0]["x"]["label"] == "Raman shift"
    assert data["signals"][0]["points"][0] == [10.0, 100.0]


@respx.mock
def test_scan_endpoint_summarizes_records():
    _listing_cache.clear()
    respx.get("https://api.github.com/repos/o/r").mock(
        return_value=httpx.Response(200, json={"default_branch": "main"}))
    tree = {"tree": [
        {"path": "DSC/2026_01_01_run.csv", "type": "blob", "size": 10},
        {"path": "DSC/2026_01_01_run.tri", "type": "blob", "size": 10},
    ]}
    respx.get("https://api.github.com/repos/o/r/git/trees/main").mock(
        return_value=httpx.Response(200, json=tree))
    body = client.get("/api/scan", params={"url": "o/r"}).json()
    assert body["n_records"] == 1                          # csv + tri -> one dataset
    assert any(t["technique"] == "DSC" for t in body["techniques"])


@respx.mock
def test_convert_endpoint_returns_csdm_download():
    raw = "https://raw.githubusercontent.com/o/r/main/Raman/2026_01_01_x.csv"
    respx.get(raw).mock(return_value=httpx.Response(200, text="10,100\n9,200\n8,150\n"))
    resp = client.get("/api/convert", params={"url": raw, "name": "2026_01_01_x.csv",
                                              "technique": "Raman", "fmt": "csdf"})
    assert resp.status_code == 200
    assert "attachment" in resp.headers.get("content-disposition", "")
    import json
    assert json.loads(resp.content)["csdm"]["version"] == "1.0"


@respx.mock
def test_convert_endpoint_csv_download():
    raw = "https://raw.githubusercontent.com/o/r/main/Raman/2026_01_01_x.csv"
    respx.get(raw).mock(return_value=httpx.Response(200, text="10,100\n9,200\n8,150\n"))
    resp = client.get("/api/convert", params={"url": raw, "name": "2026_01_01_x.csv",
                                              "technique": "Raman", "fmt": "csv"})
    assert resp.status_code == 200
    assert resp.headers["content-disposition"].endswith('.csv"')
    assert b"signal" in resp.content  # tidy CSV header


def test_convert_endpoint_rejects_unknown_format():
    assert client.get("/api/convert", params={"url": "x", "name": "y.csv", "fmt": "bogus"}
                      ).status_code == 400


def test_dataset_endpoint_reports_errors():
    # missing required params -> 422 from FastAPI
    assert client.get("/api/dataset").status_code == 422


@respx.mock
def test_catalog_endpoint_returns_summary_and_records():
    _listing_cache.clear()
    respx.get("https://api.github.com/repos/o/r").mock(
        return_value=httpx.Response(200, json={"default_branch": "main"}))
    tree = {"tree": [
        {"path": "Raman/2026_01_01_x.csv", "type": "blob", "size": 10},
        {"path": "DSC/2026_01_01_run.csv", "type": "blob", "size": 10},
    ]}
    respx.get("https://api.github.com/repos/o/r/git/trees/main").mock(
        return_value=httpx.Response(200, json=tree))
    body = client.get("/api/catalog", params={"url": "o/r"}).json()
    assert "records" in body and isinstance(body["records"], list)
    techniques = {r["technique"] for r in body["records"]}
    assert {"Raman", "DSC"} <= techniques
    assert all("url" in r and "name" in r for r in body["records"])
