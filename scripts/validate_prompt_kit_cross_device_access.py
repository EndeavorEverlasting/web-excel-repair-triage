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
ACQUISITION_SKILL = ".ai/skills/technician-prompt-kit-acquisition/SKILL.md"
ACQUISITION_TRIGGER = "technician-needs-latest-prompt-kit"
ACQUISITION_WORKFLOW = "WORKFLOW.md#a-technician-acquisition-or-update"
REQUIRED_MODE_IDS = {
    "browser-use",
    "phone-install",
    "windows-local-app",
    "editable-checkout",
    "zip-snapshot",
}
EDITABLE_CHECKOUT_REQUIREMENTS = {
    "origin": REPOSITORY_URL,
    "worktree": "clean",
    "branch": "main",
    "local_only_commits": 0,
}
EDITABLE_UPDATE_SEQUENCE = [
    "git remote get-url origin",
    "git status --porcelain",
    "git branch --show-current",
    "git fetch origin main --prune",
    "git rev-list --left-right --count HEAD...origin/main",
    "git merge --ff-only origin/main",
]
FORBIDDEN_DESTRUCTIVE_PATTERNS = (
    "git reset --hard",
    "git clean -fd",
    "git clean -xdf",
    "git push --force",
    "git checkout -f",
)
NORMAL_USE_FORBIDDEN = (
    "git clone",
    "main.zip",
    "download `web/prompt-kit/index.html`",
    "download web/prompt-kit/index.html",
)


class CrossDeviceAccessError(RuntimeError):
    """Raised when the cross-device Prompt Kit access contract drifts."""


def _path_label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    label = _path_label(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CrossDeviceAccessError(f"missing required file: {label}") from exc
    except json.JSONDecodeError as exc:
        raise CrossDeviceAccessError(f"invalid JSON in {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CrossDeviceAccessError(f"{label} JSON root must be an object")
    return payload


def require_text(path: Path, phrases: tuple[str, ...]) -> str:
    label = _path_label(path)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CrossDeviceAccessError(f"missing required file: {label}") from exc
    for phrase in phrases:
        if phrase not in text:
            raise CrossDeviceAccessError(f"{label} is missing required text: {phrase}")
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


def require_markdown_section(
    text: str,
    heading: str,
    *,
    required: tuple[str, ...],
    forbidden: tuple[str, ...] = (),
    label: str,
) -> str:
    """Validate required/forbidden text inside one Markdown heading boundary."""
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == heading)
    except StopIteration as exc:
        raise CrossDeviceAccessError(f"{label} is missing section: {heading}") from exc

    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if not stripped.startswith("#"):
            continue
        next_level = len(stripped) - len(stripped.lstrip("#"))
        if next_level <= level:
            end = index
            break
    section = "\n".join(lines[start:end])
    lowered = section.lower()
    for phrase in required:
        if phrase not in section:
            raise CrossDeviceAccessError(
                f"{label} section {heading!r} is missing required text: {phrase}"
            )
    for phrase in forbidden:
        if phrase.lower() in lowered:
            raise CrossDeviceAccessError(
                f"{label} section {heading!r} contains contradictory normal-use instruction: {phrase}"
            )
    return section


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
    prereqs = _string_list(
        editable.get("android_prerequisites"),
        "editable-checkout.android_prerequisites",
    )
    prereq_text = "\n".join(prereqs)
    for phrase in ("Termux", "F-Droid", "pkg update", "pkg install git"):
        if phrase not in prereq_text:
            raise CrossDeviceAccessError(
                f"Android editable-checkout prerequisites are missing: {phrase}"
            )
    if editable.get("existing_checkout_requirements") != EDITABLE_CHECKOUT_REQUIREMENTS:
        raise CrossDeviceAccessError("editable checkout safety requirements drifted")
    if editable.get("update_sequence") != EDITABLE_UPDATE_SEQUENCE:
        raise CrossDeviceAccessError("editable checkout safe update sequence drifted")
    if any("git pull" in command for command in editable["update_sequence"]):
        raise CrossDeviceAccessError("editable checkout update sequence must not use bare pull")

    if by_id["zip-snapshot"]["entry_point"] != ZIP_URL:
        raise CrossDeviceAccessError("ZIP snapshot URL drifted")

    guardrails = "\n".join(_string_list(payload.get("guardrails"), "guardrails"))
    for phrase in (
        "Do not tell a normal phone or browser user to clone",
        "download web/prompt-kit/index.html",
        "Distinguish use/install intent from edit/commit/push intent",
        "verify canonical origin, clean worktree, current branch main, and zero local-only commits",
        "never reset, clean, force-push, or discard local work",
    ):
        if phrase not in guardrails:
            raise CrossDeviceAccessError(f"cross-device guardrail is missing: {phrase}")
    if not str(payload.get("proof_ceiling", "")).strip():
        raise CrossDeviceAccessError("cross-device access proof ceiling is missing")
    return by_id


def validate_workflow_registration(payload: dict[str, Any]) -> None:
    workflows = payload.get("workflows")
    if not isinstance(workflows, list):
        raise CrossDeviceAccessError("workflow registry workflows must be a list")
    acquisition = next(
        (
            item
            for item in workflows
            if isinstance(item, dict) and item.get("id") == "technician-acquisition"
        ),
        None,
    )
    if not isinstance(acquisition, dict):
        raise CrossDeviceAccessError("technician-acquisition workflow is missing")
    if acquisition.get("document") != ACQUISITION_WORKFLOW:
        raise CrossDeviceAccessError("technician-acquisition workflow document drifted")
    if acquisition.get("validation_profile") != "harness":
        raise CrossDeviceAccessError("technician-acquisition validation profile drifted")
    expected_entry_points = {
        PUBLIC_URL,
        LAUNCHER_URL,
        "Open-Latest-PromptKit.cmd",
        "Acquire-Latest-PromptKit.cmd",
    }
    if set(_string_list(acquisition.get("entry_points"), "technician-acquisition.entry_points")) != expected_entry_points:
        raise CrossDeviceAccessError("technician-acquisition entry points drifted")
    owned = _string_list(acquisition.get("owned_scope"), "technician-acquisition.owned_scope")
    if "harness/contracts/prompt-kit-cross-device-access.v1.json" not in owned:
        raise CrossDeviceAccessError("technician-acquisition no longer owns the cross-device contract")
    forbidden = _string_list(
        acquisition.get("forbidden_scope"),
        "technician-acquisition.forbidden_scope",
    )
    if "requiring a clone for normal browser or phone use" not in forbidden:
        raise CrossDeviceAccessError("technician-acquisition no-clone guardrail drifted")


def validate_capability_registration(payload: dict[str, Any]) -> None:
    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list):
        raise CrossDeviceAccessError("capability registry capabilities must be a list")
    capability = next(
        (
            item
            for item in capabilities
            if isinstance(item, dict)
            and item.get("id") == "technician-prompt-kit-acquisition"
        ),
        None,
    )
    if not isinstance(capability, dict):
        raise CrossDeviceAccessError("technician-prompt-kit-acquisition capability is missing")
    if capability.get("status") != "canonical":
        raise CrossDeviceAccessError("technician acquisition capability must remain canonical")
    if capability.get("skill") != ACQUISITION_SKILL:
        raise CrossDeviceAccessError("technician acquisition capability skill drifted")
    if capability.get("trigger_ids") != [ACQUISITION_TRIGGER]:
        raise CrossDeviceAccessError("technician acquisition capability trigger ownership drifted")
    if capability.get("implementation") != {
        "kind": "launcher",
        "path": "Acquire-Latest-PromptKit.cmd",
    }:
        raise CrossDeviceAccessError("technician acquisition implementation ownership drifted")
    outputs = set(_string_list(capability.get("outputs"), "technician acquisition outputs"))
    expected_outputs = {
        "selected cross-device access mode",
        "public Prompt Kit or phone install surface",
        "validated Windows local app when requested",
        "clean editable checkout when source work is requested",
        "explicit runtime proof ceiling",
    }
    if outputs != expected_outputs:
        raise CrossDeviceAccessError("technician acquisition capability outputs drifted")


