from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
TEST = ROOT / "tests" / "test_prompt_kit_header_contract.py"
README = ROOT / "web" / "README.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


# --- Runtime hotkeys + help module -------------------------------------------------
polish = POLISH.read_text(encoding="utf-8")

old_toggle = """    toggle.setAttribute('aria-controls','search sectionsNav typeNav');
    toggle.setAttribute('title','Hide filters to maximize prompt browsing space');
    toggle.textContent='Hide filters ↑';
    toggle.addEventListener('click',function(){
      var collapsed=header.classList.toggle('filters-collapsed');
      toggle.setAttribute('aria-expanded',collapsed?'false':'true');
      toggle.setAttribute('title',collapsed?'Show Prompt Kit filters':'Hide filters to maximize prompt browsing space');
      toggle.textContent=collapsed?'Show filters ↓':'Hide filters ↑';
    });
"""
new_toggle = """    toggle.setAttribute('aria-controls','search sectionsNav typeNav');
    toggle.setAttribute('aria-keyshortcuts','F');
    toggle.setAttribute('title','Hide filters to maximize prompt browsing space (F)');
    toggle.textContent='Hide filters ↑';
    toggle.addEventListener('click',function(){
      var collapsed=header.classList.toggle('filters-collapsed');
      toggle.setAttribute('aria-expanded',collapsed?'false':'true');
      toggle.setAttribute('title',collapsed?'Show Prompt Kit filters (F)':'Hide filters to maximize prompt browsing space (F)');
      toggle.textContent=collapsed?'Show filters ↓':'Hide filters ↑';
    });
"""
polish = replace_once(polish, old_toggle, new_toggle, "filter toggle contract")

