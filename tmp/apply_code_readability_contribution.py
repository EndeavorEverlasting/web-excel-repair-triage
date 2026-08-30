#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "tmp/code-readability-prompt-draft.json"
DOCS = ROOT / "docs/prompts.json"
BUILD = ROOT / "build_prompt_kit.py"
TESTS = ROOT / "tests/test_spec_architecture_prompt_registry.py"
NAME = "Repository Code Readability & Structural Refactorer"


def run(*args: str) -> str:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    print(proc.stdout, end="")
    return proc.stdout


def insert_once(text: str, anchor: str, addition: str, *, before: bool = False) -> str:
    if addition.strip() in text:
        return text
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f"Expected exactly one anchor {anchor!r}; found {count}")
    replacement = addition + anchor if before else anchor + addition
    return text.replace(anchor, replacement, 1)


inspect = json.loads(run(sys.executable, "scripts/prompt_registry_ops.py", "inspect"))
choices = {item["registry_id"]: item for item in inspect["registries"]}
route = choices.get("spec-architecture-prompts")
if not route or "spec-architecture" not in route.get("profiles", []):
    raise SystemExit("spec-architecture routing is not uniquely evidenced by helper inspect")
print(json.dumps({
    "routing_receipt": {
        "next_id_before_add": inspect["next_id"],
        "registry_id": route["registry_id"],
        "registry_path": route["path"],
        "profiles": route["profiles"],
    }
}, indent=2))

receipt = json.loads(run(
    sys.executable,
    "scripts/prompt_registry_ops.py",
    "add",
    "--input",
    str(DRAFT.relative_to(ROOT)),
    "--registry",
    "spec-architecture-prompts",
))
new_id = receipt["id"]
print(json.dumps({"helper_receipt": receipt}, indent=2))

prompts = json.loads(DOCS.read_text(encoding="utf-8"))
by_id = {prompt["id"]: prompt for prompt in prompts}
for prompt_id in ("P03", "P07", "P14"):
    if prompt_id not in by_id:
        raise SystemExit(f"Missing canonical prompt {prompt_id}")

p03 = by_id["P03"]
p03_line = "- prefer a real tested slice over broad documentation or speculative refactoring\n"
p03_add = (
    f"- do not misclassify evidenced structural editability debt as speculative refactoring: "
    f"when tangled, duplicated, mixed-responsibility, or oversized source materially raises change risk "
    f"for humans or agents, route a bounded cleanup to {new_id} rather than letting green behavior hide the debt\n"
)
p03["copyContent"] = insert_once(p03["copyContent"], p03_line, p03_add)

p07 = by_id["P07"]
readability_block = f"""
CODE READABILITY / EDITABILITY FLOOR
- Green behavior is not enough when the owned diff needlessly makes source harder to understand or change. During the deliberate second-pass diff review, check touched code for new or worsened giant functions/classes/files, mixed responsibilities, duplicated rules, deep avoidable nesting, misleading names/comments, hidden coupling, needless indirection, and hand-edited generated output.
- Prefer cohesive, obvious ownership and existing seams. Do not split code merely to chase line counts, create wrapper chains, or turn a coherent module into a maze of tiny abstractions.
- Repair a concrete in-scope readability regression when the safe fix is bounded. If broader structural cleanup would materially expand the feature sprint, preserve the current behavior slice, record the debt with evidence, and route that separate cleanup to {new_id} instead of stuffing unrelated refactoring into the feature change.
"""
p07_anchor = "\nValidation:\nRun the strongest practical checks available:"
p07["copyContent"] = insert_once(p07["copyContent"], p07_anchor, readability_block + "\n", before=True)
if "readability/editability regression" not in p07["proofGate"]:
    p07["proofGate"] += (
        " Touched source must also have no unjustified readability/editability regression: concrete structural debt "
        f"introduced or worsened by the sprint is repaired in scope or recorded and routed to {new_id} without broadening the feature slice."
    )
if "structural editability" not in p07["expectedOutput"]:
    p07["expectedOutput"] += (
        " The final diff also preserves or improves structural editability in touched source, or records a separately owned "
        f"{new_id} cleanup when the broader refactor is not required for correctness."
    )

