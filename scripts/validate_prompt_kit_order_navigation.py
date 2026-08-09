#!/usr/bin/env python3
"""Validate Prompt Kit chronological ordering and dense page-navigation contracts."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-order-navigation.v1.json"
OUTPUT_DEFAULT = ROOT / "Outputs" / "prompt-kit-order-navigation-audit.json"

REQUIRED_REQUIREMENT_IDS = {
    "default_sequence_ascending",
    "filtered_sequence_ascending",
    "distributed_page_navigation",
    "filter_persistent_navigation",
    "mobile_touch_accessibility",
    "stable_prompt_identity",
}


class OrderNavigationValidationError(RuntimeError):
    """Raised when the harness contract itself is malformed or disconnected."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise OrderNavigationValidationError(f"missing JSON file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise OrderNavigationValidationError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def validate_contract(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "prompt-kit-order-navigation-contract/v1":
        raise OrderNavigationValidationError("unsupported order/navigation contract schema")
    if payload.get("contract_id") != "prompt-kit-sequence-and-long-list-navigation":
        raise OrderNavigationValidationError("order/navigation contract ID drifted")
    if payload.get("navigation_interval") != 5:
        raise OrderNavigationValidationError("navigation_interval must remain exactly 5")

    surface = payload.get("surface")
    if not isinstance(surface, dict):
        raise OrderNavigationValidationError("surface must be an object")
    for field in (
        "canonical_site",
        "base_behavior_source",
        "guided_behavior_source",
        "registry_builder",
        "display_order_policy",
    ):
        value = surface.get(field)
        if not isinstance(value, str) or not value.strip():
            raise OrderNavigationValidationError(f"surface is missing {field}")
        if not (ROOT / value).is_file():
            raise OrderNavigationValidationError(f"surface path is missing: {value}")

    requirements = payload.get("requirements")
    if not isinstance(requirements, list):
        raise OrderNavigationValidationError("requirements must be an array")
    ids = [str(item.get("id", "")) for item in requirements if isinstance(item, dict)]
    if set(ids) != REQUIRED_REQUIREMENT_IDS or len(ids) != len(REQUIRED_REQUIREMENT_IDS):
        raise OrderNavigationValidationError(f"requirement IDs drifted: {ids}")
    for item in requirements:
        expected = item.get("expected")
        if not isinstance(expected, str) or not expected.strip():
            raise OrderNavigationValidationError(
                f"requirement {item.get('id')} has empty expected behavior"
            )

    detection = payload.get("implementation_detection")
    if not isinstance(detection, dict):
        raise OrderNavigationValidationError("implementation_detection must be an object")
    for field in ("forbidden_global_order_markers", "required_navigation_markers"):
        values = detection.get(field)
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            raise OrderNavigationValidationError(f"implementation_detection.{field} is invalid")
    sparse = detection.get("existing_sparse_navigation_marker")
    if not isinstance(sparse, str) or not sparse:
        raise OrderNavigationValidationError(
            "implementation_detection.existing_sparse_navigation_marker is invalid"
        )

    validation = payload.get("validation")
    if not isinstance(validation, dict):
        raise OrderNavigationValidationError("validation must be an object")
    for field in ("harness_gate", "contract_tests", "strict_product_gate", "generated_parity"):
        value = validation.get(field)
        if not isinstance(value, str) or not value.strip():
            raise OrderNavigationValidationError(f"validation is missing {field}")

    return payload


def _finding(rule_id: str, requirement_id: str, evidence: str) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "requirement_id": requirement_id,
        "severity": "product_gap",
        "evidence": evidence,
    }


