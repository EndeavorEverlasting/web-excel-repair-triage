#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
by_id = {prompt["id"]: prompt for prompt in payload["prompts"]}

p79 = by_id["P79"]
p79.update(
    {
        "sprintRole": "Harvest one or many reusable Prompt Kit contributions from the full relevant context, distinguish user/source-bound context from agent-generated working context, strengthen canonical owners first, add only genuinely missing prompts through the helper, and execute the contribution set through focused proof and mainline convergence.",
        "useWhen": "The current chat contains one or many reusable prompt/workflow insights and the operator wants the smallest complete Prompt Kit contribution set implemented without restating recoverable context, inventing user requirements, duplicating existing owners, or stopping at a green feature branch.",
        "inspectFirst": "The entire accessible current conversation relevant to the request, including earlier decisions, examples, corrections, constraints, rejected wording, attachments, and follow-ups; distinguish user/source-bound context from agent-generated working context; then refresh current Triage default-branch/PR truth, combined Prompt Kit ownership, focused semantic tests, and deterministic helper routing only when needed.",
        "expectedOutput": "A whole-chat contribution ledger covering every material insight; an explicit context-authority map; zero or more canonical owner strengthenings; zero, one, or many helper-allocated new prompts added serially without guessed identities; bounded implement/validate/critique passes; focused semantic and generated-site proof; and the exact validated authorized result integrated into current main or stopped only by a named merge gate.",
        "nextStep": "Recover the relevant context, classify user-bound versus agent-generated working context, build the owner/contribution ledger, execute every justified strengthen/add action, run a reverse harvest and focused proof, then keep advancing the exact validated head through review and merge until main contains the contribution set or a concrete integration blocker is proven.",
        "proofGate": "The immediate request is the anchor rather than the context boundary; user/source facts and constraints are never replaced by invented working context; agent-generated hypotheses/context are explicitly subordinate and verified where exactness matters; every material insight is dispositioned; zero-to-many ADD actions are supported and multiple adds use the helper serially with fresh identity after each mutation; strengthenings preserve owner identity; at least two evidence-changing passes occur when material work exists; green branch/PR status is not terminal while safe authorized integration remains; focused semantics, exact-site parity, and resulting-main proof pass.",
        "copyContent": """ADD OR STRENGTHEN ONE OR MANY PROMPT KIT PROMPTS FROM THE FULL RELEVANT CONTEXT. EXECUTE THE REPOSITORY WORK TO A BOUNDED FIXED POINT; DO NOT STOP AT A PLAN, HELPER RECEIPT, GREEN PR, OR REVIEW-READY BRANCH WHILE SAFE AUTHORIZED WORK REMAINS.

CANONICAL REPO
`EndeavorEverlasting/web-excel-repair-triage`

MISSION
Turn the current request plus earlier relevant context into the smallest complete Prompt Kit contribution set. A contribution set may contain zero or more STRENGTHEN actions and zero, one, or many ADD actions. Recover materially relevant decisions, corrections, examples, rejected wording, definitions, constraints, and dependencies; strengthen canonical owners before creating identities; use deterministic repository machinery for exact registry mechanics; validate the whole set; and converge the exact green result into current main when authorized.

0. CONTEXT AUTHORITY CONTRACT
Do not confuse recovering context with inventing it.

USER / SOURCE-BOUND CONTEXT is authoritative for the task when supported by the current conversation, supplied files, explicit user statements, repository contracts, or other named sources. Preserve its facts, terminology, preferences, constraints, accepted/rejected wording, and distinctions. You may organize or compress it, but do not silently replace it with a more convenient interpretation.

AGENT-GENERATED WORKING CONTEXT is allowed and often useful: owner maps, hypotheses, candidate interpretations, temporary design frames, inferred dependencies, comparison criteria, draft acceptance language, or a proposed decomposition created to make the work executable. Create this context proactively when it reduces ambiguity or reveals missing structure. Label it internally as working/inferred context, test it against authoritative evidence, and discard or revise it when contradicted. It may complement user context; it may not manufacture user history, preferences, exact facts, requirements, approvals, or source claims.

If an exact fact is missing, retrieve it from current deterministic structure when possible. If a non-exact planning assumption is needed for reversible work, make the smallest explicit working assumption and keep it easy to revise. Escalate only when a genuinely user-only decision blocks safe progress.

1. FRESH EXECUTION FLOOR
Before branch-sensitive conclusions or mutation, refresh remote/provider truth. Resolve current default branch, current/open/recent overlapping Prompt Kit work, owning registries/builders/helpers/tests, and generated-site parity. Reuse a safe existing owner/branch when practical; isolate only when repository policy, concurrent writers, dirty state, or collision risk requires it. Treat prior chat SHAs and prior-agent completion claims as historical evidence, not the current floor.

2. WHOLE-CONTEXT HARVEST — PASS 1
Start from the immediate request, then traverse earlier accessible context for the same use case and dependencies. The text immediately above this prompt is an anchor, not the context boundary. Include recoverable pasted/generated content, attachments, prior definitions, examples, corrections, `also`/`another` follow-ups, accepted/rejected wording, and earlier implementation decisions when materially relevant. Ignore unrelated history.

Build a compact ledger:
`insight | authority/context source | current owner | action | proof`
Actions are STRENGTHEN / ADD / ALREADY COVERED / OUT OF SCOPE.
No material insight may silently disappear. Do not make the operator repeat context already recoverable by the agent.

3. OWNER MAP BEFORE NEW IDENTITIES
Search the combined current Prompt Kit for exact, adjacent, and materially overlapping owners. Compare trigger, mission, scope, context contract, failure behavior, proof level, and closure—not title alone.
- STRENGTHEN when an owner already has the core job but lacks compatible context recovery, failure handling, iteration, usability, proof, or convergence semantics.
- ADD only when a bounded behavior has a distinct trigger and closure condition that would make an existing owner materially incoherent if absorbed.
- ALREADY COVERED requires concrete current prompt evidence.
Do not mint a second identity because alternate wording sounds attractive.

4. DEFINE THE COMPLETE CONTRIBUTION SET
The result is not restricted to one prompt. Produce the smallest coherent set implied by the evidence:
- 0..N strengthened owners;
- 0..N genuinely new prompts;
- the closest focused semantic regressions;
- generated artifact/site updates owned by canonical builders.

For multiple ADD actions, prepare the semantic drafts as one conceptual batch but execute helper mutations SERIALly. Identity is stateful: after each successful add, the next helper call must observe the newly current registry. Never preassign or guess `id`, `seq`, or `copySheet` for the batch. If one add fails, repair its semantic/routing problem and resume from current helper truth; do not manually force the expected number.

5. COMPLEMENT — DO NOT MERELY TRANSCRIBE
Preserve explicit user intent, then add only compatible utility revealed by chat/repository evidence: useful failure states, context distinctions, entrypoints, proof levels, user-only gates, iteration, discoverability, integration seams, or adjacent examples that make the workflow more executable and reusable. Do not invent unrelated requirements or universal checklists. When the user supplied a narrower definition, that definition wins over a generic model tendency.

6. IMPLEMENT, DO NOT HAND OFF AGENT-CAPABLE WORK
For STRENGTHEN, edit the canonical source and closest focused regression.
For each ADD:
- choose the closest existing registry/profile; inspect helper routing once if unclear;
- draft semantic fields only; never set helper-owned identity fields;
- run `python scripts/prompt_registry_ops.py add --input <draft.json> --registry <existing_registry_id>`;
- let the helper allocate identity, reject obvious duplicates, inject shared policy, rebuild the generated site, prove parity, and roll back failed registry/site mutation.

Execute safe repository work yourself: source edits, helper calls, tests, builds, review repair, commits, pushes, PR updates, base reconciliation, and merge when authorized. Do not convert these into operator instructions merely because several prompts are being changed.

7. P07-STYLE ITERATION AND PROGRESS
Use bounded IMPLEMENT -> VALIDATE -> INSPECT -> CRITIQUE -> IMPROVE passes. First green is evidence, not automatic completion.
- After an evidence-changing pass, record terse `CHANGED | PROVED | NEXT` progress and continue when safe work remains.
- Inspect the actual diff and effective prompt behavior, not only raw source.
- Treat failing tests/review findings as evidence about the implementation; repair the canonical owner rather than weakening acceptance.
- Preserve separately owned/concurrent work and rebase/merge/reconcile only through non-destructive repository policy.
- Stop iterating only at a bounded fixed point or named external/user-only gate.

8. WHOLE-CONTEXT HARVEST — PASS 2
After implementation, traverse relevant context again in the opposite direction. Look specifically for missed `also`, `another`, `strengthen`, `live`, `regression`, `prototype`, corrections, examples, context-authority distinctions, referenced sources, earlier accepted definitions, and neighboring owners that should be strengthened to prevent overlap. Update the ledger and close concrete gaps. Do not manufacture empty passes.

9. FOCUSED PROOF
Run the closest semantic assertions the generic helper cannot prove. Verify each strengthened prompt retains its original role and every new prompt remains distinct from adjacent owners. Then run helper/registry validation, applicable language/order/discovery checks, generated-site `--check`, and `git diff --check`. Refresh the default-branch floor before final proof; if a required owner/base moved, reconcile and rerun affected checks.

10. MAINLINE CONVERGENCE IS PART OF COMPLETION
A commit, pushed branch, open PR, review-ready state, or green CI is intermediate evidence. When the exact validated owned head is mergeable, required checks/validators are green, dependencies/reviews/conflicts are clear, merge authority exists, and the user has not prohibited integration, merge it into the current default branch in the same run. Re-fetch main and prove it contains the intended prompt/source/generated-site result. If integration is blocked, name the exact gate and execute the action that advances it rather than stopping at status.

FAIL-CLOSED
If routing is ambiguous, inspect once. If a contract mismatch names an owner/helper/builder, inspect only that surface. Do not load the entire Prompt Kit architecture, guess identities, bypass helper parity, weaken validators, fabricate context, or make the operator a context courier/test runner.

DELIVER
Keep closeout compact: contribution ledger; context-authority decisions; strengthened IDs/names; new helper receipts; focused semantic results; prompt count/parity; validation; commit/PR/merge; resulting main SHA; remaining gaps/risks/blockers/proof ceiling; and the first executable next action. Use `none; no safe actionable work remains` only after authorized integration and proof are actually complete.""",
        "keywords": [
            "add prompt",
            "add prompts",
            "multiple prompts",
            "prompt contribution set",
            "prompt adder",
            "prompt registry",
            "strengthen prompt",
            "whole chat harvest",
            "context authority",
            "user context",
            "agent generated context",
            "working context",
            "mainline convergence",
            "P07 qualities",
            "serial helper add",
        ],
    }
)