def validate_trigger_registration(payload: dict[str, Any]) -> None:
    triggers = payload.get("triggers")
    if not isinstance(triggers, list):
        raise CrossDeviceAccessError("trigger registry triggers must be a list")
    trigger = next(
        (
            item
            for item in triggers
            if isinstance(item, dict) and item.get("id") == ACQUISITION_TRIGGER
        ),
        None,
    )
    if not isinstance(trigger, dict):
        raise CrossDeviceAccessError("technician-needs-latest-prompt-kit trigger is missing")
    if trigger.get("capability_id") != "technician-prompt-kit-acquisition":
        raise CrossDeviceAccessError("technician acquisition trigger capability drifted")
    if trigger.get("skill") != ACQUISITION_SKILL:
        raise CrossDeviceAccessError("technician acquisition trigger skill drifted")
    if trigger.get("workflow") != ACQUISITION_WORKFLOW:
        raise CrossDeviceAccessError("technician acquisition trigger workflow drifted")
    expected_conditions = {
        "user wants to open or use the Prompt Kit in a browser",
        "phone or tablet user wants to open, install, or Add to Home Screen",
        "Windows user wants the stable local Prompt Kit app",
        "user wants an editable local checkout to edit, commit, push, or run repository tooling",
        "user explicitly wants a source ZIP snapshot without Git",
    }
    if set(_string_list(trigger.get("conditions"), "technician acquisition conditions")) != expected_conditions:
        raise CrossDeviceAccessError("technician acquisition trigger conditions drifted")
    expected_forbidden = {
        "destructive Git cleanup is proposed",
        "credential embedding or authentication automation is requested",
        "an editable checkout update is requested while that checkout is dirty, divergent, non-main, or has an unexpected origin",
        "the request is a Prompt Kit product behavior change rather than acquisition or access",
    }
    if set(_string_list(trigger.get("forbidden_conditions"), "technician acquisition forbidden conditions")) != expected_forbidden:
        raise CrossDeviceAccessError("technician acquisition trigger forbidden conditions drifted")


