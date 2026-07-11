# App, Agent, Skills, and Sprint Floor Map

## Purpose

Treat `web-excel-repair-triage` as a fully fledged spreadsheet application and harness, not as a loose collection of workbook scripts.

This document maps:

- the application surfaces,
- the shared agent contract,
- conditional skills that should be loaded only when relevant,
- current PR ownership and collision risk,
- safe bases for upcoming sprints,
- and the evidence boundaries between package checks, Web Excel acceptance, and operator acceptance.

This is coordinator documentation. It does not implement new workbook behavior, repair logic, or runtime acceptance.

## Inspection snapshot

- Repository: `EndeavorEverlasting/web-excel-repair-triage`
- Default branch: `main`
- Inspected `main` head: `3d18817f89232306cc2e7e00ed7354c43c5c1afb`
- Main head subject: `docs(web-excel): expand package-shape stop-ship rules`
- Local checkout/worktree: unavailable in the connector environment
- Local dirty/conflict state: unknown
- Local worktrees: unknown
- Safe default base for isolated new work: current `origin/main`
- Open PRs inspected: #53, #52, #51, #50, #49, #48, #46, #45, #40, #34

Before local work, run:

```bash
git fetch origin
git status --short
git branch --show-current
git log --oneline --decorate -8
git worktree list
gh pr list --state open --limit 20
```

## Application posture

The repo has five connected application layers.

### 1. Workbook forensics and repair core

Responsibilities:

- inspect raw OOXML ZIP/XML,
- classify repair signatures,
- compare original versus repaired packages,
- generate byte-safe patch recipes,
- avoid accidental XML reserialization,
- and expose package evidence.

Representative surfaces:

```text
triage/gate_checks.py
triage/web_excel_compatibility_rules.py
triage/workbook_package_hygiene.py
triage/artifact_compare.py
triage/same_family_compare.py
```

### 2. Artifact-generation engines

Responsibilities:

- convert operator inputs into clean workbook outputs,
- preserve source authority and directionality,
- produce delivery workbooks plus sidecars,
- and enforce per-artifact contracts.

Representative engines:

```text
triage/admin_billing_summary/
triage/nw_prj_neuron_track_hours/
triage/nw_prj_admin_log/
triage/one_marcus_recon/
triage/cybernet_targets/
triage/billing_context/
```

### 3. Artifact lifecycle and safety harness

Responsibilities:

- keep operator sources immutable,
- route generated files to `Outputs/`,
- prevent private workbook leakage,
- fingerprint source and delivery artifacts,
- and separate candidate, active, deprecated, repaired, and output states.

Representative surfaces:

```text
triage/output_policy.py
triage/gitignore_hygiene.py
triage/artifact_fingerprint.py
configs/artifact_profiles/
Candidates/
Active/
Deprecated/
Repaired/
Outputs/
```

### 4. Acceptance and validation harness

Responsibilities:

- distinguish package validity from semantic correctness,
- distinguish presentation quality from browser acceptance,
- preserve operator acceptance as the field judge,
- and prevent package-only evidence from being promoted into unsupported claims.

Current acceptance ladder:

```text
package validity
-> semantic correctness
-> presentation quality
-> copy-surface safety where applicable
-> clipboard acceptance where applicable
-> Excel for Web acceptance
-> operator acceptance
```

### 5. Operator and agent interfaces

Responsibilities:

- browser/Streamlit workflows,
- CLI entry points,
- MCP tools,
- AI-agent instructions,
- targeted repo-navigation guidance,
- and later AI-harness orchestration.

Representative surfaces:

```text
README.md
AGENTS.md
app.py or Streamlit entry points
mcp_server.py or MCP tool modules
CLI modules under triage/
docs/*RUNBOOK*.md
docs/*CONTRACT*.md
```

## Current agent-instruction problem

`AGENTS.md` currently contains valuable rules, but it is biased toward billing-direction workflows. It includes:

- Roster Log to Admin Sheet,
- Roster Log to Task Tracker,
- Task Tracker to Roster Log,
- Friday reporting batches,
- resolved worked-project precedence,
- and operator-source immutability.

Those rules are correct within their domains. The problem is placement.

The repository now includes multiple unrelated or conditionally related domains:

- raw OOXML repair forensics,
- Web Excel package validation,
- artifact comparison,
- billing/admin workbook generation,
- Neuron tracking,
- inventory reconciliation,
- output lifecycle policy,
- prompt-kit clipboard surfaces,
- MCP/local-agent tooling,
- and Streamlit/browser operation.

Loading all conditional domain rules into every agent session increases token cost and can cause billing-specific logic to bleed into unrelated validator or repair work.