p14 = by_id["P14"]
review_block = f"""
READABILITY / STRUCTURAL EDITABILITY CHECK — STANDARDS, NOT TASTE
- Treat a readability finding as actionable when the diff materially raises future change risk or obscures ownership, not merely because a reviewer prefers another style. Look for new or worsened giant functions/classes/files, mixed responsibilities, duplicated deterministic rules, deep avoidable nesting, surprising coupling/imports, magic conditions, misleading names or stale comments, needless wrapper/abstraction chains, and manual edits to generated output.
- For each finding, cite the changed symbol/path and explain the concrete maintenance or agent-navigation cost. Prefer the smallest behavior-preserving repair and existing repository boundaries.
- Do not demand arbitrary line-count splits or abstraction for abstraction's sake. A large coherent unit may be clearer than many pass-through helpers.
- If the PR exposes substantial pre-existing structural debt that it did not worsen, do not hijack the feature review. Record it separately and route the bounded cleanup to {new_id}; block or repair the current PR only when its diff creates/worsens the defect or the readability repair is required for safe correctness.
"""
p14_anchor = "\nREGRESSION + CALL-STACK GATE\n"
p14["copyContent"] = insert_once(p14["copyContent"], p14_anchor, review_block + "\n", before=True)
if "structural editability" not in p14["proofGate"]:
    p14["proofGate"] += (
        " Standards review also checks structural editability with evidence, rejects concrete readability regressions without "
        f"turning style preference into a blocker, and routes broader pre-existing cleanup to {new_id}."
    )
if "readability regressions" not in p14["expectedOutput"]:
    p14["expectedOutput"] += (
        " Concrete readability regressions introduced or worsened by the PR are repaired or dispositioned with evidence."
    )

DOCS.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

build_text = BUILD.read_text(encoding="utf-8")
syn_anchor = '    "cleanup": "P06", "pr cleanup": "P06",\n'
syn_block = (
    f'    "code readability": "{new_id}", "codebase readability": "{new_id}", '
    f'"code cleanup": "{new_id}", "code refactor": "{new_id}",\n'
    f'    "structural refactor": "{new_id}", "maintainability refactor": "{new_id}", '
    f'"god file": "{new_id}", "giant function": "{new_id}",\n'
)
build_text = insert_once(build_text, syn_anchor, syn_block)
BUILD.write_text(build_text, encoding="utf-8")

