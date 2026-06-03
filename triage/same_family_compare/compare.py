"""Phase 3: same-family comparison orchestrator."""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.same_family_compare.classify import classify_file
from triage.same_family_compare.engines.admin_billing import compare_admin_billing
from triage.same_family_compare.engines.generic import compare_fingerprint_pair
from triage.same_family_compare.engines.roster_log import compare_roster_logs
from triage.same_family_compare.models import ArtifactMetadata, sha256_file


class CompareError(Exception):
    pass


def _validate_pair(
    base_meta: ArtifactMetadata,
    cand_meta: ArtifactMetadata,
    months: Optional[List[str]],
) -> List[str]:
    problems: List[str] = []
    problems.extend(base_meta.required_for_compare())
    problems.extend(cand_meta.required_for_compare())
    if base_meta.artifact_family != cand_meta.artifact_family:
        problems.append("artifact_family_mismatch")
    if months:
        bs = set(base_meta.month_set)
        cs = set(cand_meta.month_set)
        if bs and cs and not set(months).issubset(bs | cs):
            problems.append("month_set_not_covered")
    if base_meta.audience != cand_meta.audience and "internal" not in (
        base_meta.audience, cand_meta.audience,
    ):
        problems.append("audience_mismatch_restricted_compare")
    return problems


def run_same_family_compare(
    baseline: Path,
    candidate: Path,
    *,
    family: Optional[str] = None,
    months: Optional[List[str]] = None,
    expect_neuron_tab: Optional[str] = None,
    source_baseline_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    if not baseline.is_file():
        raise CompareError(f"Baseline not found or unreadable: {baseline}")
    if not candidate.is_file():
        raise CompareError(f"Candidate not found or unreadable: {candidate}")

    base_meta = classify_file(baseline)
    cand_meta = classify_file(candidate)
    base_meta.comparison_baseline = True
    if family:
        base_meta.artifact_family = family
        cand_meta.artifact_family = family
    if months:
        base_meta.month_set = months
        cand_meta.month_set = months
    try:
        base_meta.output_sha256 = sha256_file(baseline)
        cand_meta.output_sha256 = sha256_file(candidate)
    except OSError:
        pass

    problems = _validate_pair(base_meta, cand_meta, months)
    if problems:
        return {
            "pass": False,
            "verdict": "INSUFFICIENT_METADATA",
            "problems": problems,
            "baseline": base_meta.to_dict(),
            "candidate": cand_meta.to_dict(),
            "delta_rows": [],
        }

    source_drifted = False
    if source_baseline_sha256 and cand_meta.source_workbook_sha256:
        source_drifted = source_baseline_sha256 != cand_meta.source_workbook_sha256

    fam = base_meta.artifact_family
    if fam == "admin_billing_summary":
        engine_result = compare_admin_billing(
            baseline, candidate, expect_neuron_tab=expect_neuron_tab,
        )
    elif fam == "active_roster_log":
        engine_result = compare_roster_logs(baseline, candidate)
    elif fam in ("nw_prj_hours", "neuron_track_hours", "web_excel_opened_copy"):
        engine_result = compare_fingerprint_pair(baseline, candidate)
    else:
        raise CompareError(f"Unsupported artifact family: {fam}")

    if engine_result.get("error"):
        raise CompareError(engine_result["error"])

    passed = bool(engine_result.get("pass")) and not source_drifted
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "pass": passed,
        "artifact_family": fam,
        "baseline": base_meta.to_dict(),
        "candidate": cand_meta.to_dict(),
        "source_drifted": source_drifted,
        "engine_result": engine_result,
        "delta_rows": engine_result.get("delta_rows") or [],
    }


def write_compare_outputs(result: Dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "same_family_comparison.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8",
    )
    md_lines = [
        "# Same-family comparison",
        "",
        f"- **Pass:** {result.get('pass')}",
        f"- **Family:** {result.get('artifact_family')}",
        f"- **Verdict:** {result.get('verdict', 'COMPARED')}",
        "",
    ]
    if result.get("problems"):
        md_lines.append("## Problems")
        for p in result["problems"]:
            md_lines.append(f"- {p}")
    if result.get("source_drifted"):
        md_lines.append("- **Source drifted:** yes")
    (out_dir / "same_family_comparison.md").write_text("\n".join(md_lines), encoding="utf-8")

    rows = result.get("delta_rows") or []
    with (out_dir / "same_family_delta_rows.csv").open("w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        else:
            f.write("kind,detail\n")
