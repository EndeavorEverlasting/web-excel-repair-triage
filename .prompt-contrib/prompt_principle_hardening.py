from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(path: str, payload) -> None:
    (ROOT / path).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
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
    target.write_text(text.replace(marker, "\n" + body.rstrip() + marker, 1), encoding="utf-8")


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
    if needle not in policy["copy_content_appendix"]:
        raise SystemExit("shared actionability insertion point missing")
    policy["copy_content_appendix"] = policy["copy_content_appendix"].replace(
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
- ROLE: Act as the senior repository execution engineer/coordinator for this sprint. Own bounded implementation, verification, integration, and handoff rather than merely advising the operator.
- WHERE TO LOOK: Start with `Context or plan path` when supplied, then current governance/harness, canonical owner files, tests/validators/CI/artifacts, and overlapping work from refreshed provider truth. Resolve technical facts there before asking the user to repeat or inspect them.
- DEFINITION OF DONE: Before mutation, turn owned scope, requested behavior/artifacts, explicit constraints, repository acceptance gates, and proof requirements into a compact observable checklist.
- SELF-CHECK: Before claiming completion, verify material claims—including counts, paths, SHAs, branch/PR state, test/validator results, artifact identities, and unresolved gaps—against current evidence. Unsupported items are UNKNOWN or blockers, not plausible fill-ins."""
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
        "Audit one existing Prompt Kit prompt or a bounded family of candidate prompts against a supplied or discovered principle, then harden only compatible canonical owners without duplicating shared policy or changing stable identities unnecessarily."
    )
    prompt["useWhen"] = (
        "An existing prompt is weaker than current Prompt Kit patterns, or a learned prompt-design principle should be evaluated across every relevant existing prompt rather than only the first obvious target."
    )
    prompt["inspectFirst"] = (
        "Current main/PR/evidence floor; supplied principle/source example; named target or candidate target set; each candidate in raw and effective form; registry/profile and shared-policy owners; focused tests; generated parity; overlapping prompt/PR work."
    )
    prompt["expectedOutput"] = (
        "Existing canonical identities selectively hardened through a target ledger and principle-applicability matrix, minimal raw/shared-owner edits, focused semantic regressions, bounded growth, exact generated-site parity, and authorized mainline integration."
    )
    prompt["nextStep"] = (
        "Resolve single-target versus principle-propagation campaign mode, normalize the source into reusable principles, disposition the bounded candidate set, patch the smallest canonical owners, prove old plus new semantics, and converge the exact green result to main."
    )
    prompt["proofGate"] = (
        "Every relevant candidate is dispositioned; changed prompts retain identity/role; accepted principles have a source and concrete applicability reason; inherited policy and literal example wording are not cargo-cult copied; incompatible targets are rejected; old/new semantics are tested; raw growth stays bounded; parity and exact-head integration proof pass."
    )
    prompt["copyContent"] = """HARDEN ONE OR MORE EXISTING PROMPTS USING THE STRONGEST COMPATIBLE PRINCIPLES PROVEN BY THE CURRENT PROMPT KIT OR SUPPLIED SOURCE MATERIAL. MODIFY CANONICAL OWNERS; DO NOT CREATE DUPLICATE PROMPTS JUST TO PROPAGATE A PRINCIPLE.

Target prompt(s), if known: xyz_prompt_ids_names_or_resolve_from_context
Principle/source to integrate: xyz_principle_example_reference_or_infer_from_context
Specific weakness, if known: xyz_known_gap_or_infer_from_evidence

MISSION
Strengthen the relevant existing prompts without turning the Prompt Kit into universal boilerplate. Operate as SINGLE TARGET hardening or a bounded PRINCIPLE PROPAGATION CAMPAIGN. Preserve identity, role, profile, and useful semantics. Normalize the source principle, discover relevant targets, choose canonical owners, patch minimally, prove semantics, rebuild canonically, and integrate the exact validated result.

EXECUTION BRIEF
- ROLE: Act as a senior prompt-systems engineer responsible for prompt architecture, semantic regression, and anti-bloat ownership decisions.
- WHERE TO LOOK: Start with supplied source/example and named targets, then current raw/effective registries, shared policy owners, focused tests, generated output, and refreshed overlapping work.
- DEFINITION OF DONE: Every material candidate is dispositioned; every accepted change is minimal and proven; generated output matches canonical sources; integration is complete or an exact gate is named.
- SELF-CHECK: Verify target IDs, donor/source claims, raw/effective classification, size claims, validator/test results, generated identity, commit/PR state, and rejection reasons against current evidence.

1. RESOLVE CURRENT TRUTH AND CAMPAIGN SHAPE
Determine whether the request names one target or asks to propagate a principle. If a principle is supplied without a complete target set, do not stop at the first obvious prompt: search the combined registry for prompts whose mission, failure modes, output contract, or proof behavior could materially benefit. Resolve raw/effective forms, owners, focused tests, generated site, and overlapping work. Reuse an existing owning lane when safe. Refresh before final exact-head conclusions and invalidate affected evidence when the floor moves.

2. RAW VS EFFECTIVE PROMPT
Raw records own prompt-specific semantics; effective prompts may inherit shared policy. Do not paste inherited actionability, freshness, integration, evidence-binding, or closeout doctrine into every raw record. Count effective inherited behavior as present unless a direct-consumer prompt has a concrete reason for a compact local version.

3. NORMALIZE THE SOURCE PRINCIPLE
Translate the example, article, donor prompt, incident, or observation into atomic reusable behaviors. Distinguish principle from costume. A source may demonstrate role/competence anchoring, an explicit source map, observable definition of done, and final self-check against evidence. Preserve those behaviors without copying literal domain wording, invented tenure, emotional urgency, `take a deep breath` style filler, or source-specific formatting unless required by evidence.

4. HARVEST RELEVANT DONORS AND TARGETS
Inspect only the useful donors/shared owners and candidate prompts. Strong principles can include fresh evidence floors, exact artifact identity, stale-proof invalidation, bounded iteration, autonomous progression, fail-closed safety, source-of-truth precedence, role anchoring, explicit evidence locations, observable completion criteria, source-grounded self-check, proof ceilings, existing-work reuse, progressive disclosure, interruption recovery, dirty-work preservation, anti-fabrication, canonical-owner selection, and focused semantic regression. Strength elsewhere is evidence, not automatic applicability here.

5. BUILD THE PRINCIPLE APPLICABILITY MATRIX
For each material candidate record: target prompt; principle; source/donor or canonical policy owner; RAW/EFFECTIVE/BOTH/ABSENT; concrete gap; COMPATIBLE/INCOMPATIBLE/NOT NEEDED; RAW CHANGE/SHARED-OWNER CHANGE/NO CHANGE; focused proof. Every material candidate must receive a disposition. Silent omission is invalid.

6. CHOOSE THE CANONICAL OWNER
Prefer a shared owner only when behavior is truly common to the governed family. Prefer a raw edit for role-specific or direct-consumer-critical behavior. Do not create global policy for a narrow case or duplicate shared blocks merely to look comprehensive.

7. HARDEN CANONICAL TARGETS
Patch existing records rather than renumbering/cloning. Change only semantic fields that need strengthening. Keep stable identity/profile/color/category/copySheet unless separate evidence requires change. Use concise concepts rather than donor-section copies.

8. P03 REFERENCE CASE
For P03, compare its discovery-plus-first-sprint job with applicable current P07, P13, P48, P76, P83, P84, P85, and shared-policy principles. Adopt only what strengthens that job; do not transform P03 into those owners.

9. ANTI-BLOAT / ANTI-CARGO-CULT GATE
Reject changes justified only by `another prompt has this`. Prefer inheritance, a shared-family owner, or one target-specific sentence. If a raw target grows materially, tie each addition to a concrete failure mode and seek a smaller formulation. A campaign succeeds by correct coverage, not by number of edited prompts.

10. SEMANTIC REGRESSION PROOF
Extend the closest focused test for each changed owner, or one family-level test for a shared owner. Prove old defining behavior remains and new behavior is effective; add negative/boundary assertions where useful. Check source size when practical. Generated-site presence alone is not semantic proof.

11. VALIDATE AND ITERATE
Run owner/registry validation, focused semantic tests, applicable language/order/discovery/build checks, exact generated-site parity, and patch hygiene. Perform one deliberate second pass for duplicated policy, identity drift, weakened old behavior, stale output, missed targets, unnecessary growth, or moved evidence. Stop at a bounded fixed point.

DELIVER
Report campaign mode; normalized principles; targets changed; targets rejected/not-needed and why; shared owners changed; semantic fields; focused proof; raw-size impact; registry/helper/build validation; generated parity; commit/PR/merge state; and resulting main SHA or exact blocker. Success is correct principle coverage with stronger proof, not a larger Prompt Kit."""
    prompt["keywords"] = list(dict.fromkeys(prompt["keywords"] + [
        "multi prompt hardening", "principle propagation", "prompt campaign hardening",
        "cross prompt audit", "role source done self check",
    ]))
    if len(prompt["copyContent"]) >= 7600:
        raise SystemExit(f"P86 raw copyContent exceeded anti-bloat gate: {len(prompt['copyContent'])}")
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
- SOURCE: Treat supplied draft, audience/context, and explicit facts as authoritative. Do not invent names, dates, numbers, owners, deadlines, commitments, approvals, or motives.
- DEFINITION OF DONE: One send-ready message preserves every material fact/boundary, makes the supported ask clear, removes avoidable friction, and contains no meta commentary.
- SELF-CHECK: Before output, compare the final message back to the source and verify every factual or quantitative claim, name, date, commitment, owner, deadline, and material boundary. Preserve ambiguity or omit unsupported detail rather than guessing."""
        p72["copyContent"] = p72["copyContent"].replace("OBJECTIVE\n", block + "\n\nOBJECTIVE\n", 1)
    if marker not in p73["copyContent"]:
        block = """ROLE / SOURCE / DONE / SELF-CHECK
- ROLE: Act as a senior client-communications editor. Translate internal work into recipient-relevant truth without exposing irrelevant machinery or sanitizing material bad news.
- SOURCE: Treat supplied draft, audience/context, and supported facts as authoritative. Translate/remove implementation detail only when no material outcome, risk, dependency, obligation, date, or requested action changes.
- DEFINITION OF DONE: One external-facing message explains what happened, what matters, remaining constraints, and required action without irrelevant process narration.
- SELF-CHECK: Before output, compare the final message with the source and verify every material status, number, date, commitment, risk, dependency, limitation, and requested action. If source evidence is uncertain, preserve that uncertainty instead of manufacturing confidence."""
        p73["copyContent"] = p73["copyContent"].replace("MISSION\n", block + "\n\nMISSION\n", 1)
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
        raw_prompts = json.loads((REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
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
    print(json.dumps({"status": "mutated canonical sources and focused tests", "targets": ["shared operational policy", "P07", "P86", "P72", "P73"]}, indent=2))


if __name__ == "__main__":
    main()
