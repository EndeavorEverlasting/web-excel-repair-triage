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

function_anchor = "function activateFavoritesView(){\n  activeCat='all';\n  activeSection='__favorites__';\n  clearTransientPromptFilters();\n  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.id==='favoritesShortcut')});\n  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__favorites__')});\n  render();\n}\n\n"
functions = """function ensureFavoritesGroupJumpStyles(){
  if(document.getElementById('favorites-group-jump-styles'))return;
  var style=document.createElement('style');
  style.id='favorites-group-jump-styles';
  style.textContent='.favorites-group-jump-nav{grid-column:1/-1;display:flex;align-items:center;gap:8px;max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;padding:4px 0 10px}.favorites-group-jump-nav::-webkit-scrollbar{display:none}.favorites-group-jump-label{flex:0 0 auto;color:var(--text-muted);font-size:10px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.favorite-group-jump{display:inline-flex;align-items:center;justify-content:center;flex:0 0 auto;min-height:38px;padding:7px 10px;border:1px solid var(--border);border-radius:999px;background:var(--bg-surface);color:var(--text-secondary);font-size:11px;font-weight:700;text-decoration:none;touch-action:manipulation}.favorite-group-jump:hover,.favorite-group-jump:focus-visible{outline:none;border-color:#f59e0b;color:#fbbf24;box-shadow:0 0 0 2px rgba(245,158,11,.16)}.section-divider.favorite-group-jump-target{scroll-margin-top:12px}@media(max-width:760px){.favorites-group-jump-nav{padding:2px 0 8px}.favorite-group-jump{min-height:44px;padding:8px 12px}}';
  document.head.appendChild(style)
}

function favoriteGroupJumpId(name,index){
  var slug=String(name||'group').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'group';
  return 'favorite-group-'+String(index+1)+'-'+slug
}

function renderFavoritesGroupJumpNavigation(){
  var grid=document.getElementById('grid');
  if(!grid)return;
  var existing=document.getElementById('favoritesGroupJumpNav');
  if(existing&&existing.parentNode)existing.parentNode.removeChild(existing);
  grid.querySelectorAll('.section-divider.favorite-group-jump-target').forEach(function(divider){divider.classList.remove('favorite-group-jump-target');divider.removeAttribute('id')});
  if(activeSection!=='__favorites__')return;
  var dividers=Array.prototype.slice.call(grid.querySelectorAll('.section-divider[data-category]'));
  if(!dividers.length)return;
  var nav=document.createElement('nav');
  nav.id='favoritesGroupJumpNav';
  nav.className='favorites-group-jump-nav';
  nav.setAttribute('aria-label','Saved favorite groups');
  var label=document.createElement('span');
  label.className='favorites-group-jump-label';
  label.textContent='Saved groups';
  nav.appendChild(label);
  dividers.forEach(function(divider,index){
    var name=divider.getAttribute('data-category')||'Group';
    var countNode=divider.querySelector('.sd-count');
    var countText=countNode?String(countNode.textContent||'').trim():'';
    var id=favoriteGroupJumpId(name,index);
    divider.id=id;
    divider.classList.add('favorite-group-jump-target');
    var link=document.createElement('a');
    link.className='favorite-group-jump';
    link.href='#'+id;
    link.setAttribute('data-favorite-group',name);
    link.setAttribute('aria-label','Jump to saved favorite group '+name+(countText?' · '+countText:''));
    link.textContent=name+(countText?' · '+countText:'');
    link.addEventListener('click',function(e){
      e.preventDefault();
      var target=document.getElementById(id);
      if(!target)return;
      try{target.scrollIntoView({block:'start',behavior:hotkeyScrollBehavior()})}catch(err){target.scrollIntoView(true)}
      var toggle=target.querySelector('.section-toggle');
      if(toggle){try{toggle.focus({preventScroll:true})}catch(err){toggle.focus()}}
    });
    nav.appendChild(link)
  });
  grid.insertBefore(nav,grid.firstChild)
}

function installFavoritesGroupJumpNavigation(){
  var baseRender=window.render;
  if(typeof baseRender!=='function'||baseRender.__favoritesGroupJumpWrapped)return false;
  var wrapped=function(){baseRender();renderFavoritesGroupJumpNavigation()};
  wrapped.__favoritesGroupJumpWrapped=true;
  window.render=wrapped;
  return true
}

"""
polish = replace_once(polish, function_anchor, function_anchor + functions, 'Favorites group jump functions')

