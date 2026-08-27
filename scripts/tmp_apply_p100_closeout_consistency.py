from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "ai-engineering-level-up-prompts.v1.json"
TESTS = ROOT / "tests" / "test_ai_engineering_level_up.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p100 = next(item for item in payload["prompts"] if item.get("id") == "P100")
copy = p100["copyContent"]
anchor = "If the failure invalidates a `done/closed` claim, reopen closure certification."
section = """

7. CLOSEOUT CONSISTENCY CHECK
Before accepting a terminal closeout, cross-check REMAINING GAPS, RISKS, BLOCKERS, INTEGRATION STATE, and any acknowledged overlapping branch or identity conflict against NEXT ACTION/NEXT COMMAND. If those fields describe a safe executable continuation, `none; no safe actionable work remains` contradicts the available evidence and is itself a FAITHFULNESS_CONTEXT_IGNORED closure failure: reopen closure and execute or route the action. A true terminal case whose material items are all proven, blocked, unsafe with evidence, or out of scope may still use `none`; do not manufacture work merely to avoid a terminal result.
"""
if "7. CLOSEOUT CONSISTENCY CHECK" not in copy:
    if copy.count(anchor) != 1:
        raise SystemExit("P100 closeout-certification anchor missing or ambiguous")
    copy = copy.replace(anchor, anchor + section, 1)
    p100["copyContent"] = copy

for keyword in ("closeout contradiction", "no safe actionable work"):
    if keyword not in p100["keywords"]:
        p100["keywords"].append(keyword)

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_text = TESTS.read_text(encoding="utf-8")
method_anchor = "    def test_p68_repeats_context_refactor_until_fixed_point_and_mainline(self) -> None:\n"
method = '''    def test_p100_rejects_contradictory_terminal_closeout_and_preserves_true_terminal_case(self) -> None:\n        prompts = build_prompt_kit_registry.load_prompt_registry()\n        by_id = {item["id"]: item for item in prompts}\n        p100 = by_id["P100"]["copyContent"]\n        for phrase in (\n            "7. CLOSEOUT CONSISTENCY CHECK",\n            "REMAINING GAPS, RISKS, BLOCKERS, INTEGRATION STATE",\n            "acknowledged overlapping branch or identity conflict",\n            "none; no safe actionable work remains",\n            "FAITHFULNESS_CONTEXT_IGNORED closure failure",\n            "reopen closure and execute or route the action",\n            "A true terminal case",\n            "do not manufacture work",\n        ):\n            self.assertIn(phrase, p100)\n        self.assertIn("closeout contradiction", by_id["P100"]["keywords"])\n        self.assertIn("no safe actionable work", by_id["P100"]["keywords"])\n\n'''
if "test_p100_rejects_contradictory_terminal_closeout_and_preserves_true_terminal_case" not in test_text:
    if method_anchor not in test_text:
        raise SystemExit("AI engineering test insertion anchor missing")
    test_text = test_text.replace(method_anchor, method + method_anchor, 1)
    TESTS.write_text(test_text, encoding="utf-8")

print("P100 closeout consistency repair staged")
