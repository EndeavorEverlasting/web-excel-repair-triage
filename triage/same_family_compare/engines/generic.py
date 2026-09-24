"""Fallback fingerprint compare for nw_prj_hours, neuron_track_hours, web_excel_opened_copy."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.artifact_fingerprint import fingerprint_file, raw_sha256


def compare_fingerprint_pair(baseline: Path, candidate: Path) -> Dict[str, Any]:
    try:
        fb = fingerprint_file(str(baseline))
        fc = fingerprint_file(str(candidate))
    except Exception as exc:
        return {"pass": False, "error": f"parse_failed: {exc}", "delta_rows": []}
    raw_match = raw_sha256(str(baseline)) == raw_sha256(str(candidate))
    sem_match = fb.get("semantic_sha256") == fc.get("semantic_sha256")
    delta_rows: List[Dict[str, Any]] = []
    if not sem_match:
        delta_rows.append({
            "kind": "semantic_sha256_mismatch",
            "baseline": fb.get("semantic_sha256"),
            "candidate": fc.get("semantic_sha256"),
        })
    return {
        "pass": sem_match,
        "raw_match": raw_match,
        "baseline": fb,
        "candidate": fc,
        "delta_rows": delta_rows,
    }
