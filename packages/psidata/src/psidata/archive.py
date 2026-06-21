"""Read datasets packaged inside a ``.zip`` archive.

Two cases occur in the wild:

* **Zipped single data file** (e.g. ``…CPMG.txt.zip``) — extract the data member and hand it to the
  normal reader registry. Fully supported.
* **Bruker dataset directory** (``fid``/``acqus``/``pdata`` …) — needs real Bruker processing to turn
  the FID / processed data into a ppm spectrum. Detected and reported clearly (planned via nmrglue).

macOS ``__MACOSX`` resource-fork entries are ignored.
"""

from __future__ import annotations

import io
import os
import zipfile

from .readers.base import Candidate
from .registry import read

_TEXT_DATA_EXTS = {".txt", ".csv", ".dx", ".jdx", ".dpt", ".asc", ".dat", ".tsv"}
_BRUKER_MARKERS = {"acqus", "acqu", "fid", "ser", "pulseprogram", "procs"}


class ArchiveError(Exception):
    """Raised when an archive can't be turned into a dataset (empty, unknown, or Bruker-dir)."""


def _members(zf: zipfile.ZipFile) -> list[str]:
    return [m for m in zf.namelist() if not m.endswith("/") and "__MACOSX" not in m]


def looks_like_bruker(members: list[str]) -> bool:
    return bool({os.path.basename(m) for m in members} & _BRUKER_MARKERS)


def read_zip(filename: str, content: bytes, *, technique_hint: str | None = None):
    """Parse the dataset contained in a zip archive's bytes into the universal model."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ArchiveError(f"{filename}: not a valid zip archive ({exc})") from exc

    members = _members(zf)
    if not members:
        raise ArchiveError(f"{filename}: archive is empty")

    if looks_like_bruker(members):
        raise ArchiveError(
            f"{filename}: looks like a Bruker dataset archive (fid/acqus). Reading processed "
            "Bruker spectra from a .zip is planned (via nmrglue) but not yet supported."
        )

    data_members = [m for m in members if os.path.splitext(m)[1].lower() in _TEXT_DATA_EXTS]
    if not data_members:
        raise ArchiveError(
            f"{filename}: no recognized data file inside (members: {members[:5]})"
        )

    member = max(data_members, key=lambda m: zf.getinfo(m).file_size)
    candidate = Candidate(filename=os.path.basename(member), content=zf.read(member),
                          uri=filename, technique_hint=technique_hint)
    return read(candidate)
