"""admin_billing_summary same-family compare."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.artifact_compare import compare_artifacts
from triage.artifact_fingerprint import fingerprint_file


def compare_admin_billing(
    baseline: Path,
    candidate: Path,
    *,
    profile: str = "admin_billing_summary",
    expect_neuron_tab: str | None = None,
) -> Dict[str, Any]:
    try:
        fp_b = fingerprint_file(str(baseline))
        fp_c = fingerprint_file(str(candidate))
    except Exception as exc:
        return {
            "pass": False,
            "error": f"baseline_parse_failed: {exc}",
            "delta_rows": [],
        }
    cmp = compare_artifacts(
        reference=str(baseline),
        candidate=str(candidate),
        profile=profile,
        expect_neuron_tab=expect_neuron_tab,
    )
    delta_rows: List[Dict[str, Any]] = []
    if not cmp.get("compare_pass"):
        delta_rows.append({
            "kind": "semantic_or_profile",
            "detail": cmp.get("failures") or cmp.get("semantic_compare"),
        })
    return {
        "pass": bool(cmp.get("compare_pass")),
        "compare": cmp,
        "baseline_semantic_sha256": fp_b.get("semantic_sha256"),
        "candidate_semantic_sha256": fp_c.get("semantic_sha256"),
        "delta_rows": delta_rows,
    }