p82 = by_id["P82"]
p82["sprintRole"] = "Make functional and creative prototyping a disciplined delivery loop: build the smallest real candidate or materially distinct creative variants, measure against stable acceptance criteria and user-bound context, critique observable gaps, preserve evidence, refine deliberately, and promote only after the appropriate final proof."
p82["useWhen"] = "A feature, interface, artifact, architecture, workflow, automation, design, narrative, visual, presentation, brand direction, or other creative output has meaningful unknowns and quality improves when an agent makes concrete prototypes/variants, compares them against stable user/source constraints, and refines before final delivery."
p82["inspectFirst"] = p82["inspectFirst"].rstrip(".") + "; for creative work, inspect the user brief, audience, desired effect, accepted/rejected examples, references/assets, style/brand constraints, delivery medium, and prior feedback while separating authoritative user/source context from agent-generated concept hypotheses."
p82["expectedOutput"] = "A bounded sequence of increasingly faithful working candidates. Engineering prototypes carry hypothesis/acceptance evidence; creative prototypes carry a user/source-bound brief plus materially distinct variants, explicit retained/revised/discarded traits, and concrete critique against the same brief. Both modes preserve last-known-good state, remove prototype debt before final, and distinguish prototype proof from final acceptance."
p82["nextStep"] = "Build the smallest real prototype that tests the highest-risk assumption; for creative work, produce 2-4 materially distinct variants when divergence would teach something, critique them against the fixed user/source brief, preserve the strongest traits, and execute the next justified refinement until the final-candidate gate or exact blocker is reached."
p82["proofGate"] = "Each iteration reduces a named uncertainty rather than producing cosmetic churn; user/source-bound constraints remain authoritative while agent-generated creative hypotheses stay explicit and revisable; materially uncertain creative directions are made concrete rather than argued abstractly; variants are distinct enough to learn from; critique uses the same brief/rubric; regressions and discarded paths remain visible; subjective user feedback is requested only after concrete candidates exist when taste cannot be resolved deterministically; and no prototype is mislabeled final."
creative_block = """

CREATIVE PROTOTYPE MODE
When the output itself is creative—visual design, writing, narrative, presentation, brand expression, interaction concept, naming, illustration, layout, or another taste-bearing artifact—use the same evidence discipline without pretending subjective quality is fully deterministic.

1. Separate AUTHORITATIVE CREATIVE CONTEXT from WORKING CREATIVE CONTEXT. The user's brief, audience, desired effect, supplied references/assets, accepted/rejected examples, terminology, brand/style constraints, and explicit feedback are authoritative. The agent may generate concept territories, metaphors, mood words, compositional hypotheses, draft rubrics, or inferred design rationale as working context, but must not present those inventions as the user's preferences or source facts.
2. Diverge when uncertainty is real. Produce 2-4 materially different prototypes when multiple directions could plausibly satisfy the brief. Change meaningful dimensions—structure, visual hierarchy, tone, metaphor, pacing, composition, information density, or interaction model—not superficial color swaps that teach nothing.
3. Critique against one stable creative brief. Use only relevant dimensions such as fidelity to intent, audience fit, clarity, emotional effect, coherence, distinctiveness, legibility/accessibility, medium constraints, brand consistency, and production feasibility. Do not average every candidate into generic mush merely to avoid choosing.
4. Preserve winning traits explicitly. Record what to KEEP, COMBINE, REVISE, or DISCARD. A hybrid is valid only when the retained elements are compatible and the synthesis has a clear concept, not because every variant contributed something.
5. Use the agent's available creation tools directly for prototypes when safe. Do not ask the user to imagine alternatives the agent can render/draft itself. Ask the user for a focused taste decision only when concrete candidates reveal a genuinely subjective fork that evidence cannot settle.
6. Final creative proof is fit-to-brief plus deliverable integrity, not repository tests alone. Validate file/format/accessibility/technical constraints where applicable, then distinguish automated checks from human taste/acceptance.
"""
if "CREATIVE PROTOTYPE MODE" not in p82["copyContent"]:
    marker = "\n\n4. PRESERVE THE LAST KNOWN-GOOD STATE"
    p82["copyContent"] = p82["copyContent"].replace(marker, creative_block + marker)