## Recommended agent architecture

### Root `AGENTS.md`: common denominators only

The root agent file should be short enough to read on every session. It should contain only repo-wide invariants.

Recommended common denominator content:

1. **Repo identity**
   - Spreadsheet generation, repair, comparison, and Web Excel compatibility harness.
2. **Evidence ladder**
   - Never equate package validation with Web Excel or operator acceptance.
3. **Source immutability**
   - `Candidates/` and `Active/` are read-only.
4. **Output posture**
   - Generated work goes under `Outputs/` or an approved artifact directory.
5. **Privacy posture**
   - No private workbooks, credentials, client data, or live output artifacts in commits.
6. **Repair posture**
   - Prefer byte-safe/package-aware inspection; do not casually reserialize XML.
7. **Repo sprint discipline**
   - Inspect patterns first, keep changes bounded, validate, commit, and report exact evidence.
8. **Skill routing rule**
   - Load the relevant skill before touching a conditional workflow.
9. **Parallel ownership rule**
   - One branch/worktree per lane; do not stack on unrelated open PR branches.
10. **Operator field-judge rule**
    - Human target-environment acceptance remains authoritative.

### Targeted skills: conditional brush-up

Recommended neutral layout:

```text
.ai/
  skills/
    workbook-package-forensics/
      SKILL.md
    web-excel-compatibility/
      SKILL.md
    artifact-generation/
      SKILL.md
    billing-directionality/
      SKILL.md
    roster-resolution/
      SKILL.md
    output-immutability/
      SKILL.md
    artifact-acceptance/
      SKILL.md
    workbook-visual-system/
      SKILL.md
    prompt-kit-copy-surfaces/
      SKILL.md
    mcp-readonly-tools/
      SKILL.md
    pr-worktree-hygiene/
      SKILL.md
```

The directory name is intentionally tool-neutral. Claude-specific or agent-specific mirrors can be added later if needed.

## Proposed skill contracts

### `workbook-package-forensics`

Load when:

- inspecting an `.xlsx` repair banner,
- comparing original/repaired packages,
- editing ZIP/XML gate logic,
- or generating patch recipes.

Key sources:

```text
README.md
triage/gate_checks.py
triage/workbook_package_hygiene.py
triage/artifact_compare.py
docs/*REPAIR*
docs/*OOXML*
```

Hard rules:

- read-only diagnosis by default,
- no XML reserialization in a diagnostic lane,
- report exact package parts and evidence,
- do not claim browser acceptance.

### `web-excel-compatibility`

Load when:

- changing stop-ship rules,
- `.rels` relationship validation,
- calc-chain/shared-formula/table checks,
- or browser compatibility gates.

Key sources:

```text
triage/web_excel_compatibility_rules.py
triage/gate_checks.py
triage/webexcel_preflight.py
tests/test_web_excel_compatibility_rules.py
docs/WEB_EXCEL_COMPATIBILITY_RULES.md
```

Hard rules:

- package checks are not Web Excel acceptance,
- actual browser/operator evidence must be named separately,
- preserve existing gates when adding a bounded new rule.

### `artifact-generation`

Load when:

- adding or changing an output workbook engine,
- building manifests/sidecars,
- or changing delivery layout.

Key sources:

```text
triage/*/cli.py
triage/output_policy.py
configs/artifact_profiles/
docs/*CONTRACT*.md
```

Hard rules:

- explicit input authority,
- explicit output directory,
- source fingerprinting,
- sanitized fixture tests,
- generated outputs are not committed by default.

### `billing-directionality`

Load when:

- roster/admin/task-tracker workflows are in scope.

Move the current directional contract from global-only posture into this skill, while keeping one root pointer.

Key rules:

- Roster Log to Admin Sheet is high-priority submission flow.
- Roster Log to Task Tracker is internal contextualization.
- Task Tracker to Roster Log is reviewed proposal-only backfill.
- Friday is the reporting batch marker.
- Admin outputs must not leak internal exception machinery.

### `roster-resolution`

Load when:

- resolving worked project, overrides, assignments, lunch, overnight, or multi-project days.

Key sources:

```text
triage/admin_billing_summary/reader.py
docs/ACTIVE_ROSTER_LOG_MECHANICS.md
docs/BILLING_WORK_CONTEXT_RULES.md
```

Hard rules:

- overrides beat defaults,
- resolved worked-project logic beats raw assumption,
- contradictions route to review,
- no silent mutation of roster authority.

### `output-immutability`

Load when:

- any command writes a workbook, report, sidecar, or delivery package.

Key sources:

