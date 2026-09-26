#!/usr/bin/env python3
"""Thin executable call-stack prototype for issue-centered READY dispatch.

Success journey
---------------
AFK / CI EVENT
  -> ENTRY: validate_repository_work_ledger.main
  -> ORCHESTRATOR: validate(ledger, adoption)
  -> DOMAIN: READY gate (Gate == none AND Dependencies == none)
  -> RESULT: PASS (AFK-dispatchable)

Failure journey
---------------
AFK / CI EVENT
  -> ENTRY: validate(...)
  -> DOMAIN: READY with residual Dependencies evidence
  -> RESULT: FAIL closed with exact dependency-routing error
"""

from __future__ import annotations

import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / 'scripts'))
from validate_repository_work_ledger import validate  # noqa: E402

ADOPTION = ROOT / '.ai' / 'work-ledger-adoption.json'
PORTABLE = '429237aa41d8712d71859865c9be407ca23d8580'
HEADER = f'''portableContractRef: RepoLedgerInteroperability.v1@{PORTABLE}
canonicalContractCommit: {PORTABLE}
localAuthority: AGENTS.md

# Prototype ledger

Continuation states are not stopping states.
Work item owns progression state.
Branch / PR is execution evidence, not work identity.
READY is AFK-dispatchable only when fully specified and dependency-ready.
PR opened is not completion.
Merged PR alone is not DONE.
DONE is strict.
Canonical terminal action: none; no safe actionable work remains
'''


def _task(dependencies: str, gate: str = 'none') -> str:
    return HEADER + f'''
## TRQ-900 — Prototype READY dispatch

- **Status:** READY
- **Priority:** P1
- **Owner:** prototype-ready-dispatch
- **Work item:** ledger:TRQ-900
- **Branch / PR:** branch:prototype-ready-dispatch
- **Scope:** prove READY dispatch seam
- **Forbidden:** inventing a second ledger authority
- **Dependencies:** {dependencies}
- **References:** `AGENTS.md`
- **Acceptance gate:** READY only when dependency-ready and Gate none
- **Gate:** {gate}
- **Last proof:** artifact:AGENTS.md
- **Next action:** run the focused ledger validator and record its receipt
- **Updated:** 2026-09-26T03:10:00Z
'''


def run_stack(label: str, dependencies: str, gate: str = 'none') -> list[str]:
    with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as handle:
        handle.write(_task(dependencies, gate))
        path = Path(handle.name)
    try:
        errors = validate(path, ADOPTION)
    finally:
        path.unlink(missing_ok=True)
    print(f'[{label}] errors={len(errors)}')
    for error in errors:
        print(f'  - {error}')
    return errors


def main() -> int:
    success = run_stack('SUCCESS_READY', 'none')
    failure = run_stack('FAILURE_READY_RESIDUAL_DEPS', 'ASB #320 merged; planning floor retained')
    if success:
        print('SUCCESS path unexpectedly failed')
        return 1
    if not any('Dependencies: none' in error for error in failure):
        print('FAILURE path did not exercise READY dependency rule')
        return 1
    print('prototype call stacks PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
