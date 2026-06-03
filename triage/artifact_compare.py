"""Compare generated .xlsx artifacts to approved reference fingerprints.

Not to be confused with ``triage.nw_prj_artifact_compare`` (dashboard row reconciliation).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional

from triage.admin_billing_summary.preflight import preflight_billing_summary
from triage.artifact_fingerprint import fingerprint_file
from triage.artifact_profiles import (
    gate_profile_for,
    load_profile,
    run_profile_checks,
)
from triage.webexcel_semantic_gate import run_semantic_gate

try:
    from triage.nw_prj_neuron_track_hours.bonita_cli import preflight_bonita
except ImportError:
    preflight_bonita = None  # type: ignore


def _load_approved_delta(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _delta_allows_semantic(candidate_semantic: str, delta: Dict[str, Any]) -> bool:
    allowed = delta.get("allow_candidate_semantic_sha256")
    if allowed and candidate_semantic == allowed:
        return True
    allowlist = delta.get("semantic_sha256_allowlist") or []
    return candidate_semantic in allowlist


def _package_preflight_status(
    path: str,
    profile_name: str,
    *,
    variant: str = "client",
    expect_neuron_tab: Optional[str] = None,
) -> Dict[str, Any]:
    if profile_name == "admin_billing_summary" and expect_neuron_tab:
        return preflight_billing_summary(
            path, variant=variant, expect_neuron_tab=expect_neuron_tab
        )
    if profile_name == "bonita_neuron_track_hours" and preflight_bonita:
        return preflight_bonita(path)
    gate = run_semantic_gate(path, profile=gate_profile_for(profile_name))
    return {
        "preflight_pass": gate.get("semantic_integrity") == "PASS",
        "semantic_integrity": gate.get("semantic_integrity"),
    }


def compare_artifacts(
    reference: str,
    candidate: str,
    profile: str,
    *,
    approved_delta: Optional[str] = None,
    expect_neuron_tab: Optional[str] = None,
    variant: str = "client",
) -> Dict[str, Any]:
    """Fingerprint reference vs candidate and apply profile stop-ship rules."""
    prof = load_profile(profile)
    delta = _load_approved_delta(approved_delta)

    ref_fp = fingerprint_file(reference)
    cand_fp = fingerprint_file(candidate)

    ref_checks = run_profile_checks(
        reference, prof, expect_neuron_tab=expect_neuron_tab
    )
    cand_checks = run_profile_checks(
        candidate,
        prof,
        expect_neuron_tab=expect_neuron_tab,
        reference_totals=ref_checks.totals if prof.compare_totals else None,
    )

    preflight = _package_preflight_status(
        candidate,
        profile,
        variant=variant or (prof.variant or "client"),
        expect_neuron_tab=expect_neuron_tab,
    )
    semantic_integrity = preflight.get("semantic_integrity", "FAIL")
    package_preflight = "PASS" if preflight.get("preflight_pass") else "FAIL"

    raw_match = ref_fp.raw_sha256 == cand_fp.raw_sha256
    canonical_match = ref_fp.canonical_package_sha256 == cand_fp.canonical_package_sha256
    semantic_match = ref_fp.semantic_sha256 == cand_fp.semantic_sha256

    profile_failures = list(cand_checks.failures)
    profile_warnings: list[str] = list(cand_checks.warnings)

    if not raw_match:
        profile_warnings.append("raw_sha256_mismatch")
    if not canonical_match:
        msg = "canonical_package_sha256_mismatch"
        if prof.fail_on_canonical_mismatch:
            profile_failures.append(msg)
        else:
            profile_warnings.append(msg)

    semantic_compare = "PASS"
    if not semantic_match:
        if _delta_allows_semantic(cand_fp.semantic_sha256, delta):
            profile_warnings.append("semantic_sha256_mismatch_approved_delta")
        else:
            semantic_compare = "FAIL"
            profile_failures.append(
                f"semantic_sha256_mismatch:"
                f"ref={ref_fp.semantic_sha256[:12]}..."
                f"cand={cand_fp.semantic_sha256[:12]}..."
            )

    compare_pass = (
        package_preflight == "PASS"
        and semantic_integrity == "PASS"
        and semantic_compare == "PASS"
        and not profile_failures
    )

    return {
        "profile": profile,
        "reference": str(Path(reference).resolve()),
        "candidate": str(Path(candidate).resolve()),
        "package_preflight": package_preflight,
        "semantic_integrity": semantic_integrity,
        "semantic_compare": semantic_compare,
        "raw_sha_match": raw_match,
        "canonical_package_match": canonical_match,
        "semantic_sha_match": semantic_match,
        "excel_for_web_manual_check": preflight.get(
            "excel_for_web_manual_check", "NOT_PROVEN"
        ),
        "profile_failures": profile_failures,
        "profile_warnings": profile_warnings,
        "compare_pass": compare_pass,
        "approved_delta_applied": bool(delta) and not semantic_match,
        "fingerprints": {
            "reference": ref_fp.to_dict(),
            "candidate": cand_fp.to_dict(),
        },
        "totals": {
            "reference": ref_checks.totals,
            "candidate": cand_checks.totals,
        },
    }


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="triage.artifact_compare",
        description="Compare candidate workbook to approved reference fingerprint.",
    )
    ap.add_argument("--reference", required=True, help="Approved reference .xlsx")
    ap.add_argument("--candidate", required=True, help="Generated candidate .xlsx")
    ap.add_argument("--profile", required=True, help="Profile name under configs/artifact_profiles/")
    ap.add_argument("--out", help="Write compare JSON to this path")
    ap.add_argument("--approved-delta", help="JSON file allowing semantic hash drift")
    ap.add_argument("--expect-neuron-tab", help="Resolve {{expect_neuron_tab}} in profile")
    ap.add_argument("--variant", default="client", choices=("internal", "client"))
    args = ap.parse_args(argv)

    report = compare_artifacts(
        args.reference,
        args.candidate,
        args.profile,
        approved_delta=args.approved_delta,
        expect_neuron_tab=args.expect_neuron_tab,
        variant=args.variant,
    )
    text = json.dumps(report, indent=2, default=str)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.get("compare_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
