from __future__ import annotations

import re
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label}: anchor missing")
    return text.replace(old, new, 1)


def replace_function(text: str, name: str, new: str) -> str:
    marker = f"function {name}("
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"function anchor missing: {name}")
    brace = text.find("{", start)
    depth = 0
    quote = None
    escaped = False
    for idx in range(brace, len(text)):
        ch = text[idx]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + new.rstrip() + text[idx + 1 :]
    raise SystemExit(f"unterminated function: {name}")


def remove_function(text: str, name: str) -> str:
    marker = f"function {name}("
    if marker not in text:
        return text
    return replace_function(text, name, "")


def replace_method(text: str, name: str, new_method: str) -> str:
    pattern = re.compile(
        rf"^    def {re.escape(name)}\(self[^\n]*\).*?(?=^    def |^if __name__ ==)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"test method anchor missing: {name}")
    return text[: match.start()] + new_method.rstrip() + "\n\n" + text[match.end() :]


# --- Production runtime: catalog owns natural numeric prompt hotkeys. ---
path = Path("docs/prompt-kit-polish.js")
text = path.read_text(encoding="utf-8")
text = replace_once(
    text,
    "var PROMPT_KIT_SHORTCUT_STORAGE_KEY='promptKit.promptShortcuts.v1';\nvar PROMPT_KIT_SHORTCUT_SCHEMA='prompt-kit-shortcuts/v1';\nvar PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;\nvar promptShortcutBindings=loadPromptShortcutBindings();\nvar sharedPromptShortcutBindings=computeSharedPromptShortcutBindings();",
    "var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;\nvar sharedPromptShortcutBindings=computeSharedPromptShortcutBindings();",
    "remove manual shortcut storage globals",
)

old_registry_start = text.index("function computeSharedPromptShortcutBindings()")
old_registry_end = text.index("function resetPromptShortcutBuffer()")
new_registry = r'''function computeSharedPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item||item.sharedShortcut!==true)return;
    var promptId=normalizePromptShortcutId(item.id);
    if(promptId)bindings[promptId.slice(1)]=promptId
  });
  return bindings
}

function catalogPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    if(!promptId)return;
    var digits=promptId.slice(1);
    if(!digits)return;
    bindings[digits]=promptId;
    bindings['p'+digits]=promptId
  });
  return bindings
}

function favoritePromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    if(promptId&&isFavoritePrompt(promptId))bindings[promptId.slice(1)]=promptId
  });
  return bindings
}

function effectivePromptShortcutBindings(){
  return catalogPromptShortcutBindings()
}

function favoritePromptShortcutIds(){
  var bindings=favoritePromptShortcutBindings();
  return Object.keys(bindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return bindings[gesture]})
}

function sharedPromptShortcutIds(){
  return Object.keys(sharedPromptShortcutBindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return sharedPromptShortcutBindings[gesture]})
}

function renderPromptShortcutBindings(){
  var host=document.getElementById('promptShortcutBindings');
  if(!host)return;
  host.innerHTML='';
  var intro=document.createElement('span');
  intro.className='hotkey-shortcut-empty';
  intro.textContent='Every prompt has a natural numeric shortcut. Example: type 126 to copy + snap to P126.';
  host.appendChild(intro);
  var favoriteIds=favoritePromptShortcutIds();
  var sharedIds=sharedPromptShortcutIds().filter(function(promptId){return favoriteIds.indexOf(promptId)<0});
  sharedIds.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.slice(1);
    var label=document.createElement('span');label.textContent='Copy + snap to '+promptId;
    var shared=document.createElement('span');shared.className='hotkey-shortcut-shared';shared.textContent='Recommended';
    row.appendChild(key);row.appendChild(label);row.appendChild(shared);host.appendChild(row)
  });
  favoriteIds.forEach(function(promptId){
    var row=document.createElement('div');row.className='hotkey-shortcut-row';
    var key=document.createElement('kbd');key.textContent=promptId.slice(1);
    var label=document.createElement('span');label.textContent='Copy + snap to '+promptId;
    var favorite=document.createElement('span');favorite.className='hotkey-shortcut-shared';favorite.textContent='Favorite';
    var remove=document.createElement('button');remove.type='button';remove.className='hotkey-shortcut-remove';remove.setAttribute('aria-label','Remove '+promptId+' from Favorites');remove.textContent='Unfavorite';
    remove.addEventListener('click',function(){toggleFavoritePromptAndRefreshShortcut(promptId)});
    row.appendChild(key);row.appendChild(label);row.appendChild(favorite);row.appendChild(remove);host.appendChild(row)
  })
}

'''
text = text[:old_registry_start] + new_registry + text[old_registry_end:]

text = replace_function(
    text,
    "activatePromptShortcutTarget",
    r'''function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!revealPromptShortcutTarget(promptId,'instant')){showToast(promptId+' could not be revealed');return false}
  copyPrompt(promptId);
  return true
}''',
)

text = replace_once(
    text,
    "  {key:'`',label:'Show / hide Hotkeys'},",
    "  {key:'`',label:'Show / hide Hotkeys'},\n  {key:'126',label:'Prompt number → copy + snap to P126'},",
    "discoverable numeric shortcut help",
)

text = remove_function(text, "focusFavoritePromptShortcutInput")
text = replace_once(
    text,
    "    if(focusFavoritePromptShortcutInput(panel))return;\n",
    "",
    "remove manual shortcut input focus",
)

config_start = text.index("  var config=document.createElement('div');")
config_end_marker = "  panel.appendChild(config);"
config_end = text.index(config_end_marker, config_start) + len(config_end_marker)
new_config = r'''  var config=document.createElement('div');
  config.className='hotkey-shortcut-config';
  var configTitle=document.createElement('strong');
  configTitle.textContent='Prompt shortcuts';
  var configHint=document.createElement('span');
  configHint.className='hotkey-shortcut-hint';
  configHint.textContent='Type the digits after P anywhere outside editable fields. Example: 126 copies P126 and snaps its card to center. p126 remains accepted for compatibility. Favorites need no shortcut setup.';
  var bindings=document.createElement('div');
  bindings.id='promptShortcutBindings';
  bindings.className='hotkey-shortcut-bindings';
  config.appendChild(configTitle);config.appendChild(configHint);config.appendChild(bindings);
  panel.appendChild(config);'''
text = text[:config_start] + new_config + text[config_end:]

for stale in (
    "  saveShortcut.addEventListener('click',function(){if(configurePromptShortcut(promptInput.value))promptInput.value=''});\n",
    "  promptInput.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(configurePromptShortcut(promptInput.value))promptInput.value=''}});\n",
):
    if stale in text:
        text = text.replace(stale, "", 1)

text = replace_once(
    text,
    "  button.setAttribute('aria-label',(active?'Remove ':'Add ')+promptId+(active?' from Favorites and Hotkeys':' to Favorites and Hotkeys'));",
    "  button.setAttribute('aria-label',(active?'Remove ':'Add ')+promptId+(active?' from Favorites':' to Favorites'));",
    "favorite detail aria copy",
)
text = replace_once(
    text,
    "  if(isFavorite&&!wasFavorite)showToast('★ '+promptId+' saved · shortcut '+promptId.toLowerCase()+' ready','success');\n  else if(!isFavorite&&wasFavorite)showToast('Removed '+promptId+' from Favorites and Hotkeys');",
    "  if(isFavorite&&!wasFavorite)showToast('★ '+promptId+' saved · type '+promptId.slice(1)+' anytime','success');\n  else if(!isFavorite&&wasFavorite)showToast('Removed '+promptId+' from Favorites · shortcut '+promptId.slice(1)+' still available');",
    "favorite toast independence",
)

for forbidden in (
    "PROMPT_KIT_SHORTCUT_STORAGE_KEY",
    "PROMPT_KIT_SHORTCUT_SCHEMA",
    "promptShortcutBindings",
    "function configurePromptShortcut(",
    "function removePromptShortcut(",
    "promptShortcutPromptId",
    "saveShortcut",
):
    if forbidden in text:
        raise SystemExit(f"manual shortcut path survived: {forbidden}")
path.write_text(text, encoding="utf-8")


# --- Focused static/runtime regression: test real activation, including P126. ---
path = Path("tests/test_prompt_kit_interactions_contract.py")
test = path.read_text(encoding="utf-8")
method_name = "test_catalog_derived_prompt_hotkeys_resolve_numeric_identity_and_prefixes"
new_method = r'''    def test_catalog_derived_prompt_hotkeys_resolve_numeric_identity_and_prefixes(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        blocks = "\n\n".join(
            function_block(source, name)
            for name in (
                "normalizePromptShortcutId",
                "catalogPromptShortcutBindings",
                "resetPromptShortcutBuffer",
                "schedulePromptShortcutBufferReset",
                "promptShortcutHasLongerPrefix",
                "effectivePromptShortcutBindings",
                "activatePromptShortcutTarget",
                "handleConfiguredPromptShortcutKey",
            )
        )
        script = f"""
var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
var PROMPTS=[{{id:'P01'}},{{id:'P11'}},{{id:'P13'}},{{id:'P111'}},{{id:'P125'}},{{id:'P126'}}];
var promptShortcutBuffer='';
var promptShortcutBufferTimer=null;
var activations=[];
var reveals=[];
var copies=[];
function revealPromptShortcutTarget(promptId,behavior){{reveals.push([promptId,behavior]);return true}}
function copyPrompt(promptId){{copies.push(promptId)}}
function showToast(){{}}
{blocks}
function eventStub(){{return{{preventDefault:function(){{}},stopImmediatePropagation:function(){{}}}}}}
function press(key){{return handleConfiguredPromptShortcutKey(eventStub(),key)}}
function resetProbe(){{resetPromptShortcutBuffer();activations=[];reveals=[];copies=[]}}
function sleep(ms){{return new Promise(function(resolve){{setTimeout(resolve,ms)}})}}
function assert(condition,message){{if(!condition)throw new Error(message)}}
function assertActivated(promptId){{
  assert(JSON.stringify(reveals)===JSON.stringify([[promptId,'instant']]),promptId+' did not instant-reveal');
  assert(JSON.stringify(copies)===JSON.stringify([promptId]),promptId+' did not copy');
}}
(async function(){{
  var bindings=catalogPromptShortcutBindings();
  assert(bindings['125']==='P125','numeric P125 binding missing');
  assert(bindings['126']==='P126','numeric P126 binding missing');
  assert(bindings['p126']==='P126','p-prefixed P126 compatibility binding missing');
  assert(bindings['01']==='P01','zero-padded P01 binding missing');

  ['1','2','6'].forEach(press);
  assertActivated('P126');
  resetProbe();
  ['p','1','2','6'].forEach(press);
  assertActivated('P126');
  resetProbe();
  ['0','1'].forEach(press);
  assertActivated('P01');
  resetProbe();
  ['1','1'].forEach(press);
  assert(copies.length===0,'11 fired before longer-prefix ambiguity closed');
  await sleep(40);
  assertActivated('P11');
  resetProbe();
  ['1','1','1'].forEach(press);
  assertActivated('P111');
  resetProbe();
  ['1','3'].forEach(press);
  assertActivated('P13');
  console.log('PASS');
}})().catch(function(error){{console.error(error.stack||error);process.exit(1)}});
"""
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
        )
        self.assertEqual(completed.stdout.strip(), "PASS")
        self.assertIn("bindings[digits]=promptId", source)
        self.assertIn("bindings['p'+digits]=promptId", source)
        self.assertIn("revealPromptShortcutTarget(promptId,'instant')", source)
        self.assertNotIn("PROMPT_KIT_SHORTCUT_STORAGE_KEY", source)
        self.assertNotIn("function configurePromptShortcut(", source)
        self.assertNotIn("promptShortcutPromptId", source)
        activation = function_block(source, "activatePromptShortcutTarget")
        self.assertNotIn("isFavoritePrompt", activation)
        self.assertNotIn("sharedPromptShortcutBindings", activation)'''
test = replace_method(test, method_name, new_method)
path.write_text(test, encoding="utf-8")


# --- Update the hotkey completion contract away from manual/favorite authorization. ---
path = Path("tests/test_prompt_kit_hotkey_completion.py")
test = path.read_text(encoding="utf-8")
test = replace_method(
    test,
    "test_favorite_prompt_shortcuts_are_persisted_fail_closed",
    r'''    def test_catalog_prompt_shortcuts_are_derived_without_manual_persistence(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200",
            "function catalogPromptShortcutBindings()",
            "bindings[digits]=promptId",
            "bindings['p'+digits]=promptId",
            "function handleConfiguredPromptShortcutKey(e,key)",
            "function activatePromptShortcutTarget(promptId)",
            "revealPromptShortcutTarget(promptId,'instant')",
            "copyPrompt(promptId)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        for removed in (
            "PROMPT_KIT_SHORTCUT_STORAGE_KEY",
            "PROMPT_KIT_SHORTCUT_SCHEMA",
            "function configurePromptShortcut(",
            "function removePromptShortcut(",
            "promptShortcutPromptId",
        ):
            self.assertNotIn(removed, source)
            self.assertNotIn(removed, deployed)
        activation = source[source.index("function activatePromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertNotIn("isFavoritePrompt", activation)
        self.assertNotIn("sharedPromptShortcutBindings", activation)''',
)
test = replace_method(
    test,
    "test_favorites_automatically_publish_shortcuts_and_detail_favorite_control",
    r'''    def test_favorites_are_organizational_and_detail_control_keeps_numeric_shortcut_visible(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function favoritePromptShortcutBindings()",
            "bindings[promptId.slice(1)]=promptId",
            "function centerRenderedPromptCard(promptId,behavior)",
            "function toggleFavoritePromptAndRefreshShortcut(rawPromptId)",
            "function decoratePromptDetailFavorite(promptId)",
            "prompt-detail-favorite-btn",
            "type '+promptId.slice(1)+' anytime",
            "shortcut '+promptId.slice(1)+' still available",
            "centerRenderedPromptCard(id,'instant');",
            "toggleFavoritePromptAndRefreshShortcut(p.id)",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        self.assertIn("return catalogPromptShortcutBindings()", source)''',
)
test = replace_method(
    test,
    "test_configuration_ui_and_generated_parity_are_present",
    r'''    def test_hotkey_help_exposes_natural_numeric_route_without_manual_setup(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "Prompt shortcuts",
            "Every prompt has a natural numeric shortcut",
            "Example: type 126 to copy + snap to P126",
            "Type the digits after P anywhere outside editable fields",
            "p126 remains accepted for compatibility",
            "{key:'126',label:'Prompt number → copy + snap to P126'}",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        self.assertNotIn("promptShortcutPromptId", source)
        self.assertNotIn("Save favorite prompt keyboard shortcut", source)''',
)
test = replace_method(
    test,
    "test_shared_registry_shortcuts_publish_without_favorite_gate",
    r'''    def test_shared_registry_shortcuts_remain_recommendation_metadata_not_activation_authority(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        for marker in (
            "function computeSharedPromptShortcutBindings()",
            "item.sharedShortcut!==true",
            "function effectivePromptShortcutBindings()",
            "return catalogPromptShortcutBindings()",
            "function sharedPromptShortcutIds()",
            "shared.textContent='Recommended'",
        ):
            self.assertIn(marker, source)
            self.assertIn(marker, deployed)
        registry = json.loads(
            (ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json").read_text(encoding="utf-8")
        )
        shared_ids = [
            prompt["id"] for prompt in registry["prompts"] if prompt.get("sharedShortcut") is True
        ]
        self.assertEqual(shared_ids, ["P95"])
        activation = source[source.index("function activatePromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertNotIn("sharedPromptShortcutBindings", activation)''',
)
test = replace_method(
    test,
    "test_hotkey_open_focuses_favorite_input_and_escape_recovers_from_editable",
    r'''    def test_hotkey_open_focuses_close_and_escape_recovers_without_manual_shortcut_input(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        self.assertNotIn("focusFavoritePromptShortcutInput", source)
        self.assertNotIn("promptShortcutPromptId", source)
        self.assertIn("var close=panel.querySelector('.hotkey-help-close');", source)
        escape_guard = "if(key==='escape'&&escapeHelpPanel&&!escapeHelpPanel.hidden)"
        editable_guard = "if(editable)return;"
        backtick = "if(key==='`')"
        self.assertLess(source.index(escape_guard), source.index(editable_guard))
        self.assertLess(source.index(editable_guard), source.index(backtick))
        self.assertIn("resetPromptShortcutBuffer();setHotkeyHelpOpen(false,true);return", source)''',
)
# browser proof topology must now include real bare-numeric P126.
test = replace_once(
    test,
    "            'page.keyboard.press(\"d\")',",
    "            'page.keyboard.press(\"d\")',\n            'press(\"126\")',\n            'numeric_p126_copies_and_snaps',",
    "hotkey completion browser marker",
)
test = replace_method(
    test,
    "test_human_contract_and_design_close_previous_ux_decisions",
    r'''    def test_human_contract_and_design_close_natural_numeric_hotkey_decision(self) -> None:
        readme = README.read_text(encoding="utf-8")
        design = DESIGN.read_text(encoding="utf-8")
        for row in (
            "| `` ` `` | Show / hide Hotkeys |",
            "| `[` | Hide filters |",
            "| `]` | Show filters |",
        ):
            self.assertIn(row, readme)
        self.assertIn("Type the digits after `P`", readme)
        self.assertIn("`126` → `P126`", readme)
        self.assertIn("canonical `PROMPTS` catalog owns prompt-number hotkeys", design)
        self.assertIn("bare numeric identity is the primary gesture", design)
        self.assertIn("manual prompt-shortcut persistence is retired", design)
        self.assertIn("copy + instant snap", design)
        self.assertIn("buffer is active", design)
        self.assertIn("one hand", design)''',
)
path.write_text(test, encoding="utf-8")


# --- Browser proof: real page keyboard path, no Favorite/manual setup prerequisite. ---
path = Path("tests/prompt_kit_hotkey_identity_browser_proof.py")
browser = path.read_text(encoding="utf-8")
browser = replace_once(browser, 'TARGETS = ("P11", "P13", "P111")', 'TARGETS = ("P11", "P13", "P111", "P126")', "browser targets")
setup_start = browser.index("            # Configure all three overlapping identities through the real product UI.")
setup_end = browser.index("            def set_clipboard", setup_start)
browser = browser[:setup_start] + "            # Natural prompt hotkeys are catalog-derived; no Favorite or manual Save step is allowed.\n            p126_favorite = page.locator('[data-prompt-id=\"P126\"] .prompt-favorite-btn')\n            if p126_favorite.count() != 1 or p126_favorite.get_attribute('aria-pressed') != 'false':\n                raise AssertionError('P126 browser proof did not start from a non-favorite state')\n\n" + browser[setup_end:]
# Convert primary identity journeys to bare digits.
browser = browser.replace('press("p11")', 'press("11")')
browser = browser.replace('press("p13")', 'press("13")')
browser = browser.replace('press("p111")', 'press("111")')
browser = browser.replace('press("p1")', 'press("1")')
# Add P126 copy + geometric snap proof immediately before the P11 prefix case.
anchor = "            # P11 is a prefix of P111: it must remain pending until timeout.\n"
p126_block = r'''            # Bare numeric P126 is the operator-reported regression: it must copy and instant-snap with no Favorite gate.
            set_clipboard("sentinel-126")
            before_y = page.evaluate("window.scrollY")
            press("126")
            page.wait_for_timeout(220)
            p126_final = clipboard()
            p126_geometry = page.evaluate("""() => {
              const card=document.querySelector('[data-prompt-id="P126"]');
              if(!card)return null;
              const rect=card.getBoundingClientRect();
              return {center:(rect.top+rect.bottom)/2,viewport:window.innerHeight/2,scrollY:window.scrollY};
            }""")
            p126_snapped = bool(p126_geometry and abs(p126_geometry["center"] - p126_geometry["viewport"]) <= max(120, 900 * 0.18))
            observations.append({
                "id": "numeric_p126_copies_and_snaps",
                "event": "typing bare 126 copies P126 and centers its canonical card without Favorite/manual setup",
                "occurred": True,
                "passed": p126_final == expected["P126"] and p126_snapped,
                "clipboard_matches": p126_final == expected["P126"],
                "favorite_required": False,
                "before_scroll_y": before_y,
                "geometry": p126_geometry,
                "snapped": p126_snapped,
            })

            # p-prefixed compatibility remains valid after bare numeric becomes primary.
            set_clipboard("sentinel-p126")
            press("p126")
            page.wait_for_timeout(220)
            p126_compat = clipboard()
            observations.append({
                "id": "p126_compatibility_alias",
                "event": "p126 remains a compatibility alias for canonical P126",
                "occurred": True,
                "passed": p126_compat == expected["P126"],
                "clipboard_matches": p126_compat == expected["P126"],
            })

'''
browser = replace_once(browser, anchor, p126_block + anchor, "browser P126 journey")
# Remove obsolete incomplete-prefix B case, which is not valid once every canonical prompt owns its numeric identity.
case_start = browser.find('            set_clipboard("sentinel-p1-b")')
if case_start >= 0:
    case_end = browser.find("            # Home/End are page navigation only", case_start)
    if case_end < 0:
        raise SystemExit("browser incomplete-prefix case end missing")
    browser = browser[:case_start] + browser[case_end:]
# Update narrative IDs and claim.
browser = browser.replace('"p11_waits_for_longer_prefix"', '"numeric_11_waits_for_longer_prefix"')
browser = browser.replace('"p13_resolves_exactly"', '"numeric_13_resolves_exactly"')
browser = browser.replace('"p111_wins_over_p11_prefix"', '"numeric_111_wins_over_11_prefix"')
browser = browser.replace("p11 remains pending before the 1.2s boundary and resolves to P11 after it", "11 remains pending before the 1.2s boundary and resolves to P11 after it")
browser = browser.replace("p13 resolves to P13 without being confused with the p11 family", "13 resolves to P13 without being confused with the 11 family")
browser = browser.replace("p111 resolves to P111 before the pending P11 timeout fires", "111 resolves to P111 before the pending P11 timeout fires")
browser = browser.replace("A settles pending P11 and still activates the All profile", "A settles pending numeric P11 and still activates the All profile")
browser = browser.replace("overlapping-and-dotted-prompt-identity-hotkeys", "catalog-derived-numeric-prompt-hotkeys")
browser = browser.replace(
    '"statement": "p11, p13, p111, p1.1, and p1.11 resolve to distinct canonical prompt identities without numeric header collisions",',
    '"statement": "bare numeric prompt IDs, including 126, resolve to canonical prompts with copy + snap behavior while p-prefixed compatibility and prefix disambiguation remain intact",',
)
path.write_text(browser, encoding="utf-8")


# --- Observed proof workflow must actually execute the identity proof. ---
path = Path(".github/workflows/prompt-kit-observed-browser-proof.yml")
workflow = path.read_text(encoding="utf-8")
for needle in ("      - tests/prompt_kit_favorite_browser_proof.py\n",):
    workflow = workflow.replace(needle, needle + "      - tests/prompt_kit_hotkey_identity_browser_proof.py\n")
run_anchor = "      - name: Observe Favorite copy scroll and Enter behavior\n        run: |\n          mkdir -p Outputs/observed-proof\n          python tests/prompt_kit_favorite_browser_proof.py --receipt Outputs/observed-proof/favorite-shortcut-receipt.json --screenshot Outputs/observed-proof/favorite-shortcut.png\n          python scripts/validate_observed_behavior_receipt.py Outputs/observed-proof/favorite-shortcut-receipt.json --expected-sha \"$(git rev-parse HEAD)\" --summary\n"
identity_step = run_anchor + "      - name: Observe catalog-derived numeric prompt hotkeys\n        run: |\n          python tests/prompt_kit_hotkey_identity_browser_proof.py --receipt Outputs/observed-proof/hotkey-identity-receipt.json --screenshot Outputs/observed-proof/hotkey-identity.png\n          python scripts/validate_observed_behavior_receipt.py Outputs/observed-proof/hotkey-identity-receipt.json --expected-sha \"$(git rev-parse HEAD)\" --summary\n"
workflow = replace_once(workflow, run_anchor, identity_step, "observed identity proof step")
path.write_text(workflow, encoding="utf-8")


# --- Operational docs: remove stale manual/favorite authorization doctrine. ---
path = Path("web/README.md")
readme = path.read_text(encoding="utf-8")
old = re.search(r"Favorite-prompt shortcuts are configured from the Hotkeys panel\..*?Configured Favorite bindings take precedence over shared recommended bindings\.\n", readme, re.DOTALL)
if not old:
    # Current paragraph may have slightly different final sentence; bound it to the next heading.
    old = re.search(r"Favorite-prompt shortcuts are configured from the Hotkeys panel\..*?(?=\n### )", readme, re.DOTALL)
if not old:
    raise SystemExit("web README hotkey doctrine paragraph missing")
new = """Type the digits after `P` anywhere outside editable fields to use a prompt directly: `126` → `P126`. The canonical `PROMPTS` catalog owns these routes, so Favorites and a separate Save step are not prerequisites. The compatibility form `p126` remains accepted. Typed prompt sequences expire after 1.2 seconds; if one prompt ID prefixes another, the shorter exact match waits for that boundary while continued typing selects the longer ID. Completing a prompt-number shortcut copies the canonical prompt and instant-snaps its card to the center of the page without opening detail.\n\n"""
readme = readme[:old.start()] + new + readme[old.end():]
path.write_text(readme, encoding="utf-8")

path = Path("docs/PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md")
design = path.read_text(encoding="utf-8")
design = design.replace("| User bindings | ShortcutRegistry | ShortcutStore |", "| Prompt-number bindings | canonical `PROMPTS` catalog | generated registry |")
design = design.replace("- every current Favorite automatically participates in the effective prompt-ID shortcut registry; unfavoriting removes that derived shortcut immediately, while the versioned explicit-binding store remains a compatibility/repair path.", "- the canonical `PROMPTS` catalog owns prompt-number hotkeys for every prompt; the bare numeric identity is the primary gesture (`126` -> `P126`), with `p126` retained as a compatibility alias.")
design = design.replace("- built-ins keep precedence; Favorite-derived bindings require no duplicate shortcut write because durable Favorite state is their authority. Explicit stored bindings remain fail-closed compatibility data and are effective only while their prompt remains a Favorite.", "- built-ins keep precedence outside an active prompt-number buffer; Favorites are organizational state only and never authorize or suppress a catalog prompt hotkey. Manual prompt-shortcut persistence is retired.")
design = design.replace("- Hotkey help lists shared recommended shortcuts as a projection of the registry with a Recommended label and no Remove control, because the registry owns them.", "- Hotkey help teaches the natural numeric route and may label registry-recommended or Favorite prompts without changing activation authority.")
append = """\nProduction correction on 2026-09-08 after operator P126 regression evidence:\n- typing bare digits such as `126` is the primary desktop/keyboard route and must resolve from the canonical catalog without Favorite state or manual configuration;\n- `p126` remains a compatibility alias, not the primary contract;\n- successful prompt-number activation performs copy + instant snap to the canonical rendered card, while editable fields and modified chords remain protected;\n- observed-browser proof must type the bare numeric sequence through the real page keyboard path before this behavior can be called complete.\n"""
if "Production correction on 2026-09-08 after operator P126 regression evidence:" not in design:
    design += append
path.write_text(design, encoding="utf-8")

path = Path("docs/PROMPT_KIT_OPERATOR_GUIDE.md")
guide = path.read_text(encoding="utf-8")
section_start = guide.index("### Configure a prompt-ID shortcut")
section_end = guide.index("### Core hotkeys", section_start)
new_section = """### Use a prompt-number shortcut\n\n1. Stay outside input, textarea, select, and content-editable fields.\n2. Type the digits after `P`: for `P126`, type **`126`**.\n3. Operant resolves the number from the canonical prompt catalog, copies the prompt, and instant-snaps the P126 card to the center of the page.\n4. No Favorite and no Hotkeys-panel Save step is required. Favorites remain useful for organizing prompts.\n5. `p126` remains accepted as a compatibility alias. Prefix-ambiguous IDs wait up to **1.2 seconds** for continued digits.\n\nThe Hotkeys panel shows the natural numeric rule and labels Favorite/recommended prompts as convenience cues only; neither state controls whether a canonical prompt number works.\n\n"""
guide = guide[:section_start] + new_section + guide[section_end:]
# Correct stale core-key table to the actual A-E/Home/End runtime while in this directly connected section.
core_start = guide.index("### Core hotkeys")
core_end = guide.index("Navigation shortcuts are ignored", core_start)
core = """### Core hotkeys\n\n| Key | Action |\n|---|---|\n| `` ` `` | Show / hide Hotkeys |\n| `126` | Example prompt number: copy + snap to P126 |\n| `A` | All profile |\n| `B` | Standard profile |\n| `C` | Favorites profile |\n| `D` | Configurable profile slot (default SAS) |\n| `E` | Configurable profile slot (default PM) |\n| `/` | Focus search |\n| `R` | Toggle reference panel |\n| `F` | Show / hide filters |\n| `[` | Hide filters |\n| `]` | Show filters |\n| `Home` | Scroll to top |\n| `End` | Scroll to bottom |\n| `Esc` | Close the active surface or clear temporary filters |\n\n"""
guide = guide[:core_start] + core + guide[core_end:]
path.write_text(guide, encoding="utf-8")

print("natural prompt hotkey repair staged")