#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

prompts_path = ROOT / "docs" / "prompts.json"
prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
p07 = next(item for item in prompts if item["id"] == "P07")
p07["sprintRole"] = (
    "Execute any bounded repo change through repeated evidence passes and validated "
    "mainline convergence"
)
p07["expectedOutput"] = (
    "Repository progress that has iterated through implementation, validation, evidence "
    "review, critique, and improvement until a bounded fixed point, then integrated into "
    "the current default branch when gates permit or stopped at an exact named blocker."
)
p07["nextStep"] = (
    "Run the next bounded IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE "
    "pass until the fixed-point gate is satisfied, then converge the exact validated head "
    "into the current default branch."
)
p07["proofGate"] = (
    "At least one deliberate second-pass evidence review follows the first "
    "implementation/validation pass; every concrete in-scope gap discovered by a pass is "
    "repaired and revalidated; the loop reaches a fixed point with no practical safe "
    "in-scope improvement or unresolved acceptance gap, then the intended change is "
    "verified on the current default branch or an exact integration blocker is proven."
)
iteration_block = """ITERATIVE SPRINT FIXED-POINT
- Execute the sprint as repeated bounded evidence passes: IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE. The first green result is evidence, not an automatic stop signal.
- Pass 1 must produce the smallest useful implementation and targeted proof. Then perform at least one deliberate second-pass review of the diff, validator/test output, generated artifacts, review comments, acceptance criteria, edge cases, and remaining risk.
- Convert every concrete in-scope gap found by that review into the next implementation pass immediately. If a pass changes tracked behavior or artifacts, rerun the affected validation and review the new evidence again.
- Continue until a bounded fixed point: no failing practical check, unresolved in-scope review, unmet acceptance criterion, stale generated artifact, known regression with a practical test, or safe bounded improvement revealed by current evidence remains.
- A later pass may make zero code changes only when its evidence review proves that no safe useful in-scope mutation remains. Do not manufacture churn merely to increase the pass count.
- Do not count repeated status polling, rereading the same log, or restating the same plan as an iteration. Each pass must either create/repair an owned artifact, produce stronger proof, close a named gap, or prove the fixed-point stop condition.
- If new CI/review/runtime evidence appears before merge, treat it as another pass input rather than a handoff excuse. Repair and revalidate in the same sprint when safe and authorized.
- Stop the iterative loop only at the fixed point plus MAINLINE CONVERGENCE, or at an exact blocker that prevents the next safe pass."""
anchor = (
    "Your job is to change the repository, validate the change, commit and push it, and "
    "carry the exact validated work through integration into current `main` (or the "
    "repository's configured default branch) when the gates permit."
)
if "ITERATIVE SPRINT FIXED-POINT" not in p07["copyContent"]:
    if anchor not in p07["copyContent"]:
        raise SystemExit("P07 iteration insertion anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(
        anchor, iteration_block + "\n" + anchor, 1
    )
if "ITERATION EVIDENCE\n- pass count:" not in p07["copyContent"]:
    report_anchor = "VALIDATION\n- command:\n- result:\n- skipped checks:"
    if report_anchor not in p07["copyContent"]:
        raise SystemExit("P07 final report validation anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(
        report_anchor,
        "ITERATION EVIDENCE\n- pass count:\n- gaps found and closed by pass:\n"
        "- fixed-point reason:\n" + report_anchor,
        1,
    )
old_end = (
    "Do the repo work. Validate it. Commit and push it. Integrate the exact green "
    "authorized head into the current default branch when the gates permit, verify the "
    "default branch contains the intended change, then stop."
)
new_end = (
    "Do the repo work. Iterate through evidence-driven implementation and validation passes "
    "until the bounded fixed-point gate is satisfied. Then commit/push, integrate the exact "
    "green authorized head into the current default branch when the gates permit, verify the "
    "default branch contains the intended change, and only then stop."
)
if old_end in p07["copyContent"]:
    p07["copyContent"] = p07["copyContent"].replace(old_end, new_end, 1)
elif new_end not in p07["copyContent"]:
    raise SystemExit("P07 terminal sentence anchor missing")