old_hotkeys = """function installCompactBrowsingHotkeys(){
  document.addEventListener('keydown',function(e){
    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    var target=e.target;
    if(target&&(target.tagName==='INPUT'||target.tagName==='TEXTAREA'||target.tagName==='SELECT'||target.isContentEditable))return;
    if(e.key==='1'){
      e.preventDefault();
      e.stopImmediatePropagation();
      activateAllPromptsView();
      return;
    }
    if(e.key==='4'){
      e.preventDefault();
      e.stopImmediatePropagation();
      activateFavoritesView();
      return;
    }
    if(e.key==='5'){
      var doctrine=document.querySelector('.cat-tab[data-cat=\"doctrine\"]');
      if(doctrine){e.preventDefault();e.stopImmediatePropagation();doctrine.click()}
    }
  },true)
}
"""
new_hotkeys = """var PROMPT_KIT_SHORTCUTS=[
  {key:'1',label:'All prompts'},
  {key:'2',label:'Standard prompts'},
  {key:'3',label:'GNHF prompts'},
  {key:'4',label:'Favorites'},
  {key:'5',label:'Doctrine'},
  {key:'/',label:'Focus search'},
  {key:'R',label:'Reference panel'},
  {key:'F',label:'Show / hide filters'},
  {key:'T',label:'Scroll to top'},
  {key:'B',label:'Scroll to bottom'},
  {key:'Esc',label:'Close / clear active surface'}
];

function hotkeyScrollBehavior(){
  try{return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}catch(e){return 'auto'}
}

function scrollPromptKitTo(edge){
  var anchor=document.getElementById(edge==='top'?'page-top':'page-bottom');
  var behavior=hotkeyScrollBehavior();
  if(anchor&&typeof anchor.scrollIntoView==='function'){
    try{anchor.scrollIntoView({behavior:behavior,block:edge==='top'?'start':'end'});return}catch(e){}
  }
  var height=Math.max(document.documentElement?document.documentElement.scrollHeight:0,document.body?document.body.scrollHeight:0);
  var top=edge==='top'?0:height;
  try{window.scrollTo({top:top,behavior:behavior})}catch(e){window.scrollTo(0,top)}
}

function toggleCompactFilters(){
  var toggle=document.getElementById('filterPanelToggle');
  if(toggle)toggle.click()
}

function setHotkeyHelpOpen(open,restoreFocus){
  var panel=document.getElementById('hotkeyHelpPanel');
  var toggle=document.getElementById('hotkeyHelpToggle');
  if(!panel||!toggle)return;
  panel.hidden=!open;
  toggle.setAttribute('aria-expanded',open?'true':'false');
  if(!open&&restoreFocus){try{toggle.focus({preventScroll:true})}catch(e){toggle.focus()}}
}

function ensureHotkeyHelp(){
  if(document.getElementById('hotkeyHelp'))return;
  if(!document.getElementById('prompt-kit-hotkey-help-styles')){
    var style=document.createElement('style');
    style.id='prompt-kit-hotkey-help-styles';
    style.textContent='.hotkey-help{position:fixed;right:80px;bottom:16px;z-index:45;font-family:inherit}.hotkey-help-toggle{display:inline-flex;align-items:center;gap:7px;min-height:40px;padding:8px 11px;border:1px solid rgba(56,189,248,.62);border-radius:999px;background:linear-gradient(135deg,rgba(14,116,144,.92),rgba(15,23,42,.96));color:var(--text-primary);font-size:11px;font-weight:800;letter-spacing:.03em;cursor:pointer;box-shadow:0 0 0 1px rgba(56,189,248,.14),0 0 18px rgba(56,189,248,.32),0 8px 24px rgba(0,0,0,.28);animation:hotkey-help-glow 2.8s ease-in-out infinite}.hotkey-help-toggle:hover,.hotkey-help-toggle:focus-visible{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-glow),0 0 26px rgba(56,189,248,.46)}.hotkey-help-icon{font-size:15px;line-height:1}.hotkey-help-panel{position:absolute;right:0;bottom:calc(100% + 10px);width:min(292px,calc(100vw - 24px));max-height:min(520px,70vh);overflow:auto;padding:12px;border:1px solid rgba(56,189,248,.42);border-radius:12px;background:rgba(15,23,42,.98);box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 28px rgba(56,189,248,.22),0 18px 48px rgba(0,0,0,.46);backdrop-filter:blur(12px)}.hotkey-help-panel[hidden]{display:none}.hotkey-help-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;color:var(--text-primary);font-size:12px}.hotkey-help-close{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--border);border-radius:7px;background:var(--bg-surface);color:var(--text-secondary);cursor:pointer}.hotkey-help-close:hover,.hotkey-help-close:focus-visible{outline:none;border-color:var(--accent);color:var(--text-primary);box-shadow:0 0 0 2px var(--accent-glow)}.hotkey-help-list{display:grid;grid-template-columns:auto 1fr;gap:6px 10px;align-items:center}.hotkey-help-list kbd{min-width:28px;padding:3px 6px;border:1px solid var(--border);border-bottom-color:rgba(148,163,184,.65);border-radius:6px;background:var(--bg-surface);color:var(--accent);font:700 10px/1.3 ui-monospace,SFMono-Regular,Consolas,monospace;text-align:center}.hotkey-help-list span{color:var(--text-secondary);font-size:11px;line-height:1.35}@keyframes hotkey-help-glow{0%,100%{box-shadow:0 0 0 1px rgba(56,189,248,.12),0 0 14px rgba(56,189,248,.24),0 8px 24px rgba(0,0,0,.28)}50%{box-shadow:0 0 0 1px rgba(56,189,248,.24),0 0 24px rgba(56,189,248,.46),0 8px 28px rgba(0,0,0,.34)}}@media(max-width:760px){.hotkey-help{right:78px;bottom:16px}.hotkey-help-toggle{min-height:44px;padding:9px 12px}.hotkey-help-panel{position:fixed;right:12px;bottom:72px;width:calc(100vw - 24px);max-height:60vh}}@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}';
    document.head.appendChild(style)
  }
  var shell=document.createElement('div');
  shell.className='hotkey-help';
  shell.id='hotkeyHelp';

  var toggle=document.createElement('button');
  toggle.className='hotkey-help-toggle';
  toggle.id='hotkeyHelpToggle';
  toggle.type='button';
  toggle.setAttribute('aria-expanded','false');
  toggle.setAttribute('aria-controls','hotkeyHelpPanel');
  toggle.setAttribute('aria-label','Open keyboard shortcut help');
  toggle.innerHTML='<span class="hotkey-help-icon" aria-hidden="true">⌨</span><span>Hotkeys</span>';
  shell.appendChild(toggle);

  var panel=document.createElement('div');
  panel.className='hotkey-help-panel';
  panel.id='hotkeyHelpPanel';
  panel.hidden=true;
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-label','Keyboard shortcuts');

  var head=document.createElement('div');
  head.className='hotkey-help-head';
  var title=document.createElement('strong');
  title.textContent='Keyboard shortcuts';
  var close=document.createElement('button');
  close.className='hotkey-help-close';
  close.type='button';
  close.setAttribute('aria-label','Close keyboard shortcut help');
  close.textContent='×';
  head.appendChild(title);
  head.appendChild(close);
  panel.appendChild(head);

  var list=document.createElement('div');
  list.className='hotkey-help-list';
  PROMPT_KIT_SHORTCUTS.forEach(function(shortcut){
    var key=document.createElement('kbd');
    key.textContent=shortcut.key;
    var label=document.createElement('span');
    label.textContent=shortcut.label;
    list.appendChild(key);
    list.appendChild(label)
  });
  panel.appendChild(list);
  shell.appendChild(panel);
  document.body.appendChild(shell);

  toggle.addEventListener('click',function(){setHotkeyHelpOpen(panel.hidden)});
  close.addEventListener('click',function(){setHotkeyHelpOpen(false,true)});
  document.addEventListener('click',function(e){if(!panel.hidden&&!shell.contains(e.target))setHotkeyHelpOpen(false,false)})
}

function installCompactBrowsingHotkeys(){
  document.addEventListener('keydown',function(e){
    if(e.defaultPrevented||e.altKey||e.metaKey||e.ctrlKey)return;
    var target=e.target;
    if(target&&(target.tagName==='INPUT'||target.tagName==='TEXTAREA'||target.tagName==='SELECT'||target.isContentEditable))return;
    var key=String(e.key||'').toLowerCase();
    if(key==='escape'&&!document.getElementById('hotkeyHelpPanel').hidden){
      e.preventDefault();
      e.stopImmediatePropagation();
      setHotkeyHelpOpen(false,true);
      return;
    }
    if(key==='1'){
      e.preventDefault();
      e.stopImmediatePropagation();
      activateAllPromptsView();
      return;
    }
    if(key==='4'){
      e.preventDefault();
      e.stopImmediatePropagation();
      activateFavoritesView();
      return;
    }
    if(key==='5'){
      var doctrine=document.querySelector('.cat-tab[data-cat=\"doctrine\"]');
      if(doctrine){e.preventDefault();e.stopImmediatePropagation();doctrine.click()}
      return;
    }
    if(key==='f'){
      e.preventDefault();
      e.stopImmediatePropagation();
      toggleCompactFilters();
      return;
    }
    if(key==='t'){
      e.preventDefault();
      e.stopImmediatePropagation();
      scrollPromptKitTo('top');
      return;
    }
    if(key==='b'){
      e.preventDefault();
      e.stopImmediatePropagation();
      scrollPromptKitTo('bottom');
    }
  },true)
}
"""
polish = replace_once(polish, old_hotkeys, new_hotkeys, "compact hotkey dispatcher")
polish = replace_once(
    polish,
    "ensureCompactBrowsingControls();\ninstallCompactBrowsingViewSwitches();\ninstallCompactBrowsingHotkeys();",
    "ensureCompactBrowsingControls();\nensureHotkeyHelp();\ninstallCompactBrowsingViewSwitches();\ninstallCompactBrowsingHotkeys();",
    "runtime install order",
)
POLISH.write_text(polish, encoding="utf-8")


