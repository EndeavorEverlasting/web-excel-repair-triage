# Find the Right Prompt with the Prompt Kit Tutorial

The Prompt Kit contains many specialized prompts. You do not need to know their IDs or scroll through the entire library before beginning work.

Use the glowing **Tutorial · Find My Prompt** control to answer three short context questions and one adaptive fourth question. The Prompt Kit then recommends one prompt to start with and up to two related options. If none of the adaptive choices fits, an optional fifth question exposes the full live prompt registry without requiring you to know prompt IDs. The questionnaire runs entirely in the generated page, does not send answers to a server, and does not retain them after the page is reset or closed.

## Start the questionnaire

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html` or the public Prompt Kit URL.
2. Select the glowing **Tutorial · Find My Prompt** control in the header.
3. Answer three compact context questions:
   - where you are starting, including no checkout, unfamiliar repo, known repo, active failure, open PR/review, or an app/artifact already open;
   - what you need to accomplish, with distinct choices for discovery, planning, coordination, repeated friction/urgency recovery, implementation, diagnosis, artifacts, proof, shipping, teaching, agent/harness work, management/correspondence, and closeout;
   - what proof/result level you actually need.
4. Use the adaptive fourth question to choose the closest current prompt route. Those choices are computed from the live registry and shared search evidence, not from a private prompt-ID table.
5. If none fits, choose **Something else — show every prompt**. The optional fifth question renders every current registry prompt and lets you filter the list with ordinary Prompt Kit search terms.
6. Review the **Primary recommendation** first.
7. Select **Open** to read the full prompt or **Copy** to place it on the clipboard.
8. Complete the current prompt's expected output or proof before moving through its registry-owned **Guided workflow**.

The default experience still ends after four questions. The fifth question exists as a coverage escape hatch, so newly added or highly specialized prompts remain reachable without making every user answer a longer questionnaire.

The finder does not maintain a second prompt-ID recommendation database. The first three answers contribute ordinary search phrases through `filterPromptsForQuery(PROMPTS, query)`, with overlapping evidence de-duplicated per question. The adaptive fourth question presents live registry records. The optional fifth question renders `PROMPTS` itself and uses the same shared search function only when you type a filter. This gives every current prompt a tutorial route while keeping prompt identity and semantics owned by the canonical registry.

## Use → prove → continue

The recommendation is a starting point, not the end of the tutorial. The current Prompt Kit restores the useful sequencing principle from the earlier spreadsheet-era Prompt Sequence while keeping the experience web-native.

When you open any prompt, its detail view includes a **Guided workflow** panel:

1. **Now** identifies the prompt you are about to use.
2. **Next-step contract** shows that prompt's current `nextStep` registry guidance.
3. **Ready to continue when** shows the prompt's registered expected output or proof gate.
4. **Next** or **Option** cards appear only for prompt IDs actually referenced by the current prompt's `nextStep` and present in the current registry.
5. **Open** lets you inspect the next prompt before committing to it; **Copy** copies that registered prompt directly.
6. **Mark this step complete** gives you lightweight session progress. Completion is stored only in browser `sessionStorage`; it is cleared with the browsing session and never changes the repository or your saved Favorites.
7. If the prompt has no explicit registered successor, use **Re-run Find My Prompt** after the current result changes your context.

This is deliberately not a new routing database. The browser reads the same `nextStep`, `expectedOutput`, `proofGate`, `useWhen`, IDs, and names already produced by the canonical prompt registry. Updating prompt guidance therefore remains a registry concern instead of requiring a second UI-specific sequence map.

The workflow rail uses subtle motion to make progression visible. Browsers requesting reduced motion receive the same structure and state without the movement. Mobile layouts keep the path horizontally readable and make the workflow actions touch-sized.

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
- Guided workflow panels use an animated current-to-next rail, distinct current/next states, and compact successor cards. Reduced-motion preferences preserve the structure while disabling movement.
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
```

## Proof ceiling

Repository validation can prove registry integrity, shared-search recommendation routing, registry-owned next-step extraction, session-only completion state, JavaScript syntax, action-rail structure, generated-site parity, and focused test behavior. It does not prove every browser or assistive-technology combination, clipboard permissions on every device, organizational acceptance of the recommendations, or that a recommended prompt will succeed without the environment and permissions required by that prompt.
