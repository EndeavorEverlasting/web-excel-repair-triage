from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "p100_closeout_replay" / "opencode_p122_closeout_01ac559.v1.json"
TERMINAL_NONE = "none; no safe actionable work remains"
P100_REQUIRED_MARKERS = (
    "7. CLOSEOUT CONSISTENCY CHECK",
    "REMAINING GAPS, RISKS, BLOCKERS, INTEGRATION STATE",
    "acknowledged overlapping branch or identity conflict",
    TERMINAL_NONE,
    "FAITHFULNESS_CONTEXT_IGNORED closure failure",
    "reopen closure and execute or route the action",
    "A true terminal case",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "p100-closeout-replay/v1":
        raise ValueError(f"unsupported fixture schema: {payload.get('schema_version')!r}")
    return payload


def _load_p100() -> dict[str, Any]:
    by_id = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}
    if "P100" not in by_id:
        raise ValueError("P100 missing from effective Prompt Kit registry")
    return by_id["P100"]


def _reason_codes(closeout_text: str, evidence: list[dict[str, Any]]) -> list[str]:
    if TERMINAL_NONE not in closeout_text:
        return []

    reasons: list[str] = []
    for item in evidence:
        if not item.get("safe_action_available"):
            continue
        kind = item.get("kind")
        status = str(item.get("status", "")).lower()
        if kind == "required_gate" and item.get("required") and status not in {"success", "passed", "green", "verified"}:
            if "required_gate_failure" not in reasons:
                reasons.append("required_gate_failure")
        if kind == "identity_conflict" and status not in {"resolved", "closed", "verified"}:
            if "acknowledged_identity_conflict" not in reasons:
                reasons.append("acknowledged_identity_conflict")
    return reasons


def evaluate_closeout(closeout_text: str, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    reasons = _reason_codes(closeout_text, evidence)
    rejected = bool(reasons)
    return {
        "accepted_terminal": not rejected,
        "classification": "FAITHFULNESS_CONTEXT_IGNORED" if rejected else "NONE",
        "contradiction_reasons": reasons,
    }


def build_report(fixture: dict[str, Any], p100: dict[str, Any]) -> dict[str, Any]:
    p100_text = p100["copyContent"]
    missing_markers = [marker for marker in P100_REQUIRED_MARKERS if marker not in p100_text]
    p100_present = not missing_markers

    observed = fixture["before"]
    after = evaluate_closeout(observed["observed_closeout_text"], fixture["authoritative_evidence"])
    expected_after = fixture["expected_after"]

    counterexample = fixture["counterexample"]
    counterexample_after = evaluate_closeout(
        counterexample["observed_closeout_text"],
        counterexample["authoritative_evidence"],
    )

    expected_match = all(
        (
            after["accepted_terminal"] == expected_after["accepted_terminal"],
            after["classification"] == expected_after["classification"],
            after["contradiction_reasons"] == expected_after["contradiction_reasons"],
            counterexample_after["accepted_terminal"] == counterexample["expected_after"]["accepted_terminal"],
            counterexample_after["classification"] == counterexample["expected_after"]["classification"],
            counterexample_after["contradiction_reasons"] == counterexample["expected_after"]["contradiction_reasons"],
        )
    )

    escalation_owner = None
    escalation_reason = None
    if p100_present and not expected_match:
        escalation_owner = "P67"
        escalation_reason = "P100 is present but the bounded replay failed; route recurrence to source-faithfulness eval rather than another wording patch."

    status = "PASS" if p100_present and expected_match else "FAIL"
    return {
        "schema_version": "p100-closeout-replay-result/v1",
        "case_id": fixture["case_id"],
        "status": status,
        "prompt_owner": "P100",
        "p100": {
            "present": p100_present,
            "missing_markers": missing_markers,
            "copy_content_sha256": _sha256_text(p100_text),
        },
        "before": {
            "context_identity": observed["context_identity"],
            "accepted_terminal": observed["accepted_terminal"],
            "observed_closeout_text": observed["observed_closeout_text"],
        },
        "after": {
            "context_identity": f"effective-P100:{_sha256_text(p100_text)}",
            **after,
        },
        "counterexample": {
            "case_id": counterexample["case_id"],
            **counterexample_after,
        },
        "expected_match": expected_match,
        "escalation_owner": escalation_owner,
        "escalation_reason": escalation_reason,
        "proof_ceiling": "Deterministic replay of preserved closeout evidence against the current effective P100 contract. It does not prove hidden OpenCode/model mechanics or a fresh provider-model generation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay the preserved OpenCode closeout against effective P100.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    fixture = _load_fixture(args.fixture)
    p100 = _load_p100()
    report = build_report(fixture, p100)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.summary:
        print(
            "p100_closeout_replay "
            f"status={report['status']} "
            f"before_terminal={report['before']['accepted_terminal']} "
            f"after_terminal={report['after']['accepted_terminal']} "
            f"classification={report['after']['classification']} "
            f"reasons={','.join(report['after']['contradiction_reasons']) or 'none'} "
            f"counterexample_terminal={report['counterexample']['accepted_terminal']} "
            f"escalation={report['escalation_owner'] or 'none'}"
        )

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