for kw in ["creative prototype", "creative variants", "creative iteration", "concept variants", "design prototype", "creative brief"]:
    if kw not in p82["keywords"]:
        p82["keywords"].append(kw)

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

creative_plan = {
    "name": "Creative Direction & Production Planner",
    "type": "PLAN + CREATIVE",
    "class": "CREATIVE / DIRECTION PLANNING",
    "sprintRole": "Turn an ambiguous or high-choice creative request into an executable direction: recover the authoritative brief, create only clearly labeled working context, explore materially different concept territories, choose or narrow a direction with explicit criteria, and sequence production without prematurely making the final artifact.",
    "useWhen": "A visual, writing, presentation, brand, narrative, campaign, interface, naming, or other creative task needs a real creative plan before production because intent, audience, concept, references, constraints, or direction choices are not yet organized enough for efficient execution.",
    "inspectFirst": "Current user request and earlier relevant context; audience and desired effect; supplied references/assets; accepted/rejected examples; terminology, brand/style, medium, accessibility, legal/rights, time/budget, and delivery constraints; existing related artifacts; prior feedback; any exact source facts that must not be replaced by invented creative rationale.",
    "expectedOutput": "An authority-aware creative brief, explicit user/source-bound versus agent-generated working context, 2-4 materially different concept territories when useful, a direction decision or focused unresolved fork, production stages and assets, quality criteria, risks/dependencies, prototype handoff, and an executable next creative action rather than a mood-board-only plan.",
    "nextStep": "Lock the authoritative brief, generate the minimum useful set of distinct concept territories, select or narrow the direction using the stated criteria, then execute the first concrete prototype/outline/storyboard/mockup that tests the highest-risk creative assumption.",
    "proofGate": "The plan preserves user/source facts and constraints without inventing preferences; generated creative context is labeled as hypothesis or proposal; concept territories are meaningfully distinct when divergence is needed; the chosen direction maps back to audience/intent/constraints; production stages, assets, decisions, and proof points are executable; and the plan hands off to a concrete prototype rather than ending in generic inspiration language.",
    "copyContent": """CREATE AN EXECUTABLE CREATIVE PLAN BEFORE COMMITTING TO THE FINAL ARTIFACT. RECOVER THE REAL BRIEF, GENERATE USEFUL WORKING CONTEXT WITHOUT PRETENDING IT CAME FROM THE USER, EXPLORE DISTINCT DIRECTIONS, AND END AT THE FIRST CONCRETE PROTOTYPE ACTION.

Creative task: resolve from the current conversation/workspace
Target audience / desired effect: resolve from evidence; do not invent as user fact
Delivery medium: resolve if known

MISSION
Convert a creative request into a direction that can actually be produced. The goal is not a generic brainstorm or a project-management checklist. Preserve what the user/source already established, create the missing planning structure yourself, widen the concept space where useful, narrow it deliberately, and leave a production path that a creative prototype can execute immediately.

1. RECOVER THE AUTHORITATIVE BRIEF
Harvest the current request plus earlier relevant context for:
- audience and desired effect;
- message/content that must survive;
- supplied references, assets, examples, and anti-examples;
- accepted/rejected wording or directions;
- tone, style, brand, accessibility, platform/medium, format, rights/privacy, timing, and budget constraints;
- previous creative decisions or feedback that should not be rediscovered.
Do not ask the user to repeat recoverable information.

2. SEPARATE USER CONTEXT FROM CREATED CONTEXT
Maintain two mental buckets:
- USER/SOURCE-BOUND: facts, preferences, constraints, terminology, examples, approvals, and source claims actually supported by the conversation or supplied material.
- AGENT-GENERATED WORKING CONTEXT: proposed themes, metaphors, concept names, mood words, structure, inferred audience hypotheses, candidate rubrics, and production assumptions created to make the task executable.
Create working context proactively, but never relabel it as something the user said or wanted. If it conflicts with authoritative context, discard it.

3. DEFINE THE CREATIVE PROBLEM
Write a compact planning frame: `audience -> desired effect -> core content -> constraints -> medium -> success signals`. Identify the 1-3 uncertainties most likely to cause rework, such as tone, hierarchy, visual metaphor, narrative structure, information density, interaction model, or asset feasibility.

4. DIVERGE INTO MATERIAL CONCEPT TERRITORIES
When the direction is not already fixed, create 2-4 distinct concept territories. Each territory should have:
- one-sentence concept;
- why it fits the brief;
- visual/verbal/structural language as relevant;
- what it deliberately emphasizes or sacrifices;
- required assets or production implications;
- the prototype that would test it fastest.
Do not manufacture difference through cosmetic swaps. Distinct concepts should teach something if prototyped.

5. NARROW WITHOUT FLATTENING
Compare territories under the same relevant criteria: fidelity to intent, audience fit, clarity, emotional effect, coherence, distinctiveness, accessibility/legibility, medium constraints, feasibility, and compatibility with supplied references/brand. Select a direction when evidence is adequate. If subjective taste is the only remaining fork, present the smallest concrete choice to the user after doing the planning work; do not ask an abstract preference question before creating viable directions.

6. BUILD THE PRODUCTION MAP
For the chosen direction, define:
- content/asset inventory and provenance;
- structure/storyboard/information hierarchy;
- production stages in dependency order;
- tools or artifact types needed;
- checkpoints where the brief should be revalidated;
- technical/export/accessibility requirements;
- what can be automated versus what requires human taste/approval;
- explicit non-goals to prevent drift.
Keep the plan proportional to the task.

7. HAND OFF TO CREATIVE PROTOTYPING
End with the first concrete prototype action that tests the largest remaining uncertainty: draft the opening section, render a key frame, create a low-fidelity layout, build a slide/storyboard slice, generate naming candidates in context, or another real artifact. Specify what observation would cause KEEP / REFINE / DISCARD.

8. SECOND PASS
Re-read the relevant context from the opposite direction. Check for missed `also`, examples, corrections, disliked directions, assets, medium constraints, or prior choices. Remove invented assumptions that crept into the authoritative brief. Stop at a bounded planning fixed point.

DELIVER
Report the authoritative brief, generated working context, concept territories, selected/narrowed direction, production map, unresolved subjective fork if any, and the first prototype action. The plan succeeds when another agent—or the same one in the next step—can make the first real artifact without rediscovering the creative intent.""",
    "keywords": ["creative plan", "creative planning", "creative direction", "concept planning", "art direction", "design plan", "narrative plan", "presentation plan", "brand direction", "creative brief", "concept territories", "production plan"],
    "profile": "spec-architecture",
    "color": "Lavender",
}

