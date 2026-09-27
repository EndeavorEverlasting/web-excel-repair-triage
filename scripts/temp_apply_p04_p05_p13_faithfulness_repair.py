#!/usr/bin/env python3
"""One-shot protected P04/P05/P13 faithfulness + systemic recurrence repair.

Temporary execution carrier. The workflow removes it after the protected
lifecycle outputs and retained regressions are validated.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import prompt_registry_ops as ops

BASE_MAIN = "a9dad7322d02f8df8370a56382da4b8e2fbbea41"
PLAN = ROOT / "docs/plans/PROMPT_INVOCATION_FIDELITY_UBIQUITOUS_SPRINT_MAP.md"
OVERRIDES = ROOT / "registry/prompts/prompt-overrides.v1.json"
COVERAGE_BASELINE = ROOT / "harness/evals/prompt-regression/prompt-coverage-baseline.v1.json"
REGRESSION_CONTRACT = ROOT / "harness/contracts/prompt-regression-safety.v1.json"
DEFECT_REGISTER = ROOT / "harness/evals/prompt-regression/defect-families.v1.json"
REGRESSION_VALIDATOR = ROOT / "scripts/validate_prompt_regression_safety.py"
REGRESSION_TEST = ROOT / "tests/test_prompt_regression_safety_prompt.py"
RUNTIME_TEST = ROOT / "tests/test_prompt_runtime_partition_contract.py"
REGRESSION_DOC = ROOT / "docs/PROMPT_REGRESSION_SAFETY.md"
RUNTIME_CONTRACT = ROOT / "harness/contracts/planning-runtime-partition.v1.json"
RUNTIME_DESIGN = ROOT / "docs/program/P04_P05_RUNTIME_PARTITION_DESIGN.md"
QUALITY_HISTORY = ROOT / "harness/prompt-compilation/prompt-semantic-migrations.v1.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def append_once(text: str, marker: str, payload: str) -> str:
    if marker in text:
        return text
    return text.rstrip() + "\n\n" + payload.strip() + "\n"


def canonical_prompt(prompt_id: str) -> dict:
    rows = read_json(ROOT / "docs/prompts.json")
    return next(row for row in rows if row["id"] == prompt_id)


def protected_edit(prompt_id: str, patch: dict, rationale: str, compression_rationale: str, evidence_refs: list[str]) -> dict:
    before = canonical_prompt(prompt_id)["copyContent"]
    after = patch.get("copyContent", before)
    if len(after.strip()) < len(before.strip()):
        disposition = "COMPRESS"
    elif len(after.strip()) == len(before.strip()):
        disposition = "PRESERVE"
        compression_rationale = "Semantic repair preserves canonical body length."
    else:
        disposition = "GROWTH_JUSTIFIED"
    if not 300 <= len(after.strip()) <= 12000:
        raise RuntimeError(f"{prompt_id} repaired copyContent length {len(after.strip())} violates lifecycle ceiling")
    return ops.edit_prompt(
        prompt_id,
        patch,
        "NO_CAPABILITY_CHANGE",
        evidence_refs,
        rationale,
        disposition,
        compression_rationale,
        dry_run=False,
    )


# P04 — restore durable transition semantics and canonical runtime-owner clarity.
p04 = canonical_prompt("P04")
p04_copy = p04["copyContent"]
old_p04_runtime = (
    "Before FACTORING PASS, apply the shared planning.runtime_partition contract "
    "(harness/contracts/planning-runtime-partition.v1.json; scripts/planning_runtime_partition.py): "
    "choose exactly one HOST (CURRENT_CHAT_RUNTIME|LOCAL_AGENT_RUNTIME|CI_OR_REMOTE_RUNNER|"
    "OPERATOR_OR_PHYSICAL_RUNTIME|UNKNOWN_RUNTIME) plus zero or more PROVIDER routes. Providers are not hosts. "
    "Keep ChatGPT+provider work on CURRENT_CHAT_RUNTIME; never punt current-runtime work to local agents; "
    "never assign local FS/shell work to CURRENT_CHAT_RUNTIME; inherit sanitized evidence "
    "(type/owner/opaque ref/freshness/proof ceiling); never track private provider IDs; "
    "P07 retains implementation ownership; partition precedes adapter selection. "
    "Internal stage only: LAUNCH ORDER stays first; emit placement table after it. "
    "Manifest lanes require execution_environment, provider_access, required_capabilities, typed evidence_inputs."
)
new_p04_runtime = (
    "Before FACTORING PASS, apply the shared planning.runtime_partition contract "
    "(harness/contracts/planning-runtime-partition.v1.json; canonical implementation "
    "scripts/prompt_runtime_partition.py; scripts/planning_runtime_partition.py is compatibility-only): "
    "choose exactly one HOST (CURRENT_CHAT_RUNTIME|LOCAL_AGENT_RUNTIME|CI_OR_REMOTE_RUNNER|"
    "OPERATOR_OR_PHYSICAL_RUNTIME|UNKNOWN_RUNTIME) plus zero or more PROVIDER routes. Providers are not hosts. "
    "Keep ChatGPT+provider work on CURRENT_CHAT_RUNTIME; never punt current-runtime work to local agents; "
    "never assign local FS/shell work to CURRENT_CHAT_RUNTIME; inherit sanitized evidence "
    "(type/owner/opaque ref/freshness/proof ceiling); never track private provider IDs; "
    "P07 retains implementation ownership; partition precedes adapter selection. "
    "Internal stage only: LAUNCH ORDER stays first; emit placement table after it. "
    "Manifest lanes require execution_environment, provider_access, required_capabilities, typed evidence_inputs."
)
p04_copy = replace_once(p04_copy, old_p04_runtime, new_p04_runtime, "P04 runtime owner")
old_p04_tail = """DURABLE PLAN OUTPUT
- Chat is not the sole owner of an actionable plan; persist the complete map (floor, successors, parallel groups, collisions, scope, artifacts, gates, proof ceiling, deferred work) to the canonical plan/spec/handoff path or writable owned PR.
- If no owner exists, create the smallest tracked plan artifact before routing to execution. Use P66/ledger as index only. Unrelated PRs are not write targets; read-only scope makes durability BLOCKED."""
new_p04_tail = """DURABLE PLAN OUTPUT
- Chat is not the sole owner of an actionable plan; persist the complete map (floor, successors, parallel groups, collisions, scope, artifacts, gates, proof ceiling, deferred work) to the canonical plan/spec/handoff path or writable owned PR.
- Material approval or a material plan change must sync to that owned durable source BEFORE P05, P07, or another agent takes over.
- When P66 or another repository work ledger exists, index the canonical plan/PR, current proof, owner, and executable next action; the ledger is not a substitute for the complete plan.
- If no owner exists, create the smallest tracked plan artifact before routing to execution. Unrelated PRs are not write targets; read-only scope makes durability BLOCKED."""
p04_copy = replace_once(p04_copy, old_p04_tail, new_p04_tail, "P04 durable handoff")
p04_receipt = protected_edit(
    "P04",
    {
        "copyContent": p04_copy,
        "nextStep": (
            "Resolve and reuse the canonical repository plan/handoff owner or a relevant writable active PR owned by this lane. "
            "If none exists and repository mutation is authorized, create the smallest tracked plan artifact; persist the complete accepted factoring plan and PARALLEL DISPATCH MANIFEST there and, when P66/a work ledger exists, index canonical plan/PR + current proof + owner + executable next action. "
            "Material approval or plan change must be synchronized before P05/P07/another agent takes over. Unrelated PRs are not write targets; read-only scope keeps the chat plan PROVISIONAL and durability BLOCKED. "
            "Route implementation to P07 from the validated manifest; graph width >=2 requires an autonomous adapter or explicit AUTONOMY_GAP; validate the JSON manifest before P07 consumes it."
        ),
    },
    "Faithfulness repair: restore P04 durable plan-change synchronization and full P66 continuity indexing lost during UF-1A compression while preserving runtime-partition and P07 ownership.",
    "The restored handoff trigger and ledger continuity fields are unique operational semantics removed by prior compression; compact restoration remains below the canonical body ceiling.",
    [
        "docs/plans/PROMPT_INVOCATION_FIDELITY_UBIQUITOUS_SPRINT_MAP.md",
        "tests/test_repository_plan_durability.py",
        "tests/test_prompt_runtime_partition_contract.py",
        "harness/contracts/planning-runtime-partition.v1.json",
    ],
)

# P05 — self-contained runtime taxonomy + consume P04, fallback only.
p05 = canonical_prompt("P05")
p05_copy = p05["copyContent"]
old_p05_runtime = (
    "RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED\n"
    "Before pack construction, apply the same shared planning.runtime_partition contract as P04 "
    "(harness/contracts/planning-runtime-partition.v1.json; scripts/planning_runtime_partition.py): "
    "one HOST plus zero or more PROVIDER routes. Serialized ≠ local. Complete safe current-runtime work first; "
    "ChatGPT+provider stays CURRENT_CHAT_RUNTIME; do not invent local sprints for already-executed work—pass sanitized evidence forward; "
    "never assign FS/shell-only work to CURRENT_CHAT_RUNTIME; P07 owns implementation; never track private provider IDs. "
    "LAUNCH ORDER remains first substantive section; placement table follows it. Successor panels include EXECUTION ENVIRONMENT, "
    "PROVIDER / ACCESS ROUTE, REQUIRED CAPABILITIES, INHERITED EVIDENCE, RUNTIME HANDOFF."
)
new_p05_runtime = """RUNTIME PARTITION / EXECUTION PLACEMENT — REQUIRED
Before pack construction, apply shared planning.runtime_partition from harness/contracts/planning-runtime-partition.v1.json using canonical scripts/prompt_runtime_partition.py; scripts/planning_runtime_partition.py is compatibility-only.
HOST — choose exactly one: CURRENT_CHAT_RUNTIME | LOCAL_AGENT_RUNTIME | CI_OR_REMOTE_RUNNER | OPERATOR_OR_PHYSICAL_RUNTIME | UNKNOWN_RUNTIME.
PROVIDER / ACCESS ROUTE — zero or more routes composed with the host; a provider is metadata, never the host. Serialized ≠ local. UNKNOWN_RUNTIME is an owner-resolution gate, not permission to guess.
P05 may complete safe dependency-ready CURRENT_CHAT_RUNTIME work only inside P05 planning/evidence/recovery/durability authority when doing so closes a planning dependency or prevents rediscovery. Product/repository implementation remains P07 or another explicit canonical implementation owner's work.
ChatGPT+provider work remains CURRENT_CHAT_RUNTIME with provider metadata. Never assign FS/shell/toolchain-only work to CURRENT_CHAT_RUNTIME. Do not invent a future local sprint for work already executed here; pass its typed sanitized evidence forward. Never track private provider IDs.
LAUNCH ORDER remains the first substantive emitted section; emit placement immediately after it or in the next already-authorized coordination section. Successor panels include EXECUTION ENVIRONMENT, PROVIDER / ACCESS ROUTE, REQUIRED CAPABILITIES, INHERITED EVIDENCE, RUNTIME HANDOFF."""
p05_copy = replace_once(p05_copy, old_p05_runtime, new_p05_runtime, "P05 runtime authority")
old_p05_factor = """3. FACTORING PASS
Before creating sprint panels, factor the work into these ownership surfaces:"""
new_p05_factor = """3. FACTORING PASS — P04 CONSUMER / RECOVERY FALLBACK
When a current accepted P04 factoring artifact exists, consume it as upstream authority: preserve its owners, collisions, dependencies, durable-plan decisions, and proof floor; reconcile only claims shown stale or conflicting by fresher evidence and record the delta. Do not silently re-factor an accepted P04 map or create a competing plan authority.
Only when no usable P04 artifact exists may P05 perform the bounded recovery factoring below. State why upstream factoring is unavailable/stale, recover current evidence, preserve established decisions unless fresher evidence disproves them, and persist/reuse one canonical durable owner.
For that bounded recovery path, classify the work into these ownership surfaces:"""
p05_copy = replace_once(p05_copy, old_p05_factor, new_p05_factor, "P05 P04-consumer boundary")
p05_receipt = protected_edit(
    "P05",
    {
        "copyContent": p05_copy,
        "expectedOutput": (
            "Launch order at the top, compact coordination preamble, then one self-contained copy panel per sprint in that exact order. Consume the current accepted P04 factoring artifact when one exists; bounded fallback factoring is recovery-only. Runtime partition is self-contained, uses the shared planning.runtime_partition contract, and carries sanitized inherited evidence forward."
        ),
        "nextStep": (
            "Consume the current accepted P04 factoring artifact when available; reconcile only fresher contradictory evidence. Use bounded recovery factoring only when no usable P04 artifact exists. Then launch P06/P07/P08 as required, with implementation owned by P07/canonical implementation owner."
        ),
        "proofGate": (
            "Every lane is independently copyable; panel display equals launch order; no shared-preamble assembly. P05 preserves accepted P04 ownership/collision/dependency decisions unless fresher evidence disproves them; fallback factoring is explicit recovery, not competing authority. The self-contained host taxonomy distinguishes host from provider, UNKNOWN is owner-resolution, current-runtime execution is limited to P05 planning/evidence/recovery/durability authority, and P07/canonical owner retains implementation."
        ),
    },
    "Faithfulness repair: make P05 a self-contained serialized planner that consumes accepted P04 factoring, narrows execute-now authority to planning/evidence/durability, and preserves P07 implementation ownership.",
    "P05 requires explicit host taxonomy, upstream-P04 consumption, bounded fallback, and authority scoping that cannot be safely inferred from the prior compressed cross-reference.",
    [
        "docs/plans/PROMPT_INVOCATION_FIDELITY_UBIQUITOUS_SPRINT_MAP.md",
        "tests/test_prompt_runtime_partition_contract.py",
        "harness/contracts/planning-runtime-partition.v1.json",
    ],
)

# Raw P13 — same-mutator reliability gate. Effective P13 is repaired below.
p13 = canonical_prompt("P13")
p13_copy = p13["copyContent"]
raw_anchor = "2. FIND THE EXISTING OWNER BEFORE INVENTING"
raw_gate = """1A. SAME-MUTATOR RELIABILITY GATE
- If recurrence evidence implicates the same agent/model/tool as mutator, mutator selection is part of the defect. Read the prompt-regression-safety mutator-reliability state before assigning repair.
- A mutator in QUARANTINED_CANONICAL_PROMPT_MUTATION may inspect, diagnose, test, or implement non-prompt support, but MUST NOT author/rewrite canonical or effective prompt bodies, prompt semantic profiles/migrations, or generated Prompt Kit output. Use a different authorized author plus canonical lifecycle tooling.
- Never assign a prompt-faithfulness repair back to the mutator that caused the family merely because it is available. One green run does not requalify it.
- Failure-rate claims remain attributed operator evidence unless their corpus is independently enumerated and audited. Requalification requires retained negative + positive controls, exact lifecycle-diff review, and independent acceptance.

