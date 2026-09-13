#!/usr/bin/env python3
import json
from pathlib import Path
from src.core import value
data = json.loads(Path("generated/out.json").read_text(encoding="utf-8"))
assert data["value"] == value()
print("generated ok")
