from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one anchor, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


polish = ROOT / "docs" / "prompt-kit-polish.js"
replace_once(
    polish,
    "function mobilePromptJumpHasPrefix(promptId){\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  return catalog.some(function(item){return item&&typeof item.id==='string'&&item.id!==promptId&&item.id.indexOf(promptId)===0})\n}\n\nfunction setMobilePromptJumpOpen(open,restoreFocus){",
    "function mobilePromptJumpHasPrefix(promptId){\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  return catalog.some(function(item){return item&&typeof item.id==='string'&&item.id!==promptId&&item.id.indexOf(promptId)===0})\n}\n\nfunction setMobilePromptJumpSubmitState(promptId,exact,longer){\n  var go=document.querySelector('#mobilePromptJumpForm .mobile-prompt-jump-go');\n  if(!go)return;\n  if(exact){\n    go.disabled=false;\n    go.textContent=longer?'Open '+promptId:'Go';\n    go.setAttribute('aria-label',longer?'Open exact '+promptId:'Open exact prompt ID')\n  }else{\n    go.disabled=true;\n    go.textContent='Go';\n    go.setAttribute('aria-label','Open exact prompt ID')\n  }\n}\n\nfunction setMobilePromptJumpOpen(open,restoreFocus){"
)
replace_once(
    polish,
    "    var status=document.getElementById('mobilePromptJumpStatus');\n    if(status)status.textContent='Type the digits after P. Example: 111.';\n    try{input.focus({preventScroll:true})}catch(e){input.focus()}",
    "    var status=document.getElementById('mobilePromptJumpStatus');\n    if(status)status.textContent='Type the digits after P. Example: 111.';\n    setMobilePromptJumpSubmitState('',false,false);\n    try{input.focus({preventScroll:true})}catch(e){input.focus()}"
)
replace_once(
    polish,
    "  if(!digits){if(status)status.textContent='Type the digits after P. Example: 111.';return false}\n  var promptId='P'+digits;\n  var prompt=mobilePromptJumpPrompt(promptId);\n  var longer=mobilePromptJumpHasPrefix(promptId);\n  if(prompt&&(!longer||force)){\n    setMobilePromptJumpOpen(false,false);\n    setHotkeyHelpOpen(false,false);\n    if(typeof window.showPromptDetail==='function'){\n      window.showPromptDetail(promptId,toggle||null);\n      return true\n    }\n    if(status)status.textContent='Prompt detail is unavailable.';\n    return false\n  }\n  if(prompt&&longer){if(status)status.textContent=promptId+' exists. Keep typing, or tap Go for '+promptId+'.';return false}\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  var hasCandidate=catalog.some(function(item){return item&&typeof item.id==='string'&&item.id.indexOf(promptId)===0});\n  if(status)status.textContent=hasCandidate?'Keep typing '+promptId+'…':'No prompt begins with '+promptId+'.';\n  return false",
    "  if(!digits){setMobilePromptJumpSubmitState('',false,false);if(status)status.textContent='Type the digits after P. Example: 111.';return false}\n  var promptId='P'+digits;\n  var prompt=mobilePromptJumpPrompt(promptId);\n  var longer=mobilePromptJumpHasPrefix(promptId);\n  if(prompt&&(!longer||force)){\n    setMobilePromptJumpSubmitState(promptId,true,longer);\n    setMobilePromptJumpOpen(false,false);\n    setHotkeyHelpOpen(false,false);\n    if(typeof window.showPromptDetail==='function'){\n      window.showPromptDetail(promptId,toggle||null);\n      return true\n    }\n    if(status)status.textContent='Prompt detail is unavailable.';\n    return false\n  }\n  if(prompt&&longer){\n    setMobilePromptJumpSubmitState(promptId,true,true);\n    if(status)status.textContent=promptId+' is exact. Press Enter or tap Open '+promptId+', or keep typing for a longer ID.';\n    return false\n  }\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  var hasCandidate=catalog.some(function(item){return item&&typeof item.id==='string'&&item.id.indexOf(promptId)===0});\n  setMobilePromptJumpSubmitState(promptId,false,false);\n  if(status)status.textContent=hasCandidate?'Keep typing '+promptId+'…':'No prompt starts with '+promptId+'.';\n  return false"
)
replace_once(
    polish,
    ".mobile-prompt-jump-go{min-width:52px;height:48px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font:800 12px/1 inherit}.mobile-prompt-jump-status",
    ".mobile-prompt-jump-go{min-width:52px;height:48px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font:800 12px/1 inherit}.mobile-prompt-jump-go:disabled{opacity:.45;cursor:not-allowed}.mobile-prompt-jump-status"
)
replace_once(
    polish,
    "  go.textContent='Go';\n  go.setAttribute('aria-label','Open exact prompt ID');",
    "  go.textContent='Go';\n  go.disabled=true;\n  go.setAttribute('aria-label','Open exact prompt ID');"
)

