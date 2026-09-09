from __future__ import annotations

import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_PROVEN_HEAD = "e05bf4b1e7941d41ab16315a8e1c8f6b87f93982"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if old not in source:
        raise SystemExit(f"{label}: anchor missing")
    return source.replace(old, new, 1)


def function_span(source: str, name: str) -> tuple[int, int]:
    marker = f"function {name}("
    start = source.find(marker)
    if start < 0:
        raise SystemExit(f"function missing: {name}")
    brace = source.find("{", start)
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(brace, len(source)):
        char = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise SystemExit(f"unterminated function: {name}")


def replace_function(source: str, name: str, replacement: str) -> str:
    start, end = function_span(source, name)
    return source[:start] + replacement + source[end:]


def remove_function(source: str, name: str) -> str:
    start, end = function_span(source, name)
    while end < len(source) and source[end] == "\n":
        end += 1
    return source[:start] + source[end:]


def git_show(path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{OLD_PROVEN_HEAD}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def repair_runtime() -> None:
    path = ROOT / "docs" / "prompt-kit-polish.js"
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "var PROMPT_KIT_SHORTCUT_STORAGE_KEY='promptKit.promptShortcuts.v1';\n"
        "var PROMPT_KIT_SHORTCUT_SCHEMA='prompt-kit-shortcuts/v1';\n"
        "var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;\n"
        "var promptShortcutBindings=loadPromptShortcutBindings();\n",
        "var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=1200;\n",
        "manual shortcut globals",
    )
    numeric_help = "{key:'126',label:'Prompt number → copy + snap to P126'}"
    if numeric_help not in text:
        text = replace_once(
            text,
            "  {key:'`',label:'Show / hide Hotkeys'},\n",
            "  {key:'`',label:'Show / hide Hotkeys'},\n"
            "  {key:'126',label:'Prompt number → copy + snap to P126'},\n",
            "hotkey help numeric example",
        )

    compute_shared = """function computeSharedPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item||item.sharedShortcut!==true)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(digits)bindings[digits]=promptId
  });
  return bindings
}"""
    favorite = """function favoritePromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(digits&&isFavoritePrompt(promptId))bindings[digits]=promptId
  });
  return bindings
}"""
    catalog = """function catalogPromptShortcutBindings(){
  var bindings={};
  var catalog=typeof PROMPTS!=='undefined'&&Array.isArray(PROMPTS)?PROMPTS:[];
  catalog.forEach(function(item){
    if(!item)return;
    var promptId=normalizePromptShortcutId(item.id);
    var digits=promptShortcutDigitGesture(promptId);
    if(!digits)return;
    bindings[digits]=promptId;
    bindings['p'+digits]=promptId
  });
  return bindings
}"""
    effective = """function effectivePromptShortcutBindings(){
  return catalogPromptShortcutBindings()
}"""
    favorite_ids = """function favoritePromptShortcutIds(){
  var bindings=favoritePromptShortcutBindings();
  return Object.keys(bindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return bindings[gesture]})
}"""
    shared_ids = """function sharedPromptShortcutIds(){
  return Object.keys(sharedPromptShortcutBindings).sort(function(a,b){return Number(a)-Number(b)}).map(function(gesture){return sharedPromptShortcutBindings[gesture]})
}"""
    render_bindings = """function renderPromptShortcutBindings(){
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
}"""
    activate = """function activatePromptShortcutTarget(promptId){
  var prompt=PROMPTS.find(function(item){return item.id===promptId});
  if(!prompt)return false;
  if(!revealPromptShortcutTarget(promptId,'instant')){showToast(promptId+' could not be revealed');return false}
  copyPrompt(promptId);
  return true
}"""

    text = replace_function(text, "computeSharedPromptShortcutBindings", compute_shared)
    text = replace_function(text, "favoritePromptShortcutBindings", favorite)
    text = replace_function(text, "effectivePromptShortcutBindings", effective)
    for obsolete in (
        "publishPromptShortcutDigitAliases",
        "clonePromptShortcutBindings",
        "loadPromptShortcutBindings",
        "persistPromptShortcutBindings",
        "configuredPromptShortcutIds",
        "configurePromptShortcut",
        "removePromptShortcut",
    ):
        text = remove_function(text, obsolete)
    digit_end = function_span(text, "promptShortcutDigitGesture")[1]
    text = text[:digit_end] + "\n\n" + catalog + text[digit_end:]
    text = replace_function(text, "favoritePromptShortcutIds", favorite_ids)
    text = replace_function(text, "sharedPromptShortcutIds", shared_ids)
    text = replace_function(text, "renderPromptShortcutBindings", render_bindings)
    text = replace_function(text, "activatePromptShortcutTarget", activate)
    text = remove_function(text, "focusFavoritePromptShortcutInput")
    if "if(focusFavoritePromptShortcutInput(panel))return;" in text:
        text = text.replace("    if(focusFavoritePromptShortcutInput(panel))return;\n", "", 1)

    config_start = text.find("  var config=document.createElement('div');")
    config_end_marker = "  panel.appendChild(config);"
    config_end = text.find(config_end_marker, config_start)
    if config_start < 0 or config_end < 0:
        raise SystemExit("manual config UI block missing")
    config_end += len(config_end_marker)
    new_config = """  var config=document.createElement('div');
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
  panel.appendChild(config);"""
    text = text[:config_start] + new_config + text[config_end:]
    for line in (
        "  saveShortcut.addEventListener('click',function(){if(configurePromptShortcut(promptInput.value))promptInput.value=''});\n",
        "  promptInput.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();if(configurePromptShortcut(promptInput.value))promptInput.value=''}});\n",
    ):
        text = text.replace(line, "", 1)

    for old, new in (
        (
            "button.setAttribute('aria-label',(active?'Remove ':'Add ')+promptId+(active?' from Favorites and Hotkeys':' to Favorites and Hotkeys'));",
            "button.setAttribute('aria-label',(active?'Remove ':'Add ')+promptId+(active?' from Favorites':' to Favorites'));",
        ),
        (
            "if(isFavorite&&!wasFavorite)showToast('★ '+promptId+' saved · shortcut '+promptId.toLowerCase()+' ready','success');",
            "if(isFavorite&&!wasFavorite)showToast('★ '+promptId+' saved · type '+promptId.slice(1)+' anytime','success');",
        ),
        (
            "else if(!isFavorite&&wasFavorite)showToast('Removed '+promptId+' from Favorites and Hotkeys');",
            "else if(!isFavorite&&wasFavorite)showToast('Removed '+promptId+' from Favorites · shortcut '+promptId.slice(1)+' still available');",
        ),
    ):
        text = replace_once(text, old, new, "favorite organization wording")

    forbidden = (
        "PROMPT_KIT_SHORTCUT_STORAGE_KEY",
        "PROMPT_KIT_SHORTCUT_SCHEMA",
        "var promptShortcutBindings=",
        "function configurePromptShortcut(",
        "function removePromptShortcut(",
        "promptShortcutPromptId",
        "Save favorite prompt keyboard shortcut",
    )
    stale = [marker for marker in forbidden if marker in text]
    if stale:
        raise SystemExit(f"manual shortcut authority remains: {stale}")
    required = (
        "function catalogPromptShortcutBindings()",
        "bindings[digits]=promptId",
        "bindings['p'+digits]=promptId",
        "return catalogPromptShortcutBindings()",
        "revealPromptShortcutTarget(promptId,'instant')",
        "Every prompt has a natural numeric shortcut",
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise SystemExit(f"natural hotkey contract missing: {missing}")
    path.write_text(text, encoding="utf-8")


def repair_design() -> None:
    design = textwrap.dedent(
        """\
        # Prompt Kit hotkey program design

        ## Scope
        This document owns the keyboard-command boundary for Prompt Kit. Production behavior extends the existing runtime in `docs/prompt-kit-polish.js`; generated HTML is never hand-edited and the responsive-layout harness is not a second keyboard implementation owner.

        ## Current invariants
        - The canonical `PROMPTS` catalog owns prompt-number hotkeys for every prompt.
        - The bare numeric identity is the primary gesture: `126` → `P126`. `p126` remains a compatibility alias.
        - A prompt does not need to be a Favorite, recommended, or manually configured before its numeric hotkey works.
        - Manual prompt-shortcut persistence is retired. `promptKit.promptShortcuts.v1` is not production activation authority.
        - Completing a prompt-number sequence performs canonical copy + instant snap to the rendered card; it does not open prompt detail.
        - Favorites remain durable organizational state only. Favoriting and unfavoriting never create or revoke the catalog hotkey.
        - `sharedShortcut: true` is recommendation/discoverability metadata only; it does not authorize activation.
        - Keyboard commands are suppressed in `input`, `textarea`, `select`, and content-editable surfaces and for modified chords.
        - Header navigation is letter-only (`A`–`E`). Digits belong to prompt identity and never double as profile-tab commands.
        - Hotkey help is a projection of effective behavior, not a second truth source.

        ## Domain vocabulary
        - **ShortcutGesture**: a normalized key or sequence such as `f`, `[`, `]`, `126`, or compatibility form `p126`.
        - **PromptTarget**: canonical prompt identity such as `P126`.
        - **ShortcutRegistry**: effective built-ins plus prompt identities derived from the canonical `PROMPTS` catalog.
        - **ShortcutDispatcher**: keyboard-event orchestration and transient sequence-buffer owner.
        - **FilterVisibility**: sole owner of visible/hidden filter state.
        - **PromptNavigator**: translation from a PromptTarget to the existing reveal/center/copy behavior.

        There is no production `ShortcutStore` for prompt-number activation. Earlier persistence experiments remain historical/prototype evidence only.

        ## State ownership
        | State | Owner | Persistence |
        | --- | --- | --- |
        | Built-in commands | runtime shortcut table | code |
        | Prompt-number bindings | canonical `PROMPTS` catalog | generated registry |
        | Typed-sequence buffer | ShortcutDispatcher | none |
        | Filter visibility | FilterVisibility | none initially |
        | Favorite membership | existing Favorites owner | browser Favorites storage |
        | Recommended labels | canonical prompt metadata | generated registry |
        | Hotkey help rows | projection of runtime/catalog + metadata | none |

        Dependency direction:

        `keydown → ShortcutDispatcher → catalog-derived binding resolution → semantic action → existing DOM/copy adapters`

        No Favorite store, recommendation flag, generated HTML patch, or help row may become a second activation policy.

        ## Prompt identity behavior
        Starting state: `P11`, `P13`, `P111`, and `P126` exist in the catalog. No setup is required.

        - `126` resolves `P126` immediately, copies canonical `copyContent`, and snaps its card to center.
        - `p126` follows the same path as a compatibility alias.
        - `13` resolves `P13` immediately when no longer catalog identity shares that prefix.
        - `11` is also a prefix of `111`, so the dispatcher holds the shorter exact candidate until the 1.2-second sequence boundary.
        - `111` arriving before that boundary resolves `P111` and cancels the pending `P11` candidate.
        - Dots are visual separators while a prompt-number buffer is active: `p1.1` follows `P11`; `p1.11` follows `P111`.
        - When the prompt-number buffer is active, a nonmatching letter can settle a pending exact prompt and then continue to its normal command domain; header `A`–`E` remains independently usable.

        ## Failure boundaries
        - **Editable target:** ignore prompt hotkeys while the user is typing in an editable surface.
        - **Modified chord:** modifier-bearing input does not enter the prompt-number buffer.
        - **Unknown target:** a numeric candidate without a catalog prefix performs no prompt activation.
        - **Prefix ambiguity:** the shorter exact target waits for the sequence boundary; continued valid input wins.
        - **Reveal failure:** do not claim success or copy a different prompt when the canonical target cannot be rendered/revealed.

        ## Favorites and recommendations
        Favorites answer **what the user wants grouped**, not **which prompts are keyboard-addressable**. The Hotkeys panel may label Favorite and Recommended prompts for discoverability, but every canonical prompt already has its numeric route. Removing a Favorite therefore leaves its numeric hotkey available.

        ## Built-in command boundary
        - unmodified backtick `` ` `` toggles Hotkeys and keeps the core shortcut cluster reachable with one hand;
        - `/` focuses search;
        - `F` toggles filters, `[` hides them, and `]` shows them;
        - `Home` and `End` navigate the page;
        - `A`–`E` activate the five profile slots;
        - `Escape` closes/clears the active keyboard surface and resets transient prompt sequence state.

        ## Executable prototype status
        `docs/prompt-kit-hotkey-prototype.js` remains a seam/failure-model prototype. Its historical persistence-failure simulation is intentionally prototype-only; production prompt-number activation no longer loads, saves, configures, or validates a persisted shortcut binding.

        ## Superseded production decisions
        The following earlier decisions are explicitly superseded and must not be reintroduced:
        - Favorite-authorized prompt activation;
        - a Favorite prompt-ID Save field in Hotkeys;
        - `promptKit.promptShortcuts.v1` as an activation store;
        - requiring `p###` as the primary typed identity;
        - treating `sharedShortcut` recommendation metadata as activation authority.

        ## Routing hook for agents
        For hotkey, shortcut, keyboard navigation, Favorite shortcut, prompt-ID shortcut, or filter-key work, inspect in order:
        1. this design;
        2. `docs/prompt-kit-polish.js`;
        3. `tests/test_prompt_kit_hotkey_completion.py` and `tests/test_prompt_kit_hotkey_identity_runtime.py`;
        4. `tests/prompt_kit_hotkey_identity_browser_proof.py` and the observed-browser workflow;
        5. `scripts/build_prompt_kit_registry.py` for generated-site parity;
        6. interaction/cross-input contracts for collision regression evidence.

        Do not create another shortcut registry or patch generated HTML directly.

        ## Proof contract
        Completion requires all of the following on the exact candidate head:
        - production source asserts catalog-derived numeric authority and contains no manual prompt-shortcut persistence/configuration path;
        - focused runtime tests prove bare numeric identities, compatibility aliases, timeout/prefix behavior, editable/modifier safety, and header-domain separation;
        - generated `web/prompt-kit/index.html` is rebuilt through the canonical generator and matches source;
        - observed Chromium literally types bare `126` through the page keyboard path from a non-Favorite state, then verifies canonical P126 clipboard content and centered-card geometry;
        - the broader interaction/discovery/cross-input validators remain green.

        Repository/browser CI cannot certify every physical keyboard layout or every browser clipboard policy. Those environments remain the proof ceiling; they do not justify weakening the catalog-derived contract.

        ## Fixed implementation seam
        Production behavior is owned in `docs/prompt-kit-polish.js`; `web/prompt-kit/index.html` is rebuilt only through `scripts/build_prompt_kit_registry.py`. New hotkeys extend the existing dispatcher/state owners rather than introducing a second keyboard registry, second filter state owner, or generated-only patch.
        """
    )
    (ROOT / "docs" / "PROMPT_KIT_HOTKEY_PROGRAM_DESIGN.md").write_text(design, encoding="utf-8")


def repair_identity_runtime_test() -> None:
    content = textwrap.dedent(
        r'''\
        from __future__ import annotations

        import json
        import subprocess
        import unittest
        from pathlib import Path

        ROOT = Path(__file__).resolve().parents[1]
        POLISH = ROOT / "docs" / "prompt-kit-polish.js"
        DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"


        def function_block(text: str, name: str) -> str:
            start = text.index(f"function {name}(")
            brace = text.index("{", start)
            depth = 0
            quote = None
            escaped = False
            for index in range(brace, len(text)):
                char = text[index]
                if quote:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == quote:
                        quote = None
                    continue
                if char in ("'", '"', "`"):
                    quote = char
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : index + 1]
            raise AssertionError(f"unterminated JavaScript function: {name}")


        class PromptKitHotkeyIdentityRuntimeTests(unittest.TestCase):
            def test_production_dispatcher_uses_catalog_for_numeric_and_compatibility_identities(self) -> None:
                source = POLISH.read_text(encoding="utf-8")
                blocks = "\n\n".join(
                    function_block(source, name)
                    for name in (
                        "normalizePromptShortcutId",
                        "promptShortcutDigitGesture",
                        "catalogPromptShortcutBindings",
                        "resetPromptShortcutBuffer",
                        "schedulePromptShortcutBufferReset",
                        "promptShortcutHasLongerPrefix",
                        "effectivePromptShortcutBindings",
                        "handleConfiguredPromptShortcutKey",
                    )
                )
                script = f"""
        var PROMPT_KIT_SHORTCUT_SEQUENCE_TIMEOUT_MS=25;
        var PROMPTS=[{{id:'P11'}},{{id:'P13'}},{{id:'P111'}},{{id:'P126'}}];
        var promptShortcutBuffer='';
        var promptShortcutBufferTimer=null;
        var activations=[];
        function activatePromptShortcutTarget(promptId){{activations.push(promptId);return true}}
        {blocks}
        function eventStub(){{return{{preventDefault:function(){{}},stopImmediatePropagation:function(){{}}}}}}
        function press(key){{return handleConfiguredPromptShortcutKey(eventStub(),key)}}
        function resetProbe(){{resetPromptShortcutBuffer();activations=[]}}
        function sleep(ms){{return new Promise(function(resolve){{setTimeout(resolve,ms)}})}}
        function assert(condition,message){{if(!condition)throw new Error(message)}}
        (async function(){{
          assert(normalizePromptShortcutId('p1.1')==='P11','p1.1 normalization');
          assert(normalizePromptShortcutId('p1.11')==='P111','p1.11 normalization');
          assert(promptShortcutDigitGesture('P111')==='111','digit gesture');

          ['p','1','1'].forEach(press);
          assert(activations.length===0,'p11 fired before longer-prefix ambiguity closed');
          await sleep(40);
          assert(JSON.stringify(activations)==='["P11"]','p11 timeout resolution');

          resetProbe();
          ['p','1','3'].forEach(press);
          assert(JSON.stringify(activations)==='["P13"]','p13 exact resolution');

          resetProbe();
          ['p','1','1','1'].forEach(press);
          assert(JSON.stringify(activations)==='["P111"]','p111 longer exact resolution');

          resetProbe();
          ['1','1'].forEach(press);
          assert(activations.length===0,'digit 11 fired before longer-prefix ambiguity closed');
          await sleep(40);
          assert(JSON.stringify(activations)==='["P11"]','digit-only 11 timeout resolution');

          resetProbe();
          ['1','1','1'].forEach(press);
          assert(JSON.stringify(activations)==='["P111"]','digit-only 111 longer exact resolution');

          resetProbe();
          ['1','2','6'].forEach(press);
          assert(JSON.stringify(activations)==='["P126"]','digit-only 126 exact resolution');

          resetProbe();
          ['p','1','2','6'].forEach(press);
          assert(JSON.stringify(activations)==='["P126"]','p126 compatibility resolution');

          resetProbe();
          ['p','1','.','1'].forEach(press);
          assert(activations.length===0,'p1.1 fired before longer-prefix ambiguity closed');
          await sleep(40);
          assert(JSON.stringify(activations)==='["P11"]','p1.1 dotted timeout resolution');

          resetProbe();
          ['p','1','.','1','1'].forEach(press);
          assert(JSON.stringify(activations)==='["P111"]','p1.11 dotted longer resolution');

          console.log(JSON.stringify({{status:'PASS',cases:['p11','p13','p111','11','111','126','p126','p1.1','p1.11']}}));
        }})().catch(function(error){{console.error(error.stack||error);process.exit(1)}});
        """
                completed = subprocess.run(
                    ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
                )
                proof = json.loads(completed.stdout)
                self.assertEqual(proof["status"], "PASS")
                self.assertEqual(
                    proof["cases"],
                    ["p11", "p13", "p111", "11", "111", "126", "p126", "p1.1", "p1.11"],
                )

            def test_generated_runtime_contains_catalog_identity_dispatcher(self) -> None:
                source = POLISH.read_text(encoding="utf-8")
                deployed = DEPLOYED.read_text(encoding="utf-8")
                for name in (
                    "normalizePromptShortcutId",
                    "promptShortcutDigitGesture",
                    "catalogPromptShortcutBindings",
                    "schedulePromptShortcutBufferReset",
                    "promptShortcutHasLongerPrefix",
                    "effectivePromptShortcutBindings",
                    "handleConfiguredPromptShortcutKey",
                ):
                    self.assertEqual(function_block(source, name), function_block(deployed, name))
                for marker in (
                    "replace(/\\./g,'')",
                    "if(key==='.'&&promptShortcutBuffer)",
                    "if(exact&&!promptShortcutHasLongerPrefix(candidate,gestures))",
                    "return catalogPromptShortcutBindings()",
                    "bindings[digits]=promptId",
                    "bindings['p'+digits]=promptId",
                ):
                    self.assertIn(marker, deployed)

            def test_header_and_prompt_identity_domains_do_not_overlap(self) -> None:
                source = POLISH.read_text(encoding="utf-8")
                base = (ROOT / "docs" / "prompt-kit.js").read_text(encoding="utf-8")
                for digit in "12345":
                    self.assertNotIn(f"if(key==='{digit}')", source)
                    self.assertNotIn(f"case'{digit}'", base)
                for key in "ABCDE":
                    self.assertIn(f"{{key:'{key}'", source)


        if __name__ == "__main__":
            unittest.main()
        '''
    )
    (ROOT / "tests" / "test_prompt_kit_hotkey_identity_runtime.py").write_text(content, encoding="utf-8")


def repair_browser_and_contract_tests() -> None:
    for path in (
        "tests/prompt_kit_favorite_browser_proof.py",
        ".github/workflows/prompt-kit-observed-browser-proof.yml",
        "docs/PROMPT_KIT_OPERATOR_GUIDE.md",
        "tests/test_prompt_kit_hotkey_completion.py",
    ):
        (ROOT / path).write_text(git_show(path), encoding="utf-8")

    identity = ROOT / "tests" / "prompt_kit_hotkey_identity_browser_proof.py"
    text = identity.read_text(encoding="utf-8")
    text = replace_once(text, 'TARGETS = ("P11", "P13", "P111")', 'TARGETS = ("P11", "P13", "P111", "P126")', "identity targets")
    setup_pattern = re.compile(
        r'\n            # Configure all three overlapping identities through the real product UI\..*?            page\.evaluate\("document\.activeElement && document\.activeElement\.blur\(\)"\)\n',
        re.DOTALL,
    )
    text, count = setup_pattern.subn(
        "\n            # Natural prompt hotkeys are catalog-derived; no Favorite or manual Save setup is required.\n",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit("identity browser manual setup block missing")
    press_anchor = """            def press(sequence: str) -> None:
                for char in sequence:
                    page.keyboard.press(char)
"""
    p126_probe = press_anchor + """
            p126_favorite = page.locator('[data-prompt-id="P126"] .prompt-favorite-btn')
            if p126_favorite.count() != 1 or p126_favorite.get_attribute('aria-pressed') != 'false':
                raise AssertionError('P126 proof did not start from a non-favorite state')

            set_clipboard("sentinel-126")
            press("126")
            page.wait_for_timeout(220)
            p126_final = clipboard()
            p126_geometry = page.evaluate("""() => {
              const card=document.querySelector('[data-prompt-id="P126"]');
              if(!card)return null;
              const rect=card.getBoundingClientRect();
              return {center:(rect.top+rect.bottom)/2,viewport:window.innerHeight/2};
            }""")
            p126_snapped = bool(
                p126_geometry
                and abs(p126_geometry["center"] - p126_geometry["viewport"]) <= max(120, 900 * 0.18)
            )
            observations.append({
                "id": "numeric_p126_copies_and_snaps",
                "event": "typing bare 126 copies P126 and centers its canonical card without Favorite/manual setup",
                "occurred": True,
                "passed": p126_final == expected["P126"] and p126_snapped,
                "clipboard_matches": p126_final == expected["P126"],
                "favorite_required": False,
                "geometry": p126_geometry,
                "snapped": p126_snapped,
            })

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
"""
    text = replace_once(text, press_anchor, p126_probe, "identity press helper")
    text = text.replace('"scenario": "overlapping-and-dotted-prompt-identity-hotkeys"', '"scenario": "catalog-derived-numeric-prompt-hotkeys"', 1)
    text = text.replace(
        '"statement": "p11, p13, p111, p1.1, and p1.11 resolve to distinct canonical prompt identities without numeric header collisions"',
        '"statement": "bare 126 resolves P126 with canonical copy + snap without Favorite setup while p-prefixed compatibility, prefix disambiguation, and header separation remain intact"',
        1,
    )
    identity.write_text(text, encoding="utf-8")

    hotkey_test = ROOT / "tests" / "test_prompt_kit_hotkey_completion.py"
    text = hotkey_test.read_text(encoding="utf-8")
    anchor = "    def test_prompt_sequence_owns_digits_and_header_navigation_is_letter_only(self) -> None:\n"
    extra = textwrap.dedent(
        '''\
            def test_keyboard_digit_grammar_does_not_require_leading_p(self) -> None:
                source = POLISH.read_text(encoding="utf-8")
                readme = README.read_text(encoding="utf-8")
                self.assertIn("`126` → `P126`", readme)
                self.assertIn("leading `p`/`P` remains a compatibility alias", readme)
                self.assertIn("function catalogPromptShortcutBindings()", source)
                self.assertIn("bindings[digits]=promptId", source)
                self.assertIn("bindings['p'+digits]=promptId", source)

        '''
    )
    if anchor not in text:
        raise SystemExit("hotkey completion grammar insertion anchor missing")
    text = text.replace(anchor, extra + anchor, 1)
    human_anchor = '        self.assertIn("one hand", design)\n'
    negative = textwrap.dedent(
        '''\
                for stale in (
                    "Every current Favorite automatically publishes",
                    "Manual shortcut configuration remains a compatibility/repair path",
                    "**ShortcutStore**: persistence port",
                    "Favoriting from either surface immediately makes the canonical lower-case prompt ID an effective hotkey",
                ):
                    self.assertNotIn(stale, design)
        '''
    )
    if human_anchor not in text:
        raise SystemExit("hotkey completion design guard anchor missing")
    text = text.replace(human_anchor, human_anchor + negative, 1)
    hotkey_test.write_text(text, encoding="utf-8")


def repair_readme_and_discovery() -> None:
    path = ROOT / "web" / "README.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("### Hotkeys\n")
    end = text.index("### Header navigation contract\n", start)
    section = textwrap.dedent(
        """\
        ### Hotkeys

        The glowing **Hotkeys** module beside the floating reference control is the in-product shortcut reference and five-tab profile editor. Select it or press the unmodified **backtick** key (`` ` ``) to toggle it; select outside it, use its close control, or press **Esc** to dismiss it. The five header identities are always `A`–`E`; their visible names and profile compositions are user configuration. Numeric keys are never header navigation.

        | Key | Action |
        |---|---|
        | `` ` `` | Show / hide Hotkeys |
        | `126` | Example prompt-number route: copy + snap to `P126` |
        | `/` | Focus search |
        | `A` | All |
        | `B` | Standard |
        | `C` | Favorites |
        | `D` | SAS |
        | `E` | PM |
        | `R` | Toggle reference panel |
        | `F` | Show / hide filters |
        | `[` | Hide filters |
        | `]` | Show filters |
        | `Home` | Scroll to top |
        | `End` | Scroll to bottom |
        | `Esc` | Close the active surface or clear filters |

        Every canonical prompt has a natural numeric keyboard route. Type the digits after `P`: **`126` → `P126`**. A leading `p`/`P` remains a compatibility alias (`p126` → `P126`), not a setup requirement. No Favorite and no Hotkeys-panel Save step is required. Sequences expire after 1.2 seconds and are ignored in editable fields. If one catalog ID prefixes another, the shorter exact match waits for that boundary and continued typing selects the longer identity. Dots remain visual separators while a prompt-number buffer is active. Completing the sequence clears transient restrictions needed to reveal the target, copies canonical prompt content, and instantly snaps the canonical card to center without opening detail.

        Favorites are organizational state only. Favoriting or unfavoriting a prompt never creates or revokes its numeric hotkey. Registry `sharedShortcut: true` metadata may label a prompt **Recommended** in Hotkeys, but recommendation metadata is not activation authority. Manual prompt-shortcut persistence/configuration is retired.

        **Mode separation for known prompt IDs:**
        - **Mouse:** locate the card, then use Open/Copy.
        - **Keyboard:** catalog-derived digits such as `126` perform copy + instant snap.
        - **Phone:** use **Go to P#** (P prefix shown; type digits) to reach the canonical card/detail path documented for touch.

        Navigation shortcuts are ignored while typing in an input, textarea, select, or content-editable surface. Modified backtick chords are ignored. Top/bottom scrolling respects reduced-motion preferences.

        """
    )
    path.write_text(text[:start] + section + text[end:], encoding="utf-8")

    path = ROOT / "tests" / "test_prompt_kit_discovery.py"
    text = path.read_text(encoding="utf-8")
    for old, new in (
        ("revealPromptShortcutTarget(promptId)", "revealPromptShortcutTarget(promptId,'instant')"),
        ("Copy + reveal ", "Copy + snap to "),
        (
            'self.assertIn("**does not open prompt detail**", guide)',
            'self.assertIn("type **`126`**", guide)\n        self.assertIn("No Favorite and no Hotkeys-panel Save step is required.", guide)',
        ),
        (
            'self.assertIn("**without opening prompt detail**", web)',
            'self.assertIn("without opening detail", web)',
        ),
    ):
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit(f"discovery anchor missing: {old}")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    repair_runtime()
    repair_design()
    repair_identity_runtime_test()
    repair_browser_and_contract_tests()
    repair_readme_and_discovery()
    print("natural hotkey mainline repair staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
