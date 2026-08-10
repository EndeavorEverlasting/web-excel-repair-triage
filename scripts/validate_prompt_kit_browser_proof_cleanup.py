#!/usr/bin/env python3
"""Validate the Prompt Kit browser-proof scratch cleanup harness."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "harness" / "browser-proof-cleanup"
MANIFEST = DOMAIN / "manifest.v1.json"

REQUIRED_COMPONENT_KEYS = {
    "codebase_map",
    "workflow",
    "artifact_registry_human",
    "artifact_registry_machine",
    "validator_registry",
    "trigger_registry",
    "cleanup_runner",
    "completeness_validator",
    "contract_tests",
    "pre_commit_hook",
    "pre_push_hook",
    "skill",
    "operator_report",
    "ci",
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON: {path.relative_to(ROOT)}: {exc}") from exc


def validate() -> list[str]:
    errors: list[str] = []
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != "prompt-kit-browser-proof-cleanup-harness/v1":
        errors.append("manifest schema_version is unsupported")

    components = manifest.get("components")
    if not isinstance(components, dict):
        errors.append("manifest components must be an object")
        components = {}
    missing_keys = sorted(REQUIRED_COMPONENT_KEYS - set(components))
    if missing_keys:
        errors.append(f"manifest missing component keys: {missing_keys}")

    for key, rel in components.items():
        if not isinstance(rel, str) or not rel.strip():
            errors.append(f"component {key} must be a non-empty path")
            continue
        if not (ROOT / rel).is_file():
            errors.append(f"component {key} is missing: {rel}")

    contract = manifest.get("scratch_contract", {})
    expected = {
        "system_temp_only": True,
        "directory_name_regex": r"^prompt-kit-browser-proof-[0-9a-fA-F]{16,64}$",
        "required_marker": "web/prompt-kit/index.html",
        "reject_reparse_points": True,
        "preview_is_default": True,
        "apply_requires_explicit_switch": True,
        "browser_profile_data_out_of_scope": True,
        "favorites_local_storage_out_of_scope": True,
        "retain_previous_report_before_overwrite": True,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            errors.append(f"scratch contract mismatch: {key}")
    try:
        re.compile(str(contract.get("directory_name_regex", "")))
    except re.error as exc:
        errors.append(f"invalid directory_name_regex: {exc}")

    cleanup_path = ROOT / str(components.get("cleanup_runner", ""))
    if cleanup_path.is_file():
        text = cleanup_path.read_text(encoding="utf-8")
        required_markers = [
            "[CmdletBinding(SupportsShouldProcess = $true)]",
            "[switch]$Apply",
            "$MinimumAgeMinutes = 60",
            "$SystemTemp",
            "$LeafPattern",
            "ReparsePoint",
            "$RequiredMarkerRelative",
            "web\\prompt-kit\\index.html",
            "Remove-Item -LiteralPath $record.path -Recurse -Force",
            "prompt-kit-browser-proof-cleanup-report.json",
            "browser localStorage and Prompt Kit Favorites",
            "backups/prompt-kit-browser-proof-cleanup",
            "Copy-Item -LiteralPath $ResolvedReportPath",
            "previous_receipt_backup",
            "ReportPath must stay under repository Outputs/",
        ]
        for marker in required_markers:
            if marker not in text:
                errors.append(f"cleanup runner missing safety marker: {marker}")
        forbidden = [
            "Remove-Item -Path $env:TEMP",
            "Remove-Item $env:TEMP",
            "Clear-SiteData",
            "localStorage.clear(",
            "promptKit.favoritePromptIds.v1",
        ]
        for marker in forbidden:
            if marker in text:
                errors.append(f"cleanup runner contains forbidden broad/browser-data mutation: {marker}")

    artifacts = load_json(DOMAIN / "artifacts.v1.json")
    if artifacts.get("schema_version") != "prompt-kit-browser-proof-cleanup-artifacts/v1":
        errors.append("artifact registry schema is unsupported")
    artifact_ids = {item.get("id") for item in artifacts.get("artifacts", []) if isinstance(item, dict)}
    if "prompt-kit-browser-proof-cleanup-report" not in artifact_ids:
        errors.append("cleanup report artifact is not registered")

    validators = load_json(DOMAIN / "validators.v1.json")
    if validators.get("schema_version") != "prompt-kit-browser-proof-cleanup-validators/v1":
        errors.append("validator registry schema is unsupported")
    validator_ids = {item.get("id") for item in validators.get("validators", []) if isinstance(item, dict)}
    for required in {
        "browser-proof-cleanup-completeness",
        "browser-proof-cleanup-contract-tests",
        "browser-proof-cleanup-powershell-smoke",
        "patch-hygiene",
    }:
        if required not in validator_ids:
            errors.append(f"missing validator registration: {required}")

    triggers = load_json(DOMAIN / "triggers.v1.json")
    if triggers.get("schema_version") != "prompt-kit-browser-proof-cleanup-triggers/v1":
        errors.append("trigger registry schema is unsupported")
    if not triggers.get("triggers"):
        errors.append("trigger registry must contain at least one trigger")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        errors = validate()
    except RuntimeError as exc:
        print(f"Prompt Kit browser-proof cleanup harness: FAIL: {exc}", file=sys.stderr)
        return 2
    if errors:
        print("Prompt Kit browser-proof cleanup harness: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.summary:
        print("Prompt Kit browser-proof cleanup harness: PASS")
    else:
        print(json.dumps({"verdict": "pass", "manifest": str(MANIFEST.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
