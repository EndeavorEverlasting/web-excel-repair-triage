# Find the Right Prompt with the Prompt Kit Tutorial

The Prompt Kit tutorial is one continuous **Find → Use → Prove → Continue** experience. You do not need to know prompt IDs or scroll the whole library before beginning work. Four short questions route you to one prompt; that prompt's registry-owned `nextStep` carries you forward through the rest of the path.

The experience runs entirely in the generated page. It does not send answers to a server and does not retain them after the page is reset or closed.

## The four phases

### Phase 1 · Find

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html` or the public Prompt Kit URL.
2. Select the glowing **Tutorial · Find My Prompt** control in the header.
3. Answer four bounded questions: where you are starting, your job to be done, your stage or work shape, and an adaptive discriminator built from the candidate pool.
4. The result names one **Phase 1 · Found** primary prompt and, when useful, follow-on options. Inline below the primary card, the same frame shows the **Use → Prove → Continue** phases so you see the whole path before you commit.

The questionnaire does not invent prompt text or maintain a private prompt-ID routing table. Each answer becomes ordinary search phrases passed through the same `filterPromptsForQuery(PROMPTS, query)` function used by the Prompt Kit search box, so the tutorial reuses the current registry, synonym dictionary, metadata ranking, and filtering behavior instead of a second recommendation engine.

### Phase 2 · Use

Select **Copy** on the found prompt and run it in a new chat. Fill its concrete variables and execute the bounded sprint it describes. **Open** lets you inspect the full prompt first. When you open any prompt, its detail view includes a guided workflow panel that carries the same four-phase rail with **Find** marked complete and **Use** active, so the experience stays continuous instead of restarting.

### Phase 3 · Prove

The guided workflow panel's **READY TO CONTINUE WHEN** section shows the prompt's registered `expectedOutput` or `proofGate`. Finish that proof before advancing. Do not stop at a summary, plan, or status-only report while the prompt's owned executable work remains.

### Phase 4 · Continue

The panel's **NEXT-STEP CONTRACT** section shows the prompt's current `nextStep` registry guidance, and **Next** or **Option** cards appear only for prompt IDs actually referenced by that `nextStep` and present in the current registry. Select **Open** to inspect the next prompt or **Copy** to run it. **Mark this step complete** gives you lightweight session progress stored only in browser `sessionStorage` — cleared with the browsing session, never changing the repository or your saved Favorites. If the prompt has no explicit registered successor, use **Re-run Find My Prompt** after the current result changes your context.

## Common paths

| Situation | Typical starting prompt | Why |
|---|---|---|
| The repository is not checked out or its local path is unknown | P61 | Establishes the exact repository and working directory safely. |
| The repository is unfamiliar | P03 | Recovers repository truth before mutation. |
| A bounded implementation task is already known | P07 | Executes one owned sprint through validation and delivery. |
| Something is failing now | P58 | Diagnoses from observed evidence before guessing at a fix. |
| Several independent lanes can run together | P59 | Defines ownership, collision boundaries, and convergence for parallel work. |
| Work must proceed in dependency order | P60 | Produces a serialized execution sequence. |
| One durable tutorial is needed | P18 | Creates tutorial content and integrates it into repository help surfaces. |
| Several possible tutorials must be ranked first | P64 | Inventories and ranks tutorial paths, prerequisites, and proof readiness. |
| Immediate coaching is needed for an app already open | P24 | Guides the current app-at-hand interaction without replacing durable documentation. |

The table is explanatory documentation, not the browser recommendation implementation. Browser recommendations are computed from the current registry and shared search/filter path, while subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.

Recommendations are evidence-informed routing aids, not automatic authorization. Read the selected prompt's owned scope, forbidden scope, dependencies, and proof gate before using it.

## Conversational fallback

The website questionnaire is the fastest path. When the generated website cannot be opened, search for or copy **P65 — Guided Prompt Finder Questionnaire** into an AI chat.

P65 asks one question at a time, recommends one primary prompt and no more than two follow-ons, and explains why each prompt fits. It also refuses to fabricate prompt IDs that are not present in the supplied or current registry.

## Why prompt IDs did not change

Prompt IDs and `seq` values are stable identities used by documentation, search synonyms, tests, capabilities, and external references. The Prompt Kit applies a separate `discoveryRank` from `registry/prompts/prompt-display-order.v1.json` to promote broadly useful entry points without renaming or renumbering established prompts.

This means:

- `P61` remains `P61`, even when it appears near the top of the Foundation section;
- newly added prompts can be promoted when they are important entry points;
- search and copied prompt references remain stable;
- future ordering changes can be reviewed as a bounded display-policy change.

## Interaction polish

The Prompt Kit has additional browser guardrails around the tutorial workflow:

- Favorite, Open, and Copy live in one explicit prompt-card action rail. Desktop cards reserve space for the rail; mobile cards move the rail into its own touch-sized row. This prevents action buttons from occupying overlapping absolute positions.
- A successful copy produces both a green glowing confirmation toast and a brief green card flash. Reduced-motion preferences disable the movement while preserving visible confirmation.
- The four-phase rail and guided workflow panels use an animated current-to-next progression. Reduced-motion preferences preserve the structure and state while disabling movement.
- Workflow completion is intentionally session-scoped; it does not compete with Favorites, which remain persistent browser-local preferences.

## Tutorial-planning prompts

Three prompts cover different tutorial needs:

- **P18** creates durable tutorial and help content after the workflow is ready to teach.
- **P25** plans a known tutorial path and separates product, harness, or runtime prerequisites.
- **P64** surveys the repository, ranks all meaningful tutorial candidates, and emits tutorial sprint panels in recommended launch order.

Use P64 before P18 when the team has several possible tutorials and does not yet know which one deserves the first sprint.

## Validation and regeneration

From the repository root:

```powershell
python -m py_compile scripts/build_prompt_kit_registry.py scripts/validate_prompt_kit_discovery.py tests/test_prompt_kit_discovery.py tests/test_prompt_kit_guidance.py tests/test_skill_prompt_registry.py
node --check docs/prompt-kit.js
node --check docs/prompt-kit-guided-recommendations.js
node --check docs/prompt-kit-journey.js
node --check docs/prompt-kit-polish.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance tests.test_skill_prompt_registry -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
node scripts/analyze_prompt_finder_routes.js
```

## Proof ceiling

Repository validation can prove registry integrity, shared-search recommendation routing, registry-owned next-step extraction, session-only completion state, JavaScript syntax, action-rail structure, the four-phase Find → Use → Prove → Continue frame, generated-site parity, transitive route coverage, and focused test behavior. It does not prove every browser or assistive-technology combination, clipboard permissions on every device, organizational acceptance of the recommendations, or that a recommended prompt will succeed without the environment and permissions required by that prompt.
