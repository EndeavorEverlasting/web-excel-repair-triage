from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TEST = ROOT / "tests/test_ux_design_prompt_suite.py"

payload = json.loads(SPEC.read_text(encoding="utf-8"))
p110 = next((p for p in payload["prompts"] if p.get("id") == "P110"), None)
if p110 is None:
    raise SystemExit("P110 not found")

orientation_heading = "2B. STABILIZE MOBILE PORTRAIT + LANDSCAPE TO A BOUNDED FIXED POINT"
if orientation_heading not in p110["copyContent"]:
    anchor = "\n\n3. AUTOMATE WHAT CAN BE PROVEN DETERMINISTICALLY"
    if anchor not in p110["copyContent"]:
        raise SystemExit("P110 section-3 anchor not found")
    block = (
        "\n\n2B. STABILIZE MOBILE PORTRAIT + LANDSCAPE TO A BOUNDED FIXED POINT"
        "\nWhen phone/tablet support includes both orientations, exercise the same representative journey as "
        "PORTRAIT -> LANDSCAPE -> PORTRAIT. Rotate/resize without reloading or resetting product state unless the product contract requires it. "
        "Record orientation, viewport, active state, defect, shared owner, repair, and rerun. Fix the shared layout/state owner first; do not fix portrait by breaking landscape or stack orientation-only overrides without evidence. "
        "After every repair rerun the failing orientation, the opposite orientation, and the transition between them. Continue until at least one full orientation cycle after the final repair exposes no practical in-scope defect and protected adjacent controls remain green. "
        "If physical rotation is unavailable, keep safe-area, software-keyboard, browser-chrome, and real-device rotation feel explicitly unproven."
    )
    p110["copyContent"] = p110["copyContent"].replace(anchor, block + anchor, 1)

append_fields = {
    "useWhen": " It specifically owns iterative mobile stabilization when portrait and landscape are both supported and rotation repeatedly exposes layout, reachability, focus, viewport, or state regressions.",
    "inspectFirst": " For orientation-sensitive mobile work, include declared portrait/landscape dimensions or device classes, rotation/resize behavior, safe-area/dynamic-viewport constraints, and whether application state is expected to survive orientation changes.",
    "expectedOutput": " For portrait/landscape stabilization, include an orientation convergence ledger and exact-head proof of a clean portrait -> landscape -> portrait cycle after the final repair, with any physical-device-only claims left below the proof ceiling.",
    "proofGate": " When both mobile orientations are supported, no portrait-only repair may regress landscape (or vice versa), and acceptance requires at least one clean portrait -> landscape -> portrait cycle after the final repair on the strongest available runtime evidence.",
}
for field, suffix in append_fields.items():
    if suffix.strip() not in p110[field]:
        p110[field] += suffix

p110["nextStep"] = (
    "Run the highest-risk representative journey through the supported viewport/input matrix using the repository's existing browser/layout harness when available. "
    "When mobile portrait and landscape are both supported, run portrait -> landscape -> portrait without an artificial reset, repair the first real overlap/focus/state/responsive defect, then rerun the failing orientation, the opposite orientation, the rotation transition, and impacted protected controls until one full post-repair cycle is clean before broadening the matrix."
)

for keyword in (
    "portrait ux",
    "landscape ux",
    "portrait landscape",
    "mobile orientation",
    "orientation change",
    "screen rotation",
    "rotation regression",
    "responsive stability",
):
    if keyword not in p110["keywords"]:
        p110["keywords"].append(keyword)

if len(p110["copyContent"]) >= 8000:
    raise SystemExit(f"P110 copyContent exceeded bounded prompt contract: {len(p110['copyContent'])}")

SPEC.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_text = TEST.read_text(encoding="utf-8")
phrase_anchor = '            "exact head",\n'
phrase_insert = (
    '            "STABILIZE MOBILE PORTRAIT + LANDSCAPE TO A BOUNDED FIXED POINT",\n'
    '            "PORTRAIT -> LANDSCAPE -> PORTRAIT",\n'
    '            "do not fix portrait by breaking landscape",\n'
    '            "one full orientation cycle after the final repair",\n'
)
if '"STABILIZE MOBILE PORTRAIT + LANDSCAPE TO A BOUNDED FIXED POINT"' not in test_text:
    if phrase_anchor not in test_text:
        raise SystemExit("focused P110 phrase assertion anchor not found")
    test_text = test_text.replace(phrase_anchor, phrase_anchor + phrase_insert, 1)

keyword_anchor = '        self.assertIn("40px", content)\n'
keyword_insert = (
    '        for keyword in ("portrait ux", "landscape ux", "portrait landscape", "mobile orientation", "orientation change", "screen rotation", "rotation regression", "responsive stability"):\n'
    '            self.assertIn(keyword, prompt["keywords"])\n'
)
if '"rotation regression", "responsive stability"' not in test_text:
    if keyword_anchor not in test_text:
        raise SystemExit("focused P110 keyword assertion anchor not found")
    test_text = test_text.replace(keyword_anchor, keyword_anchor + keyword_insert, 1)

TEST.write_text(test_text, encoding="utf-8")

print(json.dumps({
    "prompt": p110["id"],
    "name": p110["name"],
    "copy_content_chars": len(p110["copyContent"]),
    "orientation_heading": orientation_heading in p110["copyContent"],
    "keywords_added": [k for k in p110["keywords"] if k in {
        "portrait ux", "landscape ux", "portrait landscape", "mobile orientation",
        "orientation change", "screen rotation", "rotation regression", "responsive stability"
    }],
}, indent=2))
