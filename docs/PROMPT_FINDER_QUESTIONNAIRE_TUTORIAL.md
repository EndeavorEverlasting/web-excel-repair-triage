# Find the Right Prompt with the Prompt Kit Tutorial

The Prompt Kit tutorial is one continuous **Find → Use → Prove → Continue** experience. You do not need to know prompt IDs or scroll the whole library before beginning work. Four short questions route you to one prompt; that prompt's registry-owned `nextStep` carries you forward through the rest of the path.

The experience runs entirely in the generated page. It does not send answers to a server and does not retain them after the page is reset or closed.

For the broader operating model—supported entry points, Favorites, hotkeys, inherited-work verification, troubleshooting, and proof boundaries—see [`PROMPT_KIT_OPERATOR_GUIDE.md`](PROMPT_KIT_OPERATOR_GUIDE.md).

## The four phases

### Phase 1 · Find

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html` or the public Prompt Kit URL.
2. Select the glowing **Tutorial · Find My Prompt** control in the header.
3. Answer the four current questions:
   - **Where are you starting?** — no checkout/new start, already in a repository, or app/artifact open.
   - **Do you have a known problem you want to solve?** — active failure, known task, repeated stall, or discovery/planning.
   - **What are you trying to accomplish?** — plan, coordinate, build, AI/agent production hardening, prove, ship, teach, or close out.
   - **How should the work be organized?** — one bounded sprint, parallel lanes, dependency-ordered work, or live/runtime proof.
4. The result names one **Phase 1 · Found** primary prompt and, when useful, follow-on options. Inline below the primary card, the same frame shows the **Use → Prove → Continue** phases so you see the whole path before you commit.
5. Select **Open** to inspect the full prompt or **Copy** to place it on the clipboard.

The questionnaire does not invent prompt text or maintain a private prompt-ID routing table. Each answer becomes ordinary search phrases passed through the same `filterPromptsForQuery(PROMPTS, query)` function used by the Prompt Kit search box, so the tutorial reuses the current registry, synonym dictionary, metadata ranking, and filtering behavior instead of a second recommendation engine.

For each phrase, the finder considers the first five shared-search results, gives stronger results more weight, aggregates evidence across the four answers, sorts by score and discovery rank, and returns at most three candidates. It is a routing aid—not an authorization or correctness oracle. If you already know the exact specialist you need, search its ID or exact name directly.

### When another agent says the work is complete

A specific inherited-completion claim is an important case that the current four-question browser questionnaire does not represent with a dedicated answer.

If another agent, chat, handoff, branch, PR, report, artifact, or implementation claims work is complete or partially complete and you need to establish whether that claim is actually true, search for **P83 — Agent Work Verifier & Iterative Advancer** directly.

P83 owns independent verification of inherited work: resolve the exact prior work and current evidence floor, treat the completion report as a hypothesis rather than proof, repair or finish concrete gaps, independently derive validation, and advance proven work through integration when authorized.

Do not force a broader questionnaire answer such as **known task**, **runtime proof**, or **one sprint** to stand in for the inherited-claim distinction. Prototyping, regression proof, runtime proof, and integration may be later gates after the inherited work has been verified.

### Phase 2 · Use

Select **Copy** on the found prompt and run it in a new chat. Fill its concrete variables and execute the bounded sprint it describes. **Open** lets you inspect the full prompt first. When you open any prompt, its detail view includes a guided workflow panel that carries the same four-phase rail with **Find** marked complete and **Use** active, so the experience stays continuous instead of restarting.

### Phase 3 · Prove

The guided workflow panel's **READY TO CONTINUE WHEN** section shows the prompt's registered `expectedOutput` or `proofGate`. Finish that proof before advancing. Do not stop at a summary, plan, or status-only report while the prompt's owned executable work remains.

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

### Phase 4 · Continue

The panel's **NEXT-STEP CONTRACT** section shows the prompt's current `nextStep` registry guidance, and **Next** or **Option** cards appear only for prompt IDs actually referenced by that `nextStep` and present in the current registry. Select **Open** to inspect the next prompt or **Copy** to run it. **Mark this step complete** gives you lightweight session progress stored only in browser `sessionStorage` — cleared with the browsing session, never changing the repository or your saved Favorites. If the prompt has no explicit registered successor, use **Re-run Find My Prompt** after the current result changes your context.

This is deliberately not a second routing database. The browser reads the same `nextStep`, `expectedOutput`, `proofGate`, `useWhen`, IDs, and names already produced by the canonical prompt registry.

Marking a step complete is navigation state, not validation. It does not prove a test, runtime, deployment, merge, or operator-acceptance gate.

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
| One durable tutorial is needed | P18 | Creates tutorial content and integrates it into repository help surfaces. |
| Several possible tutorials must be ranked first | P64 | Inventories and ranks tutorial paths, prerequisites, and proof readiness. |
| Immediate coaching is needed for an app already open | P24 | Guides the current app-at-hand interaction without replacing durable documentation. |

The table is explanatory documentation, not the browser recommendation implementation. Browser recommendations are computed from the current registry and shared search path, while subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.

Recommendations are evidence-informed routing aids, not automatic authorization. Read the selected prompt's owned scope, forbidden scope, dependencies, and proof gate before using it.

## Conversational fallback

The website questionnaire is the fastest general path. When the generated website cannot be opened—or when you need a conversational distinction the current browser questions do not represent—search for or copy **P65 — Guided Prompt Finder Questionnaire** into an AI chat.

P65 asks one concise question at a time, recommends one primary prompt and no more than two follow-ons, and refuses to fabricate prompt IDs that are not present in its supplied/current routing vocabulary.

When you already know the exact specialist, such as P83 for verifying another agent's claimed completion, open that prompt directly rather than using P65 merely for ceremony.

## Interaction notes

- Favorite, Open, and Copy live in one explicit prompt-card action rail. Desktop cards reserve space for the rail; mobile cards move the rail into its own touch-sized row. This prevents action buttons from occupying overlapping absolute positions.
- A successful copy produces both a green glowing confirmation toast and a brief green card flash. Reduced-motion preferences disable the movement while preserving visible confirmation.
- The four-phase rail and guided workflow panels use an animated current-to-next progression. Reduced-motion preferences preserve the structure and state while disabling movement.
- Workflow completion is intentionally session-scoped; it does not compete with Favorites, which remain persistent browser-local preferences.
- The explicit **Favorites** view is a filter; Favorites do not reorder the normal chronological library by default.
- Favorite prompt-ID shortcuts copy the canonical prompt and reveal its card rather than opening prompt detail. See the operator guide for the full shortcut workflow.
- `P61` remains `P61`, even when it appears near the top of the Foundation section; newly added prompts can be promoted when they are important entry points; search and copied prompt references remain stable; future ordering changes can be reviewed as a bounded display-policy change.

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
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
node scripts/analyze_prompt_finder_routes.js
```

## Proof ceiling

Repository validation can prove registry integrity, shared-search recommendation routing, registry-owned next-step extraction, session-only completion state, JavaScript syntax, action-rail structure, the four-phase Find → Use → Prove → Continue frame, current Favorite/shortcut semantics, generated-site parity, transitive route coverage, and focused test/documentation behavior.

It does not prove every browser or assistive-technology combination, clipboard permissions on every device, live Windows launcher behavior on a particular workstation, organizational acceptance of the recommendations, or that a recommended prompt will succeed without the environment and permissions required by that prompt.
