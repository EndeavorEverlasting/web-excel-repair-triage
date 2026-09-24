"""triage/excel_desktop_worker.py
--------------------------------
Worker process for Desktop Excel probe.

Why
---
Excel/COM can hang (especially during server startup) in ways that bypass in-process
watchdogs. The supervisor (`probe_open_in_desktop_excel_isolated`) runs this worker
in a subprocess so it can enforce a hard wall-clock timeout and still retain
artifacts (stdout/stderr + recovery XML).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from triage.excel_desktop import ExcelDesktopProbeResult, probe_open_in_desktop_excel


def _atomic_write_json(path: Path, payload: dict) -> None:
    """Best-effort atomic JSON write (write temp + replace) so supervisor can read partial results."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Desktop Excel probe worker")
    ap.add_argument("--file", required=True, help="Path to candidate .xlsx")
    ap.add_argument("--out-dir", required=True, help="Exact output directory to write into")
    ap.add_argument("--result-json", required=True, help="Where to write JSON result payload")

    ap.add_argument("--timeout", type=int, default=15)

    ap.add_argument("--no-visible", action="store_true")
    ap.add_argument("--no-repair", action="store_true")
    ap.add_argument("--no-save-repaired", action="store_true")
    ap.add_argument("--no-alerts", action="store_true")
    ap.add_argument("--no-force-kill-timeout", action="store_true")
    ap.add_argument("--no-force-kill-exit", action="store_true")
    ap.add_argument("--search-log-dir", action="append", default=[])

    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result_path = Path(args.result_json)

    # Write an initial/heartbeat result immediately so the supervisor has *something*
    # to read even if the worker is force-killed later.
    try:
        heartbeat = ExcelDesktopProbeResult(candidate_path=args.file, out_dir=str(out_dir))
        heartbeat.exception = "worker_started"
        _atomic_write_json(result_path, heartbeat.to_dict())
    except Exception:
        pass

    try:
        r = probe_open_in_desktop_excel(
            candidate_path=args.file,
            out_root=str(out_dir.parent),
            out_dir_override=str(out_dir),
            visible=not args.no_visible,
            try_repair=not args.no_repair,
            save_repaired_copy=not args.no_save_repaired,
            timeout_seconds=int(args.timeout),
            display_alerts=not args.no_alerts,
            search_log_dirs=list(args.search_log_dir) or None,
            force_kill_on_timeout=not args.no_force_kill_timeout,
            force_kill_on_exit=not args.no_force_kill_exit,
        )
        try:
            _atomic_write_json(result_path, r.to_dict())
        except Exception:
            pass
        return 0 if r.opened and not r.fatal else 2
    except Exception as e:
        try:
            fail = ExcelDesktopProbeResult(candidate_path=args.file, out_dir=str(out_dir))
            fail.opened = False
            fail.fatal = True
            fail.exception = f"worker_exception: {type(e).__name__}: {e}"
            _atomic_write_json(result_path, fail.to_dict())
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

