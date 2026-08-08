#!/usr/bin/env python3
"""Fail-closed validator for Prompt Kit freshness guidance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-freshness-guidance.v1.json"
TRIGGERS_PATH = ROOT / "harness" / "triggers.v1.json"
SKILL_PATH = ROOT / ".ai" / "skills" / "technician-prompt-kit-acquisition" / "SKILL.md"
REPORT_PATH = ROOT / "harness" / "reports" / "CURRENT_STATE.md"

PUBLIC_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/prompt-kit/"
LAUNCHER_URL = "https://endeavoreverlasting.github.io/web-excel-repair-triage/"
TRIGGER_ID = "technician-needs-latest-prompt-kit"
FRESHNESS_TRIGGER = "user reports a Prompt Kit or prompt version label and currentness is not proven"

EXPECTED_ROUTES = {
    "browser-use": f"Open {PUBLIC_URL} and use that public surface as the normal-use latest route.",
    "phone-install": f"Open {LAUNCHER_URL} in the system browser, then use Install app or Add to Home Screen when offered.",
    "windows-local-app": "Run Open-Latest-PromptKit.cmd so the repository-owned launcher performs safe acquisition/update and validation.",
    "editable-checkout": "Verify canonical origin, clean worktree, current branch main, and zero local-only commits; fetch origin/main; then integrate only with git merge --ff-only origin/main.",
    "zip-snapshot": "Explain that the ZIP is point-in-time and re-download main.zip when the user explicitly wants a fresh no-Git source snapshot.",
}


class FreshnessGuidanceError(RuntimeError):
    """Raised when Prompt Kit freshness guidance drifts."""


def load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FreshnessGuidanceError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise FreshnessGuidanceError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise FreshnessGuidanceError(f"{path.relative_to(ROOT)} JSON root must be an object")
    return payload


def string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise FreshnessGuidanceError(f"{field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise FreshnessGuidanceError(f"{field} contains an empty/non-string item")
    return [item.strip() for item in value]


def validate_contract(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "prompt-kit-freshness-guidance/v1":
        raise FreshnessGuidanceError("unsupported freshness-guidance schema")
    if payload.get("repository") != "EndeavorEverlasting/web-excel-repair-triage":
        raise FreshnessGuidanceError("freshness-guidance repository drifted")
    if payload.get("default_branch") != "main":
        raise FreshnessGuidanceError("freshness-guidance default branch must be main")

    triggers = string_list(payload.get("freshness_triggers"), "freshness_triggers")
    if FRESHNESS_TRIGGER not in triggers:
        raise FreshnessGuidanceError("version-label freshness trigger is missing")
    if not any("downloaded, cloned, installed, or opened previously" in item for item in triggers):
        raise FreshnessGuidanceError("previous-copy freshness trigger is missing")

    behavior = "\n".join(string_list(payload.get("required_agent_behavior"), "required_agent_behavior"))
    for phrase in (
        "may be stale before troubleshooting or prompt-selection guidance",
        "lowest-friction latest route",
        "only wants to use the Prompt Kit in a browser",
        "explicitly declines to refresh",
        "stale-or-unverified",
    ):
        if phrase not in behavior:
            raise FreshnessGuidanceError(f"required freshness behavior is missing: {phrase}")

    routes = payload.get("freshness_routes")
    if routes != EXPECTED_ROUTES:
        raise FreshnessGuidanceError("freshness routes drifted")

    evidence = "\n".join(string_list(payload.get("currentness_evidence"), "currentness_evidence"))
    for phrase in ("canonical public Prompt Kit URL", "repository-owned launcher", "origin/main", "freshly downloaded"):
        if phrase not in evidence:
            raise FreshnessGuidanceError(f"currentness evidence is missing: {phrase}")

    anti_patterns = "\n".join(string_list(payload.get("anti_patterns"), "anti_patterns"))
    for phrase in ("version label such as V39", "reported old local copy", "normal phone/browser user", "bare git pull"):
        if phrase not in anti_patterns:
            raise FreshnessGuidanceError(f"freshness anti-pattern is missing: {phrase}")

    if not str(payload.get("proof_ceiling", "")).strip():
        raise FreshnessGuidanceError("freshness proof ceiling is missing")


def validate_trigger(payload: dict[str, Any]) -> None:
    triggers = payload.get("triggers")
    if not isinstance(triggers, list):
        raise FreshnessGuidanceError("trigger registry triggers must be a list")
    trigger = next((item for item in triggers if isinstance(item, dict) and item.get("id") == TRIGGER_ID), None)
    if not isinstance(trigger, dict):
        raise FreshnessGuidanceError("technician-needs-latest-prompt-kit trigger is missing")
    conditions = string_list(trigger.get("conditions"), "technician-needs-latest-prompt-kit.conditions")
    if FRESHNESS_TRIGGER not in conditions:
        raise FreshnessGuidanceError("technician acquisition trigger does not fire on a reported version label")


def validate_skill() -> None:
    try:
        text = SKILL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FreshnessGuidanceError("technician acquisition skill is missing") from exc
    required = (
        "### 0. Freshness gate before guidance",
        "A version label is a freshness signal, not proof of currentness.",
        "Before troubleshooting, tutorial guidance, or prompt selection",
        "recommend the lowest-friction refresh route first",
        PUBLIC_URL,
        LAUNCHER_URL,
        "Open-Latest-PromptKit.cmd",
        "git merge --ff-only origin/main",
        "stale-or-unverified",
    )
    for phrase in required:
        if phrase not in text:
            raise FreshnessGuidanceError(f"acquisition skill is missing freshness guidance: {phrase}")


def validate_report() -> None:
    try:
        text = REPORT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FreshnessGuidanceError("harness operator report is missing") from exc
    for phrase in (
        "Prompt Kit freshness",
        "version label",
        "recommend a refresh before troubleshooting",
    ):
        if phrase not in text:
            raise FreshnessGuidanceError(f"operator report is missing freshness state: {phrase}")


def validate() -> dict[str, Any]:
    contract = load_object(CONTRACT_PATH)
    validate_contract(contract)
    validate_trigger(load_object(TRIGGERS_PATH))
    validate_skill()
    validate_report()
    return {
        "schema_version": "prompt-kit-freshness-guidance-validation/v1",
        "status": "PASS",
        "freshness_trigger_count": len(contract["freshness_triggers"]),
        "route_count": len(contract["freshness_routes"]),
        "proof_ceiling": contract["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except FreshnessGuidanceError as exc:
        print(f"prompt-kit-freshness-guidance: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "prompt-kit-freshness-guidance: PASS "
            f"({report['freshness_trigger_count']} triggers, {report['route_count']} routes)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
