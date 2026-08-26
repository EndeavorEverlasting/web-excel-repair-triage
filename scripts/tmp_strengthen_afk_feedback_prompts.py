#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TARGET_NAME = "AFK Feedback-Driven Development Loop Executor"


def run(*args: str) -> str:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if proc.returncode:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    if proc.stdout:
        print(proc.stdout, end="")
    return proc.stdout


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def save_registry(payload: dict) -> None:
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def prompt_by_id(payload: dict, prompt_id: str) -> dict:
    matches = [p for p in payload["prompts"] if p.get("id") == prompt_id]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one {prompt_id}, found {len(matches)}")
    return matches[0]


def append_once(text: str, marker: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    if marker not in text:
        raise SystemExit(f"anchor not found: {marker!r}")
    return text.replace(marker, addition.rstrip() + "\n\n" + marker, 1)


def insert_test_method(path: Path, method: str, sentinel: str) -> None:
    text = path.read_text(encoding="utf-8")
    if sentinel in text:
        return
    anchor = '\n\nif __name__ == "__main__":\n'
    if anchor not in text:
        raise SystemExit(f"test anchor missing in {path}")
    path.write_text(text.replace(anchor, "\n" + method.rstrip() + anchor, 1), encoding="utf-8")


def draft() -> dict:
    copy_content = r'''RUN A FEEDBACK-DRIVEN AFK DEVELOPMENT LOOP. CI, REVIEWS, TESTS, AND AUTOMATION MUST CREATE MORE REAL WORK UNTIL THE BOUNDED MISSION IS DONE OR AN EXACT BLOCKER IS PROVEN. DO NOT TURN AFK INTO PERIODIC STATUS REPORTING.

Repo/product: xyz_repo_or_product
Primary mission or backlog slice: xyz_goal_or_resolve_from_context
Allowed worker/automation surfaces, if known: xyz_agents_models_scripts_generators_bots_or_workflows
AFK window or cost budget, if explicitly given: xyz_window_or_budget
Forbidden runtime, deployment, credential, or destructive scope: xyz_forbidden_scope

MISSION
Make the repository's existing feedback and automation surfaces actively drive development while the operator is away. Treat CI failures, review comments, test/eval findings, provider receipts, generated-artifact drift, issue findings, stale proof, and newly green integration opportunities as inputs to another bounded work pass—not as reasons to merely summarize and stop. Reuse and strengthen existing developers, scripts, agents, models, PRs, generators, CI workflows, and repository-native helpers before inventing a competing automation stack.

1. RECOVER THE CURRENT WORK SYSTEM
Refresh remote/default-branch truth and recover current branches, PRs, CI workflows, review threads, issue/task queues, test/eval owners, generators, scripts, agent/model integrations, promotion paths, permissions, concurrency guards, and durable run/ledger evidence. Build a compact map:
SIGNAL -> CURRENT OWNER -> CAPABLE WORKER -> MUTATION SURFACE -> VALIDATION -> INTEGRATION GATE -> NEXT SIGNAL.
If the repository already has an AFK or autonomous mechanism, strengthen or connect it. Do not create a second scheduler, bot, branch writer, test floor, generator, or promotion authority merely because the current mechanism stops too early.

2. FEEDBACK IS A WORK QUEUE, NOT A REPORT ENDPOINT
Ingest concrete signals with provenance: provider run/job/check ID and candidate SHA; failing command/test and first useful error; PR review thread/comment/path/line; static-analysis finding; generated-artifact mismatch; skipped/blocked gate; issue/task identity; runtime receipt; or moved-base/stale-proof evidence. Classify each as ACTIONABLE_REPAIR, TEST_EVOLUTION, PROMOTION_BLOCKED, USER_ONLY, INFORMATION_ONLY, OUT_OF_SCOPE, or SUPERSEDED. Deduplicate already-consumed signal identities so schedules or repeated webhooks do not create churn.

Every ACTIONABLE_REPAIR must become either a concrete repository mutation owned by a capable worker or an exact blocker. A review summary, CI dashboard, comment, issue, artifact, or receipt is evidence for the next pass; it is not itself completion.

3. P07-STYLE NONTERMINAL WORK LOOP
Use this execution invariant:
REFRESH -> INGEST SIGNALS -> SELECT SAFE HIGHEST-VALUE WORK -> EXECUTE -> VALIDATE -> INGEST NEW FEEDBACK -> CRITIQUE -> IMPROVE -> INTEGRATE -> REFRESH -> REPEAT.

A status-only pass is a failed pass when safe agent-capable work exists. Every meaningful pass must mutate owned state, produce stronger decision-relevant evidence, integrate a coherent green slice, or prove the exact blocker that prevents the next safe pass. CI success, an open PR, a review summary, or a scheduled wake-up is not terminal state while an actionable queue item or integration gate remains. The first green result triggers at least one evidence review for new findings instead of granting automatic closure.

4. DISPATCH TO THE CAPABLE OWNER; DO NOT MAKE ONE MEGABOT
Use existing specialized owners rather than teaching this loop to impersonate every subsystem. P07 owns general bounded repository execution and its fixed-point/mainline discipline. P32 owns repair of an established failing CI lane. P112 owns bootstrap of a missing deterministic automated-test floor. P113 owns proactive risk-driven evolution of an already trustworthy floor. P104 owns bounded deterministic repository-native code generation from canonical inputs. P105 owns validation and authorized promotion of an already-authored exact candidate. Route other domain work to its current repository owner, developer, agent, model, script, generator, or workflow.

Dispatch parallel independent lanes when supported, but enforce one writer per mutation surface and serialize shared registries, schemas, generators, lockfiles, workflows, manifests, and default-branch mutation. A worker's completion claim is input evidence; the coordinator still revalidates and integrates the combined result.

5. FEED CI AND REVIEW RESULTS BACK INTO DEVELOPMENT
When CI fails, preserve the exact candidate identity and failing gate, then route the smallest repair to the owner that can change the implicated surface. When a review bot or human leaves a concrete finding, bind the thread/comment identity to the candidate head, validate the finding, repair it when correct, rerun affected proof, and resolve/respond only after current evidence supports the disposition. When a test/eval reveals a product defect, keep or add the regression and repair the product owner; do not stop after proving that the defect exists. When a promotion gate fails, P105 must remain fail-closed while this loop routes the repair; a new exact candidate must re-enter promotion after repair.

Feedback should reach developers, scripts, agents, models, PRs, and any other authorized work conductor in a form they can act on: exact target, owned surface, evidence, acceptance condition, forbidden scope, and command or mutation entrypoint. Do not force the operator to shuttle CI logs or review text between systems when repository/provider automation can preserve that context.

6. AFK WAKEUPS ARE NOT AFK WORK
Push, pull_request, review, issue, workflow_run, repository_dispatch, provider webhook, queue, and justified schedule events are wakeups. A cron tick that merely reruns unchanged checks and posts another summary is not useful AFK development. Prefer event-driven wakeups when the source can emit them; use schedules as bounded recovery/revalidation mechanisms when events are unavailable or stale state must be revisited. Record timing as best-effort when the provider does not guarantee exact scheduling.

On every wakeup, recover durable state from the repository/provider rather than model memory: last consumed signal IDs, current candidate/base, active work items, last proof, unresolved reviews, integration state, budgets, and blockers. If nothing relevant changed and no safe queued work remains, exit cleanly without manufacturing commits.

7. COERCE REAL WORK, NOT STATUS THEATER
If a safe mutation is available, a response that only explains, reports, waits, polls, opens a PR, restates failures, or asks the operator to run ordinary checks violates this prompt. Advance the first executable gate yourself. If an existing AFK workflow, prompt, bot, script, or agent repeatedly stops after producing feedback, repair that mechanism's contract/routing so the next run consumes its own evidence and continues development. Prefer changing the durable system over compensating forever with a smarter one-off agent.

Do not use artificial churn to satisfy the loop. No-op passes are valid only when they prove the fixed-point stop condition or a real blocker. Preserve cost/token/runtime budgets and cap repeated retries on unchanged evidence.

8. SAFETY, AUTHORITY, AND RECURSION
AFK authority does not expand because no human is watching. Preserve branch protection, environment approvals, review requirements, secrets policy, production boundaries, output containment, generated-surface ownership, and user-only gates. Do not grant a model new credentials, approve its own protected deployment, weaken a failing test, force-push, or bypass review to keep the loop moving. Guard bot/workflow commits against recursive self-triggering and conflicting writers. Stop a lane at the protected gate while continuing independent safe lanes.

9. PROVE THE LOOP IN THE REAL PROVIDER
Static orchestration prose is insufficient. Exercise one bounded canary feedback cycle in the actual provider where safe: create/select a controlled failing check, review finding, or stale-proof condition; observe the signal with exact identity; route it to the intended worker; perform the repair; rerun the affected gate; ingest the new result; conduct the second critique/improvement pass; and integrate one coherent green slice when authorized. Prove the operator did not have to relay ordinary logs or manually restart the development logic. Do not leave a deliberate defect in the durable branch.

10. TERMINAL CONDITIONS
Terminal state requires a bounded fixed point: requested acceptance criteria are proven; current feedback/review/test queues contain no unresolved in-scope actionable signal; exact-head validation is current; authorized integration is complete or specifically blocked; post-integration containment is verified; and remaining items are USER_ONLY, OUT_OF_SCOPE, UNSAFE with evidence, or exact blockers. An open PR, green CI, generated report, review-ready label, or successful scheduled run is nonterminal by itself.

After every merge/integration, refresh current default-branch truth and continue remaining queue items from that new floor. Most of the work should happen AFK because the loop carries signal context forward to the next capable worker, not because it runs a timer frequently.

DELIVER
Keep the operator closeout compact: signals consumed; real work passes executed; workers/owners used; files/artifacts changed; CI/review findings repaired; exact-head validation; integrations; remaining blockers/user-only gates; proof ceiling; and whether the loop reached fixed point. Do not substitute an activity report for the repository changes it should describe.'''
    return {
        "name": TARGET_NAME,
        "type": "AUTONOMY + EXECUTE",
        "class": "HARNESS / AFK DEVELOPMENT",
        "sprintRole": "Continuously turn CI, review, test, eval, runtime, and integration feedback into bounded repository work executed by the current capable developers, scripts, agents, models, generators, PRs, and workflows until a proven fixed point or exact blocker",
        "useWhen": "A repository already has some combination of CI, review bots, tests, agents, scripts, generators, PR automation, or AFK schedules, but those systems mostly report status or stop after one pass and the operator wants actionable feedback to keep driving real development and integration while away.",
        "inspectFirst": "Fresh default-branch and candidate truth; open/recent PRs and review threads; CI/workflow runs and artifacts; current test/eval owners; issue/task queues; repo-native generators/scripts; agent/model/bot integrations; existing AFK/schedule/webhook mechanisms; P07 execution/mainline contracts; P32/P104/P105/P112/P113 ownership boundaries; permissions, protection, concurrency, recursion, cost, and user-only gates.",
        "expectedOutput": "A durable feedback-to-work loop that maps exact signals to authorized capable workers, repeatedly performs real repository mutations and validation, feeds resulting CI/review evidence into later passes, repairs passive AFK mechanisms when they stop too early, integrates coherent exact-green slices when permitted, and emits compact evidence only after fixed point or an exact blocker.",
        "nextStep": "Consume the highest-value unprocessed CI/review/test/runtime signal now, route it to the existing capable owner, execute the bounded repair and validation, then ingest the resulting feedback and continue another P07-style pass before considering closure; send an exact authored green candidate to P105 only when promotion is the next gate.",
        "proofGate": "A real provider canary demonstrates signal -> owned work item -> authorized worker -> repository mutation -> validation -> new feedback -> second critique/improvement pass -> exact-green integration or exact blocker without ordinary operator log shuttling; repeated unchanged signals are deduplicated; safe work cannot terminate at status/report/PR-open/green-CI alone; one-writer/protection/recursion/cost boundaries hold; and refreshed default-branch evidence proves each integrated slice before the loop advances.",
        "copyContent": copy_content,
        "keywords": [
            "AFK development",
            "feedback driven development",
            "autonomous development loop",
            "CI feedback loop",
            "PR review automation",
            "unattended development",
            "agentic fixed point",
            "AFK coding agents",
            "continuous repair loop",
            "review feedback routing",
            "CI to code repair",
            "night shift development"
        ],
        "profile": "spec-architecture",
        "color": "Cyan",
        "category": "standard"
    }


def main() -> int:
    initial = load_registry()
    if any(p.get("name") == TARGET_NAME for p in initial["prompts"]):
        raise SystemExit(f"{TARGET_NAME} already exists; refusing duplicate add")

    with tempfile.TemporaryDirectory() as tmp:
        draft_path = Path(tmp) / "draft.json"
        draft_path.write_text(json.dumps(draft(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt_text = run(
            sys.executable,
            "scripts/prompt_registry_ops.py",
            "add",
            "--input",
            str(draft_path),
            "--registry",
            "spec-architecture-prompts",
        )
        receipt = json.loads(receipt_text)
    new_id = receipt["id"]

    payload = load_registry()
    new_matches = [p for p in payload["prompts"] if p.get("name") == TARGET_NAME]
    if len(new_matches) != 1 or new_matches[0].get("id") != new_id:
        raise SystemExit("helper receipt does not match newly loaded prompt")

    p112 = prompt_by_id(payload, "P112")
    p113 = prompt_by_id(payload, "P113")
    p105 = prompt_by_id(payload, "P105")

    p112_section = f'''10. ROUTE AFK TEST SIGNALS INTO DEVELOPMENT
If a trustworthy test floor already exists, do not spend AFK cycles merely rerunning it and posting another summary when CI, review, runtime, or test evidence identifies an actionable repository gap. This prompt still owns test-floor bootstrap; it must emit exact signal provenance and route generalized feedback-driven repair to {new_id} {TARGET_NAME}. A scheduled wake-up is not work by itself. Missing or weak regression coverage belongs to P113; a red established CI lane belongs to P32; an authored exact-green candidate belongs to P105 for promotion.'''
    p112["copyContent"] = append_once(p112["copyContent"], "SECOND PASS\n", p112_section)
    if new_id not in p112["nextStep"]:
        p112["nextStep"] += f" When the floor is already healthy but CI/review/test feedback should keep causing real repository development while AFK, route that signal stream to {new_id} {TARGET_NAME} instead of adding more passive scheduled validation."

    p113_section = f'''PRODUCT DEFECTS MUST ESCAPE THE TEST LANE
When risk-driven test evolution exposes a real product/workflow defect, do not stop after adding a failing regression or writing a report about it. Preserve the regression, bind the exact failure evidence, and route the bounded product repair through {new_id} {TARGET_NAME} or the repository's current execution owner (including P07 when appropriate). After the repair, rerun the regression and provider gate, ingest the new feedback, and continue the next justified pass. This prompt owns test evolution; it does not gain arbitrary product ownership merely because a test found the defect.'''
    p113["copyContent"] = append_once(p113["copyContent"], "SECOND-PASS FALSIFICATION\n", p113_section)
    if new_id not in p113["nextStep"]:
        p113["nextStep"] += f" If the evolved floor exposes an actionable product/CI/review defect, preserve the regression and route the repair through {new_id} {TARGET_NAME} so AFK development continues instead of ending at the finding."

    p105_section = f'''11A. FAILED PROMOTION GATES FEED DEVELOPMENT; THEY DO NOT AUTHOR CODE HERE
This pipeline remains promotion-only, but a failed promotion gate must produce an actionable repair signal instead of a dead-end status. Emit candidate SHA/base, failing job/check/command, relevant artifact/log or review-thread identity, owning surface, required acceptance condition, and proof ceiling. When repository policy allows AFK repair, hand that exact signal to {new_id} {TARGET_NAME} and keep promotion blocked. The repair owner must create a new exact candidate; re-enter this P105 pipeline from the beginning and never reuse proof from the failed candidate.'''
    p105["copyContent"] = append_once(p105["copyContent"], "12. OBSERVE AND AUDIT THE PIPELINE\n", p105_section)
    if new_id not in p105["nextStep"]:
        p105["nextStep"] += f" When a promotion gate fails with an agent-capable repair, emit the exact repair packet to {new_id} {TARGET_NAME}; keep promotion blocked until a newly authored exact candidate returns through all required gates."

    save_registry(payload)

    afk_test = ROOT / "tests/test_afk_deterministic_testing_prompt.py"
    insert_test_method(
        afk_test,
        f'''    def test_feedback_driven_afk_development_handoff(self) -> None:
        matches = [p for p in self.full if p.get("name") == {TARGET_NAME!r}]
        self.assertEqual(len(matches), 1)
        owner = matches[0]
        self.assertEqual(owner["id"], {new_id!r})
        self.assertIn(owner["id"], self.target["nextStep"])
        self.assertIn(owner["id"], self.target["copyContent"])
        self.assertIn("A scheduled wake-up is not work by itself", self.target["copyContent"])
        self.assertIn("This prompt still owns test-floor bootstrap", self.target["copyContent"])
''',
        "test_feedback_driven_afk_development_handoff",
    )

    evolution_test = ROOT / "tests/test_test_floor_evolution_prompt.py"
    insert_test_method(
        evolution_test,
        f'''    def test_product_defect_feedback_routes_to_afk_development(self) -> None:
        matches = [p for p in self.full if p.get("name") == {TARGET_NAME!r}]
        self.assertEqual(len(matches), 1)
        owner = matches[0]
        self.assertEqual(owner["id"], {new_id!r})
        self.assertIn(owner["id"], self.target["nextStep"])
        self.assertIn(owner["id"], self.target["copyContent"])
        self.assertIn("PRODUCT DEFECTS MUST ESCAPE THE TEST LANE", self.target["copyContent"])
        self.assertIn("Preserve the regression", self.target["copyContent"])
''',
        "test_product_defect_feedback_routes_to_afk_development",
    )

    spec_test = ROOT / "tests/test_spec_architecture_prompt_registry.py"
    insert_test_method(
        spec_test,
        f'''    def test_afk_feedback_executor_connects_real_work_to_existing_owners(self) -> None:
        matches = [p for p in self.full.values() if p.get("name") == {TARGET_NAME!r}]
        self.assertEqual(len(matches), 1)
        owner = matches[0]
        self.assertEqual(owner["id"], {new_id!r})
        self.assertEqual(owner["class"], "HARNESS / AFK DEVELOPMENT")
        content = owner["copyContent"]
        for phrase in (
            "FEEDBACK IS A WORK QUEUE, NOT A REPORT ENDPOINT",
            "P07-STYLE NONTERMINAL WORK LOOP",
            "REFRESH -> INGEST SIGNALS -> SELECT SAFE HIGHEST-VALUE WORK -> EXECUTE -> VALIDATE -> INGEST NEW FEEDBACK -> CRITIQUE -> IMPROVE -> INTEGRATE -> REFRESH -> REPEAT",
            "A status-only pass is a failed pass when safe agent-capable work exists",
            "developers, scripts, agents, models, PRs",
            "AFK WAKEUPS ARE NOT AFK WORK",
            "COERCE REAL WORK, NOT STATUS THEATER",
            "one writer per mutation surface",
            "Prove the operator did not have to relay ordinary logs",
            "An open PR, green CI, generated report",
        ):
            self.assertIn(phrase, content)
        for neighbor in ("P07", "P32", "P104", "P105", "P112", "P113"):
            self.assertIn(neighbor, content)
        self.assertEqual(self.full["P104"]["class"], "HARNESS / REPO-NATIVE CODE GENERATION")
        self.assertEqual(self.full["P105"]["class"], "HARNESS / CI-CD PROMOTION")
        self.assertEqual(self.full["P112"]["class"], "HARNESS / AUTOMATED TESTING")
        self.assertEqual(self.full["P113"]["class"], "HARNESS / TEST EVOLUTION")

    def test_p105_failed_gate_routes_to_afk_repair_without_gaining_authoring(self) -> None:
        owner = [p for p in self.full.values() if p.get("name") == {TARGET_NAME!r}][0]
        promotion = self.full["P105"]
        self.assertIn(owner["id"], promotion["nextStep"])
        self.assertIn(owner["id"], promotion["copyContent"])
        self.assertIn("FAILED PROMOTION GATES FEED DEVELOPMENT", promotion["copyContent"])
        self.assertIn("This pipeline remains promotion-only", promotion["copyContent"])
        self.assertIn("new exact candidate", promotion["copyContent"])
''',
        "test_afk_feedback_executor_connects_real_work_to_existing_owners",
    )

    new_test = ROOT / "tests/test_afk_feedback_development_prompt.py"
    new_test.write_text(
        f'''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TARGET_NAME = {TARGET_NAME!r}


class AfkFeedbackDevelopmentPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full_list = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.full = {{p["id"]: p for p in cls.full_list}}
        matches = [p for p in cls.full_list if p.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected one {{TARGET_NAME!r}}, found {{len(matches)}}")
        cls.target = matches[0]
        raw = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        raw_matches = [p for p in raw if p.get("name") == TARGET_NAME]
        if len(raw_matches) != 1:
            raise AssertionError(f"expected one raw {{TARGET_NAME!r}}, found {{len(raw_matches)}}")
        cls.raw = raw_matches[0]

    def test_helper_owns_identity_and_profile(self) -> None:
        self.assertEqual(self.target["id"], {new_id!r})
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{{self.target['id']}}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "HARNESS / AFK DEVELOPMENT")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_nonterminal_loop_requires_real_work(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "P07-STYLE NONTERMINAL WORK LOOP",
            "REFRESH -> INGEST SIGNALS -> SELECT SAFE HIGHEST-VALUE WORK -> EXECUTE -> VALIDATE -> INGEST NEW FEEDBACK -> CRITIQUE -> IMPROVE -> INTEGRATE -> REFRESH -> REPEAT",
            "A status-only pass is a failed pass when safe agent-capable work exists",
            "Every ACTIONABLE_REPAIR must become either a concrete repository mutation",
            "COERCE REAL WORK, NOT STATUS THEATER",
            "If a safe mutation is available",
            "An open PR, green CI, generated report",
        ):
            self.assertIn(phrase, content)

    def test_feedback_reaches_capable_workers_with_provenance(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "provider run/job/check ID and candidate SHA",
            "PR review thread/comment/path/line",
            "developers, scripts, agents, models, PRs",
            "exact target, owned surface, evidence, acceptance condition",
            "Do not force the operator to shuttle CI logs",
            "deduplicate already-consumed signal identities",
        ):
            self.assertIn(phrase, content)

    def test_existing_owner_boundaries_are_reused_not_collapsed(self) -> None:
        content = self.target["copyContent"]
        expected = {{
            "P07": "Repo Sprint Executor",
            "P32": "GNHF Validation and CI Repair",
            "P104": "Repository-Native Code Update Harness Builder",
            "P105": "Validated CI/CD Promotion Pipeline Builder",
            "P112": "AFK Deterministic Automated Test Harness Builder",
            "P113": "Risk-Driven Test Floor Evolution Executor",
        }}
        for prompt_id, name in expected.items():
            self.assertEqual(self.full[prompt_id]["name"], name)
            self.assertIn(prompt_id, content)
            self.assertNotEqual(self.target["id"], prompt_id)
        self.assertIn("Use existing specialized owners rather than teaching this loop to impersonate every subsystem", content)

    def test_p112_p113_and_p105_feed_the_new_loop(self) -> None:
        for prompt_id in ("P112", "P113", "P105"):
            self.assertIn(self.target["id"], self.full[prompt_id]["nextStep"])
            self.assertIn(self.target["id"], self.full[prompt_id]["copyContent"])
        self.assertIn("This pipeline remains promotion-only", self.full["P105"]["copyContent"])
        self.assertIn("This prompt still owns test-floor bootstrap", self.full["P112"]["copyContent"])
        self.assertIn("This prompt owns test evolution", self.full["P113"]["copyContent"])

    def test_generated_site_contains_exact_prompt_and_parity(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )

    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")

    # Whole-chat harvest pass 2 / fixed-point assertions.
    refreshed = load_registry()
    by_id = {p["id"]: p for p in refreshed["prompts"]}
    owner = [p for p in refreshed["prompts"] if p.get("name") == TARGET_NAME]
    if len(owner) != 1:
        raise SystemExit("pass 2: AFK feedback owner is not unique")
    owner = owner[0]
    checks = {
        "real_work": "A status-only pass is a failed pass when safe agent-capable work exists",
        "p07_loop": "P07-STYLE NONTERMINAL WORK LOOP",
        "worker_fanout": "developers, scripts, agents, models, PRs",
        "existing_systems": "If the repository already has an AFK or autonomous mechanism, strengthen or connect it",
        "signal_dedupe": "Deduplicate already-consumed signal identities",
        "provider_proof": "PROVE THE LOOP IN THE REAL PROVIDER",
        "mainline_continue": "After every merge/integration, refresh current default-branch truth",
    }
    missing = [name for name, phrase in checks.items() if phrase not in owner["copyContent"]]
    if missing:
        raise SystemExit("pass 2 missing owner semantics: " + ", ".join(missing))
    for prompt_id in ("P112", "P113", "P105"):
        if new_id not in by_id[prompt_id]["copyContent"] or new_id not in by_id[prompt_id]["nextStep"]:
            raise SystemExit(f"pass 2 missing routing from {prompt_id} to {new_id}")
    if "P113" not in by_id["P112"]["copyContent"]:
        raise SystemExit("pass 2 accidentally erased P112 -> P113 test-evolution routing")
    if "promotion-only" not in by_id["P105"]["copyContent"]:
        raise SystemExit("pass 2 blurred P105 promotion-only boundary")

    print(json.dumps({
        "status": "strengthened",
        "new_prompt_id": new_id,
        "new_prompt_name": TARGET_NAME,
        "strengthened": ["P112", "P113", "P105"],
        "pass2_fixed_point": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