creative_harness = {
    "name": "Creative Context & Quality Harness Builder",
    "type": "BUILD + HARNESS",
    "class": "CREATIVE / CONTEXT HARNESS",
    "sprintRole": "Build a reusable creative harness that preserves authoritative user/source context, separates agent-generated working context, organizes references/assets/examples, defines repeatable briefs and quality rubrics, routes planning/prototyping/production, and reduces repeated re-explanation without freezing creativity into one template.",
    "useWhen": "Creative work recurs across sessions, agents, or artifacts and quality drifts because style, audience, terminology, references, examples, constraints, feedback, asset provenance, or evaluation criteria must be repeatedly reconstructed from memory.",
    "inspectFirst": "Current and prior creative briefs; user/source-bound preferences and constraints; supplied references/assets and rights/provenance; accepted and rejected outputs; terminology/style/brand guides; prompt templates; feedback history; target media/tools; current workspace/repository structure; existing context, asset, evaluation, or artifact registries that should be reused instead of duplicated.",
    "expectedOutput": "A lean versioned creative harness with an authority map, demand-loaded context layers, reference/asset registry, examples and anti-examples, reusable brief template, working-context scratch boundary, creative quality rubric, plan->prototype->production routing, change/invalidation rules, and one representative creative task proving the harness reduces re-explanation while preserving flexibility.",
    "nextStep": "Extract the smallest durable creative context from current evidence, separate source-bound facts from generated working context, register the references/assets and quality criteria, wire the plan/prototype/production route, then run one representative creative task through the harness and repair any drift or missing context it exposes.",
    "proofGate": "A fresh agent can recover the creative brief and constraints without inventing user preferences; generated hypotheses cannot masquerade as authoritative context; references/assets have provenance and load conditions; examples/anti-examples clarify rather than overfit style; the rubric can critique a representative prototype without forcing sameness; changed source context has an invalidation/update path; one end-to-end creative task uses the harness successfully; and the harness remains lean enough to demand-load detail instead of becoming a giant permanent prompt.",
    "copyContent": """BUILD A REUSABLE CREATIVE HARNESS SO CREATIVE QUALITY DOES NOT DEPEND ON MODEL MEMORY OR THE USER REPEATING THE SAME BRIEF. PRESERVE AUTHORITY, REFERENCES, AND QUALITY SIGNALS WHILE KEEPING GENERATED CREATIVE CONTEXT EXPLICITLY REVISABLE.

Workspace/repo: resolve from current context
Creative domain or recurring output: resolve from the user's request
Existing briefs/assets/style guidance: recover before inventing a new owner

MISSION
Create the smallest durable system that lets future creative planning and prototyping recover the right context, references, constraints, and evaluation criteria on demand. This is not a technical CI harness with a creative name, and it is not one giant system prompt. It is a reusable context-and-quality substrate for taste-bearing work.

1. RECOVER REPEATED CREATIVE FRICTION
Find what repeatedly has to be re-explained or rediscovered: audience, goals, tone, vocabulary, brand/style constraints, visual language, references, accepted/rejected examples, asset locations, rights/provenance, medium/export requirements, feedback patterns, and quality criteria. Distinguish durable context from one-off task details.

2. INSTALL AN AUTHORITY MODEL
Use at least these layers:
A. USER/SOURCE-BOUND CONTEXT — supported facts, preferences, constraints, terminology, supplied references/assets, approvals/rejections, and exact source claims. This is durable only while its source/version remains current.
B. AGENT-GENERATED WORKING CONTEXT — concept hypotheses, mood words, candidate metaphors, inferred rationale, temporary rubrics, draft structures, and synthesis notes. Useful, but revisable and never evidence that the user said or preferred something.
C. TASK-LOCAL CONTEXT — the current artifact's brief, decisions, prototype evidence, and temporary production state.
Define precedence and what invalidates each layer.

3. FACTOR THE HARNESS INTO LEAN OWNERS
Reuse existing workspace conventions where possible. Create or strengthen only the minimum useful owners, such as:
- compact creative orientation/README or manifest;
- source/authority index with version/provenance;
- reference and asset registry with load conditions and rights notes;
- examples + anti-examples library that records WHY they matter rather than copying style blindly;
- reusable creative-brief template;
- quality/evaluation rubric by output type;
- working-context scratch area or structured dossier that is explicitly non-authoritative;
- artifact/prototype history or decision log when comparison across iterations matters;
- routing from creative plan -> creative prototype -> final production/acceptance.
Do not create every file on this list automatically. Deep detail should be demand-loaded.

4. MAKE CONTEXT RETRIEVABLE, NOT MASSIVE
A future agent should be able to answer `What must I know to create this?` without loading every prior artifact. Prefer stable IDs, short summaries with pointers, metadata, tags, source hashes/versions, and explicit load triggers. Put large images, long source material, research, and historical prototypes behind references. If an exact fact can be retrieved from a file/schema/asset manifest, do not rely on prose memory.

5. BUILD A CREATIVE QUALITY RUBRIC WITHOUT HOMOGENIZING OUTPUT
Define only dimensions that reflect the user's real goals: fidelity to intent, audience fit, clarity, emotional effect, coherence, distinctiveness, brand/style consistency, accessibility/legibility, medium constraints, craft/production quality, or others supported by the domain. Include valid counterexamples and anti-examples. The rubric should help critique; it must not force every artifact toward the same average style.

6. CONNECT PLAN, PROTOTYPE, AND PRODUCTION
Route recurring work deliberately:
- CREATIVE PLAN recovers the brief, creates working context, explores territories, and chooses/narrows direction.
- CREATIVE PROTOTYPE makes the direction concrete, compares materially different variants when useful, records KEEP/REFINE/DISCARD evidence, and requests focused taste feedback only when needed.
- PRODUCTION/FINALIZATION creates the full deliverable, applies technical/export/accessibility checks, and records final user acceptance separately from automated proof.
A fresh task should load only the context needed for its stage.

7. VERSION AND INVALIDATE
Record source identity/version for durable context where practical. When the user changes a preference, replaces a reference, updates a brand guide, rejects a previously accepted pattern, or changes the target medium, invalidate or supersede affected derived working context. Do not keep stale generated rationale alive merely because it was written into the harness first.

8. PROVE THE HARNESS ON A REPRESENTATIVE CREATIVE TASK
Run one real bounded task through it. Start with a fresh-agent perspective: recover the brief from harness sources, create a small plan, produce a concrete prototype, critique it with the rubric, and verify that no critical user context had to be guessed or re-requested. Measure context size/lookup burden when feasible and remove duplicated or always-loaded material revealed by the trial.

9. SECOND PASS / ANTI-BLOAT
Inspect what the harness caused the agent to load and what it still had to guess. Remove duplicate authority, split oversized always-on context, repair missing provenance or load triggers, and keep generated working context clearly non-authoritative. Stop at a bounded fixed point; do not turn a creative memory aid into a repository encyclopedia.

DELIVER
Report the creative harness owners, authority/context layers, references/assets registry, brief/rubric structure, routing, invalidation rules, representative trial, context-reduction evidence where available, remaining subjective/user-only gates, and integration state. The success condition is repeatable creative quality with less re-explanation—not more permanent prompt text.""",
    "keywords": ["creative harness", "creative context", "creative memory", "style harness", "design harness", "brand harness", "creative references", "asset registry", "creative rubric", "creative brief template", "creative workflow", "examples and anti examples"],
    "profile": "spec-architecture",
    "color": "Lavender",
}

