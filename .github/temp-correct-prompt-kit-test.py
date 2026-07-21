#!/usr/bin/env python3
"""Correct the generated builder-source assertion before publication."""
from pathlib import Path

path = Path("tests/test_prompt_kit_header_contract.py")
text = path.read_text(encoding="utf-8")
old_marker = "        marker = f'data-cat=\\\\\"{category}\\\\\"'\n"
new_marker = "        marker = f'data-cat=\"{category}\"'\n"
old_kbd = "        assert f'>{label}<span class=\\\\\"kbd\\\\\">{key}</span>' in source\n"
new_kbd = "        assert f'>{label}<span class=\"kbd\">{key}</span>' in source\n"
if text.count(old_marker) != 1 or text.count(old_kbd) != 1:
    raise SystemExit("unexpected generated builder assertion shape")
path.write_text(text.replace(old_marker, new_marker).replace(old_kbd, new_kbd), encoding="utf-8")
