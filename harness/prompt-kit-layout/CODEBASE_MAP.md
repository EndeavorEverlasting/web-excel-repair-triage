# Prompt Kit responsive-layout harness map

## Purpose
This subordinate harness owns detection and workflow guidance for header/search/filter overlap regressions. It does not own the Prompt Kit product implementation.

## Relevant repository surfaces
- `web/prompt-kit/index.html` — canonical generated website artifact; product/runtime target, read-only for this sprint.
- `docs/prompt-kit.js` and related Prompt Kit runtime sources — behavior sources; read-only for this sprint.
- `harness/contracts/prompt-kit-mobile.v1.json` — existing mobile behavior contract; this layout harness complements it with collision-specific geometry requirements.
- `tests/test_prompt_kit_header_contract.py` and `tests/test_prompt_kit_mobile.py` — existing static product checks; useful evidence but not sufficient browser-geometry proof.
- `scripts/build_prompt_kit_registry.py` — canonical site builder/check command.

## Harness entry points
- `harness/prompt-kit-layout/manifest.v1.json` — complete component index.
- `harness/prompt-kit-layout/WORKFLOW.md` — task and handoff procedure.
- `scripts/validate_prompt_kit_layout_harness.py` — fail-closed harness completeness validator.
- `tests/test_prompt_kit_layout_harness.py` — contract regressions.
- `.github/workflows/prompt-kit-layout-harness.yml` — remote exact-head proof.

## Routing hook: hotkeys and keyboard shortcuts
If work mentions hotkeys, keyboard shortcuts, show/hide/toggle filters, favorite-prompt shortcuts, prompt-ID shortcuts, or examples such as `p95`, route first to `docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md` and then to the existing Prompt Kit runtime/test owners. Do not extend this layout harness or invent a second shortcut registry merely to implement keyboard behavior.

## Build / test / deploy commands
- Hotkey design seam: `node docs/prompt-kit-hotkey-prototype.js`
- Harness: `python scripts/validate_prompt_kit_layout_harness.py --summary`
- Contract tests: `python -m unittest tests.test_prompt_kit_layout_harness -v`
- Existing generated-site parity: `python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check`
- Existing header contract: `python tests/test_prompt_kit_header_contract.py`
- Existing mobile contract: `python -m unittest tests.test_prompt_kit_mobile -v`
- Patch hygiene: `git diff --check`
- Deployment remains the existing Prompt Kit Pages path; this harness does not deploy.

## Known trap
A static assertion that the search element exists or that a media query exists does not prove non-overlap. Product repair must eventually be certified with browser geometry at representative narrow, medium, and wide viewports.