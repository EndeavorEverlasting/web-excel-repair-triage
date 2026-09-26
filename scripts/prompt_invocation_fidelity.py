#!/usr/bin/env python3
"""Classify prompt invocation fidelity for operational Prompt Kit use.

An invoked operational prompt must execute unless the operator explicitly
requests prompt mutation (rewrite/upgrade/edit/strengthen/compress/critique/redesign).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness/contracts/prompt-retrospective-evaluation.v1.json"

MUTATION_INTENT_RE = re.compile(
    r"\b(rewrite|reword|upgrade|edit|strengthen|compress|critique|redesign|"
    r"improve the prompt|revise the prompt|mutate the prompt)\b",
    re.IGNORECASE,
)
REWRITE_OUTPUT_RE = re.compile(
    r"\b(here(?:'| i)s (?:an )?improved (?:version of )?(?:the )?prompt|"
    r"rewritten prompt|suggested prompt rewrite|prompt rewrite|"
    r"improved copyContent|updated prompt body)\b",
    re.IGNORECASE,
)
EXECUTION_SIGNAL_RE = re.compile(
    r"\b(LAUNCH ORDER|PARALLEL DISPATCH MANIFEST|FACTORING PASS|"
    r"owned scope|validation|commit|pull request|worktree|"
    r"dispatch manifest|sprint panel)\b",
    re.IGNORECASE,
)


class InvocationFidelityError(ValueError):
    pass


def _contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    merit = contract.get("terminal_merits", {}).get("INVOCATION_FIDELITY")
    if not isinstance(merit, dict):
        raise InvocationFidelityError("INVOCATION_FIDELITY merit missing from retrospective contract")
    return contract


def classify_invocation_fidelity(event: dict[str, Any]) -> dict[str, Any]:
    """Return terminal INVOCATION_FIDELITY for one prompt-use event."""
    contract = _contract()
    allowed = set(contract["terminal_merits"]["INVOCATION_FIDELITY"]["values"])
    if not isinstance(event, dict):
        raise InvocationFidelityError("event must be an object")

    prompt_id = str(event.get("prompt_id") or "").strip().upper()
    operator_request = str(event.get("operator_request") or "")
    agent_output = str(event.get("agent_output") or "")
    executed = bool(event.get("executed_workflow", False))
    produced_artifacts = event.get("produced_artifacts") or []
    if produced_artifacts is not None and not isinstance(produced_artifacts, list):
        raise InvocationFidelityError("produced_artifacts must be a list when present")

    mutation_requested = bool(MUTATION_INTENT_RE.search(operator_request))
    rewrite_output = bool(REWRITE_OUTPUT_RE.search(agent_output))
    execution_signals = (
        bool(EXECUTION_SIGNAL_RE.search(agent_output))
        or executed
        or bool(produced_artifacts)
    )

    if event.get("applicable") is False:
        rating = "NOT_APPLICABLE"
    elif not prompt_id or not operator_request:
        rating = "UNKNOWN"
    elif mutation_requested:
        rating = "PASS"
    elif rewrite_output and not execution_signals:
        rating = "FAIL"
    elif execution_signals:
        rating = "PASS"
    else:
        rating = "UNKNOWN"

    if rating not in allowed:
        raise InvocationFidelityError(f"invalid rating: {rating}")
    return {
        "schema_version": "prompt-invocation-fidelity-result/v1",
        "prompt_id": prompt_id or None,
        "INVOCATION_FIDELITY": rating,
        "mutation_requested": mutation_requested,
        "terminal": rating == "FAIL",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON event path")
    args = parser.parse_args(argv)
    try:
        event = json.loads(Path(args.input).read_text(encoding="utf-8"))
        print(json.dumps(classify_invocation_fidelity(event), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, InvocationFidelityError) as exc:
        print(f"invocation-fidelity error: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
