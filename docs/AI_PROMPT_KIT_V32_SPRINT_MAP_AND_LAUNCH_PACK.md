# AI Prompt Kit V32 Sprint Map and Launch Pack

## LAUNCH ORDER

One prompt panel goes into one new chat.

1. **Prompt 1 — Land the Prompt-Kit Contract Floor**
2. **Dependency Gate A — PR #57 prompt-kit generator and the V32 operability contract are available on one integration branch**
3. **Parallel Group A**
   - **Prompt 2 — Migrate the Generator to the Working V32 Package Lineage**
   - **Prompt 3 — Prove Desktop Excel and Excel for Web Operator Behavior**
   - **Prompt 4 — Integrate Atomic GNHF Launch Routing with AgentSwitchboard**
4. **Dependency Gate B — Generator, field acceptance, and routing evidence agree on prompt IDs, copy ranges, protection, and command ownership**
5. **Prompt 5 — Converge and Release the Next Canonical Prompt Kit**

## COMPACT COORDINATION PREAMBLE

Mission: converge the working V32 workbook behavior with repository-owned generation, validation, field acceptance, and agent routing. Repo: `EndeavorEverlasting/web-excel-repair-triage`; prompt-kit work is currently stacked on open PR #57. The verified working artifact is V32, while PR #57 currently reproduces V21. Prompt 1 establishes the reusable contract floor. After Gate A, generator migration, field acceptance, and AgentSwitchboard routing may proceed in parallel because they own different surfaces. Collision risks are prompt-kit generator files, shared contract validators, workbook package topology, and prompt registry metadata. Static package proof must not be promoted to PowerShell, GNHF, Desktop Excel, Excel for Web, or operator acceptance.

### Prompt 1 — Land the Prompt-Kit Contract Floor

```text
EXECUTE THE REPO SPRINT. DO NOT STOP AT A PLAN.

Repo: EndeavorEverlasting/web-excel-repair-triage
Branch base: feat/prompt-kit-v21-consolidator
PR dependency: #57
Wave: 0
Lane: prompt-kit operability contract

Mission:
Land the read-only V32+ operability validator, tests, workflow routing, contract documentation, and milestone insight record without committing a private workbook binary.

Owned scope:
- triage/prompt_kit_operability_contract.py
- tests/test_prompt_kit_operability_contract.py
- docs/AI_PROMPT_KIT_OPERABILITY_AND_GNHF_CONTRACT.md
- docs/insights/ai-prompt-kit-v32-milestone-2026-07-15.md
- prompt-kit CI workflow

Forbidden scope:
- changing the V21 generator payload
- committing generated workbooks
- claiming PowerShell, GNHF, Desktop Excel, or Excel for Web runtime proof
- merging PR #57

Read first:
- AGENTS.md
- docs/WEB_EXCEL_COMPATIBILITY_STOP_SHIP_RULES.md when present
- triage/prompt_kit_common.py
- triage/prompt_kit_contract.py
- tests/_prompt_kit_fixture.py
- .github/workflows/prompt-kit-v21.yml

Tasks:
1. Confirm the exact PR #57 head.
2. Add the operability validator and synthetic fixture tests.
3. Validate the authoritative local V32 workbook when available without committing it.
4. Add the CLI to prompt-kit CI.
5. Document the execution-surface, package-lineage, navigation, protection, font, palette, and proof contracts.
6. Commit and push a stacked branch.
7. Open a PR based on `feat/prompt-kit-v21-consolidator`.

Validation order:
1. python -m py_compile triage/prompt_kit_operability_contract.py tests/test_prompt_kit_operability_contract.py
2. python -m pytest tests/test_prompt_kit_operability_contract.py -q
3. python -m triage.prompt_kit_operability_contract --help
4. existing prompt-kit contract suite

Proof ceiling:
Static OOXML and command-shape proof only.

Final response:
Report branch, commit, PR, files, commands, results, skipped field checks, and one next command.
```

### Prompt 2 — Migrate the Generator to the Working V32 Package Lineage

```text
EXECUTE THE REPO SPRINT. DO NOT STOP AT A PLAN.

Repo: EndeavorEverlasting/web-excel-repair-triage
Wave: A
Lane: package-preserving generator migration
Dependencies: Prompt 1 complete; PR #57 generator available
Safe parallel work: field acceptance and AgentSwitchboard routing

Mission:
Teach the repository generator to start from the last working prompt-kit package lineage and produce the current P00-P36 structure without replaying broken package branches.

Owned scope:
- prompt-kit generator and payload source
- prompt registry and opportunity graph generation
- package-preserving hyperlink, protection, style, and palette edits
- deterministic manifest and validator integration
- generator tests and workflow

Forbidden scope:
- blank-workbook reconstruction
- serializer round-trip as the canonical path
- private workbook commit
- field-acceptance claim
- AgentSwitchboard routing logic

Expected artifacts:
- deterministic generated workbook under ignored output
- manifest and package delta
- operability report
- updated generation record

Tasks:
1. Recover exact V32 package and registry truth from the operator artifact.
2. Define the authoritative source package hash and lineage.
3. Apply bounded OOXML changes to generate the next candidate.
4. Enforce P00-P36 links, protection, fonts, palette, and atomic GNHF commands.
5. Run package hygiene, operability, repair-regression, and structural tests.
6. Commit generator code, tests, docs, and workflow only.

Proof ceiling:
Deterministic local generation and static package proof.

Final response:
Report source authority, output hash, package delta, tests, commit, PR state, and exact field-acceptance handoff.
```