2. FIND THE EXISTING OWNER BEFORE INVENTING"""
p13_copy = replace_once(p13_copy, raw_anchor, raw_gate, "raw P13 mutator gate")
p13_receipt = protected_edit(
    "P13",
    {
        "copyContent": p13_copy,
        "expectedOutput": (
            "A minimal rule/validator/hook improvement prototyped and tested against the repeated failure plus a counterexample, with implicated mutator reliability resolved before ownership is assigned; quarantined prompt mutators are excluded from canonical/effective prompt authorship until explicit requalification."
        ),
        "proofGate": (
            "Stale branch state is ruled out before doctrine; at least one PROTOTYPE -> TEST -> CRITIQUE -> REVISE pass occurs; the smallest non-duplicative prevention owner is strengthened; and when recurrence implicates a mutator, a quarantine/requalification state prevents reassignment of canonical prompt repair to the same unreliable author."
        ),
    },
    "Systemic recurrence repair: make mutator reliability part of P13 ownership routing so a repeated prompt-faithfulness defect is not delegated back to the implicated canonical prompt author.",
    "The same-mutator quarantine and evidence-qualified requalification rule is a new recurrence invariant not recoverable from P13's generic owner-search language.",
    [
        "harness/contracts/prompt-regression-safety.v1.json",
        "harness/evals/prompt-regression/defect-families.v1.json",
        "tests/test_prompt_regression_safety_prompt.py",
    ],
)

# Effective P13 override — live Prompt Kit behavior must receive the same rule.
override_payload = read_json(OVERRIDES)
before_override_bytes = OVERRIDES.read_bytes()
effective_p13 = next(row for row in override_payload["overrides"] if row["id"] == "P13")
effective_anchor = """- If the operator used stage labels such as R1/R2 or named proof levels, preserve those exact labels. Do not invent their semantics; recover them from current evidence.

