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


def patch_policy() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))

    plan_suffix = (
        " When repository planning produces a materially actionable plan, persist the complete plan "
        "to tracked repository/provider state before treating planning as complete or handing execution "
        "to another agent; chat text is provisional rather than canonical repository state. If an active "
        "pull request exists, the approved plan must be present there directly or by an explicit canonical "
        "tracked-plan reference."
    )
    if "chat text is provisional rather than canonical repository state" not in policy["next_step_suffix"]:
        policy["next_step_suffix"] = policy["next_step_suffix"].rstrip() + plan_suffix

    state_suffix = (
        " Do not promote evidence states: a plan, design, schema, config entry, test, branch, PR, or mention in "
        "another chat is not proof that behavior is wired, implemented, validated, integrated, deployed, or "
        "observed. Name the strongest state actually proven by refreshed repository/provider/runtime evidence."
    )
    if "Do not promote evidence states" not in policy["next_step_suffix"]:
        policy["next_step_suffix"] = policy["next_step_suffix"].rstrip() + state_suffix

    plan_section = """REPOSITORY PLAN DURABILITY CONTRACT
- When work concerns a repository and planning produces a materially actionable roadmap, sprint map, architecture plan, migration plan, phase plan, implementation sequence, or other execution dependency, the complete accepted plan MUST live in durable repository/provider state; chat alone is not a canonical planning surface.
- Chat may carry a provisional sketch, critique, or short orientation note. Before the plan becomes an execution dependency, is called approved/ready, or is handed to another agent, persist the complete plan in the existing canonical tracked plan/spec/handoff path or in the active pull request. Reuse an existing plan owner/path before creating another plan file.
- If an active pull request exists, approval must be reflected in that PR immediately: include the complete plan there or identify the exact committed canonical plan path plus its status/commit. Do not leave the approved version only in chat.
- A plan approved in chat triggers synchronization, not closure: update the tracked plan or PR in the same execution thread before implementation/handoff continues.
- Multi-phase repository work must persist the whole phase map, not only the current phase: completed floor, successor phases, dependencies, owned and forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and explicit deferred work. Future phases may remain unimplemented, but they may not exist only as conversational leftovers when they are already actionable.
- If a materially actionable repository plan changes, update the durable plan/PR before handing off or claiming the planning state current. Agents entering later must be able to recover the plan from refreshed repository/provider truth without needing the originating chat.
- When the repository already has a work-ledger owner such as P66, use it as the continuity index and link the complete canonical plan/PR rather than pasting the whole implementation design into a second ledger authority.
- Closeout is invalid when an actionable repository plan, approved plan revision, or successor-phase map exists only in chat. Persist it first, then report the canonical path/PR and exact revision.
"""

    state_section = """EVIDENCE STATE / NO PROMOTION CONTRACT
- Keep repository state claims typed. At minimum distinguish PLANNED/DESIGNED, TRACKED, IMPLEMENTED, WIRED/REACHABLE, VALIDATED, INTEGRATED, DEPLOYED, and OBSERVED when those distinctions matter to the task.
- Evidence for a weaker state never silently proves a stronger one. A design document or config field does not prove implementation; implementation does not prove wiring; a test or branch does not prove mainline integration; mainline integration does not prove deployment; deployment does not prove observed runtime behavior.
- A different chat, agent, worktree, branch, or PR may be concurrent evidence to inspect, but its existence is not completion evidence for this thread. Promote state only after refreshed repository/provider/runtime truth resolves the exact artifact, commit, PR, integration, deployment, or observation that proves the stronger state.
- Do not infer that a named future phase was executed merely because its design ingredients, schema fields, tests, or historical plan exist. Report the strongest proven state and the missing transition explicitly.
- Before terminal closeout, compare the requested target state with the strongest proven state. If the target requires a stronger state and the transition is SAFE & EXECUTABLE, continue; if blocked, name the exact gate. Do not manufacture completion by relabeling design or partial evidence.
"""

    appendix = policy["copy_content_appendix"]
    insert_before = "\n\nREMOTE FRESHNESS / BRANCH FLOOR CONTRACT"
    if PLAN_MARKER not in appendix:
        if insert_before not in appendix:
            raise SystemExit("Remote freshness marker not found in shared appendix")
        appendix = appendix.replace(insert_before, "\n\n" + plan_section.rstrip() + insert_before, 1)
    if STATE_MARKER not in appendix:
        if insert_before not in appendix:
            raise SystemExit("Remote freshness marker not found after plan insertion")
        appendix = appendix.replace(insert_before, "\n\n" + state_section.rstrip() + insert_before, 1)
    policy["copy_content_appendix"] = appendix
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_core_owners() -> None:
    prompts = json.loads(PROMPTS.read_text(encoding="utf-8"))
    by_id = {prompt["id"]: prompt for prompt in prompts}
    for prompt_id in ("P02", "P04", "P07", "P12"):
        if prompt_id not in by_id:
            raise SystemExit(f"Missing canonical owner: {prompt_id}")

    p02 = by_id["P02"]
    p02["expectedOutput"] = (
        "A context-grounded launch order and executable build panels that have been privately prototyped, "
        "checked against recovered requirements and repo evidence, revised to a bounded fixed point, and—when "
        "they concern actionable repository work—persisted in the repository's canonical tracked plan/handoff "
        "surface or active PR before another agent depends on them. Chat presentation is an orientation/copy "
        "surface, not the sole durable owner."
    )
    p02["nextStep"] = (
        "Privately prototype and validate the launch pack; for actionable repository work, synchronize the "
        "complete accepted launch map into the existing canonical tracked plan/handoff path or active PR, then "
        "present the concise chat-facing copy panels and launch the first executable panel from that durable state."
    )
    p02["proofGate"] = (
        "Prior context is recovered as far as available; at least one deliberate prototype -> critique -> revise "
        "pass occurs; every identified gap has an executable owner or evidence no build is needed; and any "
        "materially actionable repository launch map is recoverable in full from tracked repository/provider "
        "state (and reflected in the active PR when one exists) before handoff or completion."
    )
    if "DURABLE REPOSITORY PLAN HANDOFF" not in p02["copyContent"]:
        p02["copyContent"] = p02["copyContent"].rstrip() + """

DURABLE REPOSITORY PLAN HANDOFF
- A chat launch pack is provisional presentation, not canonical repository state. When the recovered work belongs to a repository and the resulting map is materially actionable, persist the complete accepted launch order, dependencies, lanes, proof gates, and deferred phases in the existing canonical tracked plan/handoff surface or active PR before another agent depends on it.
- If an active PR exists, synchronize approval there immediately: include the complete plan or the exact committed canonical plan path and revision. A plan approved in chat triggers repository/PR synchronization in the same execution thread.
- When a repository work ledger already exists, update it to point at the canonical plan/PR and current continuation state; do not make the ledger or the chat a duplicate implementation specification.
- Do not close a repository-planning conversation with a plan that later agents can recover only by finding this chat.
"""

    p04 = by_id["P04"]
    p04["expectedOutput"] = (
        "Launch order first, ordered copy-panel sprint candidates, and harness/skill/capability/trigger/app-logic "
        "factoring ledgers, with the complete actionable repository plan persisted to the existing canonical "
        "tracked plan/spec/handoff owner or active PR rather than existing only in chat."
    )
    p04["nextStep"] = (
        "Persist the complete accepted factoring plan to the canonical repository plan/handoff path or active PR, "
        "update the repository work ledger to reference it when a ledger exists, then use P05 or P07 from that durable revision."
    )
    p04["proofGate"] = (
        "Dependencies, collision ownership, exact panel sequence, successor phases, and proof gates are explicit; "
        "for actionable repository work the complete plan is tracked and recoverable from repository/provider "
        "truth, and any active PR points to or contains the approved revision."
    )
    if "DURABLE PLAN OUTPUT" not in p04["copyContent"]:
        p04["copyContent"] = p04["copyContent"].rstrip() + """

DURABLE PLAN OUTPUT
- Do not make chat the sole owner of an actionable repository plan. The chat response may be a concise orientation or copy surface, but the complete accepted sprint map must be committed to the existing canonical repository plan/spec/handoff path, or carried directly in the active PR when that is the repository's planning owner.
- Reuse the existing plan owner before inventing a second plan file. Persist the whole dependency map, not only the first lane: completed floor, ordered successor phases, parallel groups, collision ownership, owned/forbidden scope, expected artifacts, validation/proof gates, proof ceiling, and deferred work.
- If a P66-style repository ledger exists, use it to index the canonical plan, current owner, proof, and next action; do not replace the complete plan with a terse ledger row.
- If the operator approves or materially changes the plan in chat, synchronize that revision to the tracked plan/PR before handing execution to P05/P07 or another agent.
"""

    p12 = by_id["P12"]
    p12["expectedOutput"] = (
        str(p12["expectedOutput"]).rstrip(".")
        + ", with every actionable repository continuation recoverable from durable repository/provider state rather than chat alone."
    ) if "durable repository/provider state" not in str(p12["expectedOutput"]) else p12["expectedOutput"]
    p12["nextStep"] = (
        "Before final compression, reconcile the requested target state against refreshed repository/provider truth, "
        "persist any actionable plan/successor map that exists only in chat to its canonical plan/PR owner, update the "
        "work ledger when present, then emit the handoff only after no safe agent-capable continuation is being hidden by closeout."
    )
    p12["proofGate"] = (
        str(p12["proofGate"]).rstrip(".")
        + "; closeout is invalid if an actionable repository plan or successor phase exists only in chat, if a phase-local scope boundary is being treated as a whole-mission terminal boundary, or if a weaker evidence state is promoted into completion without exact proof."
    ) if "actionable repository plan or successor phase exists only in chat" not in str(p12["proofGate"]) else p12["proofGate"]
    if "DURABLE CLOSEOUT GATE" not in p12["copyContent"]:
        p12["copyContent"] = p12["copyContent"].rstrip() + """

DURABLE CLOSEOUT GATE
- Compress durable state; do not create terminality by omission. Before closeout, inspect whether any materially actionable repository plan, approved plan revision, successor phase, or execution dependency exists only in chat. Persist it to the existing canonical plan/spec/handoff path or active PR first, and update the repository work ledger when one exists.
- A phase-local forbidden/out-of-scope boundary does not by itself make the overall mission terminal. If a safe evidence-backed successor exists and the user/repository has not prohibited it, route back to the execution owner instead of emitting a terminal closeout.
- Do not promote PLANNED/DESIGNED/TRACKED evidence into IMPLEMENTED/WIRED/VALIDATED/INTEGRATED/DEPLOYED/OBSERVED. State the strongest proven level and the exact missing transition.
"""

    # P07 already owns the original phase-boundary defect. Preserve it and fail if
    # the previously merged repair disappears while this sprint changes adjacent contracts.
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
    prompts = payload.get("prompts", [])
    p100 = next((prompt for prompt in prompts if prompt.get("id") == "P100"), None)
    if p100 is None:
        raise SystemExit("P100 diagnosis owner missing")

    if "evidence-state promotion" not in p100.get("keywords", []):
        p100.setdefault("keywords", []).extend([
            "evidence-state promotion",
            "designed vs implemented",
            "wired vs planned",
            "concurrent chat false completion",
        ])

    if "evidence-state ledger" not in p100["expectedOutput"]:
        p100["expectedOutput"] = p100["expectedOutput"].rstrip(".") + (
            "; when the failure is a premature completion/state claim, also produce an evidence-state ledger that "
            "distinguishes PLANNED/DESIGNED, TRACKED, IMPLEMENTED, WIRED/REACHABLE, VALIDATED, INTEGRATED, DEPLOYED, "
            "and OBSERVED and names the unsupported promotion."
        )

    if "DESIGNED is not WIRED" not in p100["proofGate"]:
        p100["proofGate"] = p100["proofGate"].rstrip(".") + (
            "; evidence-state diagnosis proves the exact transition rather than inferring it: DESIGNED is not WIRED, "
            "a branch/PR is not INTEGRATED, and concurrent work in another chat/agent is UNKNOWN for this thread until "
            "refreshed repository/provider/runtime evidence resolves and proves the stronger state."
        )

    if "EVIDENCE-STATE PROMOTION FAILURE" not in p100["copyContent"]:
        p100["copyContent"] = p100["copyContent"].rstrip() + """

EVIDENCE-STATE PROMOTION FAILURE
When the wrong answer is a completion/progress claim, classify the state transition explicitly before repairing it.
- Distinguish PLANNED/DESIGNED -> TRACKED -> IMPLEMENTED -> WIRED/REACHABLE -> VALIDATED -> INTEGRATED -> DEPLOYED -> OBSERVED as separate evidence states when relevant. Do not skip a state merely because a design, schema, config field, test, branch, PR, or historical plan exists.
- A different chat, agent, worktree, branch, or PR is evidence to inspect, not evidence that this thread completed the work. Resolve refreshed provider/repository/runtime truth and the exact artifact/commit before promoting the state.
- Record the unsupported promotion that caused the error (for example DESIGN_EXISTENCE -> WIRED or CONCURRENT_ACTIVITY -> COMPLETED), the missing proof transition, the resulting premature stop/rework, and the smallest owner contract that prevents recurrence.
- Replay the nearby counterfactual: what should the agent have said and done if it had named the strongest proven state rather than the desired state?
"""

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
            "persist the complete plan",
            "active pull request",
            "plan approved in chat triggers synchronization",
            "Multi-phase repository work must persist the whole phase map",
            "P66",
            "Closeout is invalid",
        ):
            self.assertIn(phrase, appendix)

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
        self.assertIn("canonical tracked plan", self.raw["P02"]["expectedOutput"])
        self.assertIn("canonical", self.raw["P04"]["expectedOutput"])
        self.assertIn("active PR", self.raw["P04"]["proofGate"])
        self.assertIn("P66", self.raw["P04"]["copyContent"])

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

    def test_p100_names_state_promotion_and_concurrent_lane_error(self) -> None:
        p100 = self.ai_raw["P100"]
        self.assertIn("EVIDENCE-STATE PROMOTION FAILURE", p100["copyContent"])
        self.assertIn("DESIGN_EXISTENCE -> WIRED", p100["copyContent"])
        self.assertIn("CONCURRENT_ACTIVITY -> COMPLETED", p100["copyContent"])
        self.assertIn("DESIGNED is not WIRED", p100["proofGate"])
        self.assertIn("evidence-state promotion", p100["keywords"])

    def test_shared_contract_reaches_planning_build_closeout_and_diagnosis_types(self) -> None:
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
