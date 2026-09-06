from pathlib import Path
import json


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)

polish_path = Path('docs/prompt-kit-polish.js')
polish = polish_path.read_text(encoding='utf-8')

polish = replace_once(
    polish,
    "function currentFavoritePromptCount(){\n  return Object.keys(favoritePromptIds||{}).filter(function(id){return favoritePromptIds[id]===true}).length\n}\n",
    "function storedFavoritePromptCount(){\n  return Object.keys(favoritePromptIds||{}).filter(function(id){return favoritePromptIds[id]===true}).length\n}\n\nfunction currentFavoritePromptCount(){\n  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];\n  return catalog.filter(function(prompt){return prompt&&isFavoritePrompt(prompt.id)}).length\n}\n",
    'Favorites count helpers',
)

old_branch = """  var savedCount=currentFavoritePromptCount();
  var state=document.createElement('section');
"""
new_branch = """  var storedCount=storedFavoritePromptCount();
  var savedCount=currentFavoritePromptCount();
  var state=document.createElement('section');
"""
polish = replace_once(polish, old_branch, new_branch, 'Favorites stored/available counts')

old_cases = """  if(savedCount===0){
    state.setAttribute('data-empty-kind','none-saved');
    title.textContent='No Favorites yet';
    copy.textContent='Star any prompt to save it here. Your Favorites stay in this browser for quick return visits.';
    action.textContent='Browse all prompts';
    action.setAttribute('aria-label','Browse all prompts');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else{
    state.setAttribute('data-empty-kind','filtered');
    title.textContent='No Favorites match these filters';
    copy.textContent='You still have saved Favorites. Clear the current search and prompt filters to show them again.';
    action.textContent='Clear Favorites filters';
    action.setAttribute('aria-label','Clear Favorites filters');
    action.addEventListener('click',function(){clearTransientPromptFilters();renderTypes();render()})
  }
"""
new_cases = """  if(storedCount===0){
    state.setAttribute('data-empty-kind','none-saved');
    title.textContent='No Favorites yet';
    copy.textContent='Star any prompt to save it here. Your Favorites stay in this browser for quick return visits.';
    action.textContent='Browse all prompts';
    action.setAttribute('aria-label','Browse all prompts');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else if(savedCount===0){
    state.setAttribute('data-empty-kind','unavailable');
    title.textContent='Saved Favorites unavailable in this version';
    copy.textContent='This browser still remembers saved prompt IDs, but none exist in the current Prompt Kit registry. Your saved IDs are preserved for portability.';
    action.textContent='Browse current prompts';
    action.setAttribute('aria-label','Browse current prompts');
    action.addEventListener('click',function(){activateAllPromptsView()})
  }else{
    state.setAttribute('data-empty-kind','filtered');
    title.textContent='No Favorites match these filters';
    copy.textContent='You still have saved Favorites available in this version. Clear the current search and prompt filters to show them again.';
    action.textContent='Clear Favorites filters';
    action.setAttribute('aria-label','Clear Favorites filters');
    action.addEventListener('click',function(){clearTransientPromptFilters();renderTypes();render()})
  }
"""
polish = replace_once(polish, old_cases, new_cases, 'Favorites three-state empty classification')
polish_path.write_text(polish, encoding='utf-8')

contract_path = Path('harness/contracts/prompt-kit-mobile.v1.json')
contract = json.loads(contract_path.read_text(encoding='utf-8'))
for item in contract['requirements']:
    if item.get('id') == 'favorites_empty_state_and_persistence':
        item['expected'] = 'Favorites saved in the existing canonical browser storage survive a page reload. An empty Favorites view distinguishes: no saved IDs, saved IDs unavailable in the current prompt registry, and available saved Favorites hidden by current filters. Recovery actions must be useful for each state, unknown imported IDs remain preserved for portability, and clearing filters must never change membership.'
        break
else:
    raise SystemExit('favorites_empty_state_and_persistence requirement missing')
contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')

