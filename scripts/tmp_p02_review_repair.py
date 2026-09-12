from __future__ import annotations

import json
from pathlib import Path

PROMPT_PATH = Path("registry/prompts/prompt-overrides.v1.json")
TEST_PATH = Path("tests/test_skill_prompt_registry.py")

payload = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))
p02 = next(item for item in payload["overrides"] if item["id"] == "P02")

old_decl = (
    "- State a compact sprint declaration: mission, lane, owned scope, forbidden scope, dependencies, collision risks, "
    "expected artifacts, validation, and proof ceiling."
)
new_decl = (
    "- State a compact sprint declaration: mission, lane, owned scope, forbidden scope, dependencies, collision risks, "
    "expected artifacts, validation, proof ceiling, and explicit mutation authority for every planned tracked-file, commit, "
    "push, PR creation/update, and merge action."
)
if old_decl not in p02["copyContent"]:
    raise SystemExit("P02 sprint declaration marker not found")
p02["copyContent"] = p02["copyContent"].replace(old_decl, new_decl, 1)

old_gate = (
    "Recovered claims are reconciled as current, historical, superseded, contradicted, or unknown; actual repo/artifact "
    "movement plus validation or an exact blocker exists;"
)
new_gate = (
    "Recovered claims are reconciled as current, historical, superseded, contradicted, or unknown; mutation authority is "
    "explicit before tracked-file, commit, push, PR, or merge actions; actual repo/artifact movement plus validation or an "
    "exact blocker exists;"
)
if old_gate not in p02["proofGate"]:
    raise SystemExit("P02 proofGate marker not found")
p02["proofGate"] = p02["proofGate"].replace(old_gate, new_gate, 1)
PROMPT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST_PATH.read_text(encoding="utf-8")
needle = '''        for phrase in (\n            "CONTEXT IS A STARTING MAP, NOT A SEARCH BOUNDARY",\n            "PROVIDED-CONTEXT MODE",\n            "sufficient to begin repository exploration and execution",\n            "cannot block repository/provider inspection",\n            "do not make any one recovery surface a prerequisite for another",\n        ):\n            self.assertIn(phrase, content)\n\n'''
replacement = '''        for phrase in (\n            "CONTEXT IS A STARTING MAP, NOT A SEARCH BOUNDARY",\n            "PROVIDED-CONTEXT MODE",\n            "sufficient to begin repository exploration and execution",\n            "cannot block repository/provider inspection",\n            "do not make any one recovery surface a prerequisite for another",\n            "perform multiple targeted retrievals rather than one broad query",\n            "Previous chat resolved: <name and whether retrieval succeeded, including recovery mode>",\n            "Recovery ledger: <material decisions, superseded state, proof floor, unresolved unknowns>",\n            "Remaining gaps: <only still-open items>",\n        ):\n            self.assertIn(phrase, content)\n\n    def test_p02_declares_mutation_authority_before_repository_changes(self) -> None:\n        prompt = {\n            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()\n        }["P02"]\n        content = prompt["copyContent"]\n        for phrase in (\n            "explicit mutation authority",\n            "tracked-file",\n            "commit",\n            "push",\n            "PR creation/update",\n            "merge action",\n        ):\n            self.assertIn(phrase, content)\n        self.assertIn(\n            "mutation authority is explicit before tracked-file, commit, push, PR, or merge actions",\n            prompt["proofGate"],\n        )\n\n'''
if needle not in text:
    raise SystemExit("P02 rich handoff test block not found")
text = text.replace(needle, replacement, 1)
TEST_PATH.write_text(text, encoding="utf-8")
