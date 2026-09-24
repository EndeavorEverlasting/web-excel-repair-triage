"""
triage/scanner.py
-----------------
Package Scanner: inspect a .xlsx ZIP, enumerate parts, compute hashes + sizes.
Never re-serializes XML. All reads are byte-level.
"""
from __future__ import annotations
import hashlib
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PartInfo:
    name: str
    size: int
    sha256: str
    compress_size: int
    is_xml: bool


@dataclass
class ScanResult:
    path: str
    parts: List[PartInfo] = field(default_factory=list)
    # convenience lookups
    _by_name: Dict[str, PartInfo] = field(default_factory=dict, repr=False)

    def by_name(self, name: str) -> PartInfo | None:
        return self._by_name.get(name)

    @property
    def part_names(self) -> List[str]:
        return [p.name for p in self.parts]

    @property
    def xml_parts(self) -> List[PartInfo]:
        return [p for p in self.parts if p.is_xml]


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def scan(path: str) -> ScanResult:
    """
    Open *path* as a ZIP, enumerate every entry, return a ScanResult.
    No XML parsing; pure byte-level inspection.
    """
    result = ScanResult(path=path)
    with zipfile.ZipFile(path, "r") as z:
        for info in z.infolist():
            raw = z.read(info.filename)
            pi = PartInfo(
                name=info.filename,
                size=info.file_size,
                sha256=_sha256(raw),
                compress_size=info.compress_size,
                is_xml=info.filename.lower().endswith(".xml"),
            )
            result.parts.append(pi)
            result._by_name[info.filename] = pi
    return result


def read_part_bytes(path: str, part: str) -> bytes:
    """Read a single ZIP entry as raw bytes."""
    with zipfile.ZipFile(path, "r") as z:
        return z.read(part)


def read_part_text(path: str, part: str, encoding: str = "utf-8") -> str:
    """Read a single ZIP entry decoded to text."""
    return read_part_bytes(path, part).decode(encoding, errors="ignore")


def part_names(path: str) -> List[str]:
    """Quick listing of all ZIP entry names."""
    with zipfile.ZipFile(path, "r") as z:
        return z.namelist()

