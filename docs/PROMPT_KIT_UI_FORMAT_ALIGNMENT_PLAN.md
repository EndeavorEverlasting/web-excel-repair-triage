# Prompt Kit UI Format Alignment Plan

**Status:** ACTIVE execution plan
**Branch:** `feat/prompt-kit-ui-format-alignment-20260915`
**Base floor:** `origin/main` @ `84e93779bb87ccd959bc82614785b4d61a960d14`
**Owner lane:** Prompt Kit UI format alignment
**Updated:** 2026-09-15

## Mission
No Prompt Kit control that modifies the live view may leave the formatting sequence. Catalog classes are required. Lazy unclassed or forbidden-class UI must be coerced into the deferred ledger and become PR fodder.

## Completed floor
1. Root cause: Storage used `className='btn'` / `modal-*` which do not exist in Prompt Kit CSS, while Resources neighbors use `operant-resource-button`.
2. Storage repaired to `operant-resource-button` + `prompt-storage-*` surface styles.
3. Contract `harness/contracts/prompt-kit-ui-format-alignment.v1.json` + ledger `harness/prompt-kit-ui-format-alignment/ledger.v1.json`.
4. Fail-closed validator `scripts/validate_prompt_kit_ui_format_alignment.py` with deferred coercion.
5. Journey classless guide buttons coerced onto `guide-action`.

## Successor phases
| Phase | Scope | Gate |
|---|---|---|
| 1 (this) | Storage repair + alignment gate + ledger + tests + regenerate site | Focused validators green; site parity |
| 2 | Sweep remaining parent-scoped buttons outside current scan set; expand catalog | Validator still green; deferred rows actionable |
| 3 | Optional live pixel neighbor proof for Storage vs Resources | Browser observation receipt |

## Owned / forbidden
- **Owned:** Storage lifecycle UI classes, alignment contract/ledger/validator/tests, journey guide-action class tokens, generated site rebuild, harness wiring, TRQ index row.
- **Forbidden:** Unrelated redesign, privacy/storage policy changes, force-push, hand-editing generated HTML without builder, weakening protected storage/header contracts.

## Validation / proof gates
1. `python scripts/validate_prompt_kit_ui_format_alignment.py --summary`
2. `python -m unittest tests.test_prompt_kit_ui_format_alignment -v`
3. `python -m unittest tests.test_prompt_kit_storage_lifecycle_runtime -v`
4. `python tests/test_prompt_kit_header_contract.py`
5. `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html` then `--check`
6. Live: open Prompt Kit and confirm Storage matches Resources chrome; Escape still closes dialog.

## Proof ceiling
Static + Node runtime + generated-site parity + optional local live header observation. No Pages deploy proof in this slice.

## Deferred work
- Broader button-template sweep beyond `scan_paths`.
- Optional visual regression screenshots for header utilities.
