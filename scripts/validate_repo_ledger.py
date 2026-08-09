#!/usr/bin/env python3
"""Validate this repository's shared work-ledger adoption and local queue."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".ai" / "repo-ledger-adoption.json"
QUEUE = ROOT / ".ai" / "WORK_QUEUE.md"
ENTRY = ROOT / ".ai" / "README.md"
CONTRACT_COMMIT = "3188d577dbda1994c0629c1416ae3362198812dd"
DONOR_COMMIT = "9351c952b057ae4520b1ea0d388e1d8908f4c093"
DONOR_PATHS = {
    ".ai/README.md",
    ".ai/WORK_QUEUE.md",
    ".ai/authority.json",
    "scripts/ai-harness/validate-work-queue.mjs",
}
STATUSES = {"READY", "CLAIMED", "VERIFY", "REVIEW", "MERGE", "OPERATOR", "BLOCKED", "DONE"}
CONTINUE = {"READY", "CLAIMED", "VERIFY", "REVIEW", "MERGE"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
FIELDS = [
    "Status",
    "Priority",
    "Owner",
    "Branch / PR",
    "Scope",
    "Forbidden",
    "Dependencies",
    "References",
    "Acceptance gate",
    "Gate",
    "Last proof",
    "Next action",
    "Updated",
]
DONE_ACTION = "none; no safe actionable work remains"
SHA = re.compile(r"^[0-9a-f]{40}$")
HEADING = re.compile(r"^## (TRQ-\d{3,}) — (.+)$", re.MULTILINE)
QUEUEISH_HEADING = re.compile(r"^##\s+([A-Z][A-Z0-9]{1,7}Q-[^\n]*)$", re.MULTILINE)
FIELD = re.compile(r"^- \*\*([^*]+):\*\*[ \t]*(.*)$", re.MULTILINE)
PROOF = re.compile(
    r"(?:\b(?:commit|merge):[0-9a-f]{7,40}\b|\b(?:workflow|run):#?\d+\b|\bartifact:\S+|\boperator-proof:\S+)",
    re.IGNORECASE,
)


def is_sha(value: object) -> bool:
    return bool(SHA.fullmatch(str(value or "")))


def fail(errors: list[str]) -> None:
    print(f"[repo-ledger] FAIL ({len(errors)})", file=sys.stderr)
    for item in errors:
        print(f"- {item}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    errors: list[str] = []
    for path in (MANIFEST, QUEUE, ENTRY):
        if not path.is_file():
            errors.append(f"missing local adoption path: {path.relative_to(ROOT)}")
    if errors:
        fail(errors)

    try:
        adoption = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail([f"invalid adoption manifest: {exc}"])

    expected_scalars = {
        "schema": "RepoLedgerAdoption.v1",
        "repository": "EndeavorEverlasting/web-excel-repair-triage",
        "adoptionStatus": "implemented",
        "proofCeiling": "repository_harness_only",
    }
    for key, expected in expected_scalars.items():
        if adoption.get(key) != expected:
            errors.append(f"{key} drifted; expected {expected!r}")

    contract = adoption.get("contract", {})
    if contract.get("repository") != "EndeavorEverlasting/BlacksmithGuild":
        errors.append("shared contract owner drifted")
    if contract.get("commit") != CONTRACT_COMMIT:
        errors.append("shared contract pin drifted; explicit compatibility update required")
    if not is_sha(contract.get("commit")):
        errors.append("shared contract ref must be an exact 40-hex commit")
    if contract.get("path") != ".tbg/workflows/repo-ledger-interoperability.contract.json":
        errors.append("shared contract path drifted")
    if contract.get("version") != "RepoLedgerInteroperability.v1":
        errors.append("shared contract version drifted")

    donor = adoption.get("donor", {})
    if donor.get("repository") != "EndeavorEverlasting/AxTask":
        errors.append("donor repository drifted")
    if donor.get("commit") != DONOR_COMMIT:
        errors.append("donor commit drifted; a new shared-contract version is required")
    if not is_sha(donor.get("commit")):
        errors.append("donor ref must be an exact 40-hex commit")
    if set(donor.get("sourcePaths", [])) != DONOR_PATHS:
        errors.append("donor source paths do not match v1 provenance")

    local = adoption.get("local", {})
    if local != {
        "ledgerPath": ".ai/WORK_QUEUE.md",
        "validatorPath": "scripts/validate_repo_ledger.py",
        "taskNamespace": "TRQ",
        "format": "markdown",
    }:
        errors.append("local ledger adapter contract drifted")

    authority = adoption.get("authority", {})
    if authority.get("runtimeOwner") != "EndeavorEverlasting/web-excel-repair-triage":
        errors.append("triage repository must remain local runtime/task authority")
    if authority.get("contractOwner") != "EndeavorEverlasting/BlacksmithGuild":
        errors.append("portable contract owner drifted")
    if authority.get("noCircularAuthority") is not True:
        errors.append("noCircularAuthority must be true")

    for bad in ("main", "HEAD", "master", "feat/repo-ledger", "v1", "3188d577dbda"):
        if is_sha(bad):
            errors.append(f"stale-reference probe unexpectedly accepted {bad!r}")

    text = QUEUE.read_text(encoding="utf-8")
    if "RepoLedgerInteroperability.v1" not in text:
        errors.append("queue is missing the pinned contract-version pointer")
    if "`AGENTS.md`" not in text:
        errors.append("queue must remain explicitly subordinate to AGENTS.md")

    tasks = list(HEADING.finditer(text))
    all_queueish = list(QUEUEISH_HEADING.finditer(text))
    if not tasks:
        errors.append("queue must contain at least one canonical TRQ task")
    if len(tasks) != len(all_queueish):
        errors.append("queue contains a task outside the TRQ namespace or canonical heading format")

    seen: set[str] = set()
    for index, match in enumerate(tasks):
        task_id = match.group(1)
        title = match.group(2).strip()
        end = tasks[index + 1].start() if index + 1 < len(tasks) else len(text)
        block = text[match.start():end]
        values = {m.group(1).strip(): m.group(2).strip() for m in FIELD.finditer(block)}

        if task_id in seen:
            errors.append(f"{task_id}: duplicate task id")
        seen.add(task_id)
        if not title:
            errors.append(f"{task_id}: title is empty")
        for field in FIELDS:
            if not values.get(field):
                errors.append(f"{task_id}: missing or blank field {field!r}")

        status = values.get("Status", "")
        priority = values.get("Priority", "")
        owner = values.get("Owner", "")
        gate = values.get("Gate", "")
        next_action = values.get("Next action", "")
        proof = values.get("Last proof", "")

        if status and status not in STATUSES:
            errors.append(f"{task_id}: invalid status {status!r}")
        if priority and priority not in PRIORITIES:
            errors.append(f"{task_id}: invalid priority {priority!r}")
        if status == "CLAIMED" and owner in {"", "unclaimed"}:
            errors.append(f"{task_id}: CLAIMED requires a concrete owner/session")
        if status in CONTINUE and next_action in {"", DONE_ACTION}:
            errors.append(f"{task_id}: {status} requires an executable next action")
        if status in {"BLOCKED", "OPERATOR"}:
            if gate in {"", "none"}:
                errors.append(f"{task_id}: {status} requires an exact Gate")
            if next_action in {"", DONE_ACTION}:
                errors.append(f"{task_id}: {status} requires an executable next action")
        if status == "DONE":
            if not PROOF.search(proof):
                errors.append(f"{task_id}: DONE requires a durable proof token")
            if gate != "none":
                errors.append(f"{task_id}: DONE requires Gate: none")
            if next_action != DONE_ACTION:
                errors.append(f"{task_id}: DONE requires the canonical no-work-remains next action")

    if errors:
        fail(errors)

    print(
        "[repo-ledger] PASS "
        f"repo=web-excel-repair-triage contract={CONTRACT_COMMIT[:12]} "
        f"donor={DONOR_COMMIT[:12]} namespace=TRQ tasks={len(tasks)} stale-ref-probes=PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
