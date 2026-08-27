#!/usr/bin/env python3
from pathlib import Path

path = Path('.github/workflows/prompt-kit-web.yml')
text = path.read_text(encoding='utf-8')
old = "python -m unittest tests.test_prompt_kit_portability tests.test_prompt_kit_portability_regressions tests.test_prompt_kit_portable_health -v"
new = "python -m unittest tests/test_prompt_kit_portability.py tests/test_prompt_kit_portability_regressions.py tests/test_prompt_kit_portable_health.py -v"
if old not in text:
    raise SystemExit('portable unittest command anchor missing')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
print('preserved literal portability test-path contract')
