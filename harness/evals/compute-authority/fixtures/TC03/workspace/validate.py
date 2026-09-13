#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from src.logic import compute

expected = compute(5)
state = json.loads(Path("generated/state.json").read_text(encoding="utf-8"))
if state.get("cached_result") != expected:
    print("FAIL: generated state", state, "expected", expected)
    raise SystemExit(1)
print("ok")