# --- Focused source/generated contract ---------------------------------------------
test = TEST.read_text(encoding="utf-8")
insert_anchor = """def test_readme_records_exact_deployed_surface() -> None:\n"""
new_test = r'''def test_polish_hotkeys_and_glowing_help_are_source_and_deployed_contract() -> None:
    source = POLISH.read_text(encoding="utf-8")
    deployed = read_deployed()
    required = (
        "var PROMPT_KIT_SHORTCUTS=[",
        "{key:'4',label:'Favorites'}",
        "{key:'5',label:'Doctrine'}",
        "{key:'F',label:'Show / hide filters'}",
        "{key:'T',label:'Scroll to top'}",
        "{key:'B',label:'Scroll to bottom'}",
        "function scrollPromptKitTo(edge)",
        "function toggleCompactFilters()",
        "function ensureHotkeyHelp()",
        "id='prompt-kit-hotkey-help-styles'",
        "animation:hotkey-help-glow",
        "toggle.setAttribute('aria-label','Open keyboard shortcut help')",
        "panel.setAttribute('role','dialog')",
        "@media(prefers-reduced-motion:reduce){.hotkey-help-toggle{animation:none}}",
        "if(key==='f')",
        "scrollPromptKitTo('top')",
        "scrollPromptKitTo('bottom')",
    )
    for text, label in ((source, "polish source"), (deployed, "generated Prompt Kit")):
        for marker in required:
            assert marker in text, f"{label} missing hotkey/help contract: {marker}"

    assert "toggle.setAttribute('aria-keyshortcuts','F')" in source
    assert "target.tagName==='SELECT'||target.isContentEditable" in source
    assert "if(key==='escape'&&!document.getElementById('hotkeyHelpPanel').hidden)" in source
    assert ".hotkey-help{position:fixed;right:80px;bottom:16px" in source
    assert "@media(max-width:760px){.hotkey-help{right:78px;bottom:16px}" in source


'''
if insert_anchor not in test:
    raise SystemExit("focused test insertion anchor missing")
