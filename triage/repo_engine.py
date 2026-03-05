"""triage/repo_engine.py
---------------------
Directory classification / repo-combing engine.

Goal
----
Provide a robust, *non-destructive* way to scan the workspace and classify
artifacts into lifecycle buckets (Active/Candidates/Repaired/Deprecated/Outputs)
and to produce recommendations about what *should* happen next.

This module intentionally does **not** move/delete anything by default.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from triage.gate_checks import run_all
from triage.path_policy import repo_root, is_under_folder


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


# ─────────────────────────────────────────────────────────────────────────────-
# Model
# ─────────────────────────────────────────────────────────────────────────────-


@dataclass
class RepoItem:
    path: str
    relpath: str
    folder_bucket: str
    role: str
    ext: str
    size: int
    mtime: float
    gate: Optional[dict] = None  # run_all(...).to_dict()
    notes: List[str] = field(default_factory=list)


@dataclass
class Recommendation:
    action: str
    path: str
    reason: str
    suggested_dest: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepoScanResult:
    root: str
    scanned_at: str
    items: List[RepoItem]
    recommendations: List[Recommendation]
    summary: Dict[str, Any]
    report_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "scanned_at": self.scanned_at,
            "items": [asdict(x) for x in self.items],
            "recommendations": [asdict(x) for x in self.recommendations],
            "summary": self.summary,
            "report_path": self.report_path,
        }


# ─────────────────────────────────────────────────────────────────────────────-
# Classification
# ─────────────────────────────────────────────────────────────────────────────-


_KNOWN_BUCKETS: Tuple[str, ...] = ("Active", "Deprecated", "Candidates", "Repaired", "Outputs")


def _bucket_for_path(p: Path) -> str:
    for name in _KNOWN_BUCKETS:
        if is_under_folder(p, name):
            return name.lower()
    return "unknown"


def _role_for_path(p: Path, bucket: str) -> str:
    """Infer a semantic 'role' beyond just folder bucket."""
    parts_lower = [x.lower() for x in p.parts]
    if bucket == "active":
        return "golden"
    if bucket == "candidates":
        return "candidate"
    if bucket == "repaired":
        return "repaired"
    if bucket == "outputs":
        # includes reports, recipes, probe artifacts, etc.
        return "output"

    # Deprecated contains legacy subfolders that behave like buckets.
    if bucket == "deprecated":
        if "outputs_pre_i100" in parts_lower or "outputs" in parts_lower:
            return "output"
        if "candidates_pre_i100" in parts_lower or "candidates" in parts_lower:
            return "candidate"
        if "repaired" in parts_lower:
            return "repaired"
        if "xml_fragments" in parts_lower or "xml" in parts_lower:
            return "insight"
        return "work"

    # Unknown bucket: try light heuristics.
    if any("output" in s for s in parts_lower):
        return "output"
    if any("candidate" in s for s in parts_lower):
        return "candidate"
    if any("repaired" in s for s in parts_lower):
        return "repaired"
    return "unknown"


def _should_gate(ext: str) -> bool:
    return ext.lower() == ".xlsx"


def _walk_files(root: Path, *, recursive: bool, exts: Iterable[str], max_files: int) -> List[Path]:
    wanted = {e.lower().lstrip(".") for e in exts}
    out: List[Path] = []
    it = root.rglob("*") if recursive else root.glob("*")
    for p in it:
        if len(out) >= int(max_files):
            break
        try:
            if not p.is_file():
                continue
        except Exception:
            continue
        if wanted and p.suffix.lower().lstrip(".") not in wanted:
            continue
        out.append(p)
    return out


def scan_repo(
    *,
    root: str | Path | None = None,
    recursive: bool = True,
    exts: Tuple[str, ...] = ("xlsx", "json", "xml"),
    max_files: int = 2000,
    run_gates: bool = False,
    gates_max_files: int = 200,
) -> RepoScanResult:
    """Scan *root* (default: repo root) and classify artifacts.

    Parameters
    ----------
    root:
        Directory to scan. If None, scans the repo root.
    run_gates:
        If True, run structural gate checks for .xlsx files (bounded by gates_max_files).
    """

    rr = repo_root()
    scan_root = (Path(root) if root is not None else rr).expanduser()
    if not scan_root.is_absolute():
        scan_root = (rr / scan_root).resolve(strict=False)
    scan_root = scan_root.resolve(strict=False)

    scanned_at = _now_ts()
    files = _walk_files(scan_root, recursive=recursive, exts=exts, max_files=max_files)

    items: List[RepoItem] = []
    gate_budget = int(max(0, gates_max_files))
    gated = 0
    for p in files:
        try:
            st = p.stat()
            size = int(st.st_size)
            mtime = float(st.st_mtime)
        except Exception:
            size = 0
            mtime = 0.0

        bucket = _bucket_for_path(p)
        role = _role_for_path(p, bucket)
        rel = str(p.resolve(strict=False)).replace(str(rr), "").lstrip("\\/")
        it = RepoItem(
            path=str(p),
            relpath=rel,
            folder_bucket=bucket,
            role=role,
            ext=p.suffix.lower(),
            size=size,
            mtime=mtime,
        )

        if run_gates and _should_gate(it.ext) and gated < gate_budget:
            try:
                it.gate = run_all(str(p)).to_dict()
                gated += 1
            except Exception as e:
                it.notes.append(f"gate_error: {type(e).__name__}: {e}")

        items.append(it)

    recs = recommend(items)
    summary = summarize(items, recs, gate_ran=gated)
    return RepoScanResult(root=str(scan_root), scanned_at=scanned_at, items=items, recommendations=recs, summary=summary)


def recommend(items: List[RepoItem]) -> List[Recommendation]:
    recs: List[Recommendation] = []
    for it in items:
        # Suspicious: non-xlsx artifacts in Active.
        if it.folder_bucket == "active" and it.ext and it.ext != ".xlsx":
            recs.append(
                Recommendation(
                    action="FLAG_ACTIVE_NON_XLSX",
                    path=it.path,
                    reason=f"Active/ should be golden workbooks; found {it.ext}",
                )
            )

        # Active workbook failing gates: highlight, never auto-move.
        if it.folder_bucket == "active" and it.gate and not bool(it.gate.get("pass")):
            recs.append(
                Recommendation(
                    action="FLAG_ACTIVE_FAILING_GATES",
                    path=it.path,
                    reason="Active/ workbook fails structural gates; verify it is truly golden.",
                    extra={"failing_gates": (it.gate.get("failing_gates") or {})},
                )
            )

        # Deprecated workbook passing gates: promotion candidate.
        if it.folder_bucket == "deprecated" and it.ext == ".xlsx" and it.gate and bool(it.gate.get("pass")):
            recs.append(
                Recommendation(
                    action="PROMOTION_CANDIDATE",
                    path=it.path,
                    reason="Deprecated/ workbook passes gates; consider Promote → Active.",
                    suggested_dest=str(Path(repo_root()) / "Active" / Path(it.path).name),
                )
            )

        # Root-level / unknown bucket .xlsx: suggest importing into Deprecated.
        if it.folder_bucket == "unknown" and it.ext == ".xlsx":
            recs.append(
                Recommendation(
                    action="IMPORT_TO_DEPRECATED",
                    path=it.path,
                    reason="Workbook is outside known lifecycle folders; import into Deprecated/ (work area) before iterating.",
                    suggested_dest=str(Path(repo_root()) / "Deprecated" / Path(it.path).name),
                )
            )

        # Deprecated output-like artifacts: suggest relocating into Outputs/ so the
        # work area stays clean.
        if it.folder_bucket == "deprecated" and it.role in {"output", "insight"} and it.ext and it.ext != ".xlsx":
            dep_root = Path(repo_root()) / "Deprecated"
            src_p = Path(it.path)
            try:
                rel = src_p.resolve(strict=False).relative_to(dep_root.resolve(strict=False))
                suggested = Path(repo_root()) / "Outputs" / "legacy_from_deprecated" / rel
            except Exception:
                suggested = Path(repo_root()) / "Outputs" / "legacy_from_deprecated" / src_p.name
            recs.append(
                Recommendation(
                    action="RELOCATE_DEPRECATED_ARTIFACT_TO_OUTPUTS",
                    path=it.path,
                    reason="Artifact under Deprecated/ looks like an output/insight; relocate into Outputs/ for organization.",
                    suggested_dest=str(suggested),
                    extra={"role": it.role, "ext": it.ext},
                )
            )

        # Deprecated candidate-like workbooks: suggest relocating into Candidates/.
        if it.folder_bucket == "deprecated" and it.role == "candidate" and it.ext == ".xlsx":
            recs.append(
                Recommendation(
                    action="RELOCATE_DEPRECATED_CANDIDATE_TO_CANDIDATES",
                    path=it.path,
                    reason="Workbook under Deprecated/ appears to be a candidate; consider moving to Candidates/.",
                    suggested_dest=str(Path(repo_root()) / "Candidates" / Path(it.path).name),
                )
            )

    return recs


def summarize(items: List[RepoItem], recs: List[Recommendation], *, gate_ran: int = 0) -> Dict[str, Any]:
    by_bucket: Dict[str, int] = {}
    by_role: Dict[str, int] = {}
    xlsx = 0
    gate_pass = 0
    gate_fail = 0
    gate_err = 0
    for it in items:
        by_bucket[it.folder_bucket] = by_bucket.get(it.folder_bucket, 0) + 1
        by_role[it.role] = by_role.get(it.role, 0) + 1
        if it.ext == ".xlsx":
            xlsx += 1
        if it.gate is not None:
            if it.gate.get("pass") is True:
                gate_pass += 1
            elif it.gate.get("pass") is False:
                gate_fail += 1
            else:
                gate_err += 1

    by_action: Dict[str, int] = {}
    for r in recs:
        by_action[r.action] = by_action.get(r.action, 0) + 1

    return {
        "counts": {
            "items": len(items),
            "xlsx": xlsx,
            "gate_ran": int(gate_ran),
            "gate_pass": gate_pass,
            "gate_fail": gate_fail,
            "gate_err": gate_err,
            "recommendations": len(recs),
        },
        "by_bucket": dict(sorted(by_bucket.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_role": dict(sorted(by_role.items(), key=lambda kv: (-kv[1], kv[0]))),
        "by_action": dict(sorted(by_action.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def write_report(result: RepoScanResult, *, out_root: str | Path = "Outputs/repo_scans") -> str:
    out_dir = Path(out_root)
    if not out_dir.is_absolute():
        out_dir = repo_root() / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"repo_scan_{result.scanned_at}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    result.report_path = str(path)
    return str(path)