unit = ROOT / "tests" / "test_prompt_kit_mobile_quick_controls.py"
replace_once(
    unit,
    "            \"function mobilePromptJumpHasPrefix(promptId)\",\n            \"function resolveMobilePromptJump(force)\",",
    "            \"function mobilePromptJumpHasPrefix(promptId)\",\n            \"function setMobilePromptJumpSubmitState(promptId,exact,longer)\",\n            \"function resolveMobilePromptJump(force)\","
)
replace_once(
    unit,
    "    def test_prefix_collision_waits_but_unambiguous_exact_id_auto_opens(self) -> None:\n        source = POLISH.read_text(encoding=\"utf-8\")\n        self.assertIn(\"if(prompt&&(!longer||force))\", source)\n        self.assertIn(\"if(prompt&&longer){if(status)status.textContent=promptId+' exists. Keep typing, or tap Go for '+promptId+'.'\", source)\n        self.assertIn(\"hasCandidate?'Keep typing '+promptId+'…':'No prompt begins with '+promptId+'.'\", source)\n",
    "    def test_prefix_collision_requires_explicit_exact_confirmation_without_timing_race(self) -> None:\n        source = POLISH.read_text(encoding=\"utf-8\")\n        self.assertIn(\"if(prompt&&(!longer||force))\", source)\n        self.assertIn(\"go.textContent=longer?'Open '+promptId:'Go'\", source)\n        self.assertIn(\"promptId+' is exact. Press Enter or tap Open '+promptId+', or keep typing for a longer ID.'\", source)\n        self.assertIn(\"setMobilePromptJumpSubmitState(promptId,false,false)\", source)\n        self.assertIn(\"hasCandidate?'Keep typing '+promptId+'…':'No prompt starts with '+promptId+'.'\", source)\n        self.assertNotIn(\"setTimeout(function(){resolveMobilePromptJump\", source)\n"
)
replace_once(
    unit,
    "        for phrase in (\"Go to P#\", \"digits only\", \"P111\", \"without opening More\", \"browser Find\", \"not required\"):",
    "        for phrase in (\"Go to P#\", \"digits only\", \"P111\", \"P11\", \"Enter\", \"leading zero\", \"without opening More\", \"browser Find\", \"not required\"):"
)
replace_once(
    unit,
    "            \"Find in page\",\n        ):",
    "            \"Find in page\",\n            \"P11\",\n            \"press **Enter**\",\n            \"leading zero\",\n        ):"
)

browser = ROOT / "tests" / "prompt_kit_mobile_quick_controls_browser_proof.py"
replace_once(
    browser,
    "                # Prefix collision: P11 must not steal P111; explicit Go still opens exact P11 when requested.\n                jump.click()\n                inp.fill(\"11\")\n                inp.dispatch_event(\"input\")\n                page.wait_for_timeout(80)\n                assert not overlay.evaluate(\"el=>el.classList.contains('open')\"), \"P11 opened before the user resolved its P111 prefix collision\"\n                status = page.locator(\"#mobilePromptJumpStatus\").inner_text()\n                assert \"P11 exists\" in status and \"Keep typing\" in status, status\n                page.locator(\".mobile-prompt-jump-go\").click()\n                assert overlay.evaluate(\"el=>el.classList.contains('open')\"), \"explicit Go did not open exact P11\"\n                assert \"P11\" in page.locator(\"#promptDetail\").inner_text()\n                page.locator(\".prompt-detail-close\").click()\n",
    "                # Prefix collision: P11 must not steal P111, but Enter/submit is an obvious exact-ID choice.\n                jump.click()\n                inp.fill(\"11\")\n                page.wait_for_timeout(80)\n                assert not overlay.evaluate(\"el=>el.classList.contains('open')\"), \"P11 opened before the user resolved its P111 prefix collision\"\n                status = page.locator(\"#mobilePromptJumpStatus\").inner_text()\n                go = page.locator(\".mobile-prompt-jump-go\")\n                assert \"P11 is exact\" in status and \"Press Enter\" in status and \"keep typing\" in status.lower(), status\n                assert go.is_enabled(), \"exact ambiguous P11 should be explicitly submittable\"\n                assert go.inner_text() == \"Open P11\", go.inner_text()\n                inp.press(\"Enter\")\n                assert overlay.evaluate(\"el=>el.classList.contains('open')\"), \"Enter did not open exact P11\"\n                assert \"P11\" in page.locator(\"#promptDetail\").inner_text()\n                page.locator(\".prompt-detail-close\").click()\n\n                # Prefix-only input has no exact target, so submit stays disabled instead of pretending there is one.\n                jump.click()\n                inp.fill(\"1\")\n                page.wait_for_timeout(40)\n                assert not overlay.evaluate(\"el=>el.classList.contains('open')\")\n                assert page.locator(\".mobile-prompt-jump-go\").is_disabled()\n                assert \"Keep typing P1\" in page.locator(\"#mobilePromptJumpStatus\").inner_text()\n                set_open = page.evaluate(\"document.getElementById('mobilePromptJumpForm').hidden=false; document.getElementById('mobilePromptJumpToggle').setAttribute('aria-expanded','true'); true\")\n                assert set_open\n\n                # Canonical leading-zero IDs remain first-class (P01 is entered as 01).\n                inp.fill(\"01\")\n                page.wait_for_timeout(40)\n                assert overlay.evaluate(\"el=>el.classList.contains('open')\"), \"P01 did not open from leading-zero digits\"\n                assert \"P01\" in page.locator(\"#promptDetail\").inner_text()\n                page.locator(\".prompt-detail-close\").click()\n\n                # Pasted IDs are sanitized, while nonexistent IDs fail closed with no submit target.\n                jump.click()\n                inp.fill(\"P111\")\n                page.wait_for_timeout(40)\n                assert overlay.evaluate(\"el=>el.classList.contains('open')\"), \"pasted P111 was not sanitized to the known ID\"\n                page.locator(\".prompt-detail-close\").click()\n                jump.click()\n                inp.fill(\"999999\")\n                page.wait_for_timeout(40)\n                assert not overlay.evaluate(\"el=>el.classList.contains('open')\")\n                assert page.locator(\".mobile-prompt-jump-go\").is_disabled()\n                assert \"No prompt starts with P999999\" in page.locator(\"#mobilePromptJumpStatus\").inner_text()\n"
)
replace_once(
    browser,
    '                    "known_id": "P111",\n                    "direct_path": "tap Go to P# + type 111",',
    '                    "known_id": "P111",\n                    "edge_cases": ["P11-enter", "P1-prefix-only", "P01-leading-zero", "paste-P111", "P999999-missing"],\n                    "direct_path": "tap Go to P# + type 111",'
)

