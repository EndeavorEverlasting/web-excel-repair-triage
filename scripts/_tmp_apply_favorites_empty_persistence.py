from __future__ import annotations

from pathlib import Path
import json


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


polish_path = Path('docs/prompt-kit-polish.js')
polish = polish_path.read_text(encoding='utf-8')

style_anchor = "function favoriteGroupJumpId(name,index){\n"
journey_styles = """function ensureFavoritesJourneyStyles(){
  if(document.getElementById('favorites-journey-styles'))return;
  var style=document.createElement('style');
  style.id='favorites-journey-styles';
  style.textContent='.favorites-empty-state{grid-column:1/-1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-height:220px;padding:28px 20px;border:1px dashed var(--border);border-radius:12px;background:var(--bg-surface);text-align:center}.favorites-empty-icon{font-size:30px;line-height:1;color:#fbbf24}.favorites-empty-title{margin:0;color:var(--text-primary);font-size:18px}.favorites-empty-copy{max-width:520px;margin:0;color:var(--text-secondary);font-size:12px;line-height:1.55}.favorites-empty-action{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:8px 14px;border:1px solid var(--accent);border-radius:8px;background:var(--accent-glow);color:var(--text-primary);font-size:12px;font-weight:800;cursor:pointer;touch-action:manipulation}.favorites-empty-action:hover,.favorites-empty-action:focus-visible{outline:none;box-shadow:0 0 0 2px var(--accent-glow)}@media(max-width:760px){.favorites-empty-state{min-height:190px;padding:24px 16px}.favorites-empty-action{width:100%;min-height:48px}}';
  document.head.appendChild(style)
}

function currentFavoritePromptCount(){
  return Object.keys(favoritePromptIds||{}).filter(function(id){return favoritePromptIds[id]===true}).length
}

function renderFavoritesEmptyState(grid){
  if(!grid||activeSection!=='__favorites__')return false;
  var savedCount=currentFavoritePromptCount();
  var state=document.createElement('section');
  state.id='favoritesEmptyState';
  state.className='favorites-empty-state';
  state.setAttribute('role','status');
  state.setAttribute('aria-live','polite');
  var icon=document.createElement('div');
  icon.className='favorites-empty-icon';
  icon.setAttribute('aria-hidden','true');
  icon.textContent='★';
  var title=document.createElement('h2');
  title.className='favorites-empty-title';
  var copy=document.createElement('p');
  copy.className='favorites-empty-copy';
  var action=document.createElement('button');
  action.className='favorites-empty-action';
  action.type='button';
  if(savedCount===0){
    state.setAttribute('data-empty-kind','none-saved');
    title.textContent='No Favorites yet';
    copy.textContent='Star any prompt to save it here. Your Favorites stay in this browser for quick return visits.';
    action.textContent='Browse all prompts';
    action.setAttribute('aria-label','Browse all prompts and choose Favorites');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else{
    state.setAttribute('data-empty-kind','filtered');
    title.textContent='No Favorites match these filters';
    copy.textContent='You still have saved Favorites. Clear the current search and prompt filters to show them again.';
    action.textContent='Clear Favorites filters';
    action.setAttribute('aria-label','Clear Favorites search and prompt filters');
    action.addEventListener('click',function(){clearTransientPromptFilters();renderTypes();render()})
  }
  state.appendChild(icon);
  state.appendChild(title);
  state.appendChild(copy);
  state.appendChild(action);
  grid.appendChild(state);
  return true
}

"""
polish = replace_once(polish, style_anchor, journey_styles + style_anchor, 'Favorites journey helpers')

old_empty = """  var existing=document.getElementById('favoritesGroupJumpNav');
  if(existing&&existing.parentNode)existing.parentNode.removeChild(existing);
  grid.querySelectorAll('.section-divider.favorite-group-jump-target').forEach(function(divider){divider.classList.remove('favorite-group-jump-target');divider.removeAttribute('id')});
  if(activeSection!=='__favorites__')return;
  var dividers=Array.prototype.slice.call(grid.querySelectorAll('.section-divider[data-category]'));
  if(!dividers.length)return;
"""
new_empty = """  var existing=document.getElementById('favoritesGroupJumpNav');
  if(existing&&existing.parentNode)existing.parentNode.removeChild(existing);
  var existingEmpty=document.getElementById('favoritesEmptyState');
  if(existingEmpty&&existingEmpty.parentNode)existingEmpty.parentNode.removeChild(existingEmpty);
  grid.querySelectorAll('.section-divider.favorite-group-jump-target').forEach(function(divider){divider.classList.remove('favorite-group-jump-target');divider.removeAttribute('id')});
  if(activeSection!=='__favorites__')return;
  var dividers=Array.prototype.slice.call(grid.querySelectorAll('.section-divider[data-category]'));
  if(!dividers.length){renderFavoritesEmptyState(grid);return}
"""
polish = replace_once(polish, old_empty, new_empty, 'Favorites empty-state hook')

