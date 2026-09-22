# Prompt Findability + Agent Readability Sprint Map

**Status:** TRACKED PLAN  
**Repository:** EndeavorEverlasting/web-excel-repair-triage  
**Planning branch:** `plan/prompt-findability-agent-readability-20260922`  
**Planning floor:** `main@c97718247e7b14544d198035dd3cdc07725545a8`  
**Primary complaint:** fresh local agents spend too much context and too many grep/glob/search calls finding the prompt, skill, or owner they need.

## Operator evidence

OpenCode / MiMo-V2.6-Flash correctly recovered the four registered upstream sources and P79 prior-art command, but only after expensive search. Its own diagnosis was:

- `harness/CONTEXT.md` has no direct donor/upstream/prior-art route;
- P79 is buried in prompt registry/prose rather than exposed as a one-hop repository route;
- “upstream” is overloaded;
- the relevant external-resource skill did not surface naturally in that local run;
- the current experience burns context through grep/glob before owner resolution.

Current provider truth sharpens that diagnosis:

- `operant-external-resource-intake` **is** registered today in `SKILLS.md`, `CAPABILITIES.md`, and `harness/triggers.v1.json`;
- its skill body still copies a three-donor list while the authoritative contract contains four registered sources, proving duplicated navigation/reference prose can drift;
- `harness/CONTEXT.md` is explicitly the default 50,000-foot router but has no donor/upstream/prompt-owner route;
- prompt search synonyms are hard-coded as `build_prompt_kit.py::SYNONYMS`, so browser prompt discovery has a routing vocabulary that repository-local agents cannot query through a compact canonical CLI;
- P14 already separates **Standards** and **Spec** review axes;
- P124 already owns repo-wide source readability and representative-edit proof;
- P76 already owns progressive disclosure and context-budget architecture.

## Upstream donor evidence

Registered Matt Pocock donor floor and current upstream `main` are both:

`mattpocock/skills@c55ee46073ed923f86ce59a5eb3b6d895095d1b7`

Relevant donor concepts to adapt, not copy blindly:

1. **ask-matt** — one router over a large skill graph; when reachable skills change, the router must remain truthful.
2. **writing-for-agents** — context pointers must encode when to follow them; duplicated docs are caches that must earn their load; progressive disclosure protects attention.
3. **improve-codebase-architecture / codebase-design** — optimize for AI-navigability, locality, leverage, and deep modules; “understanding one concept requires bouncing between many files” is an architecture smell.
4. **code-review** — pin a fixed point and review **Standards** and **Spec** independently; repository standards override generic smell heuristics; a fresh reviewer is preferred.

The repository already has close equivalents in P76, P14, and P124. This program strengthens those existing owners and the deterministic discovery seam rather than creating duplicate prompt identities or a second review framework.

## LAUNCH ORDER

1. **F0 — Prompt Wayfinding Baseline + Retrieval-Cost Contract**
   - Establish measurable before-state and a deterministic evaluation corpus.
   - Gate: representative prompt-finding cases have expected owner/route, search-cost metrics, and a reproducible baseline.

2. **A1 — P79 One-Hop Route + Donor Reference De-duplication**
   - Immediate low-risk wayfinding repair using existing P79 / external-resource ownership.
   - Gate: a fresh agent starting from `AGENTS.md` + `harness/CONTEXT.md` can route “registered donor/upstream prompt prior-art” to the external-resource owner and P79 command without broad search.

3. **B1 — Canonical Prompt Discovery Deep Module**
   - Hard dependency: PR #623 must integrate or release `build_prompt_kit.py`; do not race its active writer.
   - Factor browser/repository discovery vocabulary into one canonical data/interface seam and expose a compact prompt-locator CLI.
   - Gate: browser search and repository CLI consume the same alias authority; P79/P65/P76/P124/P14 representative cases resolve deterministically.

4. **PARALLEL GROUP C — launch together after B1**
   - **C1 — Fresh Standards/Spec + Readability Review**
   - **C2 — OpenCode/MiMo Live Wayfinding Proof**

