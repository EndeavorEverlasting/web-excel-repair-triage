"""
triage/diff.py
--------------
Part-level diff between a candidate .xlsx and its repaired counterpart.
Produces a DiffReport with hash/size deltas and XML unified-diff snippets.
No reserialization; all operations are byte/string level.
"""
from __future__ import annotations
import difflib
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from triage.scanner import scan, ScanResult


@dataclass
class PartDelta:
    name: str
    status: str  # "added" | "removed" | "changed" | "unchanged"
    candidate_size: Optional[int] = None
    repaired_size: Optional[int] = None
    candidate_sha256: Optional[str] = None
    repaired_sha256: Optional[str] = None
    size_delta: Optional[int] = None
    xml_diff: Optional[str] = None  # unified diff snippet for XML parts


@dataclass
class DiffReport:
    candidate_path: str
    repaired_path: str
    parts: List[PartDelta] = field(default_factory=list)

    @property
    def added(self) -> List[PartDelta]:
        return [p for p in self.parts if p.status == "added"]

    @property
    def removed(self) -> List[PartDelta]:
        return [p for p in self.parts if p.status == "removed"]

    @property
    def changed(self) -> List[PartDelta]:
        return [p for p in self.parts if p.status == "changed"]

    @property
    def unchanged(self) -> List[PartDelta]:
        return [p for p in self.parts if p.status == "unchanged"]

    def summary(self) -> Dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "changed": len(self.changed),
            "unchanged": len(self.unchanged),
        }

    def to_dict(self) -> dict:
        return {
            "candidate": self.candidate_path,
            "repaired": self.repaired_path,
            "summary": self.summary(),
            "added": [p.name for p in self.added],
            "removed": [p.name for p in self.removed],
            "changed": [
                {
                    "part": p.name,
                    "candidate_size": p.candidate_size,
                    "repaired_size": p.repaired_size,
                    "size_delta": p.size_delta,
                    "candidate_sha256": p.candidate_sha256,
                    "repaired_sha256": p.repaired_sha256,
                    "xml_diff": p.xml_diff,
                }
                for p in self.changed
            ],
        }


def _xml_diff(a_bytes: bytes, b_bytes: bytes, context: int = 4, max_lines: int = 200) -> str:
    a_lines = a_bytes.decode("utf-8", errors="ignore").splitlines()
    b_lines = b_bytes.decode("utf-8", errors="ignore").splitlines()
    diff = list(difflib.unified_diff(a_lines, b_lines, lineterm="", n=context))
    if len(diff) > max_lines:
        diff = diff[:max_lines] + [f"... diff truncated at {max_lines} lines ..."]
    return "\n".join(diff)


def _read(path: str, name: str) -> bytes:
    with zipfile.ZipFile(path, "r") as z:
        return z.read(name)


def diff_packages(candidate_path: str, repaired_path: str) -> DiffReport:
    """
    Compare candidate vs repaired at the ZIP-entry level.
    Returns a DiffReport with per-part status + XML diff snippets.
    """
    cand_scan: ScanResult = scan(candidate_path)
    rep_scan: ScanResult = scan(repaired_path)

    cand_map = {p.name: p for p in cand_scan.parts}
    rep_map = {p.name: p for p in rep_scan.parts}

    all_names = sorted(set(cand_map) | set(rep_map))
    report = DiffReport(candidate_path=candidate_path, repaired_path=repaired_path)

    for name in all_names:
        in_cand = name in cand_map
        in_rep = name in rep_map

        if in_cand and not in_rep:
            cp = cand_map[name]
            report.parts.append(PartDelta(
                name=name, status="removed",
                candidate_size=cp.size, candidate_sha256=cp.sha256,
            ))
        elif in_rep and not in_cand:
            rp = rep_map[name]
            report.parts.append(PartDelta(
                name=name, status="added",
                repaired_size=rp.size, repaired_sha256=rp.sha256,
            ))
        else:
            cp, rp = cand_map[name], rep_map[name]
            if cp.sha256 == rp.sha256:
                report.parts.append(PartDelta(
                    name=name, status="unchanged",
                    candidate_size=cp.size, repaired_size=rp.size,
                    candidate_sha256=cp.sha256, repaired_sha256=rp.sha256,
                ))
            else:
                xml_diff_txt = None
                if name.lower().endswith(".xml"):
                    a_raw = _read(candidate_path, name)
                    b_raw = _read(repaired_path, name)
                    xml_diff_txt = _xml_diff(a_raw, b_raw)
                report.parts.append(PartDelta(
                    name=name, status="changed",
                    candidate_size=cp.size, repaired_size=rp.size,
                    size_delta=rp.size - cp.size,
                    candidate_sha256=cp.sha256, repaired_sha256=rp.sha256,
                    xml_diff=xml_diff_txt,
                ))

    return report

