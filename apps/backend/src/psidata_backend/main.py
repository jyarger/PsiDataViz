"""PsiData API — async FastAPI backend that turns the psidata library into a JSON service.

Endpoints (all read-only):
  GET  /api/health
  GET  /api/scan?url=             -> repo summary (datasets-by-technique)
  GET  /api/records?url=&technique=
  GET  /api/dataset?url=&name=&technique=&max_points=
  POST /api/compare   {url, technique, key}  -> cross-format comparison
"""

from __future__ import annotations

import os
import tempfile

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from psidata import __version__, compare_record_formats, get_readers
from psidata.convert import to_csdm, to_hdf5
from starlette.background import BackgroundTask

from . import services

app = FastAPI(title="PsiData API", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("PSIDATA_CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "readers": [{"technique": r.technique, "name": r.name, "extensions": list(r.extensions)}
                    for r in get_readers()],
    }


@app.get("/api/scan")
def scan(url: str = Query(..., description="GitHub repo URL or owner/repo")) -> dict:
    try:
        return services.scan_summary(services.scan_repo(url))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not scan {url!r}: {exc}") from exc


@app.get("/api/records")
def records(url: str, technique: str) -> list[dict]:
    catalog = services.scan_repo(url)
    return [services.record_row(r) for r in catalog.record_groups().get(technique, []) if r.supported]


@app.get("/api/dataset")
def dataset(url: str, name: str, technique: str | None = None, max_points: int = 4000) -> dict:
    try:
        ds = services.load_dataset(name, url, technique=technique)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not load {name!r}: {exc}") from exc
    return services.dataset_json(ds, max_points=max_points)


@app.get("/api/convert")
def convert(url: str, name: str, technique: str | None = None, fmt: str = "csdf"):
    """Convert a dataset to a standard format and return it as a download (CSDM or HDF5)."""
    try:
        ds = services.load_dataset(name, url, technique=technique)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not load {name!r}: {exc}") from exc
    stem = (ds.source.filename or "dataset").rsplit(".", 1)[0]
    fmt = fmt.lower()
    if fmt in ("csdf", "csdm"):
        return Response(
            to_csdm(ds), media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{stem}.csdf"'},
        )
    if fmt in ("h5", "hdf5"):
        tmp = tempfile.NamedTemporaryFile(suffix=".h5", delete=False)
        tmp.close()
        to_hdf5(ds, tmp.name)
        return FileResponse(
            tmp.name, media_type="application/x-hdf5", filename=f"{stem}.h5",
            background=BackgroundTask(lambda: os.unlink(tmp.name)),
        )
    raise HTTPException(status_code=400, detail=f"unsupported format {fmt!r} (use csdf or hdf5)")


@app.post("/api/compare")
def compare(payload: dict = Body(...)) -> dict:
    url, technique, key = payload.get("url"), payload.get("technique"), payload.get("key")
    if not (url and technique and key):
        raise HTTPException(status_code=422, detail="url, technique and key are required")
    catalog = services.scan_repo(url)
    record = next((r for r in catalog.record_groups().get(technique, []) if r.key == key), None)
    if record is None:
        raise HTTPException(status_code=404, detail=f"record {key!r} not found")
    return compare_record_formats(record, services.load_dataset)


def main() -> None:
    import uvicorn
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"),
                port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
