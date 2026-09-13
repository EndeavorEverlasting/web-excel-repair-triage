#!/usr/bin/env python3
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
assert "42" in text
print("docs contract ok")