```text
triage/output_policy.py
triage/gitignore_hygiene.py
docs/OPERATOR_SOURCE_IMMUTABILITY.md
docs/ONE_MARCUS_SOURCE_OVERWRITE_INCIDENT_2026_06_04.md
```

Hard rules:

- never overwrite `Candidates/` or `Active/`,
- never set output equal to input,
- use dated run directories,
- preserve source SHA in manifests.

### `artifact-acceptance`

Load when:

- writing completion language,
- promoting a candidate artifact,
- or validating delivery readiness.

Hard rules:

- package-valid, correct, presentation-safe, Web Excel accepted, and operator accepted are distinct,
- clipboard acceptance is separate for prompt/runbook workbooks,
- skipped gates must be named.

### `workbook-visual-system`

Load when:

- styling workbooks,
- changing tab colors,
- freeze panes,
- executive layouts,
- or conditional-format presentation.

Key sources:

```text
configs/spreadsheet_style_v1.json
configs/workbook_visual_design_v1.json
docs/SPREADSHEET_STYLE_SYSTEM.md
docs/WORKBOOK_VISUAL_DESIGN_SYSTEM.md
```

Hard rules:

- semantic color only,
- style passes must not rewrite formulas or table mechanics,
- validate package metadata after visible layout changes.

### `prompt-kit-copy-surfaces`

Load when:

- generating workbook-based prompt libraries or operator copy surfaces.

Key sources after PR #51:

```text
docs/WORKBOOK_COPY_SURFACE_AND_OOXML_TRIAGE_LESSONS.md
docs/AI_PROMPT_KIT_V10_XML_AND_CLIPBOARD_RECORD.md
triage/workbook_package_hygiene.py
```

Hard rules:

- index/catalog sheets are not execution surfaces,
- paste-only sheets contain only the intended payload,
- one prompt line per row is preferred,
- giant multiline cells are clipboard-risk surfaces,
- package shape cannot prove proprietary clipboard output.

### `mcp-readonly-tools`

Load when:

- exposing repo/package inspection through MCP,
- or adding local-agent code intelligence.

Hard rules:

- read-only by default,
- JSON-serializable results,
- no private artifact scanning by default,
- no hidden network or mutation behavior,
- tool result must state proof level.

### `pr-worktree-hygiene`

Load when:

- coordinating branches, PRs, worktrees, merge order, and collision risk.

Hard rules:

- use `origin/main` for independent new lanes,
- continue a PR branch only when explicitly owning that PR,
- do not use non-mergeable product branches as new bases,
- do not delete branches without merged proof,
- local worktree state must be checked before destructive cleanup.

## Proposed agent routing table

| Task signal | Load skill(s) | Do not load by default |
| --- | --- | --- |
| repair banner, corrupt workbook, repaired export | workbook-package-forensics, artifact-acceptance | billing-directionality |
| `.rels`, calcChain, table refs, shared formula | web-excel-compatibility, workbook-package-forensics | roster-resolution |
| generate admin billing workbook | artifact-generation, billing-directionality, roster-resolution, output-immutability, artifact-acceptance | prompt-kit-copy-surfaces |
| generate inventory recon | artifact-generation, output-immutability, workbook-visual-system, artifact-acceptance | billing-directionality |
| style-only pass | workbook-visual-system, workbook-package-forensics | roster-resolution |
| prompt library workbook | prompt-kit-copy-surfaces, workbook-visual-system, artifact-acceptance | billing-directionality |
| MCP tool | mcp-readonly-tools plus the domain skill for the tool | unrelated generator skills |
| PR floor cleanup | pr-worktree-hygiene | artifact-generation unless a PR specifically owns it |

## Current PR map

| PR | Branch/lane | Posture | Collision/landing note |
| --- | --- | --- | --- |
| #53 | relationship-target validator | Mergeable, focused `.rels` audit | Overlaps conceptually with #51 package hygiene. Decide ownership before broadening either. |
| #52 | open PR floor map | Mergeable docs-only coordinator lane | Existing floor map; refresh after #51/#53 disposition. |
| #51 | package hygiene + clipboard record | Mergeable executable validator/docs lane | Owns broad package hygiene, prompt-kit package shape, focused CI job. |
| #50 | admin-log product generator | Mergeable product lane | Depends conceptually on #46 output policy and #49 style contract. Not a floor base. |
| #49 | admin-log style contract | Mergeable docs lane | Land before or with #50 if still canonical. |
| #48 | Bonita repair-free profile gate | Mergeable validator/product lane | Needs operator-local golden reference and manual Excel acceptance. |
| #46 | output immutability policy | Mergeable floor/policy lane | High-value shared dependency; inspect for landing after validator overlap is resolved. |
| #45 | candidate Neuron generator | Not mergeable | Do not stack. Rebase or supersede. |
| #40 | client-coordination doctrine | Mergeable older docs lane | Merge if canonical; otherwise close with replacement citation. |
| #34 | bundled April/May engines | Not mergeable | Avoid as base. Split or supersede. |

