#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DRAFTS = [
    {
        "name": "Continuous Agentic Repo Loop Runner",
        "type": "EXECUTE + LOOP + INTEGRATE",
        "class": "AGENT HARNESS / CONTINUOUS CONVERGENCE",
        "sprintRole": "Keep an active repository moving through evidence-backed state transitions, integrate each independently valid bounded green slice into the current default branch, refresh, and continue until the mission reaches a real fixed point or an exact external gate",
        "useWhen": "A repository task is broad or multi-stage and agents tend to stop after planning, one implementation pass, green CI, an open PR, or a merge-ready branch instead of continuously selecting the next executable gate and converging finished slices into main.",
        "inspectFirst": "Fresh remote/default-branch and evidence floor; current mission and acceptance criteria; repository governance; work ledger or handoff state; current/open/recent overlapping branches and PRs; dependency order; exact heads and mergeability; validators/tests/CI; generated artifacts; unresolved reviews; available tools/permissions; and the strongest durable proof for the last completed slice.",
        "expectedOutput": "A sequence of bounded progress slices, each driven from current evidence through execution, validation, critique, and same-run integration when independently green, with main refreshed between slices; no status-spinning, no stranded green PR, durable recovery checkpoints after material transitions, and a final fixed-point or exact blocker report.",
        "nextStep": "Refresh the repository and evidence floor, identify the highest-value executable acceptance gate, complete one coherent bounded slice through validation and integration, refresh main, then immediately select the next remaining gate.",
        "proofGate": "Every loop pass either changes owned repository state, produces new decision-relevant evidence, integrates a validated slice, or proves an exact blocker; independently releasable green slices are merged in dependency order when authorized; moved heads invalidate affected proof; the loop resumes from durable current-main evidence after each integration or interruption; agent-capable work is not delegated to the user; and stopping occurs only at a bounded mission fixed point or a named external/user-only gate.",
        "copyContent": """RUN THE REPOSITORY AS A CONTINUOUS AGENTIC LOOP. KEEP WORKING, PROVING, MERGING, REFRESHING, AND CONTINUING UNTIL THE BOUNDED MISSION REACHES A REAL FIXED POINT OR AN EXACT EXTERNAL GATE.\n\nRepo: resolve the current repository from the environment or supplied context.\nMission: inherit the user's current repository objective and acceptance criteria.\nOwned scope: the smallest connected implementation, validation, artifact, review, integration, and recovery surfaces required to finish that mission safely.\nForbidden scope: unrelated rewrites, destructive cleanup, force-reset/force-push to erase unique work, secrets/private data, invented requirements, weakening validators, merging unproven work, or delegating ordinary agent-capable work back to the user.\n\nAGENTIC LOOP PRINCIPLE\nAn agentic loop is not `try again` and it is not repeated status polling. It is a state-transition engine. Each pass must consume current evidence, choose the next executable gate, perform work, validate the result, critique what the new evidence means, integrate completed work when safe, refresh the floor, and continue.\n\nUse this core loop:\nREFRESH -> ORIENT -> SELECT NEXT GATE -> EXECUTE -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE\n\nA pass is legitimate only if it does at least one of the following:\n- mutates owned repository state toward an acceptance criterion;\n- produces new decision-relevant validation/review/artifact evidence;\n- repairs a discovered defect or stale assumption;\n- integrates an independently valid bounded slice;\n- proves a concrete blocker that cannot be advanced with current tools/authority.\nRepeatedly listing branches, showing the same CI state, restating a plan, re-reading unchanged files, or telling the user to continue is not a progress loop.\n\n1. REFRESH THE REAL FLOOR\nBefore branch-sensitive decisions or mutation, refresh remote/provider truth and resolve the actual default branch. Inspect current/open/recent overlapping branches and PRs, latest relevant commits, current contracts/registries/generators, validators/tests/CI, artifacts/reports, review findings, dependencies, and merge authority. Reconcile stale or diverged local state without destroying unique work. Prior proof is versioned to the exact head, base, inputs, artifacts, and dependencies that produced it.\n\n2. ORIENT AROUND ACCEPTANCE GATES\nTranslate the mission into a short ordered set of observable acceptance gates. Keep them tied to repository truth rather than prose milestones. Do not create ceremonial gates that merely restate already-proven status.\n\n3. SELECT THE NEXT EXECUTABLE GATE\nChoose the highest-value unblocked gate that can be advanced now with available tools and authority. Prefer the critical path, but exploit safe parallelism when lanes do not collide. If another branch/PR already owns the work, reuse or advance that owner rather than creating duplicate effort.\n\n4. EXECUTE ONE COHERENT BOUNDED SLICE\nA slice should be small enough to validate and integrate independently but large enough to preserve correctness. Do not split an atomic schema/consumer migration, generated-source/parity update, or implementation/test pair merely to create artificial merge frequency. Conversely, do not accumulate unrelated finished work on a long-lived branch when a coherent subset has already earned integration.\n\n5. VALIDATE THE EXACT SLICE\nRun the owning focused checks plus the smallest connected validators required by changed surfaces. Confirm generated artifacts from canonical builders rather than hand-editing generated output. Re-fetch before exact-head conclusions. If head/base/dependencies moved after validation, invalidate affected proof, reconcile, and rerun what movement could have changed.\n\n6. CRITIQUE THE NEW EVIDENCE\nAsk what the validation actually proves and what it exposes: incomplete acceptance criteria, hidden dependency or generated-artifact drift, stale assumptions, review findings, branch/main movement, proof inflation, a safer/smaller implementation, or a newly unblocked next gate. Repair concrete in-scope defects and revalidate. Do not manufacture churn merely to demonstrate another pass.\n\n7. CONTINUOUS GREEN-SLICE INTEGRATION\nTreat a feature branch or PR as a temporary execution lane, not a parking lot. When one coherent bounded slice is independently valid, its exact head is current, required checks and owning validators are green, reviews/dependencies/protection gates are satisfied, merge authority exists, and the user has not prohibited merge, integrate that slice into the current default branch in the same run.\nDo not keep a validated slice unmerged just because the larger mission has more work remaining.\nWhen several green slices depend on one another, integrate in dependency order. After every merge:\n- refresh the default branch and provider state;\n- verify the intended change is present on the resulting default-branch SHA;\n- retire/supersede the temporary lane safely;\n- re-evaluate remaining acceptance gates against the new main;\n- continue from current main rather than from remembered pre-merge state.\n\n8. RECOVERY AND INTERRUPTIBILITY\nMake the loop resumable. After material state transitions, preserve durable evidence such as commit/merge SHA, PR, workflow run, artifact path/hash, ledger update, or validator receipt. If execution is interrupted, recover the latest durable state and current remote floor, classify which evidence is still current, then resume at the first unproven gate. Do not restart the whole mission or ask the user to reconstruct recoverable context.\n\n9. CONCURRENCY WITHOUT COLLISION\nOne writer owns a mutation surface at a time. Preserve separately owned dirty work and active branches. For parallel lanes, state owned scope, forbidden scope, dependency/start gate, expected artifact/proof, and convergence point. Merge completed dependency slices first, refresh downstream branches, and revalidate affected heads before integrating them.\n\n10. ANTI-SPIN AND RETRY DISCIPLINE\nRetries must have a reason and a changed condition. A retry is valid after a repair, refreshed dependency, transient external failure, or materially changed input. Re-running the same failing command with no changed state is not an agentic loop. Use bounded retries for flaky/transient systems. When no new action can change the result, classify the exact blocker instead of polling forever.\n\n11. USER ESCALATION BOUNDARY\nKeep agent-capable work with the agent: repository inspection, edits, tests, log collection, review resolution, CI inspection, routine branch reconciliation, generated-artifact rebuilds, commits, pushes, and authorized merges. Involve the user only for a genuinely user-controlled dependency such as inaccessible credentials/secrets, explicit consequential consent, physical-world action, inaccessible private runtime, or a material preference that cannot be inferred safely. Before asking, complete every safe action that does not depend on that answer.\n\n12. STOP CONDITION\nStop only when one of these is true:\nA. FIXED POINT: all bounded mission acceptance gates are satisfied on the current default branch, integration is verified, no safe in-scope action remains, and the final proof ceiling is explicit.\nB. EXACT GATE: progress requires a named dependency or user-only action that current tools/authority cannot perform, and all independent safe work has already been advanced.\n\nCode written, tests passed once, commit created, branch pushed, PR opened, review requested, CI green, PR mergeable, `ready to merge`, or a handoff saying the next agent should continue are never sufficient stop conditions by themselves.\n\nFINAL REPORT\nReport the repository/default branch, mission and acceptance gates, slices completed, meaningful iteration evidence, validation actually run, integrations with pre/post default-branch SHAs when available, remaining gaps/risks and proof ceiling, exact blocker if any, and NEXT COMMAND / NEXT ACTION. Use `none; no safe actionable work remains` only after the fixed-point definition above is actually satisfied.""",
        "keywords": ["agentic loop", "continuous agent loop", "keep working", "keep agent working", "continuous repo execution", "continuous merge", "merge continuously", "green slice", "green branch", "mainline convergence", "fixed point loop", "agent state machine", "repository loop", "autonomous repo agent", "continue until done", "anti spin", "resume interrupted agent", "merge then continue"]
    },
    {
        "name": "Agentic Loop Harness Hardener",
        "type": "HARDEN + ENFORCE",
        "class": "AGENT HARNESS / LOOP RELIABILITY",
        "sprintRole": "Retrofit a repository's agent prompts, harness, workflows, ledgers, and validators so agents advance through explicit progress states, resume safely after interruption, and continuously converge independently green work into the default branch instead of stopping early or spinning",
        "useWhen": "A repository repeatedly produces agents that plan instead of execute, stop at commits or green PRs, leave merge-ready branches stranded, poll without changing state, lose context after interruptions, re-prove old work, or ask users to perform routine repository operations.",
        "inspectFirst": "Repository governance and context router; operational prompts/skills; work ledger/status vocabulary; branch/PR and merge-gate conventions; CI/workflow triggers; validators/tests; current main/open/recent PR history showing early-stop or stranded-green patterns; recovery artifacts; proof/acceptance contracts; and existing shared actionability or integration policies.",
        "expectedOutput": "The smallest durable loop contract placed in canonical owners, focused regressions that fail on early-stop/spin/stale-proof/stranded-green behavior, recovery and progress-state semantics, merge-forward enforcement, updated affected prompts without duplicating shared policy, generated artifact parity when applicable, and validated integration to main.",
        "nextStep": "Identify the highest-frequency early-stop or loop failure in current repository evidence, patch the narrowest canonical prompt/harness/validator owner that can prevent it, add a regression reproducing the failure, validate the connected surfaces, integrate the green prevention slice, refresh main, and iterate on the next proven failure only if it remains.",
        "proofGate": "The repository has an explicit non-spinning progress state machine; continuation states cannot terminate with generic status or a green unmerged PR; independently valid green slices converge to the default branch when gates permit; stale proof is invalidated by material movement; interrupted work resumes from durable evidence; user escalation is limited to genuine user-only gates; regressions exercise the observed failure modes; and the final prevention change is verified on current main.",
        "copyContent": """HARDEN THIS REPOSITORY FOR CONTINUOUS AGENTIC LOOPS. FIX THE SYSTEM THAT MAKES AGENTS STOP EARLY, SPIN, LOSE STATE, OR LEAVE GREEN WORK UNMERGED. DO NOT JUST WRITE A BETTER ONE-OFF PROMPT.\n\nRepo: resolve the current repository and actual default branch.\nObserved failure: derive from the user's complaint and current repository evidence.\nOwned scope: canonical agent prompts/skills/harness contracts, work-state/ledger semantics, focused validators/tests, workflow wiring, and generated Prompt Kit parity when those surfaces own the failure.\nForbidden scope: unrelated product rewrites, wholesale governance replacement, duplicated policy appendices, weakening checks, destructive cleanup, secrets/private data, or changing domain behavior merely to make the harness simpler.\n\nMISSION\nTurn recurring `the agent stopped` behavior into an executable repository contract. The hardened repository should make the easiest correct path:\nREFRESH -> CHOOSE NEXT EXECUTABLE GATE -> ACT -> VALIDATE -> CRITIQUE -> INTEGRATE GREEN SLICE -> REFRESH -> CONTINUE.\nTreat agentic looping as a consistency, recovery, and convergence problem, not as instructions to retry forever.\n\n1. RECOVER THE FAILURE PATTERN\nInspect recent/current evidence for concrete loop failures: plan/status-only termination while executable work remained; stopping after code, commit, push, PR creation, review-ready state, green CI, or mergeability; green branches/PRs stranded instead of integrated; stale local/default-branch assumptions; repeated proof of already-established facts; repeated polling with no state change; branch multiplication instead of owner reuse; giant long-lived branches that postpone safe integration; interruption causing the next agent to restart or ask for context already recorded; routine tests/logs/review/merge work delegated to the user; moved heads treated as still validated; dependency order ignored; or proof claims exceeding observed evidence. Use actual repository/PR/CI history when available. Do not invent a failure merely to justify a new rule.\n\n2. FIND THE CANONICAL OWNER\nBefore adding text, locate where the behavior should live. Prefer an existing shared actionability/integration policy if the rule is universal; the canonical repo-sprint/executor prompt for execution-loop specifics; an agent continuity/verifier/work-ledger prompt for handoff/resume specifics; a harness workflow/state contract for deterministic transitions; or a validator/test when the behavior can be machine-checked. Do not paste the same long doctrine into every prompt.\n\n3. DEFINE A PROGRESS STATE MACHINE\nEncode states in repository-native vocabulary. If none exists, model equivalent semantics such as READY -> ACTIVE -> VERIFY -> REVIEW -> INTEGRATE -> CONTINUE/DONE with BLOCKED/OPERATOR only for exact external gates. Every nonterminal state needs a current evidence floor, owner, one executable next action, an acceptance/exit gate, and durable proof from the last material transition. A state transition must change owned repository state, produce decision-relevant evidence, integrate validated work, or prove a blocker. Status restatement is not a transition.\n\n4. SEPARATE PROGRESS LOOPS FROM RETRY LOOPS\nA progress loop chooses and advances a new gate. A retry loop repeats a failed operation after a changed condition. Require a reason for retries and bound transient retries. Prevent commands/workflows from silently re-running unchanged failures forever. After retries are exhausted, record the exact external/system gate.\n\n5. ENFORCE CONTINUOUS GREEN-SLICE CONVERGENCE\nA branch/PR is a temporary lane. Add or strengthen the rule that independently coherent, exact-head-validated, review-clean, dependency-satisfied, merge-authorized work integrates into the current default branch in the same execution window. Do not require the entire broad mission to finish before merging a smaller independently valid slice. Do not split atomic migrations merely to merge more often. After each integration require current default-branch SHA resolution, proof that the slice is present, refreshed dependency/PR floor, downstream revalidation when base movement matters, and selection of the next remaining gate. A green PR that the agent is authorized and able to merge is a continuation state, not a blocker and not completion.\n\n6. HARDEN RESUME / INTERRUPTION RECOVERY\nRequire durable checkpoints for material transitions: commit/merge SHA, PR, workflow run, artifact/hash, ledger task, or validation receipt. A new agent/session should refresh current remote/provider truth, recover the latest durable checkpoint, classify inherited proof as current/stale/partial, and resume at the first unproven gate. Do not force users to replay prior chats or reconstruct repository state that tools/ledgers can recover.\n\n7. HARDEN FRESHNESS\nBind validation to exact head/base/dependency/input/artifact identities. Material movement invalidates only the proof it could affect; do not blindly restart all proof. Re-fetch before final integration. Preserve dirty/separately owned work instead of force-resetting to current main.\n\n8. KEEP AGENT-CAPABLE WORK WITH THE AGENT\nPrompts/harnesses must not use the user as a test runner, log collector, CI watcher, branch reconciler, generated-artifact builder, or routine merge operator when tools/permissions can perform those actions. User escalation requires a genuine user-controlled dependency and must happen only after independent safe work is exhausted.\n\n9. ADD EXECUTABLE REGRESSIONS\nFor each observed failure you claim to harden, add the smallest focused test/validator/fixture that would fail if the behavior regresses. Useful checks include executor loop semantics; green+mergeable+authorized PR classified as merge-now; continuation states rejecting status-only next actions; moved-head proof invalidation; canonical generated-artifact parity; inherited completion claims requiring current evidence; recovery state containing durable checkpoint plus executable resume action; shared policy inheritance; and compact direct invariants for raw prompts that bypass policy injection. Static text cannot prove runtime model obedience, so keep the proof ceiling explicit.\n\n10. ITERATE THE HARDENING ITSELF\nUse at least two meaningful passes. PASS 1: implement the narrowest prevention for the highest-evidence failure and validate it. PASS 2: inspect the diff, generated artifacts, tests, current PR/base movement, and whether a weaker model could still stop at an intermediate state. Repair concrete gaps and revalidate. Continue only while evidence exposes a real defect.\n\n11. INTEGRATE THE PREVENTION\nWhen the hardening slice is exact-head green, review-clean, dependency-satisfied, mergeable, and authorized, merge it to the current default branch in the same run. Refresh main and verify the prevention exists there. If the original request includes more than one proven loop failure, select the next highest-value failure and repeat from current main rather than stacking indefinite unmerged hardening.\n\nDELIVER\nReport the observed agent-loop failures used as evidence; canonical owner(s) strengthened; prompts/contracts/validators/tests changed; state-machine and anti-spin rules installed; green-slice integration behavior installed; recovery/freshness behavior installed; focused regressions and connected validation actually run; generated-site parity when applicable; commit/PR/merge state and resulting default-branch SHA; proof ceiling; and next executable action or exact blocker.""",
        "keywords": ["agentic loop hardening", "agent loop harness", "repo agent harness", "agents stop early", "agent stops at PR", "green PR unmerged", "stranded green branch", "continuous integration agents", "agent recovery", "resume agent work", "anti spin loop", "agent state machine", "autonomous merge", "harden repo agents", "prompt harness hardening", "merge ready not done", "continuous convergence"]
    }
]

