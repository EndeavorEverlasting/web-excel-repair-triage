#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "docs" / "prompts.json"
prompts = json.loads(path.read_text(encoding="utf-8"))
p07 = next(item for item in prompts if item["id"] == "P07")
required = "branch or PR alone is insufficient"
if required not in p07["proofGate"]:
    p07["proofGate"] = p07["proofGate"].rstrip(" .") + "; a branch or PR alone is insufficient."
path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