5. **D1 — Convergence + Stale Discovery Owner Cleanup**
   - Rejoin C1/C2 evidence, repair bounded findings, integrate the exact green result, then disposition stale discovery PRs only after proving whether unique work remains.

## Dependency graph

```
F0
 ↓
A1
 ↓
B1
 ├──────────────┐
 ↓              ↓
C1             C2
 └──────┬───────┘
        ↓
       D1
```

Mutation graph width is 1 through B1. After B1, C1 and C2 are safely parallel because C1 owns review/repair of the candidate diff while C2 is a runtime evidence lane and must not mutate product source.

## Collision ledger

| Surface | Current collision | Rule |
|---|---|---|
| `build_prompt_kit.py` | PR #623 | B1 waits for #623 integration/release |
| `scripts/prompt_registry_ops.py` | PR #623 and #629 | this program does **not** add locator behavior there; prompt mutation and prompt finding remain separate interfaces |
| `harness/test-floor.v1.json` | PR #623 and #629 | avoid new registration by extending already-registered context/discovery tests where practical |
| semantic profile/migration files | PR #623 and #629 | no prompt-body lifecycle change is required by this plan |
| external-resource contract/validator/workflow | PR #619 | A1 must not mutate those surfaces; it may change only the skill/reference/router surfaces not owned by #619 |
| `.ai/WORK_QUEUE.md` | PR #615 and #626 | do not index this plan there until the ledger writer converges |
| prompt discovery/guidance files | stale PR #263 | donor evidence only; compare before B1 and preserve unique useful work |
| compiled prompt routing | stale PR #600 | donor evidence only; inspect before inventing a new routing algorithm |
| classifier observations | stale PR #431 | donor evidence only; runtime observation data may inform F0/C2 but does not own canonical routing |

## F0 — Prompt Wayfinding Baseline + Retrieval-Cost Contract

**Primary owner:** P76 / context architecture + skill-evaluation evidence.

**Owned surfaces:**
- new bounded evaluation fixtures/reporting under `harness/evals/` and/or `Outputs/`;
- existing registered tests such as `tests/test_context_architecture.py` and `tests/test_prompt_kit_discovery.py` when a regression assertion belongs there;
- no product routing mutation yet.

**Representative cases:**
1. “Does a registered donor/upstream skill or prompt already cover this?” → external-resource intake + P79 prior-art gate.
2. “I need to add/strengthen a prompt after prior-art search.” → P79.
3. “I don’t know which prompt fits this request.” → P65.
4. “The repository burns too much context finding owners.” → P76.
5. “Make this code easier for agents to navigate/edit.” → P124.
6. “Review this PR since main against repo standards and the requested behavior.” → P14.

**Metrics:**
- correct first owner;
- number of repository files opened before owner resolution;
- grep/glob/free-text search count;
- route hops from default load;
- approximate characters/tokens loaded using the existing context-architecture estimator;
- time/tool-call count when runtime capture supports it;
- whether a wrong adjacent owner is selected.

**Acceptance target:** static route corpus is deterministic and the MiMo baseline case is recorded without claiming model-general runtime proof.

## A1 — P79 One-Hop Route + Donor Reference De-duplication

**Goal:** fix the specific MiMo/P79 failure without waiting for a larger search refactor.

**Owned surfaces:**
- `harness/CONTEXT.md`;
- `harness/contracts/context-architecture.v1.json` only if a machine-enforced route invariant is required;
- `.ai/skills/operant-external-resource-intake/SKILL.md`;
- human routing index `TRIGGERS.md` only if current machine trigger is not visibly represented;
- existing context/external-resource tests.

**Required behavior:**
- add one compact default-router row using unambiguous leading words such as **donor / registered external source / prompt prior-art**;
- route the user to the already-existing `operant-external-resource-intake` capability/skill and `python scripts/prompt_registry_ops.py prior-art --query "<terms>"` when the task is prompt admission/strengthening;
- keep generic external prior-art analysis distinct from P79 prompt-admission prior art;
- remove the copied three-donor list from the skill or replace it with a compact pointer to `harness/contracts/operant-external-resource-intake.v1.json → sources[]`;
- do not duplicate the four-source list into another always-loaded document.

