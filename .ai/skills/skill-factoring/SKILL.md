# Skill Factoring

## Trigger

Use this skill when a repository skill is oversized, overlaps another skill, owns multiple unrelated activation conditions, hides deterministic product behavior in prose, or lacks testable boundaries.

Do not use it merely to rename a healthy skill or reorganize files without a behavioral boundary problem.

## Required inputs

- Repository law and nearest scoped instructions.
- Existing skill, capability, trigger, workflow, and artifact registries.
- The in-scope skill files and their current consumers.
- Application code and schemas referenced by those skills.
- Existing validators, fixtures, open PRs, and recent failure evidence.

## Outputs

- A disposition for every inspected skill: `KEEP`, `SPLIT`, `MERGE`, `RETIRE`, or `REWIRE`.
- Factored skill files with one deterministic activation condition each.
- Updated trigger, capability, workflow, and manifest references.
- Positive, negative, and boundary fixtures.
- A validator that rejects ambiguous routing, duplicate ownership, or missing required sections.
- A committed change with explicit proof ceiling.

## Procedure

1. Record the Git floor and use an isolated branch or worktree.
2. Inventory the in-scope skills and map each to its triggers, capabilities, workflows, application modules, outputs, and validators.
3. Identify boundary defects:
   - multiple unrelated triggers;
   - duplicate ownership;
   - a single skill spanning unrelated domains;
   - deterministic behavior implemented only in prose;
   - missing inputs, outputs, preconditions, forbidden conditions, or proof ceiling;
   - routing that requires an agent to guess.
4. Assign one disposition to each skill.
5. Split only at a stable behavioral boundary. Each resulting skill must own one reusable procedure and one deterministic trigger family.
6. Merge only when activation, inputs, outputs, guardrails, and validation are materially identical.
7. Retire only after every useful procedure and consumer is preserved or deliberately superseded.
8. Move deterministic operations into code, schemas, registries, validators, or workflows. Keep judgment, sequencing, and reusable operating guidance in the skill.
9. Update routing and ownership records atomically with the skill changes.
10. Add fixtures that prove:
    - expected activation;
    - near-miss non-activation;
    - missing-precondition refusal;
    - forbidden-condition refusal;
    - no duplicate owner for the same trigger surface.
11. Run focused skill and routing validation before broader repository checks.
12. Commit the coherent factoring change and report the exact destination of retired or merged work.

## Guardrails

- Do not move application logic into prompts or skill prose.
- Do not create a second routing authority when one already exists.
- Do not retire a skill before preserving its unique useful work.
- Do not weaken triggers merely to eliminate a failing fixture.
- Do not claim runtime or model-quality proof from static validation.
- Do not modify unrelated product code, secrets, generated artifacts, or default-branch history.

## Validation

At minimum, validate:

- every active skill has Trigger, Required inputs, Outputs, Procedure, Guardrails, and Validation sections;
- every trigger resolves to one primary skill owner;
- positive, negative, and boundary fixtures pass;
- referenced capability and workflow IDs exist;
- retired skills have a preservation destination;
- `git diff --check` passes;
- the intended commit exists ahead of the recorded floor.

## Proof ceiling

Static contracts and fixtures prove discoverability, routing boundaries, ownership, and repository integration. They do not prove model judgment quality, provider behavior, or live runtime success; use the Skill Evaluation Harness prompt for those additional proof levels.