test_path = Path('tests/test_prompt_kit_mobile.py')
tests = test_path.read_text(encoding='utf-8')
tests = replace_once(
    tests,
    '            "currentFavoritePromptCount()",\n',
    '            "storedFavoritePromptCount()",\n            "currentFavoritePromptCount()",\n            "catalog.filter(function(prompt){return prompt&&isFavoritePrompt(prompt.id)}).length",\n',
    'Favorites count regression markers',
)
tests = replace_once(
    tests,
    '            "action.setAttribute(\'aria-label\',\'Browse all prompts\')",\n            "activateAllPromptsView()",\n',
    '            "action.setAttribute(\'aria-label\',\'Browse all prompts\')",\n            "state.setAttribute(\'data-empty-kind\',\'unavailable\')",\n            "title.textContent=\'Saved Favorites unavailable in this version\'",\n            "action.textContent=\'Browse current prompts\'",\n            "action.setAttribute(\'aria-label\',\'Browse current prompts\')",\n            "activateAllPromptsView()",\n',
    'Favorites unavailable-state deterministic markers',
)
test_path.write_text(tests, encoding='utf-8')

browser_path = Path('tests/prompt_kit_favorite_browser_proof.py')
browser = browser_path.read_text(encoding='utf-8')

anchor = """                if filtered_empty_visible:
                    filtered_empty.get_by_role('button', name='Clear Favorites filters').click()
                    mobile_page.wait_for_timeout(100)
                    clear_filters_restored = (
                        mobile_page.locator('[data-prompt-id=\"P79\"]').count() == 1
                        and mobile_page.locator('#search').input_value() == ''
                        and mobile_page.evaluate(\"activeSection === '__favorites__'\")
                    )
            else:
                empty_title = ''
                filtered_title = ''

            observations.append({
"""
replacement = """                if filtered_empty_visible:
                    filtered_empty.get_by_role('button', name='Clear Favorites filters').click()
                    mobile_page.wait_for_timeout(100)
                    clear_filters_restored = (
                        mobile_page.locator('[data-prompt-id=\"P79\"]').count() == 1
                        and mobile_page.locator('#search').input_value() == ''
                        and mobile_page.evaluate(\"activeSection === '__favorites__'\")
                    )

                mobile_page.evaluate(\"localStorage.setItem('promptKit.favoritePromptIds.v1', JSON.stringify(['P999999']))\")
                mobile_page.reload(wait_until=\"domcontentloaded\")
                mobile_page.wait_for_timeout(120)
                mobile_page.locator('#mobileFavoritesQuick').click()
                mobile_page.wait_for_timeout(100)
                unavailable_empty = mobile_page.locator('#favoritesEmptyState')
                unavailable_visible = unavailable_empty.is_visible()
                unavailable_kind = unavailable_empty.get_attribute('data-empty-kind')
                unavailable_title = unavailable_empty.locator('.favorites-empty-title').inner_text() if unavailable_visible else ''
                unavailable_action_visible = unavailable_empty.get_by_role('button', name='Browse current prompts').is_visible() if unavailable_visible else False
                unknown_id_preserved = mobile_page.evaluate(\"JSON.parse(localStorage.getItem('promptKit.favoritePromptIds.v1')||'[]').includes('P999999')\")
            else:
                empty_title = ''
                filtered_title = ''
                unavailable_visible = False
                unavailable_kind = None
                unavailable_title = ''
                unavailable_action_visible = False
                unknown_id_preserved = False

            observations.append({
"""
browser = replace_once(browser, anchor, replacement, 'browser stale Favorite scenario')

browser = replace_once(
    browser,
    "                    clear_filters_restored,\n                ))),\n",
    "                    clear_filters_restored,\n                    unavailable_visible,\n                    unavailable_kind == 'unavailable',\n                    unavailable_title == 'Saved Favorites unavailable in this version',\n                    unavailable_action_visible,\n                    unknown_id_preserved,\n                ))),\n",
    'browser persistence pass tuple',
)

browser = replace_once(
    browser,
    '                "clear_filters_restored": bool(clear_filters_restored),\n                "viewport": {"width": 390, "height": 844},\n',
    '                "clear_filters_restored": bool(clear_filters_restored),\n                "unavailable_visible": bool(unavailable_visible),\n                "unavailable_kind": unavailable_kind,\n                "unavailable_title": unavailable_title,\n                "unavailable_action_visible": bool(unavailable_action_visible),\n                "unknown_id_preserved": bool(unknown_id_preserved),\n                "viewport": {"width": 390, "height": 844},\n',
    'browser stale Favorite receipt fields',
)

browser = browser.replace(
    '"event": "Favorites persist across reload and empty states provide actionable recovery for zero saved and filtered-out saved prompts"',
    '"event": "Favorites persist across reload and empty states distinguish zero saved, unavailable saved IDs, and filtered-out available prompts"',
    1,
)
browser_path.write_text(browser, encoding='utf-8')

print('FAVORITES_STALE_ID_CLASSIFICATION_REPAIRED=PASS')
