# Upstream Design + Skill-Authoring Source Research

**Repository floor:** `main@b9089975e5dd87bc710102b4d35af54e4c499709`
**Lane:** U0B — authoritative design/skill-authoring source research
**Status:** PROVEN source disposition; no donor registration performed here.

## Mission

Identify authoritative, versionable Anthropic/Claude donor surfaces for:

- skill authoring/evaluation mechanics; and
- frontend/design mechanics.

Map those mechanics to existing Prompt Kit owners without treating donor authority as local mutation authority.

## Authoritative sources

### 1. `anthropics/skills` — REGISTER candidate

Pinned repository revision inspected:

- repository: `anthropics/skills`
- commit: `34040c9c568585f6929bedeaad110ad08f079624`
- README blob: `eb54ee8b92f2d40b4b26569be0772be3c1e23156`

Anthropic's README explicitly identifies this repository as Anthropic's implementation/examples of skills for Claude. It is therefore an authoritative first-party prior-art source.

Relevant bounded resources:

| Resource | Blob | License | Disposition |
|---|---|---|---|
| `skills/skill-creator/SKILL.md` | `65b3a402dbd09b8e83f9d637c6b553875189085c` | Apache-2.0 via sibling `LICENSE.txt` `4f881c52d1f72f4cfb720e339e2d35c3058d01a9` | REGISTER candidate |
| `skills/frontend-design/SKILL.md` | `a5333457c414d20d625f307df945842c0952ecc3` | Apache-2.0 via sibling `LICENSE.txt` `f433b1a53f5b830a205fd2df78e2b34974656c7b` | REGISTER candidate |
| `skills/canvas-design/SKILL.md` | inspected as corroborating design prior art | Apache-2.0 via sibling license | REFERENCE_ONLY for this sprint |

The repository also includes source-available document skills with different licensing. U3 must therefore preserve the existing repository rule: metadata-only donor registration is acceptable, but any copy/adaptation decision requires per-resource license review. Do not infer one repository-wide Apache license for every skill.

### 2. `anthropics/claude-plugins-official` — REFERENCE_ONLY

Pinned repository revision inspected:

- repository: `anthropics/claude-plugins-official`
- commit: `c447c3207a425bc4e2a0d068435f64b0477ae981`
- `plugins/plugin-dev/skills/skill-development/SKILL.md` blob: `1cb3bd90b29d0469d25c5df9ad72741ac1e2c4cd`
- repository `LICENSE` blob: `d645695673349e3947e8e5ae42332d0ac3164cd7` (Apache-2.0)

This is authoritative first-party Claude Code plugin guidance, but its skill-development material substantially overlaps the more general `anthropics/skills/skills/skill-creator` surface and is plugin-specific. Keep it as corroborating prior art rather than a second general skill-authoring authority unless a future plugin-specific use case requires separate registration.

### 3. Agent Skills specification — REFERENCE_ONLY

At the inspected `anthropics/skills` revision, `spec/agent-skills-spec.md` delegates the canonical Agent Skills specification to `agentskills.io/specification`.

That surface is authoritative for format/spec questions, but the current external-resource intake is Git-repository oriented. Do not invent a second HTTP polling implementation merely to watch this documentation. U3 may reference it for schema interpretation while keeping `anthropics/skills` as the versionable Git donor.

## Reusable mechanics

### Skill authoring / evaluation

The first-party `skill-creator` material provides reusable mechanics that should inform existing Prompt Kit authoring/evaluation owners rather than become a new prompt authority:

1. **Intent before authoring** — recover workflow, trigger conditions, expected output, edge cases, and dependencies before writing.
2. **Trigger description is an execution boundary** — name + description determine when the skill is selected; triggering behavior deserves explicit evaluation.
3. **Progressive disclosure** — keep always-loaded metadata small; load the main skill when triggered; place detailed deterministic resources in scripts/references/assets.
4. **Reusable deterministic helpers** — repeated/reliability-sensitive operations belong in scripts rather than repeatedly regenerated prose.
5. **Evaluation loop** — draft realistic test prompts, run the skill, assess qualitative and quantitative evidence, revise, and expand the test set.
6. **Fresh-context critique** — review a draft with a fresh pass instead of treating first-pass completion as terminal.
7. **Parallel research when a safe adapter exists** — research similar skills/docs without turning the user into the scheduler.

