#!/usr/bin/env python3
"""Fail-closed contract validator for Prompt Kit cross-device access routing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-cross-device-access.v1.json"
MANIFEST_PATH = ROOT / "harness" / "manifest.v1.json"
WORKFLOWS_PATH = ROOT / "harness" / "workflows.v1.json"
ARTIFACTS_PATH = ROOT / "harness" / "artifacts.v1.json"
CAPABILITIES_PATH = ROOT / "harness" / "capabilities.v1.json"
TRIGGERS_PATH = ROOT / "harness" / "triggers.v1.json"
ACCESS_GUIDE_PATH = ROOT / "PROMPT_KIT_ACCESS.md"
PHONE_GUIDE_PATH = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"
SKILL_PATH = ROOT / ".ai" / "skills" / "technician-prompt-kit-acquisition" / "SKILL.md"

PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
REPOSITORY_URL = "https://github.com/EndeavorEverlasting/web-excel-repair-triage.git"
ZIP_URL = "https://github.com/EndeavorEverlasting/web-excel-repair-triage/archive/refs/heads/main.zip"
REQUIRED_MODE_IDS = {
    "browser-use",
    "phone-install",
    "windows-local-app",
    "editable-checkout",
    "zip-snapshot",
}
FORBIDDEN_DESTRUCTIVE_PATTERNS = (
    "git reset --hard",
    "git clean -fd",
    "git clean -xdf",
    "git push --force",
    "git checkout -f",
)


class CrossDeviceAccessError(RuntimeError):
    """Raised when the cross-device Prompt Kit access contract drifts."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CrossDeviceAccessError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise CrossDeviceAccessError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def require_text(path: Path, phrases: tuple[str, ...]) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CrossDeviceAccessError(f"missing required file: {path.relative_to(ROOT)}") from exc
    for phrase in phrases:
        if phrase not in text:
            raise CrossDeviceAccessError(
                f"{path.relative_to(ROOT)} is missing required text: {phrase}"
            )
    return text


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CrossDeviceAccessError(f"{field} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise CrossDeviceAccessError(f"{field} contains an empty/non-string item")
        result.append(item.strip())
    if len(result) != len(set(result)):
        raise CrossDeviceAccessError(f"{field} contains duplicate items")
    return result


def validate_contract_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if payload.get("schema_version") != "prompt-kit-cross-device-access/v1":
        raise CrossDeviceAccessError("unsupported cross-device access schema")
    if payload.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise CrossDeviceAccessError("cross-device access repository is not canonical")
    if payload.get("default_branch") != "main":
        raise CrossDeviceAccessError("cross-device access default branch must be main")
    if payload.get("canonical_repository_url") != REPOSITORY_URL:
        raise CrossDeviceAccessError("canonical repository URL drifted")
    if payload.get("canonical_site") != "web/prompt-kit/index.html":
        raise CrossDeviceAccessError("canonical Prompt Kit site path drifted")
    if payload.get("public_prompt_kit_url") != PUBLIC_URL:
        raise CrossDeviceAccessError("public Prompt Kit URL drifted")
    if payload.get("public_launcher_url") != LAUNCHER_URL:
        raise CrossDeviceAccessError("public phone launcher URL drifted")
    if payload.get("source_guides") != ["PROMPT_KIT_ACCESS.md", "OPEN_PROMPT_KIT_ON_PHONE.md"]:
        raise CrossDeviceAccessError("source guide ownership drifted")

    priority = _string_list(payload.get("routing_priority"), "routing_priority")
    if set(priority) != REQUIRED_MODE_IDS or priority[:2] != ["browser-use", "phone-install"]:
        raise CrossDeviceAccessError(
            "routing priority must cover every mode and prefer direct browser/phone access"
        )

    modes = payload.get("modes")
    if not isinstance(modes, list) or not modes:
        raise CrossDeviceAccessError("modes must be a non-empty list")
    by_id: dict[str, dict[str, Any]] = {}
    for mode in modes:
        if not isinstance(mode, dict):
            raise CrossDeviceAccessError("mode entry must be an object")
        mode_id = str(mode.get("id", "")).strip()
        if not mode_id or mode_id in by_id:
            raise CrossDeviceAccessError(f"duplicate or empty mode ID: {mode_id}")
        by_id[mode_id] = mode
        _string_list(mode.get("intent"), f"mode.{mode_id}.intent")
        _string_list(mode.get("devices"), f"mode.{mode_id}.devices")
        if not isinstance(mode.get("manual_clone_required"), bool):
            raise CrossDeviceAccessError(
                f"mode.{mode_id}.manual_clone_required must be boolean"
            )
        if not str(mode.get("entry_point", "")).strip():
            raise CrossDeviceAccessError(f"mode.{mode_id}.entry_point is required")
        if not str(mode.get("operator_message", "")).strip():
            raise CrossDeviceAccessError(f"mode.{mode_id}.operator_message is required")

    if set(by_id) != REQUIRED_MODE_IDS:
        raise CrossDeviceAccessError(f"mode IDs drifted: {sorted(by_id)}")
    if by_id["browser-use"]["manual_clone_required"] is not False:
        raise CrossDeviceAccessError("browser use must never require a manual clone")
    if by_id["phone-install"]["manual_clone_required"] is not False:
        raise CrossDeviceAccessError("phone install must never require a manual clone")
    if by_id["editable-checkout"]["manual_clone_required"] is not True:
        raise CrossDeviceAccessError("editable checkout must explicitly own clone behavior")
    if by_id["browser-use"]["entry_point"] != PUBLIC_URL:
        raise CrossDeviceAccessError("browser-use entry point drifted")
    if by_id["phone-install"]["entry_point"] != LAUNCHER_URL:
        raise CrossDeviceAccessError("phone-install entry point drifted")
    if by_id["windows-local-app"]["entry_point"] != "Open-Latest-PromptKit.cmd":
        raise CrossDeviceAccessError("Windows local-app entry point drifted")
    editable = by_id["editable-checkout"]
    if editable.get("entry_point") != f"git clone --branch main --single-branch {REPOSITORY_URL}":
        raise CrossDeviceAccessError("editable checkout clone command drifted")
    if editable.get("update_command") != "git pull --ff-only origin main":
        raise CrossDeviceAccessError("editable checkout must update with ff-only")
    prereqs = _string_list(editable.get("android_prerequisites"), "editable-checkout.android_prerequisites")
    prereq_text = "\n".join(prereqs)
    for phrase in ("Termux", "F-Droid", "pkg update", "pkg install git"):
        if phrase not in prereq_text:
            raise CrossDeviceAccessError(
                f"Android editable-checkout prerequisites are missing: {phrase}"
            )
    if by_id["zip-snapshot"]["entry_point"] != ZIP_URL:
        raise CrossDeviceAccessError("ZIP snapshot URL drifted")

    guardrails = "\n".join(_string_list(payload.get("guardrails"), "guardrails"))
    for phrase in (
        "Do not tell a normal phone or browser user to clone",
        "download web/prompt-kit/index.html",
        "Distinguish use/install intent from edit/commit/push intent",
        "never reset, clean, force-push, or discard local work",
    ):
        if phrase not in guardrails:
            raise CrossDeviceAccessError(f"cross-device guardrail is missing: {phrase}")
    if not str(payload.get("proof_ceiling", "")).strip():
        raise CrossDeviceAccessError("cross-device access proof ceiling is missing")
    return by_id


def validate_repository_surfaces() -> None:
    require_text(
        ACCESS_GUIDE_PATH,
        (
            PUBLIC_URL,
            LAUNCHER_URL,
            "No repository clone, ZIP extraction, Git client, Python installation, PowerShell, or local web server is required for normal browser use.",
            "Open-Latest-PromptKit.cmd",
            ZIP_URL,
            f"git clone --branch main --single-branch {REPOSITORY_URL}",
        ),
    )
    require_text(
        PHONE_GUIDE_PATH,
        (
            LAUNCHER_URL,
            PUBLIC_URL,
            "Open in browser",
            "Install on this Android phone",
            "same Prompt Kit used on desktop",
        ),
    )
    skill = require_text(
        SKILL_PATH,
        (
            "## Trigger",
            "## Required inputs",
            "## Outputs",
            "## Procedure",
            "## Guardrails",
            "## Validation",
            "## Proof ceiling",
            "Termux",
            "F-Droid",
            "pkg install git",
            f"git clone --branch main --single-branch {REPOSITORY_URL}",
            "git pull --ff-only origin main",
            "Do not require a clone merely to use the Prompt Kit",
        ),
    )
    lowered_skill = skill.lower()
    for pattern in FORBIDDEN_DESTRUCTIVE_PATTERNS:
        if pattern in lowered_skill:
            raise CrossDeviceAccessError(
                f"acquisition skill contains forbidden destructive command: {pattern}"
            )

    manifest = load_json(MANIFEST_PATH)
    domain = manifest.get("domain_contracts", {}).get("prompt_kit_cross_device_access")
    if not isinstance(domain, dict):
        raise CrossDeviceAccessError("manifest is missing prompt_kit_cross_device_access")
    expected_domain = {
        "contract": "harness/contracts/prompt-kit-cross-device-access.v1.json",
        "validator": "scripts/validate_prompt_kit_cross_device_access.py",
        "contract_tests": "tests/test_prompt_kit_cross_device_access.py",
        "workflow": "WORKFLOW.md#a-technician-acquisition-or-update",
        "harness_gate": "python scripts/validate_prompt_kit_cross_device_access.py --summary",
    }
    for key, value in expected_domain.items():
        if domain.get(key) != value:
            raise CrossDeviceAccessError(
                f"manifest cross-device domain field drifted: {key}"
            )

    workflows = load_json(WORKFLOWS_PATH).get("workflows", [])
    acquisition = next((item for item in workflows if item.get("id") == "technician-acquisition"), None)
    if not isinstance(acquisition, dict):
        raise CrossDeviceAccessError("technician-acquisition workflow is missing")
    workflow_text = json.dumps(acquisition, sort_keys=True).lower()
    for phrase in ("phone", "browser", "edit", "commit", "public"):
        if phrase not in workflow_text:
            raise CrossDeviceAccessError(
                f"technician-acquisition workflow lacks cross-device routing term: {phrase}"
            )

    capabilities = load_json(CAPABILITIES_PATH).get("capabilities", [])
    capability = next(
        (item for item in capabilities if item.get("id") == "technician-prompt-kit-acquisition"),
        None,
    )
    if not isinstance(capability, dict):
        raise CrossDeviceAccessError("technician-prompt-kit-acquisition capability is missing")
    capability_text = json.dumps(capability, sort_keys=True).lower()
    for phrase in ("public", "phone", "editable checkout", "termux"):
        if phrase not in capability_text:
            raise CrossDeviceAccessError(
                f"acquisition capability lacks cross-device routing term: {phrase}"
            )

    triggers = load_json(TRIGGERS_PATH).get("triggers", [])
    trigger = next(
        (item for item in triggers if item.get("id") == "technician-needs-latest-prompt-kit"),
        None,
    )
    if not isinstance(trigger, dict):
        raise CrossDeviceAccessError("technician-needs-latest-prompt-kit trigger is missing")
    trigger_text = json.dumps(trigger, sort_keys=True).lower()
    for phrase in ("phone", "browser", "install", "edit"):
        if phrase not in trigger_text:
            raise CrossDeviceAccessError(
                f"acquisition trigger lacks cross-device routing term: {phrase}"
            )

    artifacts = load_json(ARTIFACTS_PATH).get("artifacts", [])
    site = next((item for item in artifacts if item.get("id") == "prompt-kit-website"), None)
    if not isinstance(site, dict):
        raise CrossDeviceAccessError("prompt-kit-website artifact is missing")
    surfaces = site.get("delivery_surfaces")
    if not isinstance(surfaces, list):
        raise CrossDeviceAccessError("prompt-kit-website delivery_surfaces are missing")
    if PUBLIC_URL not in surfaces or LAUNCHER_URL not in surfaces or "Open-Latest-PromptKit.cmd" not in surfaces:
        raise CrossDeviceAccessError("prompt-kit-website delivery surfaces drifted")


def validate() -> dict[str, Any]:
    payload = load_json(CONTRACT_PATH)
    modes = validate_contract_payload(payload)
    validate_repository_surfaces()
    return {
        "schema_version": "prompt-kit-cross-device-access-validation/v1",
        "status": "PASS",
        "mode_count": len(modes),
        "mode_ids": list(payload["routing_priority"]),
        "proof_ceiling": payload["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Print a compact PASS summary.")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except CrossDeviceAccessError as exc:
        print(f"prompt-kit-cross-device-access: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "prompt-kit-cross-device-access: PASS "
            f"({report['mode_count']} modes: {', '.join(report['mode_ids'])})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
