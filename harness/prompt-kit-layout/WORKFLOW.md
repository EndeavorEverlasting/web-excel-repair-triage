# Responsive layout workflow

## Trigger
Use this workflow when Prompt Kit branding, search, filters, version labels, header controls, or other toolbar elements overlap, clip, escape their container, or regress at a viewport size.

## Pick up the task
1. Read `AGENTS.md`, this manifest, the collision contract, current Prompt Kit header/mobile tests, and recent Prompt Kit PRs.
2. Preserve any dirty or separately owned checkout; use one isolated branch/worktree per writer.
3. Determine whether the requested lane is **harness-only** or **product repair**. Harness-only may record and validate the defect but must not edit product HTML/CSS/JS.
4. Capture viewport dimensions, affected elements, observed collision, and version/commit when known.

## Validate before commit
Run in order:
1. `python scripts/validate_prompt_kit_layout_harness.py --summary`
2. `python -m unittest tests.test_prompt_kit_layout_harness -v`
3. existing Prompt Kit checks applicable to any shared harness edits
4. `git diff --check`

For a later product-repair lane, additionally require a browser geometry probe that proves every declared viewport has zero forbidden intersections and no horizontal page overflow.

## Failure handling
- Missing harness component, duplicate viewport ID, invalid threshold, or unowned output path: stop and repair the harness.
- Known product overlap while in harness-only scope: keep `implementation_status=known_defect`, report the proof ceiling, and hand off to a product lane. Do not weaken the contract to obtain green CI.
- Browser geometry failure in a product lane: repair the canonical responsive layout source, regenerate only through the registered builder, rerun geometry plus existing header/mobile/product checks.

## Handoff
Report exact branch/commit, changed files, validator results, CI state, collision evidence, proof ceiling, and the next executable gate. A handoff must identify whether the remaining blocker is product-code authority, browser runtime, review/merge, or deployment.