init_anchor = "ensurePromptKitPolishStyles();\nensureCompactBrowsingControls();\nensureHotkeyHelp();\ninstallCompactBrowsingViewSwitches();\ninstallCompactBrowsingHotkeys();\nrender();"
init_replacement = "ensurePromptKitPolishStyles();\nensureFavoritesGroupJumpStyles();\nensureCompactBrowsingControls();\nensureHotkeyHelp();\ninstallCompactBrowsingViewSwitches();\ninstallCompactBrowsingHotkeys();\ninstallFavoritesGroupJumpNavigation();\nrender();"
polish = replace_once(polish, init_anchor, init_replacement, 'Favorites group jump init')
polish_path.write_text(polish, encoding='utf-8')

contract_path = Path('harness/contracts/prompt-kit-mobile.v1.json')
contract = json.loads(contract_path.read_text(encoding='utf-8'))
ids = [item.get('id') for item in contract.get('requirements', [])]
if 'favorites_group_jump_navigation' in ids:
    raise SystemExit('favorites_group_jump_navigation already exists; patcher stale')
insert_at = ids.index('favorites_quick_access') + 1
contract['requirements'].insert(insert_at, {
    'id': 'favorites_group_jump_navigation',
    'expected': 'When Favorites contains saved prompts in one or more existing prompt sections, the Favorites view exposes a compact touch-usable Saved groups navigator built from those existing rendered sections and counts. Activating a group jumps to that section without changing Favorites membership, creating collection state, or using browser Find.'
})
contract_path.write_text(json.dumps(contract, indent=2) + '\n', encoding='utf-8')

test_path = Path('tests/test_prompt_kit_mobile.py')
tests = test_path.read_text(encoding='utf-8')
tests = replace_once(
    tests,
    '                "favorites_quick_access",\n',
    '                "favorites_quick_access",\n                "favorites_group_jump_navigation",\n',
    'mobile contract requirement set',
)
next_test = '    def test_category_collapse_control_is_touch_sized_and_native(self) -> None:\n'
regression = '''    def test_favorites_group_jump_navigation_reuses_rendered_sections(self) -> None:
        polish = POLISH.read_text(encoding="utf-8")
        for marker in (
            "function renderFavoritesGroupJumpNavigation()",
            "nav.id='favoritesGroupJumpNav'",
            "nav.setAttribute('aria-label','Saved favorite groups')",
            "label.textContent='Saved groups'",
            "grid.querySelectorAll('.section-divider[data-category]')",
            "countNode=divider.querySelector('.sd-count')",
            "link.setAttribute('data-favorite-group',name)",
            "target.scrollIntoView({block:'start',behavior:hotkeyScrollBehavior()})",
            "installFavoritesGroupJumpNavigation()",
            "wrapped=function(){baseRender();renderFavoritesGroupJumpNavigation()}",
            ".favorite-group-jump{",
        ):
            self.assertIn(marker, polish)
        self.assertIn("if(activeSection!=='__favorites__')return", polish)
        self.assertNotIn("favoriteGroupsStorage", polish)
        self.assertNotIn("favoriteCollections", polish)

'''
tests = replace_once(tests, next_test, regression + next_test, 'mobile group jump regression')
test_path.write_text(tests, encoding='utf-8')

