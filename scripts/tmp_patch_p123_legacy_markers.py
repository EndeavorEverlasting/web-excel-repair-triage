#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p123 = next(item for item in payload["prompts"] if item.get("id") == "P123")

old_expected = "and canonical ledger write with exact mutation receipt when writable/authorized or row-ready records otherwise"
new_expected = "and canonical ledger records written with exact mutation receipt when writable/authorized or row-ready records otherwise"
if old_expected not in p123["expectedOutput"] and new_expected not in p123["expectedOutput"]:
    raise SystemExit("P123 expectedOutput legacy receipt anchor missing")
p123["expectedOutput"] = p123["expectedOutput"].replace(old_expected, new_expected, 1)

old_subprocess = "Tests must import subprocess when used"
new_subprocess = "Tests must import `subprocess` when used"
if old_subprocess not in p123["copyContent"] and new_subprocess not in p123["copyContent"]:
    raise SystemExit("P123 subprocess legacy marker anchor missing")
p123["copyContent"] = p123["copyContent"].replace(old_subprocess, new_subprocess, 1)

if len(p123["copyContent"]) > 12000:
    raise SystemExit(f"P123 copyContent exceeds helper ceiling after reconciliation: {len(p123['copyContent'])}")

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"P123_LEGACY_MARKER_RECONCILIATION_PASS chars={len(p123['copyContent'])}")