### Prompt 3 — Prove Desktop Excel and Excel for Web Operator Behavior

```text
EXECUTE THE VALIDATION SPRINT. DO NOT MUTATE GENERATOR CODE.

Repo: EndeavorEverlasting/web-excel-repair-triage
Wave: A
Lane: field acceptance
Dependencies: Prompt 1 complete; candidate workbook available
Safe parallel work: generator migration and AgentSwitchboard routing

Mission:
Produce evidence for protected-sheet navigation, exact-range selection, clipboard fidelity, workbook open behavior, and the Opportunity Discovery edit boundary in Desktop Excel and Excel for Web.

Owned scope:
- operator runbook
- sanitized acceptance record
- screenshots or logs stored outside Git unless explicitly sanitized
- machine-readable acceptance summary

Forbidden scope:
- repairing the workbook during the acceptance run
- saving a repaired workbook over the candidate
- claiming browser acceptance from local OOXML checks
- embedding private workbook data in the repo

Tasks:
1. Verify package hash before testing.
2. Open in Desktop Excel without repair.
3. Test left/right Prompt Library navigation.
4. Test Prompt ID exact-range selection and clipboard output.
5. Test top and bottom backlinks on representative prompt tabs.
6. Verify protected sheets and the Opportunity Discovery input range.
7. Repeat in Excel for Web and record repair/banner behavior.
8. Produce PASS, FAIL, BLOCKED, or NOT_RUN evidence per check.

Proof ceiling:
Field behavior for the exact tested artifact and environment only.

Final response:
Report artifact hash, environment, matrix, evidence paths, failures, and promotion recommendation.
```

### Prompt 4 — Integrate Atomic GNHF Launch Routing with AgentSwitchboard

```text
EXECUTE THE REPO SPRINT. DO NOT STOP AT A PLAN.

Repo: EndeavorEverlasting/AgentSwitchboard
Wave: A
Lane: GNHF launch routing and provider failover integration
Dependencies: Prompt 1 command contract complete
Safe parallel work: prompt-kit generator and field acceptance

Mission:
Consume the P26-P36 atomic command taxonomy as routing contracts while keeping provider and agent failover in AgentSwitchboard rather than inside repository prompts.

Owned scope:
- command manifest or registry
- route selection by lane
- preflight for available agents and provider readiness
- bounded retry/failover evidence
- logs and operator guidance
- tests with fake agents and synthetic quota failures

Forbidden scope:
- storing credentials
- claiming native GNHF agent switching
- paid-provider calls in tests
- automatic Git push
- overlapping mutation lanes in the same files

Tasks:
1. Map each P26-P36 lane to an AgentSwitchboard route.
2. Validate the command shape before launch.
3. Select an available configured agent.
4. Record switch reason, token/quota evidence, selected model, and worktree.
5. Resume or hand off without duplicating repository work.
6. Add fake-agent tests for exhaustion, permanent error, and safe fallback.

Proof ceiling:
Harness and synthetic failover proof; live provider switching remains separate.

Final response:
Report routes, tests, logs, commit, PR, skipped live calls, and exact operator command.
```

### Prompt 5 — Converge and Release the Next Canonical Prompt Kit

```text
CONVERGE THE PROMPT-KIT PROGRAM. DO NOT REIMPLEMENT PARALLEL LANES.

Repo: EndeavorEverlasting/web-excel-repair-triage
Wave: convergence
Dependencies: Prompts 2, 3, and 4 complete or explicitly blocked
Lane: integration, release evidence, and cleanup

Mission:
Converge generator output, static validators, field acceptance, registry metadata, and AgentSwitchboard routing into one canonical next-version release decision.

Owned scope:
- integration branch
- final registry and manifest
- release generation record
- acceptance matrix
- obsolete branch and documentation dispositions
- PR dependency order

Forbidden scope:
- silently overriding failed field acceptance
- accepting a generator output whose package differs from the tested artifact
- merging unreviewed remote work
- claiming live failover without evidence

Tasks:
1. Refresh every dependency branch and artifact hash.
2. Confirm generator output matches the field-tested candidate.
3. Run all static and package validators.
4. Reconcile prompt registry, links, protection, style, palette, and routing IDs.
5. Record every remaining BLOCKED or NOT_RUN gate.
6. Merge or stage PRs in dependency order when authorized.
7. Publish the exact generation and acceptance handoff.

Proof ceiling:
The minimum of generator proof, field acceptance, and routing proof.

Final response:
Report launch order completed, commits and PRs, final artifact hash, validation matrix, field evidence, blocked gates, and one exact next action.
```

