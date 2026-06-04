"""Record manual Excel for Web browser proof (never auto-PROVEN from generation)."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_ALLOWED = frozenset({"NOT_PROVEN", "PROVEN", "FAILED"})


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def record_workbook_proof(
    *,
    out_dir: str,
    workbook: str,
    status: str,
    checked_by: str,
    notes: str = "",
    repair_prompt_seen: bool = False,
    meaningful_headers_visible: bool = True,
    key_tabs_visible: bool = True,
    checked_at: Optional[str] = None,
    preflight_json: Optional[str] = None,
    artifact_compare_json: Optional[str] = None,
) -> Dict[str, Any]:
    """Append/update manual proof sidecar and optional preflight/compare JSON."""
    if status not in _ALLOWED:
        raise ValueError(f"status must be one of {_ALLOWED}, got {status!r}")
    if status == "PROVEN" and repair_prompt_seen:
        raise ValueError("cannot mark PROVEN when repair_prompt_seen is true")

    out = Path(out_dir)
    wb_path = Path(workbook)
    if not wb_path.is_file():
        raise FileNotFoundError(workbook)

    ts = checked_at or datetime.now(timezone.utc).isoformat()
    entry = {
        "path": str(wb_path.resolve()),
        "name": wb_path.name,
        "opened_in_excel_for_web": status in ("PROVEN", "FAILED"),
        "repair_prompt_seen": repair_prompt_seen,
        "meaningful_headers_visible": meaningful_headers_visible,
        "key_tabs_visible": key_tabs_visible,
        "checked_utc": ts,
        "checked_by": checked_by,
        "notes": notes,
        "excel_for_web_manual_check": status,
    }

    sidecar_path = out / "manual_web_excel_check.json"
    sidecar = _load_json(sidecar_path)
    workbooks: List[Dict[str, Any]] = list(sidecar.get("workbooks") or [])
    workbooks = [w for w in workbooks if w.get("name") != wb_path.name]
    workbooks.append(entry)
    sidecar["workbooks"] = workbooks
    sidecar["updated_utc"] = ts
    _save_json(sidecar_path, sidecar)

    if preflight_json:
        pf = _load_json(Path(preflight_json))
        pf["excel_for_web_manual_check"] = status
        pf["excel_for_web_checked_by"] = checked_by
        pf["excel_for_web_checked_at"] = ts
        pf["excel_for_web_notes"] = notes
        pf["excel_for_web_repair_prompt_seen"] = repair_prompt_seen
        _save_json(Path(preflight_json), pf)

    if artifact_compare_json:
        cmp = _load_json(Path(artifact_compare_json))
        cmp["excel_for_web_manual_check"] = status
        _save_json(Path(artifact_compare_json), cmp)

    return {"sidecar": str(sidecar_path), "entry": entry}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.record_excel_for_web_manual")
    ap.add_argument("--out-dir", required=True, help="Run output folder")
    ap.add_argument("--workbook", required=True, help="Workbook path that was checked")
    ap.add_argument("--status", required=True, choices=sorted(_ALLOWED))
    ap.add_argument("--checked-by", required=True)
    ap.add_argument("--notes", default="")
    ap.add_argument("--repair-prompt-seen", action="store_true")
    ap.add_argument("--preflight-json")
    ap.add_argument("--artifact-compare-json")
    ap.add_argument("--checked-at")
    args = ap.parse_args(argv)

    result = record_workbook_proof(
        out_dir=args.out_dir,
        workbook=args.workbook,
        status=args.status,
        checked_by=args.checked_by,
        notes=args.notes,
        repair_prompt_seen=args.repair_prompt_seen,
        preflight_json=args.preflight_json,
        artifact_compare_json=args.artifact_compare_json,
        checked_at=args.checked_at,
    )
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
