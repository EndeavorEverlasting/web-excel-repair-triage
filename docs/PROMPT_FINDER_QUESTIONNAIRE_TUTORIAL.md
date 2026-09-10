# Find the Right Prompt with the Prompt Kit Tutorial

The Prompt Kit contains many specialized prompts. You do not need to know their IDs or scroll through the entire library before beginning work.

For the broader operating model—supported entry points, Favorites, hotkeys, inherited-work verification, troubleshooting, and proof boundaries—see [`PROMPT_KIT_OPERATOR_GUIDE.md`](PROMPT_KIT_OPERATOR_GUIDE.md).

## Start the questionnaire

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html` or the public Prompt Kit URL.
2. Select the glowing **Tutorial · Find My Prompt** control in the header.
3. Answer the four current questions:
   - **Where are you starting?** — no checkout/new start, already in a repository, or app/artifact open.
   - **Do you have a known problem you want to solve?** — active failure, known task, repeated stall, or discovery/planning.
   - **What are you trying to accomplish?** — plan, coordinate, build, AI/agent production hardening, prove, ship, teach, or close out.
   - **How should the work be organized?** — one bounded sprint, parallel lanes, dependency-ordered work, or live/runtime proof.
4. Review the **Primary recommendation** first. The page may show up to two additional candidates.
5. Read **After the recommendation** when it appears to see the current registry-owned continuation path.
6. Select **Open** to inspect the full prompt or **Copy** to place it on the clipboard.
7. Complete the current prompt's expected output or proof gate before moving to a registered next step.

The questionnaire runs in the generated page. It does not send answers to a separate recommendation service and does not retain questionnaire answers after reset/closure.

## How recommendations are computed

The browser finder does not maintain a private prompt-ID routing table. Each selected answer contributes ordinary search phrases and passes them through the same `filterPromptsForQuery(PROMPTS, query)` path used by normal Prompt Kit search.

For each phrase, the finder considers the first five shared-search results, gives stronger results more weight, aggregates evidence across the four answers, sorts by score and discovery rank, and returns at most three candidates.

That means the tutorial reuses the current prompt registry, synonyms, metadata, search ranking, and filters rather than creating a second recommendation database. It also means the questionnaire is a routing aid—not an authorization or correctness oracle. If you already know the exact specialist you need, search its ID or exact name directly.

## When another agent says the work is complete

A specific inherited-completion claim is an important case that the current four-question browser questionnaire does not represent with a dedicated answer.

If another agent, chat, handoff, branch, PR, report, artifact, or implementation claims work is complete or partially complete and you need to establish whether that claim is actually true, search for **P83 — Agent Work Verifier & Iterative Advancer** directly.

P83 owns independent verification of inherited work: resolve the exact prior work and current evidence floor, treat the completion report as a hypothesis rather than proof, repair or finish concrete gaps, independently derive validation, and advance proven work through integration when authorized.

Do not force a broader questionnaire answer such as **known task**, **runtime proof**, or **one sprint** to stand in for the inherited-claim distinction. Prototyping, regression proof, runtime proof, and integration may be later gates after the inherited work has been verified.

## Use → prove → continue

The recommendation is a starting point, not the end of the tutorial.

When you open a prompt, its detail view includes a **Guided workflow** panel:

1. **Now** identifies the prompt you are about to use.
2. **NEXT-STEP CONTRACT** shows that prompt's current registry `nextStep` guidance.
3. **READY TO CONTINUE WHEN** shows the prompt's registered expected output or proof gate.
4. **Next** or **Option** cards appear only for prompt IDs actually referenced by the current prompt's `nextStep` and present in the current registry.
5. **Open** lets you inspect the next prompt; **Copy** copies that registered prompt.
6. **Mark this step complete** gives lightweight session progress. Completion is stored only in browser `sessionStorage`; it is cleared with the browsing session and never changes the repository or saved Favorites.
7. If there is no explicit registered successor, use **Re-run Find My Prompt** after the current result changes your context.

This is deliberately not a second routing database. The browser reads the same `nextStep`, `expectedOutput`, `proofGate`, `useWhen`, IDs, and names already produced by the canonical prompt registry.

Marking a step complete is navigation state, not validation. It does not prove a test, runtime, deployment, merge, or operator-acceptance gate.

### Evidence-bearing closeout

Effective Prompt Kit prompts inherit the shared operational closeout contract. Before a legitimate stop, the agent should spend words on decisions, evidence, uncertainty, and continuation—not on narrating tool use or repeating the plan.

A useful closeout distinguishes:

- **completed / proven** work, changed surfaces, produced artifacts, and validation actually observed;
- **commands / examples verified** only when they actually ran or have independent execution evidence;
- **unproven runtime / field steps** that static or CI checks cannot promote into browser, device, production, or operator acceptance;
- **review / reconciliation** when a finding, failed check, or earlier design changed the work: finding → repair/disposition → rerun proof;
- **integration state** for repository work, including target branch, PR/merge state, and refreshed-main evidence;
- **remaining gaps, risks, blockers, and proof ceiling** without hiding uncertainty behind `green` or `ready`;
- the first executable **next action**, or `none; no safe actionable work remains` only when the owned work is genuinely complete.

A copy-paste handoff is useful when work must continue in another chat or agent. It should carry the exact repo/source, branch/PR/SHA or artifact identity, proven floor, remaining gap or blocker, forbidden scope, and first executable action. Do not add a ceremonial handoff when no continuation remains.

## Common paths

| Situation | Typical starting prompt | Why |
|---|---|---|
| The repository is not checked out or its local path is unknown | P61 | Establishes the exact repository and working directory safely. |
| The repository is unfamiliar | P03 | Recovers repository truth before mutation. |
| A bounded implementation task is already known | P07 | Executes one owned sprint through validation and delivery. |
| Something is failing now | P58 | Diagnoses from observed evidence before guessing at a fix. |
| Another agent claims work is complete or partially complete and you need to verify it | P83 | Treats inherited completion claims as evidence to verify, then repairs/advances the actual state. |
| Several independent lanes can run together | P59 | Defines ownership, collision boundaries, and convergence for parallel work. |
| Work must proceed in dependency order | P60 | Produces a serialized execution sequence. |
| CI/CD promotion should work locally or over generic Git whenever possible and use a forge only for forge-owned gates | P105 | Builds a provider-agnostic, local-first promotion core with thin host adapters and a bounded provider-request budget. |
| One durable tutorial is needed | P18 | Creates tutorial content and integrates it into repository help surfaces. |
| Several possible tutorials must be ranked first | P64 | Inventories and ranks tutorial paths, prerequisites, freshness signals, and proof readiness. |
| Immediate coaching is needed for an app already open | P24 | Guides the current app-at-hand interaction without replacing durable documentation. |

The table is explanatory documentation, not the browser recommendation implementation. Browser recommendations are computed from the current registry and shared search path, while subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.

Recommendations are evidence-informed routing aids, not automatic authorization. Read the selected prompt's owned scope, forbidden scope, dependencies, and proof gate before using it.

## Local-first CI/CD with P105

P105 now separates the **repository-owned promotion core** from any particular forge. The first question is not “which GitHub Action should we write?” It is “which parts of this promotion can the repository and plain Git prove without a provider?”

Use three execution modes:

1. **LOCAL_ONLY** — run repository-owned validation, build/package, provenance, candidate-receipt, and policy-evaluation commands without a hosted CI provider.
2. **GIT_REMOTE_MINIMAL** — use ordinary Git transport for fetch/push/tag/ref operations when repository policy allows them and no provider-only gate is required.
3. **PROVIDER_GOVERNED** — use the host adapter only for facts or mutations Git cannot establish, such as required-check state, unresolved review threads, merge queues, protected environments, or authoritative provider mutation receipts.

GitHub Actions remains supported when GitHub is the observed host, but it is an adapter over the same repository-owned commands. A GitLab CI, Azure Pipelines, Gitea/Forgejo, self-hosted runner, or local shell should be able to invoke the same core when its capability map permits. This follows the upstream pattern where multiple CI providers call one repository-owned build/release implementation instead of embedding product logic in each provider YAML.

### Rate-limit behavior

Provider calls are a budgeted dependency, not free background polling. P105 requires agents to:

- classify a call as **GIT_PROVABLE** or **PROVIDER_ONLY** before adding another provider dependency;
- reuse candidate-bound provider truth while its SHA/base/policy identity remains current;
- prefer event-driven wakeups over status polling and batch compatible reads where supported;
- honor `Retry-After` and provider reset metadata, use bounded backoff with jitter, and cap refresh attempts;
- preserve the highest proven local gate and candidate receipt when `PROVIDER_RATE_LIMITED` occurs;
- resume from the same candidate after provider recovery instead of rerunning unchanged local work;
- still perform the authoritative fresh provider read immediately before a provider-governed mutation.

A provider outage or rate limit never grants permission to bypass branch protection. Local/Git proof reduces dependence on the forge; it does not counterfeit provider-owned proof.

## Conversational fallback

The website questionnaire is the fastest general path. When the generated website cannot be opened—or when you need a conversational distinction the current browser questions do not represent—search for or copy **P65 — Guided Prompt Finder Questionnaire** into an AI chat.

P65 asks one concise question at a time, recommends one primary prompt and no more than two follow-ons, and refuses to fabricate prompt IDs that are not present in its supplied/current routing vocabulary.

When you already know the exact specialist, such as P83 for verifying another agent's claimed completion, open that prompt directly rather than using P65 merely for ceremony.

## Interaction notes

- Favorite, Open, and Copy live in one prompt-card action rail.
- A successful copy produces the current green confirmation path.
- Guided workflow panels preserve the same structure under reduced-motion preferences.
- Workflow completion is session-scoped and separate from persistent Favorites.
- The explicit **Favorites** view is a filter; Favorites do not reorder the normal chronological library by default.
- Favorite prompt-ID shortcuts copy the canonical prompt and reveal its card rather than opening prompt detail. See the operator guide for the full shortcut workflow.

## Tutorial-planning prompts

Three prompts cover different tutorial needs:

- **P18** creates durable tutorial and help content after the workflow is ready to teach.
- **P25** plans a known tutorial path and separates product, harness, or runtime prerequisites.
- **P64** surveys the repository, ranks meaningful tutorial candidates, consumes tutorial-freshness signals, and emits tutorial sprint panels in recommended launch order.

Use P64 before P18 when the team has several possible tutorials and does not yet know which one deserves the first sprint.

## Keeping tutorials current as prompts evolve

Tutorial maintenance is part of Prompt Kit contribution work, not an optional cleanup pass.

The machine-readable lifecycle record is `registry/prompts/tutorial-freshness.v1.json`. **P79 — Prompt Registry Prompt Adder** owns ADD/STRENGTHEN contribution completeness; **P64 — Repository Tutorial Portfolio Ranker** owns tutorial prioritization and journey judgment.

### When a prompt is added

Before the canonical `prompt_registry_ops.py add` command may write a new identity, its draft must include a `tutorial` object with:

- `disposition`: `UPDATE_EXISTING_TUTORIAL`, `ADD_TUTORIAL`, or `REFERENCE_ONLY_WITH_REASON`;
- `tutorial_paths`: at least one current repository tutorial path;
- `reason`: why that tutorial treatment is correct.

At least one declared tutorial path must already mention the new prompt's **name**. This makes the tutorial update precede the registry write instead of leaving a new identity with stale teaching. The helper records the resulting prompt ID and tutorial disposition in the tutorial-freshness ledger inside the same rollback boundary as the registry and generated Prompt Kit site.

A dry run may omit the tutorial object so authors can inspect identity/routing first, but a real ADD fails closed until tutorial coverage is supplied.

### When a prompt is strengthened

Material strengthenings use `registry/prompts/prompt-strengthenings.v1.json`. Each strengthening declares its tutorial disposition, paths, and reason. The builder appends the bounded semantic strengthening without copying the entire canonical prompt body, which keeps the original owner readable while preventing a second full prompt from drifting.

### When prompt use reveals friction

Do **not** create a second telemetry system for tutorial maintenance. Prompt Kit already keeps raw ordinary usage local and information-only. Search text, typed content, prompt bodies, navigation history, clipboard content, and user identity are not tutorial inputs.

Repeated usage patterns may influence tutorial work only after the existing P99/feedback path reduces them to an accepted coarse privacy-bounded `operant_friction` receipt. P64 may consume those accepted receipts as prioritization evidence.

### Recycle proven work

When a prompt or normal repository workflow has already produced current verified commands, sanitized fixtures, expected results, failure/recovery examples, safe screenshots/diagrams, or candidate-bound proof, reuse those artifacts in the tutorial instead of rediscovering the workflow. Revalidate identity-sensitive evidence after head, dependency, UI, schema, or command changes.

The goal is a loop:

`prompt change/use → freshness signal → reuse current proof → tutorial update/disposition → validation → future operators reuse the tutorial`

That loop reduces repeated investigation without promoting stale or private evidence into documentation.

## Validation and regeneration

From the repository root:

```powershell
python -m py_compile scripts/build_prompt_kit_registry.py scripts/prompt_registry_ops.py scripts/validate_prompt_kit_discovery.py tests/test_prompt_kit_discovery.py tests/test_prompt_kit_guidance.py
node --check docs/prompt-kit.js
node --check docs/prompt-kit-guided-recommendations.js
node --check docs/prompt-kit-journey.js
node --check docs/prompt-kit-polish.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/prompt_registry_ops.py validate
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance tests.test_p105_local_first_tutorial_freshness -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

## Proof ceiling

Repository validation can prove registry integrity, bounded prompt strengthenings, prompt-add tutorial freshness enforcement, the current four-question shared-search implementation, registry-owned next-step extraction, session-only completion state, JavaScript syntax, current Favorite/shortcut semantics, generated-site parity, and focused documentation assertions.

It does not prove every browser or assistive-technology combination, clipboard permissions on every device, live Windows launcher behavior on a particular workstation, organizational acceptance of a recommendation, that usage-driven tutorial candidates are valuable before P64 evaluates them, or that a recommended prompt succeeds without the environment and permissions it requires.