Path("/tmp/creative-plan.json").write_text(json.dumps(creative_plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
Path("/tmp/creative-harness.json").write_text(json.dumps(creative_harness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST.read_text(encoding="utf-8")
method = r'''
    def test_creative_workflow_trio_and_p79_context_mainline_contract(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        prompts = payload["prompts"]
        by_id = {prompt["id"]: prompt for prompt in prompts}
        by_name = {prompt["name"]: prompt for prompt in prompts}

        p79 = by_id["P79"]
        p79_text = p79["copyContent"]
        for phrase in (
            "USER / SOURCE-BOUND CONTEXT",
            "AGENT-GENERATED WORKING CONTEXT",
            "zero, one, or many ADD actions",
            "execute helper mutations SERIALly",
            "P07-STYLE ITERATION AND PROGRESS",
            "MAINLINE CONVERGENCE IS PART OF COMPLETION",
            "green CI is intermediate evidence",
        ):
            self.assertIn(phrase, p79_text)
        self.assertIn("multiple prompts", p79["keywords"])
        self.assertIn("mainline convergence", p79["keywords"])

        p82 = by_id["P82"]
        self.assertIn("CREATIVE PROTOTYPE MODE", p82["copyContent"])
        self.assertIn("creative prototype", p82["keywords"])
        self.assertIn("user/source-bound", p82["proofGate"].lower())
        self.assertIn("2-4 materially distinct variants", p82["nextStep"])

        plan = by_name["Creative Direction & Production Planner"]
        harness = by_name["Creative Context & Quality Harness Builder"]
        self.assertNotEqual(plan["id"], harness["id"])
        self.assertEqual(plan["profile"], "spec-architecture")
        self.assertEqual(harness["profile"], "spec-architecture")
        self.assertIn("AGENT-GENERATED WORKING CONTEXT", plan["copyContent"])
        self.assertIn("CREATIVE PROTOTYPE", plan["copyContent"])
        self.assertIn("USER/SOURCE-BOUND CONTEXT", harness["copyContent"])
        self.assertIn("CREATIVE PLAN", harness["copyContent"])
        self.assertIn("CREATIVE PROTOTYPE", harness["copyContent"])
        self.assertNotIn("PROGRAM DESIGN", plan["class"])
        self.assertNotIn("SOFTWARE ARCHITECTURE", harness["class"])

        rendered = registry.render()
        self.assertIn("Creative Direction &amp; Production Planner", rendered)
        self.assertIn("Creative Context &amp; Quality Harness Builder", rendered)
'''
anchor = '\n\nif __name__ == "__main__":\n'
if "test_creative_workflow_trio_and_p79_context_mainline_contract" not in text:
    if anchor not in text:
        raise SystemExit("could not locate unittest module footer")
    text = text.replace(anchor, "\n" + method + anchor)
    TEST.write_text(text, encoding="utf-8")

print("prepared P79/P82 strengthenings and two semantic creative drafts")
