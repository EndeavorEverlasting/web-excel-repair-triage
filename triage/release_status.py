"""Compute release_candidate and release_blockers for artifact manifests."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def compute_release_status(
    *,
    delivery_artifact: bool,
    websafe_preflight_pass: Optional[bool],
    semantic_integrity: str,
    excel_for_web_manual_check: str,
    artifact_compare_status: str,
    artifact_compare_pass: Optional[bool],
    extra_blockers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Return release_candidate bool and human-readable release_blockers list."""
    blockers: List[str] = list(extra_blockers or [])

    if websafe_preflight_pass is False:
        blockers.append("websafe_preflight_failed")
    if semantic_integrity != "PASS":
        blockers.append(f"semantic_integrity:{semantic_integrity}")

    if artifact_compare_status == "FAIL":
        blockers.append("artifact_compare_failed")
    elif artifact_compare_status == "NOT_RUN":
        if delivery_artifact:
            blockers.append("artifact_compare_not_run")

    if delivery_artifact:
        if excel_for_web_manual_check != "PROVEN":
            blockers.append(
                f"excel_for_web_manual_check:{excel_for_web_manual_check or 'NOT_PROVEN'}"
            )
    elif excel_for_web_manual_check == "FAILED":
        blockers.append("excel_for_web_manual_check:FAILED")

    if artifact_compare_pass is False:
        blockers.append("artifact_compare_pass:false")

    release_candidate = len(blockers) == 0
    return {
        "release_candidate": release_candidate,
        "release_blockers": blockers,
    }


def enrich_variant_output(
    variant_out: Dict[str, Any],
    *,
    delivery_artifact: bool,
    variant: str,
    reference_supplied: bool,
) -> Dict[str, Any]:
    """Add release fields and explicit compare status to a per-variant output dict."""
    preflight_pass = variant_out.get("websafe_preflight_pass")
    semantic = variant_out.get("semantic_integrity", "FAIL")
    excel_web = variant_out.get("excel_for_web_manual_check", "NOT_PROVEN")
    cmp_pass = variant_out.get("artifact_compare_pass")
    cmp_json = variant_out.get("artifact_compare_json")

    if cmp_json:
        if cmp_pass is True:
            cmp_status = "PASS"
        elif cmp_pass is False:
            cmp_status = "FAIL"
        else:
            cmp_status = "NOT_RUN"
    elif reference_supplied:
        cmp_status = "FAIL"
        variant_out.setdefault("artifact_compare_reason", "compare not executed")
    else:
        cmp_status = "NOT_RUN"
        variant_out["artifact_compare_reason"] = (
            f"no {variant} reference supplied"
        )

    variant_out["artifact_compare_status"] = cmp_status
    release = compute_release_status(
        delivery_artifact=delivery_artifact,
        websafe_preflight_pass=preflight_pass,
        semantic_integrity=semantic,
        excel_for_web_manual_check=excel_web,
        artifact_compare_status=cmp_status,
        artifact_compare_pass=cmp_pass,
    )
    variant_out.update(release)
    return variant_out
