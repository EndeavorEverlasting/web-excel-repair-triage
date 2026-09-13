#!/usr/bin/env python3
import json
from pathlib import Path
from src.feature import ENABLE_GREETING, greeting

Path("generated/feature.json").write_text(
    json.dumps({"ENABLE_GREETING": ENABLE_GREETING, "greeting": greeting()}) + "\n",
    encoding="utf-8",
)
print("synced generated/feature.json")
