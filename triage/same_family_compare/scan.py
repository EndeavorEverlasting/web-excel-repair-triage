"""Phase 1: intake inventory scanner (read-only)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from triage.same_family_compare.classify import classify_file
from triage.same_family_compare.models import sha256_file


def scan_intake(intake_root: Path) -> Dict[str, Any]:
    if not intake_root.is_dir():
        raise FileNotFoundError(f"Intake root not found: {intake_root}")

    artifacts: List[Dict[str, Any]] = []
    unknown: List[str] = []
    by_family: Dict[str, List[str]] = {}

    for path in sorted(intake_root.rglob("*.xlsx")):
        if path.name.startswith("~$"):
            continue
        meta = classify_file(path)
        d = meta.to_dict()
        try:
            d["output_sha256"] = sha256_file(path)
        except OSError:
            d["output_sha256"] = None
        artifacts.append(d)
        fam = meta.artifact_family
        if fam == "unknown":
            unknown.append(str(path))
        by_family.setdefault(fam, []).append(str(path))

    return {
        "intake_root": str(intake_root.resolve()),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "unknown_artifacts": unknown,
        "family_grouping": {k: len(v) for k, v in by_family.items()},
        "family_paths": by_family,
    }


def write_scan_outputs(scan: Dict[str, Any], out_dir: Path) -> Dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name in ("artifact_inventory.json", "unknown_artifacts.json", "family_grouping_summary.json"):
        if name == "unknown_artifacts.json":
            payload = {"unknown": scan.get("unknown_artifacts", [])}
        elif name == "family_grouping_summary.json":
            payload = {
                "family_grouping": scan.get("family_grouping"),
                "family_paths": scan.get("family_paths"),
            }
        else:
            payload = scan
        p = out_dir / name
        p.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        paths[name] = p
    return paths
