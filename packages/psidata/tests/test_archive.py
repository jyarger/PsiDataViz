from __future__ import annotations

import io
import zipfile

import pytest

from psidata import ArchiveError, read_zip


def _zip(files: dict[str, str | bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_read_zip_of_text_data_file(dsc_txt):
    content = _zip({
        "__MACOSX/._x.txt": "junk",                    # macOS fork — must be ignored
        "2023_06_14_Indium_wire_std.txt": dsc_txt,
    })
    ds = read_zip("2023_06_14_Indium_wire_std.txt.zip", content)
    assert ds.technique == "DSC"
    assert len(ds.signals) == 2


def test_read_zip_passes_technique_hint(raman_csv):
    content = _zip({"2022_CBD_977wn.csv": raman_csv})
    ds = read_zip("2022_CBD_977wn.csv.zip", content, technique_hint="Raman")
    assert ds.technique == "Raman"


def test_bruker_directory_archive_reports_clearly():
    content = _zip({"expt/1/fid": b"\x00\x01\x02\x03", "expt/1/acqus": "##TITLE= acqus\n"})
    with pytest.raises(ArchiveError, match="Bruker"):
        read_zip("dataset.zip", content)


def test_empty_or_unknown_archive_raises():
    with pytest.raises(ArchiveError):
        read_zip("empty.zip", _zip({}))
    with pytest.raises(ArchiveError, match="no recognized data"):
        read_zip("imgs.zip", _zip({"a.png": b"\x89PNG"}))
