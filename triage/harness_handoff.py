"""Compress run context and validation evidence into the repository handoff contract."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Mapping, Optional, Sequence
from . import harness_operational_discipline as discipline

SECTIONS = ("CONTEXT", "WORK COMMITTED", "VALIDATION", "BLOCKERS / GAPS", "FINAL GIT STATE", "NEXT COMMAND")

def render(context: Mapping[str, object], validation: Mapping[str, object] | None = None) -> str:
    issues = discipline.validate_run_context(context, validation_order_specified=bool(context.get("validation_order")))
    if issues: raise ValueError("invalid run context: " + "; ".join(issues))
    validation = validation or {}
    lines = ["CONTEXT", f"- repo: {context['repo']}", f"- branch/worktree: {context['branch_or_worktree']}", f"- PR/sprint: {context['pr_or_sprint']}", f"- lane: {context['lane']}", f"- owned scope: {context['owned_scope']}", f"- forbidden scope: {context['forbidden_scope']}", "", "WORK COMMITTED", f"- expected artifacts: {context['expected_artifacts']}", "", "VALIDATION", f"- status: {validation.get('status', 'not supplied')}", f"- evidence: {validation.get('evidence', 'not supplied')}", "", "BLOCKERS / GAPS", f"- proof ceiling: {context.get('proof_ceiling', 'not supplied')}", "", "FINAL GIT STATE", f"- state: {validation.get('git_state', 'not supplied')}", "", "NEXT COMMAND", f"- {validation.get('next_command', 'not supplied')}"]
    return "\n".join(lines) + "\n"

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        context = json.loads(args.context.read_text(encoding="utf-8"))
        validation = json.loads(args.validation.read_text(encoding="utf-8")) if args.validation else None
        text = render(context, validation)
        if args.output: args.output.write_text(text, encoding="utf-8")
        else: print(text, end="")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"handoff compression failed: {exc}")
        return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