browser_path = Path('tests/prompt_kit_favorite_browser_proof.py')
browser = browser_path.read_text(encoding='utf-8')
scenario_anchor = "            observations.append({\n                \"id\": \"mobile_favorites_quick_access\","
# Insert the structured navigation scenario immediately before the existing quick-access observation is appended,
# after the prior P79 quick-access journey has returned to All with no Favorites saved.
structured = '''            group_pair = mobile_page.evaluate("""() => {
              const firstBySection={};
              for(const prompt of PROMPTS){
                const section=sectionForPrompt(prompt);
                const name=section?section.name:'Other';
                if(!firstBySection[name])firstBySection[name]=prompt.id;
              }
              return Object.keys(firstBySection).slice(0,2).map(name => ({name,id:firstBySection[name]}));
            }""")
            structured_pair_available = len(group_pair) == 2
            if structured_pair_available:
                for item in group_pair:
                    mobile_page.locator(f'[data-prompt-id="{item["id"]}"] .prompt-favorite-btn').click()
                    mobile_page.wait_for_timeout(60)
                quick.click()
                mobile_page.wait_for_timeout(100)
                group_nav = mobile_page.locator('#favoritesGroupJumpNav')
                group_nav_visible = group_nav.is_visible()
                group_links = group_nav.locator('.favorite-group-jump')
                group_link_count = group_links.count()
                group_labels = [group_links.nth(i).get_attribute('data-favorite-group') for i in range(group_link_count)]
                counts_present = all('prompt' in group_links.nth(i).inner_text().lower() for i in range(group_link_count))
                second_link = group_links.nth(1)
                target_id = (second_link.get_attribute('href') or '').lstrip('#')
                second_link.click()
                mobile_page.wait_for_timeout(120)
                target_visible = mobile_page.evaluate("""targetId => {
                  const target=document.getElementById(targetId);
                  if(!target)return false;
                  const r=target.getBoundingClientRect();
                  return r.bottom>0 && r.top<innerHeight;
                }""", target_id)
                target_focused = mobile_page.evaluate("""targetId => {
                  const target=document.getElementById(targetId);
                  return !!(target && target.contains(document.activeElement));
                }""", target_id)
                favorites_state_preserved = mobile_page.evaluate("activeSection === '__favorites__'")
            else:
                group_nav_visible = False
                group_link_count = 0
                group_labels = []
                counts_present = False
                target_visible = False
                target_focused = False
                favorites_state_preserved = False
            observations.append({
                "id": "mobile_favorites_group_jump_navigation",
                "event": "Favorites exposes saved section groups with counts and direct in-page jumps without leaving Favorites",
                "occurred": True,
                "passed": bool(all((
                    structured_pair_available,
                    group_nav_visible,
                    group_link_count >= 2,
                    set(group_labels) == {item['name'] for item in group_pair},
                    counts_present,
                    target_visible,
                    target_focused,
                    favorites_state_preserved,
                ))),
                "pair": group_pair,
                "group_nav_visible": bool(group_nav_visible),
                "group_link_count": group_link_count,
                "group_labels": group_labels,
                "counts_present": bool(counts_present),
                "target_visible": bool(target_visible),
                "target_focused": bool(target_focused),
                "favorites_state_preserved": bool(favorites_state_preserved),
                "viewport": {"width": 390, "height": 844},
            })

'''
if browser.count(scenario_anchor) != 1:
    raise SystemExit(f'browser structured scenario anchor count={browser.count(scenario_anchor)}')
browser = browser.replace(scenario_anchor, structured + scenario_anchor, 1)
claim_anchor = '        "claims": [\n'
claim = '            {"id": "mobile_favorites_group_jump_navigation", "statement": "Favorites on a phone-width viewport exposes only saved prompt groups with counts and direct section jumps while preserving Favorites state", "status": "PASS" if by_id["mobile_favorites_group_jump_navigation"]["passed"] else "FAIL", "required_evidence_class": "browser_runtime_observed", "observation_ids": ["mobile_favorites_group_jump_navigation"]},\n'
browser = replace_once(browser, claim_anchor, claim_anchor + claim, 'browser group jump claim')
browser_path.write_text(browser, encoding='utf-8')

print('FAVORITES_GROUP_JUMP_PATCH_APPLIED=PASS')
