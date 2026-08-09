# Prompt Kit Order and Long-List Navigation State

**As of:** 2026-08-08

**Repository:** `EndeavorEverlasting/web-excel-repair-triage`

**Harness contract:** `harness/contracts/prompt-kit-order-navigation.v1.json`

**Harness validator:** `scripts/validate_prompt_kit_order_navigation.py`

## Working harness surfaces

- The contract requires chronological numeric sequence as the default main-library order when no filter or explicit alternate sort is active.
- Filtered visible prompt sets must also retain numeric sequence order with gaps allowed and stable prompt IDs unchanged.
- Long-list navigation density is fixed at a maximum of five visible prompt cards between navigation opportunities.
- Each distributed navigation point must expose both Top and Bottom actions.
- Navigation placement must be recomputed from the current visible result set after every render so search, category, type, color, Favorites, and other filtering states cannot remove the guarantee.
- Mobile/coarse-pointer controls require at least a 40px touch target and must not clear filters when navigating.
- The normal harness gate validates the contract, records source evidence, writes `Outputs/prompt-kit-order-navigation-audit.json`, and exits successfully while a clearly classified product gap remains.
- The strict product gate uses `--require-implementation` and exits nonzero while any implementation finding remains.

## Fresh-agent route

1. Read `harness/contracts/prompt-kit-order-navigation.v1.json` to recover the exact ordering and navigation-density contract.
2. Run `python scripts/validate_prompt_kit_order_navigation.py --output Outputs/prompt-kit-order-navigation-audit.json --summary` to classify the current implementation without changing product code.
3. Run `python -m unittest tests.test_prompt_kit_order_navigation_contract -v` to prove the harness detector and mutation fixtures.
4. In a harness-only lane, stop product mutation at the explicit `needs-product-repair` boundary and preserve the audit as evidence.
5. In an authorized Prompt Kit product lane, run the same validator with `--require-implementation`, repair canonical behavior sources, rebuild `web/prompt-kit/index.html`, and require exact parity before browser/mobile observation.

## Observed product gaps

Current repository evidence shows the requested behavior is not yet implemented:

1. `registry/prompts/prompt-display-order.v1.json` promotes `P65` first.
2. `scripts/build_prompt_kit_registry.py` applies the display-order policy to the combined prompt registry rather than keeping chronological sequence as the default library order.
3. `docs/prompt-kit-guided-recommendations.js` globally assigns `window.promptSequenceValue=rank` and rerenders, so recommendation discovery rank replaces normal numeric sequence ordering in the main library.
4. `docs/prompt-kit.js` provides Top/Bottom links on section/category dividers, but does not distribute navigation by visible prompt count. A long Favorites or filtered result set can therefore leave more than five prompt cards between navigation points.

These are **product implementation gaps**, not harness defects. This harness-only sprint must not repair those behavior sources or the generated site.

## Validation

Harness/contract proof:

```bash
python -m py_compile scripts/validate_prompt_kit_order_navigation.py tests/test_prompt_kit_order_navigation_contract.py
python scripts/validate_prompt_kit_order_navigation.py --output Outputs/prompt-kit-order-navigation-audit.json --summary
python -m unittest tests.test_prompt_kit_order_navigation_contract -v
python scripts/validate_harness.py --report Outputs/harness-completeness-report.json
python -m unittest tests.test_harness_contract -v
git diff --check
```

Strict product acceptance gate for the subsequent product lane:

```bash
python scripts/validate_prompt_kit_order_navigation.py --require-implementation --output Outputs/prompt-kit-order-navigation-audit.json --summary
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
```

The strict gate is expected to fail until the product implementation is repaired.

## Product-lane completion gate

A product implementation may close this gap only when all of the following are true:

- unfiltered main-library ordering begins at the lowest numeric prompt sequence rather than P65/discovery rank;
- recommendation ranking remains available inside the recommendation feature without globally replacing library chronology;
- all filtered result sets stay numeric-sequence ascending;
- both Top and Bottom controls occur at least once in every chunk of five visible prompt cards, including the final partial chunk;
- the same density survives search, category, type, color, Favorites, and other filtering rerenders;
- mobile/coarse-pointer touch targets remain at least 40px;
- navigation does not clear active filters;
- exact generated Prompt Kit parity passes;
- browser/mobile observation confirms the controls are actually usable and sensibly distributed.

## Proof ceiling

This report plus the non-strict validator establishes contract proof and static evidence of the current gap. It does not establish product implementation, browser scrolling behavior, touch ergonomics, focus behavior, or physical mobile acceptance. Those require the strict product gate followed by browser/device observation.
