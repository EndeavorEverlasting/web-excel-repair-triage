from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(path: str, payload) -> None:
    (ROOT / path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def prompt_by_id(prompts, prompt_id: str):
    return next(prompt for prompt in prompts if prompt["id"] == prompt_id)


def append_unittest(path: str, method_name: str, body: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if f"def {method_name}" in text:
        return
    marker = '\n\nif __name__ == "__main__":'
    if marker not in text:
        raise SystemExit(f"unittest insertion marker missing: {path}")
    text = text.replace(marker, "\n" + body.rstrip() + marker, 1)
    target.write_text(text, encoding="utf-8")


def harden_shared_policy() -> None:
    path = "registry/prompts/actionable-next-step-policy.v1.json"
    policy = load(path)
    marker = "EXECUTION BRIEF / SOURCE / DONE / SELF-CHECK CONTRACT"
    if marker in policy["copy_content_appendix"]:
        return
    block = """EXECUTION BRIEF / SOURCE / DONE / SELF-CHECK CONTRACT
- ROLE: Operate as the senior practitioner and execution owner for the domain named by this prompt. Use that role to choose relevant standards, checks, and failure boundaries; never invent authority, credentials, access, or facts.
- WHERE TO LOOK: Start with explicit source, repository, context, plan, artifact, or path inputs in the prompt, then resolve the current canonical owners, governing contracts, tests/validators, and evidence those inputs point to. Do not ask the user to restate evidence the agent can inspect.
- DEFINITION OF DONE: Before mutation, translate the mission, owned scope, explicit user constraints, acceptance requirements, and proof requirements into a compact observable done checklist. Output existence alone is not completion; every material criterion needs evidence or an explicit UNKNOWN/blocker.
- SELF-CHECK: Before any completion claim, re-read the current source evidence and verify every material factual or quantitative claim, path, file/artifact identity, SHA/version, validator/test result, and completion statement against the evidence that supports it. Flag unsupported or stale claims instead of filling gaps from memory."""
    needle = "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT"
    appendix = policy["copy_content_appendix"]
    if needle not in appendix:
        raise SystemExit("shared actionability insertion point missing")
    policy["copy_content_appendix"] = appendix.replace(
        needle, block + "\n\n" + needle, 1
    )
    save(path, policy)


def harden_p07() -> None:
    path = "docs/prompts.json"
    payload = load(path)
    prompt = prompt_by_id(payload, "P07")
    marker = "EXECUTION BRIEF / EVIDENCE BINDING"
    if marker not in prompt["copyContent"]:
        block = """EXECUTION BRIEF / EVIDENCE BINDING
- ROLE: Act as the senior repository execution engineer/coordinator for this sprint. Own the bounded implementation, verification, integration, and handoff rather than merely advising the operator.
- WHERE TO LOOK: Start with `Context or plan path` when supplied, then current repository governance/harness, canonical owner files, tests/validators/CI/artifacts, and overlapping work from refreshed provider truth. Resolve technical facts from those sources before asking the user to repeat or inspect them.
- DEFINITION OF DONE: Before mutation, turn the owned scope, requested behavior/artifacts, explicit user constraints, repository acceptance gates, and proof requirements into a compact observable checklist. Keep that checklist stable unless current evidence or the user changes the requirement.
- SELF-CHECK: Before claiming completion, verify each material claim—including counts, paths, SHAs, branch/PR state, test or validator results, artifact identities, and unresolved gaps—against current evidence. Unsupported items are UNKNOWN or blockers, not plausible fill-ins."""
        needle = "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT"
        if needle not in prompt["copyContent"]:
            raise SystemExit("P07 insertion point missing")
        prompt["copyContent"] = prompt["copyContent"].replace(
            needle, block + "\n\n" + needle, 1
        )
    save(path, payload)


def harden_p86() -> None:
    path = "registry/prompts/spec-architecture-prompts.v1.json"
    payload = load(path)
    prompt = prompt_by_id(payload["prompts"], "P86")
    prompt["sprintRole"] = (
        "Audit one existing Prompt Kit prompt or a bounded family of candidate prompts against a supplied or discovered principle, "
        "then harden only the compatible canonical owners without duplicating shared policy or changing stable identities unnecessarily."
    )
    prompt["useWhen"] = (
        "An existing prompt is semantically weaker than current Prompt Kit patterns, or a newly learned prompt-design principle should be evaluated "
        "across every relevant existing prompt rather than applied only to the first obvious target."
    )
    prompt["inspectFirst"] = (
        "Current main/PR/evidence floor; the supplied principle/source example and the reusable behavior it actually demonstrates; the named target or candidate target set; "
        "each candidate in raw and effective form; registry/profile owners; shared prompt policies; focused tests; generated Prompt Kit parity; and overlapping prompt/PR work."
    )
    prompt["expectedOutput"] = (
        "The same canonical prompt identities selectively hardened through a campaign/target ledger and per-target principle-applicability matrix, minimal compatible raw or shared-owner edits, "
        "focused semantic regressions, bounded source growth, exact generated-site parity, and mainline integration when authorized."
    )
    prompt["nextStep"] = (
        "Resolve whether this is a single-target hardening or a principle-propagation campaign; normalize the source into atomic reusable principles, sweep the bounded candidate set, "
        "disposition every relevant prompt, patch the smallest canonical owners, prove old plus new semantics, and converge the exact green result to main."
    )
    prompt["proofGate"] = (
        "Every relevant candidate is dispositioned rather than silently skipped; changed prompts retain identity and primary role; every added principle has a source/donor or policy owner plus a concrete applicability reason; "
        "literal example wording and inherited policy are not cargo-cult copied; incompatible targets are rejected explicitly; old required semantics and new semantics are tested; raw growth stays bounded; generated-site parity and exact-head integration proof pass."
    )
    prompt["copyContent"] = """HARDEN ONE OR MORE EXISTING PROMPTS USING THE STRONGEST COMPATIBLE PRINCIPLES PROVEN BY THE CURRENT PROMPT KIT OR SUPPLIED SOURCE MATERIAL. MODIFY CANONICAL OWNERS; DO NOT CREATE DUPLICATE PROMPTS JUST TO PROPAGATE A PRINCIPLE.

Target prompt(s), if known: xyz_prompt_ids_names_or_resolve_from_context
Principle/source to integrate: xyz_principle_example_reference_or_infer_from_context
Specific weakness, if known: xyz_known_gap_or_infer_from_evidence

MISSION
Make the relevant existing prompts materially stronger without turning the Prompt Kit into a collage of universal boilerplate. This prompt supports either SINGLE TARGET hardening or a bounded PRINCIPLE PROPAGATION CAMPAIGN. Preserve prompt identities, roles, profiles, and useful semantics. Normalize the source principle, discover every genuinely relevant target, decide where the behavior belongs, patch only canonical owners, prove the result semantically, rebuild through canonical machinery, and integrate the exact validated result.

EXECUTION BRIEF
- ROLE: Act as a senior prompt-systems engineer responsible for prompt architecture, semantic regression, and anti-bloat ownership decisions.
- WHERE TO LOOK: Start with the supplied source/example and named targets, then current raw/effective registries, shared policy owners, focused tests, generated output, and refreshed overlapping PR/branch evidence.
- DEFINITION OF DONE: Every material candidate target is dispositioned; every accepted change is minimal and proven; generated output matches canonical sources; integration is complete or an exact gate is named.
- SELF-CHECK: Before finalizing, verify every target ID, donor/source claim, raw/effective classification, size claim, validator/test result, generated artifact identity, commit/PR state, and rejection reason against current evidence.

1. RESOLVE CAMPAIGN SHAPE AND CURRENT TRUTH
Work from current repository/provider truth, not remembered prompt text. Determine whether the request names one target or asks to propagate a principle across a family. If a principle is supplied but the target set is not, do not stop at the first obvious prompt: search the combined registry for prompts whose mission, failure modes, output contract, or proof behavior could materially benefit. Resolve each candidate's raw record, effective built form, registry/profile owner, shared policy owners, focused tests, generated site, and overlapping prompt/PR work. Reuse or repair an existing owning hardening lane instead of opening a competing one. Refresh again immediately before final exact-head conclusions; if main, a target, donor/source, or shared owner moves materially, reclassify affected evidence and rerun the decisions it could change.

2. RAW VS EFFECTIVE PROMPT
Read both forms before editing. Raw records own prompt-specific semantics; effective prompts may inherit shared policy. Separate those layers so global actionability, freshness, integration, evidence-binding, or closeout doctrine is not pasted back into every source record. Count inherited behavior as present unless a direct-consumer prompt has a concrete reason to carry a compact local version.

3. NORMALIZE THE SOURCE PRINCIPLE
Translate the supplied example, article, donor prompt, incident, or user observation into atomic reusable behaviors before searching targets. Distinguish principle from costume. For example, a source may demonstrate role/competence anchoring, an explicit source map or `where to look`, an observable definition of done, and a final self-check against evidence. Preserve those behaviors without blindly copying literal domain wording, invented tenure, emotional urgency, `take a deep breath` style filler, or source-specific formatting unless evidence shows those details are themselves required.

4. HARVEST ONLY RELEVANT DONORS AND TARGETS
Inspect the smallest useful set of current donors/shared owners plus the candidate prompts that overlap the principle. Candidate principles may include fresh repository/evidence floors; exact artifact identity; evidence-version invalidation; bounded implement/validate/critique iteration; continuous acceptance-gate progression; autonomous agent work with a user-only gate; fail-closed safety; source-of-truth precedence; role anchoring; explicit evidence/source locations; observable completion criteria; source-grounded self-check; proof ceilings; existing-work reuse; progressive disclosure; interruption recovery; dirty-work preservation; anti-fabrication boundaries; canonical-owner selection; and focused semantic regression. A strong principle is not automatically relevant to every prompt.

5. BUILD THE PRINCIPLE APPLICABILITY MATRIX
Before mutation, record one row per candidate target and principle:
- target prompt
- principle
- source/donor or canonical policy owner
- already present in RAW, EFFECTIVE, BOTH, or ABSENT
- concrete target-specific gap/failure mode
- COMPATIBLE, INCOMPATIBLE, or NOT NEEDED
- RAW CHANGE, SHARED-OWNER CHANGE, or NO CHANGE
- focused proof for the decision
Every material candidate must receive a disposition. `Not changed` is valid only with evidence; silent omission is not.

6. CHOOSE THE CANONICAL OWNER
Prefer one shared owner when the behavior is truly universal to the governed prompt family. Prefer a raw prompt edit when the behavior is role-specific, direct-consumer critical, or intentionally excluded from shared policy. Do not create a new global policy for a narrow use case. Do not copy a shared policy block into multiple raw prompts merely to make the diff look comprehensive.

7. HARDEN THE CANONICAL TARGETS
Patch existing records rather than renumbering or cloning them. Update only semantic fields that need strengthening—typically inspectFirst, sprintRole, useWhen, expectedOutput, nextStep, proofGate, copyContent, or keywords. Keep profile/color/category/copySheet and stable identity unchanged unless separate evidence requires otherwise. Reuse concise named concepts instead of copying whole donor sections.

8. P03 REFERENCE CASE
When P03 / Repository Evidence + First Sprint Executor is a target, explicitly compare its older evidence-harvest/execution semantics with applicable current principles from P07 (iterative autonomous repo execution and convergence), P13 (bounded self-improvement and evidence critique), P48 (fresh subject/evidence pinning and stale-proof invalidation where certification-like proof is claimed), P76 (progressive disclosure/context restraint), P83 (treat completion/handoff claims as hypotheses until verified), P84 (continuous acceptance-gate progression, green-slice convergence, anti-spin, resumable checkpoints), P85 (canonical-owner hardening and focused failure regressions), and current shared policies. Adopt only what strengthens P03's discovery-plus-first-sprint job; do not transform P03 into P07, P13, P48, P76, P83, P84, or P85.

9. ANTI-BLOAT / ANTI-CARGO-CULT GATE
Do not copy every strong rule into every prompt. Reject changes whose only rationale is `another prompt has this`. Prefer inherited shared policy, a shared-family owner, or one target-specific sentence when equivalent. If a raw target grows materially, justify the growth against a concrete failure mode and try a smaller formulation before accepting it. A campaign succeeds by correct coverage, not by number of edited prompts.

10. SEMANTIC REGRESSION PROOF
Extend the closest existing focused test for each changed owner or a compact family-level test when one shared owner governs them. Prove prior defining behavior remains and the selected principle is now effective. Add a negative/boundary assertion when useful so the test proves the target did not absorb an incompatible donor role. Check raw-source size or another anti-bloat boundary when practical. Do not replace semantic proof with generated-site presence alone.

11. VALIDATE AND ITERATE
Run target/shared-owner registry validation, focused semantic tests, applicable prompt-language/order/discovery/build checks, exact generated-site parity, and patch hygiene. Inspect the resulting diff and evidence for one deliberate second pass. Repair duplicated policy, identity drift, weakened old behavior, stale generated output, untested targets, unnecessary growth, or moved donor/base evidence, then rerun affected checks. Stop only when the bounded candidate set is fully dispositioned and no practical in-scope semantic improvement or regression remains.

DELIVER
Report campaign mode; normalized source principles; targets changed, shared owners changed, targets rejected/not-needed and why; semantic fields changed; focused proof; raw-size impact; registry/helper/build validation; generated-site parity; commit/PR/merge state; and resulting main SHA or exact blocker. Keep the report compact. The success condition is correct principle coverage with stronger proof, not a larger Prompt Kit."""
    prompt["keywords"] = list(
        dict.fromkeys(
            prompt["keywords"]
            + [
                "multi prompt hardening",
                "principle propagation",
                "prompt campaign hardening",
                "cross prompt audit",
                "role source done self check",
            ]
        )
    )
    if len(prompt["copyContent"]) >= 7600:
        raise SystemExit(
            f"P86 raw copyContent exceeded anti-bloat gate: {len(prompt['copyContent'])}"
        )
    save(path, payload)


def harden_correspondence() -> None:
    path = "registry/prompts/correspondence-prompts.v1.json"
    payload = load(path)
    p72 = prompt_by_id(payload["prompts"], "P72")
    p73 = prompt_by_id(payload["prompts"], "P73")
    marker = "ROLE / SOURCE / DONE / SELF-CHECK"
    if marker not in p72["copyContent"]:
        block = """ROLE / SOURCE / DONE / SELF-CHECK
- ROLE: Act as a senior correspondence editor. Optimize for clarity, fidelity, actionability, and relationship-preserving tone—not generic polish.
- SOURCE: Treat the supplied draft, audience/context, and explicit facts as authoritative. Do not invent names, dates, numbers, owners, deadlines, commitments, approvals, or motives.
- DEFINITION OF DONE: One send-ready message preserves every material fact and boundary, makes the supported ask/action clear, removes avoidable friction, and contains no meta commentary.
- SELF-CHECK: Before output, compare the final message back to the source and verify every factual or quantitative claim, name, date, commitment, owner, deadline, and material boundary. Preserve ambiguity or omit unsupported detail rather than guessing."""
        p72["copyContent"] = p72["copyContent"].replace(
            "OBJECTIVE\n", block + "\n\nOBJECTIVE\n", 1
        )
    if marker not in p73["copyContent"]:
        block = """ROLE / SOURCE / DONE / SELF-CHECK
- ROLE: Act as a senior client-communications editor. Translate internal work into recipient-relevant truth without exposing irrelevant machinery or sanitizing material bad news.
- SOURCE: Treat the supplied draft, audience/context, and supported underlying facts as authoritative. Internal implementation detail may be translated or removed only when doing so does not alter a material outcome, risk, dependency, obligation, date, or requested action.
- DEFINITION OF DONE: One external-facing message lets the recipient understand what happened, what matters to them, what remains constrained, and what action is required without irrelevant process narration.
- SELF-CHECK: Before output, compare the final message with the source and verify every material status, number, date, commitment, risk, dependency, limitation, and requested action. If source evidence is uncertain, preserve that uncertainty instead of manufacturing confidence."""
        p73["copyContent"] = p73["copyContent"].replace(
            "MISSION\n", block + "\n\nMISSION\n", 1
        )
    save(path, payload)


def add_tests() -> None:
    append_unittest(
        "tests/test_actionable_prompt_registry.py",
        "test_execution_brief_contract_is_global_for_operational_prompts",
        '''    def test_execution_brief_contract_is_global_for_operational_prompts(self) -> None:
        marker = "EXECUTION BRIEF / SOURCE / DONE / SELF-CHECK CONTRACT"
        appendix = self.policy["copy_content_appendix"]
        for phrase in (
            marker,
            "ROLE: Operate as the senior practitioner and execution owner",
            "WHERE TO LOOK: Start with explicit source, repository, context, plan, artifact, or path inputs",
            "DEFINITION OF DONE: Before mutation",
            "SELF-CHECK: Before any completion claim",
            "verify every material factual or quantitative claim",
            "Flag unsupported or stale claims",
        ):
            self.assertIn(phrase, appendix)
        for prompt in self.prompts:
            with self.subTest(prompt=prompt["id"]):
                self.assertIn(marker, prompt["copyContent"])

    def test_p07_carries_direct_execution_brief_for_raw_consumers(self) -> None:
        raw_prompts = json.loads(
            (REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8")
        )
        p07 = next(prompt for prompt in raw_prompts if prompt["id"] == "P07")
        for phrase in (
            "EXECUTION BRIEF / EVIDENCE BINDING",
            "senior repository execution engineer/coordinator",
            "WHERE TO LOOK: Start with `Context or plan path`",
            "DEFINITION OF DONE: Before mutation",
            "SELF-CHECK: Before claiming completion",
            "Unsupported items are UNKNOWN or blockers",
        ):
            self.assertIn(phrase, p07["copyContent"])
        self.assertIn("current/open/recent overlapping branches and PRs", p07["inspectFirst"])
        self.assertIn("fixed point", p07["proofGate"])
''',
    )
    append_unittest(
        "tests/test_spec_architecture_prompt_registry.py",
        "test_p86_supports_bounded_multi_prompt_principle_campaign",
        '''    def test_p86_supports_bounded_multi_prompt_principle_campaign(self) -> None:
        prompt = self.full["P86"]
        raw = self.raw["P86"]
        content = raw["copyContent"]
        for phrase in (
            "HARDEN ONE OR MORE EXISTING PROMPTS",
            "SINGLE TARGET hardening or a bounded PRINCIPLE PROPAGATION CAMPAIGN",
            "do not stop at the first obvious prompt",
            "NORMALIZE THE SOURCE PRINCIPLE",
            "Distinguish principle from costume",
            "role/competence anchoring",
            "explicit source map",
            "observable definition of done",
            "final self-check against evidence",
            "literal domain wording, invented tenure, emotional urgency",
            "Every material candidate must receive a disposition",
            "CHOOSE THE CANONICAL OWNER",
            "A campaign succeeds by correct coverage, not by number of edited prompts",
        ):
            self.assertIn(phrase, content)
        self.assertIn("one existing Prompt Kit prompt or a bounded family", raw["sprintRole"])
        self.assertIn("every relevant existing prompt", raw["useWhen"])
        self.assertIn("candidate target set", raw["inspectFirst"])
        self.assertIn("targets changed", content)
        self.assertLess(len(content), 7600)
        self.assertEqual(prompt["id"], "P86")
        self.assertEqual(prompt["copySheet"], "P86_COPY_SAFE")
''',
    )
    append_unittest(
        "tests/test_correspondence_prompt_registry.py",
        "test_correspondence_prompts_bind_role_source_done_and_self_check",
        '''    def test_correspondence_prompts_bind_role_source_done_and_self_check(self) -> None:
        for prompt_id in ("P72", "P73"):
            content = self.prompts[prompt_id]["copyContent"]
            with self.subTest(prompt=prompt_id):
                self.assertIn("ROLE / SOURCE / DONE / SELF-CHECK", content)
                self.assertIn("- ROLE:", content)
                self.assertIn("- SOURCE:", content)
                self.assertIn("- DEFINITION OF DONE:", content)
                self.assertIn("- SELF-CHECK:", content)
        self.assertIn("senior correspondence editor", self.prompts["P72"]["copyContent"])
        self.assertIn("compare the final message back to the source", self.prompts["P72"]["copyContent"])
        self.assertIn("senior client-communications editor", self.prompts["P73"]["copyContent"])
        self.assertIn("preserve that uncertainty instead of manufacturing confidence", self.prompts["P73"]["copyContent"])
''',
    )


def main() -> None:
    harden_shared_policy()
    harden_p07()
    harden_p86()
    harden_correspondence()
    add_tests()
    print(
        json.dumps(
            {
                "status": "mutated canonical sources and focused tests",
                "targets": ["shared operational policy", "P07", "P86", "P72", "P73"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
