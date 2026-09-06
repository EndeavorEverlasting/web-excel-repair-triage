from __future__ import annotations

from pathlib import Path
import json


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


polish_path = Path("docs/prompt-kit-polish.js")
polish = polish_path.read_text(encoding="utf-8")

polish = replace_once(
    polish,
    ".header.filters-collapsed .filter-panel-toggle{justify-self:end;margin-left:0}@keyframes",
    ".header.filters-collapsed .filter-panel-toggle{justify-self:end;margin-left:0}.mobile-favorites-quick{display:none;align-items:center;justify-content:center;min-height:44px;padding:8px 12px;border:1px solid rgba(245,158,11,.45);border-radius:8px;background:rgba(245,158,11,.08);color:#fbbf24;font-size:12px;font-weight:800;letter-spacing:.02em;cursor:pointer;touch-action:manipulation}.mobile-favorites-quick:hover,.mobile-favorites-quick:focus-visible{outline:none;border-color:#f59e0b;box-shadow:0 0 0 2px rgba(245,158,11,.18)}@keyframes",
    "mobile Favorites base styles",
)

polish = replace_once(
    polish,
    ".header-top>.header-controls .stats{justify-content:center}.header.filters-collapsed .header-top{grid-template-columns:minmax(0,1fr) auto}}",
    ".header-top>.header-controls .stats{justify-content:center}.header-top>.header-controls .mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}.header.filters-collapsed .header-top{grid-template-columns:minmax(0,1fr) auto}}",
    "mobile Favorites responsive styles",
)

controls_anchor = "  if(!document.getElementById('favoritesShortcut')){\n    var favoritesButton=document.createElement('button');"
quick_block = """  if(!document.getElementById('mobileFavoritesQuick')){
    var mobileFavoritesQuick=document.createElement('button');
    mobileFavoritesQuick.className='mobile-favorites-quick';
    mobileFavoritesQuick.id='mobileFavoritesQuick';
    mobileFavoritesQuick.type='button';
    mobileFavoritesQuick.setAttribute('data-view','favorites');
    mobileFavoritesQuick.setAttribute('aria-label','Open saved favorite prompts');
    mobileFavoritesQuick.textContent='★ Favorites';
    mobileFavoritesQuick.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();activateFavoritesView()});
    if(catTabs.parentNode)catTabs.parentNode.insertBefore(mobileFavoritesQuick,catTabs)
  }

"""
polish = replace_once(polish, controls_anchor, quick_block + controls_anchor, "mobile Favorites control")
polish_path.write_text(polish, encoding="utf-8")

contract_path = Path("harness/contracts/prompt-kit-mobile.v1.json")
contract = json.loads(contract_path.read_text(encoding="utf-8"))
ids = [item.get("id") for item in contract.get("requirements", [])]
if "favorites_quick_access" in ids:
    raise SystemExit("favorites_quick_access already exists; temporary patcher is stale")
insert_at = ids.index("touch_copy_preserved") + 1
contract["requirements"].insert(
    insert_at,
    {
        "id": "favorites_quick_access",
        "expected": "On narrow mobile layouts, a persistent touch-sized Favorites quick action remains visible outside horizontally scrollable rails and opens the existing canonical Favorites view without creating separate Favorites state or storage.",
    },
)
contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

test_path = Path("tests/test_prompt_kit_mobile.py")
tests = test_path.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    'JS = ROOT / "docs" / "prompt-kit.js"\n',
    'JS = ROOT / "docs" / "prompt-kit.js"\nPOLISH = ROOT / "docs" / "prompt-kit-polish.js"\n',
    "mobile test POLISH path",
)
tests = replace_once(
    tests,
    '                "touch_copy_preserved",\n',
    '                "touch_copy_preserved",\n                "favorites_quick_access",\n',
    "mobile requirement set",
)
next_test = "    def test_category_collapse_control_is_touch_sized_and_native(self) -> None:\n"
regression = '''    def test_mobile_favorites_quick_action_is_persistent_and_reuses_canonical_view(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "id='mobileFavoritesQuick'",
            "className='mobile-favorites-quick'",
            "setAttribute('data-view','favorites')",
            "setAttribute('aria-label','Open saved favorite prompts')",
            "textContent='★ Favorites'",
            "activateFavoritesView()",
            "catTabs.parentNode.insertBefore(mobileFavoritesQuick,catTabs)",
            ".mobile-favorites-quick{display:none",
            ".header-top>.header-controls .mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",
        ):
            self.assertIn(marker, polish)
        self.assertEqual(polish.count("id='mobileFavoritesQuick'"), 1)
        self.assertNotIn("mobileFavoritePromptIds", polish)
        self.assertNotIn("mobileFavoritesStorage", polish)

'''
tests = replace_once(tests, next_test, regression + next_test, "mobile regression insertion")
test_path.write_text(tests, encoding="utf-8")

