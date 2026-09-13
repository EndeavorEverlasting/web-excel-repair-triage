#!/usr/bin/env python3
import json
from pathlib import Path
from src.logic import compute

payload = {"cached_result": compute(5), "input": 5}
Path("generated/state.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
print("rebuilt generated/state.json")