2. CLASSIFY THE FAILURE MODE"""
effective_gate = """- If the operator used stage labels such as R1/R2 or named proof levels, preserve those exact labels. Do not invent their semantics; recover them from current evidence.

1A. SAME-MUTATOR RELIABILITY GATE
- If recurrence evidence implicates the same agent/model/tool as mutator, mutator selection is part of the defect. Read harness/contracts/prompt-regression-safety.v1.json before assigning repair.
- A mutator in QUARANTINED_CANONICAL_PROMPT_MUTATION may inspect, diagnose, test, or implement non-prompt support, but MUST NOT author/rewrite canonical or effective prompt bodies, prompt semantic profiles/migrations, or generated Prompt Kit output. Use a different authorized author plus canonical lifecycle tooling.
- Never assign a prompt-faithfulness repair back to the mutator that caused the family merely because it is available. One green CI run is not requalification.
- Failure-rate claims remain attributed operator evidence unless the underlying corpus is independently enumerated and audited. Requalification requires retained negative + positive controls, exact lifecycle-diff review, and independent acceptance.

2. CLASSIFY THE FAILURE MODE"""
effective_p13["copyContent"] = replace_once(effective_p13["copyContent"], effective_anchor, effective_gate, "effective P13 mutator gate")
effective_p13["expectedOutput"] = (
    "A mandatory P114 execution-posture canary/access matrix; immediate critical-path advancement; P07-owned dependency-graph and capability-ladder dispatch when width >=2; the smallest durable prevention; implicated mutator reliability/quarantine resolved before assigning canonical prompt repair; specialist routing without duplication; and validated default-branch convergence or an exact external/user-only blocker."
)
effective_p13["proofGate"] = (
    "The recurrence is evidence-backed; material execution posture is resolved; P07 proves graph width/capability-ladder behavior; durable prevention has one canonical owner; a mutator implicated in a systemic prompt-faithfulness family cannot author canonical/effective prompt repair while quarantined; focused regression/build/parity checks pass; second-pass review reaches a bounded fixed point; and validated owned head converges to default branch when authorized."
)
after_override_bytes = (json.dumps(override_payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
OVERRIDES.write_bytes(after_override_bytes)

quality = read_json(QUALITY_HISTORY)
override_migration = ops._build_quality_history_migration(
    OVERRIDES,
    before_override_bytes,
    after_override_bytes,
    "P13",
    "NO_CAPABILITY_CHANGE",
    "Strengthen effective P13 with a same-mutator quarantine/requalification gate so repeated prompt-faithfulness repair cannot be assigned back to a quarantined mutator.",
    len(quality.get("migrations", [])),
)
override_migration["focused_tests"] = [
    "tests/test_prompt_regression_safety_prompt.py",
    "tests/test_skill_prompt_registry.py",
    "tests/test_prompt_kit_mainline_delivery.py",
]
quality.setdefault("migrations", []).append(override_migration)
write_json(QUALITY_HISTORY, quality)

baseline = read_json(COVERAGE_BASELINE)
baseline["override_registry_git_blob_sha1"] = ops._git_blob_sha1(after_override_bytes)
p13_binding = next(row for row in baseline["override_bindings"] if row["prompt_id"] == "P13")
marker = "1A. SAME-MUTATOR RELIABILITY GATE"
if marker not in p13_binding["required_markers"]:
    p13_binding["required_markers"].append(marker)
write_json(COVERAGE_BASELINE, baseline)

# Shared systemic owner — mutator quarantine + attributed rate semantics.
contract = read_json(REGRESSION_CONTRACT)
contract["mutator_reliability"] = {
    "rate_claim_policy": (
        "Failure-rate claims from operator feedback are stored as attributed, scoped observations unless the underlying attempt corpus is independently enumerated and audited; attributed evidence may still trigger a conservative quarantine when recurrence is independently repository-evidenced."
    ),
    "same_actor_rule": (
        "When a systemic defect family implicates the same mutator in repeated canonical prompt-faithfulness loss, mutator assignment is part of the defect: do not delegate canonical/effective prompt repair back to that mutator while quarantined."
    ),
    "quarantine_states": [
        "QUARANTINED_CANONICAL_PROMPT_MUTATION",
        "ELIGIBLE_CANONICAL_PROMPT_MUTATION"
    ],
    "restricted_mutators": [
        {
            "mutator": "Cursor",
            "state": "QUARANTINED_CANONICAL_PROMPT_MUTATION",
            "operator_observation": (
                "Operator reports a 100% failure rate across their observed Cursor canonical-prompt-edit attempts. This is attributed operator evidence, not an independently audited statistical corpus."
            ),
            "repository_evidence": [
                "e6737d06a71e2882ad2ce4375007f900314a8a00",
                "8d7eff7749aee8e80ed3d7ff49e22827c6f1a33f",
                "a9dad7322d02f8df8370a56382da4b8e2fbbea41"
            ],
            "forbidden_surfaces": [
                "canonical prompt bodies",
                "effective prompt override bodies",
                "prompt semantic profiles and migrations",
                "prompt quality-history migrations",
                "generated Prompt Kit output"
            ],
            "allowed_roles": [
                "READ_ONLY_ANALYSIS",
                "DIAGNOSIS",
                "TEST_EXECUTION",
                "NON_PROMPT_SUPPORT_IMPLEMENTATION"
            ],
            "requalification_requirements": [
                "Retained negative fixture reproduces the prompt-faithfulness loss.",
                "Positive control proves legitimate non-prompt Cursor work remains allowed.",
                "A candidate canonical prompt mutation is produced outside the quarantined mutator and its exact lifecycle diff is independently reviewed.",
                "Focused semantic, lifecycle, generated-parity, and deterministic-floor checks pass on the exact candidate.",
                "An explicit reviewed contract change promotes the mutator; one green CI run or one apparently correct edit is insufficient."
            ]
        }
    ]
}
write_json(REGRESSION_CONTRACT, contract)

register = read_json(DEFECT_REGISTER)
family_id = "CURSOR_CANONICAL_PROMPT_FAITHFULNESS"
register["families"] = [row for row in register["families"] if row.get("id") != family_id]
register["families"].append(
    {
        "id": family_id,
        "status": "SYSTEMIC",
        "classification": "PROMPT_SEMANTICS",
        "recurring_across_repositories": False,
        "matrix_capture_required": False,
        "canonical_owner": (
            "prompt-regression-safety mutator reliability + P13 recurrence owner; canonical prompt repair must use a non-quarantined author and P79 lifecycle"
        ),
        "prompt_strengthening": "SCOPED_SHARED_POLICY",
        "detector_commands": [
            "python scripts/validate_prompt_regression_safety.py --summary",
            "python -m unittest tests.test_prompt_regression_safety_prompt tests.test_prompt_runtime_partition_contract -v"
        ],
        "prevention_surfaces": [
            "harness/contracts/prompt-regression-safety.v1.json",
            "registry/prompts/prompt-overrides.v1.json",
            "tests/test_prompt_regression_safety_prompt.py",
            "tests/test_prompt_runtime_partition_contract.py",
            "docs/plans/PROMPT_INVOCATION_FIDELITY_UBIQUITOUS_SPRINT_MAP.md"
        ],
        "regression_gate": "tests/test_prompt_regression_safety_prompt.py",
        "local_first_requirement": (
            "Before assigning canonical/effective Prompt Kit mutation, resolve mutator reliability. Cursor remains quarantined from prompt-body/profile/migration/generated-output authorship until the explicit requalification gate passes. The operator's reported 100% observed failure rate is retained as attributed evidence, not presented as an independently audited statistic."
        ),
        "occurrences": [
            {
                "repository": "EndeavorEverlasting/web-excel-repair-triage",
                "commit": "e6737d06a71e2882ad2ce4375007f900314a8a00",
                "summary": (
                    "Repair history records restoration of P07 non-parallel proof gates after prior prompt strengthening dropped protected semantics; the repair commit is Cursor-co-authored and evidences the recurring prompt-faithfulness family."
                )
            },
            {
                "repository": "EndeavorEverlasting/web-excel-repair-triage",
                "commit": "8d7eff7749aee8e80ed3d7ff49e22827c6f1a33f",
                "summary": (
                    "Repair history explicitly records P07 closeout and phase-continuity requirements lost during prompt shortening; the repair commit is Cursor-co-authored and independently evidences recurring semantic loss."
                )
            },
            {
                "repository": "EndeavorEverlasting/web-excel-repair-triage",
                "commit": "a9dad7322d02f8df8370a56382da4b8e2fbbea41",
                "summary": (
                    "Merged post-UF-1A faithfulness audit records F1-F7 after the Cursor-authored/assisted #665 implementation passed existing checks yet still weakened P04 durability and P05 ownership/self-containment semantics."
                )
            }
        ]
    }
)
register["evaluation_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
write_json(DEFECT_REGISTER, register)

# Validator hardening — quarantine is executable contract, not prose.
validator = REGRESSION_VALIDATOR.read_text(encoding="utf-8")
contract_anchor = '    _text(recurrence.get("rule"), "recurrence.rule")\n\n    loop = contract.get("required_loop")'
contract_insert = '''    _text(recurrence.get("rule"), "recurrence.rule")

    reliability = contract.get("mutator_reliability")
    if not isinstance(reliability, dict):
        raise RegressionSafetyError("mutator_reliability must be an object")
    expected_reliability_fields = {"rate_claim_policy", "same_actor_rule", "quarantine_states", "restricted_mutators"}
    if set(reliability) != expected_reliability_fields:
        raise RegressionSafetyError("mutator_reliability fields do not match contract")
    rate_policy = _text(reliability.get("rate_claim_policy"), "mutator_reliability.rate_claim_policy")
    if "attributed" not in rate_policy.lower() or "audited" not in rate_policy.lower():
        raise RegressionSafetyError("mutator reliability must distinguish attributed from audited rate claims")
    _text(reliability.get("same_actor_rule"), "mutator_reliability.same_actor_rule")
    states = _string_list(reliability.get("quarantine_states"), "mutator_reliability.quarantine_states", min_items=2)
    if set(states) != {"QUARANTINED_CANONICAL_PROMPT_MUTATION", "ELIGIBLE_CANONICAL_PROMPT_MUTATION"}:
        raise RegressionSafetyError("mutator reliability quarantine state vocabulary drifted")
    restricted = reliability.get("restricted_mutators")
    if not isinstance(restricted, list) or not restricted:
        raise RegressionSafetyError("mutator_reliability.restricted_mutators must be non-empty")
    seen_mutators: set[str] = set()
    cursor = None
    required_mutator_fields = {
        "mutator", "state", "operator_observation", "repository_evidence",
        "forbidden_surfaces", "allowed_roles", "requalification_requirements",
    }
    for index, mutator in enumerate(restricted):
        if not isinstance(mutator, dict) or set(mutator) != required_mutator_fields:
            raise RegressionSafetyError(f"restricted_mutator[{index}] fields do not match contract")
        name = _text(mutator.get("mutator"), f"restricted_mutator[{index}].mutator")
        if name in seen_mutators:
            raise RegressionSafetyError(f"duplicate restricted mutator: {name}")
        seen_mutators.add(name)
        if mutator.get("state") not in states:
            raise RegressionSafetyError(f"invalid mutator reliability state: {name}")
        _text(mutator.get("operator_observation"), f"{name}.operator_observation")
        evidence = _string_list(mutator.get("repository_evidence"), f"{name}.repository_evidence", min_items=2)
        if any(not COMMIT_RE.fullmatch(commit) for commit in evidence):
            raise RegressionSafetyError(f"{name} repository evidence must be lowercase 40-hex commits")
        _string_list(mutator.get("forbidden_surfaces"), f"{name}.forbidden_surfaces", min_items=3)
        _string_list(mutator.get("allowed_roles"), f"{name}.allowed_roles", min_items=2)
        requirements = _string_list(mutator.get("requalification_requirements"), f"{name}.requalification_requirements", min_items=4)
        joined_requirements = " ".join(requirements).lower()
        for phrase in ("negative", "positive", "lifecycle diff", "explicit reviewed"):
            if phrase not in joined_requirements:
                raise RegressionSafetyError(f"{name} requalification is missing concept: {phrase}")
        if name == "Cursor":
            cursor = mutator
    if cursor is None:
        raise RegressionSafetyError("Cursor systemic prompt-faithfulness quarantine must be retained")
    if cursor.get("state") != "QUARANTINED_CANONICAL_PROMPT_MUTATION":
        raise RegressionSafetyError("Cursor canonical prompt mutation quarantine may change only through explicit reviewed requalification")
    observation = str(cursor.get("operator_observation", "")).lower()
    if "100%" not in observation or "operator" not in observation or "not an independently audited" not in observation:
        raise RegressionSafetyError("Cursor operator-rate observation must remain attributed and explicitly unaudited")
    forbidden_text = " ".join(cursor.get("forbidden_surfaces", [])).lower()
    for phrase in ("canonical prompt", "effective prompt", "semantic profiles", "generated prompt kit"):
        if phrase not in forbidden_text:
            raise RegressionSafetyError(f"Cursor quarantine missing forbidden surface: {phrase}")

    loop = contract.get("required_loop")'''
validator = replace_once(validator, contract_anchor, contract_insert, "regression validator contract gate")
register_anchor = '''    if ".gitattributes" not in line_ending_family.get("prevention_surfaces", []):
        raise RegressionSafetyError("LINE_ENDING_DRIFT must retain .gitattributes prevention owner")

    return {'''
register_insert = '''    if ".gitattributes" not in line_ending_family.get("prevention_surfaces", []):
        raise RegressionSafetyError("LINE_ENDING_DRIFT must retain .gitattributes prevention owner")

    cursor_family = next(
        (family for family in families if family.get("id") == "CURSOR_CANONICAL_PROMPT_FAITHFULNESS"),
        None,
    )
    if cursor_family is None:
        raise RegressionSafetyError("defect register must retain CURSOR_CANONICAL_PROMPT_FAITHFULNESS systemic family")
    if cursor_family.get("classification") != "PROMPT_SEMANTICS":
        raise RegressionSafetyError("CURSOR_CANONICAL_PROMPT_FAITHFULNESS must remain PROMPT_SEMANTICS")
    if cursor_family.get("recurring_across_repositories") is not False:
        raise RegressionSafetyError("Cursor prompt-faithfulness family is currently Triage-scoped")
    if cursor_family.get("matrix_capture_required") is not False:
        raise RegressionSafetyError("Cursor prompt-faithfulness recurrence must not depend on retrospective matrix capture")
    cursor_prevention = set(cursor_family.get("prevention_surfaces", []))
    for required_surface in (
        "harness/contracts/prompt-regression-safety.v1.json",
        "registry/prompts/prompt-overrides.v1.json",
        "tests/test_prompt_regression_safety_prompt.py",
    ):
        if required_surface not in cursor_prevention:
            raise RegressionSafetyError(
                f"CURSOR_CANONICAL_PROMPT_FAITHFULNESS missing prevention surface: {required_surface}"
            )

    return {'''
validator = replace_once(validator, register_anchor, register_insert, "regression validator family retention")
REGRESSION_VALIDATOR.write_text(validator, encoding="utf-8")

# Focused negative/positive controls retained in deterministic floor.
tests = REGRESSION_TEST.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    '{"TRAILING_WHITESPACE", "PROVIDER_QUOTA_TERMINATION", "LINE_ENDING_DRIFT", "PROMPT_REGRESSION_COVERAGE_GAP"}',
    '{"TRAILING_WHITESPACE", "PROVIDER_QUOTA_TERMINATION", "LINE_ENDING_DRIFT", "PROMPT_REGRESSION_COVERAGE_GAP", "CURSOR_CANONICAL_PROMPT_FAITHFULNESS"}',
    "regression family expected set",
)
test_anchor = '''    def test_required_loop_retains_negative_and_positive_controls(self) -> None:
'''
new_tests = '''    def test_cursor_prompt_mutator_quarantine_is_retained(self) -> None:
        reliability = self.contract["mutator_reliability"]
        cursor = next(item for item in reliability["restricted_mutators"] if item["mutator"] == "Cursor")
        self.assertEqual(cursor["state"], "QUARANTINED_CANONICAL_PROMPT_MUTATION")
        observation = cursor["operator_observation"]
        self.assertIn("100%", observation)
        self.assertIn("Operator reports", observation)
        self.assertIn("not an independently audited statistical corpus", observation)
        self.assertGreaterEqual(len(cursor["repository_evidence"]), self.contract["recurrence"]["systemic_threshold"])
        forbidden = " ".join(cursor["forbidden_surfaces"])
        for phrase in ("canonical prompt bodies", "effective prompt override bodies", "prompt semantic profiles and migrations", "generated Prompt Kit output"):
            self.assertIn(phrase, forbidden)
        self.assertIn("NON_PROMPT_SUPPORT_IMPLEMENTATION", cursor["allowed_roles"])

    def test_cursor_quarantine_cannot_silently_promote_itself(self) -> None:
        contract = copy.deepcopy(self.contract)
        cursor = next(item for item in contract["mutator_reliability"]["restricted_mutators"] if item["mutator"] == "Cursor")
        cursor["state"] = "ELIGIBLE_CANONICAL_PROMPT_MUTATION"
        with self.assertRaisesRegex(regression.RegressionSafetyError, "Cursor canonical prompt mutation quarantine"):
            regression.validate_contract(contract)

    def test_cursor_prompt_faithfulness_family_cannot_disappear(self) -> None:
        register = copy.deepcopy(self.register)
        register["families"] = [item for item in register["families"] if item["id"] != "CURSOR_CANONICAL_PROMPT_FAITHFULNESS"]
        with self.assertRaisesRegex(regression.RegressionSafetyError, "retain CURSOR_CANONICAL_PROMPT_FAITHFULNESS"):
            regression.validate_register(register, self.contract)

    def test_effective_p13_enforces_same_mutator_quarantine(self) -> None:
        overrides = regression.load_json(regression.OVERRIDE_REGISTRY_PATH)
        p13 = next(item for item in overrides["overrides"] if item["id"] == "P13")
        copy_content = p13["copyContent"]
        self.assertIn("1A. SAME-MUTATOR RELIABILITY GATE", copy_content)
        self.assertIn("QUARANTINED_CANONICAL_PROMPT_MUTATION", copy_content)
        self.assertIn("MUST NOT author/rewrite canonical or effective prompt bodies", copy_content)
        self.assertIn("One green CI run is not requalification", copy_content)
        self.assertIn("attributed operator evidence", copy_content)

    def test_non_prompt_cursor_role_remains_positive_control(self) -> None:
        cursor = next(item for item in self.contract["mutator_reliability"]["restricted_mutators"] if item["mutator"] == "Cursor")
        self.assertIn("READ_ONLY_ANALYSIS", cursor["allowed_roles"])
        self.assertIn("TEST_EXECUTION", cursor["allowed_roles"])
        self.assertIn("NON_PROMPT_SUPPORT_IMPLEMENTATION", cursor["allowed_roles"])

    def test_required_loop_retains_negative_and_positive_controls(self) -> None:
'''
tests = replace_once(tests, test_anchor, new_tests, "regression quarantine tests")
REGRESSION_TEST.write_text(tests, encoding="utf-8")

runtime_tests = RUNTIME_TEST.read_text(encoding="utf-8")
runtime_tests = replace_once(
    runtime_tests,
    'self.assertIn("same shared planning.runtime_partition contract as P04", text)',
    'self.assertIn("apply shared planning.runtime_partition", text)',
    "P05 old cross-reference assertion",
)
runtime_tests = replace_once(
    runtime_tests,
    'self.assertIn("LAUNCH ORDER remains first substantive section", text)',
    'self.assertIn("LAUNCH ORDER remains the first substantive emitted section", text)',
    "P05 launch-order wording assertion",
)
runtime_test_anchor = '''    def test_dispatch_contract_requires_runtime_partition_lane_fields(self) -> None:
'''
runtime_new_tests = '''    def test_p04_restores_durable_handoff_and_canonical_runtime_owner(self) -> None:
        text = self.prompts["P04"]["copyContent"]
        self.assertIn("canonical implementation scripts/prompt_runtime_partition.py", text)
        self.assertIn("scripts/planning_runtime_partition.py is compatibility-only", text)
        self.assertIn("Material approval or a material plan change must sync", text)
        self.assertIn("BEFORE P05, P07, or another agent takes over", text)
        self.assertIn("canonical plan/PR, current proof, owner, and executable next action", text)
        self.assertLess(text.index("RUNTIME PARTITION / EXECUTION PLACEMENT"), text.index("FACTORING PASS"))

    def test_p05_consumes_p04_and_fallback_is_recovery_only(self) -> None:
        text = self.prompts["P05"]["copyContent"]
        self.assertIn("P04 CONSUMER / RECOVERY FALLBACK", text)
        self.assertIn("When a current accepted P04 factoring artifact exists, consume it as upstream authority", text)
        self.assertIn("Do not silently re-factor an accepted P04 map", text)
        self.assertIn("Only when no usable P04 artifact exists", text)
        self.assertIn("planning/evidence/recovery/durability authority", text)
        self.assertIn("Product/repository implementation remains P07", text)
        self.assertNotIn("Complete safe current-runtime work first", text)

    def test_p05_runtime_taxonomy_is_self_contained(self) -> None:
        text = self.prompts["P05"]["copyContent"]
        runtime_slice = text.split("RUNTIME PARTITION / EXECUTION PLACEMENT", 1)[1].split("3. FACTORING PASS", 1)[0]
        for host in ("CURRENT_CHAT_RUNTIME", "LOCAL_AGENT_RUNTIME", "CI_OR_REMOTE_RUNNER", "OPERATOR_OR_PHYSICAL_RUNTIME", "UNKNOWN_RUNTIME"):
            self.assertIn(host, runtime_slice)
        self.assertIn("a provider is metadata, never the host", runtime_slice)
        self.assertIn("UNKNOWN_RUNTIME is an owner-resolution gate", runtime_slice)
        self.assertIn("canonical scripts/prompt_runtime_partition.py", runtime_slice)
        self.assertIn("scripts/planning_runtime_partition.py is compatibility-only", runtime_slice)

    def test_runtime_partition_contract_status_matches_integrated_consumption(self) -> None:
        shared = json.loads((ROOT / "harness/contracts/planning-runtime-partition.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(shared["status"], "INTEGRATED")
        self.assertEqual(shared["canonical_implementation"], "scripts/prompt_runtime_partition.py")

    def test_dispatch_contract_requires_runtime_partition_lane_fields(self) -> None:
'''
runtime_tests = replace_once(runtime_tests, runtime_test_anchor, runtime_new_tests, "runtime faithfulness tests")
RUNTIME_TEST.write_text(runtime_tests, encoding="utf-8")

# F7 status reconciliation.
runtime_contract = read_json(RUNTIME_CONTRACT)
if runtime_contract.get("status") != "PROTOTYPE":
    raise RuntimeError(f"unexpected runtime contract status before repair: {runtime_contract.get('status')}")
runtime_contract["status"] = "INTEGRATED"
runtime_contract["proof_ceiling"] = (
    "Integrated repository/static/CI planning seam for P04/P05 host/provider placement and sanitized evidence projection. Does not prove live provider authentication, downstream model obedience, or external runtime behavior."
)
write_json(RUNTIME_CONTRACT, runtime_contract)

design = RUNTIME_DESIGN.read_text(encoding="utf-8")
design = replace_once(
    design,
    "**Status:** PROTOTYPE / pre-broad-implementation design gate",
    "**Status:** INTEGRATED shared planning seam; original prototype gate satisfied by UF-1A. Live provider/model obedience remains outside repository proof.",
    "runtime design status",
)
RUNTIME_DESIGN.write_text(design, encoding="utf-8")

# Durable plan and docs record systemic escalation, not raw chat.
plan = PLAN.read_text(encoding="utf-8")
systemic_note = """### Systemic recurrence escalation — canonical prompt mutator quarantine