## Worktree map

Connector-visible facts:

- No local worktree is mounted in this environment.
- Dirty/conflicted local state is unknown.
- Sibling worktrees cannot be verified remotely.

Required local decision:

```bash
git status --short
git branch --show-current
git worktree list
```

Safe posture:

- if the primary tree is clean and on `main`, new independent docs/skills work can use a sibling worktree from `origin/main`,
- if the primary tree is dirty, do not reuse it for a separate lane,
- continue PR #51/#52/#53 only in worktrees attached to their existing branches.

## Safe sprint bases

| Next sprint | Safe base | Parallel posture |
| --- | --- | --- |
| root `AGENTS.md` minimization | `origin/main` after docs map review | Separate from product/validator PRs; likely conflicts only in `AGENTS.md`. |
| create `.ai/skills/` skeleton | same branch as AGENTS minimization or a follow-up from main | Do not split AGENTS pointers and skill files across unrelated branches unless coordinated. |
| PR #51 closeout | PR #51 branch | Not parallel with another branch editing package-hygiene docs/workflow. |
| PR #53 closeout | PR #53 branch | Safe in parallel with AGENTS/skills docs; coordinate validator overlap with #51. |
| output policy closeout | PR #46 branch | Safe in parallel with agent docs if no `AGENTS.md` edits. |
| product generator work | new branch from updated main after dependencies land | One product engine per branch/worktree. |
| clipboard acceptance skill | origin/main after #51 lands | Depends on #51 docs becoming canonical. |
| MCP/local-agent skill | origin/main | Safe as docs/design lane; runtime MCP changes require separate implementation sprint. |

## Recommended sprint sequence

### Wave 0: floor and overlap

1. Close or merge PR #51 with its dedicated package-hygiene CI proof.
2. Resolve conceptual overlap between #51 and #53.
3. Refresh or merge PR #52 floor map.
4. Inspect #46 as the shared output-policy floor.

### Wave 1: agent harness foundation

1. Reduce root `AGENTS.md` to common denominators.
2. Add `.ai/skills/` with the first five high-value skills:
   - workbook-package-forensics,
   - web-excel-compatibility,
   - artifact-generation,
   - output-immutability,
   - artifact-acceptance.
3. Move billing-specific detail into billing-directionality and roster-resolution skills.
4. Add a short skill routing table to root `AGENTS.md`.
5. Add a validator that ensures required skill files and root pointers exist.

### Wave 2: product-aligned skills

1. workbook-visual-system,
2. prompt-kit-copy-surfaces,
3. mcp-readonly-tools,
4. pr-worktree-hygiene,
5. engine-local skills only when recurring complexity justifies them.

## Validation expectations for the future agent-harness sprint

The agent-harness implementation sprint should prove:

1. `AGENTS.md` is materially shorter than the current file.
2. Root invariants remain visible without loading a skill.
3. Billing directionality is preserved in a targeted skill.
4. Source immutability remains globally discoverable.
5. Each skill names triggers, read-first files, forbidden scope, validation, and evidence language.
6. Skills do not duplicate entire docs; they route agents to canonical sources.
7. A simple static validator checks required skill files and links.
8. No runtime, workbook generation, or acceptance claim is made from docs alone.

## Risks and gaps

- `AGENTS.md` is currently useful but over-specialized for a repo-wide entry point.
- No repository-local `SKILL.md` layer was found during connector searches; local untracked files remain unknown.
- README is comprehensive but too large to serve as an agent bootstrap document.
- Many domain contracts are scattered across `docs/`, increasing discovery cost.
- PR #51 and #53 overlap around package validation and can create duplicate gate logic.
- PR #52 may become stale as soon as PRs land or change scope.
- Non-mergeable PRs #45 and #34 are unsafe bases.
- Local dirty state and worktree inventory cannot be verified through the connector.
- A skills system must point to canonical docs rather than fork policy into multiple conflicting copies.

## Coordinator decision

The repo is mature enough to justify a formal agent-skill harness.

The right posture is not to add more instructions to the root file. It is:

```text
lean root invariants
+ explicit skill routing
+ targeted conditional skills
+ static harness validation
+ existing canonical docs/contracts
```

That architecture preserves fast startup, lowers token cost, and keeps specialized workflows from contaminating unrelated agent sessions.
