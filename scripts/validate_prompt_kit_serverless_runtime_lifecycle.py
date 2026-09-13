#!/usr/bin/env python3
"""Fail-closed validator for Prompt Kit serverless runtime lifecycle planning."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-serverless-runtime-lifecycle.v1.json"
PLAN_PATH = ROOT / "docs" / "PROMPT_KIT_SERVERLESS_RUNTIME_PHASE_PLAN.md"
PARENT_CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-kit-cross-device-access.v1.json"
SCOUT_PATH = ROOT / "harness" / "prompt-topology" / "POST_PHASE_C_STRATEGIC_SCOUT.md"
GAMEPLAY_PATH = ROOT / "docs" / "prompt-kit-preference-gameplay.js"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "prompt-kit-serverless-runtime-lifecycle.yml"

REQUIRED_CAPABILITIES = {
    "local-storage-separation-and-lifecycle",
    "encrypted-pkenc-export-import",
    "cross-device-pairing",
    "serverless-sync-transport",
    "privacy-reducer-runtime",
    "collective-learning-ingestion",
    "network-anonymity",
}
REQUIRED_PHASES = {
    "phase-1-local-lifecycle",
    "phase-2-portable-private-sync",
    "phase-3-serverless-sync-transport",
    "phase-4-local-collective-learning",
    "phase-5-serverless-collective-ingestion",
}
REQUIRED_HEADINGS = (
    "## MISSION",
    "## SOURCE PROMPT DISPOSITION",
    "## CONFLICT RESOLUTION",
    "## IMMEDIATE OWNED SCOPE",
    "## FORBIDDEN SCOPE",
    "## REPOSITORY EVIDENCE REQUIRED",
    "## EXECUTION CONTRACT",
    "## VALIDATION",
    "## DEFERRED DOCUMENTATION BRANCH",
    "## FINAL HANDOFF",
)
VALID_DISPOSITIONS = {
    "included",
    "merged",
    "deferred-to-docs",
    "superseded",
    "rejected-with-reason",
    "unresolved-blocker",
}
EXPECTED_CLEANUP_RUN_POINTS = {
    "application-start",
    "after-local-journal-write",
    "after-reducer-buffer-write",
    "before-network-export-or-upload",
    "after-successful-export-or-acknowledgement",
    "manual-user-clear",
}
EXPECTED_LIMITS = {
    "local_journal": {"max_age_days": 14, "max_bytes": 2097152},
    "privacy_reducer_buffer": {"max_age_days": 30, "max_bytes": 524288, "max_aggregate_keys": 2048},
    "sync_retry_queue": {"max_age_days": 7, "max_bytes": 262144, "max_items": 64},
}
REQUIRED_USER_CONTROLS = {
    "clear_usage_and_local_journal_required",
    "clear_collective_buffer_required",
    "clear_sync_retry_and_polling_state_required",
    "clear_personal_state_must_be_separate",
    "clear_personal_state_confirmation_required",
}
EXPECTED_PHASE4_DEPENDENCY = (
    "phase-1-local-lifecycle plus Prompt Topology Phase C closeout plus resolved P95 "
    "evidence-spine/state-ownership investigation"
)
EXPECTED_PHASE5_DEPENDENCY = "phase-4-local-collective-learning plus network-anonymity investigation"
EXPECTED_STRATEGIC_GATE = (
    "Prompt Topology Phase C closeout integrated and P95 Prompt Execution Evidence Spine/"
    "state-ownership investigation resolved"
)
REQUIRED_WORKFLOW_PATHS = {
    "harness/contracts/prompt-kit-serverless-runtime-lifecycle.v1.json",
    "harness/contracts/prompt-kit-cross-device-access.v1.json",
    "harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md",
    "docs/PROMPT_KIT_SERVERLESS_RUNTIME_PHASE_PLAN.md",
    "docs/prompt-kit-preference-gameplay.js",
    "scripts/validate_prompt_kit_serverless_runtime_lifecycle.py",
    "tests/test_prompt_kit_serverless_runtime_lifecycle.py",
}
REQUIRED_WORKFLOW_COMMANDS = {
    "python scripts/validate_prompt_kit_serverless_runtime_lifecycle.py --summary",
    "python -m unittest tests.test_prompt_kit_serverless_runtime_lifecycle -v",
    "python scripts/validate_prompt_kit_privacy_storage.py --summary",
    "python -m unittest tests.test_prompt_kit_privacy_storage -v",
    "python scripts/validate_prompt_kit_cross_device_access.py --summary",
    "python -m unittest tests.test_prompt_kit_cross_device_access -v",
    "python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check",
}


class LifecycleError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LifecycleError(f"missing required file: {path.relative_to(ROOT).as_posix()}") from exc
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"invalid JSON: {path.relative_to(ROOT).as_posix()}: {exc}") from exc
    if not isinstance(value, dict):
        raise LifecycleError(f"JSON root must be an object: {path.relative_to(ROOT).as_posix()}")
    return value


def _require_exact_keys(value: Any, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LifecycleError(f"{field} must be an object")
    actual = set(value)
    if actual != expected:
        raise LifecycleError(f"{field} keys drifted; missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}")
    return value


def _require_nonempty_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise LifecycleError(f"{field} must be a non-empty list")
    return value


def validate_contract(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != "prompt-kit-serverless-runtime-lifecycle/v1":
        raise LifecycleError("schema version drifted")
    if payload.get("parent_contract") != "harness/contracts/prompt-kit-cross-device-access.v1.json":
        raise LifecycleError("parent contract drifted")
    if payload.get("phase_plan") != "docs/PROMPT_KIT_SERVERLESS_RUNTIME_PHASE_PLAN.md":
        raise LifecycleError("phase plan ownership drifted")

    strategic = payload.get("strategic_dependencies")
    if not isinstance(strategic, dict):
        raise LifecycleError("strategic_dependencies must be an object")
    if strategic.get("post_phase_c_scout") != "harness/prompt-topology/POST_PHASE_C_STRATEGIC_SCOUT.md":
        raise LifecycleError("post-Phase-C strategic scout ownership drifted")
    if strategic.get("required_before_phase_4") != EXPECTED_STRATEGIC_GATE:
        raise LifecycleError("Phase 4 strategic admission gate drifted")

    architecture = payload.get("architecture")
    if not isinstance(architecture, dict):
        raise LifecycleError("architecture must be an object")
    if architecture.get("deployment_model") != "serverless-local-first":
        raise LifecycleError("deployment model must remain serverless-local-first")
    if architecture.get("private_plaintext_authority") != "user-device":
        raise LifecycleError("private plaintext authority must remain user-device")
    if architecture.get("prompt_kit_owned_always_on_server_required") is not False:
        raise LifecycleError("always-on Prompt Kit server must not become required")
    _require_nonempty_list(architecture.get("invariants"), "architecture.invariants")

    horizon = payload.get("runtime_capability_horizon")
    if not isinstance(horizon, list) or len(horizon) != len(REQUIRED_CAPABILITIES):
        raise LifecycleError("runtime capability horizon count drifted")
    ids = {item.get("id") for item in horizon if isinstance(item, dict)}
    if ids != REQUIRED_CAPABILITIES:
        raise LifecycleError(f"runtime capability horizon drifted: {sorted(ids)}")
    statuses = {item["id"]: item.get("status") for item in horizon}
    if statuses.get("network-anonymity") != "investigate-first":
        raise LifecycleError("network anonymity must remain investigate-first until runtime/network proof exists")
    for capability_id, status in statuses.items():
        if capability_id != "network-anonymity" and status != "planned":
            raise LifecycleError(f"{capability_id} must remain planned in this planning contract")

    lifecycle = payload.get("local_storage_lifecycle")
    if not isinstance(lifecycle, dict) or lifecycle.get("cleanup_engine_required") is not True:
        raise LifecycleError("cleanup engine must be required")
    run_points = set(_require_nonempty_list(lifecycle.get("cleanup_run_points"), "cleanup_run_points"))
    if run_points != EXPECTED_CLEANUP_RUN_POINTS:
        raise LifecycleError("cleanup run points drifted")

    stores = lifecycle.get("stores")
    required_stores = {
        "personal_state",
        "local_journal",
        "privacy_reducer_buffer",
        "sync_retry_queue",
        "polling_state",
        "secrets",
    }
    stores = _require_exact_keys(stores, required_stores, "local_storage_lifecycle.stores")
    personal = stores["personal_state"]
    if personal.get("automatic_purge") is not False or personal.get("retention") != "until-user-delete":
        raise LifecycleError("Personal State must never be automatically purged")
    if personal.get("user_clear_required") is not True:
        raise LifecycleError("Personal State must have an explicit user-clear path")

    secrets = stores["secrets"]
    if secrets.get("automatic_purge") is not False or secrets.get("telemetry_cleanup_may_delete") is not False:
        raise LifecycleError("secret/recovery material must remain outside telemetry auto-cleanup")
    if secrets.get("retention") != "until-user-revocation-or-rotation":
        raise LifecycleError("secret/recovery retention ownership drifted")

    for store_name, expected in EXPECTED_LIMITS.items():
        store = stores[store_name]
        for key, expected_value in expected.items():
            if store.get(key) != expected_value:
                raise LifecycleError(f"{store_name}.{key} drifted")
        _require_nonempty_list(store.get("delete_on"), f"{store_name}.delete_on")

    polling = stores["polling_state"]
    if polling.get("max_age_hours") != 24:
        raise LifecycleError("polling state max age must remain 24 hours")
    for field in ("persistent_request_history_allowed", "persistent_response_history_allowed", "persistent_cycle_log_allowed"):
        if polling.get(field) is not False:
            raise LifecycleError(f"polling_state.{field} must remain false")
    if polling.get("max_persistent_cursor_records") != 1:
        raise LifecycleError("polling state may persist at most one cursor record")
    polling_delete = set(_require_nonempty_list(polling.get("delete_on"), "polling_state.delete_on"))
    if "age-expiry" not in polling_delete:
        raise LifecycleError("polling state must delete on age expiry")

    pressure = lifecycle.get("storage_pressure_policy")
    if not isinstance(pressure, dict):
        raise LifecycleError("storage_pressure_policy must be an object")
    must_never = set(_require_nonempty_list(pressure.get("must_never_auto_delete"), "storage_pressure_policy.must_never_auto_delete"))
    if "Personal State" not in must_never:
        raise LifecycleError("storage pressure policy must protect Personal State")

    controls = _require_exact_keys(lifecycle.get("user_controls"), REQUIRED_USER_CONTROLS, "local_storage_lifecycle.user_controls")
    if not all(value is True for value in controls.values()):
        raise LifecycleError("all lifecycle user-clear controls must remain required")

    telemetry = payload.get("polling_and_telemetry_policy")
    if not isinstance(telemetry, dict):
        raise LifecycleError("polling_and_telemetry_policy must be an object")
    if telemetry.get("network_polling_default") != "disabled-until-transport-phase":
        raise LifecycleError("network polling must remain disabled until transport phase")
    if telemetry.get("telemetry_write_requires_cleanup_pass") is not True:
        raise LifecycleError("telemetry writes must require a cleanup pass")
    if telemetry.get("delete_local_batch_after_positive_acknowledgement") is not True:
        raise LifecycleError("acknowledged local batches must be deleted")
    if telemetry.get("persist_poll_request_or_response_bodies") is not False:
        raise LifecycleError("poll request/response bodies must not be persisted")
    if telemetry.get("persist_exact_poll_timestamps") is not False:
        raise LifecycleError("exact poll timestamps must not be persisted")

    phases = payload.get("phase_map")
    phases = _require_exact_keys(phases, REQUIRED_PHASES, "phase_map")
    if phases["phase-1-local-lifecycle"].get("status") != "planned":
        raise LifecycleError("Phase 1 must remain the immediate planned implementation")
    if phases["phase-2-portable-private-sync"].get("dependency") != "phase-1-local-lifecycle":
        raise LifecycleError("Phase 2 dependency drifted")
    if phases["phase-3-serverless-sync-transport"].get("dependency") != "phase-2-portable-private-sync":
        raise LifecycleError("Phase 3 dependency drifted")
    if phases["phase-4-local-collective-learning"].get("dependency") != EXPECTED_PHASE4_DEPENDENCY:
        raise LifecycleError("Phase 4 dependency drifted")
    forbidden_phase4 = set(phases["phase-4-local-collective-learning"].get("forbidden_scope", []))
    if "new route/usage/outcome event model before evidence-spine ownership is resolved" not in forbidden_phase4:
        raise LifecycleError("Phase 4 must forbid a duplicate evidence event model before P95 resolution")
    if phases["phase-5-serverless-collective-ingestion"].get("dependency") != EXPECTED_PHASE5_DEPENDENCY:
        raise LifecycleError("Phase 5 dependency drifted")

    collision = payload.get("known_runtime_collision")
    if not isinstance(collision, dict) or collision.get("pull_request") != 242:
        raise LifecycleError("known runtime collision with PR #242 must remain tracked until reconciled")
    if collision.get("observed_store") != "promptKit.usage.v1":
        raise LifecycleError("PR #242 observed store identity drifted")

    return {
        "capabilities": len(ids),
        "phases": len(phases),
        "cleanup_run_points": len(run_points),
        "bounded_disposable_stores": 4,
        "protected_stores": 2,
    }


def validate_plan() -> None:
    try:
        text = PLAN_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LifecycleError("missing durable serverless runtime phase plan") from exc
    last_index = -1
    for heading in REQUIRED_HEADINGS:
        index = text.find(heading)
        if index < 0:
            raise LifecycleError(f"phase plan missing required heading: {heading}")
        if index <= last_index:
            raise LifecycleError(f"phase plan heading order drifted: {heading}")
        last_index = index
    for capability in REQUIRED_CAPABILITIES:
        if capability not in text:
            raise LifecycleError(f"phase plan lost capability: {capability}")
    for disposition in VALID_DISPOSITIONS:
        if disposition not in text and disposition not in {"rejected-with-reason", "unresolved-blocker"}:
            raise LifecycleError(f"source disposition vocabulary missing from durable plan: {disposition}")
    required_phrases = (
        "Personal State survives automatic cleanup",
        "stop telemetry/sync writes",
        "promptKit.usage.v1",
        "No separate documentation PR is required",
        "P95 evidence-spine/state-ownership",
        "Phase C closeout",
    )
    for phrase in required_phrases:
        if phrase not in text:
            raise LifecycleError(f"phase plan lost required lifecycle concept: {phrase}")


def validate_parent_contract() -> None:
    parent = _load_json(PARENT_CONTRACT_PATH)
    architecture = parent.get("data_plane_architecture", {})
    planes = architecture.get("planes", {}) if isinstance(architecture, dict) else {}
    if set(planes) != {"prompt_canon", "personal_state", "private_sync", "collective_learning"}:
        raise LifecycleError("parent four-plane privacy/storage contract is missing or drifted")
    backend = parent.get("v1_backend_policy")
    if not isinstance(backend, dict) or backend.get("prompt_kit_owned_backend_required") is not False:
        raise LifecycleError("parent contract no-backend-required invariant drifted")


def validate_strategy_dependency() -> None:
    try:
        text = SCOUT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LifecycleError("missing post-Phase-C strategic scout required by current main") from exc
    for phrase in (
        "Recommended next owner:** P95",
        "Prompt execution evidence-spine/state-ownership architecture before Phase D Passive Learning",
        "Phase C closeout integration is a prerequisite",
    ):
        if phrase not in text:
            raise LifecycleError(f"post-Phase-C strategic dependency drifted: {phrase}")


def _strip_js_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    quote: str | None = None
    escaped = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if quote is not None:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] != "\n":
                i += 1
            out.append("\n")
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _js_function_body(text: str, name: str) -> str | None:
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{", text)
    if not match:
        return None
    open_index = match.end() - 1
    depth = 0
    quote: str | None = None
    escaped = False
    i = open_index
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            i += 1
            continue
        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : i]
        i += 1
    return None


def validate_gameplay_if_present() -> None:
    if not GAMEPLAY_PATH.exists():
        return
    raw = GAMEPLAY_PATH.read_text(encoding="utf-8")
    text = _strip_js_comments(raw)
    if "promptKit.usage.v1" not in text:
        return

    load_bound = re.search(r"next\.recent\s*=\s*[^;\n]*\.slice\(\s*0\s*,\s*12\s*\)", text)
    write_bound = re.search(r"state\.recent\s*=\s*[^;\n]*\.slice\(\s*0\s*,\s*12\s*\)", text)
    if not load_bound or not write_bound:
        raise LifecycleError(
            "prompt-kit-preference-gameplay must assign the 12-item slice into both loaded and persisted recent state"
        )

    body = _js_function_body(text, "clearUsageData")
    if body is None:
        raise LifecycleError("prompt-kit-preference-gameplay usage storage lacks clearUsageData()")
    compact_body = re.sub(r"\s+", "", _strip_js_comments(body))
    if not (
        "root.localStorage.removeItem(STORAGE_KEY)" in compact_body
        or "localStorage.removeItem(STORAGE_KEY)" in compact_body
    ):
        raise LifecycleError("clearUsageData() must delete the promptKit.usage.v1 storage key")
    if "state=emptyState()" not in compact_body:
        raise LifecycleError("clearUsageData() must clear the in-memory usage state")

    exported = re.search(r"PromptKitPreferenceGameplay\s*=\s*\{[^}]*clearUsageData\s*:\s*clearUsageData", text, re.S)
    direct_binding = re.search(
        r"querySelector\([^)]*data-clear-usage[^)]*\)\.addEventListener\(\s*['\"]click['\"]\s*,\s*clearUsageData\s*\)",
        text,
    )
    wrapper_binding = re.search(
        r"querySelector\([^)]*data-clear-usage[^)]*\)\.addEventListener\(\s*['\"]click['\"]\s*,\s*function\s*\(\s*\)\s*\{\s*clearUsageData\(\)\s*\}\s*\)",
        text,
    )
    if not exported or not (direct_binding or wrapper_binding):
        raise LifecycleError(
            "clearUsageData() must be exported and wired to a data-clear-usage user control"
        )


def _workflow_event_paths(text: str, event: str) -> set[str]:
    lines = text.splitlines()
    event_marker = f"  {event}:"
    try:
        event_index = next(i for i, line in enumerate(lines) if line == event_marker)
    except StopIteration as exc:
        raise LifecycleError(f"lifecycle workflow missing event: {event}") from exc
    paths_index: int | None = None
    for i in range(event_index + 1, len(lines)):
        line = lines[i]
        if line and len(line) - len(line.lstrip()) <= 2:
            break
        if line == "    paths:":
            paths_index = i
            break
    if paths_index is None:
        raise LifecycleError(f"lifecycle workflow missing {event}.paths")
    paths: set[str] = set()
    for line in lines[paths_index + 1 :]:
        if line and len(line) - len(line.lstrip()) <= 4:
            break
        if line.startswith("      - "):
            paths.add(line[len("      - ") :].strip().strip("'\""))
    return paths


def _workflow_run_commands(text: str) -> set[str]:
    lines = text.splitlines()
    commands: set[str] = set()
    for index, line in enumerate(lines):
        if line.strip() != "run: |":
            continue
        indent = len(line) - len(line.lstrip())
        for child in lines[index + 1 :]:
            if child.strip() and len(child) - len(child.lstrip()) <= indent:
                break
            stripped = child.strip()
            if stripped and not stripped.startswith("#"):
                commands.add(stripped)
    return commands


def validate_workflow() -> None:
    try:
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LifecycleError("missing lifecycle workflow") from exc
    for event in ("pull_request", "push"):
        paths = _workflow_event_paths(text, event)
        missing = sorted(REQUIRED_WORKFLOW_PATHS - paths)
        if missing:
            raise LifecycleError(f"lifecycle workflow {event}.paths missing: {missing}")
    commands = _workflow_run_commands(text)
    missing_commands = sorted(REQUIRED_WORKFLOW_COMMANDS - commands)
    if missing_commands:
        raise LifecycleError(f"lifecycle workflow missing active run commands: {missing_commands}")


def validate() -> dict[str, Any]:
    report = validate_contract(_load_json(CONTRACT_PATH))
    validate_parent_contract()
    validate_plan()
    validate_strategy_dependency()
    validate_gameplay_if_present()
    validate_workflow()
    return {"status": "PASS", **report}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate()
    except (LifecycleError, FileNotFoundError) as exc:
        print(f"prompt-kit-serverless-runtime-lifecycle: FAIL: {exc}")
        return 1
    if args.summary:
        print(
            "prompt-kit-serverless-runtime-lifecycle: PASS "
            f"({report['capabilities']} capabilities, {report['phases']} phases, "
            f"{report['bounded_disposable_stores']} bounded disposable stores, "
            f"{report['protected_stores']} protected stores, "
            f"{report['cleanup_run_points']} cleanup run points)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