contract_path = ROOT / "harness" / "contracts" / "prompt-kit-mobile.v1.json"
contract = json.loads(contract_path.read_text(encoding="utf-8"))
req = next(item for item in contract["requirements"] if item["id"] == "mobile_prompt_id_jump")
req["expected"] = (
    "On narrow touch layouts, a persistent Go to P# control is the fastest route when the user already knows a prompt ID. "
    "The user taps Go to P#, enters digits only (for P111, type 111), and an exact unambiguous ID opens its canonical prompt detail automatically without opening More, swiping, browser Find, typing the P prefix, or tapping a search result. "
    "When an exact ID is also a prefix of a longer prompt ID (for example P11 versus P111), it must not auto-open and steal the longer route: the status explicitly says the shorter ID is exact, the submit control becomes Open P11, and Enter or that button deliberately opens P11 while continued typing can reach P111. "
    "Prefix-only or nonexistent IDs have no enabled exact-submit target; canonical P00-P09 IDs require their leading zero; pasted values such as P111 are safely normalized to the same digits-only resolver. "
    "A separate compact More control exposes Find Prompt, previous/next profile, Search, Favorites, Filters, Reference, Top, and Bottom as labeled buttons. Swiping is not required and no hidden gesture vocabulary is part of the primary phone interaction contract. Desktop Hotkeys and shared semantic actions remain authoritative; phone controls do not create parallel prompt state."
)
contract["proof_ceiling"] = contract["proof_ceiling"].replace(
    "including the P111 one-tap-plus-digits direct path.",
    "including the P111 one-tap-plus-digits direct path and the P11/P111, prefix-only, leading-zero, pasted-ID, and missing-ID edge-case matrix."
)
contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

guide = ROOT / "OPEN_PROMPT_KIT_ON_PHONE.md"
replace_once(
    guide,
    "If a shorter ID is also the start of a longer ID (for example `P11` and `P111`), the shorter one waits instead of stealing the route. Keep typing for the longer ID, or tap **Go** to deliberately open the shorter exact ID.\n",
    "If a shorter ID is also the start of a longer ID (for example `P11` and `P111`), the shorter one waits instead of stealing the route. For **P11**, type `11`; the button changes to **Open P11** and the status tells you the ID is exact. Press **Enter** (including the phone keyboard's Go/Enter key) or tap **Open P11** to open it, or keep typing `1` to continue to P111. There is no timing race.\n\nFor the zero-padded IDs `P00` through `P09`, keep the **leading zero**: type `00` for P00, `01` for P01, and so on. A prefix such as `1` that is not itself a canonical prompt stays in **Keep typing** state and cannot submit a fake exact target. A nonexistent number stays closed with a clear no-match message. Pasting `P111` is also safe: the control strips the `P` and resolves the same canonical ID.\n"
)

print("mobile ID edge-case source/tests/contract/docs updated")
