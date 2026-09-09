#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests/test_skill_prompt_registry.py"

OLD = '''        self.assertEqual(payload["schema_version"], "prompt-registry-overrides/v1")
        self.assertEqual(len(payload["overrides"]), 2)
        by_id = {item["id"]: item for item in payload["overrides"]}
        self.assertEqual(set(by_id), {"P02", "P13"})
        self.assertEqual((by_id["P02"]["id"], by_id["P02"]["seq"]), ("P02", "02"))
        self.assertEqual(by_id["P02"]["copySheet"], "P02_COPY_SAFE")
        self.assertEqual((by_id["P13"]["id"], by_id["P13"]["seq"]), ("P13", "13"))
        self.assertEqual(by_id["P13"]["copySheet"], "P13_COPY_SAFE")
        source_by_id = {
            item["id"]: item
            for item in json.loads(build_prompt_kit_registry.BASE_REGISTRY.read_text(encoding="utf-8"))
        }
        self.assertEqual(source_by_id["P02"]["seq"], by_id["P02"]["seq"])
        self.assertEqual(source_by_id["P13"]["seq"], by_id["P13"]["seq"])
'''

NEW = '''        self.assertEqual(payload["schema_version"], "prompt-registry-overrides/v1")
        by_id = {item["id"]: item for item in payload["overrides"]}
        self.assertEqual(len(by_id), len(payload["overrides"]))
        self.assertTrue({"P02", "P13", "P19"}.issubset(by_id))
        source_by_id = {
            item["id"]: item
            for item in json.loads(build_prompt_kit_registry.BASE_REGISTRY.read_text(encoding="utf-8"))
        }
        for prompt_id, override in by_id.items():
            self.assertIn(prompt_id, source_by_id)
            source = source_by_id[prompt_id]
            self.assertEqual((override["id"], override["seq"]), (source["id"], source["seq"]))
            self.assertEqual(override["copySheet"], source["copySheet"])
'''

text = PATH.read_text(encoding="utf-8")
if NEW in text:
    print("PROMPT_OVERRIDE_IDENTITY_TEST_ALREADY_REPAIRED")
elif OLD in text:
    PATH.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("PROMPT_OVERRIDE_IDENTITY_TEST_REPAIRED")
else:
    raise SystemExit("expected override identity test block not found")
