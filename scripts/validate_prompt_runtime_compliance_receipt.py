from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "harness" / "contracts" / "prompt-runtime-compliance-receipt.schema.v1.json"
CONTRACT_PATH = ROOT / "harness" / "contracts" / "prompt-runtime-compliance.v1.json"
TAXONOMY_PATH = ROOT / "harness" / "contracts" / "execution-boundary-taxonomy.v1.json"
DEFAULT_RECEIPT = ROOT / "harness" / "evals" / "runtime-compliance" / "contract-fixtures" / "receipt.positive.v1.json"

STATE_RANK = {
    "PLANNED_DESIGNED": 0,
    "TRACKED": 1,
    "IMPLEMENTED": 2,
    "WIRED_REACHABLE": 3,
    "VALIDATED": 4,
    "INTEGRATED": 5,
    "DEPLOYED": 6,
    "OBSERVED": 7,
}
MATERIAL = {"MATERIAL", "CRITICAL"}
FAILURE_SEVERITIES = {"CRITICAL", "HIGH"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


SCHEMA = load_json(SCHEMA_PATH)
CONTRACT = load_json(CONTRACT_PATH)
TAXONOMY = load_json(TAXONOMY_PATH)
RULES = {row["rule_id"]: row for row in CONTRACT["rules"]}
RULE_IDS = set(RULES)
CANONICAL_CLASSES = {
    (family["id"], klass["id"])
    for family in TAXONOMY["families"]
    for klass in family["classes"]
}
FORMAT_CHECKER = FormatChecker()


def _time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _finding(
    rule_id: str,
    result: str,
    subject: str,
    message: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    rule = RULES[rule_id]
    return {
        "rule_id": rule_id,
        "severity": rule["severity"],
        "result": result,
        "subject": subject,
        "message": message,
        "evidence_refs": sorted(set(evidence_refs or [])),
    }


def _pass(rule_id: str, subject: str, message: str, refs: list[str] | None = None) -> dict[str, Any]:
    return _finding(rule_id, "PASS", subject, message, refs)


def _fail(rule_id: str, subject: str, message: str, refs: list[str] | None = None) -> dict[str, Any]:
    return _finding(rule_id, "FAIL", subject, message, refs)


def _na(rule_id: str, subject: str, message: str) -> dict[str, Any]:
    return _finding(rule_id, "NOT_APPLICABLE", subject, message)


def _unknown(rule_id: str, subject: str, message: str, refs: list[str] | None = None) -> dict[str, Any]:
    return _finding(rule_id, "UNKNOWN", subject, message, refs)


def _monotonic(values: list[int]) -> bool:
    return len(values) == len(set(values)) and values == sorted(values)


def _rank(value: str | None) -> int | None:
    if value is None:
        return None
    return STATE_RANK.get(value)


def _all_evidence_refs(receipt: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    rows: list[tuple[str, str, list[str]]] = []
    for event in receipt["boundary_events"]:
        rows.append(("boundary", event["boundary_event_id"], event["evidence_refs"]))
    for action in receipt["actions"]:
        rows.append(("action", action["action_id"], action["evidence_refs"]))
    for violation in receipt["violations"]:
        rows.append(("violation", violation["violation_id"], violation["evidence_refs"]))
    for check in receipt["proof"]["checks"]:
        rows.append(("check", check["check_id"], check["evidence_refs"]))
    return rows


def _semantic_context(receipt: dict[str, Any]) -> dict[str, Any]:
    boundaries = {row["boundary_event_id"]: row for row in receipt["boundary_events"]}
    actions = {row["action_id"]: row for row in receipt["actions"]}
    violations = {row["violation_id"]: row for row in receipt["violations"]}
    evidence = {row["evidence_id"]: row for row in receipt["evidence"]}
    rule_violations = {row["rule_id"]: row for row in receipt["violations"]}
    material = [row for row in receipt["boundary_events"] if row["materiality"] in MATERIAL]
    return {
        "boundaries": boundaries,
        "actions": actions,
        "violations": violations,
        "evidence": evidence,
        "rule_violations": rule_violations,
        "material": material,
    }


def _evaluate_nonaggregate(receipt: dict[str, Any]) -> list[dict[str, Any]]:
    ctx = _semantic_context(receipt)
    boundaries = ctx["boundaries"]
    actions = ctx["actions"]
    evidence = ctx["evidence"]
    findings: dict[str, dict[str, Any]] = {
        rule_id: _na(rule_id, "receipt", "Trigger conditions were not met.")
        for rule_id in RULE_IDS
    }

    def setf(row: dict[str, Any]) -> None:
        findings[row["rule_id"]] = row

    ids = (
        [row["boundary_event_id"] for row in receipt["boundary_events"]]
        + [row["action_id"] for row in receipt["actions"]]
        + [row["violation_id"] for row in receipt["violations"]]
        + [row["evidence_id"] for row in receipt["evidence"]]
    )
    setf(
        _pass("PRCR.ID.UNIQUE", "receipt", "Trace object identifiers are unique.")
        if len(ids) == len(set(ids))
        else _fail("PRCR.ID.UNIQUE", "receipt", "Trace object identifiers collide.")
    )

    bseq = [row["sequence"] for row in receipt["boundary_events"]]
    setf(
        _na("PRCR.SEQUENCE.BOUNDARY_MONOTONIC", "boundary_events", "Fewer than two boundary events.")
        if len(bseq) < 2
        else (
            _pass("PRCR.SEQUENCE.BOUNDARY_MONOTONIC", "boundary_events", "Boundary sequences are unique and increasing.")
            if _monotonic(bseq)
            else _fail("PRCR.SEQUENCE.BOUNDARY_MONOTONIC", "boundary_events", "Boundary sequence is duplicated or non-monotonic.")
        )
    )
    aseq = [row["sequence"] for row in receipt["actions"]]
    setf(
        _na("PRCR.SEQUENCE.ACTION_MONOTONIC", "actions", "Fewer than two actions.")
        if len(aseq) < 2
        else (
            _pass("PRCR.SEQUENCE.ACTION_MONOTONIC", "actions", "Action sequences are unique and increasing.")
            if _monotonic(aseq)
            else _fail("PRCR.SEQUENCE.ACTION_MONOTONIC", "actions", "Action sequence is duplicated or non-monotonic.")
        )
    )

    unresolved: list[str] = []
    type_errors: list[str] = []
    for kind, owner, refs in _all_evidence_refs(receipt):
        for ref in refs:
            if ref not in evidence:
                unresolved.append(f"{kind}:{owner}->{ref}")
    for action in receipt["actions"]:
        event_id = action["boundary_event_id"]
        if event_id is not None and event_id not in boundaries:
            unresolved.append(f"action:{action['action_id']}->boundary:{event_id}")
        for field in ("readback_of_action_id", "retry_of_action_id"):
            ref = action.get(field)
            if ref is not None and ref not in actions:
                unresolved.append(f"action:{action['action_id']}->{field}:{ref}")
    for event in receipt["boundary_events"]:
        first_id = event["recovery_sprint"].get("first_executable_action_id")
        if first_id is not None and first_id not in actions:
            unresolved.append(f"boundary:{event['boundary_event_id']}->action:{first_id}")
    regression_ids = set(receipt["regression_linkage"]["regression_link_ids"])
    for violation in receipt["violations"]:
        link = violation.get("regression_link_id")
        if link is not None and link not in regression_ids:
            unresolved.append(f"violation:{violation['violation_id']}->regression:{link}")
    setf(
        _pass("PRCR.REF.RESOLVES", "receipt", "All internal references resolve.")
        if not unresolved
        else _fail("PRCR.REF.RESOLVES", "receipt", "Unresolved internal references: " + ", ".join(unresolved[:8]))
    )
    setf(
        _pass("PRCR.REF.TYPE_SAFE", "receipt", "Resolved references point to the required trace object classes.")
        if not type_errors and not unresolved
        else _fail("PRCR.REF.TYPE_SAFE", "receipt", "Reference type safety cannot be established while references are unresolved.")
    )

    start = _time(receipt["run"]["started_at"])
    end = _time(receipt["run"]["ended_at"])
    inside = start is not None and end is not None and start <= end
    if inside:
        for event in receipt["boundary_events"]:
            occurred = _time(event["occurred_at"])
            if occurred is None or occurred < start or occurred > end:
                inside = False
                break
        for action in receipt["actions"]:
            started = _time(action["started_at"])
            completed = _time(action["completed_at"])
            if started is None or started < start or started > end:
                inside = False
                break
            if completed is not None and completed > end:
                inside = False
                break
    setf(
        _pass("PRCR.TIME.RUN_ORDER", "run", "Run and ordinary trace timestamps are ordered inside the run window.")
        if inside
        else _fail("PRCR.TIME.RUN_ORDER", "run", "Run or trace timestamps are out of order.")
    )
    bad_action_times = [
        action["action_id"]
        for action in receipt["actions"]
        if action["completed_at"] is not None
        and _time(action["started_at"]) > _time(action["completed_at"])
    ]
    setf(
        _na("PRCR.TIME.ACTION_ORDER", "actions", "No completed actions.")
        if not any(action["completed_at"] is not None for action in receipt["actions"])
        else (
            _pass("PRCR.TIME.ACTION_ORDER", "actions", "Completed actions start no later than completion.")
            if not bad_action_times
            else _fail("PRCR.TIME.ACTION_ORDER", "actions", "Action time order failed for " + ", ".join(bad_action_times))
        )
    )

    fallback = [row for row in receipt["boundary_events"] if row["classification_status"] == "FALLBACK_UNCLASSIFIED"]
    setf(
        _na("PRCR.BOUNDARY.UNCLASSIFIED_FALLBACK", "boundary_events", "No fallback-unclassified boundary.")
        if not fallback
        else (
            _pass("PRCR.BOUNDARY.UNCLASSIFIED_FALLBACK", "boundary_events", "Fallback boundaries use the canonical unknown class and materiality.")
            if all(
                row.get("class_id") == "UE_UNCLASSIFIED_MATERIAL_BOUNDARY"
                and row["materiality"] in MATERIAL
                for row in fallback
            )
            else _fail("PRCR.BOUNDARY.UNCLASSIFIED_FALLBACK", "boundary_events", "Fallback boundary did not use UE_UNCLASSIFIED_MATERIAL_BOUNDARY with material severity.")
        )
    )
    canonical = [row for row in receipt["boundary_events"] if row["classification_status"] == "CANONICAL"]
    invalid_classes = [
        row["boundary_event_id"]
        for row in canonical
        if (row.get("family_id"), row.get("class_id")) not in CANONICAL_CLASSES
    ]
    setf(
        _na("PRCR.BOUNDARY.CANONICAL_CLASS", "boundary_events", "No canonical boundary.")
        if not canonical
        else (
            _pass("PRCR.BOUNDARY.CANONICAL_CLASS", "boundary_events", "Canonical boundary classes resolve in the pinned taxonomy.")
            if not invalid_classes
            else _fail("PRCR.BOUNDARY.CANONICAL_CLASS", "boundary_events", "Unknown canonical class on " + ", ".join(invalid_classes))
        )
    )

    material = ctx["material"]
    pending = [row["boundary_event_id"] for row in material if row["publication_ack"] == "PENDING"]
    setf(
        _na("PRCR.BOUNDARY.MATERIAL_PUBLICATION", "boundary_events", "No material boundary.")
        if not material
        else (
            _pass("PRCR.BOUNDARY.MATERIAL_PUBLICATION", "boundary_events", "Every material boundary has non-pending publication state.")
            if not pending or receipt["terminal"]["state"] == "HARD_TERMINATED_SYNTHETIC"
            else _fail("PRCR.BOUNDARY.MATERIAL_PUBLICATION", "boundary_events", "Material boundary publication remains pending: " + ", ".join(pending))
        )
    )
    missing_checkpoint = [
        row["boundary_event_id"]
        for row in material
        if row["last_proven_checkpoint"] is None or not row["evidence_refs"]
    ]
    setf(
        _na("PRCR.BOUNDARY.CHECKPOINT_REQUIRED", "boundary_events", "No material boundary.")
        if not material
        else (
            _pass("PRCR.BOUNDARY.CHECKPOINT_REQUIRED", "boundary_events", "Material boundaries retain an evidence-backed checkpoint.")
            if not missing_checkpoint
            else _fail("PRCR.BOUNDARY.CHECKPOINT_REQUIRED", "boundary_events", "Missing evidence-backed checkpoint: " + ", ".join(missing_checkpoint))
        )
    )

    terminal_state = receipt["terminal"]["state"]
    unfinished = terminal_state not in {"COMPLETE", "HARD_TERMINATED_SYNTHETIC", "EXPLICIT_OPERATOR_CANCELLATION"}
    recovery_required_events = [row for row in material if unfinished]
    wrong_required = [
        row["boundary_event_id"]
        for row in recovery_required_events
        if row["recovery_sprint"]["required"] is not True
    ]
    setf(
        _na("PRCR.BOUNDARY.RECOVERY_REQUIRED", "boundary_events", "No material unfinished boundary requires recovery.")
        if not recovery_required_events
        else (
            _pass("PRCR.BOUNDARY.RECOVERY_REQUIRED", "boundary_events", "Material unfinished boundaries require a primary recovery sprint.")
            if not wrong_required
            else _fail("PRCR.BOUNDARY.RECOVERY_REQUIRED", "boundary_events", "Recovery sprint requirement missing for " + ", ".join(wrong_required))
        )
    )

    opened_fail: list[str] = []
    required_fields = (
        "sprint_id", "scope", "outcome", "first_executable_action_id",
        "completion_gate", "return_condition",
    )
    for row in recovery_required_events:
        sprint = row["recovery_sprint"]
        if not sprint["opened"] or any(sprint.get(field) in (None, "") for field in required_fields):
            opened_fail.append(row["boundary_event_id"])
    setf(
        _na("PRCR.BOUNDARY.RECOVERY_OPENED", "boundary_events", "No required recovery sprint.")
        if not recovery_required_events
        else (
            _pass("PRCR.BOUNDARY.RECOVERY_OPENED", "boundary_events", "Required recovery sprints are opened with executable metadata.")
            if not opened_fail
            else _fail("PRCR.BOUNDARY.RECOVERY_OPENED", "boundary_events", "Required recovery sprint not fully opened: " + ", ".join(opened_fail))
        )
    )

    opened = [row for row in receipt["boundary_events"] if row["recovery_sprint"]["opened"]]
    preserve_fail = [
        row["boundary_event_id"]
        for row in opened
        if row["recovery_sprint"].get("preserves_parent_outcome") is not True
    ]
    setf(
        _na("PRCR.BOUNDARY.PRESERVE_OUTCOME", "boundary_events", "No opened recovery sprint.")
        if not opened
        else (
            _pass("PRCR.BOUNDARY.PRESERVE_OUTCOME", "boundary_events", "Recovery sprints preserve the parent outcome.")
            if not preserve_fail
            else _fail("PRCR.BOUNDARY.PRESERVE_OUTCOME", "boundary_events", "Recovery outcome preservation not proven for " + ", ".join(preserve_fail))
        )
    )

    first_resolve_fail: list[str] = []
    first_progress_fail: list[str] = []
    for row in opened:
        first_id = row["recovery_sprint"].get("first_executable_action_id")
        action = actions.get(first_id)
        if action is None or action.get("boundary_event_id") != row["boundary_event_id"]:
            first_resolve_fail.append(row["boundary_event_id"])
            continue
        if not action["progress_bearing"] or action["status"] == "SKIPPED":
            first_progress_fail.append(row["boundary_event_id"])
    setf(
        _na("PRCR.BOUNDARY.FIRST_ACTION_RESOLVES", "boundary_events", "No opened recovery sprint.")
        if not opened
        else (
            _pass("PRCR.BOUNDARY.FIRST_ACTION_RESOLVES", "boundary_events", "Every recovery first action resolves to its boundary context.")
            if not first_resolve_fail
            else _fail("PRCR.BOUNDARY.FIRST_ACTION_RESOLVES", "boundary_events", "Recovery first action does not resolve for " + ", ".join(first_resolve_fail))
        )
    )
    setf(
        _na("PRCR.BOUNDARY.FIRST_ACTION_PROGRESS", "boundary_events", "No opened recovery sprint.")
        if not opened
        else (
            _pass("PRCR.BOUNDARY.FIRST_ACTION_PROGRESS", "boundary_events", "Every recovery first action is progress-bearing and attempted.")
            if not first_progress_fail and not first_resolve_fail
            else _fail("PRCR.BOUNDARY.FIRST_ACTION_PROGRESS", "boundary_events", "Recovery first action is missing or non-progress for " + ", ".join(first_resolve_fail + first_progress_fail))
        )
    )
    setf(copy.deepcopy(findings["PRCR.BOUNDARY.RECOVERY_REQUIRED"]))
    findings["PRCR.BOUNDARY.CLASSIFICATION_NOT_GATE"] = (
        _na("PRCR.BOUNDARY.CLASSIFICATION_NOT_GATE", "boundary_events", "No known material unfinished boundary.")
        if not [row for row in canonical if row["materiality"] in MATERIAL and unfinished]
        else (
            _pass("PRCR.BOUNDARY.CLASSIFICATION_NOT_GATE", "boundary_events", "Known classification did not waive recovery.")
            if not wrong_required
            else _fail("PRCR.BOUNDARY.CLASSIFICATION_NOT_GATE", "boundary_events", "Known classification waived required recovery.")
        )
    )
    findings["PRCR.BOUNDARY.RECOVERY_HISTORY_RETAINED"] = _na(
        "PRCR.BOUNDARY.RECOVERY_HISTORY_RETAINED", "boundary_events",
        "Single receipt cannot prove a previously omitted recovered boundary; retained material events remain present."
    )

    linked = [row for row in receipt["actions"] if row["boundary_event_id"] is not None]
    bad_links = [
        row["action_id"]
        for row in linked
        if row["boundary_event_id"] not in boundaries
        or _time(boundaries[row["boundary_event_id"]]["occurred_at"]) > _time(row["started_at"])
    ]
    setf(
        _na("PRCR.ACTION.BOUNDARY_LINK", "actions", "No boundary-linked actions.")
        if not linked
        else (
            _pass("PRCR.ACTION.BOUNDARY_LINK", "actions", "Boundary-linked actions resolve and occur after their boundary.")
            if not bad_links
            else _fail("PRCR.ACTION.BOUNDARY_LINK", "actions", "Invalid boundary/action ordering for " + ", ".join(bad_links))
        )
    )
    progress = [row for row in receipt["actions"] if row["progress_bearing"]]
    unsubstantiated = [
        row["action_id"]
        for row in progress
        if not row["evidence_refs"]
        and row["proof_before"] == row["proof_after"]
        and row["status"] in {"SKIPPED", "CANCELLED"}
    ]
    setf(
        _na("PRCR.ACTION.PROGRESS_TRUTH", "actions", "No action claims progress-bearing status.")
        if not progress
        else (
            _pass("PRCR.ACTION.PROGRESS_TRUTH", "actions", "Progress-bearing actions carry evidence, a proof transition, or an executed status.")
            if not unsubstantiated
            else _fail("PRCR.ACTION.PROGRESS_TRUTH", "actions", "Unsupported progress-bearing claim on " + ", ".join(unsubstantiated))
        )
    )

    succeeded = [row for row in receipt["actions"] if row["status"] == "SUCCEEDED"]
    proof_regress = [
        row["action_id"]
        for row in succeeded
        if _rank(row["proof_before"]) is not None
        and _rank(row["proof_after"]) is not None
        and _rank(row["proof_after"]) < _rank(row["proof_before"])
    ]
    setf(
        _na("PRCR.ACTION.SUCCEEDED_PROOF_ADVANCE", "actions", "No succeeded actions.")
        if not succeeded
        else (
            _pass("PRCR.ACTION.SUCCEEDED_PROOF_ADVANCE", "actions", "Succeeded actions do not silently regress proof state.")
            if not proof_regress
            else _fail("PRCR.ACTION.SUCCEEDED_PROOF_ADVANCE", "actions", "Succeeded action regressed proof state: " + ", ".join(proof_regress))
        )
    )

    promotions = [
        row for row in receipt["actions"]
        if _rank(row["proof_before"]) is not None
        and _rank(row["proof_after"]) is not None
        and _rank(row["proof_after"]) > _rank(row["proof_before"])
    ]
    unsupported_promotions: list[str] = []
    pass_checks = [check for check in receipt["proof"]["checks"] if check["status"] == "PASS"]
    for row in promotions:
        if not row["evidence_refs"] or not pass_checks:
            unsupported_promotions.append(row["action_id"])
    setf(
        _na("PRCR.ACTION.NO_FALSE_PROOF_PROMOTION", "actions", "No action strengthens proof state.")
        if not promotions
        else (
            _pass("PRCR.ACTION.NO_FALSE_PROOF_PROMOTION", "actions", "Proof promotions are evidence-backed.")
            if not unsupported_promotions
            else _fail("PRCR.ACTION.NO_FALSE_PROOF_PROMOTION", "actions", "Unsupported proof promotion on " + ", ".join(unsupported_promotions))
        )
    )

    ambiguous = [
        row for row in receipt["actions"]
        if row["side_effect_state"] in {"PARTIAL", "UNKNOWN"}
    ]
    partial_fail: list[str] = []
    for row in ambiguous:
        action_id = row["action_id"]
        readbacks = [
            other for other in receipt["actions"]
            if other.get("readback_of_action_id") == action_id
        ]
        retries = [
            other for other in receipt["actions"]
            if other.get("retry_of_action_id") == action_id
        ]
        first_readback = min((other["sequence"] for other in readbacks), default=None)
        first_retry = min((other["sequence"] for other in retries), default=None)
        if first_readback is None or (first_retry is not None and first_retry < first_readback):
            partial_fail.append(action_id)
    setf(
        _na("PRCR.ACTION.PARTIAL_READBACK", "actions", "No partial or unknown mutation side effect.")
        if not ambiguous
        else (
            _pass("PRCR.ACTION.PARTIAL_READBACK", "actions", "Authoritative readback precedes every equivalent retry.")
            if not partial_fail
            else _fail("PRCR.ACTION.PARTIAL_READBACK", "actions", "Partial/unknown mutation lacks readback-before-retry: " + ", ".join(partial_fail))
        )
    )

    nonsuccess = [row for row in receipt["actions"] if row["status"] in {"FAILED", "BLOCKED", "CANCELLED", "SKIPPED"}]
    bad_nonsuccess = [
        row["action_id"]
        for row in nonsuccess
        if _rank(row["proof_before"]) is not None
        and _rank(row["proof_after"]) is not None
        and _rank(row["proof_after"]) > _rank(row["proof_before"])
    ]
    setf(
        _na("PRCR.ACTION.CANCELLED_NOT_SUCCESS", "actions", "No failed, blocked, cancelled, or skipped action.")
        if not nonsuccess
        else (
            _pass("PRCR.ACTION.CANCELLED_NOT_SUCCESS", "actions", "Non-success actions do not independently strengthen proof.")
            if not bad_nonsuccess
            else _fail("PRCR.ACTION.CANCELLED_NOT_SUCCESS", "actions", "Non-success action strengthened proof: " + ", ".join(bad_nonsuccess))
        )
    )

    terminal = receipt["terminal"]
    if terminal["state"] == "COMPLETE":
        complete_ok = (
            terminal["reason_code"] == "OBJECTIVE_COMPLETED"
            and terminal["resumption_trigger"] is None
            and terminal["next_transition"] is None
            and not any(v["status"] == "OPEN" and v["severity"] in FAILURE_SEVERITIES for v in receipt["violations"])
            and not any(check["status"] == "BLOCKED" for check in receipt["proof"]["checks"])
        )
        setf(
            _pass("PRCR.TERMINAL.COMPLETE_GATE", "terminal", "Completion gate has no retained blocker or open high-severity violation.")
            if complete_ok
            else _fail("PRCR.TERMINAL.COMPLETE_GATE", "terminal", "COMPLETE lacks objective-complete evidence or still carries a blocker/open high-severity violation.")
        )
    else:
        setf(_na("PRCR.TERMINAL.COMPLETE_GATE", "terminal", "Terminal state is not COMPLETE."))

    if terminal["state"] == "QUIESCENT_BLOCKED":
        blocked_ok = (
            terminal["reason_code"] in {"UNAVAILABLE_DEPENDENCY", "NO_SAFE_PROGRESS_PATH"}
            and terminal["resumption_trigger"] is not None
            and terminal["next_transition"] is not None
        )
        setf(
            _pass("PRCR.TERMINAL.BLOCKED_GATE", "terminal", "Blocked terminal state carries dependency/resumption/next-transition evidence.")
            if blocked_ok
            else _fail("PRCR.TERMINAL.BLOCKED_GATE", "terminal", "QUIESCENT_BLOCKED lacks an unavailable dependency, resumption trigger, or next transition.")
        )
    else:
        setf(_na("PRCR.TERMINAL.BLOCKED_GATE", "terminal", "Terminal state is not QUIESCENT_BLOCKED."))

    if terminal["reason_code"] == "NO_SAFE_PROGRESS_PATH":
        if terminal["state"] != "QUIESCENT_BLOCKED":
            setf(_fail("PRCR.TERMINAL.NO_SAFE_PATH_EVIDENCE", "terminal", "NO_SAFE_PROGRESS_PATH must quiesce blocked, not claim completion."))
        elif terminal["next_transition"] is None:
            setf(_fail("PRCR.TERMINAL.NO_SAFE_PATH_EVIDENCE", "terminal", "NO_SAFE_PROGRESS_PATH lacks actionable continuation."))
        else:
            setf(_unknown("PRCR.TERMINAL.NO_SAFE_PATH_EVIDENCE", "terminal", "Single receipt cannot independently prove every safe alternative was exhausted."))
    else:
        setf(_na("PRCR.TERMINAL.NO_SAFE_PATH_EVIDENCE", "terminal", "Reason is not NO_SAFE_PROGRESS_PATH."))

    if terminal["state"] == "HARD_TERMINATED_SYNTHETIC":
        runtime_evidence = [row for row in receipt["evidence"] if row["kind"] in {"runtime", "provider"}]
        setf(
            _pass("PRCR.TERMINAL.HARD_SYNTHETIC", "terminal", "Synthetic hard termination is externally evidenced.")
            if terminal["supervisor_synthesized"] and runtime_evidence
            else _fail("PRCR.TERMINAL.HARD_SYNTHETIC", "terminal", "Hard termination was self-asserted or lacks external supervisor evidence.")
        )
        setf(
            _pass("PRCR.TERMINAL.HARD_REASON", "terminal", "Hard termination uses HOST_FORCED_TERMINATION with a checkpoint.")
            if terminal["reason_code"] == "HOST_FORCED_TERMINATION" and terminal["last_proven_checkpoint"] is not None
            else _fail("PRCR.TERMINAL.HARD_REASON", "terminal", "Hard termination lacks the required reason/checkpoint.")
        )
    else:
        setf(_na("PRCR.TERMINAL.HARD_SYNTHETIC", "terminal", "Terminal state is not HARD_TERMINATED_SYNTHETIC."))
        setf(_na("PRCR.TERMINAL.HARD_REASON", "terminal", "Terminal state is not HARD_TERMINATED_SYNTHETIC."))

    if terminal["state"] == "EXPLICIT_OPERATOR_CANCELLATION":
        cancellation = any("cancel" in row["supports"].lower() for row in receipt["evidence"])
        setf(
            _pass("PRCR.TERMINAL.CANCEL_AUTHORITY", "terminal", "Explicit operator cancellation is evidenced.")
            if terminal["reason_code"] == "OPERATOR_CANCELLED" and cancellation
            else _fail("PRCR.TERMINAL.CANCEL_AUTHORITY", "terminal", "Cancellation terminal state lacks explicit cancellation evidence.")
        )
    else:
        setf(_na("PRCR.TERMINAL.CANCEL_AUTHORITY", "terminal", "Terminal state is not operator cancellation."))

    if terminal["state"] == "USER_ONLY_DECISION_REQUIRED":
        setf(
            _pass("PRCR.TERMINAL.USER_ONLY", "terminal", "User-only decision is explicit and carries the next transition.")
            if terminal["reason_code"] == "USER_DECISION_REQUIRED" and terminal["next_transition"] is not None
            else _fail("PRCR.TERMINAL.USER_ONLY", "terminal", "User-only decision terminal state lacks its exact decision/continuation gate.")
        )
    else:
        setf(_na("PRCR.TERMINAL.USER_ONLY", "terminal", "Terminal state is not USER_ONLY_DECISION_REQUIRED."))

    if receipt["violations"]:
        missing_ev = [v["violation_id"] for v in receipt["violations"] if not v["evidence_refs"] or any(ref not in evidence for ref in v["evidence_refs"])]
        bad_rule = [v["violation_id"] for v in receipt["violations"] if v["rule_id"] not in RULE_IDS]
        setf(
            _pass("PRCR.VIOLATION.EVIDENCE_REQUIRED", "violations", "Violations are evidence-backed.")
            if not missing_ev
            else _fail("PRCR.VIOLATION.EVIDENCE_REQUIRED", "violations", "Violation lacks valid evidence: " + ", ".join(missing_ev))
        )
        setf(
            _pass("PRCR.VIOLATION.RULE_RESOLVES", "violations", "Violation rule IDs resolve to the pinned contract.")
            if not bad_rule
            else _fail("PRCR.VIOLATION.RULE_RESOLVES", "violations", "Violation rule ID does not resolve: " + ", ".join(bad_rule))
        )
    else:
        setf(_na("PRCR.VIOLATION.EVIDENCE_REQUIRED", "violations", "No violations."))
        setf(_na("PRCR.VIOLATION.RULE_RESOLVES", "violations", "No violations."))

    open_high = [
        v for v in receipt["violations"]
        if v["status"] == "OPEN" and v["severity"] in FAILURE_SEVERITIES
    ]
    if receipt["compliance_result"] == "PASS":
        setf(
            _pass("PRCR.VIOLATION.PASS_CRITICAL", "violations", "PASS has no open high/critical violation.")
            if not open_high
            else _fail("PRCR.VIOLATION.PASS_CRITICAL", "violations", "PASS cannot retain open high/critical violations.")
        )
    else:
        setf(_na("PRCR.VIOLATION.PASS_CRITICAL", "violations", "Receipt does not claim PASS."))

    if receipt["compliance_result"] == "FAIL":
        substantive = [v for v in receipt["violations"] if v["status"] != "INFORMATIONAL" and v["evidence_refs"]]
        setf(
            _pass("PRCR.VIOLATION.FAIL_REQUIRES_VIOLATION", "violations", "FAIL is backed by a substantive violation.")
            if substantive
            else _fail("PRCR.VIOLATION.FAIL_REQUIRES_VIOLATION", "violations", "FAIL lacks an evidence-backed substantive violation.")
        )
    else:
        setf(_na("PRCR.VIOLATION.FAIL_REQUIRES_VIOLATION", "violations", "Receipt does not claim FAIL."))

    needing_regression = [v for v in receipt["violations"] if v["regression_required"]]
    bad_regression = [
        v["violation_id"]
        for v in needing_regression
        if v["regression_link_id"] not in set(receipt["regression_linkage"]["regression_link_ids"])
        or receipt["regression_linkage"]["status"] == "NONE"
    ]
    setf(
        _na("PRCR.VIOLATION.REGRESSION_REQUIRED", "violations", "No violation requires regression routing.")
        if not needing_regression
        else (
            _pass("PRCR.VIOLATION.REGRESSION_REQUIRED", "violations", "Regression-required violations resolve to durable linkage.")
            if not bad_regression
            else _fail("PRCR.VIOLATION.REGRESSION_REQUIRED", "violations", "Regression-required violation lacks linkage: " + ", ".join(bad_regression))
        )
    )
    runtime_family_bad = [
        v["violation_id"]
        for v in receipt["violations"]
        if v["family"] not in {"RUNTIME_BEHAVIOR", "PROOF_INTEGRITY", "PRIVACY", "REGRESSION", "SCHEMA", "PATCH_HYGIENE"}
    ]
    setf(
        _na("PRCR.VIOLATION.RUNTIME_FAMILY", "violations", "No runtime violation family requires classification.")
        if not receipt["violations"]
        else (
            _pass("PRCR.VIOLATION.RUNTIME_FAMILY", "violations", "Violation families use the bounded canonical vocabulary.")
            if not runtime_family_bad
            else _fail("PRCR.VIOLATION.RUNTIME_FAMILY", "violations", "Violation family is not canonical.")
        )
    )

    proof = receipt["proof"]
    runtime_evidence = [row for row in receipt["evidence"] if row["kind"] == "runtime"]
    if proof["strongest_state"] == "OBSERVED":
        setf(
            _pass("PRCR.PROOF.OBSERVED_RUNTIME", "proof", "OBSERVED proof has runtime_observed=true and direct runtime evidence.")
            if proof["runtime_observed"] and runtime_evidence
            else _fail("PRCR.PROOF.OBSERVED_RUNTIME", "proof", "OBSERVED proof lacks direct runtime evidence.")
        )
    else:
        setf(_na("PRCR.PROOF.OBSERVED_RUNTIME", "proof", "Strongest state is not OBSERVED."))

    if _rank(proof["strongest_state"]) >= STATE_RANK["DEPLOYED"]:
        deployment = [row for row in proof["checks"] if "deploy" in row["name"].lower() and row["status"] == "PASS"]
        setf(
            _pass("PRCR.PROOF.DEPLOYED_EVIDENCE", "proof", "Deployment-class proof includes a passing deployment check.")
            if deployment
            else _fail("PRCR.PROOF.DEPLOYED_EVIDENCE", "proof", "DEPLOYED/OBSERVED proof lacks deployment evidence.")
        )
    else:
        setf(_na("PRCR.PROOF.DEPLOYED_EVIDENCE", "proof", "Strongest state is below DEPLOYED."))

    if _rank(proof["strongest_state"]) >= STATE_RANK["INTEGRATED"]:
        integration = [row for row in proof["checks"] if ("integrat" in row["name"].lower() or "contain" in row["name"].lower()) and row["status"] == "PASS"]
        setf(
            _pass("PRCR.PROOF.INTEGRATED_EVIDENCE", "proof", "Integration-class proof includes passing containment/integration evidence.")
            if integration
            else _fail("PRCR.PROOF.INTEGRATED_EVIDENCE", "proof", "INTEGRATED-or-stronger proof lacks containment/integration evidence.")
        )
    else:
        setf(_na("PRCR.PROOF.INTEGRATED_EVIDENCE", "proof", "Strongest state is below INTEGRATED."))

    if _rank(proof["strongest_state"]) >= STATE_RANK["VALIDATED"]:
        setf(
            _pass("PRCR.PROOF.VALIDATED_EVIDENCE", "proof", "Validated-or-stronger proof includes a passing check.")
            if any(check["status"] == "PASS" for check in proof["checks"])
            else _fail("PRCR.PROOF.VALIDATED_EVIDENCE", "proof", "VALIDATED-or-stronger proof lacks a passing validation check.")
        )
    else:
        setf(_na("PRCR.PROOF.VALIDATED_EVIDENCE", "proof", "Strongest state is below VALIDATED."))

    blocked_checks = [check for check in proof["checks"] if check["status"] == "BLOCKED"]
    if blocked_checks:
        overpromoted = _rank(proof["strongest_state"]) > STATE_RANK["VALIDATED"] and not any(
            check["status"] == "PASS" and ("equivalent" in check["name"].lower() or "substitute" in check["name"].lower())
            for check in proof["checks"]
        )
        setf(
            _fail("PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED", "proof", "Blocked required proof was promoted without equivalent evidence.")
            if overpromoted
            else _pass("PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED", "proof", "Blocked proof remains inside the declared proof ceiling.")
        )
    else:
        setf(_na("PRCR.PROOF.NO_PROMOTION_FROM_BLOCKED", "proof", "No proof check is BLOCKED."))

    setf(
        _pass("PRCR.PROOF.CEILING_REQUIRED", "proof", "Proof ceiling is explicitly bounded.")
        if proof["proof_ceiling"].strip()
        else _fail("PRCR.PROOF.CEILING_REQUIRED", "proof", "Proof ceiling is empty.")
    )
    fp = proof["fingerprint"]
    required_fp = ("effective_prompt", "governing_contracts", "scenario_fixture", "evaluator", "model_config", "runtime_host")
    fp_complete = all(key in fp for key in required_fp) and bool(fp["governing_contracts"])
    setf(
        _pass("PRCR.PROOF.FINGERPRINT.REQUIRED", "proof", "Required proof-relevance fingerprint components are present.")
        if fp_complete
        else _fail("PRCR.PROOF.FINGERPRINT.REQUIRED", "proof", "Proof-relevance fingerprint is incomplete.")
    )
    setf(
        _pass("PRCR.PROOF.FINGERPRINT.UNIQUE", "proof", "Fingerprint governing-contract identities are unique.")
        if len(fp["governing_contracts"]) == len(set(fp["governing_contracts"]))
        else _fail("PRCR.PROOF.FINGERPRINT.UNIQUE", "proof", "Fingerprint governing-contract identities are duplicated.")
    )
    if receipt.get("supersedes_receipt_id"):
        setf(_unknown("PRCR.PROOF.FINGERPRINT.FRESH", "proof", "Superseded receipt fingerprint is not embedded; freshness requires comparison evidence."))
        setf(_unknown("PRCR.PROOF.FINGERPRINT.UNKNOWN", "proof", "Prior fingerprint cannot be reconstructed from this single receipt."))
    else:
        setf(_na("PRCR.PROOF.FINGERPRINT.FRESH", "proof", "No prior receipt reuse/comparison is claimed."))
        setf(_na("PRCR.PROOF.FINGERPRINT.UNKNOWN", "proof", "No required prior fingerprint comparison is claimed."))

    linkage = receipt["regression_linkage"]
    if linkage["status"] != "NONE":
        setf(
            _pass("PRCR.REGRESSION.INCIDENT_SOURCE", "regression_linkage", "Regression linkage has a non-none incident source.")
            if linkage["incident_source"] != "none"
            else _fail("PRCR.REGRESSION.INCIDENT_SOURCE", "regression_linkage", "Active regression linkage cannot use incident_source=none.")
        )
    else:
        setf(_na("PRCR.REGRESSION.INCIDENT_SOURCE", "regression_linkage", "Regression status is NONE."))

    if linkage["status"] == "SYSTEMIC":
        setf(
            _pass("PRCR.REGRESSION.SYSTEMIC_THRESHOLD", "regression_linkage", "Systemic status has at least two independent occurrences.")
            if len(linkage["occurrences"]) >= 2
            else _fail("PRCR.REGRESSION.SYSTEMIC_THRESHOLD", "regression_linkage", "SYSTEMIC status lacks two independent occurrences.")
        )
    else:
        setf(_na("PRCR.REGRESSION.SYSTEMIC_THRESHOLD", "regression_linkage", "Regression status is not SYSTEMIC."))

    if linkage["systemic_threshold_met"]:
        ok = linkage["status"] in {"SYSTEMIC", "REPAIRED", "RETAINED"} and len(linkage["occurrences"]) >= 2
        setf(
            _pass("PRCR.REGRESSION.SYSTEMIC_BOOLEAN", "regression_linkage", "systemic_threshold_met agrees with status and occurrences.")
            if ok
            else _fail("PRCR.REGRESSION.SYSTEMIC_BOOLEAN", "regression_linkage", "systemic_threshold_met is inconsistent.")
        )
    else:
        setf(_na("PRCR.REGRESSION.SYSTEMIC_BOOLEAN", "regression_linkage", "systemic_threshold_met is false."))

    if linkage["status"] in {"SYSTEMIC", "REPAIRED", "RETAINED"}:
        setf(
            _pass("PRCR.REGRESSION.CANONICAL_OWNER", "regression_linkage", "Systemic/repair linkage names a canonical owner.")
            if linkage["canonical_owner"]
            else _fail("PRCR.REGRESSION.CANONICAL_OWNER", "regression_linkage", "Systemic/repair linkage lacks canonical owner.")
        )
    else:
        setf(_na("PRCR.REGRESSION.CANONICAL_OWNER", "regression_linkage", "Regression status does not require a canonical owner."))

    if linkage["status"] in {"REPAIRED", "RETAINED"}:
        complete = all(linkage.get(key) for key in ("negative_fixture", "positive_control", "regression_test", "canonical_owner"))
        setf(
            _pass("PRCR.REGRESSION.REPAIR_COMPLETENESS", "regression_linkage", "Repair links negative/positive controls and regression test.")
            if complete
            else _fail("PRCR.REGRESSION.REPAIR_COMPLETENESS", "regression_linkage", "Repair linkage is incomplete.")
        )
    else:
        setf(_na("PRCR.REGRESSION.REPAIR_COMPLETENESS", "regression_linkage", "Regression status is not REPAIRED/RETAINED."))

    if linkage["status"] == "RETAINED":
        setf(
            _pass("PRCR.REGRESSION.RETAINED_INTEGRATION", "regression_linkage", "Retained regression links an integrated commit.")
            if linkage.get("integrated_commit")
            else _fail("PRCR.REGRESSION.RETAINED_INTEGRATION", "regression_linkage", "RETAINED regression lacks integrated commit.")
        )
    else:
        setf(_na("PRCR.REGRESSION.RETAINED_INTEGRATION", "regression_linkage", "Regression status is not RETAINED."))

    if linkage["status"] == "NONE":
        none_ok = (
            linkage["systemic_threshold_met"] is False
            and not linkage["occurrences"]
            and not linkage["regression_link_ids"]
            and not linkage.get("negative_fixture")
            and not linkage.get("positive_control")
            and not linkage.get("regression_test")
        )
        setf(
            _pass("PRCR.REGRESSION.NONE_CONSISTENT", "regression_linkage", "NONE linkage carries no active regression program.")
            if none_ok
            else _fail("PRCR.REGRESSION.NONE_CONSISTENT", "regression_linkage", "NONE linkage still implies an active regression program.")
        )
    else:
        setf(_na("PRCR.REGRESSION.NONE_CONSISTENT", "regression_linkage", "Regression status is not NONE."))

    privacy = receipt.get("privacy")
    for rule_id, field, label in (
        ("PRCR.PRIVACY.NO_RAW_TRANSCRIPT", "raw_transcript_persisted", "raw transcript"),
        ("PRCR.PRIVACY.NO_SECRETS", "secrets_persisted", "secret"),
        ("PRCR.PRIVACY.NO_HIDDEN_REASONING", "hidden_reasoning_persisted", "hidden reasoning"),
    ):
        if privacy is None:
            setf(_unknown(rule_id, "privacy", "Privacy block is absent, so non-persistence cannot be verified."))
        elif privacy[field] is False:
            setf(_pass(rule_id, "privacy", f"No {label} persistence is declared."))
        else:
            setf(_fail(rule_id, "privacy", f"Receipt persists forbidden {label} evidence."))

    if privacy is None or privacy["redaction_count"] == 0:
        setf(_na("PRCR.PRIVACY.REDACTION_ACCOUNTING", "privacy", "No persisted redaction is claimed."))
    else:
        setf(_pass("PRCR.PRIVACY.REDACTION_ACCOUNTING", "privacy", "Redaction count is explicitly recorded."))

    model = receipt["model_config"]
    identity_ok = all(model.get(key) for key in ("provider", "model", "configuration_id", "configuration_fingerprint", "host_surface"))
    setf(
        _pass("PRCR.MODEL.IDENTITY_REQUIRED", "model_config", "Provider/model/configuration/host identity is present.")
        if identity_ok
        else _fail("PRCR.MODEL.IDENTITY_REQUIRED", "model_config", "Model configuration identity is incomplete.")
    )
    if model["model_revision"] is None:
        setf(
            _pass("PRCR.MODEL.REVISION_UNKNOWN_EXPLICIT", "model_config", "Unknown model revision is explicit and configuration fingerprint remains present.")
            if model["configuration_fingerprint"]
            else _fail("PRCR.MODEL.REVISION_UNKNOWN_EXPLICIT", "model_config", "Unknown model revision also lacks configuration fingerprint.")
        )
    else:
        setf(_na("PRCR.MODEL.REVISION_UNKNOWN_EXPLICIT", "model_config", "Exact model revision is known."))
    setf(_na("PRCR.MODEL.CONFIG_FINGERPRINT_STABLE", "model_config", "Cross-run configuration stability requires another receipt for comparison."))

    invariants = receipt["scenario"]["protected_invariants"]
    setf(
        _pass("PRCR.SCENARIO.PROTECTED_INVARIANTS", "scenario", "Scenario declares protected invariants.")
        if invariants
        else _fail("PRCR.SCENARIO.PROTECTED_INVARIANTS", "scenario", "Scenario has no protected invariants.")
    )
    if receipt["scenario"]["kind"] in {"synthetic", "replay"}:
        setf(
            _pass("PRCR.SCENARIO.FIXTURE_REQUIRED", "scenario", "Synthetic/replay scenario has a durable fixture identity.")
            if receipt["scenario"].get("fixture_path")
            else _fail("PRCR.SCENARIO.FIXTURE_REQUIRED", "scenario", "Synthetic/replay scenario lacks fixture identity.")
        )
    else:
        setf(_na("PRCR.SCENARIO.FIXTURE_REQUIRED", "scenario", "Observed scenario does not require a synthetic fixture path."))

    return [findings[rule["rule_id"]] for rule in CONTRACT["rules"]]


def validate_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    schema_errors = sorted(
        Draft202012Validator(SCHEMA, format_checker=FORMAT_CHECKER).iter_errors(receipt),
        key=lambda error: list(error.absolute_path),
    )
    if schema_errors:
        message = "; ".join(error.message for error in schema_errors[:6])
        result = {
            "schema_version": "prompt-runtime-compliance-validation/v1",
            "receipt_id": str(receipt.get("receipt_id", "unknown")),
            "receipt_schema": "prompt-runtime-compliance-receipt/v1",
            "overall_result": "INCONCLUSIVE",
            "counts": {"PASS": 0, "FAIL": 1, "NOT_APPLICABLE": 0, "UNKNOWN": 0},
            "findings": [
                _fail(
                    "PRCR.COMPLIANCE.INCONCLUSIVE",
                    "receipt-schema",
                    "Structural receipt validation failed: " + message,
                )
            ],
        }
        return result

    findings = _evaluate_nonaggregate(receipt)
    by_id = {row["rule_id"]: row for row in findings}

    def serious(rows: list[dict[str, Any]], result: str) -> list[dict[str, Any]]:
        return [row for row in rows if row["severity"] in FAILURE_SEVERITIES and row["result"] == result]

    nonaggregate = [
        row for row in findings
        if row["rule_id"] not in {
            "PRCR.COMPLIANCE.PASS",
            "PRCR.COMPLIANCE.FAIL",
            "PRCR.COMPLIANCE.BLOCKED",
            "PRCR.COMPLIANCE.INCONCLUSIVE",
        }
    ]
    hard_fail = serious(nonaggregate, "FAIL")
    hard_unknown = serious(nonaggregate, "UNKNOWN")

    if receipt["compliance_result"] == "PASS":
        by_id["PRCR.COMPLIANCE.PASS"] = (
            _pass("PRCR.COMPLIANCE.PASS", "receipt", "PASS is consistent with all applicable critical/high rules.")
            if not hard_fail and not hard_unknown
            else _fail("PRCR.COMPLIANCE.PASS", "receipt", "PASS hides a critical/high failure or unknown.")
        )
    else:
        by_id["PRCR.COMPLIANCE.PASS"] = _na("PRCR.COMPLIANCE.PASS", "receipt", "Receipt does not claim PASS.")

    if hard_fail:
        by_id["PRCR.COMPLIANCE.FAIL"] = (
            _pass("PRCR.COMPLIANCE.FAIL", "receipt", "Critical/high semantic failure is represented as FAIL.")
            if receipt["compliance_result"] == "FAIL"
            else _fail("PRCR.COMPLIANCE.FAIL", "receipt", "Critical/high semantic failure is not represented as FAIL.")
        )
    elif receipt["compliance_result"] == "FAIL":
        by_id["PRCR.COMPLIANCE.FAIL"] = _fail("PRCR.COMPLIANCE.FAIL", "receipt", "FAIL has no critical/high semantic failure.")
    else:
        by_id["PRCR.COMPLIANCE.FAIL"] = _na("PRCR.COMPLIANCE.FAIL", "receipt", "No critical/high semantic rule failed.")

    if receipt["compliance_result"] == "BLOCKED":
        blocked_ok = receipt["terminal"]["state"] == "QUIESCENT_BLOCKED" and receipt["terminal"]["next_transition"] is not None
        by_id["PRCR.COMPLIANCE.BLOCKED"] = (
            _pass("PRCR.COMPLIANCE.BLOCKED", "receipt", "BLOCKED result carries an exact blocked terminal gate.")
            if blocked_ok
            else _fail("PRCR.COMPLIANCE.BLOCKED", "receipt", "BLOCKED result lacks an exact blocked terminal gate.")
        )
    else:
        by_id["PRCR.COMPLIANCE.BLOCKED"] = _na("PRCR.COMPLIANCE.BLOCKED", "receipt", "Receipt does not claim BLOCKED.")

    if receipt["compliance_result"] == "INCONCLUSIVE":
        by_id["PRCR.COMPLIANCE.INCONCLUSIVE"] = (
            _pass("PRCR.COMPLIANCE.INCONCLUSIVE", "receipt", "INCONCLUSIVE is justified by unresolved critical/high evidence.")
            if hard_unknown
            else _fail("PRCR.COMPLIANCE.INCONCLUSIVE", "receipt", "INCONCLUSIVE lacks unresolved critical/high evidence.")
        )
    else:
        by_id["PRCR.COMPLIANCE.INCONCLUSIVE"] = _na("PRCR.COMPLIANCE.INCONCLUSIVE", "receipt", "Receipt does not claim INCONCLUSIVE.")

    findings = [by_id[rule["rule_id"]] for rule in CONTRACT["rules"]]
    hard_fail = serious(findings, "FAIL")
    hard_unknown = serious(findings, "UNKNOWN")
    if hard_fail:
        overall = "FAIL"
    elif receipt["compliance_result"] == "PASS" and hard_unknown:
        overall = "INCONCLUSIVE"
    else:
        overall = receipt["compliance_result"]

    counts = {key: 0 for key in ("PASS", "FAIL", "NOT_APPLICABLE", "UNKNOWN")}
    for row in findings:
        counts[row["result"]] += 1

    result = {
        "schema_version": "prompt-runtime-compliance-validation/v1",
        "receipt_id": receipt["receipt_id"],
        "receipt_schema": receipt["schema_version"],
        "overall_result": overall,
        "counts": counts,
        "findings": findings,
    }
    Draft202012Validator(
        CONTRACT["validation_result_schema_definition"],
        format_checker=FORMAT_CHECKER,
    ).validate(result)
    return result


def validate_path(path: Path) -> dict[str, Any]:
    return validate_receipt(load_json(path))


def exit_code(result: dict[str, Any]) -> int:
    if result["overall_result"] == "PASS":
        return 0
    if result["overall_result"] == "FAIL":
        return 1
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prompt-runtime-compliance receipt semantics.")
    parser.add_argument("receipt", nargs="?", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--json", action="store_true", dest="emit_json")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    result = validate_path(args.receipt)
    if args.emit_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "PROMPT RUNTIME COMPLIANCE: "
            f"{result['overall_result']} "
            f"receipt={result['receipt_id']} "
            f"pass={result['counts']['PASS']} "
            f"fail={result['counts']['FAIL']} "
            f"unknown={result['counts']['UNKNOWN']} "
            f"na={result['counts']['NOT_APPLICABLE']}"
        )
        if not args.summary:
            for row in result["findings"]:
                if row["result"] in {"FAIL", "UNKNOWN"}:
                    print(f"{row['result']} {row['rule_id']}: {row['message']}")
    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
