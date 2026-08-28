# Find the Right Prompt with the Prompt Kit Tutorial

The Prompt Kit contains many specialized prompts. You do not need to know their IDs or scroll through the entire library before beginning work.

For the broader operating model—supported entry points, Favorites, hotkeys, inherited-work verification, troubleshooting, and proof boundaries—see [`PROMPT_KIT_OPERATOR_GUIDE.md`](PROMPT_KIT_OPERATOR_GUIDE.md).

## Start the questionnaire

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html` or the public Prompt Kit URL.
2. Select the glowing **Tutorial · Find My Prompt** control in the header.
3. Answer the four current questions:
   - **Where are you starting?** — no checkout/new start, already in a repository, or app/artifact open.
   - **Do you have a known problem you want to solve?** — active failure, known task, repeated stall, or discovery/planning.
   - **What outcome must this tutorial hand you?** — create/strengthen a Prompt Kit prompt, implement, troubleshoot, verify inherited work, prioritize repositories by current circumstances, publish tutorial docs, prove a change, ship validated work, or close out.
   - **How should the work be organized?** — one bounded sprint, parallel lanes, dependency-ordered work, or live/runtime proof.
4. Review the **Outcome owner** first. The page may show up to two context follow-ons, but they cannot displace the owner selected by your declared terminal outcome.
5. Read **After the recommendation** when it appears to see the current registry-owned continuation path.
6. Select **Open owner** to inspect the full prompt or **Copy & start** to place the canonical owner prompt on the clipboard. Copying routes you to executable work; it does not claim the work is complete.
7. Complete the current prompt's expected output or proof gate before moving to a registered next step.

The questionnaire runs in the generated page. It does not send answers to a separate recommendation service and does not retain questionnaire answers after reset/closure.

## How recommendations are computed

The browser finder separates **terminal outcome ownership** from **context discovery**. The outcome answer names a canonical Prompt Kit owner ID already present in the registry. That owner must exist and expose non-empty copy content, expected output, proof gate, and next-step contract; otherwise the route fails closed to P65 rather than silently substituting P07.

The other answers still contribute ordinary phrases through `filterPromptsForQuery(PROMPTS, query)`. For each phrase, the finder considers the first five shared-search results, but those scores are used only for at most two context follow-ons. Shared-search ranking cannot displace the terminal outcome owner, so the full result returns at most three recommendations.

The key regression case is explicit: **Create or strengthen a Prompt Kit prompt** resolves to **P79 — Prompt Registry Prompt Adder**, regardless of broad surrounding words such as `implement`, `sprint`, or `one bounded sprint`. **Decide which repository should move first right now** resolves to **P23 — Circumstance-Aware Repo Priority Planner**.

This remains a routing aid, not authorization or completion proof. The selected owner must execute its own mission and proof gate.

## When another agent says the work is complete

Inherited-completion verification is now an explicit terminal outcome in the four-question browser questionnaire.

If another agent, chat, handoff, branch, PR, report, artifact, or implementation claims work is complete or partially complete and you need to establish whether that claim is actually true, search for **P83 — Agent Work Verifier & Iterative Advancer** directly.

P83 owns independent verification of inherited work: resolve the exact prior work and current evidence floor, treat the completion report as a hypothesis rather than proof, repair or finish concrete gaps, independently derive validation, and advance proven work through integration when authorized.

Choose **Verify work another agent says is complete** to route directly to P83. Prototyping, regression proof, runtime proof, and integration may be later gates after the inherited work has been verified.

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
| Create or strengthen a Prompt Kit prompt | P79 | Harvests relevant chat context, strengthens canonical owners first, and helper-adds only genuinely missing prompt identities. |
| Decide which repository should move first under current circumstances | P23 | Separates urgency/access/readiness from structural gap severity. |
| A bounded implementation task is already known | P07 | Executes one owned sprint through validation and delivery. |
| Something is failing now | P58 | Diagnoses from observed evidence before guessing at a fix. |
| Another agent claims work is complete or partially complete and you need to verify it | P83 | Treats inherited completion claims as evidence to verify, then repairs/advances the actual state. |
| Several independent lanes can run together | P59 | Defines ownership, collision boundaries, and convergence for parallel work. |
| Work must proceed in dependency order | P60 | Produces a serialized execution sequence. |
| One durable tutorial is needed | P18 | Creates tutorial content and integrates it into repository help surfaces. |
| Several possible tutorials must be ranked first | P64 | Inventories and ranks tutorial paths, prerequisites, and proof readiness. |
| Immediate coaching is needed for an app already open | P24 | Guides the current app-at-hand interaction without replacing durable documentation. |

The table is explanatory documentation, not the browser recommendation implementation. Browser outcome ownership is resolved from the current registry, shared search supplies only context follow-ons, and subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.

Recommendations are evidence-informed routing aids, not automatic authorization. Read the selected prompt's owned scope, forbidden scope, dependencies, and proof gate before using it.

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
- **P64** surveys the repository, ranks meaningful tutorial candidates, and emits tutorial sprint panels in recommended launch order.

Use P64 before P18 when the team has several possible tutorials and does not yet know which one deserves the first sprint.

## Validation and regeneration

From the repository root:

```powershell
python -m py_compile scripts/build_prompt_kit_registry.py scripts/validate_prompt_kit_discovery.py tests/test_prompt_kit_discovery.py tests/test_prompt_kit_guidance.py
node --check docs/prompt-kit.js
node --check docs/prompt-kit-guided-recommendations.js
node --check docs/prompt-kit-journey.js
node --check docs/prompt-kit-polish.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/validate_prompt_kit_discovery.py --summary
node scripts/validate_prompt_finder_outcomes.js
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

`validate_prompt_finder_outcomes.js` is the fail-closed owner for terminal-outcome routing. Run it before interpreting the broader discovery tests so an owner mismatch cannot be hidden by otherwise healthy search behavior.

## Proof ceiling

Repository validation can prove registry integrity, the current four-question outcome-owner model, repeated terminal-route stability across many context combinations, registry-owned next-step extraction, session-only completion state, JavaScript syntax, current Favorite/shortcut semantics, generated-site parity, and focused documentation assertions.

It does not prove every browser or assistive-technology combination, clipboard permissions on every device, live Windows launcher behavior on a particular workstation, organizational acceptance of a recommendation, or that a recommended prompt succeeds without the environment and permissions it requires.