**Acceptance:** starting from the default two-file context load, a donor/upstream prompt query resolves to the correct owner in one routing hop and no broad repository search is required.

## B1 — Canonical Prompt Discovery Deep Module

**Primary design objective:** one stable interface hides registry loading, aliases, and ranking so agents and browser consumers do not need to understand several implementation files.

**Likely canonical surfaces:**
- new machine-readable alias authority such as `registry/prompts/prompt-discovery-aliases.v1.json`;
- a cohesive module such as `scripts/prompt_discovery.py`;
- a thin CLI such as `scripts/find_prompt.py --query "<intent>"`;
- `build_prompt_kit.py` changed to consume the shared alias authority instead of owning a giant hard-coded `SYNONYMS` table;
- `harness/contracts/prompt-kit-discovery.v1.json`;
- `scripts/validate_prompt_kit_discovery.py`;
- `tests/test_prompt_kit_discovery.py`;
- `harness/CONTEXT.md` route upgraded from the A1 P79-specific path to the general locator where appropriate;
- generated Prompt Kit only through its canonical builder.

**Design constraints:**
- browser Prompt Finder and repository CLI share one alias/data owner;
- prompt bodies remain in their existing registries; do not build a second prompt catalog;
- aliases are routing metadata, not prompt identity;
- P65 remains conversational guided discovery; the CLI is a deterministic fast path, not a replacement;
- P79 remains admission/mutation/prior-art owner;
- the locator returns compact results: prompt ID, name, useWhen/role summary, canonical registry path, and next relevant command/owner;
- exact IDs/names remain strongest matches;
- ambiguous generic terms may return a bounded ranked set rather than silently selecting one prompt;
- include focused aliases for the observed failures: donor/registered external source/prompt prior-art → P79 path; code readability → P124; PR Standards+Spec review → P14; prompt finder → P65; context/token bloat → P76.

**Readability objective:** a fresh maintainer should be able to answer “where do I change prompt-discovery aliases/ranking?” with one canonical owner instead of bouncing among builder, tutorial JS, docs, and tests.

**Acceptance:**
- one alias authority;
- one deterministic Python discovery interface;
- browser behavior remains parity-compatible;
- CLI locator resolves representative F0 cases;
- context/discovery tests pass;
- no new prompt identity, skill, or second search database.

## C1 — Fresh Standards/Spec + Readability Review

Run in a **fresh chat/session** against the exact B1 fixed point.

Use repository P14 as the execution owner. Matt Pocock `code-review` is donor evidence for the method, not a new installed owner.

Review two independent axes:

### Standards
- repository law and existing tests/contracts;
- P124 readability/editability rules;
- AI-navigability: does one discovery concept still require opening many shallow files?
- duplicated alias/ranking rules;
- shotgun surgery / divergent change / middle-man / speculative-generalization signals;
- generated-source ownership;
- naming/locality/interface depth.

### Spec
Check the B1 diff against this sprint map:
- one-hop prompt finding;
- no second prompt catalog;
- P79/P65/P76/P124/P14 ownership preserved;
- same alias authority for browser and CLI;
- P79 donor query no longer requires grep/glob;
- no scope creep into prompt lifecycle or generic external prior-art ownership.

Every finding must cite a file/hunk plus the repo rule/spec line it derives from. Review output is a hypothesis until verified against source.

**Mutation:** only bounded B1 repair findings. Broader pre-existing debt is routed to P124 and does not hijack this program.

## C2 — OpenCode/MiMo Live Wayfinding Proof

**Environment:** local OpenCode with MiMo-V2.6-Flash, fresh sessions, exact candidate checkout.

**No product-source mutation.**

Run the F0 representative cases on:
1. refreshed pre-change baseline when reproducible;
2. exact B1 candidate.

