#!/usr/bin/env python3
"""Fail-closed validator for the Neuron Track Hours domain harness overlay."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NTH_MANIFEST = ROOT / "harness" / "nth" / "manifest.v1.json"
RULE_PACKS = ROOT / "harness" / "nth" / "monthly-rule-packs.v1.json"
TRIGGERS = ROOT / "harness" / "nth" / "triggers.v1.json"
SKILL = ROOT / ".ai" / "skills" / "neuron-track-hours-monthly-artifact" / "SKILL.md"

REQUIRED_SKILL_SECTIONS = (
    "## Trigger",
    "## Required inputs",
    "## Outputs",
    "## Procedure",
    "## Guardrails",
    "## Validation",
    "## Proof ceiling",
)
REQUIRED_TRIGGER_IDS = {
    "nth-internal-workbook-request",
    "nth-client-send-copy-request",
}
REQUIRED_CLIENT_TABS = ["Executive Summary", "July 2026"]


class NthHarnessValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NthHarnessValidationError(
            f"missing required JSON: {path.relative_to(ROOT)}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise NthHarnessValidationError(
            f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
        ) from exc


def require_file(relative_path: str) -> Path:
    path = ROOT / relative_path
    if not path.is_file():
        raise NthHarnessValidationError(f"missing required file: {relative_path}")
    if path.stat().st_size == 0:
        raise NthHarnessValidationError(f"required file is empty: {relative_path}")
    return path


def require_tracked(relative_path: str) -> None:
    if not (ROOT / ".git").exists():
        return
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise NthHarnessValidationError(f"required NTH harness file is not tracked: {relative_path}")


def require_text(relative_path: str, phrases: tuple[str, ...]) -> str:
    text = require_file(relative_path).read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            raise NthHarnessValidationError(
                f"{relative_path} is missing required NTH harness text: {phrase}"
            )
    return text


def validate_manifest() -> dict[str, Any]:
    payload = load_json(NTH_MANIFEST)
    if payload.get("schema_version") != "neuron-track-hours-harness/v1":
        raise NthHarnessValidationError("unsupported NTH harness manifest schema")
    if payload.get("governance") != "AGENTS.md":
        raise NthHarnessValidationError("NTH harness must consume AGENTS.md governance")

    required_paths = {
        "rule_pack_registry": "harness/nth/monthly-rule-packs.v1.json",
        "trigger_registry": "harness/nth/triggers.v1.json",
        "skill": ".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md",
        "validator": "scripts/validate_nth_harness.py",
        "tests": "tests/test_nth_harness_contract.py",
        "operator_report": "harness/reports/CURRENT_STATE.md",
    }
    for key, expected in required_paths.items():
        if payload.get(key) != expected:
            raise NthHarnessValidationError(
                f"NTH manifest {key} drifted: expected {expected!r}, got {payload.get(key)!r}"
            )
        require_file(expected)
        require_tracked(expected)

    if payload.get("workflow") != "WORKFLOW.md#h-neuron-track-hours-monthly-artifact":
        raise NthHarnessValidationError("NTH workflow anchor drifted")
    if payload.get("artifact_registry") != "ARTIFACT_REGISTRY.md#neuron-track-hours-artifacts":
        raise NthHarnessValidationError("NTH artifact-registry anchor drifted")

    order = payload.get("validation_order")
    if not isinstance(order, list) or len(order) < 6:
        raise NthHarnessValidationError("NTH validation order is incomplete")
    if order[:2] != [
        "python scripts/validate_nth_harness.py",
        "python -m unittest tests.test_nth_harness_contract -v",
    ]:
        raise NthHarnessValidationError("NTH focused validators must run first")
    if order[-1] != "git diff --check":
        raise NthHarnessValidationError("git diff --check must close NTH validation")
    return payload


def validate_rule_pack() -> dict[str, Any]:
    payload = load_json(RULE_PACKS)
    if payload.get("schema_version") != "neuron-track-hours-rule-packs/v1":
        raise NthHarnessValidationError("unsupported NTH rule-pack schema")
    packs = payload.get("rule_packs")
    if not isinstance(packs, list) or not packs:
        raise NthHarnessValidationError("NTH rule-pack registry is empty")
    ids = [str(pack.get("id", "")) for pack in packs]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise NthHarnessValidationError("NTH rule-pack IDs are duplicate or empty")
    try:
        july = next(pack for pack in packs if pack.get("id") == "july-2026")
    except StopIteration as exc:
        raise NthHarnessValidationError("July 2026 NTH rule pack is missing") from exc

    if july.get("coverage_month") != "2026-07":
        raise NthHarnessValidationError("July coverage month drifted")
    if july.get("effective_start") != "2026-06-26":
        raise NthHarnessValidationError("July guardrail effective start must remain June 26")
    if july.get("hours_source_of_truth") != "roster/attendance":
        raise NthHarnessValidationError("roster/attendance must remain the NTH hours source of truth")

    guardrail = july.get("aggregate_guardrail", {})
    config = guardrail.get("configurations")
    other = guardrail.get("other_work")
    if config != 0.6 or other != 0.4 or abs((config + other) - 1.0) > 1e-9:
        raise NthHarnessValidationError("July aggregate guardrail must remain 60% Configuration / 40% other work")
    if guardrail.get("mode") != "reasonableness_not_quota":
        raise NthHarnessValidationError("July 60/40 rule must remain a reasonableness guardrail, not a quota")

    primary = july.get("primary_workstream", {})
    if primary.get("one_dominant_per_paid_shift") is not True:
        raise NthHarnessValidationError("one dominant primary workstream per paid shift is required")
    if primary.get("complimentary_work_creates_hours") is not False:
        raise NthHarnessValidationError("complimentary work must never create hours")

    cadence = july.get("role_cadence", {}).get("Rich Perez", {})
    if cadence.get("full_client_correspondence_days_per_week") != 1:
        raise NthHarnessValidationError("Rich must retain one full correspondence day per week")
    if cadence.get("usual_day") != "Thursday":
        raise NthHarnessValidationError("Rich's usual full correspondence day must remain Thursday")
    if set(cadence.get("known_anchors", [])) != {"2026-07-02", "2026-07-23"}:
        raise NthHarnessValidationError("Rich's known July correspondence anchors drifted")

    exceptions = july.get("date_person_exceptions", [])
    by_key = {(item.get("date"), item.get("person")): item for item in exceptions}
    holiday = by_key.get(("2026-07-03", "core team"), {})
    if holiday.get("type") != "holiday" or holiday.get("project_hours") != 0:
        raise NthHarnessValidationError("July 3 holiday exception drifted")
    alejandro = by_key.get(("2026-07-24", "Alejandro Perales"), {})
    if alejandro.get("internal_status") != "A" or alejandro.get("project_hours") != 0:
        raise NthHarnessValidationError("Alejandro July 24 absence exception drifted")
    mixed = by_key.get(("2026-07-10", "team"), {})
    if mixed.get("type") != "mixed_operational_day":
        raise NthHarnessValidationError("July 10 must remain a mixed operational day")

    semantics = july.get("task_semantics", {})
    if semantics.get("configuration_and_deployment_are_distinct") is not True:
        raise NthHarnessValidationError("Configuration and Deployment must remain distinct")
    if semantics.get("pm_operational_control_is_not_catch_all") is not True:
        raise NthHarnessValidationError("PM / Operational Control must not become a catch-all")
    if semantics.get("role_specific_pm_client_ticket_work") is not True:
        raise NthHarnessValidationError("PM/client/ticket work must remain role-specific")

    modes = july.get("delivery_modes", {})
    internal = modes.get("internal", {})
    client = modes.get("client", {})
    if internal.get("preserve_complete_supporting_workbook") is not True:
        raise NthHarnessValidationError("internal NTH mode must preserve the complete supporting workbook")
    if client.get("derived_from") != "validated internal workbook":
        raise NthHarnessValidationError("client NTH mode must derive from the validated internal workbook")
    if client.get("tabs") != REQUIRED_CLIENT_TABS:
        raise NthHarnessValidationError(
            f"July client tabs must be exactly {REQUIRED_CLIENT_TABS!r}"
        )
    if client.get("omit_internal_only_sheets") is not True:
        raise NthHarnessValidationError("client mode must omit internal-only sheets")
    if client.get("hidden_internal_sheets_allowed") is not False:
        raise NthHarnessValidationError("hiding internal sheets is not a valid client packaging strategy")
    for flag in (
        "preserve_attendance_totals",
        "preserve_primary_workstream_truth",
        "preserve_task_attribution",
    ):
        if client.get(flag) is not True:
            raise NthHarnessValidationError(f"client/internal parity flag must remain true: {flag}")
    if client.get("expose_internal_percentages") is not False:
        raise NthHarnessValidationError("client mode must not expose internal allocation percentages")

    history = july.get("historical_review_boundaries", {}).get(
        "2026-05-26_to_2026-05-29", {}
    )
    if history.get("mode") != "review_not_correction":
        raise NthHarnessValidationError("May 26-29 must remain historical review, not correction")
    if history.get("historical_workbook_mutation_authorized") is not False:
        raise NthHarnessValidationError("historical May workbook mutation must remain unauthorized")
    if july.get("carry_forward_policy") != "forbidden_without_month_specific_confirmation":
        raise NthHarnessValidationError("month-specific NTH rules must not silently carry forward")
    return july


def validate_triggers() -> None:
    payload = load_json(TRIGGERS)
    if payload.get("schema_version") != "neuron-track-hours-triggers/v1":
        raise NthHarnessValidationError("unsupported NTH trigger schema")
    triggers = payload.get("triggers")
    if not isinstance(triggers, list):
        raise NthHarnessValidationError("NTH triggers must be a list")
    ids = {str(item.get("id", "")) for item in triggers}
    if ids != REQUIRED_TRIGGER_IDS:
        raise NthHarnessValidationError(f"NTH trigger IDs drifted: {sorted(ids)}")
    for trigger in triggers:
        if trigger.get("workflow") != "WORKFLOW.md#h-neuron-track-hours-monthly-artifact":
            raise NthHarnessValidationError(f"NTH trigger workflow drifted: {trigger.get('id')}")
        if trigger.get("skill") != ".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md":
            raise NthHarnessValidationError(f"NTH trigger skill drifted: {trigger.get('id')}")
        if trigger.get("mode") not in {"internal", "client"}:
            raise NthHarnessValidationError(f"NTH trigger mode invalid: {trigger.get('id')}")
        if not trigger.get("conditions") or not trigger.get("forbidden_conditions"):
            raise NthHarnessValidationError(f"NTH trigger conditions incomplete: {trigger.get('id')}")


def validate_skill() -> None:
    text = require_file(".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md").read_text(
        encoding="utf-8"
    )
    for section in REQUIRED_SKILL_SECTIONS:
        if section not in text:
            raise NthHarnessValidationError(f"NTH skill is missing {section}")
    for phrase in (
        "roster/attendance",
        "one dominant primary workstream",
        "60% Configuration / 40% other-work",
        "one full Client Correspondence / Coordination day per week",
        "Executive Summary",
        "July 2026",
        "derived copy",
        "historical attribution questions as reviews",
    ):
        if phrase not in text:
            raise NthHarnessValidationError(f"NTH skill is missing required rule: {phrase}")


def validate_governance_dependency() -> None:
    require_text(
        "AGENTS.md",
        (
            "Neuron Track Hours monthly task-distribution doctrine",
            "two governed NTH spreadsheet delivery modes",
            "60% Configuration / 40% other-work allocation",
            "one full Client Correspondence / Coordination day per week",
            "July client-facing mode contains exactly two tabs",
            "July internal mode preserves the complete supporting workbook",
        ),
    )


def validate_human_surfaces() -> None:
    require_text(
        "CODEBASE_MAP.md",
        (
            "harness/nth/manifest.v1.json",
            "harness/nth/monthly-rule-packs.v1.json",
            "scripts/validate_nth_harness.py",
            "neuron-track-hours-monthly-artifact",
        ),
    )
    require_text(
        "WORKFLOW.md",
        (
            "### H. Neuron Track Hours monthly artifact",
            "nth-internal-workbook-request",
            "nth-client-send-copy-request",
            "validated internal workbook",
        ),
    )
    require_text(
        "ARTIFACT_REGISTRY.md",
        (
            "## Neuron Track Hours artifacts",
            "NTH internal working workbook",
            "NTH client-facing send copy",
        ),
    )
    require_text(
        "SKILLS.md",
        (
            "Neuron Track Hours monthly artifact",
            ".ai/skills/neuron-track-hours-monthly-artifact/SKILL.md",
        ),
    )
    require_text(
        "TRIGGERS.md",
        (
            "NTH domain overlay triggers",
            "`nth-internal-workbook-request`",
            "`nth-client-send-copy-request`",
        ),
    )
    require_text(
        "harness/reports/CURRENT_STATE.md",
        (
            "## Neuron Track Hours domain overlay",
            "two workbook delivery modes",
            "July 2026",
        ),
    )


def main() -> int:
    checks = (
        ("manifest", validate_manifest),
        ("governance dependency", validate_governance_dependency),
        ("July 2026 rule pack", validate_rule_pack),
        ("NTH triggers", validate_triggers),
        ("NTH skill", validate_skill),
        ("human harness surfaces", validate_human_surfaces),
    )
    failures: list[str] = []
    print("Neuron Track Hours Harness Validation")
    print("=" * 39)
    for name, check in checks:
        try:
            check()
        except (NthHarnessValidationError, KeyError, TypeError, ValueError) as exc:
            failures.append(f"{name}: {exc}")
            print(f"[FAIL] {name}: {exc}")
        else:
            print(f"[PASS] {name}")
    if failures:
        print("\nNTH harness validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nNTH harness validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