init_anchor = "ensureFavoritesGroupJumpStyles();\nensureCompactBrowsingControls();"
init_replacement = "ensureFavoritesGroupJumpStyles();\nensureFavoritesJourneyStyles();\nensureCompactBrowsingControls();"
polish = replace_once(polish, init_anchor, init_replacement, 'Favorites journey style initialization')
polish_path.write_text(polish, encoding='utf-8')

contract_path = Path('harness/contracts/prompt-kit-mobile.v1.json')
contract = json.loads(contract_path.read_text(encoding='utf-8'))
ids = [item.get('id') for item in contract.get('requirements', [])]
if 'favorites_empty_state_and_persistence' in ids:
    raise SystemExit('favorites_empty_state_and_persistence already exists; patcher stale')
insert_at = ids.index('favorites_group_jump_navigation') + 1
contract['requirements'].insert(insert_at, {
    'id': 'favorites_empty_state_and_persistence',
    'expected': 'Favorites saved in the existing canonical browser storage survive a page reload. An empty Favorites view shows a touch-actionable explanation and Browse all prompts action; when saved Favorites exist but current filters hide them, the empty state instead offers Clear Favorites filters and restores the saved results without changing membership.'
})
contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')

test_path = Path('tests/test_prompt_kit_mobile.py')
tests = test_path.read_text(encoding='utf-8')
tests = replace_once(
    tests,
    '                "favorites_group_jump_navigation",\n',
    '                "favorites_group_jump_navigation",\n                "favorites_empty_state_and_persistence",\n',
    'mobile contract requirement set',
)
next_test = '    def test_category_collapse_control_is_touch_sized_and_native(self) -> None:\n'
regression = '''    def test_favorites_empty_state_reuses_canonical_membership_and_has_two_recovery_paths(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function renderFavoritesEmptyState(grid)",
            "currentFavoritePromptCount()",
            "state.id='favoritesEmptyState'",
            "state.setAttribute('data-empty-kind','none-saved')",
            "title.textContent='No Favorites yet'",
            "action.textContent='Browse all prompts'",
            "activateAllPromptsView()",
            "state.setAttribute('data-empty-kind','filtered')",
            "title.textContent='No Favorites match these filters'",
            "action.textContent='Clear Favorites filters'",
            "clearTransientPromptFilters();renderTypes();render()",
            "if(!dividers.length){renderFavoritesEmptyState(grid);return}",
            "ensureFavoritesJourneyStyles();",
        ):
            self.assertIn(marker, polish)
        self.assertIn("favoritePromptIds", polish)
        self.assertNotIn("favoritesEmptyStorage", polish)
        self.assertNotIn("favoritesSessionStorage", polish)

'''
tests = replace_once(tests, next_test, regression + next_test, 'Favorites empty-state regression')
test_path.write_text(tests, encoding='utf-8')

