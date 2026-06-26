"""Scan a :class:`DataSource` into a grouped, summarized catalog — cheaply, without downloads.

Files are grouped by their top-level folder (the lab convention: one folder per instrument/method),
enriched with filename-derived metadata (date, description), and flagged as ``supported`` when a
registered reader is likely to handle them. Full parsing happens later, on demand.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ..filename import ParsedName, parse_filename
from ..registry import get_readers
from .base import DataSource, FileRef

ROOT_GROUP = "(root)"

# Different labs/sources name the same technique folder differently (e.g. "IR" vs "FTIR").
# Map lowercase folder names to one canonical technique so they merge into a single group.
_TECHNIQUE_ALIASES = {
    "ir": "FTIR",
    "ft-ir": "FTIR",
    "ftir": "FTIR",
    "infrared": "FTIR",
    "uv": "UV-Vis",
    "uvvis": "UV-Vis",
    "uv-vis": "UV-Vis",
    "uv_vis": "UV-Vis",
    "uv-visible": "UV-Vis",
    "mass_spec": "Mass Spec",
    "massspec": "Mass Spec",
    "ms": "Mass Spec",
    "circular_dichroism": "CD",
}


def canonical_technique(top_dir: str) -> str:
    """Normalize a folder name to one canonical technique label (``IR`` → ``FTIR``, …)."""
    if not top_dir:
        return ROOT_GROUP
    return _TECHNIQUE_ALIASES.get(top_dir.strip().lower(), top_dir)


@dataclass(frozen=True)
class CatalogEntry:
    file: FileRef
    technique: str
    parsed: ParsedName
    supported: bool
    reader_name: str | None = None

    def as_dict(self) -> dict:
        return {
            "path": self.file.path,
            "name": self.file.name,
            "technique": self.technique,
            "date": self.parsed.date.isoformat() if self.parsed.date else None,
            "description": self.parsed.description,
            "ext": self.file.ext,
            "size": self.file.size,
            "supported": self.supported,
            "reader": self.reader_name,
            "download_url": self.file.download_url,
        }


@dataclass
class Catalog:
    source_label: str
    entries: list[CatalogEntry]

    def groups(self) -> dict[str, list[CatalogEntry]]:
        grouped: dict[str, list[CatalogEntry]] = defaultdict(list)
        for entry in self.entries:
            grouped[entry.technique].append(entry)
        return dict(sorted(grouped.items()))

    def techniques(self) -> list[str]:
        return sorted({e.technique for e in self.entries})

    def supported(self) -> list[CatalogEntry]:
        return [e for e in self.entries if e.supported]

    def records(self):
        """Collapse files into datasets: one :class:`DataRecord` per base name, many formats."""
        from .records import build_records  # local import avoids a circular dependency
        return build_records(self.entries)

    def record_groups(self) -> dict[str, list]:
        """Records grouped by technique (the dataset-centric view of the catalog)."""
        grouped: dict[str, list] = defaultdict(list)
        for record in self.records():
            grouped[record.technique].append(record)
        return dict(sorted(grouped.items()))

    def summary(self) -> dict:
        groups = self.groups()
        records = self.records()
        data_records = [r for r in records if r.is_data_record]
        return {
            "source": self.source_label,
            "n_files": len(self.entries),
            "n_supported": len(self.supported()),
            "n_records": len(records),
            "n_data_records": len(data_records),
            "n_supported_records": sum(r.supported for r in records),
            "groups": {
                tech: {
                    "n_files": len(items),
                    "n_supported": sum(e.supported for e in items),
                }
                for tech, items in groups.items()
            },
        }


def _match_reader(top_dir: str, ext: str):
    """Find a registered reader whose technique matches the folder and whose extension fits.

    A generic reader (``technique == "*"``, e.g. the spreadsheet reader) is used only as a fallback when
    no technique-specific reader matches.
    """
    folder = canonical_technique(top_dir).lower()
    generic = None
    for reader in get_readers():
        tech = reader.technique.lower()
        ext_ok = not reader.extensions or ext in reader.extensions
        if tech == "*":
            if ext_ok and generic is None:
                generic = reader
        elif ext_ok and (tech == folder or tech in folder or (folder in tech and folder)):
            return reader
    return generic


def _technique_has_reader(technique: str) -> bool:
    """True if a *technique-specific* reader handles this technique (generic readers don't count)."""
    folder = canonical_technique(technique).lower()
    return any(
        r.technique.lower() != "*" and (
            r.technique.lower() == folder or r.technique.lower() in folder
            or (folder and folder in r.technique.lower()))
        for r in get_readers()
    )


# Keyword -> technique, for sources organized by sample/compound (the top folder is the molecule,
# not the instrument), where the technique is encoded in the filename instead.
_TECHNIQUE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("FTIR", ("ftir", "_ir_", "_ir.", "atrir", "atr-ir", "infrared", "opus")),
    ("NMR", ("nmr", "bruker400", "bruker500", "spinsolve", "nmready", "mhz", "_1h", "_13c", "_31p",
             "_19f", "_15n")),
    ("Raman", ("raman",)),  # bare wavelengths (532nm…) are ambiguous (also Brillouin) — keep explicit
    ("DSC", ("dsc", "mdsc", "calorimetry", "trios", "cmin")),  # cmin = a °C/min ramp rate (e.g. 5Cmin)
    ("XRD", ("xrd", "pxrd", "saxs", "waxs", "giwaxs", "diffract")),
    ("UV-Vis", ("uvvis", "uv-vis", "uv_vis", "uv_visible")),
    ("TGA", ("tga", "thermogravimetric")),
)


def infer_technique(filename: str) -> str | None:
    """Guess the technique from a filename's keywords (for sample-organized sources)."""
    low = filename.lower()
    for technique, keywords in _TECHNIQUE_KEYWORDS:
        if any(kw in low for kw in keywords):
            return technique
    return None


def build_entry(ref: FileRef) -> CatalogEntry:
    technique = canonical_technique(ref.top_dir)
    if not _technique_has_reader(technique):
        # sample-organized source (the top folder is a compound): infer technique from the filename
        technique = infer_technique(ref.name) or technique
    reader = _match_reader(technique, ref.ext)
    supported = reader is not None
    reader_name = reader.name if reader else None
    # A `.zip` is a packaged dataset (e.g. zipped Bruker/SpinSolve NMR); mark it supported when the
    # technique has a reader, and let `read_zip` extract/parse it on open.
    if ref.ext == ".zip" and not supported and _technique_has_reader(technique):
        supported, reader_name = True, "archive_zip"
    return CatalogEntry(
        file=ref,
        technique=technique,
        parsed=parse_filename(ref.name),
        supported=supported,
        reader_name=reader_name,
    )


def scan(source: DataSource) -> Catalog:
    """List a source and build a grouped, summarized catalog (no file contents fetched)."""
    entries = [build_entry(ref) for ref in source.list_files()]
    return Catalog(source_label=source.label, entries=entries)
