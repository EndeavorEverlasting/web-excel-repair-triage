# Find the Right Prompt with the Prompt Finder

The Prompt Kit contains many specialized prompts. You do not need to know their IDs or scroll through the entire library before beginning work.

Use **Find My Prompt** to answer three short questions. The Prompt Kit then recommends one prompt to start with and, when useful, up to two follow-on prompts.

## Start the questionnaire

1. Open the generated Prompt Kit website at `web/prompt-kit/index.html`.
2. Select **Find My Prompt** in the header.
3. Answer each question based on the work in front of you:
   - what you are trying to accomplish;
   - what state the work is currently in;
   - how the work should be organized.
4. Review the **Primary recommendation** first.
5. Select **Open** to read the full prompt or **Copy** to place it on the clipboard.
6. Use a follow-on option only when its described gate becomes relevant.

The questionnaire does not invent new prompt text. Every result is resolved from the current combined prompt registry, so the name, content, and metadata shown are the same records used elsewhere in the Prompt Kit.

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

Recommendations are evidence-informed routing aids, not automatic authorization. Read the selected prompt's owned scope, forbidden scope, dependencies, and proof gate before using it.

## Conversational fallback

The website questionnaire is the fastest path. When the generated website cannot be opened, search for or copy **P65 — Guided Prompt Finder Questionnaire** into an AI chat.

P65 asks one question at a time, recommends one primary prompt and no more than two follow-ons, and explains why each prompt fits. It also refuses to fabricate prompt IDs that are not present in the supplied or current registry.

## Why prompt IDs did not change

Prompt IDs and `seq` values are stable identities used by documentation, search synonyms, tests, capabilities, and external references. The Prompt Kit now applies a separate `discoveryRank` from `registry/prompts/prompt-display-order.v1.json` to promote broadly useful entry points without renaming or renumbering established prompts.

This means:

- `P61` remains `P61`, even when it appears near the top of the Foundation section;
- newly added prompts can be promoted when they are important entry points;
- search and copied prompt references remain stable;
- future ordering changes can be reviewed as a bounded display-policy change.

## Tutorial-planning prompts

Three prompts cover different tutorial needs:

- **P18** creates durable tutorial and help content after the workflow is ready to teach.
- **P25** plans a known tutorial path and separates product, harness, or runtime prerequisites.
- **P64** surveys the repository, ranks all meaningful tutorial candidates, and emits tutorial sprint panels in recommended launch order.

Use P64 before P18 when the team has several possible tutorials and does not yet know which one deserves the first sprint.

## Validation and regeneration

From the repository root:

```powershell
python -m py_compile scripts/build_prompt_kit_registry.py scripts/validate_prompt_kit_discovery.py tests/test_prompt_kit_discovery.py tests/test_skill_prompt_registry.py
node --check docs/prompt-kit.js
node --check docs/prompt-kit-guided-recommendations.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/validate_prompt_kit_discovery.py --summary
python -m unittest tests.test_prompt_kit_discovery tests.test_skill_prompt_registry -v
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

## Proof ceiling

Repository validation can prove registry integrity, deterministic recommendation routing, JavaScript syntax, generated-site parity, and focused test behavior. It does not prove every browser or assistive-technology combination, organizational acceptance of the recommendations, or that a recommended prompt will succeed without the environment and permissions required by that prompt.