TEST_CONTENT = r'''from __future__ import annotations

import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as registry

ROOT = Path(__file__).resolve().parents[1]


class AgenticLoopPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.operational = {p["id"]: p for p in registry.load_prompt_registry()}
        cls.all_prompts = {p["id"]: p for p in registry.load_prompt_kit_registry()}

    def test_continuous_loop_prompt_encodes_progress_and_green_slice_convergence(self):
        prompt = next(p for p in self.all_prompts.values() if p["name"] == "Continuous Agentic Repo Loop Runner")
        content = prompt["copyContent"]
        self.assertIn("REFRESH -> ORIENT -> SELECT NEXT GATE -> EXECUTE -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE", content)
        self.assertIn("A pass is legitimate only if", content)
        self.assertIn("CONTINUOUS GREEN-SLICE INTEGRATION", content)
        self.assertIn("Do not keep a validated slice unmerged just because the larger mission has more work remaining.", content)
        self.assertIn("ANTI-SPIN AND RETRY DISCIPLINE", content)
        self.assertIn("RECOVERY AND INTERRUPTIBILITY", content)
        self.assertIn("FIXED POINT", content)
        self.assertEqual(prompt["actionabilityPolicy"], registry.load_actionability_policy()["policy_id"])

    def test_hardener_targets_early_stop_spin_recovery_and_merge_forward_failures(self):
        prompt = next(p for p in self.all_prompts.values() if p["name"] == "Agentic Loop Harness Hardener")
        content = prompt["copyContent"]
        for phrase in (
            "plan/status-only termination",
            "green branches/PRs stranded instead of integrated",
            "DEFINE A PROGRESS STATE MACHINE",
            "SEPARATE PROGRESS LOOPS FROM RETRY LOOPS",
            "ENFORCE CONTINUOUS GREEN-SLICE CONVERGENCE",
            "HARDEN RESUME / INTERRUPTION RECOVERY",
            "ADD EXECUTABLE REGRESSIONS",
            "ITERATE THE HARDENING ITSELF",
        ):
            self.assertIn(phrase, content)
        self.assertEqual(prompt["actionabilityPolicy"], registry.load_actionability_policy()["policy_id"])

    def test_p07_and_p83_have_direct_continuous_loop_invariants(self):
        p07 = self.operational["P07"]["copyContent"]
        p83 = self.operational["P83"]["copyContent"]
        for content in (p07, p83):
            self.assertIn("CONTINUOUS AGENTIC LOOP INVARIANT", content)
            self.assertIn("bounded green slice", content)
            self.assertIn("refresh", content.lower())
            self.assertIn("continue", content.lower())
        self.assertIn("do not strand it while broader mission work remains", p07.lower())
        self.assertIn("after integrating verified inherited work", p83.lower())

    def test_generated_site_is_exact_and_contains_agentic_loop_prompts(self):
        expected = registry.render()
        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        self.assertIn("Continuous Agentic Repo Loop Runner", actual)
        self.assertIn("Agentic Loop Harness Hardener", actual)


if __name__ == "__main__":
    unittest.main()
'''


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def add_prompts() -> None:
    receipts = []
    for index, draft in enumerate(DRAFTS, 1):
        path = ROOT / f".tmp-agentic-loop-draft-{index}.json"
        path.write_text(json.dumps(draft, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        completed = subprocess.run(
            ["python", "scripts/prompt_registry_ops.py", "add", "--input", str(path), "--registry", "repository-work-ledger-prompts"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        receipts.append(json.loads(completed.stdout))
        path.unlink()
    (ROOT / ".tmp-agentic-loop-receipts.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipts, indent=2))


def strengthen_p07() -> None:
    path = ROOT / "docs" / "prompts.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    prompt = next(item for item in payload if item.get("id") == "P07")
    marker = "CONTINUOUS AGENTIC LOOP INVARIANT"
    if marker not in prompt["copyContent"]:
        prompt["copyContent"] = prompt["copyContent"].rstrip() + "\n\n" + """CONTINUOUS AGENTIC LOOP INVARIANT
- Treat every nonterminal repository state as a continuation state. Each meaningful pass must mutate owned state, produce new decision-relevant evidence, integrate a validated bounded green slice, or prove an exact blocker; repeated status narration is not progress.
- When a coherent bounded green slice is independently valid, exact-head current, review/dependency/protection clean, merge-authorized, and safe, integrate it into the current default branch now; do not strand it while broader mission work remains.
- After each merge, refresh the default branch/evidence floor, verify the slice on the resulting main SHA, re-evaluate remaining acceptance gates, and continue from current main.
- Preserve atomic migrations: merge frequently only at coherent correctness boundaries, not by slicing required implementation/tests/generated parity apart.
- If interrupted, recover the latest durable commit/merge/PR/workflow/artifact evidence and resume at the first unproven gate instead of restarting or asking the user to reconstruct recoverable context.
"""
    prompt["nextStep"] = "Advance the highest-value executable gate through one bounded state-changing pass; integrate any independently green coherent slice, refresh main/evidence, and continue until the mission fixed point or an exact external gate."
    if "Continuous-loop proof also requires" not in prompt["proofGate"]:
        prompt["proofGate"] = prompt["proofGate"].rstrip() + " Continuous-loop proof also requires that each nonterminal pass changes state/evidence or proves a blocker, independently green coherent slices are not stranded while broader work remains, and the loop refreshes current main/evidence after integration before selecting the next gate."
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_p83() -> None:
    path = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    prompt = next(item for item in payload["prompts"] if item.get("id") == "P83")
    marker = "CONTINUOUS AGENTIC LOOP INVARIANT"
    if marker not in prompt["copyContent"]:
        prompt["copyContent"] = prompt["copyContent"].rstrip() + "\n\n" + """CONTINUOUS AGENTIC LOOP INVARIANT
- Verification is a continuation loop, not a review endpoint. Each meaningful pass must correct/advance owned state, produce new decision-relevant evidence, integrate a verified bounded green slice, or prove an exact blocker.
- If inherited work becomes independently green, exact-head current, review/dependency/protection clean, merge-authorized, and safe, integrate it now; do not leave verified work stranded merely because additional useful in-scope advancement remains.
- After integrating verified inherited work, refresh the default branch and evidence floor, verify the result on current main, then continue with the next unproven acceptance gate from that floor.
- If the prior agent stopped at commit/push/PR/green CI/merge-ready state, treat that as an intermediate state and advance the integration gate yourself when authorized.
- Preserve atomic correctness boundaries and separately owned work; continuous integration means frequent coherent convergence, not arbitrary fragmentation.
"""
    prompt["nextStep"] = "Resolve the exact inherited work and current floor, advance the highest-value unproven gate, integrate any independently verified green slice, refresh main/evidence, and continue until the bounded fixed point or a genuine user-only gate."
    if "Continuous-loop proof additionally requires" not in prompt["proofGate"]:
        prompt["proofGate"] = prompt["proofGate"].rstrip() + " Continuous-loop proof additionally requires that verified coherent green slices are integrated when authorized instead of stranded, post-merge main/evidence is refreshed before further advancement, and no pass terminates on status alone while an executable gate remains."
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    add_prompts()
    strengthen_p07()
    strengthen_p83()
    (ROOT / "tests" / "test_agentic_loop_prompts.py").write_text(TEST_CONTENT, encoding="utf-8")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/prompt_registry_ops.py", "validate")


if __name__ == "__main__":
    main()
