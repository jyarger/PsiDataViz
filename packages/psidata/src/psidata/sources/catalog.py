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
    """Find a registered reader whose technique matches the folder and whose extension fits."""
    folder = top_dir.lower()
    for reader in get_readers():
        tech = reader.technique.lower()
        if (tech == folder or (tech in folder) or (folder in tech and folder)) and (
            not reader.extensions or ext in reader.extensions
        ):
            return reader
    return None


def build_entry(ref: FileRef) -> CatalogEntry:
    technique = canonical_technique(ref.top_dir)
    reader = _match_reader(technique, ref.ext)
    return CatalogEntry(
        file=ref,
        technique=technique,
        parsed=parse_filename(ref.name),
        supported=reader is not None,
        reader_name=reader.name if reader else None,
    )


def scan(source: DataSource) -> Catalog:
    """List a source and build a grouped, summarized catalog (no file contents fetched)."""
    entries = [build_entry(ref) for ref in source.list_files()]
    return Catalog(source_label=source.label, entries=entries)
