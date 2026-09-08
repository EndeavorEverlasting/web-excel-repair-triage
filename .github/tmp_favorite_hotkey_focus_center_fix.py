from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


path = Path("docs/prompt-kit-polish.js")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    ".prompt-detail-favorite-btn[data-prompt-id=\"'+promptId+'\"]",
    ".prompt-detail-favorite-btn[data-favorite-prompt-id=\"'+promptId+'\"]",
    "detail favorite selector",
)
text = replace_once(
    text,
    "button.setAttribute('data-prompt-id',normalized);",
    "button.setAttribute('data-favorite-prompt-id',normalized);",
    "detail favorite metadata",
)
old_center = """function centerRenderedPromptCard(promptId){
  var selector='[data-prompt-id="'+String(promptId||'').replace(/"/g,'')+'"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  try{card.scrollIntoView({behavior:hotkeyScrollBehavior(),block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}

function revealPromptShortcutTarget(promptId){
  if(window.PromptKitProfiles&&typeof window.PromptKitProfiles.activateSlot==='function'){
    window.PromptKitProfiles.activateSlot('A',true)
  }
  activeCat='all';
  activeSection=null;
  clearTransientPromptFilters();
  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.dataset.cat==='all')});
  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__all__')});
  renderTypes();
  render();
  return centerRenderedPromptCard(promptId)
}"""
new_center = """function centerRenderedPromptCard(promptId,behavior){
  var selector='[data-prompt-id="'+String(promptId||'').replace(/"/g,'')+'"]';
  var card=document.querySelector(selector);
  if(!card)return false;
  var scrollBehavior=behavior||hotkeyScrollBehavior();
  try{card.scrollIntoView({behavior:scrollBehavior,block:'center',inline:'nearest'})}catch(e){try{card.scrollIntoView()}catch(ignore){}}
  return true
}

function revealPromptShortcutTarget(promptId,behavior){
  if(window.PromptKitProfiles&&typeof window.PromptKitProfiles.activateSlot==='function'){
    window.PromptKitProfiles.activateSlot('A',true)
  }
  activeCat='all';
  activeSection=null;
  clearTransientPromptFilters();
  document.querySelectorAll('.cat-tab').forEach(function(button){button.classList.toggle('active',button.dataset.cat==='all')});
  document.querySelectorAll('.section-tab').forEach(function(button){button.classList.toggle('active',button.dataset.section==='__all__')});
  renderTypes();
  render();
  return centerRenderedPromptCard(promptId,behavior||hotkeyScrollBehavior())
}"""
text = replace_once(text, old_center, new_center, "deterministic center helper")
text = replace_once(
    text,
    "if(!revealPromptShortcutTarget(promptId)){",
    "if(!revealPromptShortcutTarget(promptId,'instant')){",
    "direct jump instant reveal",
)
text = replace_once(
    text,
    "    centerRenderedPromptCard(id);\n    baseShowPromptDetailWithFavorite(id,origin);",
    "    centerRenderedPromptCard(id,'instant');\n    baseShowPromptDetailWithFavorite(id,origin);",
    "detail open instant center",
)
path.write_text(text, encoding="utf-8")

hotkey_test = Path("tests/test_prompt_kit_hotkey_completion.py")
test = hotkey_test.read_text(encoding="utf-8")
test = replace_once(
    test,
    '            "function centerRenderedPromptCard(promptId)",\n',
    '            "function centerRenderedPromptCard(promptId,behavior)",\n',
    "hotkey center signature marker",
)
test = replace_once(
    test,
    '            "centerRenderedPromptCard(id);",\n',
    '            "centerRenderedPromptCard(id,\'instant\');",\n',
    "hotkey detail instant marker",
)
hotkey_test.write_text(test, encoding="utf-8")

mobile_test = Path("tests/test_prompt_kit_mobile_quick_controls.py")
mtest = mobile_test.read_text(encoding="utf-8")
if "revealPromptShortcutTarget(promptId)" not in mtest:
    raise SystemExit("mobile reveal test anchor missing")
mtest = mtest.replace(
    "revealPromptShortcutTarget(promptId)",
    "revealPromptShortcutTarget(promptId,'instant')",
)
mobile_test.write_text(mtest, encoding="utf-8")

print("deterministic centering repair applied")
