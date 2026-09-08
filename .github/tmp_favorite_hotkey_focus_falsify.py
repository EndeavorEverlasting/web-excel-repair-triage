from __future__ import annotations

from pathlib import Path

polish = Path("docs/prompt-kit-polish.js").read_text(encoding="utf-8")
html = Path("web/prompt-kit/index.html").read_text(encoding="utf-8")
contract = Path("harness/contracts/prompt-kit-mobile.v1.json").read_text(encoding="utf-8")
guide = Path("OPEN_PROMPT_KIT_ON_PHONE.md").read_text(encoding="utf-8")

checks = {
    "favorite-derived shortcuts": "var favorites=favoritePromptShortcutBindings();" in polish,
    "stale explicit binding gated": "if(isFavoritePrompt(promptId))merged[gesture]=promptId" in polish,
    "detail favorite": "function decoratePromptDetailFavorite(promptId)" in polish,
    "unique prompt card anchors": "data-favorite-prompt-id" in polish
    and ".prompt-detail-favorite-btn[data-prompt-id" not in polish,
    "direct jump is instant": "revealPromptShortcutTarget(promptId,'instant')" in polish,
    "detail opens after instant center": "centerRenderedPromptCard(id,'instant');" in polish,
    "ordinary hotkeys preserve motion policy": "centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())"
    in polish,
    "generated shortcut parity": "function favoritePromptShortcutBindings()" in html,
    "generated detail parity": "prompt-detail-favorite-btn" in html
    and "data-favorite-prompt-id" in html
    and "centerRenderedPromptCard(id,'instant');" in html,
    "mobile contract": "centered in the underlying Prompt Kit page" in contract
    and "without a second shortcut-save step" in contract,
    "operator guide": "reveals and centers P111" in guide
    and "automatically becomes its lower-case P-ID hotkey" in guide,
}

jump = polish[
    polish.index("function resolveMobilePromptJump") : polish.index("function installMobilePromptJump")
]
checks["Go to reveal before detail"] = jump.index(
    "revealPromptShortcutTarget(promptId,'instant')"
) < jump.index("window.showPromptDetail(promptId,toggle||null)")

failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit(f"second-pass falsification failed: {failed}")

print("second-pass fixed-point checks: PASS")
