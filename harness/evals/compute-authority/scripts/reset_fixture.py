#!/usr/bin/env python3
"""Reset a compute-authority fixture workspace to its pristine snapshot."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIX = ROOT / "harness" / "evals" / "compute-authority" / "fixtures"
HIDDEN_NAMES = {"evaluator.manifest.yaml", "AGENT_MUST_NOT_SEE.txt", "workspace.sha256"}


def workspace_hash(ws: Path) -> str:
    files = sorted(p for p in ws.rglob("*") if p.is_file())
    h = hashlib.sha256()
    for path in files:
        rel = path.relative_to(ws).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def pristine_dir(case_id: str) -> Path:
    return FIX / case_id / "workspace"


def work_dir(case_id: str, run_id: str | None) -> Path:
    if run_id:
        return ROOT / "harness" / "evals" / "compute-authority" / "runs" / run_id / "workspace"
    return FIX / case_id / "work"


def _rmtree(path: Path) -> None:
    if not path.exists():
        return

    def onexc(func, p, _exc_info=None):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    last_error: Exception | None = None
    for _ in range(8):
        try:
            shutil.rmtree(path, onerror=lambda func, p, info: onexc(func, p, info))
            if not path.exists():
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.15)
    if path.exists():
        raise RuntimeError(f"unable to remove {path}: {last_error}")


def reset_case(case_id: str, run_id: str | None = None) -> Path:
    src = pristine_dir(case_id)
    if not src.is_dir():
        raise FileNotFoundError(f"missing pristine workspace: {src}")
    expected = (FIX / case_id / "workspace.sha256").read_text(encoding="utf-8").strip()
    actual = workspace_hash(src)
    if actual != expected:
        raise RuntimeError(
            f"pristine workspace drift for {case_id}: {actual} != {expected}. "
            "Re-run materialize_fixtures.py"
        )
    dest = work_dir(case_id, run_id)
    _rmtree(dest)
    shutil.copytree(src, dest)
    for name in HIDDEN_NAMES:
        stray = dest / name
        if stray.exists():
            stray.unlink()
    parent = FIX / case_id
    for name in HIDDEN_NAMES:
        if (dest / name).exists():
            raise RuntimeError(f"hidden evaluator file leaked into workspace: {name}")
        if name == "evaluator.manifest.yaml" and not (parent / name).is_file():
            raise RuntimeError(f"missing hidden manifest for {case_id}")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, help="TC01..TC08")
    parser.add_argument("--run-id", default=None, help="optional run id under runs/")
    parser.add_argument("--print-path", action="store_true")
    args = parser.parse_args()
    dest = reset_case(args.case.upper(), args.run_id)
    if args.print_path:
        print(dest)
    else:
        print(f"reset {args.case} -> {dest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
