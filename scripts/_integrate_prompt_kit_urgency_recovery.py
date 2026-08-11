from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

P13_CONTENT = '''THE SAME PROBLEM HAS REPEATED. TREAT THAT AS A PROCESS DEFECT AND FIX THE SYSTEM THAT LET IT RECUR.

Do not ask the operator to restate a complaint, urgency signal, current proof floor, deployment gate, or missing parallel lane when the current conversation and repository evidence can recover it.

TRIGGER EXAMPLES
Use this prompt when the operator is effectively saying any of the following:
- "We need to move past R1" or another named proof/stage floor.
- "Deployment has held up."
- "You and the other agents do not appreciate the urgency."
- "A plan for a Sub-Part Agent was not in your output."
- "I keep telling agents the same thing."
- The same explanation, safety correction, setup fix, no-progress loop, missing parallelization, or completion failure has appeared again.

MISSION
Recover the repeated failure from evidence, advance the current critical path now, and install the smallest durable rule, prompt, validator, workflow, hook, ledger, or skill change that makes the recurrence less likely. The durable improvement is not a substitute for current execution: fix the process defect and move the work forward in the same sprint whenever tools and authority permit.

1. RECOVER THE RECURRENCE WITHOUT MAKING THE OPERATOR RETYPE IT
- Inspect the current conversation, recent handoffs, current repository law, work ledger, open PRs, current branch/worktree, recent commits, validators, artifacts, deployment/release state, and the last relevant failed or no-progress attempts.
- Identify the repeated operator correction in one sentence and cite the concrete evidence that it actually repeated.
- Distinguish a recurring process defect from a one-off failure. Do not create permanent doctrine for an isolated accident.
- If the operator used stage labels such as R1/R2 or named proof levels, preserve those exact labels. Do not invent their semantics; recover them from current evidence.

2. CLASSIFY THE FAILURE MODE
Choose every class that materially applies:
- EXECUTION_STALL — work keeps returning plans/status instead of advancing.
- URGENCY_MISS — the critical path is being treated as optional or low priority.
- PROOF_FLOOR_LOOP — an already-established proof/stage is being re-reported instead of moving to the next gate.
- DEPLOYMENT_DELAY — release/deploy/merge/runtime work is ready enough to advance but noncritical work is consuming the turn.
- MISSING_PARALLELISM — an independent lane should have been delegated or prepared for a Sub-Part Agent.
- REPEATED_EXPLANATION — the operator must keep re-explaining a known constraint or decision.
- TOOL_OR_SETUP_FRICTION — the same environment/command/setup failure keeps recurring.
- PROOF_INFLATION — static, synthetic, ACK, or partial evidence was overstated and caused rework.
- SAFETY_OR_SCOPE_REWORK — preventable unsafe or out-of-scope behavior keeps returning.

3. ESTABLISH THE CURRENT CRITICAL PATH
State explicitly:
- current proven floor or stage;
- next unproven gate;
- deployment/release/runtime blocker when relevant;
- the one action on the critical path that can be executed now;
- work that is useful but not critical and therefore must not displace the gate.
If the operator says to move past R1 or another stage, do not spend the response proving R1 again unless current evidence shows it regressed. Advance to the next real gate or prove the exact blocker preventing that advance.
If deployment, release, merge, or live proof is the current goal, prioritize the action that advances that gate over polish, commentary, broad documentation, or new planning unless those directly unblock it.

4. EXECUTE ONE CRITICAL-PATH ADVANCEMENT NOW
- Perform the highest-leverage safe action available in the current environment before producing a long report.
- A branch listing, PR status, repeated validation, plan, handoff, or explanation is supporting evidence, not sufficient movement when implementation, integration, deployment preparation, validation repair, or another authorized action remains executable.
- Reuse existing contracts, helpers, validators, artifacts, and repository patterns instead of starting a new subsystem.
- Keep the mutation bounded and preserve unrelated work.
- If the true blocker is external authority, credentials, protected runtime access, review, merge protection, or a technician/operator action, name it exactly and produce the smallest action packet that advances that gate.

5. SUB-PART AGENT PLAN IS MANDATORY WHEN PARALLEL WORK IS SAFE OR WHEN MISSING PARALLELISM CAUSED DELAY
Do not omit parallelization analysis from the output.
For every independent lane worth delegating, provide a Sub-Part Agent packet containing:
- lane / mission;
- owned scope;
- forbidden scope;
- dependency and start gate;
- exact inputs and files to inspect;
- expected tracked artifact or proof;
- validation command/gate;
- collision boundary with the primary lane and other agents;
- return packet: files changed, commit/artifact/proof, blockers, and next action.
If the environment can actually launch independent sub-agents and the lane is safe, launch the useful lane instead of only describing it. If the environment cannot launch agents, emit one self-contained copy-paste Sub-Part Agent prompt and keep executing the primary lane yourself. Never use a Sub-Part Agent plan as an excuse to stop the primary critical path.
If no safe parallel lane exists, state `Sub-Part Agent: none — serialized dependency` and name the exact dependency that makes parallel work unsafe.

6. INSTALL THE SMALLEST DURABLE PREVENTION
Choose the correct authority; do not duplicate authority across all surfaces.
Possible owners include:
- prompt registry when the failure is instruction/recovery behavior;
- repository governance when it is durable repository law;
- workflow/skill when it is a repeatable procedure;
- validator/test when the recurrence is mechanically detectable;
- hook/CI gate when prevention belongs at commit/push/integration time;
- work ledger when continuity/ownership is the recurring defect;
- code when deterministic behavior, not prose, is missing.
Make the smallest useful change. Prefer an executable regression over prose alone when the behavior is machine-checkable.
When a generated artifact or website derives from the changed authority, rebuild it through the canonical producer instead of hand-editing the generated copy.

7. REGRESSION SCENARIO
Add or update a focused test/validator/fixture that represents the real recurrence where practical. For an urgency/execution miss, prove at least that the durable prompt/rule requires:
- current proof floor + next gate;
- immediate critical-path movement;
- deployment/release prioritization when relevant;
- explicit Sub-Part Agent plan or serialized-dependency reason;
- no stopping at plan/status while safe action remains.
Do not weaken an existing gate to make the new rule pass.

8. VALIDATE, COMMIT, AND INTEGRATE
- Run focused tests first, then the owning registry/harness/build/parity checks, then broader checks when practical.
- Run git diff --check.
- Commit the coherent repair, push normally, and open/update/merge the PR when safe, authorized, and repository gates permit.
- Report skipped checks with exact reasons and commands.
- Do not claim a higher proof level than actually observed.

FINAL RESPONSE
RECURRENCE
- repeated problem:
- evidence it repeated:
- failure class(es):
CRITICAL PATH
- current proof/stage floor:
- next unproven gate:
- deployment/release/runtime gate:
- critical-path action executed now:
SUB-PART AGENT
- launched / copy-paste packet / none — serialized dependency:
- lane, scope, dependency, artifact, validation, collision boundary, return packet:
DURABLE PREVENTION
- authority chosen:
- files changed:
- validator/test added or updated:
DELIVERY
- validation actually run:
- commit SHA:
- push / PR / merge state:
- proof achieved / proof ceiling:
- final Git state:
NEXT COMMAND
- one exact action that advances the next unproven gate.

A response that merely restates urgency, reports the already-known proof floor, proposes rules without implementing an authorized durable change, omits Sub-Part Agent analysis, or stops at a plan/status while safe critical-path work remains has failed this prompt.'''


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def dump(path: str, payload) -> None:
    (ROOT / path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main() -> None:
    overrides = load('registry/prompts/prompt-overrides.v1.json')
    if overrides.get('schema_version') != 'prompt-registry-overrides/v1':
        raise SystemExit('unexpected prompt override schema')
    base_prompts = load('docs/prompts.json')
    base_p13 = next(item for item in base_prompts if item.get('id') == 'P13')
    p13 = dict(base_p13)
    p13.update({
        'name': 'Repeated Friction → Urgency Recovery + Rule Repair',
        'type': 'IMPROVE',
        'class': 'IMPROVE / RULES + EXECUTION',
        'sprintRole': 'Turn recurring pain, urgency misses, proof-floor loops, and missing parallelism into immediate critical-path progress plus durable prevention',
        'progress': 'YES',
        'useWhen': 'A mistake, explanation, setup problem, execution stall, urgency complaint, proof-floor loop, deployment delay, or missing Sub-Part Agent/parallel lane repeats and the operator should not have to type the correction again.',
        'inspectFirst': 'Current conversation and repeated operator corrections; current proof/stage floor; deployment/release/runtime gate; work ledger; AGENTS.md and scoped rules; prompt/workflow/skill/validator owners; open PRs and CI; recent commits; current branch/worktree; artifacts and blockers.',
        'expectedOutput': 'Immediate advancement of the current critical path, an explicit Sub-Part Agent launch/packet or serialized-dependency reason, and the smallest implemented durable rule/prompt/validator/workflow/ledger change that prevents the repeated failure.',
        'nextStep': 'Continue the primary critical path through the next unproven gate while any safe Sub-Part Agent lane runs independently; do not fall back to the already-established proof floor or stop at status/planning.',
        'proofGate': 'The recurrence is evidence-backed; current proof floor and next gate are explicit; one critical-path action advances now or an exact external blocker is proven; Sub-Part Agent analysis is present; the prevention change is owned by one correct authority; and focused regression/build/parity validation passes without proof inflation.',
        'color': 'Lavender',
        'copySheet': 'P13_COPY_SAFE',
        'category': 'standard',
        'copyContent': P13_CONTENT,
        'keywords': [
            'improve rules', 'self improving', 'repeated pain', 'lesson learned',
            'rule change', 'validator change', 'hook change', 'urgency',
            'urgency not met', 'deployment held up', 'move past r1',
            'proof floor loop', 'stalled execution', 'no progress',
            'sub-part agent', 'subpart agent', 'parallelize',
            'missing parallelism', 'repeating myself', 'critical path'
        ],
    })
    overrides['overrides'] = [item for item in overrides['overrides'] if item.get('id') != 'P13'] + [p13]
    dump('registry/prompts/prompt-overrides.v1.json', overrides)

    reference = load('docs/reference.json')
    seq = [item for item in reference['promptSequence'] if item.get('promptId') == 'P13']
    if len(seq) != 1:
        raise SystemExit('expected one P13 promptSequence entry')
    seq[0].update({
        'moment': 'Repeated Friction → Urgency Recovery + Durable Rule Repair',
        'useItFor': 'A mistake, stall, urgency miss, proof-floor loop, deployment delay, repeated explanation, or missing parallel lane has happened again.',
        'doNotUseWhen': 'The issue is a one-off failure and another executor already owns the next safe action.',
        'produces': 'Immediate critical-path movement, explicit Sub-Part Agent launch/packet or serialized-dependency reason, and the smallest durable prevention change.',
        'gate': 'The known proof floor is not recycled as completion; the next real gate advances or an exact blocker is proven; recurrence receives an enforceable prevention path.',
        'then': 'Continue the owning executor, integration, deployment, or runtime lane through the next unproven gate.',
        'mutatesRepo': 'YES',
        'authority': 'Bounded prompt/rule/validator/workflow/ledger repair plus current safe critical-path action',
        'proofCeiling': 'Only the executed action and validated durable prevention are proven; deployment/runtime/merge proof remains separate unless actually observed.',
    })
    legend = [item for item in reference['classLegend'] if item.get('promptIds') == 'P13']
    if len(legend) != 1:
        raise SystemExit('expected one P13 classLegend entry')
    legend[0].update({
        'promptType': 'IMPROVE',
        'promptClass': 'IMPROVE / RULES + EXECUTION',
        'whenToUse': 'Repeated friction, urgency miss, proof-floor loop, deployment delay, or missing parallelism',
        'progressUse': 'YES',
        'proofGate': 'Critical path advances and recurrence gains durable prevention',
        'fillRole': 'Urgency recovery + learning',
        'meaning': 'Turn repeated operator correction into immediate next-gate progress, explicit Sub-Part Agent analysis, and one owned enforceable prevention change.',
    })
    dump('docs/reference.json', reference)

    order = load('registry/prompts/prompt-display-order.v1.json')
    ids = [item for item in order['promoted_prompt_ids'] if item != 'P13']
    insert_at = ids.index('P66') + 1 if 'P66' in ids else min(4, len(ids))
    ids.insert(insert_at, 'P13')
    order['promoted_prompt_ids'] = ids
    order['rationale'] = 'Promote guided entry, repository intake, durable work-ledger continuity, repeated-friction/urgency recovery, common execution, diagnosis, validation, closeout, planning, and tutorial discovery without renumbering stable prompt identities. All unlisted prompts retain numeric sequence order.'
    dump('registry/prompts/prompt-display-order.v1.json', order)

    builder_path = ROOT / 'build_prompt_kit.py'
    builder = builder_path.read_text(encoding='utf-8')
    old = '    "rules": "P13", "improve rules": "P13", "self improving": "P13",\n'
    new = (
        '    "rules": "P13", "improve rules": "P13", "self improving": "P13",\n'
        '    "urgency": "P13", "urgency not met": "P13", "deployment held up": "P13",\n'
        '    "move past r1": "P13", "proof floor loop": "P13", "stalled execution": "P13",\n'
        '    "sub-part agent": "P13", "subpart agent": "P13", "missing parallelism": "P13",\n'
        '    "repeating myself": "P13", "critical path": "P13",\n'
    )
    if old not in builder:
        raise SystemExit('P13 synonym anchor not found')
    builder_path.write_text(builder.replace(old, new, 1), encoding='utf-8')

    guided_path = ROOT / 'docs/prompt-kit-guided-recommendations.js'
    guided = guided_path.read_text(encoding='utf-8')
    old = "  {id:'known-task',label:'Yes — the task and desired change are already known',queries:['implement','sprint','code change']},\n  {id:'not-yet',label:'Not yet — I need to discover or plan first',queries:['discovery','plan','opportunity']}"
    new = "  {id:'known-task',label:'Yes — the task and desired change are already known',queries:['implement','sprint','code change']},\n  {id:'repeated-stall',label:'Yes — the work keeps stalling, urgency is being missed, or I keep repeating the same correction',queries:['urgency','repeated pain','sub-part agent','stalled execution']},\n  {id:'not-yet',label:'Not yet — I need to discover or plan first',queries:['discovery','plan','opportunity']}"
    if old not in guided:
        raise SystemExit('guided recommendation anchor not found')
    guided_path.write_text(guided.replace(old, new, 1), encoding='utf-8')

    test_path = ROOT / 'tests/test_skill_prompt_registry.py'
    tests = test_path.read_text(encoding='utf-8')
    old = '''        self.assertEqual(len(payload["overrides"]), 1)\n        override = payload["overrides"][0]\n        self.assertEqual((override["id"], override["seq"]), ("P02", "02"))\n        self.assertEqual(override["copySheet"], "P02_COPY_SAFE")\n        source_p02 = next(\n            item\n            for item in json.loads(build_prompt_kit_registry.BASE_REGISTRY.read_text(encoding="utf-8"))\n            if item["id"] == "P02"\n        )\n        self.assertEqual(source_p02["seq"], override["seq"])\n'''
    new = '''        self.assertEqual(len(payload["overrides"]), 2)\n        by_id = {item["id"]: item for item in payload["overrides"]}\n        self.assertEqual(set(by_id), {"P02", "P13"})\n        self.assertEqual((by_id["P02"]["id"], by_id["P02"]["seq"]), ("P02", "02"))\n        self.assertEqual(by_id["P02"]["copySheet"], "P02_COPY_SAFE")\n        self.assertEqual((by_id["P13"]["id"], by_id["P13"]["seq"]), ("P13", "13"))\n        self.assertEqual(by_id["P13"]["copySheet"], "P13_COPY_SAFE")\n        source_by_id = {\n            item["id"]: item\n            for item in json.loads(build_prompt_kit_registry.BASE_REGISTRY.read_text(encoding="utf-8"))\n        }\n        self.assertEqual(source_by_id["P02"]["seq"], by_id["P02"]["seq"])\n        self.assertEqual(source_by_id["P13"]["seq"], by_id["P13"]["seq"])\n'''
    if old not in tests:
        raise SystemExit('override test anchor not found')
    tests = tests.replace(old, new, 1)
    marker = '    def test_prompt_override_registry_is_explicit_and_identity_preserving(self) -> None:\n'
    p13_test = '''    def test_p13_recurring_urgency_recovery_advances_and_parallelizes(self) -> None:\n        prompt = {\n            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()\n        }["P13"]\n        content = prompt["copyContent"]\n\n        self.assertEqual(prompt["name"], "Repeated Friction → Urgency Recovery + Rule Repair")\n        self.assertEqual(prompt["class"], "IMPROVE / RULES + EXECUTION")\n        self.assertEqual(prompt["progress"], "YES")\n        for phrase in (\n            "THE SAME PROBLEM HAS REPEATED",\n            "We need to move past R1",\n            "Deployment has held up",\n            "A plan for a Sub-Part Agent was not in your output",\n            "ESTABLISH THE CURRENT CRITICAL PATH",\n            "current proven floor or stage",\n            "next unproven gate",\n            "EXECUTE ONE CRITICAL-PATH ADVANCEMENT NOW",\n            "SUB-PART AGENT PLAN IS MANDATORY",\n            "Sub-Part Agent: none — serialized dependency",\n            "Never use a Sub-Part Agent plan as an excuse to stop the primary critical path",\n            "INSTALL THE SMALLEST DURABLE PREVENTION",\n            "REGRESSION SCENARIO",\n            "no stopping at plan/status while safe action remains",\n        ):\n            self.assertIn(phrase, content)\n\n        self.assertEqual(build_prompt_kit_registry.build_prompt_kit.SYNONYMS["urgency"], "P13")\n        self.assertEqual(build_prompt_kit_registry.build_prompt_kit.SYNONYMS["sub-part agent"], "P13")\n        self.assertEqual(prompt["discoveryGroup"], "promoted")\n\n        reference = json.loads(build_prompt_kit_registry.REFERENCE.read_text(encoding="utf-8"))\n        sequence = next(item for item in reference["promptSequence"] if item["promptId"] == "P13")\n        legend = next(item for item in reference["classLegend"] if item["promptIds"] == "P13")\n        self.assertIn("Urgency Recovery", sequence["moment"])\n        self.assertIn("Sub-Part Agent", sequence["produces"])\n        self.assertEqual(sequence["mutatesRepo"], "YES")\n        self.assertEqual(legend["promptClass"], "IMPROVE / RULES + EXECUTION")\n\n        guided = build_prompt_kit_registry.GUIDED_RECOMMENDATIONS.read_text(encoding="utf-8")\n        self.assertIn("id:'repeated-stall'", guided)\n        self.assertIn("work keeps stalling, urgency is being missed", guided)\n        self.assertIn("'sub-part agent'", guided)\n\n'''
    if marker not in tests:
        raise SystemExit('P13 test insertion anchor not found')
    test_path.write_text(tests.replace(marker, p13_test + marker, 1), encoding='utf-8')


if __name__ == '__main__':
    main()
