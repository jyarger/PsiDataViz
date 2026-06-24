from __future__ import annotations

import numpy as np

from psidata import Candidate, read


def _edf(arr: np.ndarray, *, byteorder: str = "LowByteFirst") -> bytes:
    rows, cols = arr.shape
    header = (
        f"{{\nDim_1 = {cols} ;\nDim_2 = {rows} ;\n"
        f"DataType = FloatValue ;\nByteOrder = {byteorder} ;\n"
        "BIO_SAMPLE_NAME = watertest ;\n}\n"
    )
    order = "<" if "low" in byteorder.lower() else ">"
    return header.encode("latin1") + arr.astype(order + "f4").tobytes()


def test_read_edf_detector_image():
    arr = np.array([[1, 2, 3], [4, 5, 6]], dtype="float32")
    ds = read(Candidate(filename="frame.edf", content=_edf(arr), technique_hint="XRD"))
    assert ds.technique == "XRD" and ds.source.reader == "xrd_image"
    assert ds.signals == [] and len(ds.images) == 1
    im = ds.images[0]
    assert im.shape == (2, 3)
    np.testing.assert_array_equal(im.data, arr)
    assert im.z.label == "Intensity"
    assert ds.metadata.sample_name == "watertest"


def test_read_h5_detector_image(tmp_path):
    import h5py

    p = tmp_path / "frame.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("entry/data/data", data=np.arange(12, dtype="uint32").reshape(3, 4))
        f["entry/Metadata/Sample_Description"] = np.array([b"AuSi"])
    ds = read(Candidate(filename="frame.h5", content=p.read_bytes(), technique_hint="XRD"))
    assert ds.source.reader == "xrd_image"
    im = ds.images[0]
    assert im.shape == (3, 4)
    assert float(im.data.max()) == 11.0
    assert ds.metadata.sample_name == "AuSi"


def test_edf_not_claimed_without_brace_magic():
    from psidata.readers.xrd_image import XRDImageReader

    assert XRDImageReader().sniff(Candidate(filename="x.edf", content=b"not an edf")) == 0.0
