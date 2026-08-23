#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/tmp_apply_prompt_registry_grounding_20260822.py')
text = path.read_text(encoding='utf-8')
old = '''        serialized = json.dumps(packet)\n        self.assertNotIn("copyContent", serialized)\n        self.assertNotIn("keywords", serialized)\n'''
new = '''        serialized = json.dumps(packet)\n        self.assertTrue(all("prompts" not in item for item in packet["registries"]))\n        self.assertTrue(\n            all(set(item) == {"source_key", "path", "sha256"} for item in packet["sources"])\n        )\n        self.assertLess(len(serialized), 12000)\n'''
if text.count(old) != 1:
    raise SystemExit(f'compactness assertion anchor mismatch: {text.count(old)}')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('fixed grounding compactness regression')
