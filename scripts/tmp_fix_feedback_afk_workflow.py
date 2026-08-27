#!/usr/bin/env python3
from pathlib import Path

path = Path('.github/workflows/prompt-kit-web.yml')
text = path.read_text(encoding='utf-8')
required = (
    'tests/test_prompt_kit_portability.py',
    'tests/test_prompt_kit_portability_regressions.py',
    'tests/test_prompt_kit_portable_health.py',
)
if all(marker in text for marker in required):
    print('literal portability test-path contract already present')
    raise SystemExit(0)
replacements = (
    ('tests.test_prompt_kit_portability_regressions', 'tests/test_prompt_kit_portability_regressions.py'),
    ('tests.test_prompt_kit_portable_health', 'tests/test_prompt_kit_portable_health.py'),
    ('tests.test_prompt_kit_portability', 'tests/test_prompt_kit_portability.py'),
)
changed = text
for old, new in replacements:
    changed = changed.replace(old, new)
missing = [marker for marker in required if marker not in changed]
if missing:
    raise SystemExit(f'portable unittest markers still missing after repair: {missing}')
path.write_text(changed, encoding='utf-8')
print('preserved literal portability test-path contract')