prompts_path.write_text(
    json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

spec_path = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
spec = json.loads(spec_path.read_text(encoding="utf-8"))
p79 = next(item for item in spec["prompts"] if item["id"] == "P79")
p79["sprintRole"] = (
    "Turn the immediately preceding request into a canonical Prompt Kit contribution through "
    "the repo-owned low-friction registry helper, with minimal architecture rediscovery and "
    "preserved validation quality"
)
p79["inspectFirst"] = (
    "The immediately preceding request; current Triage main/PR floor; `python "
    "scripts/prompt_registry_ops.py inspect` only when the target registry/profile is unclear; "
    "closest focused semantic test and Prompt Kit CI."
)
p79["expectedOutput"] = (
    "A requested prompt contributed through the repo-owned helper with auto-allocated stable "
    "identity/copy sheet, existing-registry reuse, generated-site parity, concise validation "
    "evidence, and integration to main when authorized."
)
p79["nextStep"] = (
    "Use `scripts/prompt_registry_ops.py` instead of manually rediscovering registry internals: "
    "prepare the semantic draft, add it through the existing registry owner, add only the "
    "focused semantic assertion the generic contracts cannot prove, validate, and converge "
    "to main."
)
p79["proofGate"] = (
    "The helper resolves or explicitly requests an existing registry owner, owns "
    "identity/sequence/copySheet allocation, rejects malformed or obvious duplicate "
    "contributions, applies shared policies, rebuilds exact site parity with rollback on "
    "failure, and the new prompt receives any necessary focused semantic assertion before "
    "exact-head validation and mainline integration."
)
p79["copyContent"] = """ADD A PROMPT TO THE PROMPT REGISTRY FROM THE CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION. EXECUTE THE REPO WORK; DO NOT ASK ME TO RESTATE CONTEXT THAT IS ALREADY PRESENT.

CANONICAL REPO
`EndeavorEverlasting/web-excel-repair-triage`

MISSION
Turn the preceding request into one reusable Prompt Kit contribution with as little registry ceremony and context loading as possible. Use the repo-owned prompt contribution helper as the default path. Do not manually rediscover IDs, copy-sheet naming, builder policy injection, or generated-site mechanics that the helper already owns.

FAST PATH
1. Read the immediately preceding request and preserve its explicit title, scope, wording, constraints, and intent. Search the current combined Prompt Kit for an exact/obvious duplicate; strengthen the existing canonical prompt instead of creating a second identity when one exists.
2. Choose the closest EXISTING registry/profile owner. If it is obvious from nearby prompts, use it directly. If not, run `python scripts/prompt_registry_ops.py inspect` once and consume its compact JSON routing receipt. Do not open every registry file merely to rediscover the same routing facts.
3. Create one small draft JSON containing semantic prompt fields only: name, type, class, sprintRole, useWhen, inspectFirst, expectedOutput, nextStep, proofGate, copyContent, and keywords. Supply `registry_id` or `--registry` plus profile/color/category only when they are not safely inferable. Do NOT set id, seq, or copySheet; those belong to the helper.
4. Execute `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`. The helper must allocate the next live P## identity/sequence, create copySheet, reuse/infer stable existing metadata, reject malformed or obvious duplicate input, reject copied shared actionability boilerplate, write the existing registry, apply shared policies, rebuild `web/prompt-kit/index.html`, prove exact parity, and roll back registry/site writes if validation fails.
5. Add or extend only the closest focused semantic assertion that the generic registry/helper contracts cannot prove. The registry record plus focused test remains the normal documentation surface; do not add a tutorial, architecture essay, duplicate catalog, or new registry family for ordinary prompt contributions.
6. Run `python scripts/prompt_registry_ops.py validate`, the focused registry test, applicable prompt-language/order/discovery checks, and `git diff --check`. Then commit/push, use the existing PR/integration lane when needed, and merge the exact green authorized head into `main` when gates permit.

FAIL-CLOSED FALLBACK
If the helper reports ambiguous routing, run its `inspect` command and select from the returned current registry IDs. If it reports a contract mismatch, inspect only the named owner/helper/builder surface needed to repair that mismatch. Do not fall back to loading the entire Prompt Kit architecture by default. Never force a guessed registry, overwrite an existing prompt identity, or bypass a failing generated-site/registry check.

QUALITY BOUNDARY
The helper removes deterministic ceremony; it does not replace semantic judgment. Preserve user intent, avoid invented requirements, keep source `copyContent` compact and executable, reuse shared policies instead of pasting them into the source record, and add focused semantic proof when the new behavior would otherwise be untested.

DELIVER
Report the prompt ID/name, owning registry, helper receipt, focused semantic proof, generated-site parity, validation, commit/PR/merge state, and resulting `main` SHA or exact blocker. Keep the final report compact; successful prompt contribution should not require another architecture tutorial."""
spec_path.write_text(
    json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

test_path = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
test_text = test_path.read_text(encoding="utf-8")
if "from scripts import prompt_registry_ops" not in test_text:
    test_text = test_text.replace(
        "from scripts import build_prompt_kit_registry\n",
        "from scripts import build_prompt_kit_registry\nfrom scripts import prompt_registry_ops\n",
        1,
    )
old_method = '''    def test_prompt_adder_consumes_preceding_context_and_executes_registry_work(self) -> None:
        prompt = self.full["P79"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "79")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "PROMPT KIT / REGISTRY OPERATIONS")
        self.assertIn("CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION", content)
        self.assertIn("DO NOT ASK ME TO RESTATE CONTEXT", content)
        self.assertIn("Assign the next valid unused `P##` identity", content)
        self.assertIn("Reuse the closest existing extension registry and profile", content)
        self.assertIn("registry record plus focused test is normally the documentation", content)
        self.assertIn("Regenerate the canonical website", content)
        self.assertIn("merge the exact green authorized head", content)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
'''
new_method = '''    def test_prompt_adder_uses_low_friction_helper_without_losing_semantic_proof(self) -> None:
        prompt = self.full["P79"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["seq"], "79")
        self.assertEqual(prompt["profile"], "spec-architecture")
        self.assertEqual(prompt["color"], "Cyan")
        self.assertEqual(prompt["class"], "PROMPT KIT / REGISTRY OPERATIONS")
        self.assertIn("CONTEXT IMMEDIATELY ABOVE THIS INSTRUCTION", content)
        self.assertIn("DO NOT ASK ME TO RESTATE CONTEXT", content)
        self.assertIn("scripts/prompt_registry_ops.py add", content)
        self.assertIn("Do NOT set id, seq, or copySheet", content)
        self.assertIn("roll back registry/site writes if validation fails", content)
        self.assertIn("focused semantic assertion", content)
        self.assertIn("Do not fall back to loading the entire Prompt Kit architecture", content)
        self.assertIn("merge the exact green authorized head", content)
        self.assertLess(len(self.raw["P79"]["copyContent"]), 5000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)

    def test_prompt_registry_ops_exposes_compact_current_routing_and_auto_identity(self) -> None:
        state = prompt_registry_ops.inspect_state()
        self.assertRegex(state["next_id"], r"^P\\d+$")
        self.assertEqual(state["next_id"][1:], state["next_seq"])
        self.assertIn("id", state["auto_fields"])
        self.assertIn("seq", state["auto_fields"])
        self.assertIn("copySheet", state["auto_fields"])
        ids = {item["registry_id"] for item in state["registries"]}
        self.assertIn("spec-architecture-prompts", ids)
        self.assertGreaterEqual(len(ids), 6)

    def test_prompt_registry_ops_dry_run_builds_complete_record_without_mutation(self) -> None:
        draft = {
            "name": "Prompt Ops Test Fixture",
            "type": "MAINTENANCE",
            "class": "PROMPT KIT / TEST",
            "sprintRole": "Exercise low-friction prompt contribution",
            "useWhen": "A deterministic helper regression is required.",
            "inspectFirst": "Current registry truth.",
            "expectedOutput": "A complete dry-run prompt record.",
            "nextStep": "Validate the dry-run record.",
            "proofGate": "No tracked source is mutated by dry-run.",
            "copyContent": "EXECUTE A DETERMINISTIC PROMPT REGISTRY HELPER TEST. " * 12,
            "keywords": ["prompt ops fixture", "registry helper fixture"],
            "profile": "spec-architecture",
            "color": "Cyan",
        }
        result = prompt_registry_ops.add_prompt(
            draft, "spec-architecture-prompts", dry_run=True
        )
        record = result["record"]
        self.assertEqual(result["status"], "dry-run")
        self.assertRegex(record["id"], r"^P\\d+$")
        self.assertEqual(record["copySheet"], f"{record['id']}_COPY_SAFE")
        self.assertEqual(record["profile"], "spec-architecture")
        self.assertEqual(record["color"], "Cyan")
        self.assertEqual(record["category"], "standard")

    def test_p07_requires_repeated_evidence_passes_until_fixed_point(self) -> None:
        p07 = self.full["P07"]
        content = p07["copyContent"]
        self.assertIn("ITERATIVE SPRINT FIXED-POINT", content)
        self.assertIn("IMPLEMENT -> VALIDATE -> INSPECT EVIDENCE -> CRITIQUE -> IMPROVE", content)
        self.assertIn("at least one deliberate second-pass review", content)
        self.assertIn("Continue until a bounded fixed point", content)
        self.assertIn("Do not manufacture churn", content)
        self.assertIn("Each pass must either create/repair an owned artifact", content)
        self.assertIn("ITERATION EVIDENCE", content)
        self.assertIn("fixed-point reason", content)
        self.assertIn("only then stop", content)
'''
if old_method in test_text:
    test_text = test_text.replace(old_method, new_method, 1)
elif "test_prompt_adder_uses_low_friction_helper_without_losing_semantic_proof" not in test_text:
    raise SystemExit("P79 focused test anchor missing")
test_path.write_text(test_text, encoding="utf-8")
