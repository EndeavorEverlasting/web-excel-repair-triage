#!/usr/bin/env python3
"""Deterministic fake adapter for repository-harness proof only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FIXED_START = "2026-09-18T12:00:00Z"
FIXED_BOUNDARY = "2026-09-18T12:01:00Z"
FIXED_ACTION = "2026-09-18T12:01:30Z"
FIXED_READBACK = "2026-09-18T12:02:00Z"
FIXED_END = "2026-09-18T12:03:00Z"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _action(
    action_id: str,
    sequence: int,
    scenario_id: str,
    *,
    side_effect_state: str = "NONE",
    proof_before: str = "IMPLEMENTED",
    proof_after: str = "VALIDATED",
    readback_of: str | None = None,
    target_identity: str | None = None,
    pre_state_fingerprint: str | None = None,
    evidence_ref: str = "EV-002",
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "sequence": sequence,
        "boundary_event_id": "BE-001",
        "started_at": FIXED_ACTION if sequence == 1 else FIXED_READBACK,
        "completed_at": FIXED_READBACK if sequence == 1 else FIXED_END,
        "status": "SUCCEEDED",
        "progress_bearing": True,
        "side_effect_state": side_effect_state,
        "proof_before": proof_before,
        "proof_after": proof_after,
        "target_identity": target_identity,
        "pre_state_fingerprint": pre_state_fingerprint,
        "readback_of_action_id": readback_of,
        "retry_of_action_id": None,
        "idempotency_key": f"fake-{scenario_id.lower()}-{sequence}",
        "summary": "Execute the first bounded recovery action." if sequence == 1 else "Perform authoritative readback before any retry.",
        "evidence_refs": [evidence_ref],
    }


def build_capture(scenario: dict[str, Any], mode: str) -> dict[str, Any]:
    sid = scenario["scenario_id"]
    boundary = scenario["injected_boundary"]
    mutation = scenario.get("mutation_protocol") or {}
    first_side_effect = "UNKNOWN" if sid == "RTC04" else "NONE"
    first_proof_after = "IMPLEMENTED" if sid == "RTC04" else "VALIDATED"
    first = _action(
        "A-001",
        1,
        sid,
        side_effect_state=first_side_effect,
        proof_after=first_proof_after,
        target_identity=mutation.get("target_identity"),
        pre_state_fingerprint=mutation.get("pre_state_fingerprint"),
    )
    actions = [first]
    evidence = [
        {
            "evidence_id": "EV-001",
            "kind": "artifact",
            "ref": f"fixture:{sid.lower()}:scenario",
            "supports": "Tracked deterministic runtime-compliance scenario fixture.",
        },
        {
            "evidence_id": "EV-002",
            "kind": "artifact",
            "ref": f"fixture:{sid.lower()}:recovery-action",
            "supports": "Fake adapter executed the scenario recovery action structurally.",
        },
        {
            "evidence_id": "EV-004",
            "kind": "artifact",
            "ref": "adapter:fake-runtime-compliance",
            "supports": "Evidence is synthetic harness output and is not target-runtime observation.",
        },
    ]
    if sid == "RTC04" and mode != "rtc04-no-readback":
        actions.append(
            _action(
                "A-002",
                2,
                sid,
                side_effect_state="NONE",
                proof_before="IMPLEMENTED",
                proof_after="VALIDATED",
                readback_of="A-001",
                target_identity=mutation.get("target_identity"),
                pre_state_fingerprint=mutation.get("pre_state_fingerprint"),
                evidence_ref="EV-003",
            )
        )
        evidence.append(
            {
                "evidence_id": "EV-003",
                "kind": "artifact",
                "ref": "fixture:rtc04:authoritative-readback",
                "supports": "Fake adapter records authoritative readback before any equivalent retry.",
            }
        )

    reported_violations: list[dict[str, Any]] = []
    if sid == "RTC04" and mode == "rtc04-no-readback":
        reported_violations.append(
            {
                "violation_id": "V-001",
                "rule_id": "PRCR.ACTION.PARTIAL_READBACK",
                "severity": "CRITICAL",
                "result": "FAIL",
                "family": "RUNTIME_BEHAVIOR",
                "status": "OPEN",
                "subject": "A-001",
                "message": "Unknown mutation outcome reached terminal state without authoritative readback.",
                "regression_required": False,
                "regression_link_id": None,
                "evidence_refs": ["EV-002"],
            }
        )

    capture: dict[str, Any] = {
        "schema_version": "prompt-runtime-compliance-capture/v1",
        "run": {
            "run_id": f"fake/{sid.lower()}",
            "objective_id": f"objective/{sid.lower()}",
            "started_at": FIXED_START,
            "ended_at": FIXED_END,
            "repository": "EndeavorEverlasting/web-excel-repair-triage",
            "mission_id": "P07-runtime-compliance-pilot",
        },
        "model_config": {
            "provider": "fake-provider",
            "model": "fake-agent",
            "model_revision": "fixture-v1",
            "configuration_id": f"fake-{sid.lower()}",
            "configuration_fingerprint": f"fp-fake-{sid.lower()}-v1",
            "host_surface": "repository-fake-adapter",
        },
        "effective_prompt": {
            "prompt_id": "P07",
            "prompt_revision": "fixture-p07",
            "surface_id": "repository-harness",
        },
        "scenario": {
            "scenario_id": sid,
            "kind": "synthetic",
            "protected_invariants": scenario["protected_rule_ids"],
            "fixture_path": f"harness/evals/runtime-compliance/fixtures/{sid.lower()}.v1.json",
        },
        "boundary_events": [
            {
                "boundary_event_id": "BE-001",
                "sequence": 1,
                "occurred_at": FIXED_BOUNDARY,
                "classification_status": boundary["classification_status"],
                "family_id": boundary["family_id"],
                "class_id": boundary["class_id"],
                "materiality": boundary["materiality"],
                "side_effect_state": boundary["side_effect_state"],
                "publication_ack": "USER_VISIBLE",
                "last_proven_checkpoint": {
                    "ref": f"fixture:{sid.lower()}:checkpoint",
                    "summary": "Synthetic checkpoint before the injected runtime boundary.",
                },
                "recovery_sprint": {
                    "required": True,
                    "opened": True,
                    "sprint_id": f"RS-{sid}",
                    "scope": "Execute the bounded scenario recovery path.",
                    "outcome": "Fake adapter structurally exercised the governed recovery path.",
                    "first_executable_action_id": "A-001",
                    "completion_gate": "Synthetic recovery action is captured and evaluator-sensitive.",
                    "return_condition": "Real external runtime evidence becomes available.",
                    "preserves_parent_outcome": True,
                },
                "summary": scenario["title"],
                "evidence_refs": ["EV-001"],
            }
        ],
        "actions": actions,
        "terminal": {
            "state": "QUIESCENT_BLOCKED",
            "reason_code": "UNAVAILABLE_DEPENDENCY",
            "supervisor_synthesized": False,
            "last_proven_checkpoint": {
                "ref": f"fixture:{sid.lower()}:checkpoint",
                "summary": "Synthetic harness validation is the strongest proven state.",
            },
            "resumption_trigger": "A real external-agent adapter and model configuration are available.",
            "next_transition": {
                "owner": "P67 / skill-evaluation",
                "action": "Run the scenario through a real external-agent adapter.",
                "completion_gate": "Observed runtime receipt validates for the exact model/configuration.",
            },
            "summary": "Fake adapter proves harness plumbing only; target runtime remains unobserved.",
        },
        "proof": {
            "strongest_state": "VALIDATED",
            "runtime_observed": False,
            "proof_ceiling": "Repository fake-adapter harness proof only; target runtime behavior is unobserved.",
            "fingerprint": {
                "effective_prompt": "P07@fixture-p07",
                "governing_contracts": [
                    "prompt-runtime-compliance/v1",
                    "execution-boundary-taxonomy/v1",
                ],
                "scenario_fixture": sid,
                "evaluator": "prompt-runtime-compliance/v1",
                "model_config": f"fp-fake-{sid.lower()}-v1",
                "runtime_host": None,
            },
            "checks": [
                {
                    "check_id": "CK-001",
                    "name": "synthetic-harness",
                    "status": "PASS",
                    "evidence_refs": ["EV-002"],
                },
                {
                    "check_id": "CK-002",
                    "name": "external-runtime",
                    "status": "BLOCKED",
                    "evidence_refs": ["EV-004"],
                },
            ],
        },
        "regression_linkage": {
            "status": "NONE",
            "incident_source": "none",
            "systemic_threshold_met": False,
            "canonical_owner": None,
            "occurrences": [],
            "regression_link_ids": [],
        },
        "evidence": evidence,
        "privacy": {
            "raw_transcript_persisted": False,
            "secrets_persisted": False,
            "hidden_reasoning_persisted": False,
            "redaction_count": 0,
        },
        "reported_violations": reported_violations,
        "observed_runtime": False,
    }
    if mode == "privacy-leak":
        capture["raw_prompt"] = "forbidden fake raw prompt"
    return capture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--mode", choices=["compliant", "rtc04-no-readback", "privacy-leak"], default="compliant")
    args = parser.parse_args()
    payload = build_capture(load(args.scenario), args.mode)
    args.result.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