## SUPPORTING SPRINT MAP

### MISSION

Create one durable prompt-kit product whose workbook package, copy surface, protection, visual semantics, terminal commands, generator, validation, and agent routing agree.

### TOPICS COVERED

| Topic | Status | Useful context | Likely repo impact |
|---|---|---|---|
| Complete workbook releases | decided | Addenda are not numbered full releases. | Generator and registry must retain P00-P36. |
| Exact copy ranges | decided | Prompt IDs select column-A payloads. | OOXML hyperlink validation. |
| Top/bottom navigation | decided | Each prompt tab and library need bidirectional navigation. | Native hyperlink generation and tests. |
| Workbook protection | decided | Only Opportunity Discovery is editable. | Style/protection validation. |
| Semantic fonts and palette | decided | Prompt ID is large; Sequence is compact; Color controls row styling. | Style contract and regression tests. |
| Atomic GNHF commands | decided | Separate complementary launch lanes with caps. | Prompt payload and AgentSwitchboard manifests. |
| Chat-to-terminal distinction | decided | Naked natural-language prompts fail in PowerShell. | Docs and command-shape validator. |
| Package lineage | decided | Start from the last working package. | Generator source authority and hash. |
| PowerShell runtime | unresolved | Static command shape passed; Windows execution not yet observed. | Runtime proof sprint. |
| Excel for Web acceptance | unresolved | Static package proof is not browser acceptance. | Field acceptance record. |
| Agent failover | partial | AgentSwitchboard should own routing; live fallback unproven. | AgentSwitchboard integration sprint. |

### DECISIONS MADE

- Product: one complete workbook, exact mouse navigation, protected non-input surfaces.
- Technical: native internal hyperlinks, package-preserving lineage, read-only OOXML validators.
- Naming: P26-P36 atomic GNHF lanes; Prompt ID remains the primary large identifier.
- Rejected: two-workbook releases, unlimited prompts, drawing-only navigation, hidden chat context assumptions, and proof inflation.

### CURRENT STATE

- Repo: `EndeavorEverlasting/web-excel-repair-triage`.
- Main head observed during harvest: `e2e57ff01a5b466869d9b06679a4500421f3c6e0`.
- Prompt-kit generator PR: #57, open and mergeable at `c10af39018de093031f586a529a27b143d2c6e5c`.
- PR #57 prompt-kit workflow passed; a broader artifact-engine workflow failed and requires separate attribution.
- Working operator artifact: V32, generated outside the repository and not committed.
- Stale context: PR #57 reproduces V21, not V32.

### FACTORING MAP

- Harness spine: run context, validation reports, artifact registry, package and operability validators.
- Skills: prompt-kit generation, field acceptance, GNHF bounded-run preparation.
- Capabilities: package inspection, exact-range link audit, protection/style audit, command-shape validation.
- Triggers: workbook version change, Prompt Library column shift, new GNHF prompt ID, field-repair report, provider exhaustion.
- Application logic: workbook generator, registry generation, AgentSwitchboard route selection.
- Integration seams: generator to validator, workbook prompt IDs to routing manifest, artifact hash to field acceptance.
- Collision ownership: prompt-kit generator files owned by the migration lane; AgentSwitchboard routing owned outside this repo.

### LINGERING WORK

- Feature: package-preserving next-version generator.
- Harness: operability validator integration and report schema.
- Agent harness: route taxonomy and failover evidence.
- Application logic: generator mutations and registry output.
- Cleanup: stale prompt-kit branch and doc disposition after convergence.
- Validation: full CI and exact artifact validation.
- Docs/reporting: runbook, generation record, field acceptance record.
- Runtime proof: PowerShell, GNHF commit, Desktop Excel, Excel for Web.
- Research/design: protected-sheet behavior differences across Excel clients.
- Parallel-safe: field acceptance and AgentSwitchboard routing after the contract floor.

### TARGETS TO INSPECT FIRST

- `AGENTS.md`
- PR #57 and `.github/workflows/prompt-kit-v21.yml`
- `triage/prompt_kit_common.py`
- `triage/prompt_kit_contract.py`
- `tests/_prompt_kit_fixture.py`
- `triage/workbook_package_hygiene.py`
- `triage/web_excel_compatibility_rules.py`
- `docs/insights/web-excel-compatibility-artifact-lessons-2026-07-01.md`
- the V32 workbook hash and generation record
- AgentSwitchboard GNHF manifest, router, logs, and fake-agent fixtures

### RISKS AND GAPS

- PR #57 is stacked on an older base and owns overlapping prompt-kit files.
- Recreating V32 from semantic content without its working OOXML lineage may regress links or protection.
- A valid ZIP, local import, or render is insufficient for Web Excel acceptance.
- PowerShell continuation backticks fail when trailing spaces are introduced.
- GNHF cannot consume unspecified ChatGPT context.
- Windows Update can interrupt a prevent-sleep run.
- Provider/model latency must be attributed from logs rather than token-counter intuition.
- Worktree-local `.gnhf/runs` evidence may not appear in the primary checkout.
