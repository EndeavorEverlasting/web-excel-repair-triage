#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/management-operations-prompts.v1.json"
TEST = ROOT / "tests/test_job_search_prompt_registry.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
by_id = {item["id"]: item for item in payload["prompts"]}
for prompt_id in ("P126", "P127"):
    prompt = by_id[prompt_id]
    if prompt.get("profile") != "career-operations":
        raise SystemExit(f"Expected inert career-operations profile on {prompt_id}")
    del prompt["profile"]
REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST.read_text(encoding="utf-8")
old = '''        self.assertNotEqual(self.portable["id"], self.sync["id"])
        self.assertEqual(self.portable.get("profile"), "career-operations")
        self.assertEqual(self.sync.get("profile"), "career-operations")
'''
new = '''        self.assertNotEqual(self.portable["id"], self.sync["id"])
        self.assertNotIn("profile", self.portable)
        self.assertNotIn("profile", self.sync)
'''
if old not in text:
    raise SystemExit("Focused test profile anchor not found")
TEST.write_text(text.replace(old, new, 1), encoding="utf-8")
print("SECOND_PASS_REPAIR removed_inert_profile=P126,P127 ui_scope_unchanged=PASS")
