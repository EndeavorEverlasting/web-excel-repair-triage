#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-feedback-afk-routing.v1.json"
CAPABILITIES = ROOT / "harness" / "capabilities.v1.json"
TRIGGERS = ROOT / "harness" / "triggers.v1.json"
WORKFLOWS = ROOT / "harness" / "workflows.v1.json"
MANIFEST = ROOT / "harness" / "manifest.v1.json"
SKILL = ROOT / ".ai" / "skills" / "prompt-kit-feedback-afk-routing" / "SKILL.md"
ROUTER = ROOT / "scripts" / "prompt_kit_afk_signal_router.py"
BRIDGE = ROOT / "scripts" / "prompt_kit_feedback_bridge.py"
WEB_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
FEEDBACK_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-feedback-hook.yml"
REPORT_SCHEMA = "prompt-kit-feedback-afk-routing-validation/v1"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def one(items: list[dict[str, Any]], key: str, value: str, label: str) -> dict[str, Any]:
    matches = [item for item in items if item.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label} {value}, found {len(matches)}")
    return matches[0]


def validate() -> dict[str, Any]:
    contract = load_json(CONTRACT)
    capabilities = load_json(CAPABILITIES)
    triggers = load_json(TRIGGERS)
    workflows = load_json(WORKFLOWS)
    manifest = load_json(MANIFEST)
    skill = SKILL.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    bridge = BRIDGE.read_text(encoding="utf-8")
    web_workflow = WEB_WORKFLOW.read_text(encoding="utf-8")
    feedback_workflow = FEEDBACK_WORKFLOW.read_text(encoding="utf-8")

    errors: list[str] = []
    checks: dict[str, bool] = {}

    def check(name: str, condition: bool, message: str) -> None:
        checks[name] = bool(condition)
        if not condition:
            errors.append(message)

    check(
        "contract_schema",
        contract.get("schema_version") == "prompt-kit-feedback-afk-routing/v1",
        "feedback AFK routing contract schema mismatch",
    )
    owners = contract.get("semantic_owners", {})
    check("p99_owner", owners.get("explicit_feedback") == "P99", "P99 must own explicit feedback semantics")
    check("p115_owner", owners.get("afk_coordination") == "P115", "P115 must own AFK coordination semantics")
    check(
        "p105_owner",
        owners.get("promotion") == "P105/pr-floor-integration",
        "P105/pr-floor-integration must own promotion",
    )
    check(
        "no_second_scheduler",
        contract.get("wakeups", {}).get("second_scheduler_allowed") is False,
        "contract must forbid a second scheduler",
    )
    check(
        "raw_comment_private",
        contract.get("privacy", {}).get("raw_comment_provider_dispatch") is False,
        "raw written feedback must not be provider-dispatched",
    )

    bridge_contract = contract.get("surfaces", {}).get("private_bridge", {})
    check(
        "bridge_owner_path",
        bridge_contract.get("path") == "scripts/prompt_kit_feedback_bridge.py",
        "private bridge contract path drift",
    )
    bridge_forbidden = set(bridge_contract.get("forbidden", []))
    for required in (
        "pull-request merge authority",
        "worker scheduling loop",
        "raw written feedback in provider dispatch payloads",
        "browser credential storage",
    ):
        check(
            f"bridge_contract_forbids_{required[:16].replace(' ', '_')}",
            required in bridge_forbidden,
            f"private bridge contract lost forbidden boundary: {required}",
        )

    try:
        capability = one(capabilities.get("capabilities", []), "id", "prompt-kit-feedback-afk-routing", "capability")
        check(
            "capability_skill",
            capability.get("skill") == ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md",
            "feedback AFK capability must route to focused skill",
        )
        check(
            "capability_router",
            capability.get("implementation", {}).get("path") == "scripts/prompt_kit_afk_signal_router.py",
            "feedback AFK capability must use one-shot signal router",
        )
    except ValueError as exc:
        errors.append(str(exc))

    try:
        trigger = one(triggers.get("triggers", []), "id", "prompt-kit-actionable-feedback", "trigger")
        check(
            "trigger_capability",
            trigger.get("capability_id") == "prompt-kit-feedback-afk-routing",
            "actionable feedback trigger must route to focused capability",
        )
    except ValueError as exc:
        errors.append(str(exc))

    try:
        workflow = one(workflows.get("workflows", []), "id", "prompt-kit-feedback-afk-routing", "workflow")
        forbidden = set(workflow.get("forbidden_scope", []))
        check("workflow_forbids_merge", "direct PR merge" in forbidden, "AFK routing workflow must forbid direct PR merge")
        check(
            "workflow_forbids_polling",
            "second scheduler or infinite polling loop" in forbidden,
            "AFK routing workflow must forbid a second scheduler",
        )
    except ValueError as exc:
        errors.append(str(exc))

    domain = manifest.get("domain_contracts", {}).get("prompt_kit_feedback_afk_routing", {})
    check(
        "manifest_contract",
        domain.get("contract") == "harness/contracts/prompt-kit-feedback-afk-routing.v1.json",
        "root manifest must register AFK routing contract",
    )
    check(
        "manifest_validator",
        domain.get("validator") == "scripts/validate_prompt_kit_feedback_afk_routing.py",
        "root manifest must register AFK routing validator",
    )
    check(
        "manifest_skill",
        ".ai/skills/prompt-kit-feedback-afk-routing/SKILL.md" in manifest.get("skills", []),
        "root manifest must register AFK routing skill",
    )

    for heading in (
        "## Trigger",
        "## Required inputs",
        "## Outputs",
        "## Procedure",
        "## Guardrails",
        "## Validation",
        "## Proof ceiling",
    ):
        check(
            f"skill_{heading[3:].lower().replace(' ', '_')}",
            heading in skill,
            f"skill missing required heading: {heading}",
        )

    for marker in (
        "time.sleep(",
        "--poll-seconds",
        "gh api",
        "gh pr",
        "/merge\"",
        "GITHUB_TOKEN",
    ):
        check(
            f"router_bans_{marker.replace(' ', '_')}",
            marker not in router,
            f"one-shot AFK router contains forbidden provider/scheduler marker: {marker}",
        )
    check(
        "router_uses_p115",
        "P115 AFK Feedback-Driven Development Loop Executor" in router,
        "router work request must name P115",
    )
    check("router_no_shell", "shell=True" not in router, "router must not invoke workers through shell=True")

    for marker in (
        "prompt_kit_afk_local_loop",
        "PROMPT_KIT_AFK_WORKER_COMMAND",
        "one_pass(",
        "time.sleep(",
        "--poll-seconds",
        "gh pr",
        '"/merge"',
    ):
        check(
            f"bridge_bans_{marker.replace(' ', '_')}",
            marker not in bridge,
            f"private bridge contains forbidden worker/scheduler/merge marker: {marker}",
        )
    required_bridge_markers = (
        "sync_authorized",
        "canonical_prompt_ids",
        "load_prompt_kit_registry",
        "_validate_timestamp",
        "default_spool_root",
        "LOCALAPPDATA",
        "XDG_STATE_HOME",
        "bridge-local:",
        "hashlib.sha256(event_id.encode",
        "0o700",
        "0o600",
        "provider_receipt",
        "retry_pending_receipts",
        "PROVIDER_WAKEUP_DISABLED",
        "PROVIDER_CONSUMER_UNREGISTERED",
        "PROVIDER_TIMEOUT_SECONDS",
        "pending receipt repository mismatch",
        "repository_dispatch:",
    )
    for required in required_bridge_markers:
        check(
            f"bridge_requires_{required[:22].replace(' ', '_')}",
            required in bridge,
            f"private bridge missing required transport/privacy marker: {required}",
        )
    check(
        "bridge_raw_feedback_not_repo_default",
        "Outputs/prompt-kit-feedback-spool" not in bridge,
        "raw feedback spool must not default inside the repository",
    )
    check(
        "bridge_provider_receipt_no_raw_comment",
        '"comment":' not in bridge.split("def provider_receipt", 1)[1].split("def _same_receipt_shape", 1)[0],
        "provider receipt must not include raw written feedback",
    )
    check(
        "bridge_default_wakeup_off",
        "enabled: bool = False" in bridge and "provider_wakeup: bool = False" in bridge,
        "private bridge provider wakeup must be opt-in",
    )
    check(
        "bridge_consumer_gate_precedes_gh",
        bridge.find("PROVIDER_CONSUMER_UNREGISTERED") < bridge.find('"gh",\n                "api"'),
        "provider consumer gate must precede gh dispatch",
    )
    check(
        "bridge_timeout_is_bounded",
        "timeout=PROVIDER_TIMEOUT_SECONDS" in bridge and "except subprocess.TimeoutExpired" in bridge,
        "provider dispatch must have a finite timeout and retry-pending timeout handling",
    )

    check(
        "web_workflow_read_only",
        "contents: write" not in web_workflow and "contents: read" in web_workflow,
        "Prompt Kit web workflow must be read-only",
    )
    for stale in (
        "P122 Gemini regression strengthening",
        "feat/gemini-youtube-ingestion-prompt-20260827",
        "git push origin",
    ):
        check(
            f"web_workflow_retires_{stale[:12]}",
            stale not in web_workflow,
            f"Prompt Kit web workflow retains stale writer behavior: {stale}",
        )
    for required in (
        "scripts/serve_prompt_kit_portable.py",
        "scripts/validate_prompt_kit_portability.py",
        "tests/test_prompt_kit_portability.py",
        "tests/test_prompt_kit_portability_regressions.py",
        "docs/prompt-kit-favorites-portability.js",
        "tests.test_prompt_kit_feedback_bridge",
        "Build portable Prompt Kit runtime artifact",
        "Validate portable Favorites and harness discipline",
        "prompt-kit-portable-runtime",
    ):
        check(
            f"web_workflow_portability_{required[:16]}",
            required in web_workflow,
            f"Prompt Kit web workflow lost required contract marker: {required}",
        )

    check(
        "feedback_hook_read_only",
        "contents: write" not in feedback_workflow and "contents: read" in feedback_workflow,
        "feedback hook must remain read-only",
    )

    return {
        "schema_version": REPORT_SCHEMA,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "proof_ceiling": "Static repository boundary and routing proof only; browser loopback, configured worker, provider consumer activation, review, and promotion require separate observed proof.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Prompt Kit feedback AFK routing validation failed: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary or not args.output:
        print(
            json.dumps(
                {"status": report["status"], "checks": len(report["checks"]), "errors": report["errors"]},
                sort_keys=True,
            )
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
