from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'tests' / 'test_prompt_kit_filtering_access.py'
text = path.read_text(encoding='utf-8')
old = '''        hotkeys = polish[polish.index("function installCompactBrowsingHotkeys()") : polish.index("window.appendPromptCard")]
        key_one = hotkeys[hotkeys.index("if(e.key==='1')") : hotkeys.index("if(e.key==='4')")]
        self.assertIn("e.preventDefault();", key_one)
        self.assertIn("e.stopImmediatePropagation();", key_one)
        self.assertIn("activateAllPromptsView();", key_one)
'''
new = '''        hotkeys = polish[polish.index("function installCompactBrowsingHotkeys()") : polish.index("window.appendPromptCard")]
        self.assertIn("var key=String(e.key||'').toLowerCase();", hotkeys)
        key_one = hotkeys[hotkeys.index("if(key==='1')") : hotkeys.index("if(key==='4')")]
        self.assertIn("e.preventDefault();", key_one)
        self.assertIn("e.stopImmediatePropagation();", key_one)
        self.assertIn("activateAllPromptsView();", key_one)
'''
if text.count(old) != 1:
    raise SystemExit(f'atomic-reset hotkey assertion anchor mismatch: {text.count(old)}')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
