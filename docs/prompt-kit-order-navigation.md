# Prompt Kit ordering and long-list navigation

The main Prompt Kit library uses stable numeric prompt sequence as its display order. Recommendation discovery rank remains metadata for the guided tutorial and does not replace the library sort.

## Ordering

- The unfiltered library displays prompt cards by numeric `seq`/P-number order.
- Search, category, type, color, and Favorites filtering preserve numeric sequence among the visible cards.
- Saving a prompt does not move it ahead of earlier prompts in the default library.
- Use the **★ Favorites** category control to view only saved prompts; that filtered view remains chronological.
- Stable prompt IDs and sequence values are never renumbered to achieve display order.

## Long-list navigation

The renderer counts visible prompt cards after filtering and section collapse state. After every five visible prompt cards, it renders a same-document navigation pair:

- **↑ Top** jumps to `#page-top`.
- **Bottom ↓** jumps to `#page-bottom`.

A final partial group also receives the pair, so navigation stays available even when the visible count is not divisible by five. Because the controls are constructed inside `render()`, every search, category, type, color, Favorites, save/remove, and other rerender recomputes navigation from the current visible prompt stream.

Distributed navigation links are native anchors and have at least a 40px touch target, with a 44px target in the mobile layout.

## Validation

```bash
python -m unittest tests.test_prompt_kit_order_navigation_product -v
python -m unittest tests.test_prompt_kit_order_navigation_contract -v
python scripts/validate_prompt_kit_order_navigation.py --require-implementation --output Outputs/prompt-kit-order-navigation-audit.json --summary
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html
python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check
git diff --check
```

The strict order/navigation gate is static/contract proof. Browser and physical mobile observation are still required to prove real scrolling ergonomics and touch behavior.