Local ownership:

- **P79 / prompt operations:** prompt/skill identity, strengthen-before-add decisions, prior-art comparison, promotion boundaries.
- **P67 / regression-eval owners:** evaluation methodology where repository-wide AI/prompt regression infrastructure is involved.
- Existing prompt-specific semantic owners remain authoritative for their own content.

### Frontend / UX design

The first-party `frontend-design` material contributes process mechanics, not a universal local design owner:

1. **Ground the aesthetic in the real subject/audience/job** before selecting a visual direction.
2. **Plan → review against the brief → build → critique** as an explicit design loop.
3. **Avoid template defaults by evidence**, not by banning individual styles universally.
4. **Typography, layout, motion, and copy are semantic design choices**, not decorative afterthoughts.
5. **Use structural devices only when they encode information.**
6. **Spend boldness selectively; remove decoration that does not serve the brief.**
7. **Accessibility and responsive behavior are baseline quality requirements.**
8. **Screenshot/visual critique is preferred when the environment supports it.**

Current local owner map recovered from Prompt Kit routing:

- **P106 — UX Product Designer & Interaction Architect:** overall UX architecture, journeys, interaction states, responsive/accessibility behavior.
- **P108 — UX Polish & Sophistication Refiner:** typography, spacing, hierarchy, density, feedback, motion, microcopy refinement without gratuitous redesign.
- **P109 — Cross-App UX Design System & Pattern Factorer:** reusable cross-app patterns/tokens/components/accessibility conventions.
- **P110 — UX Integrity & Cross-Viewport Acceptance Guard:** browser/layout/focus/touch/responsive acceptance proof.
- **P129 — Cross-Input UX Modality & Phone-Native Interaction Architect:** keyboard/pointer/touch modality language when relevant.

Do not create a new generic `/design` Prompt Kit authority merely because Anthropic has a `frontend-design` skill.

## Source disposition

| Source | Disposition | Reason |
|---|---|---|
| `anthropics/skills` | **REGISTER** | authoritative first-party, commit-pinnable, contains both directly relevant skill-authoring and frontend-design resources |
| `anthropics/claude-plugins-official` | **REFERENCE_ONLY** | authoritative but plugin-specific and overlapping with the general skill-creator source |
| `agentskills.io/specification` | **REFERENCE_ONLY** | canonical format/spec reference, but not a reason to create a second non-Git polling system |
| `canvas-design` within `anthropics/skills` | **REFERENCE_ONLY for current mission** | useful visual-design prior art, but current local UX owner mapping is adequately served by `frontend-design`; no need to widen U3 automatically |

## U3 registration constraints

When U3 executes:

- preserve `operant-external-resource-intake` as the only donor registry;
- prefer the smallest stable `anthropics/skills` registration that exposes the needed skill metadata without copying bodies;
- retain commit-pinned URLs and per-resource identity once U1/U2A establish it;
- do not copy/adapt a skill unless that specific resource's license has been reviewed;
- route skill-authoring/evaluation impact to P79/prompt operations;
- route design impact to the current P106/P108/P109/P110/P129 owner set according to the changed mechanic;
- do not auto-author, auto-rewrite, or auto-promote local prompts from donor changes.

## Proof ceiling

PROVEN:

- first-party repository identities and exact inspected revisions;
- exact relevant resource/blob identities;
- Apache-2.0 license evidence for `skill-creator`, `frontend-design`, and `claude-plugins-official`;
- authoritative-vs-corroborating source roles;
- current local Prompt Kit UX and prompt-authoring owner map;
- REGISTER / REFERENCE_ONLY dispositions.

UNPROVEN:

- future upstream stability beyond the pinned commits;
- semantic superiority of donor guidance over local prompts;
- whether any current local prompt requires modification;
- U3 registration/runtime behavior;
- user-visible or live runtime effect.

## Next transition

U3 may register `anthropics/skills` only after U1 establishes the capability identity/event/impact contract and U2B resolves teaching-owner overlap. Registration is metadata-only prior art; promotion remains owned by existing local authorities.
