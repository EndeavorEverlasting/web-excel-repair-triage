from __future__ import annotations

import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLISH = ROOT / "docs" / "prompt-kit-polish.js"
GAMEPLAY = ROOT / "docs" / "prompt-kit-preference-gameplay.js"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
BASE_BUILDER = ROOT / "build_prompt_kit.py"


class PromptKitFavoriteGameplayTests(unittest.TestCase):
    def test_favorite_shortcut_reaches_terminal_copy_instead_of_detail_panel(self) -> None:
        source = POLISH.read_text(encoding="utf-8")
        block = source[source.index("function openPromptShortcutTarget"):source.index("function handleConfiguredPromptShortcutKey")]
        self.assertIn("copyPrompt(promptId);", block)
        self.assertNotIn("showPromptDetail", block)
        self.assertIn("label.textContent='Copy '+promptId;", source)
        self.assertIn("to copy it immediately", source)

    def test_semantic_usage_is_recorded_only_inside_success_callback(self) -> None:
        source = GAMEPLAY.read_text(encoding="utf-8")
        copy_block = re.search(r"root\.copyPrompt=function\(id\)\{.*?\n\};", source, re.S)
        self.assertIsNotNone(copy_block)
        block = copy_block.group(0)
        self.assertIn("var recorded=false", block)
        self.assertIn("if(recorded)return;recorded=true;recordSuccessfulCopy(id);root.showCopyConfirmation(id)", block)
        self.assertNotIn("recordSuccessfulCopy(id);\n  root.copyToClipboard", block)
        self.assertIn("state=loadState();", source[source.index("function recordSuccessfulCopy"):source.index("function rows")])
        self.assertIn("STORAGE_KEY='promptKit.usage.v1'", source)
        self.assertIn("SCHEMA='prompt-kit-usage/v1'", source)

    def test_success_callback_is_exactly_once_and_tabs_merge_latest_storage(self) -> None:
        source = GAMEPLAY.read_text(encoding="utf-8")
        harness = textwrap.dedent(
            r"""
            const vm = require('vm');
            const fs = require('fs');
            const source = fs.readFileSync(process.argv[1], 'utf8');
            const store = new Map();
            const localStorage = {
              getItem(key){ return store.has(key) ? store.get(key) : null; },
              setItem(key,value){ store.set(key,String(value)); }
            };
            function tab(callbackMode){
              let confirmations = 0;
              const root = {
                PROMPTS:[
                  {id:'P01',seq:'1',name:'One',type:'BUILD',copyContent:'one'},
                  {id:'P02',seq:'2',name:'Two',type:'VALIDATE',copyContent:'two'}
                ],
                localStorage,
                copyToClipboard(text,success){
                  if(callbackMode==='twice'){ success(); success(); return; }
                  if(callbackMode==='once'){ success(); return; }
                  if(callbackMode==='throw') throw new Error('clipboard failed');
                },
                showCopyConfirmation(){ confirmations += 1; },
                configuredPromptShortcutIds(){ return []; },
                isFavoritePrompt(){ return false; }
              };
              const context = {globalThis:root, console};
              vm.runInNewContext(source, context);
              return {root, confirmations:()=>confirmations};
            }
            const first = tab('twice');
            const second = tab('once');
            first.root.copyPrompt('P01');
            let afterFirst = JSON.parse(localStorage.getItem('promptKit.usage.v1'));
            if(afterFirst.totalCopies !== 1 || afterFirst.byPrompt.P01.count !== 1 || first.confirmations() !== 1){
              throw new Error('duplicate success callback was not de-duplicated');
            }
            second.root.copyPrompt('P02');
            let afterSecond = JSON.parse(localStorage.getItem('promptKit.usage.v1'));
            if(afterSecond.totalCopies !== 2 || afterSecond.byPrompt.P01.count !== 1 || afterSecond.byPrompt.P02.count !== 1){
              throw new Error('stale second tab overwrote latest usage state');
            }
            const failure = tab('never');
            failure.root.copyPrompt('P01');
            let afterFailure = JSON.parse(localStorage.getItem('promptKit.usage.v1'));
            if(afterFailure.totalCopies !== 2){ throw new Error('failed copy changed usage'); }
            const throwing = tab('throw');
            try { throwing.root.copyPrompt('P01'); } catch(error) {}
            let afterThrow = JSON.parse(localStorage.getItem('promptKit.usage.v1'));
            if(afterThrow.totalCopies !== 2){ throw new Error('throwing copy changed usage'); }
            console.log('gameplay runtime accounting: PASS');
            """
        )
        completed = subprocess.run(
            ["node", "-e", harness, str(GAMEPLAY)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("gameplay runtime accounting: PASS", completed.stdout)
        self.assertIn("state=loadState();", source)

    def test_dashboard_is_interactive_game_like_and_badges_are_deferred(self) -> None:
        source = GAMEPLAY.read_text(encoding="utf-8")
        for marker in (
            "Preference Dashboard",
            "Prompt Playbook",
            "LEVEL_SIZE=5",
            "Most used prompts",
            "Preference signals",
            "Favorite loadout",
            "data-dashboard-copy",
            "Only successful clipboard writes earn progress",
            "PromptKitPreferenceGameplay",
        ):
            self.assertIn(marker, source)
        self.assertNotIn("Badge Cabinet", source)

    def test_p99_makes_prompt_only_completion_invalid_for_runtime_requests(self) -> None:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        p99 = next(prompt for prompt in payload["prompts"] if prompt["id"] == "P99")
        combined = "\n".join(str(p99.get(field, "")) for field in ("expectedOutput", "nextStep", "proofGate", "copyContent"))
        for marker in (
            "RUNTIME ACCEPTANCE WHEN THE USER ASKED FOR BEHAVIOR",
            "successful clipboard write",
            "exactly one semantic usage",
            "live dashboard refresh",
            "Prompt-only or contract-only work is incomplete",
            "badges are a separate future capability",
        ):
            self.assertIn(marker, combined)

    def test_builder_owns_gameplay_runtime_and_generated_site_contains_it(self) -> None:
        builder = BUILDER.read_text(encoding="utf-8")
        base_builder = BASE_BUILDER.read_text(encoding="utf-8")
        source = GAMEPLAY.read_text(encoding="utf-8")
        deployed = DEPLOYED.read_text(encoding="utf-8")
        self.assertIn("PREFERENCE_GAMEPLAY_RUNTIME", builder)
        self.assertIn("preference_gameplay_script", builder)
        self.assertIn("var PROMPTS=", base_builder)
        self.assertIn("root.PROMPTS", source)
        self.assertIn(source, deployed)
        self.assertIn("copyPrompt(promptId);", deployed)
        self.assertIn("if(recorded)return;recorded=true;recordSuccessfulCopy(id);root.showCopyConfirmation(id)", deployed)


if __name__ == "__main__":
    unittest.main()
