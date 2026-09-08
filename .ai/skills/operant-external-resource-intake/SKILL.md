# Operant External Resource Intake

## Trigger

Use this skill when Operant should discover, refresh, expose, or evaluate reusable resources from approved public donor repositories, especially when a user asks whether a prompt/skill already exists upstream or when the scheduled donor-resource drift check reports movement.

This skill owns donor **resource discovery and coverage routing**. It does not make a donor repository authoritative for Operant and it does not copy donor skill bodies into the Prompt Kit.

## Required inputs

- `harness/contracts/operant-external-resource-intake.v1.json`;
- current Operant prompt registry and local `.ai/skills/*/SKILL.md` inventory;
- live public GitHub metadata for each registered donor source;
- exact donor default branch and resolved commit SHA.

## Outputs

- compact metadata-only `web/prompt-kit/resources.v1.json` projection;
- `registry/resources/operant-external-resource-gaps.v1.json` coverage/gap ledger;
- source commit receipts and deterministic counts;
- one disposition per resource: `POINT_TO_EXISTING_PROMPT`, `POINT_TO_EXISTING_SKILL`, or `POINT_TO_EXTERNAL`;
- `REVIEW_ADD_PROMPT` only when no deterministic internal coverage exists, routed to P79 rather than auto-authored.

## Procedure

1. **Refresh donor truth.** Resolve each registered public repository's actual default branch and current commit. Fail closed if the observed default branch differs from the registered expectation until the contract is deliberately reconciled.
2. **Enumerate by declared mode.**
   - `git_skill_tree`: read the resolved Git tree and select `SKILL.md` records under the registered root up to `max_depth` (nested category/slug trees are allowed when configured).
   - `catalog_csv`: pin the catalog file (for example `prompts.csv`), record entry count and license boundary in the source floor, and project **zero** per-row records into the public sidecar. Search large catalogs on demand with `python scripts/search_operant_external_catalog.py`.
3. **Project metadata, not bodies.** For skill donors, emit source ID, repository, pinned commit, skill slug/title, path, pinned GitHub URL, and bounded search terms. Do not embed donor instructions, CSV prompt bodies, `contentPreview`, or prose in Operant's prompt registry or generated HTML.
4. **Compare against existing Operant owners first.** Use the deterministic coverage scorer against current prompt names/keywords and local skill titles. Prefer pointing users to an existing Operant prompt or skill when coverage clears the contract threshold.
5. **Keep external-only skill resources useful.** If no strong local owner exists, keep the upstream pinned resource directly discoverable as `POINT_TO_EXTERNAL` and record `REVIEW_ADD_PROMPT` in the maintenance ledger. External-only does not mean unavailable.
6. **Promote through the existing grounded prompt path.** P79 owns strengthen-before-add prompt contributions. Before ADD, require registered external-source/catalog search, commonality extraction against current owners, and a distinct residual. `REVIEW_ADD_PROMPT` means candidate for that comparison, not permission to author. Never auto-copy or mechanically translate a donor skill/catalog row into a new prompt.
7. **Preserve progressive disclosure.** The main Operant page embeds only the small resource runtime. It must not embed donor records and must not fetch `resources.v1.json` until the user explicitly opens Resources.
8. **Refresh regularly without bypassing review.** The scheduled workflow generates a current candidate snapshot and gap ledger as CI artifacts, compares them with tracked canonical projections, and signals drift. It never writes directly to the default branch.

Registered donor floor (current contract):

- `deepseek-ai/deepseek-harness` — `.agents/skills/*/SKILL.md`
- `f/prompts.chat` — commit-pinned `prompts.csv` catalog searched on demand (CC0 prompt data / MIT source); not bulk-projected into the sidecar
- `mattpocock/skills` — nested `skills/<category>/<slug>/SKILL.md` (excluding `deprecated/`)

## Guardrails

- maximum entries, index bytes, search terms, and render page size come from the contract and fail closed;
- donor content never joins the `PROMPTS` array merely to make it searchable;
- the Resources panel renders a bounded page and filters the sidecar client-side only after explicit open;
- default page load performs zero resource-index requests;
- pinned URLs include the exact donor commit SHA;
- no credentials, private repositories, user-specific paths, or donor execution are required;
- a donor is evidence/reference until its behavior is separately adopted and proved under Operant ownership;
- license review is mandatory before copying or adapting donor content.

## Validation

```bash
python scripts/sync_operant_external_resources.py
python scripts/validate_operant_external_resources.py --summary
python -m unittest tests.test_operant_external_resources -v
python scripts/search_operant_external_catalog.py --live-proof --summary --receipt-output Outputs/operant-external-resources/catalog-search-live-proof.json
node --check docs/prompt-kit-external-resources.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

## Proof ceiling

These checks prove registered-source resolution, commit-pinned metadata projection, catalog floor-only receipts, deterministic coverage/gap routing, fixture catalog search, CI live catalog-search latency budget against the pinned SHA, size budgets, lazy-load source semantics, and repository integration on the tested commit. They do not prove that every upstream skill or catalog row is good, safe, license-compatible for reuse, successfully fetched in every browser, reachable through MCP, or deserving of a new Operant prompt.
