#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from scripts import prompt_registry_ops as ops

prompts=json.loads((ROOT/"docs/prompts.json").read_text(encoding="utf-8"))
p04=next(row for row in prompts if row["id"]=="P04")
new_next=(
    "Resolve and reuse the canonical repository plan/handoff owner or a relevant writable active PR owned by this lane. "
    "If none exists and repository mutation is authorized, create the smallest tracked plan artifact following existing repository plan/docs/harness conventions; "
    "persist the complete accepted factoring plan and PARALLEL DISPATCH MANIFEST there and, when P66 or another repository work ledger exists, index the canonical plan/PR, current proof, owner, and executable next action. "
    "Material approval or a material plan change must be synchronized to that owned durable source before P05, P07, or another agent takes over. "
    "If the active PR is unrelated, separately owned, or not writable by this lane, do not modify it; use or create an owned tracked plan/handoff artifact instead. "
    "If the planning task is explicitly read-only or repository mutation is forbidden, keep the chat plan PROVISIONAL and name durable-plan synchronization as BLOCKED. "
    "Route execution to P07 from the validated manifest. "
    "If graph width is at least two, every dependency-ready lane must have an autonomous execution adapter or an explicit AUTONOMY_GAP with a machine-executable bootstrap/repair owner; do not make the operator launch chats. "
    "Validate the JSON manifest with `scripts/prompt_parallel_dispatch.py` before P07 consumes it."
)
required=[
    "following existing repository plan/docs/harness conventions",
    "canonical plan/PR, current proof, owner, and executable next action",
    "before P05, P07, or another agent takes over",
    "unrelated, separately owned, or not writable",
    "explicitly read-only or repository mutation is forbidden",
    "every dependency-ready lane must have an autonomous execution adapter",
    "do not make the operator launch chats",
    "Validate the JSON manifest",
]
missing=[x for x in required if x not in new_next]
if missing:
    raise SystemExit("candidate missing preserved semantics: "+repr(missing))
old_body_phrase="If no owner exists, create the smallest tracked plan artifact before routing to execution."
new_body_phrase="If no owner exists, create the smallest tracked plan artifact before P05/P07 handoff."
if p04["copyContent"].count(old_body_phrase) != 1:
    raise RuntimeError("P04 durable-body anchor missing or duplicated")
new_copy=p04["copyContent"].replace(old_body_phrase,new_body_phrase,1)

result=ops.edit_prompt(
    "P04",
    {"nextStep":new_next,"copyContent":new_copy},
    "NO_CAPABILITY_CHANGE",
    [
        "tests/test_prompt_parallel_execution_contract.py",
        "tests/test_repository_plan_durability.py",
        "docs/plans/PROMPT_INVOCATION_FIDELITY_UBIQUITOUS_SPRINT_MAP.md",
    ],
    "Non-weakening follow-up: restore the complete pre-existing P04 next-step autonomy/PR/read-only semantics while retaining the new material-plan-change and P66 continuity requirements.",
    "COMPRESS",
    "A five-character body compression sharpens the durable transition from generic execution routing to explicit P05/P07 handoff while the metadata restoration reinstates protected autonomy, PR-ownership, and read-only semantics.",
    dry_run=False,
)
print(json.dumps(result,indent=2))