test = test.replace(insert_anchor, new_test + insert_anchor, 1)

old_readme_test = r'''def test_readme_records_exact_deployed_surface() -> None:
    text = README.read_text(encoding="utf-8")
    assert "### Header navigation contract" in text
    assert "1. All\n2. Standard\n3. GNHF" in text
    assert "Doctrine may use shortcut `4`, but it must never displace GNHF." in text
    assert "`web/prompt-kit/index.html`" in text
    for key, label in (("1", "All prompts"), ("2", "Standard prompts"), ("3", "GNHF prompts"), ("4", "Doctrine")):
        assert f"| `{key}` | {label} |" in text
'''
new_readme_test = r'''def test_readme_records_exact_deployed_surface() -> None:
    text = README.read_text(encoding="utf-8")
    assert "### Header navigation contract" in text
    assert "1. All\n2. Standard\n3. GNHF" in text
    assert "The supplemental polish runtime assigns `4` to Favorites and remaps Doctrine to `5`" in text
    assert "`web/prompt-kit/index.html`" in text
    for key, label in (
        ("1", "All prompts"),
        ("2", "Standard prompts"),
        ("3", "GNHF prompts"),
        ("4", "Favorites"),
        ("5", "Doctrine"),
        ("F", "Show / hide filters"),
        ("T", "Scroll to top"),
        ("B", "Scroll to bottom"),
    ):
        assert f"| `{key}` | {label} |" in text
'''
test = replace_once(test, old_readme_test, new_readme_test, "README contract test")

test = replace_once(
    test,
    "        test_responsive_header_reflows_before_collision,\n        test_readme_records_exact_deployed_surface,",
    "        test_responsive_header_reflows_before_collision,\n        test_polish_hotkeys_and_glowing_help_are_source_and_deployed_contract,\n        test_readme_records_exact_deployed_surface,",
    "test runner list",
)
TEST.write_text(test, encoding="utf-8")


# --- Human contract ----------------------------------------------------------------
readme = README.read_text(encoding="utf-8")
old_table = """### Hotkeys

| Key | Action |
|---|---|
| `/` | Focus search |
| `1` | All prompts |
| `2` | Standard prompts |
| `3` | GNHF prompts |
| `4` | Doctrine |
| `R` | Toggle reference panel |
| `Esc` | Close the active surface or clear filters |

### Header navigation contract

The first three library-view filters are fixed and ordered:

1. All
2. Standard
3. GNHF

Their keyboard shortcuts are `1`, `2`, and `3` respectively. Doctrine may use shortcut `4`, but it must never displace GNHF.
"""
new_table = """### Hotkeys

The glowing **Hotkeys** module beside the floating reference control is the in-product shortcut reference. Select it to view the current effective bindings; select outside it, use its close control, or press **Esc** to dismiss it.

| Key | Action |
|---|---|
| `/` | Focus search |
| `1` | All prompts |
| `2` | Standard prompts |
| `3` | GNHF prompts |
| `4` | Favorites |
| `5` | Doctrine |
| `R` | Toggle reference panel |
| `F` | Show / hide filters |
| `T` | Scroll to top |
| `B` | Scroll to bottom |
| `Esc` | Close the active surface or clear filters |

Single-letter navigation shortcuts are ignored while typing in an input, textarea, select, or content-editable surface. Top/bottom scrolling respects reduced-motion preferences.

### Header navigation contract

The first three library-view filters are fixed and ordered:

1. All
2. Standard
3. GNHF

Their keyboard shortcuts are `1`, `2`, and `3` respectively. The generated base header still carries Doctrine's legacy `4` label before supplemental runtime enhancement. The supplemental polish runtime assigns `4` to Favorites and remaps Doctrine to `5`; the visible Hotkeys module and effective dispatcher must remain aligned without displacing GNHF.
"""
readme = replace_once(readme, old_table, new_table, "README hotkey section")
README.write_text(readme, encoding="utf-8")