test_text = TESTS.read_text(encoding="utf-8")
method_marker = "    def test_code_readability_prompt_owns_general_source_refactoring_without_absorbing_specialists(self) -> None:"
if method_marker not in test_text:
    methods = f'''\n\n    def test_code_readability_prompt_owns_general_source_refactoring_without_absorbing_specialists(self) -> None:\n        matches = [p for p in self.full.values() if p.get("name") == {NAME!r}]\n        self.assertEqual(len(matches), 1)\n        prompt = matches[0]\n        content = prompt["copyContent"]\n        raw_content = self.raw[prompt["id"]]["copyContent"]\n        self.assertEqual(prompt["class"], "ENGINEERING / CODE READABILITY")\n        self.assertEqual(prompt["profile"], "spec-architecture")\n        self.assertEqual(prompt["color"], "Cyan")\n        for phrase in (\n            "BUILD A STRUCTURAL-DEBT LEDGER",\n            "PROTECT BEHAVIOR BEFORE MOVING IT",\n            "REFACTOR FOR COHESION, NOT SMALLNESS ALONE",\n            "DO NOT REPLACE A MONOLITH WITH A MAZE",\n            "Pass 2: read the resulting diff from the perspective of a fresh maintainer",\n            "Where would a fresh maintainer change <responsibility>?",\n            "Never hand-edit generated output for tidiness",\n        ):\n            self.assertIn(phrase, content)\n        self.assertLess(len(raw_content), 7000)\n        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])\n        for existing_id in ("P06", "P63", "P68", "P76", "P78"):\n            self.assertNotEqual(prompt["id"], existing_id)\n        for synonym in (\n            "code readability",\n            "codebase readability",\n            "code cleanup",\n            "code refactor",\n            "structural refactor",\n            "maintainability refactor",\n            "god file",\n            "giant function",\n        ):\n            self.assertEqual(build_prompt_kit.SYNONYMS[synonym], prompt["id"])\n\n    def test_general_execution_review_and_discovery_prompts_do_not_hide_readability_debt(self) -> None:\n        owner = [p for p in self.full.values() if p.get("name") == {NAME!r}][0]\n        owner_id = owner["id"]\n        p03 = self.full["P03"]["copyContent"]\n        p07 = self.full["P07"]\n        p14 = self.full["P14"]\n        self.assertIn("do not misclassify evidenced structural editability debt as speculative refactoring", p03)\n        self.assertIn(f"route a bounded cleanup to {{owner_id}}", p03)\n        self.assertIn("CODE READABILITY / EDITABILITY FLOOR", p07["copyContent"])\n        self.assertIn("Green behavior is not enough", p07["copyContent"])\n        self.assertIn(f"route that separate cleanup to {{owner_id}}", p07["copyContent"])\n        self.assertIn("readability/editability regression", p07["proofGate"])\n        self.assertIn("READABILITY / STRUCTURAL EDITABILITY CHECK — STANDARDS, NOT TASTE", p14["copyContent"])\n        self.assertIn("do not hijack the feature review", p14["copyContent"])\n        self.assertIn(f"route the bounded cleanup to {{owner_id}}", p14["copyContent"])\n        self.assertIn("structural editability", p14["proofGate"])\n        self.assertIn("Avoid permission theater, duplicate ownership, giant prompts, and trivial-only progress", self.full["P04"]["copyContent"])\n        self.assertEqual(self.full["P76"]["class"], "HARNESS / SPEC ARCHITECTURE")\n        self.assertEqual(self.full["P78"]["class"], "HARNESS / KNOWLEDGE ARCHITECTURE")\n        self.assertEqual(self.full["P63"]["class"], "AGENT HARNESS / SKILL FACTORING")\n        self.assertEqual(self.full["P68"]["class"], "AI ENGINEERING / CONTEXT")\n'''
    marker = "\nif __name__ == \"__main__\":"
    if marker in test_text:
        test_text = test_text.replace(marker, methods + marker, 1)
    else:
        test_text = test_text.rstrip() + methods + "\n"
    TESTS.write_text(test_text, encoding="utf-8")

# Reverse sweep: explicitly disposition adjacent owners after implementation.
from scripts import build_prompt_kit_registry  # noqa: E402
full = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
actual = [p for p in full.values() if p.get("name") == NAME]
if len(actual) != 1 or actual[0]["id"] != new_id:
    raise SystemExit("New readability owner is not unique after implementation")
ledger = [
    {"insight": "general source-code readability and structural editability", "owner": new_id, "action": "ADD", "proof": "dedicated trigger/closure; distinct from specialist factoring"},
    {"insight": "repo intake must not dismiss evidenced readability debt as speculative", "owner": "P03", "action": "STRENGTHEN", "proof": f"routes bounded debt to {new_id}"},
    {"insight": "generic implementation can be green yet worsen editability", "owner": "P07", "action": "STRENGTHEN", "proof": "second-pass structural editability floor"},
    {"insight": "PR review must distinguish maintainability risk from style taste", "owner": "P14", "action": "STRENGTHEN", "proof": "evidence-backed structural editability review axis"},
    {"insight": "harness/spec default-context bloat", "owner": "P76", "action": "ALREADY COVERED", "proof": "progressive-disclosure spec/harness owner"},
    {"insight": "documentation/prose bloat", "owner": "P78", "action": "ALREADY COVERED", "proof": "documentation diet owner"},
    {"insight": "oversized or overlapping skills", "owner": "P63", "action": "ALREADY COVERED", "proof": "skill-factoring owner"},
    {"insight": "model context/system prompt bloat", "owner": "P68", "action": "ALREADY COVERED", "proof": "context-engineering owner"},
    {"insight": "parallel sprint factoring", "owner": "P04", "action": "ALREADY COVERED", "proof": "already forbids giant prompts and separates app/harness factoring"},
    {"insight": "branch/PR state cleanup", "owner": "P06", "action": "ALREADY COVERED", "proof": "distinct Git/PR cleanup trigger; not source refactoring"},
]
print(json.dumps({"reverse_sweep_ledger": ledger}, indent=2))
print(json.dumps({"new_prompt_id": new_id, "new_prompt_name": NAME}, indent=2))
