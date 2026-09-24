"""triage/repo_apply.py
----------------------
Opt-in application of Repo Engine recommendations.

Policy
------
- Prefer copy over move (non-destructive) unless explicitly requested.
- If overwriting: create a backup of the existing destination first.
- If destination exists with different hash: require an explicit confirmation
  phrase from the caller (UI supplies it).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.path_policy import repo_root
from triage.storage_policy import dir_size_bytes


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _now_ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in (name or ""))[:120] or "file"


@dataclass
class AppliedOp:
    action: str
    src: str
    dest: str
    mode: str  # copy|move
    status: str  # ok|skipped|error
    note: str = ""
    src_sha256: str = ""
    dest_sha256_before: str = ""
    dest_sha256_after: str = ""
    backup_path: Optional[str] = None
    bytes_copied: int = 0


@dataclass
class ApplyResult:
    endeavor: str
    applied_at: str
    ops: List[AppliedOp]
    report_path: str
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "endeavor": self.endeavor,
            "applied_at": self.applied_at,
            "ops": [asdict(o) for o in self.ops],
            "summary": self.summary,
            "report_path": self.report_path,
        }


def _backup_existing(dest: Path, backups_root: Path) -> Path:
    backups_root.mkdir(parents=True, exist_ok=True)
    sha = _sha256_file(dest)
    stamp = _now_ts()
    backup_name = f"{_safe_name(dest.stem)}__backup__{stamp}__{sha[:12]}{dest.suffix or '.bak'}"
    backup_path = backups_root / backup_name
    shutil.copy2(dest, backup_path)
    return backup_path


def _copy_or_move(src: Path, dest: Path, *, move: bool) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if move:
        # shutil.move returns dest path string; bytes unknown, so compute from src stat pre-move
        n = int(src.stat().st_size) if src.exists() else 0
        shutil.move(str(src), str(dest))
        return n
    shutil.copy2(src, dest)
    return int(dest.stat().st_size) if dest.exists() else 0


def apply_recommendations(
    recs: List[dict],
    *,
    selected_actions: List[str],
    move_instead_of_copy: bool = False,
    allow_overwrite: bool = False,
    confirmation_phrase: str = "",
    required_phrase: str = "OVERWRITE",
    budget_root: str | Path = "Outputs",
    budget_bytes: Optional[int] = None,
    backups_dir: str | Path = "Outputs/backups",
    outputs_dir: str | Path = "Outputs/repo_actions",
) -> ApplyResult:
    """Apply selected recommendation actions.

    Expected recommendation dict schema (from Repo Engine):
      {action, path, suggested_dest?, reason?, extra?}
    """
    rr = repo_root()
    ts = _now_ts()

    out_dir = Path(outputs_dir)
    if not out_dir.is_absolute():
        out_dir = rr / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    bdir = Path(backups_dir)
    if not bdir.is_absolute():
        bdir = rr / bdir
    bdir.mkdir(parents=True, exist_ok=True)
    bdir = bdir / f"backup_{ts}"
    bdir.mkdir(parents=True, exist_ok=True)

    budget_root_p = Path(budget_root)
    if not budget_root_p.is_absolute():
        budget_root_p = (rr / budget_root_p).resolve(strict=False)
    budget_used = dir_size_bytes(budget_root_p) if budget_bytes is not None else 0

    ops: List[AppliedOp] = []

    for r in recs:
        action = (r.get("action") or "").strip()
        if action not in set(selected_actions):
            continue
        src = Path(r.get("path") or "")
        dest_s = r.get("suggested_dest") or ""
        if not dest_s:
            ops.append(AppliedOp(action=action, src=str(src), dest="", mode="move" if move_instead_of_copy else "copy", status="skipped", note="no_suggested_dest"))
            continue
        dest = Path(dest_s)
        if not dest.is_absolute():
            dest = (rr / dest).resolve(strict=False)
        src = src.resolve(strict=False)
        dest = dest.resolve(strict=False)

        op = AppliedOp(action=action, src=str(src), dest=str(dest), mode="move" if move_instead_of_copy else "copy", status="error")
        try:
            if not src.exists() or not src.is_file():
                op.status = "skipped"
                op.note = "missing_src"
                ops.append(op)
                continue

            op.src_sha256 = _sha256_file(src)

            # Budget enforcement (safe-by-default): skip operations that would push
            # the budget root beyond budget_bytes.
            if budget_bytes is not None:
                try:
                    under_budget_root = dest.is_relative_to(budget_root_p)
                except Exception:
                    under_budget_root = False
                if under_budget_root:
                    src_size = int(src.stat().st_size)
                    if budget_used + src_size > int(budget_bytes):
                        op.status = "skipped"
                        op.note = "budget_exceeded"
                        ops.append(op)
                        continue

            if dest.exists() and dest.is_file():
                op.dest_sha256_before = _sha256_file(dest)
                if op.dest_sha256_before == op.src_sha256:
                    op.status = "skipped"
                    op.note = "dest_same_hash"
                    ops.append(op)
                    continue

                if not allow_overwrite:
                    op.status = "skipped"
                    op.note = "dest_exists_no_overwrite"
                    ops.append(op)
                    continue

                if (confirmation_phrase or "").strip() != required_phrase:
                    op.status = "skipped"
                    op.note = "overwrite_requires_confirmation"
                    ops.append(op)
                    continue

                backup_path = _backup_existing(dest, bdir)
                op.backup_path = str(backup_path)

            op.bytes_copied = _copy_or_move(src, dest, move=bool(move_instead_of_copy))
            if dest.exists() and dest.is_file():
                op.dest_sha256_after = _sha256_file(dest)
            op.status = "ok"
            if budget_bytes is not None:
                try:
                    if dest.is_relative_to(budget_root_p):
                        budget_used += int(op.bytes_copied)
                except Exception:
                    pass
        except Exception as e:
            op.status = "error"
            op.note = f"{type(e).__name__}: {e}"
        ops.append(op)

    ok = sum(1 for o in ops if o.status == "ok")
    skipped = sum(1 for o in ops if o.status == "skipped")
    err = sum(1 for o in ops if o.status == "error")
    summary = {"ok": ok, "skipped": skipped, "error": err, "total": len(ops)}

    report_path = out_dir / f"apply_recommendations_{ts}.json"
    res = ApplyResult(
        endeavor="APPLY_REPO_RECOMMENDATIONS",
        applied_at=ts,
        ops=ops,
        report_path=str(report_path),
        summary=summary,
    )
    report_path.write_text(json.dumps(res.to_dict(), indent=2), encoding="utf-8")
    return res