browser_path = Path("tests/prompt_kit_favorite_browser_proof.py")
browser = browser_path.read_text(encoding="utf-8")
mobile_scenario = '''            mobile_context = browser.new_context(
                viewport={"width": 390, "height": 844},
                is_mobile=True,
                has_touch=True,
                reduced_motion="reduce",
            )
            mobile_page = mobile_context.new_page()
            mobile_page.goto(f"http://127.0.0.1:{port}/web/prompt-kit/index.html", wait_until="domcontentloaded")
            quick = mobile_page.locator('#mobileFavoritesQuick')
            quick_visible = quick.is_visible()
            quick_rect = quick.bounding_box() or {}
            quick_in_viewport = bool(
                quick_rect
                and quick_rect.get('x', -1) >= 0
                and quick_rect.get('y', -1) >= 0
                and quick_rect.get('x', 0) + quick_rect.get('width', 0) <= 390
                and quick_rect.get('y', 0) + quick_rect.get('height', 0) <= 844
            )
            mobile_card = mobile_page.locator('[data-prompt-id="P79"]')
            mobile_card.locator('.prompt-favorite-btn').click()
            mobile_page.wait_for_timeout(80)
            quick.click()
            mobile_page.wait_for_timeout(100)
            favorite_view_active = mobile_page.evaluate("activeSection === '__favorites__'")
            favorite_card_present = mobile_page.locator('[data-prompt-id="P79"]').count() == 1
            showing_favorite = mobile_page.locator('#showing').inner_text() == '1'
            mobile_page.locator('[data-prompt-id="P79"] .prompt-favorite-btn').click()
            mobile_page.wait_for_timeout(100)
            removed_from_view = (
                mobile_page.locator('[data-prompt-id="P79"]').count() == 0
                and mobile_page.locator('#showing').inner_text() == '0'
            )
            quick_still_visible = quick.is_visible()
            mobile_page.locator('#homeReset').click()
            mobile_page.wait_for_timeout(100)
            returned_to_all = (
                mobile_page.evaluate("activeSection === null && activeCat === 'all'")
                and mobile_page.locator('[data-prompt-id="P79"]').count() == 1
            )
            observations.append({
                "id": "mobile_favorites_quick_access",
                "event": "Mobile Favorites quick action stays visible outside scroll rails and reuses canonical Favorites state",
                "occurred": True,
                "passed": bool(all((
                    quick_visible,
                    quick_in_viewport,
                    favorite_view_active,
                    favorite_card_present,
                    showing_favorite,
                    removed_from_view,
                    quick_still_visible,
                    returned_to_all,
                ))),
                "quick_visible": bool(quick_visible),
                "quick_in_viewport": bool(quick_in_viewport),
                "favorite_view_active": bool(favorite_view_active),
                "favorite_card_present": bool(favorite_card_present),
                "showing_favorite": bool(showing_favorite),
                "removed_from_view": bool(removed_from_view),
                "quick_still_visible": bool(quick_still_visible),
                "returned_to_all": bool(returned_to_all),
                "viewport": {"width": 390, "height": 844},
            })
            mobile_context.close()

'''
browser = replace_once(browser, "            browser.close()\n", mobile_scenario + "            browser.close()\n", "browser mobile scenario")
claim_anchor = '        "claims": [\n'
claim = '            {"id": "mobile_favorites_quick_access", "statement": "A phone-width viewport exposes a persistent Favorites quick action outside horizontal rails; saving, opening Favorites, removing, and returning to All reuse the canonical Favorites state", "status": "PASS" if by_id["mobile_favorites_quick_access"]["passed"] else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["mobile_favorites_quick_access"]},\n'
browser = replace_once(browser, claim_anchor, claim_anchor + claim, "browser mobile claim")
browser_path.write_text(browser, encoding="utf-8")

print("MOBILE_FAVORITES_PATCH_APPLIED=PASS")
