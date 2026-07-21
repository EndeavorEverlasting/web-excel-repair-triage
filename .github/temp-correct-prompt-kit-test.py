#!/usr/bin/env python3
"""Correct generated builder-source assertions before publication."""
from pathlib import Path

path = Path("tests/test_prompt_kit_header_contract.py")
text = path.read_text(encoding="utf-8")
replacements = {
    "        marker = f'data-cat=\\\\\"{category}\\\\\"'\n": "        marker = f'data-cat=\"{category}\"'\n",
    "        position = source.find(marker)\n": "        position = header_source.find(marker)\n",
    "        assert f'>{label}<span class=\\\\\"kbd\\\\\">{key}</span>' in source\n": "        assert f'>{label}<span class=\"kbd\">{key}</span>' in header_source\n",
}
source_line = "    source = BUILDER.read_text(encoding=\"utf-8\")\n"
header_line = (
    source_line
    + "    header_source = source.split(\"html.append('      <div class=\\\"cat-tabs\\\">')\", 1)[1]"
      ".split(\"html.append('      </div>')\", 1)[0]\n"
)
if text.count(source_line) != 1:
    raise SystemExit("unexpected builder source-loading shape")
text = text.replace(source_line, header_line)
for old, new in replacements.items():
    if text.count(old) != 1:
        raise SystemExit(f"unexpected generated assertion shape: {old!r}")
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
