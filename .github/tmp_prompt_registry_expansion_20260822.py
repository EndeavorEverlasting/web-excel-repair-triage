from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    if capture:
        print(result.stdout, end="")
        return result.stdout
    return ""


def load(path: str) -> dict | list:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path: str, payload: dict | list) -> None:
    (ROOT / path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def add_prompt(draft: str, registry: str) -> dict:
    output = run(
        "python",
        "scripts/prompt_registry_ops.py",
        "add",
        "--input",
        draft,
        "--registry",
        registry,
        capture=True,
    )
    receipt = json.loads(output)
    if receipt.get("status") != "added" or not receipt.get("site_parity"):
        raise SystemExit(f"prompt helper failed to add {draft}: {receipt}")
    return receipt


print("=== CURRENT PROMPT ROUTING ===")
run("python", "scripts/prompt_registry_ops.py", "inspect")

# New identities are helper-owned. Add the three genuinely missing bounded capabilities.
regression = add_prompt(".github/prompt-regression-draft.json", "spec-architecture-prompts")
program_design = add_prompt(".github/prompt-program-design-draft.json", "spec-architecture-prompts")
teach = add_prompt(".github/prompt-teach-draft.json", "tutorial-discovery-prompts")

print("=== HELPER RECEIPTS ===")
print(json.dumps({
    "regression": regression,
    "program_design": program_design,
    "teach": teach,
}, indent=2))

# Strengthen P79: the immediate request is the anchor, not the context boundary.
spec_path = "registry/prompts/spec-architecture-prompts.v1.json"
spec = load(spec_path)
p79 = next(item for item in spec["prompts"] if item["id"] == "P79")
p79["sprintRole"] = (
    "Harvest the full relevant current conversation into a bounded Prompt Kit contribution set, "
    "strengthening canonical owners first and using the repo helper only for genuinely missing identities"
)
p79["useWhen"] = (
    "The current chat contains one or more reusable prompt/workflow insights and the operator wants them represented in the Prompt Kit without restating prior context or creating overlapping prompt identities."
)
p79["inspectFirst"] = (
    "The entire accessible current conversation relevant to the request, including earlier decisions, examples, corrections, constraints, and follow-ups; then current Triage main/PR floor, combined Prompt Kit ownership, focused semantic tests, and helper routing only when needed."
)
p79["expectedOutput"] = (
    "A whole-chat contribution ledger that dispositions every material reusable insight, strengthens overlapping canonical owners, adds only genuinely missing bounded prompts through the helper, expands compatible utility beyond literal transcription, proves generated-site parity, and converges the exact green result to main."
)
p79["nextStep"] = (
    "Sweep the whole relevant chat, build an insight-to-owner ledger, implement strengthen/add actions, then sweep the chat again for missed constraints or complementary utility before validation and mainline convergence."
)
p79["proofGate"] = (
    "The immediate request is treated as the anchor rather than the context boundary; at least two deliberate context/coverage passes occur; every material reusable insight is dispositioned as STRENGTHEN, ADD, ALREADY COVERED, or OUT OF SCOPE; new identities are helper-allocated only after overlap review; compatible utility may be expanded without inventing requirements; and focused semantic plus exact-site-parity proof passes."
)
p79["copyContent"] = """ADD OR STRENGTHEN PROMPT KIT PROMPTS FROM THE RELEVANT CONTEXT IN THIS CHAT. EXECUTE THE REPO WORK; DO NOT ASK ME TO RESTATE CONTEXT THAT IS ALREADY ACCESSIBLE.

CANONICAL REPO
`EndeavorEverlasting/web-excel-repair-triage`

MISSION
Turn the operator's current request plus the earlier relevant conversation into the smallest complete Prompt Kit contribution set. The instruction immediately above is the anchor, not the context boundary. Search backward through the accessible chat for decisions, examples, corrections, constraints, adjacent ideas, and earlier definitions that materially change what should be represented. Strengthen existing canonical owners before creating new identities. Use the repo-owned prompt helper for genuinely new prompts; do not manually rediscover IDs, copy-sheet naming, policy injection, or generated-site mechanics.

1. WHOLE-CHAT HARVEST — PASS 1
- Read the current request first, then traverse the earlier accessible conversation for the same use case/topic and its dependencies.
- Recover prior wording the operator approved, rejected, corrected, or refined. Preserve those decisions instead of asking for repetition.
- Include generated/pasted context and recoverable chat/history/context sources when available.
- Ignore unrelated conversation history; whole-chat means all materially relevant context, not indiscriminate token loading.
- Build a compact contribution ledger: `insight | current owner | action | proof`.
Actions are: STRENGTHEN / ADD / ALREADY COVERED / OUT OF SCOPE.
No material insight may silently disappear.

2. OWNER MAP BEFORE NEW IDS
Search the current combined Prompt Kit for exact, adjacent, and materially overlapping owners. Compare role/useWhen/proof boundary, not title alone.
- STRENGTHEN when an existing prompt owns the core use case but lacks a useful principle, failure mode, context rule, live-proof rule, or iteration contract.
- ADD only when the requested behavior has a distinct trigger, mission, and closure condition that would make an existing owner confused or bloated.
- ALREADY COVERED only with concrete current prompt evidence.
- Do not create a second prompt merely because different wording sounds attractive.

3. COMPLEMENT — DO NOT MERELY TRANSCRIBE
Preserve explicit user intent and terminology, then improve the reusable prompt with compatible utility exposed by the conversation and repository evidence: missing entrypoints, failure states, proof levels, iterative checks, context recovery, user-only gates, discoverability, or integration seams.
Do not invent product requirements, universal checklists, or unrelated architecture. Expansion must make the original use case more executable, testable, reusable, or failure-resistant.

4. IMPLEMENT THE CONTRIBUTION SET
For each STRENGTHEN item, edit the existing canonical source and closest focused regression rather than cloning it.
For each ADD item:
- choose the closest existing registry/profile owner;
- run `python scripts/prompt_registry_ops.py inspect` only when routing is unclear;
- create a semantic draft containing name/type/class/sprintRole/useWhen/inspectFirst/expectedOutput/nextStep/proofGate/copyContent/keywords plus only necessary routing metadata;
- do NOT set id, seq, or copySheet;
- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;
- let the helper allocate identity, reject obvious duplicates, inject shared policy, rebuild the canonical site, prove parity, and roll back failed writes.
Multiple genuinely distinct prompts may be added from one chat; `one contribution` does not mean collapsing unrelated capabilities into a super-prompt.

5. WHOLE-CHAT HARVEST — PASS 2
After the first implementation, traverse the relevant chat again from the opposite direction. Look specifically for:
- `also`, `another`, `we skipped`, `strengthen`, `live`, `regression`, `prototype`, `don't`, corrections, examples, and referenced sources;
- earlier accepted definitions that the draft lost;
- related existing prompts that should be strengthened to prevent overlap;
- useful complementary behavior that is compatible but still absent.
Update the contribution ledger and immediately close concrete gaps. Repeat only when new evidence changes the result. Stop at a bounded fixed point, not after the first successful helper receipt.

6. FOCUSED PROOF + SITE PARITY
Add or extend only the closest semantic assertions the generic registry/helper contracts cannot prove. Verify new identities are distinct and strengthened owners retain their original role.
Run:
- `python scripts/prompt_registry_ops.py validate`
- focused semantic tests
- applicable prompt-language/order/discovery tests
- canonical generated-site `--check`
- `git diff --check`
Then refresh the remote/default-branch floor, reconcile if it moved, run exact-head CI, and merge the authorized green result to main.

FAIL-CLOSED
If helper routing is ambiguous, inspect once and choose a current registry. If a contract mismatch names an owner/helper/builder, inspect that surface only. Never guess an ID/registry, overwrite another prompt identity, bypass stale-site parity, weaken a validator, or turn the operator into a context courier/test runner when the agent can recover or prove the information itself.

DELIVER
Keep the report compact: contribution ledger; strengthened prompt IDs/names; new helper-allocated IDs/names; helper receipts; focused semantic proof; site prompt count/parity; validation; commit/PR/merge; resulting main SHA; remaining exact blocker if any."""
if len(p79["copyContent"]) >= 5000:
    raise SystemExit(f"P79 raw copyContent exceeded existing compact boundary: {len(p79['copyContent'])}")
dump(spec_path, spec)

# Strengthen live proof with explicit regression controls.
base_path = "docs/prompts.json"
base = load(base_path)
p08 = next(item for item in base if item["id"] == "P08")
p08["sprintRole"] = "Prove requested live behavior and impacted known-good controls safely through the canonical runtime path"
p08["expectedOutput"] = "Observed behavior proof for the requested path plus impacted protected controls, or an honest bounded runtime failure/proof ceiling."
p08["proofGate"] = "Observed behavior is not confused with ACK/static proof; when the change can affect previously accepted runtime behavior, at least one impacted protected live control is exercised alongside the requested behavior or the exact inaccessible-runtime gate is named."
live_insert = """\nRegression control:\n- When this runtime sprint follows a code/config/migration change, identify the impacted behavior that already worked before the change.\n- Do not inherit the changed agent's chosen test set as complete; derive at least one protected control from the original request, accepted behavior, changed callers/call stack, or prior live evidence.\n- Through the canonical launcher/entrypoint, exercise both the requested new/repaired behavior and the impacted protected control when safe.\n- A successful new path does not prove an old path did not regress. Command ACK, process exit, mocked output, or route issuance do not satisfy either behavior observation.\n- If the protected live control cannot run because credentials, hardware, environment, authorization, or destructive state are unavailable, mark that claim unproved at the live level and name the exact gate.\n- After any runtime repair, rerun both paths before closeout.\n"""
if "Regression control:" not in p08["copyContent"]:
    p08["copyContent"] = p08["copyContent"].replace("\nValidation:\n", live_insert + "\nValidation:\n", 1)

# Strengthen PR/code review: separate standards from spec, then add regression/live gates.
p14 = next(item for item in base if item["id"] == "P14")
p14["sprintRole"] = "Review and repair a specific PR on separate standards/spec axes, then prove impacted regression and live-runtime behavior before merge when applicable"
p14["expectedOutput"] = "Applied review repairs with separate Standards and Spec findings, regression-impact proof, runtime proof where the PR makes a live claim, pushed commits, and updated PR/review state."
p14["proofGate"] = "Exact PR head is pinned; Standards and Spec are reviewed separately without inventing absent requirements; concrete findings are repaired; impacted protected behavior is regression-tested; runtime-facing claims receive canonical live proof when safely executable or an exact proof ceiling; and final exact-head PR state is verified."
review_insert = """\nREVIEW AXES — KEEP THEM SEPARATE\nPin the exact PR head and base/merge-base before conclusions. Review two independent axes:\nA. STANDARDS: repository law, correctness, security, maintainability, API/interface quality, failure handling, tests, hygiene, and operational safety.\nB. SPEC: whether the change actually implements the stated user/request/issue/acceptance behavior. If no usable spec/request exists, state `no spec available`; do not invent one.\nDo not let a clean style/standards review imply spec compliance, and do not let spec compliance hide a standards defect. Preserve both dispositions in the review evidence.\n\nREGRESSION + CALL-STACK GATE\n- Trace changed public interfaces/symbols through practical callers/call stacks and identify existing behavior the diff can affect.\n- Independently select protected regression controls; do not assume tests added/edited by the PR author are sufficient.\n- Inspect suspicious snapshot/fixture/mock/expected-value changes to ensure the test was not changed merely to bless broken behavior.\n- Run requested behavior plus impacted protected controls. If the PR claims user-visible/runtime behavior and a safe canonical runtime is available, exercise that actual entrypoint for both the new path and at least one impacted control.\n- If live execution is inaccessible, report the precise live proof ceiling instead of calling static green `field proven`.\n"""
if "REVIEW AXES — KEEP THEM SEPARATE" not in p14["copyContent"]:
    p14["copyContent"] = p14["copyContent"].replace("\nVALIDATION\n", review_insert + "\nVALIDATION\n", 1)
dump(base_path, base)

# Strengthen cross-agent review without bloating its existing iteration contract.
ledger_path = "registry/prompts/repository-work-ledger-prompts.v1.json"
ledger = load(ledger_path)
p83 = next(item for item in ledger["prompts"] if item["id"] == "P83")
p83["inspectFirst"] = p83["inspectFirst"].replace(
    "tests/validators/logs/artifacts, acceptance criteria,",
    "tests/validators/logs/artifacts, original requested behavior and accepted controls, impacted callers/call stacks, acceptance criteria,",
)
p83["proofGate"] = p83["proofGate"].replace(
    "concrete in-scope defects found during review are repaired and revalidated;",
    "concrete in-scope defects found during review are repaired and revalidated; the verifier independently derives a regression/control set rather than inheriting only the prior agent's chosen tests; runtime-facing completion claims receive the verifier's own canonical live proof when safely executable or remain explicitly unproved at that level;",
)
p83_insert = """\nINDEPENDENT REGRESSION / LIVE CLAIM CHECK\n- Do not accept the prior agent's chosen tests as the complete proof set. Re-derive the minimum controls from the original request, previously accepted behavior, current diff, and impacted callers/call stacks.\n- Treat changed snapshots, fixtures, mocks, or expected values as evidence to review, not automatic proof that behavior legitimately changed.\n- If the inherited claim is runtime/user-visible and a safe canonical runtime exists, execute that entrypoint yourself for the claimed outcome plus an impacted known-good control. Static tests, ACK, or the prior agent's reported live run are historical evidence only.\n- If that runtime is inaccessible, classify the live claim UNPROVEN and name the exact gate; do not make the user rerun it when the agent can.\n"""
if "INDEPENDENT REGRESSION / LIVE CLAIM CHECK" not in p83["copyContent"]:
    anchor = "\nSTOP ONLY AT THE REAL FIXED POINT"
    if anchor not in p83["copyContent"]:
        raise SystemExit("P83 fixed-point anchor missing")
    p83["copyContent"] = p83["copyContent"].replace(anchor, p83_insert + anchor, 1)
if len(p83["copyContent"]) >= 8000:
    raise SystemExit(f"P83 raw copyContent exceeded existing boundary: {len(p83['copyContent'])}")
dump(ledger_path, ledger)

# Strengthen P65 discovery after helper identities are known.
tutorial_path = "registry/prompts/tutorial-discovery-prompts.v1.json"
tutorial = load(tutorial_path)
p65 = next(item for item in tutorial["prompts"] if item["id"] == "P65")
routes = (
    f"- {regression['id']} Regression Test & Live Behavior Guard: prove a change preserves impacted previously accepted behavior with automated and live controls.\n"
    f"- {program_design['id']} Program Design & Call-Stack Prototype Architect: design runtime modules/seams/state ownership and prototype representative success/failure call stacks before broad implementation.\n"
    f"- {teach['id']} Stateful Socratic Technical Tutor Workspace: learn a technical topic through persistent grounded lessons, active retrieval, practical exercises, visualizers, and mastery records.\n"
)
if "Regression Test & Live Behavior Guard" not in p65["copyContent"]:
    anchor = "- P93 Use-Case Closure Certification"
    pos = p65["copyContent"].find(anchor)
    if pos >= 0:
        line_end = p65["copyContent"].find("\n", pos)
        if line_end < 0:
            line_end = len(p65["copyContent"])
        p65["copyContent"] = p65["copyContent"][: line_end + 1] + routes + p65["copyContent"][line_end + 1 :]
    else:
        marker = "\nRECOMMENDATION CONTRACT"
        if marker not in p65["copyContent"]:
            raise SystemExit("P65 routing insertion anchor missing")
        p65["copyContent"] = p65["copyContent"].replace(marker, "\n" + routes + marker, 1)
dump(tutorial_path, tutorial)

# New focused semantic proof covers the three new identities and all five strengthened owners.
test_path = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"
test_path.write_text(r'''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]


class PromptRegistryExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
        cls.by_name = {p["name"]: p for p in cls.full.values()}

    def test_new_prompts_are_distinct_and_visible(self) -> None:
        regression = self.by_name["Regression Test & Live Behavior Guard"]
        design = self.by_name["Program Design & Call-Stack Prototype Architect"]
        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]
        self.assertEqual(regression["class"], "TESTING / REGRESSION")
        self.assertEqual(design["class"], "SOFTWARE ARCHITECTURE / PROGRAM DESIGN")
        self.assertEqual(teach["class"], "LEARNING / STATEFUL TUTOR")
        self.assertEqual(len({regression["id"], design["id"], teach["id"]}), 3)
        for prompt in (regression, design, teach):
            self.assertRegex(prompt["id"], r"^P\d+$")
            self.assertEqual(prompt["copySheet"], f"{prompt['id']}_COPY_SAFE")
        html = build_prompt_kit_registry.render()
        for name in (regression["name"], design["name"], teach["name"]):
            self.assertIn(name, html)

    def test_regression_prompt_protects_old_behavior_and_requires_live_controls(self) -> None:
        content = self.by_name["Regression Test & Live Behavior Guard"]["copyContent"]
        for phrase in (
            "BUILD THE PROTECTED-BEHAVIOR LEDGER",
            "TRACE CHANGE IMPACT THROUGH CALL STACKS",
            "Do not let deleting or rewriting a test silently delete an accepted behavior",
            "RUN THE CANONICAL LIVE PATH WHEN THE CLAIM IS LIVE",
            "requested new/repaired behavior",
            "impacted previously working control",
            "Do not modify expected results, snapshots, fixtures, mocks, or tolerances merely to fit the broken candidate",
            "What behavior could this change break that our selected tests would not notice?",
        ):
            self.assertIn(phrase, content)

    def test_program_design_prototypes_success_and_failure_call_stacks(self) -> None:
        content = self.by_name["Program Design & Call-Stack Prototype Architect"]["copyContent"]
        for phrase in (
            "GOVERNANCE: rules for how work is performed",
            "PROGRAM DESIGN: runtime/application modules",
            "DESIGN DEEP MODULES AND CLEAN SEAMS",
            "PROTOTYPE REPRESENTATIVE CALL STACKS",
            "ENTRYPOINT/CONTROLLER",
            "PROTOTYPE FAILURE CALL STACKS TOO",
            "state/data has one canonical owner",
            "COMPARE SEAMS WHEN THE DESIGN IS UNCERTAIN",
            "This prompt may create design artifacts, thin prototypes",
        ):
            self.assertIn(phrase, content)

    def test_teach_prompt_is_grounded_stateful_and_active(self) -> None:
        content = self.by_name["Stateful Socratic Technical Tutor Workspace"]["copyContent"]
        for phrase in (
            ".teach/",
            "GROUND BEFORE EXPLAINING",
            "Treat unsupported model memory as a hypothesis, not a citation",
            "DECOMPOSE FROM FIRST PRINCIPLES",
            "DIAGNOSTIC CHECK",
            "PRACTICAL HARNESS",
            "ZERO BLACK-BOX PRODUCTION GENERATION DURING TEACHING",
            "USE TEST-DRIVEN LEARNING WHEN CODE IS THE SKILL",
            "self-contained HTML/JS visualizer",
            "Reuse components from existing `.teach/assets/`",
            "MASTERED requires demonstrated retrieval and practical application",
            "RECAP WITHOUT STARTING OVER",
        ):
            self.assertIn(phrase, content)

    def test_p79_harvests_whole_chat_twice_and_complements_utility(self) -> None:
        p79 = self.full["P79"]
        content = p79["copyContent"]
        for phrase in (
            "instruction immediately above is the anchor, not the context boundary",
            "WHOLE-CHAT HARVEST — PASS 1",
            "insight | current owner | action | proof",
            "No material insight may silently disappear",
            "COMPLEMENT — DO NOT MERELY TRANSCRIBE",
            "Multiple genuinely distinct prompts may be added from one chat",
            "WHOLE-CHAT HARVEST — PASS 2",
            "Stop at a bounded fixed point",
        ):
            self.assertIn(phrase, content)
        raw = json.loads((ROOT / "registry/prompts/spec-architecture-prompts.v1.json").read_text(encoding="utf-8"))
        source = next(p for p in raw["prompts"] if p["id"] == "P79")
        self.assertLess(len(source["copyContent"]), 5000)

    def test_runtime_and_review_owners_add_regression_live_proof(self) -> None:
        p08 = self.full["P08"]["copyContent"]
        self.assertIn("Regression control:", p08)
        self.assertIn("requested new/repaired behavior", p08)
        self.assertIn("impacted protected control", p08)
        self.assertIn("After any runtime repair, rerun both paths", p08)

        p14 = self.full["P14"]["copyContent"]
        self.assertIn("REVIEW AXES — KEEP THEM SEPARATE", p14)
        self.assertIn("A. STANDARDS", p14)
        self.assertIn("B. SPEC", p14)
        self.assertIn("no spec available", p14)
        self.assertIn("REGRESSION + CALL-STACK GATE", p14)
        self.assertIn("canonical runtime", p14)

    def test_agent_verifier_independently_derives_regressions_and_live_proof(self) -> None:
        p83 = self.full["P83"]["copyContent"]
        self.assertIn("INDEPENDENT REGRESSION / LIVE CLAIM CHECK", p83)
        self.assertIn("Do not accept the prior agent's chosen tests as the complete proof set", p83)
        self.assertIn("impacted callers/call stacks", p83)
        self.assertIn("execute that entrypoint yourself", p83)
        self.assertIn("classify the live claim UNPROVEN", p83)

    def test_p65_routes_all_three_new_capabilities(self) -> None:
        p65 = self.full["P65"]["copyContent"]
        for name in (
            "Regression Test & Live Behavior Guard",
            "Program Design & Call-Stack Prototype Architect",
            "Stateful Socratic Technical Tutor Workspace",
        ):
            prompt = self.by_name[name]
            self.assertIn(f"{prompt['id']} {name}", p65)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

# Rebuild because strengthened existing sources were edited after helper-generated parity.
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")

# Strong practical validation for the changed prompt surfaces.
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "tests.test_spec_architecture_prompt_registry", "tests.test_repository_work_ledger_prompt", "-v")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "-v")
run("python", "scripts/validate_prompt_kit_order_navigation.py", "--output", "/tmp/prompt-expansion-order.json", "--summary")
run("python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "-v")
run("python", "-m", "unittest", "tests.test_prompt_language_audit", "-v")
run("python", "scripts/evaluate_prompt_language.py", "--output", "/tmp/prompt-expansion-language.json", "--summary")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("git", "diff", "--check")

print("=== FINAL CONTRIBUTION RECEIPT ===")
print(json.dumps({
    "new_prompts": [regression, program_design, teach],
    "strengthened": ["P79", "P08", "P14", "P83", "P65"],
}, indent=2))