Capture:
- model/provider;
- commit;
- initial loaded files;
- tool calls;
- grep/glob/search calls;
- files opened;
- approximate characters/tokens loaded when available;
- time to first correct owner;
- final selected prompt/skill/capability;
- whether the agent followed `harness/CONTEXT.md` rather than free-searching.

**Primary acceptance for the original failure:**
- donor/upstream prompt prior-art query reaches the external-resource owner/P79 path from the default router without broad grep/glob;
- correct owner arrives before loading large prompt registries/bodies;
- candidate uses materially fewer search calls/files/context than the captured baseline.

Do not call this model-general proof; it is observed MiMo/OpenCode runtime evidence.

## D1 — Convergence + Stale Discovery Owner Cleanup

Rejoin C1 and C2.

1. repair only verified bounded findings;
2. rerun F0 static corpus, context architecture, discovery validator/tests, generated parity, and exact relevant CI;
3. compare stale PRs #263, #600, #431, and #393 against integrated current behavior;
4. close or supersede a stale PR only when its unique useful behavior is either integrated or explicitly preserved elsewhere;
5. once PR #615/#626 release the work-ledger surface, index this plan/result in the canonical ledger rather than racing them;
6. integrate the exact green result to current default branch;
7. preserve the runtime proof ceiling.

## Skill / capability / trigger factoring

| Item | Decision | Reason |
|---|---|---|
| P76 context architecture | KEEP / strengthen routing evidence | already owns progressive disclosure and context budgets |
| P65 Guided Prompt Finder | KEEP | conversational fallback remains useful |
| P79 Prompt Registry owner | KEEP | prompt admission/prior-art owner, not general router |
| P124 Code Readability | KEEP | already owns repo-wide source editability |
| P14 PR Review | KEEP | already has independent Standards + Spec axes |
| `operant-external-resource-intake` skill | KEEP / de-duplicate stale donor list | capability and trigger already exist |
| external-resource trigger | KEEP | machine trigger already routes open-source resource queries |
| new “prompt finder skill” | REJECT | adds context and duplicates P65/discovery code |
| new review skill | REJECT | duplicates P14 |
| deterministic prompt-locator operation | CREATE as code/capability surface, not prose skill | fast exact operation is reusable and low-context |
| shared alias registry | CREATE | removes hard-coded browser-only routing vocabulary and creates one source of truth |
| MiMo/OpenCode proof | CREATE eval/receipt only | runtime evidence, not product owner |

## Proof taxonomy

- **Contract proof:** router/alias/ownership contracts are coherent.
- **Static routing proof:** representative queries deterministically map to intended owners.
- **Context-budget proof:** default route stays inside P76/context-architecture budgets.
- **Build proof:** browser Prompt Kit consumes the shared aliases and generated parity passes.
- **Review proof:** fixed-point Standards and Spec findings are independently dispositioned.
- **Observed runtime proof:** MiMo/OpenCode uses the candidate and measurably reduces search/context cost.
- **Integration proof:** exact candidate is contained on refreshed default branch.
- **Operator acceptance:** the repository actually feels easier to navigate in routine work.

Never promote a lower level upward. Static route tests do not prove MiMo behavior; MiMo behavior does not prove every model; green build does not prove readability; review findings do not become facts until source verification.

## Success criteria for the whole program

A fresh agent should be able to:
1. load only `AGENTS.md` + `harness/CONTEXT.md`;
2. ask “which prompt/owner handles this?” through one deterministic locator;
3. resolve the P79 donor/prior-art path without broad grep/glob;
4. resolve P14/P65/P76/P124 from ordinary intent language;
5. locate the canonical discovery code/data owner without opening a chain of shallow files;
6. preserve browser finder behavior from the same routing vocabulary;
7. spend materially less context/tool-search effort in MiMo/OpenCode observed proof.

The program is not complete merely because another index document exists. The win is fewer search branches, fewer loaded files, one canonical routing vocabulary, clearer code ownership, and observed lower agentic retrieval cost.
