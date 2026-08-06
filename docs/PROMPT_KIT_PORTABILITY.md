# Prompt Kit Portability Contract

This is the human-readable authority for portable Prompt Kit user state and the focused execution discipline that protects it.

## Surface

This contract belongs to the **Standard AI** Prompt Kit surface. It is not a Goodnight, Have Fun prompt or an overnight-autonomy contract.

## User-state portability

Favorites must survive a website upgrade even when the new Prompt Kit is opened from a different local file, browser profile, device, or deployed origin.

The website therefore provides two explicit controls:

- **Export Favorites** downloads a small JSON backup using schema `prompt-kit-favorites/v1`.
- **Import Favorites** validates and merges that backup into the current browser's Favorites.

Import is additive and deduplicating. It does not silently delete current Favorites. Prompt IDs that are unavailable in the current version remain stored so they can become visible again if a later version restores them. Imported content is parsed only as data and is never executed.

The current browser-local key remains `promptKit.favoritePromptIds.v1`. Legacy array backups and known older storage keys are migrated without replacing the portable JSON contract.

### Upgrade procedure

Before replacing a local Prompt Kit copy, clearing browser data, changing browser profiles, or moving to another device, the operator exports Favorites from the old site. After opening the upgraded site, the operator imports that JSON backup and verifies that the expected Favorites section is restored.

Every release must regenerate the standalone website through the canonical registry builder so the portability runtime is carried into the next version. A release that omits the runtime, export/import controls, schema validator, or focused tests is stale and must fail validation.

## Portable execution discipline

Every repository-writing sprint must name:

- repository;
- branch or worktree;
- PR or sprint;
- lane;
- owned scope;
- forbidden scope;
- expected artifacts;
- validation order.

The preferred executable loop is:

`request -> evidence review -> bounded decision -> repository/GitHub mutation -> artifacts -> validation -> report -> next decision`

Before mutation, resolve and enter the exact Git root and verify origin, branch, HEAD, and status. When the execution container cannot clone the repository, use the connected GitHub branch as the mutation surface and reconstruct only the relevant generator, validator, and focused tests locally. Report that lower proof ceiling explicitly.

## Repository and artifact rules

Search existing contracts, helpers, validators, generators, registries, output patterns, branches, and PRs before inventing. Preserve useful work before cleanup. Generate the actual artifact, inspect it, validate it, and record its path and hash when practical.

### Prompt Library workbook artifacts

For every prompt row:

- columns `B:O` link to the associated prompt tab and exact copy range while preserving displayed values;
- columns `A` and `P` remain reserved for sparse top/bottom navigation;
- choose the largest divisor among `10`, `5`, and `2` that evenly divides the prompt count;
- fail closed when no allowed cadence divides the prompt count.

### Sequential prompt routing

Use:

- `P03` for unknown repository intake and first action;
- `P06` for repository and PR cleanup;
- `P07` for general implementation;
- `P14` for broken PR repair;
- `P15` for merge or release;
- `P20` for a selected `Opportunity_Discovery` row;
- `P12` for closeout.

Task-specific prompt rules override generic closeout behavior.

## Implementation ownership

- Runtime behavior: `docs/prompt-kit-favorites-portability.js`
- Machine policy: `harness/contracts/prompt-kit-portability.v1.json`
- Builder: `scripts/build_prompt_kit_registry.py`
- Generated site: `web/prompt-kit/index.html`
- Validator: `scripts/validate_prompt_kit_portability.py`
- Tests: `tests/test_prompt_kit_portability.py`
- CI: `.github/workflows/prompt-kit-web.yml`

The canonical builder embeds the portability runtime into the standalone website. Generated HTML is never the primary editable source.

## Validation and proof ceiling

Repository validation proves schema, source, builder integration, generated-site parity, and focused behavior contracts. It does not by itself prove physical browser download dialogs, browser-profile transfer, mobile file-picking behavior, or cross-device operator acceptance. Those require observed browser proof.
