"""triage/insight_ingest.py
------------------------
Ingest 'insights' artifacts (especially Excel recoveryLog XML) into the repo.

Why
---
Desktop Excel often writes recovery logs like %TEMP%/error*.xml. We already try
to copy those during the desktop probe, but this module covers the broader
workflow requirement: if XML appears *outside* the repo, import/copy it into
Outputs/ so we never lose the forensic evidence.

Policy
------
- Copy-only by default (never delete/move external files).
- Deduplicate by SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from triage.path_policy import repo_root
from triage.storage_policy import dir_size_bytes


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _safe_name(name: str) -> str:
    name = (name or "").strip() or "insight.xml"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:120]


def _extract_source_workbook_path(xml_text: str) -> Optional[str]:
    """Best-effort: extract the workbook path from an Excel recoveryLog XML."""
    # Example in-the-wild:
    #   <summary>Errors were detected in file 'C:\...\Deprecated\Foo.xlsx'</summary>
    m = re.search(r"Errors were detected in file '([^']+\.xlsx)'", xml_text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"file \"([^\"]+\.xlsx)\"", xml_text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def parse_recovery_log(xml_text: str) -> Dict[str, Any]:
    """Parse a recoveryLog-ish XML into a small JSONable dict (no hard failures)."""
    src = _extract_source_workbook_path(xml_text)
    repaired_records: List[str] = []
    # Avoid XML parsing dependencies/namespace fuss; this is good enough for summary.
    for rec in re.findall(r"<repairedRecord>(.*?)</repairedRecord>", xml_text, flags=re.IGNORECASE | re.DOTALL):
        repaired_records.append(re.sub(r"\s+", " ", rec).strip()[:400])
    return {
        "kind": "excel_recovery_log" if "<recoverylog" in xml_text.lower() else "xml",
        "source_workbook_path": src,
        "repaired_records": repaired_records[:50],
    }


@dataclass
class IngestedInsight:
    source_path: str
    sha256: str
    dest_path: str
    parsed: Dict[str, Any] = field(default_factory=dict)
    note: Optional[str] = None


@dataclass
class IngestResult:
    sources: List[str]
    scanned_at: str
    dest_root: str
    matched_files: int
    copied: int
    skipped_duplicates: int
    errors: int
    insights: List[IngestedInsight]
    report_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "sources": self.sources,
            "scanned_at": self.scanned_at,
            "dest_root": self.dest_root,
            "matched_files": self.matched_files,
            "copied": self.copied,
            "skipped_duplicates": self.skipped_duplicates,
            "errors": self.errors,
            "insights": [asdict(x) for x in self.insights],
            "report_path": self.report_path,
        }


def _iter_xml_files(source: Path, *, recursive: bool, max_files: int) -> Iterable[Path]:
    it = source.rglob("*.xml") if recursive else source.glob("*.xml")
    n = 0
    for p in it:
        if n >= int(max_files):
            break
        try:
            if p.is_file():
                yield p
                n += 1
        except Exception:
            continue


def ingest_xml_insights(
    sources: List[str | Path],
    *,
    dest_root: str | Path = "Outputs/insights/xml",
    recursive: bool = True,
    max_files: int = 500,
    dedupe: bool = True,
    budget_bytes: Optional[int] = None,
) -> IngestResult:
    """Copy .xml insights from *sources* into the repo.

    - Each source may be a file or directory.
    - Returns an IngestResult; also writes a JSON report under Outputs/insights/.
    """
    rr = repo_root()
    ts = _now_ts()

    dest_dir = Path(dest_root)
    if not dest_dir.is_absolute():
        dest_dir = rr / dest_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Put each run into its own folder for auditability.
    run_dir = dest_dir / f"ingest_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)

    budget_used = dir_size_bytes(dest_dir) if budget_bytes is not None else 0

    matched = 0
    copied = 0
    skipped = 0
    errors = 0
    insights: List[IngestedInsight] = []

    # Simple dedupe set based on existing files in dest_root.
    existing_shas: set[str] = set()
    if dedupe:
        try:
            for p in dest_dir.rglob("*.xml"):
                nm = p.name
                # Expected prefix: <sha256>_<name>.xml
                if re.match(r"^[a-f0-9]{64}_", nm):
                    existing_shas.add(nm.split("_", 1)[0])
        except Exception:
            existing_shas = set()

    for src in sources:
        sp = Path(src).expanduser()
        if not sp.is_absolute():
            sp = (rr / sp).resolve(strict=False)
        sp = sp.resolve(strict=False)

        if sp.is_file() and sp.suffix.lower() == ".xml":
            xml_files = [sp]
        elif sp.is_dir():
            xml_files = list(_iter_xml_files(sp, recursive=recursive, max_files=max_files))
        else:
            continue

        for xf in xml_files:
            matched += 1
            try:
                raw = xf.read_bytes()
                sha = _sha256(raw)

                if budget_bytes is not None and (budget_used + len(raw)) > int(budget_bytes):
                    skipped += 1
                    insights.append(
                        IngestedInsight(
                            source_path=str(xf),
                            sha256=sha,
                            dest_path="",
                            parsed={},
                            note="budget_exceeded_skip",
                        )
                    )
                    continue
                if dedupe and sha in existing_shas:
                    skipped += 1
                    insights.append(
                        IngestedInsight(
                            source_path=str(xf),
                            sha256=sha,
                            dest_path="",
                            parsed={},
                            note="duplicate_sha_skip",
                        )
                    )
                    continue

                dest_name = f"{sha}_{_safe_name(xf.name)}"
                dest_path = run_dir / dest_name
                dest_path.write_bytes(raw)
                copied += 1
                existing_shas.add(sha)
                if budget_bytes is not None:
                    budget_used += len(raw)

                parsed: Dict[str, Any] = {}
                try:
                    parsed = parse_recovery_log(raw.decode("utf-8", errors="replace"))
                except Exception:
                    parsed = {}

                insights.append(
                    IngestedInsight(
                        source_path=str(xf),
                        sha256=sha,
                        dest_path=str(dest_path),
                        parsed=parsed,
                    )
                )
            except Exception as e:
                errors += 1
                insights.append(
                    IngestedInsight(
                        source_path=str(xf),
                        sha256="",
                        dest_path="",
                        parsed={},
                        note=f"error: {type(e).__name__}: {e}",
                    )
                )

    res = IngestResult(
        sources=[str(x) for x in sources],
        scanned_at=ts,
        dest_root=str(dest_dir),
        matched_files=matched,
        copied=copied,
        skipped_duplicates=skipped,
        errors=errors,
        insights=insights,
    )

    report_path = (dest_dir.parent / f"insight_ingest_{ts}.json")
    report_path.write_text(json.dumps(res.to_dict(), indent=2), encoding="utf-8")
    res.report_path = str(report_path)
    return res