def evaluate_source_payloads(
    contract: dict[str, Any],
    display_policy: dict[str, Any],
    builder_text: str,
    guided_text: str,
    base_text: str,
) -> dict[str, Any]:
    """Evaluate static implementation evidence without changing product code."""
    contract = validate_contract(contract)
    detection = contract["implementation_detection"]
    findings: list[dict[str, str]] = []

    combined_order_sources = {
        "registry_builder": builder_text,
        "guided_behavior_source": guided_text,
    }
    for marker in detection["forbidden_global_order_markers"]:
        for source_name, source_text in combined_order_sources.items():
            if marker in source_text:
                findings.append(
                    _finding(
                        "PKON001",
                        "default_sequence_ascending",
                        f"{source_name} contains global ordering marker: {marker}",
                    )
                )
                findings.append(
                    _finding(
                        "PKON002",
                        "filtered_sequence_ascending",
                        f"{source_name} can apply non-chronological rank to the visible library: {marker}",
                    )
                )

    promoted = display_policy.get("promoted_prompt_ids")
    if isinstance(promoted, list) and promoted and str(promoted[0]).upper() == "P65":
        findings.append(
            _finding(
                "PKON003",
                "default_sequence_ascending",
                "display-order policy promotes P65 first; this is acceptable only when it is not applied as the default library sort",
            )
        )

    missing_navigation = [
        marker for marker in detection["required_navigation_markers"] if marker not in base_text
    ]
    if missing_navigation:
        sparse_marker = detection["existing_sparse_navigation_marker"]
        sparse_note = (
            " Existing category-divider navigation is present."
            if sparse_marker in base_text
            else " Existing category-divider navigation marker was not found."
        )
        findings.append(
            _finding(
                "PKON004",
                "distributed_page_navigation",
                "missing distributed-navigation implementation markers: "
                + ", ".join(missing_navigation)
                + sparse_note,
            )
        )
        findings.append(
            _finding(
                "PKON005",
                "filter_persistent_navigation",
                "navigation is not proven to be regenerated by visible-prompt position after each filtered render",
            )
        )

    if "min-height:40px" not in base_text or "page-jump" not in base_text:
        findings.append(
            _finding(
                "PKON006",
                "mobile_touch_accessibility",
                "40px touch-target and page-jump evidence is incomplete",
            )
        )

    requirement_status = {requirement_id: "pass" for requirement_id in REQUIRED_REQUIREMENT_IDS}
    for finding in findings:
        requirement_status[finding["requirement_id"]] = "gap"

    return {
        "schema_version": "prompt-kit-order-navigation-audit/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_id": contract["contract_id"],
        "navigation_interval": contract["navigation_interval"],
        "implementation_status": "pass" if not findings else "needs-product-repair",
        "requirement_status": requirement_status,
        "findings": findings,
        "proof_ceiling": contract["proof_ceiling"],
    }


def evaluate_repository(contract_path: Path = CONTRACT) -> dict[str, Any]:
    contract = validate_contract(load_json(contract_path))
    surface = contract["surface"]
    return evaluate_source_payloads(
        contract,
        load_json(ROOT / surface["display_order_policy"]),
        (ROOT / surface["registry_builder"]).read_text(encoding="utf-8"),
        (ROOT / surface["guided_behavior_source"]).read_text(encoding="utf-8"),
        (ROOT / surface["base_behavior_source"]).read_text(encoding="utf-8"),
    )


def write_report(report: dict[str, Any], output: Path) -> None:
    output = output.expanduser().resolve()
    for protected in (ROOT / "Candidates", ROOT / "Active"):
        try:
            output.relative_to(protected.resolve())
        except ValueError:
            continue
        raise OrderNavigationValidationError(f"refusing protected output path: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument(
        "--require-implementation",
        action="store_true",
        help="Fail while any ordering or distributed-navigation product gap remains.",
    )
    args = parser.parse_args(argv)

    try:
        report = evaluate_repository(args.contract)
        write_report(report, args.output)
    except OrderNavigationValidationError as exc:
        print(f"Prompt Kit order/navigation validation failed: {exc}", file=sys.stderr)
        return 2

    if args.summary:
        print(
            "Prompt Kit order/navigation audit "
            f"{report['implementation_status']}: interval={report['navigation_interval']} "
            f"findings={len(report['findings'])} output={args.output}"
        )
    else:
        print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_implementation and report["findings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
