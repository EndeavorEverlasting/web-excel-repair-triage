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
2. **Enumerate only declared resource roots.** Read the resolved Git tree and select `SKILL.md` records under the registered root. Ignore caches, examples, notes, and unrelated repository files.
3. **Project metadata, not bodies.** Emit source ID, repository, pinned commit, skill slug/title, path, pinned GitHub URL, and bounded search terms. Do not embed donor instructions or prose in Operant's prompt registry or generated HTML.
4. **Compare against existing Operant owners first.** Use the deterministic coverage scorer against current prompt names/keywords and local skill titles. Prefer pointing users to an existing Operant prompt or skill when coverage clears the contract threshold.
5. **Keep external-only resources useful.** If no strong local owner exists, keep the upstream pinned resource directly discoverable as `POINT_TO_EXTERNAL` and record `REVIEW_ADD_PROMPT` in the maintenance ledger. External-only does not mean unavailable.
6. **Promote through the existing grounded prompt path.** P79 owns strengthen-before-add prompt contributions. A strategic owner reviews the gap evidence, donor license, real user task, and current registry before changing prompts. Never auto-copy or mechanically translate a donor skill into a new prompt.
7. **Preserve progressive disclosure.** The main Operant page embeds only the small resource runtime. It must not embed donor records and must not fetch `resources.v1.json` until the user explicitly opens Resources.
8. **Refresh regularly without bypassing review.** The scheduled workflow generates a current candidate snapshot and gap ledger as CI artifacts, compares them with tracked canonical projections, and signals drift. It never writes directly to the default branch.

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
node --check docs/prompt-kit-external-resources.js
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
git diff --check
```

## Proof ceiling

These checks prove registered-source resolution, commit-pinned metadata projection, deterministic coverage/gap routing, size budgets, lazy-load source semantics, and repository integration on the tested commit. They do not prove that every upstream skill is good, safe, license-compatible for reuse, successfully fetched in every browser, or deserving of a new Operant prompt.