The post-UF-1A review crossed the repository recurrence threshold. Repository history independently records repeated prompt-semantic restoration after Cursor-authored/assisted changes, including e6737d06... and 8d7eff77...; this plan merge at a9dad732... records the current P04/P05 recurrence after #665.

The operator additionally reports a 100% failure rate across their observed Cursor canonical-prompt-edit attempts. That rate is retained as attributed operator evidence and is not represented as an independently audited statistical corpus.

Disposition:
- Cursor is QUARANTINED_CANONICAL_PROMPT_MUTATION for canonical/effective prompt bodies, prompt semantic/profile/history mutation, and generated Prompt Kit output.
- Cursor may still perform read-only analysis, diagnosis, test execution, and non-prompt support implementation.
- Canonical prompt repair is authored by a non-quarantined owner and executed through the P79 lifecycle.
- Requalification requires retained negative + positive controls, exact lifecycle-diff review, semantic/build/parity proof, deterministic-floor proof, and an explicit reviewed contract change. One green CI run is insufficient.

Canonical prevention owner: harness/contracts/prompt-regression-safety.v1.json.
Defect family: CURSOR_CANONICAL_PROMPT_FAITHFULNESS.
"""
plan = append_once(plan, "### Systemic recurrence escalation — canonical prompt mutator quarantine", systemic_note)
PLAN.write_text(plan, encoding="utf-8")

doc = REGRESSION_DOC.read_text(encoding="utf-8")
doc_note = """## Mutator reliability and canonical-prompt quarantine