def validate_repository_surfaces() -> None:
    access_guide = require_text(
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
    require_markdown_section(
        access_guide,
        "## Phone, tablet, or any browser",
        required=(
            PUBLIC_URL,
            "No repository clone, ZIP extraction, Git client, Python installation, PowerShell, or local web server is required for normal browser use.",
            "Add to Home Screen",
            "Add to Home screen",
        ),
        forbidden=NORMAL_USE_FORBIDDEN,
        label="PROMPT_KIT_ACCESS.md",
    )

    phone_guide = require_text(
        PHONE_GUIDE_PATH,
        (
            LAUNCHER_URL,
            PUBLIC_URL,
            "Open in browser",
            "Install on this Android phone",
            "same Prompt Kit used on desktop",
        ),
    )
    require_markdown_section(
        phone_guide,
        "## One tap — no download required",
        required=(
            LAUNCHER_URL,
            PUBLIC_URL,
            "does not need to download `index.html`",
            "Open in browser",
            "Install on this Android phone",
        ),
        forbidden=("git clone", "main.zip"),
        label="OPEN_PROMPT_KIT_ON_PHONE.md",
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
            *EDITABLE_UPDATE_SEQUENCE,
            "Do not require a clone merely to use the Prompt Kit",
        ),
    )
    require_markdown_section(
        skill,
        "### 1. Normal browser use",
        required=(PUBLIC_URL, "Do not require a clone merely to use the Prompt Kit"),
        forbidden=NORMAL_USE_FORBIDDEN,
        label=ACQUISITION_SKILL,
    )
    require_markdown_section(
        skill,
        "### 2. Android or iPhone/iPad install",
        required=(LAUNCHER_URL, "Open in browser", "Add to Home Screen"),
        forbidden=NORMAL_USE_FORBIDDEN,
        label=ACQUISITION_SKILL,
    )
    require_markdown_section(
        skill,
        "### 4. Real editable checkout",
        required=(
            f"git clone --branch main --single-branch {REPOSITORY_URL}",
            *EDITABLE_UPDATE_SEQUENCE,
            "must equal `https://github.com/EndeavorEverlasting/web-excel-repair-triage.git`",
            "must return no output",
            "must return `main`",
            "must report **0** in the first (local-only) count",
        ),
        forbidden=("git pull --ff-only origin main",),
        label=ACQUISITION_SKILL,
    )
    lowered_skill = skill.lower()
    for pattern in FORBIDDEN_DESTRUCTIVE_PATTERNS:
        if pattern in lowered_skill:
            raise CrossDeviceAccessError(
                f"acquisition skill contains forbidden destructive command: {pattern}"
            )

    manifest = load_json(MANIFEST_PATH)
    domains = manifest.get("domain_contracts")
    if not isinstance(domains, dict):
        raise CrossDeviceAccessError("manifest domain_contracts must be an object")
    domain = domains.get("prompt_kit_cross_device_access")
    if not isinstance(domain, dict):
        raise CrossDeviceAccessError("manifest is missing prompt_kit_cross_device_access")
    expected_domain = {
        "contract": "harness/contracts/prompt-kit-cross-device-access.v1.json",
        "validator": "scripts/validate_prompt_kit_cross_device_access.py",
        "contract_tests": "tests/test_prompt_kit_cross_device_access.py",
        "workflow": ACQUISITION_WORKFLOW,
        "harness_gate": "python scripts/validate_prompt_kit_cross_device_access.py --summary",
    }
    for key, value in expected_domain.items():
        if domain.get(key) != value:
            raise CrossDeviceAccessError(f"manifest cross-device domain field drifted: {key}")

    validate_workflow_registration(load_json(WORKFLOWS_PATH))
    validate_capability_registration(load_json(CAPABILITIES_PATH))
    validate_trigger_registration(load_json(TRIGGERS_PATH))

    artifacts = load_json(ARTIFACTS_PATH).get("artifacts")
    if not isinstance(artifacts, list):
        raise CrossDeviceAccessError("artifact registry artifacts must be a list")
    site = next(
        (
            item
            for item in artifacts
            if isinstance(item, dict) and item.get("id") == "prompt-kit-website"
        ),
        None,
    )
    if not isinstance(site, dict):
        raise CrossDeviceAccessError("prompt-kit-website artifact is missing")
    surfaces = set(_string_list(site.get("delivery_surfaces"), "prompt-kit-website.delivery_surfaces"))
    expected_surfaces = {
        PUBLIC_URL,
        LAUNCHER_URL,
        "Open-Latest-PromptKit.cmd",
        "PROMPT_KIT_ACCESS.md",
        "OPEN_PROMPT_KIT_ON_PHONE.md",
    }
    if surfaces != expected_surfaces:
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
