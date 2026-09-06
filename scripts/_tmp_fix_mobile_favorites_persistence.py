from pathlib import Path


def replace_once(text, old, new, label):
    count=text.count(old)
    if count!=1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old,new,1)

polish_path=Path('docs/prompt-kit-polish.js')
polish=polish_path.read_text(encoding='utf-8')
polish=replace_once(
    polish,
    ".header-top>.header-controls .mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",
    ".header-top>.mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",
    'mobile Favorites always-visible selector',
)
polish=replace_once(
    polish,
    "    if(catTabs.parentNode)catTabs.parentNode.insertBefore(mobileFavoritesQuick,catTabs)\n",
    "    if(search)headerTop.insertBefore(mobileFavoritesQuick,search);else headerTop.appendChild(mobileFavoritesQuick)\n",
    'mobile Favorites insertion surface',
)
polish_path.write_text(polish,encoding='utf-8')

test_path=Path('tests/test_prompt_kit_mobile.py')
tests=test_path.read_text(encoding='utf-8')
tests=replace_once(
    tests,
    '            "catTabs.parentNode.insertBefore(mobileFavoritesQuick,catTabs)",\n',
    '            "if(search)headerTop.insertBefore(mobileFavoritesQuick,search);else headerTop.appendChild(mobileFavoritesQuick)",\n',
    'mobile test insertion marker',
)
tests=replace_once(
    tests,
    '            ".header-top>.header-controls .mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",\n',
    '            ".header-top>.mobile-favorites-quick{display:inline-flex;width:100%;grid-column:1/-1}",\n',
    'mobile test selector marker',
)
test_path.write_text(tests,encoding='utf-8')

browser_path=Path('tests/prompt_kit_favorite_browser_proof.py')
browser=browser_path.read_text(encoding='utf-8')
browser=replace_once(
    browser,
    "            quick_in_viewport = bool(\n                quick_rect\n                and quick_rect.get('x', -1) >= 0\n                and quick_rect.get('y', -1) >= 0\n                and quick_rect.get('x', 0) + quick_rect.get('width', 0) <= 390\n                and quick_rect.get('y', 0) + quick_rect.get('height', 0) <= 844\n            )\n            mobile_card = mobile_page.locator('[data-prompt-id=\"P79\"]')\n",
    "            quick_in_viewport = bool(\n                quick_rect\n                and quick_rect.get('x', -1) >= 0\n                and quick_rect.get('y', -1) >= 0\n                and quick_rect.get('x', 0) + quick_rect.get('width', 0) <= 390\n                and quick_rect.get('y', 0) + quick_rect.get('height', 0) <= 844\n            )\n            mobile_page.locator('#filterPanelToggle').click()\n            mobile_page.wait_for_timeout(80)\n            quick_visible_when_filters_collapsed = quick.is_visible()\n            mobile_card = mobile_page.locator('[data-prompt-id=\"P79\"]')\n",
    'browser collapsed-filter observation',
)
browser=replace_once(
    browser,
    "                    quick_in_viewport,\n                    favorite_view_active,\n",
    "                    quick_in_viewport,\n                    quick_visible_when_filters_collapsed,\n                    favorite_view_active,\n",
    'browser pass tuple',
)
browser=replace_once(
    browser,
    '                "quick_in_viewport": bool(quick_in_viewport),\n                "favorite_view_active": bool(favorite_view_active),\n',
    '                "quick_in_viewport": bool(quick_in_viewport),\n                "quick_visible_when_filters_collapsed": bool(quick_visible_when_filters_collapsed),\n                "favorite_view_active": bool(favorite_view_active),\n',
    'browser receipt field',
)
browser_path.write_text(browser,encoding='utf-8')

print('MOBILE_FAVORITES_PERSISTENCE_REPAIR=PASS')
