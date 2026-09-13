from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
PROMPTS = ROOT / "docs" / "prompts.json"
AI_PROMPTS = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TEST = ROOT / "tests" / "test_repository_plan_durability.py"
STALE_TOPOLOGY_ROADMAP = ROOT / "harness" / "prompt-topology" / "PHASE_B_C_ROADMAP.md"
PLAN_MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"
STATE_MARKER = "EVIDENCE STATE / NO PROMOTION CONTRACT"
REMOTE_MARKER = "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT"


def _replace_policy_section(text: str, marker: str, replacement: str) -> str:
    if marker not in text:
        anchor = f"\n\n{REMOTE_MARKER}"
        if anchor not in text:
            raise SystemExit(f"Missing policy anchor: {REMOTE_MARKER}")
        return text.replace(anchor, "\n\n" + replacement.rstrip() + anchor, 1)
    start = text.index(marker)
    end = text.find(f"\n\n{REMOTE_MARKER}", start)
    if end < 0:
        raise SystemExit(f"Cannot bound policy section: {marker}")
    return text[:start] + replacement.rstrip() + text[end:]


def patch_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    additions = (
        " When repository planning produces a materially actionable plan, persist the complete plan to tracked "
        "repository/provider state before treating planning as complete or handing execution to another agent; "
        "chat text is provisional rather than canonical repository state. If an active pull request exists, the "
        "approved plan must be present there directly or by an explicit canonical tracked-plan reference."
        " Do not promote evidence states: a plan, design, schema, config entry, test, branch, PR, or mention in "
        "another chat is not proof that behavior is wired, implemented, validated, integrated, deployed, or "
        "observed. Name the strongest state actually proven by refreshed repository/provider/runtime evidence."
    )
    suffix = policy["next_step_suffix"]
    if "chat text is provisional rather than canonical repository state" not in suffix:
        suffix = suffix.rstrip() + additions.split(" Do not promote evidence states:", 1)[0]
    if "Do not promote evidence states" not in suffix:
        suffix = suffix.rstrip() + " Do not promote evidence states:" + additions.split(" Do not promote evidence states:", 1)[1]
    policy["next_step_suffix"] = suffix

    plan_section = """REPOSITORY PLAN DURABILITY CONTRACT
- When repository planning produces a materially actionable roadmap, sprint map, architecture plan, migration plan, phase plan, implementation sequence, or other execution dependency, the complete accepted plan MUST live in durable repository/provider state; chat alone is not a canonical planning surface.
- Chat may carry a provisional sketch, critique, or orientation note. Before the plan becomes an execution dependency, is called approved/ready, or is handed to another agent, persist the complete plan in the existing canonical tracked plan/spec/handoff path or active pull request. Reuse an existing plan owner before creating another plan file.
- If an active pull request exists, approval must be reflected there immediately: include the complete plan or the exact committed canonical plan path and revision. A plan approved in chat triggers synchronization, not closure.
- Multi-phase repository work must persist the whole phase map, not only the current phase: completed floor, successor phases, dependencies, owned/forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and deferred work.
- When P66 or another repository work ledger exists, use it as the continuity index that points to the canonical plan/PR, current proof, owner, and next action; do not replace the complete plan with a terse ledger row or duplicate implementation specification.
- If a materially actionable plan changes, update the durable plan/PR before handoff or completion. Later agents must be able to recover it from refreshed repository/provider truth without the originating chat.
- Closeout is invalid when an actionable repository plan, approved revision, or successor-phase map exists only in chat. Persist it first, then report its canonical path/PR and exact revision.
"""
    state_section = """EVIDENCE STATE / NO PROMOTION CONTRACT
- Keep repository progress claims typed. Distinguish PLANNED/DESIGNED, TRACKED, IMPLEMENTED, WIRED/REACHABLE, VALIDATED, INTEGRATED, DEPLOYED, and OBSERVED when those states matter.
- Evidence for a weaker state never silently proves a stronger one. Design/config does not prove implementation; implementation does not prove wiring; a test/branch/PR does not prove mainline integration; integration does not prove deployment; deployment does not prove observed runtime behavior.
- A different chat, agent, worktree, branch, or PR is evidence to inspect, not completion evidence for this thread. Promote state only after refreshed repository/provider/runtime truth resolves the exact artifact, commit, integration, deployment, or observation that proves it.
- Do not infer that a named future phase was executed because design ingredients, schema fields, tests, branches, or historical plans exist. Report the strongest proven state and the missing transition explicitly.
- Before terminal closeout, compare the requested target state with the strongest proven state. If the missing transition is SAFE & EXECUTABLE, continue; otherwise name the exact blocker. Never manufacture completion by relabeling partial evidence.
"""
    appendix = policy["copy_content_appendix"]
    appendix = _replace_policy_section(appendix, PLAN_MARKER, plan_section)
    appendix = _replace_policy_section(appendix, STATE_MARKER, state_section)
    policy["copy_content_appendix"] = appendix

    forbidden = policy["forbidden_solo_actions"]
    for item in (
        "treat an actionable repository plan that exists only in chat as durable completion or handoff state",
        "promote PLANNED/DESIGNED evidence to IMPLEMENTED, WIRED/REACHABLE, VALIDATED, INTEGRATED, DEPLOYED, or OBSERVED without exact supporting proof",
    ):
        if item not in forbidden:
            forbidden.append(item)

    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_core_owners() -> None:
    prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
    by_id = {prompt["id"]: prompt for prompt in prompts}
    for prompt_id in ("P02", "P04", "P07", "P12"):
        if prompt_id not in by_id:
            raise SystemExit(f"Missing canonical owner: {prompt_id}")

    p02 = by_id["P02"]
    p02["expectedOutput"] = (
        "A context-grounded launch order and executable build panels privately prototyped and checked against "
        "recovered requirements/repo evidence, with any materially actionable repository launch map persisted in "
        "the canonical tracked plan/handoff surface or active PR before another agent depends on it. Chat is an "
        "orientation/copy surface, not the sole durable owner."
    )
    p02["nextStep"] = (
        "Prototype and validate the launch pack; persist any actionable repository plan to the existing canonical "
        "plan/handoff path or active PR, update the work ledger to reference it when one exists, then present the "
        "concise chat-facing panels and launch the first executable panel from that durable state."
    )
    p02["proofGate"] = (
        "Recovered context is reconciled; at least one prototype -> critique -> revise pass occurs; every gap has "
        "an executable owner or no-build evidence; and every actionable repository launch map is recoverable in "
        "full from tracked repository/provider state and reflected in the active PR when one exists."
    )
    p02_block = """DURABLE REPOSITORY PLAN HANDOFF
- A chat launch pack is provisional presentation, not canonical repository state. Persist every materially actionable repository launch map in the existing canonical tracked plan/handoff surface or active PR before another agent depends on it.
- If an active PR exists, synchronize approval there immediately: include the complete plan or exact committed canonical plan path/revision. Approval in chat triggers repository/PR synchronization in the same execution thread.
- When P66 or another repository work ledger exists, update it to point at the canonical plan/PR, proof, owner, and next action; do not turn the ledger or chat into a duplicate implementation specification.
- Do not close a repository-planning conversation with a plan later agents can recover only by finding this chat.
"""
    if "DURABLE REPOSITORY PLAN HANDOFF" in p02["copyContent"]:
        p02["copyContent"] = p02["copyContent"].split("DURABLE REPOSITORY PLAN HANDOFF", 1)[0].rstrip() + "\n\n" + p02_block
    else:
        p02["copyContent"] = p02["copyContent"].rstrip() + "\n\n" + p02_block

    p04 = by_id["P04"]
    p04["expectedOutput"] = (
        "Launch order, ordered copy-panel sprint candidates, and factoring ledgers, with the complete actionable "
        "repository plan persisted to the existing canonical tracked plan/spec/handoff owner or active PR instead "
        "of existing only in chat."
    )
    p04["nextStep"] = (
        "Persist the complete accepted factoring plan to the canonical repository plan/handoff path or active PR, "
        "update P66/the repository work ledger to reference it when present, then use P05 or P07 from that revision."
    )
    p04["proofGate"] = (
        "Dependencies, collision ownership, exact panel sequence, successor phases, and proof gates are explicit; "
        "the complete actionable repository plan is tracked/recoverable from provider truth, and any active PR "
        "contains or points to the approved revision."
    )
    p04_block = """DURABLE PLAN OUTPUT
- Chat may present the plan, but it may not be the sole owner of an actionable repository plan. Commit the complete accepted sprint map to the existing canonical plan/spec/handoff path or carry it directly in the active PR.
- Persist the whole dependency map: completed floor, ordered successor phases, parallel groups, collision ownership, owned/forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and deferred work.
- When P66 or another repository work ledger exists, use it to index the canonical plan, current proof, owner, and next action; a terse ledger row is not a substitute for the complete plan.
- Approval or material plan change in chat triggers synchronization to the tracked plan/PR before P05/P07 or another agent takes over.
"""
    if "DURABLE PLAN OUTPUT" in p04["copyContent"]:
        p04["copyContent"] = p04["copyContent"].split("DURABLE PLAN OUTPUT", 1)[0].rstrip() + "\n\n" + p04_block
    else:
        p04["copyContent"] = p04["copyContent"].rstrip() + "\n\n" + p04_block

    p12 = by_id["P12"]
    if "durable repository/provider state" not in p12["expectedOutput"]:
        p12["expectedOutput"] = p12["expectedOutput"].rstrip(".") + (
            ", with actionable repository continuations recoverable from durable repository/provider state rather than chat alone."
        )
    p12["nextStep"] = (
        "Before final compression, reconcile requested target state against refreshed repository/provider truth; "
        "persist any actionable plan/successor map that exists only in chat to its canonical plan/PR owner, update "
        "the work ledger when present, and route any safe successor back to execution rather than hiding it in closeout."
    )
    if "actionable repository plan or successor phase exists only in chat" not in p12["proofGate"]:
        p12["proofGate"] = p12["proofGate"].rstrip(".") + (
            "; closeout is invalid if an actionable repository plan or successor phase exists only in chat, if a "
            "phase-local boundary is treated as whole-mission terminal, or if weaker evidence is promoted into a stronger completion state."
        )
    p12_block = """DURABLE CLOSEOUT GATE
- Compress durable state; do not create terminality by omission. Persist actionable repository plans, approved revisions, and successor maps to their canonical plan/PR owner before closeout, and update the repository work ledger when one exists.
- A phase-local forbidden/out-of-scope boundary is not a whole-mission stop. If a safe evidence-backed successor exists and user/repo law does not prohibit it, route back to execution.
- Do not promote PLANNED/DESIGNED/TRACKED evidence into IMPLEMENTED/WIRED/VALIDATED/INTEGRATED/DEPLOYED/OBSERVED. State the strongest proven level and missing transition.
"""
    if "DURABLE CLOSEOUT GATE" in p12["copyContent"]:
        p12["copyContent"] = p12["copyContent"].split("DURABLE CLOSEOUT GATE", 1)[0].rstrip() + "\n\n" + p12_block
    else:
        p12["copyContent"] = p12["copyContent"].rstrip() + "\n\n" + p12_block

    p07 = by_id["P07"]
    for phrase in (
        "PHASE-LOCAL OUT OF SCOPE",
        "USER/REPO FORBIDDEN",
        "do not by themselves forbid a later successor phase",
    ):
        if phrase not in p07["copyContent"]:
            raise SystemExit(f"P07 phase-continuity repair missing: {phrase}")

    PROMPTS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_diagnosis_owner() -> None:
    payload = json.loads(AI_PROMPTS.read_text(encoding="utf-8"))
    p100 = next((p for p in payload.get("prompts", []) if p.get("id") == "P100"), None)
    if p100 is None:
        raise SystemExit("P100 diagnosis owner missing")
    for keyword in (
        "evidence-state promotion",
        "designed vs implemented",
        "wired vs planned",
        "concurrent chat false completion",
    ):
        if keyword not in p100["keywords"]:
            p100["keywords"].append(keyword)
    if "DESIGNED is not WIRED" not in p100["proofGate"]:
        p100["proofGate"] = p100["proofGate"].rstrip(".") + (
            "; for progress-state failures, DESIGNED is not WIRED and concurrent chat/branch/PR activity is not "
            "COMPLETED until refreshed exact evidence proves the stronger state."
        )
    # Keep P100's established <8000-character raw prompt budget. The shared policy
    # carries the full state ladder; P100's direct contract only needs the trigger.
    direct = (
        "\n\nEVIDENCE-STATE CHECK\nFor progress/completion errors, name the unsupported promotion "
        "(for example DESIGN->WIRED or CONCURRENT->COMPLETE), the missing proof transition, and the correct owner."
    )
    if "EVIDENCE-STATE CHECK" not in p100["copyContent"]:
        candidate = p100["copyContent"].rstrip() + direct
        if len(candidate) >= 8000:
            raise SystemExit(f"P100 budget exceeded by concise evidence-state trigger: {len(candidate)}")
        p100["copyContent"] = candidate
    AI_PROMPTS.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_test() -> None:
    TEST.write_text(
        '''from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
BASE = ROOT / "docs" / "prompts.json"
AI = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
PLAN_MARKER = "REPOSITORY PLAN DURABILITY CONTRACT"
STATE_MARKER = "EVIDENCE STATE / NO PROMOTION CONTRACT"


class RepositoryPlanDurabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.raw = {p["id"]: p for p in json.loads(BASE.read_text(encoding="utf-8"))}
        ai_payload = json.loads(AI.read_text(encoding="utf-8"))
        cls.ai_raw = {p["id"]: p for p in ai_payload["prompts"]}
        cls.effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}

    def test_shared_policy_makes_chat_only_repository_plans_noncanonical(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(PLAN_MARKER, appendix)
        for phrase in (
            "chat alone is not a canonical planning surface",
            "active pull request",
            "approved in chat triggers synchronization",
            "Multi-phase repository work must persist the whole phase map",
            "P66",
            "Closeout is invalid",
        ):
            self.assertIn(phrase, appendix)
        self.assertTrue(any("exists only in chat" in item for item in self.policy["forbidden_solo_actions"]))

    def test_shared_policy_forbids_evidence_state_promotion(self) -> None:
        appendix = self.policy["copy_content_appendix"]
        self.assertIn(STATE_MARKER, appendix)
        for phrase in (
            "PLANNED/DESIGNED",
            "IMPLEMENTED",
            "WIRED/REACHABLE",
            "INTEGRATED",
            "different chat, agent, worktree, branch, or PR",
            "named future phase",
            "strongest proven state",
        ):
            self.assertIn(phrase, appendix)
        self.assertIn("Do not promote evidence states", self.policy["next_step_suffix"])

    def test_p02_and_p04_persist_actionable_repository_plans(self) -> None:
        self.assertIn("DURABLE REPOSITORY PLAN HANDOFF", self.raw["P02"]["copyContent"])
        self.assertIn("DURABLE PLAN OUTPUT", self.raw["P04"]["copyContent"])
        self.assertIn("P66", self.raw["P02"]["copyContent"])
        self.assertIn("P66", self.raw["P04"]["copyContent"])
        self.assertIn("canonical tracked plan", self.raw["P02"]["expectedOutput"])
        self.assertIn("active PR", self.raw["P04"]["proofGate"])

    def test_p12_refuses_chat_only_or_state_promoted_closeout(self) -> None:
        p12 = self.raw["P12"]
        self.assertIn("DURABLE CLOSEOUT GATE", p12["copyContent"])
        self.assertIn("phase-local", p12["copyContent"].lower())
        self.assertIn("PLANNED/DESIGNED/TRACKED", p12["copyContent"])
        self.assertIn("actionable repository plan or successor phase exists only in chat", p12["proofGate"])

    def test_p07_phase_continuity_repair_remains_present(self) -> None:
        p07 = self.raw["P07"]["copyContent"]
        for phrase in (
            "PHASE-LOCAL OUT OF SCOPE",
            "USER/REPO FORBIDDEN",
            "do not by themselves forbid a later successor phase",
        ):
            self.assertIn(phrase, p07)

    def test_p100_names_state_promotion_without_breaking_prompt_budget(self) -> None:
        p100 = self.ai_raw["P100"]
        self.assertIn("EVIDENCE-STATE CHECK", p100["copyContent"])
        self.assertIn("DESIGN->WIRED", p100["copyContent"])
        self.assertIn("CONCURRENT->COMPLETE", p100["copyContent"])
        self.assertIn("DESIGNED is not WIRED", p100["proofGate"])
        self.assertIn("evidence-state promotion", p100["keywords"])
        self.assertLess(len(p100["copyContent"]), 8000)

    def test_shared_contract_reaches_plan_build_closeout_ledger_and_diagnosis(self) -> None:
        for prompt_id in ("P02", "P04", "P07", "P12", "P66", "P83", "P95", "P100", "P141"):
            self.assertIn(prompt_id, self.effective)
            copy = self.effective[prompt_id]["copyContent"]
            self.assertIn(PLAN_MARKER, copy)
            self.assertIn(STATE_MARKER, copy)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


def remove_bad_assumption_artifact() -> None:
    if STALE_TOPOLOGY_ROADMAP.exists():
        STALE_TOPOLOGY_ROADMAP.unlink()


if __name__ == "__main__":
    remove_bad_assumption_artifact()
    patch_policy()
    patch_core_owners()
    patch_diagnosis_owner()
    write_test()
