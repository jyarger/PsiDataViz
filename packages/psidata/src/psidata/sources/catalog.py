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

    def summary(self) -> dict:
        groups = self.groups()
        return {
            "source": self.source_label,
            "n_files": len(self.entries),
            "n_supported": len(self.supported()),
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
    technique = ref.top_dir or ROOT_GROUP
    reader = _match_reader(ref.top_dir, ref.ext)
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
