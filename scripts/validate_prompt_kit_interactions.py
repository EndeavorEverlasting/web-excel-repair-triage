#!/usr/bin/env python3
"""Validate the Prompt Kit interaction contract and audit recognizable JS markers.

Default mode validates the harness contract and reports current implementation status.
Use --require-implementation only in the Prompt Kit product lane, where every required
interaction must be recognizable in the canonical behavior source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-interactions.v1.json"
PROTECTED_OUTPUT_ROOTS = (ROOT / "Candidates", ROOT / "Active")
REQUIRED_REQUIREMENT_IDS = {
    "single_click_copy",
    "double_click_expand",
    "outside_click_collapse_restore",
    "escape_close_preserved",
    "copy_button_compatibility",
}


class InteractionContractError(RuntimeError):
    """Raised when the tracked interaction harness is incomplete or inconsistent."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InteractionContractError(f"missing interaction contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InteractionContractError(f"invalid interaction contract JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise InteractionContractError("interaction contract must be a JSON object")
    return payload


def validate_contract() -> dict[str, Any]:
    payload = _load_json(CONTRACT_PATH)
    if payload.get("schema_version") != "prompt-kit-interaction-contract/v1":
        raise InteractionContractError("unsupported interaction contract schema")
    if payload.get("contract_id") != "prompt-kit-card-interactions":
        raise InteractionContractError("unexpected interaction contract ID")
    if payload.get("status") not in {"specified_unimplemented", "implemented"}:
        raise InteractionContractError("interaction contract status is invalid")

    surface = payload.get("surface")
    if not isinstance(surface, dict):
        raise InteractionContractError("surface contract must be an object")
    for key in (
        "canonical_site",
        "canonical_behavior_source",
        "canonical_renderer",
        "combined_builder",
        "main_results_surface",
    ):
        value = surface.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InteractionContractError(f"surface contract is missing {key}")
    for key in ("canonical_site", "canonical_behavior_source", "canonical_renderer", "combined_builder"):
        path = ROOT / str(surface[key])
        if not path.is_file():
            raise InteractionContractError(f"registered interaction surface is missing: {surface[key]}")

    owner = payload.get("owner")
    if not isinstance(owner, dict):
        raise InteractionContractError("owner contract must be an object")
    if owner.get("workflow") != "WORKFLOW.md#b-prompt-registry-or-website-change":
        raise InteractionContractError("interaction workflow owner drifted")
    if owner.get("implementation_lane") != "Prompt Kit product behavior":
        raise InteractionContractError("product implementation lane drifted")
    forbidden = owner.get("forbidden_in_harness_lane")
    if not isinstance(forbidden, list) or not forbidden:
        raise InteractionContractError("harness lane must declare forbidden product mutations")

    requirements = payload.get("requirements")
    if not isinstance(requirements, list):
        raise InteractionContractError("requirements must be a list")
    ids = [str(item.get("id", "")) for item in requirements if isinstance(item, dict)]
    if set(ids) != REQUIRED_REQUIREMENT_IDS or len(ids) != len(REQUIRED_REQUIREMENT_IDS):
        raise InteractionContractError(f"interaction requirement IDs drifted: {ids}")
    for item in requirements:
        if not isinstance(item, dict):
            raise InteractionContractError("every interaction requirement must be an object")
        for key in ("event", "expected", "forbidden"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise InteractionContractError(f"{item.get('id')} is missing {key}")

    validation = payload.get("validation")
    if not isinstance(validation, dict):
        raise InteractionContractError("validation contract must be an object")
    for key in (
        "harness_command",
        "implementation_gate",
        "contract_tests",
        "exact_site_parity",
        "browser_field_gate",
    ):
        value = validation.get(key)
        if not isinstance(value, str) or not value.strip():
            raise InteractionContractError(f"validation contract is missing {key}")
    if "--require-implementation" not in validation["implementation_gate"]:
        raise InteractionContractError("strict implementation gate must be explicit")

    artifact = payload.get("artifact")
    if not isinstance(artifact, dict):
        raise InteractionContractError("artifact contract must be an object")
    if artifact.get("schema_version") != "prompt-kit-interaction-audit-result/v1":
        raise InteractionContractError("interaction audit result schema drifted")
    if artifact.get("default_path") != "Outputs/prompt-kit-interaction-audit.json":
        raise InteractionContractError("interaction audit default path drifted")

    proof_ceiling = payload.get("proof_ceiling")
    if not isinstance(proof_ceiling, str) or "does not prove" not in proof_ceiling.lower():
        raise InteractionContractError("proof ceiling must distinguish static and browser proof")
    return payload


def _assigned_handler(js: str, assignment: str) -> str:
    pattern = re.escape(assignment) + r"\s*=\s*function\s*\([^)]*\)\s*\{([^}]*)\}"
    match = re.search(pattern, js, flags=re.DOTALL)
    return match.group(1) if match else ""


def _event_listener_body(js: str, element_id: str, event_name: str) -> str:
    pattern = (
        r"getElementById\(['\"]"
        + re.escape(element_id)
        + r"['\"]\)\.addEventListener\(['\"]"
        + re.escape(event_name)
        + r"['\"]\s*,\s*function\s*\([^)]*\)\s*\{([^}]*)\}"
    )
    match = re.search(pattern, js, flags=re.DOTALL)
    return match.group(1) if match else ""


def evaluate_source(js: str) -> dict[str, bool]:
    """Return conservative static evidence for each required interaction."""
    click_body = _assigned_handler(js, "card.onclick")
    dblclick_body = _assigned_handler(js, "card.ondblclick")
    if not dblclick_body:
        dbl_match = re.search(
            r"(?:prompt-card|card).*?addEventListener\(['\"]dblclick['\"].*?showPromptDetail",
            js,
            flags=re.DOTALL,
        )
        dblclick_body = "showPromptDetail" if dbl_match else ""

    overlay_body = _event_listener_body(js, "promptDetailOverlay", "click")
    if not overlay_body:
        overlay_match = re.search(
            r"promptDetailOverlay.*?addEventListener\(['\"]click['\"].*?closePromptDetail.*?(?:\.focus\(|focusPrompt|restorePrompt)",
            js,
            flags=re.DOTALL,
        )
        overlay_body = "closePromptDetail focus" if overlay_match else ""

    escape_match = re.search(
        r"case\s*['\"]Escape['\"].*?promptDetailOverlay.*?closePromptDetail\(\)",
        js,
        flags=re.DOTALL,
    )
    button_body = _assigned_handler(js, "btn.onclick")

    return {
        "single_click_copy": bool(click_body and "copyPrompt(" in click_body and "showPromptDetail(" not in click_body),
        "double_click_expand": bool(dblclick_body and "showPromptDetail" in dblclick_body),
        "outside_click_collapse_restore": bool(
            overlay_body
            and "closePromptDetail" in overlay_body
            and (".focus(" in overlay_body or "focusPrompt" in overlay_body or "restorePrompt" in overlay_body or " focus" in overlay_body)
        ),
        "escape_close_preserved": bool(escape_match),
        "copy_button_compatibility": bool(button_body and "copyPrompt(" in button_body and "stopPropagation" in button_body),
    }


def audit_implementation(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or validate_contract()
    behavior_path = ROOT / contract["surface"]["canonical_behavior_source"]
    js = behavior_path.read_text(encoding="utf-8")
    checks = evaluate_source(js)
    requirement_results = [
        {
            "id": requirement["id"],
            "static_marker_observed": checks[requirement["id"]],
            "event": requirement["event"],
        }
        for requirement in contract["requirements"]
    ]
    return {
        "schema_version": contract["artifact"]["schema_version"],
        "contract_id": contract["contract_id"],
        "contract_status": contract["status"],
        "behavior_source": contract["surface"]["canonical_behavior_source"],
        "implementation_ready": all(checks.values()),
        "requirements": requirement_results,
        "missing_static_markers": [key for key, passed in checks.items() if not passed],
        "proof_ceiling": contract["proof_ceiling"],
    }


def validate_output_path(output: Path) -> Path:
    resolved = output.expanduser().resolve()
    for protected in PROTECTED_OUTPUT_ROOTS:
        try:
            resolved.relative_to(protected.resolve())
        except ValueError:
            continue
        raise InteractionContractError(f"refusing to write interaction audit inside protected input: {protected}")
    return resolved


def _write_report(report: dict[str, Any], output: Path) -> None:
    resolved = validate_output_path(output)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON audit output path")
    parser.add_argument("--summary", action="store_true", help="Print a concise status summary")
    parser.add_argument(
        "--require-implementation",
        action="store_true",
        help="Fail unless every required interaction has recognizable static implementation evidence",
    )
    args = parser.parse_args(argv)

    try:
        contract = validate_contract()
        report = audit_implementation(contract)
        if args.output:
            _write_report(report, args.output)
    except (InteractionContractError, OSError) as exc:
        print(f"[FAIL] Prompt Kit interaction harness: {exc}", file=sys.stderr)
        return 1

    if args.summary:
        state = "IMPLEMENTATION MARKERS COMPLETE" if report["implementation_ready"] else "HARNESS COMPLETE; PRODUCT GAP DETECTED"
        print(f"Prompt Kit interaction contract: {state}")
        if report["missing_static_markers"]:
            print("Missing static markers: " + ", ".join(report["missing_static_markers"]))
        if args.output:
            print(f"Report: {validate_output_path(args.output)}")

    if args.require_implementation and not report["implementation_ready"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
