from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
MOBILE_TEST = ROOT / "tests" / "test_prompt_kit_mobile.py"
DIRECT_TEST = ROOT / "tests" / "test_prompt_kit_mobile_quick_controls.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


source = POLISH.read_text(encoding="utf-8")
source = replace_once(
    source,
    '<span class="mobile-quick-label">Quick Controls</span>',
    '<span class="mobile-quick-label">More</span>',
    "mobile More label",
)
source = replace_once(
    source,
    "  title.textContent='Quick controls & hotkeys';",
    "  title.innerHTML='<span class=\"hotkey-panel-title\">Hotkeys</span><span class=\"mobile-quick-panel-title\">More controls</span>';",
    "responsive panel title",
)
source = replace_once(
    source,
    ".mobile-quick-label{display:inline}.mobile-quick-handle-cue{display:none!important}}",
    ".mobile-quick-label{display:inline}.hotkey-panel-title{display:none}.mobile-quick-panel-title{display:inline}.hotkey-help-panel{width:min(340px,calc(100vw - 24px));max-height:min(460px,58vh)}.hotkey-help-list,.hotkey-shortcut-config,.prompt-profile-editor{display:none!important}.mobile-quick-handle-cue{display:none!important}}",
    "compact mobile More CSS",
)
POLISH.write_text(source, encoding="utf-8")

mobile_test = MOBILE_TEST.read_text(encoding="utf-8")
mobile_test = replace_once(
    mobile_test,
    '                "mobile_quick_controls_gesture_parity",',
    '                "mobile_prompt_id_jump",',
    "mobile contract requirement test",
)
MOBILE_TEST.write_text(mobile_test, encoding="utf-8")

direct_test = DIRECT_TEST.read_text(encoding="utf-8")
direct_test = direct_test.replace('"Chrome Find in page",', '"Find in page",')
lines = direct_test.splitlines()
more_lines = [i for i, line in enumerate(lines) if "mobile-quick-label" in line and "More" in line]
if len(more_lines) != 1:
    raise SystemExit(f"direct test More marker: expected one line, found {len(more_lines)}")
lines[more_lines[0]] = "            'mobile-quick-label\">More',"
direct_test = "\n".join(lines) + "\n"
# Add current-floor compactness markers beside the existing mobile hide assertion if absent.
if '".hotkey-help-panel{width:min(340px,calc(100vw - 24px));max-height:min(460px,58vh)}",' not in direct_test:
    hide = '            ".hotkey-help-list,.hotkey-shortcut-config,.prompt-profile-editor{display:none!important}",\n'
    if hide not in direct_test:
        raise SystemExit("direct test compact hide marker missing")
    direct_test = direct_test.replace(
        hide,
        '            ".hotkey-help-panel{width:min(340px,calc(100vw - 24px));max-height:min(460px,58vh)}",\n' + hide,
        1,
    )
DIRECT_TEST.write_text(direct_test, encoding="utf-8")

print("current-main direct-jump reconciliation applied")