browser_path = Path('tests/prompt_kit_favorite_browser_proof.py')
browser = browser_path.read_text(encoding='utf-8')
insert_anchor = '''            observations.append({
                "id": "mobile_favorites_group_jump_navigation",
'''
journey = '''            persisted_after_reload = False
            persisted_group_count = 0
            empty_state_visible = False
            empty_state_kind = None
            browse_all_returned = False
            filtered_empty_visible = False
            filtered_empty_kind = None
            clear_filters_restored = False
            if structured_pair_available:
                mobile_page.reload(wait_until="domcontentloaded")
                mobile_page.wait_for_timeout(120)
                quick = mobile_page.locator('#mobileFavoritesQuick')
                quick.click()
                mobile_page.wait_for_timeout(120)
                persisted_after_reload = all(
                    mobile_page.locator(f'[data-prompt-id="{item["id"]}"]').count() == 1
                    for item in group_pair
                )
                persisted_group_count = mobile_page.locator('#favoritesGroupJumpNav .favorite-group-jump').count()
                for item in group_pair:
                    card = mobile_page.locator(f'[data-prompt-id="{item["id"]}"]')
                    if card.count():
                        card.locator('.prompt-favorite-btn').click()
                        mobile_page.wait_for_timeout(80)
                empty = mobile_page.locator('#favoritesEmptyState')
                empty_state_visible = empty.is_visible()
                empty_state_kind = empty.get_attribute('data-empty-kind')
                empty_title = empty.locator('.favorites-empty-title').inner_text() if empty_state_visible else ''
                browse = empty.get_by_role('button', name='Browse all prompts') if empty_state_visible else None
                if browse is not None:
                    browse.click()
                    mobile_page.wait_for_timeout(100)
                    browse_all_returned = mobile_page.evaluate("activeSection === null && activeCat === 'all'")

                p79 = mobile_page.locator('[data-prompt-id="P79"]')
                if p79.count():
                    p79.locator('.prompt-favorite-btn').click()
                    mobile_page.wait_for_timeout(80)
                quick = mobile_page.locator('#mobileFavoritesQuick')
                quick.click()
                mobile_page.wait_for_timeout(100)
                mobile_page.locator('#search').fill('definitely-no-favorite-match-xyz')
                mobile_page.wait_for_timeout(100)
                filtered_empty = mobile_page.locator('#favoritesEmptyState')
                filtered_empty_visible = filtered_empty.is_visible()
                filtered_empty_kind = filtered_empty.get_attribute('data-empty-kind')
                filtered_title = filtered_empty.locator('.favorites-empty-title').inner_text() if filtered_empty_visible else ''
                if filtered_empty_visible:
                    filtered_empty.get_by_role('button', name='Clear Favorites filters').click()
                    mobile_page.wait_for_timeout(100)
                    clear_filters_restored = (
                        mobile_page.locator('[data-prompt-id="P79"]').count() == 1
                        and mobile_page.locator('#search').input_value() == ''
                        and mobile_page.evaluate("activeSection === '__favorites__'")
                    )
            else:
                empty_title = ''
                filtered_title = ''

            observations.append({
                "id": "mobile_favorites_persistence_and_empty_state",
                "event": "Favorites persist across reload and empty states provide actionable recovery for zero saved and filtered-out saved prompts",
                "occurred": True,
                "passed": bool(all((
                    structured_pair_available,
                    persisted_after_reload,
                    persisted_group_count == 2,
                    empty_state_visible,
                    empty_state_kind == 'none-saved',
                    empty_title == 'No Favorites yet',
                    browse_all_returned,
                    filtered_empty_visible,
                    filtered_empty_kind == 'filtered',
                    filtered_title == 'No Favorites match these filters',
                    clear_filters_restored,
                ))),
                "persisted_after_reload": bool(persisted_after_reload),
                "persisted_group_count": persisted_group_count,
                "empty_state_visible": bool(empty_state_visible),
                "empty_state_kind": empty_state_kind,
                "empty_title": empty_title,
                "browse_all_returned": bool(browse_all_returned),
                "filtered_empty_visible": bool(filtered_empty_visible),
                "filtered_empty_kind": filtered_empty_kind,
                "filtered_title": filtered_title,
                "clear_filters_restored": bool(clear_filters_restored),
                "viewport": {"width": 390, "height": 844},
            })

'''
if browser.count(insert_anchor) != 1:
    raise SystemExit(f'browser journey anchor count={browser.count(insert_anchor)}')
browser = browser.replace(insert_anchor, journey + insert_anchor, 1)
claim_anchor = '        "claims": [\n'
claim = '            {"id": "mobile_favorites_persistence_and_empty_state", "statement": "Canonical Favorites survive page reload; zero-saved and filtered-empty Favorites states provide touch-actionable recovery without changing the storage model", "status": "PASS" if by_id["mobile_favorites_persistence_and_empty_state"]["passed"] else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["mobile_favorites_persistence_and_empty_state"]},\n'
browser = replace_once(browser, claim_anchor, claim_anchor + claim, 'browser persistence/empty claim')
browser_path.write_text(browser, encoding='utf-8')

print('FAVORITES_EMPTY_PERSISTENCE_PATCH_APPLIED=PASS')