Recurring semantic loss can implicate not only a missing rule, but the choice of mutator. When the same agent/model/tool repeatedly authors canonical prompt changes that later require semantic restoration, assigning the repair back to that mutator reproduces the process defect.

The retained family is CURSOR_CANONICAL_PROMPT_FAITHFULNESS. Repository commit history independently satisfies the systemic recurrence threshold. The operator also reports a 100% failure rate across their observed Cursor canonical-prompt-edit attempts; the repository records that statement as attributed operator evidence, not as an independently audited statistical rate.

While the family remains quarantined, Cursor may inspect, diagnose, execute tests, and implement non-prompt support surfaces, but it may not author canonical/effective prompt bodies, prompt semantic/profile/history transitions, or generated Prompt Kit output. Requalification is explicit and evidence-bearing: negative + positive controls, exact lifecycle-diff review, semantic/build/parity gates, deterministic-floor proof, and a reviewed contract transition. A single green CI run is not requalification.
"""
doc = append_once(doc, "## Mutator reliability and canonical-prompt quarantine", doc_note)
REGRESSION_DOC.write_text(doc, encoding="utf-8")

# Rebuild effective Prompt Kit after override mutation and validate history.
ops.registry.build(ops.registry.DEFAULT_OUTPUT)
parity, _count = ops._validate_site_parity()
if not parity:
    raise RuntimeError("generated Prompt Kit parity failed after effective P13 repair")
quality_errors = ops.quality_history.validate()
if quality_errors:
    raise RuntimeError("Prompt Quality History failed after effective P13 migration: " + " | ".join(quality_errors))

print(json.dumps({
    "status": "REPAIR_APPLIED",
    "base_main": BASE_MAIN,
    "P04": p04_receipt,
    "P05": p05_receipt,
    "P13_raw": p13_receipt,
    "P13_effective_override_migration": override_migration["migration_id"],
    "cursor_mutator_state": "QUARANTINED_CANONICAL_PROMPT_MUTATION",
    "runtime_partition_status": "INTEGRATED",
    "site_parity": True,
    "proof_ceiling": "Repository canonical/effective prompt lifecycle + static regression/build parity only; live downstream model obedience remains unproven.",
}, indent=2))
