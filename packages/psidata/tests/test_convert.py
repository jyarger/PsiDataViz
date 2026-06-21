from __future__ import annotations

import json
from pathlib import Path

from psidata import Candidate, convert, read
from psidata.convert import to_csdm, to_hdf5, to_zarr


def _dataset(dsc_txt: str):
    return read(Candidate(filename="2026_01_01_run.txt", text=dsc_txt))


def test_to_csdm_json_structure(dsc_txt):
    doc = json.loads(to_csdm(_dataset(dsc_txt)))["csdm"]
    assert doc["version"] == "1.0"
    assert len(doc["dimensions"]) == 1
    # DSC temperature is not evenly spaced -> monotonic dimension
    assert doc["dimensions"][0]["type"] == "monotonic"
    dv = doc["dependent_variables"]
    assert len(dv) >= 1
    assert dv[0]["numeric_type"] == "float64"
    assert len(dv[0]["components"][0]) == len(doc["dimensions"][0]["coordinates"])


def test_to_csdm_linear_dimension():
    # an evenly spaced abscissa -> linear dimension
    nmr = (
        "##TITLE=t\n##JCAMP-DX=5.01\n##DATA TYPE= NMR SPECTRUM\n##.OBSERVE NUCLEUS=1H\n"
        "##XUNITS=PPM\n##XYDATA=(XY..XY)\n10 1\n9 2\n8 5\n7 2\n6 1\n##END=\n"
    )
    doc = json.loads(to_csdm(read(Candidate(filename="x.jdx", text=nmr))))["csdm"]
    assert doc["dimensions"][0]["type"] == "linear"
    assert doc["dimensions"][0]["count"] == 5


def test_to_hdf5_roundtrip(dsc_txt, tmp_path):
    import h5py

    path = to_hdf5(_dataset(dsc_txt), tmp_path / "out.h5")
    with h5py.File(path) as f:
        assert f.attrs["technique"] == "DSC"
        group = f["signals/signal_0"]
        assert group.attrs["x_label"] == "Temperature"
        assert len(group["x"]) == len(group["y"]) > 0


def test_to_zarr_roundtrip(dsc_txt, tmp_path):
    import zarr

    path = to_zarr(_dataset(dsc_txt), str(tmp_path / "out.zarr"))
    root = zarr.open_group(path, mode="r")
    assert root.attrs["technique"] == "DSC"
    group = root["signals/signal_0"]
    assert group.attrs["y_label"].startswith("Heat Flow")
    assert group["x"].shape[0] > 0


def test_convert_dispatch_by_suffix(dsc_txt, tmp_path):
    out = convert(_dataset(dsc_txt), tmp_path / "a.csdf")
    assert out.endswith(".csdf")
    assert json.loads(Path(out).read_text())["csdm"]["version"] == "1.0"
