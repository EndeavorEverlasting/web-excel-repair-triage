# Professional Artifact Archetype + Design-System Prompt — execution plan

Date: 2026-09-24
Issue: #644
Branch: `feat/professional-artifact-archetype-builder`

## Objective

Graduate the staged professional-artifact candidate into the Prompt Kit through the protected P79 lifecycle, then strengthen P56 with a routing seam without changing P56's generic artifact ownership.

## Current committed candidate surfaces

- `harness/fixtures/prompt-contributions/professional-artifact-archetype-builder.draft.json`
- `harness/fixtures/prompt-contributions/professional-artifact-archetype-builder.regression-cases.json`
- `harness/fixtures/prompt-contributions/professional-artifact-archetype-builder.authoring-proof.json`
- `harness/fixtures/prompt-contributions/P56-professional-artifact-routing.patch.json`
- `harness/prompt-topology/PROFESSIONAL_ARTIFACT_ARCHETYPE_BUILDER_CANDIDATE.md`

These are staging/evidence surfaces, not canonical Prompt Kit registration.

## Dependency order

### M0 — refresh and executable floor

1. Refresh `main`, provider state, open PRs, and prompt-registry floor.
2. Verify this candidate package still applies without conflicting Prompt Kit changes.
3. Run:
   ```bash
   python scripts/prompt_registry_ops.py inspect
   python scripts/prompt_registry_ops.py validate
   ```
4. If Prompt Kit has moved materially, reconcile the candidate before lifecycle mutation.

Gate: current registry validates and candidate evidence remains applicable.

### M1 — official P79 registered-upstream prior art

Run the official all-source gate:

```bash
python scripts/prompt_registry_ops.py prior-art \
  --query "professional artifact archetype design system sign-off SOP ledger ticket tracker meeting notes reference fidelity prototype render cross-platform"
```

Require:
- `all_registered_sources_searched=true`;
- pinned floors for every registered source;
- current internal best-match evidence;
- a non-empty distinct residual.

If the official receipt proves an existing owner covers the candidate, stop ADD and strengthen that owner instead.

Gate: official prior-art receipt supports a distinct residual.

### M2 — protected ADD dry-run

```bash
python scripts/prompt_registry_ops.py add \
  --input harness/fixtures/prompt-contributions/professional-artifact-archetype-builder.draft.json \
  --registry spec-architecture-prompts \
  --dry-run
```

Inspect:
- allocated candidate identity;
- target registry;
- semantic profile preview;
- PSC008 residual result;
- registered external prior-art receipt;
- tutorial coverage route;
- no protected-history violation.

Gate: dry-run is green without validator weakening.

### M3 — protected ADD

Run the same ADD without `--dry-run`.

Require the helper to own:
- ID/seq/copySheet allocation;
- canonical registry write;
- ACCEPTED semantic profile;
- semantic capability migration;
- quality/source-history migration;
- generated-site rebuild;
- rollback if validation fails.

Gate: ADD receipt reports site parity and accepted prompt identity.

### M4 — P56 protected routing edit

After the new prompt ID is known, review the staged P56 patch. If routing by name is insufficient for current Prompt Kit discovery, update the candidate patch to include the newly allocated P-number.

Then:

```bash
python scripts/prompt_registry_ops.py edit \
  --prompt-id P56 \
  --input harness/fixtures/prompt-contributions/P56-professional-artifact-routing.patch.json \
  --disposition NO_CAPABILITY_CHANGE \
  --evidence-ref issue:#644 \
  --rationale "Route professional artifact archetype/design-system fidelity to the new specialist while preserving P56 generic artifact ownership."
```

If semantic review proves this is stronger than a routing-only change, use the helper-prescribed disposition rather than forcing `NO_CAPABILITY_CHANGE`.

Gate: P56 remains the generic artifact owner, new prompt is discoverable for the specialist use case, and semantic/source-history migrations are valid.

### M5 — focused regression proof

Promote the staged regression cases into the closest repository-owned focused test form. At minimum prove:

- artifact medium and archetype are separate;
- sign-off/SOP/ledger/ticket/meeting/OTHER routing;
- favorite/index/mirror must resolve the actual exemplar;
- verified rendered appearance can outrank theme-inverted raw OOXML/headless palette;
- reference control precedes generic aesthetic lock and brand overlay;
- spreadsheet acceptance follows the declared runtime;
- first prototype cannot self-promote;
- reusable corrections backport before batch propagation;
- artifact link/path leads final handoff;
- P56 and sync owners remain non-duplicated.

Then run the repository's focused Prompt Kit semantic/source-history/classification/discovery tests selected from current truth.

Gate: all focused tests pass on the exact candidate.

### M6 — full Prompt Kit proof

Run:

```bash
python scripts/prompt_registry_ops.py validate
```

Plus current repository-mandated:
- prompt semantic coverage;
- quality/source-history checks;
- language/order/discovery checks;
- tutorial coverage;
- generated-site `--check`;
- patch hygiene;
- local evidence-integrity floor when hosted Actions are unavailable.

Gate: exact-head local required floor green; hosted provider gaps typed separately.

### M7 — integration

Refresh main again, verify review freshness, and integrate the exact green head under current repository policy.

After merge:
- read back canonical prompt registry entry;
- verify generated-site parity;
- update #644 with exact prompt ID, merge SHA, validation receipts, and any skipped hosted proof;
- remove/archive staging candidate files only if repository convention says the accepted helper output supersedes them. Preserve durable design rationale.

## Acceptance criteria for the new prompt

The canonical prompt must cause an agent to:

1. build the actual artifact;
2. classify **MEDIUM + PRIMARY/SECONDARY ARCHETYPE + DESIGN MODE**;
3. preserve functional semantics before aesthetics;
4. trace the actual reference/exemplar rather than stopping at a locator/index/mirror;
5. use rendered-authority precedence when themes disagree;
6. use **reference control -> generic aesthetic lock -> optional brand overlay**;
7. keep one semantic design language while using medium-native implementations;
8. apply artifact-specific structure for sign-off, SOP, ledger, ticket tracker, meeting notes, technician tutorial, field reference, and OTHER;
9. lock a stable acceptance rubric;
10. run tested prototype iterations and never promote an untested candidate;
11. render/open the actual artifact on the relevant target surfaces;
12. backport reusable formatting behavior to a generator/template/spec/profile before batch propagation when repository capability exists;
13. preserve stable artifact identity and avoid duplicate truth;
14. lead the final handoff with the actual artifact link/path.

## Proof ceiling at handoff

Current state: **COMMITTED CANDIDATE PACKAGE / AUTHORING STATIC ASSERTIONS PASS / PROTECTED P79 ADD NOT EXECUTED**.

The unproven gates are explicit:
- official all-registered-source prior-art receipt;
- protected ADD dry-run;
- protected ADD;
- P56 protected edit;
- focused repository tests;
- Prompt Kit validation;
- generated-site parity from the helper;
- exact-head integration.

Another agent can resume from M0 without reconstructing this conversation.
