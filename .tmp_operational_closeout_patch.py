#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT"
BLOCK = """OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT
- Before any legitimate stop, report these fields explicitly: COMPLETED / PROVEN; REMAINING GAPS; RISKS; BLOCKERS; PROOF CEILING; INTEGRATION STATE; NEXT ACTION / NEXT STEPS.
- A gap, risk, or blocker must name the affected scope, evidence, consequence, and the action that reduces or closes it. Do not hide known uncertainty behind `looks good`, `green`, `ready`, or an empty section.
- NEXT ACTION must be the first executable continuation, with owner, dependency, exact command or operator action, expected artifact/proof, and completion gate. If several actions remain, order them by dependency and keep executing agent-capable steps instead of merely listing them.
- Use `none; no safe actionable work remains` only when the owned acceptance criteria are proven, authorized integration is complete or explicitly blocked, remaining gaps/risks are either closed or explicitly accepted by scope, and no safe unproven action remains.
""".rstrip()


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path: str, payload) -> None:
    (ROOT / path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_once(text: str, addition: str) -> str:
    if MARKER in text:
        return text
    return text.rstrip() + "\n\n" + addition


def strengthen_record(record: dict, *, label: str) -> None:
    record["copyContent"] = append_once(str(record["copyContent"]), BLOCK)
    expected = str(record["expectedOutput"])
    phrase = "explicit closeout of remaining gaps, risks, blockers, proof ceiling, integration state, and the first executable continuation"
    if phrase not in expected:
        record["expectedOutput"] = expected.rstrip(". ") + ", plus " + phrase + "."
    next_step = str(record["nextStep"])
    phrase2 = "Report the current gap/risk/blocker and then execute the first safe dependency-aware continuation"
    if phrase2 not in next_step:
        record["nextStep"] = next_step.rstrip(". ") + ". " + phrase2 + "; do not stop at status-only reporting while agent-capable work remains."
    gate = str(record["proofGate"])
    phrase3 = "Closeout is incomplete while a known in-scope gap, risk, blocker, proof limitation, or executable continuation is omitted"
    if phrase3 not in gate:
        record["proofGate"] = gate.rstrip(". ") + ". " + phrase3 + "."


# Shared effective-policy owner.
policy_path = "registry/prompts/actionable-next-step-policy.v1.json"
policy = load(policy_path)
policy["closeout_marker"] = MARKER
suffix_add = (
    " Before stopping, explicitly report remaining gaps, risks, blockers, proof ceiling, integration state, "
    "and the first executable continuation; do not use a generic next step when an exact action can be named."
)
if suffix_add.strip() not in str(policy["next_step_suffix"]):
    policy["next_step_suffix"] = str(policy["next_step_suffix"]).rstrip() + suffix_add
policy["copy_content_appendix"] = append_once(str(policy["copy_content_appendix"]), BLOCK)
dump(policy_path, policy)

# Raw direct-consumer protection: build executor, sprint executor, live cert, and cross-agent verifier.
docs_path = "docs/prompts.json"
docs = load(docs_path)
for prompt_id in ("P03", "P07", "P48"):
    strengthen_record(next(p for p in docs if p.get("id") == prompt_id), label=prompt_id)
dump(docs_path, docs)

ledger_path = "registry/prompts/repository-work-ledger-prompts.v1.json"
ledger = load(ledger_path)
strengthen_record(next(p for p in ledger["prompts"] if p.get("id") == "P83"), label="P83")
dump(ledger_path, ledger)

# Builder must fail closed on the new marker and upgrade stale already-injected appendices.
builder_path = ROOT / "scripts" / "build_prompt_kit_registry.py"
builder = builder_path.read_text(encoding="utf-8")
builder = builder.replace(
    '    "freshness_marker",\n    "integration_target",',
    '    "freshness_marker",\n    "closeout_marker",\n    "integration_target",',
)
builder = builder.replace(
    '        "freshness_marker",\n        "integration_target",',
    '        "freshness_marker",\n        "closeout_marker",\n        "integration_target",',
)
builder = builder.replace(
    '    freshness_marker = str(payload["freshness_marker"])\n    if freshness_marker not in appendix:\n        raise SystemExit("Actionability appendix must include its freshness marker")\n    return payload',
    '    freshness_marker = str(payload["freshness_marker"])\n    if freshness_marker not in appendix:\n        raise SystemExit("Actionability appendix must include its freshness marker")\n    closeout_marker = str(payload["closeout_marker"])\n    if closeout_marker not in appendix:\n        raise SystemExit("Actionability appendix must include its operational closeout marker")\n    return payload',
)
builder = builder.replace(
    '    has_current_freshness = not freshness_marker or freshness_marker in copy_content\n    if marker not in copy_content:',
    '    has_current_freshness = not freshness_marker or freshness_marker in copy_content\n    closeout_marker = str(policy.get("closeout_marker", "")).strip()\n    has_current_closeout = not closeout_marker or closeout_marker in copy_content\n    if marker not in copy_content:',
)
builder = builder.replace(
    '    elif not has_current_integration or not has_current_freshness:',
    '    elif not has_current_integration or not has_current_freshness or not has_current_closeout:',
)
for needle in ('"closeout_marker",', 'has_current_closeout', 'operational closeout marker'):
    if needle not in builder:
        raise SystemExit(f"builder patch failed to install {needle}")
builder_path.write_text(builder, encoding="utf-8")

# Runtime/live-cert domain law needs the same closeout semantics even outside Prompt Kit rendering.
operator_path = ROOT / "harness" / "specs" / "operator-delivery.md"
operator = operator_path.read_text(encoding="utf-8")
operator_section = """## Actionable runtime / live-cert closeout

- Every runtime or live-cert stop must state: completed/proven behavior; remaining gaps; risks; blockers; proof ceiling; integration state; and the first executable next action or ordered dependency-aware next steps.
- Each gap/risk/blocker must identify the affected target or artifact, current evidence, consequence, and the exact action or operator gate that advances it. A passing command, process start, or green CI result does not erase unobserved runtime risk.
- The next action must identify owner, dependency, exact command or operator action, expected evidence/artifact, and completion gate. Continue agent-capable work immediately; reserve handoff for a protected runtime, physical action, inaccessible credential/system, or another genuine operator-only gate.
- `none; no safe actionable work remains` is valid only when the requested proof ceiling is actually satisfied, integration/cleanup is complete or explicitly out of scope, and no known safe unproven action remains.
""".rstrip()
if "## Actionable runtime / live-cert closeout" not in operator:
    anchor = "\n## Evidence and artifact safety\n"
    if anchor not in operator:
        raise SystemExit("operator-delivery anchor missing")
    operator = operator.replace(anchor, "\n" + operator_section + "\n" + anchor)
operator_path.write_text(operator, encoding="utf-8")

# Focused permanent proof.
test_path = ROOT / "tests" / "test_operational_closeout_contract.py"
test_path.write_text('''from __future__ import annotations\n\nimport json\nimport unittest\nfrom pathlib import Path\n\nfrom scripts import build_prompt_kit_registry\n\nROOT = Path(__file__).resolve().parents[1]\nMARKER = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT"\n\n\nclass OperationalCloseoutContractTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls) -> None:\n        cls.policy = build_prompt_kit_registry.load_actionability_policy()\n        cls.effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}\n        cls.base = {p["id"]: p for p in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))}\n        ledger = json.loads((ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json").read_text(encoding="utf-8"))\n        cls.ledger = {p["id"]: p for p in ledger["prompts"]}\n\n    def test_shared_policy_requires_gap_risk_blocker_and_executable_continuation(self) -> None:\n        self.assertEqual(self.policy["closeout_marker"], MARKER)\n        appendix = self.policy["copy_content_appendix"]\n        for phrase in (\n            "REMAINING GAPS", "RISKS", "BLOCKERS", "PROOF CEILING",\n            "INTEGRATION STATE", "NEXT ACTION / NEXT STEPS",\n            "owner, dependency, exact command or operator action",\n            "none; no safe actionable work remains",\n        ):\n            self.assertIn(phrase, appendix)\n\n    def test_operational_effective_prompts_inherit_closeout_contract(self) -> None:\n        tokens = ("BUILD", "REPAIR", "ARTIFACT", "RUNTIME", "CERT", "DEPLOY", "VERIFY", "ADVANCE")\n        selected = [p for p in self.effective.values() if any(t in str(p["type"]).upper() for t in tokens)]\n        self.assertGreater(len(selected), 0)\n        for prompt in selected:\n            with self.subTest(prompt_id=prompt["id"], prompt_type=prompt["type"]):\n                content = prompt["copyContent"]\n                self.assertIn(MARKER, content)\n                self.assertIn("REMAINING GAPS", content)\n                self.assertIn("PROOF CEILING", content)\n                self.assertIn("first executable continuation", content)\n\n    def test_p03_p07_p48_and_p83_are_strong_even_without_policy_injection(self) -> None:\n        for prompt in (self.base["P03"], self.base["P07"], self.base["P48"], self.ledger["P83"]):\n            with self.subTest(prompt_id=prompt["id"]):\n                self.assertIn(MARKER, prompt["copyContent"])\n                self.assertIn("remaining gaps, risks, blockers, proof ceiling, integration state", prompt["expectedOutput"].lower())\n                self.assertIn("Report the current gap/risk/blocker", prompt["nextStep"])\n                self.assertIn("Closeout is incomplete", prompt["proofGate"])\n\n    def test_builder_upgrades_legacy_appendix_missing_closeout(self) -> None:\n        prompt = dict(self.base["P07"])\n        marker = self.policy["marker"]\n        prompt["copyContent"] = "BASE\\n\\n" + marker + "\\n- Do not leave NEXT COMMAND blank.\\n\\n" + self.policy["integration_marker"] + "\\n- merge.\\n\\n" + self.policy["freshness_marker"] + "\\n- fetch."\n        upgraded = build_prompt_kit_registry.apply_actionability_policy(prompt, self.policy)\n        self.assertIn(MARKER, upgraded["copyContent"])\n        self.assertEqual(upgraded["copyContent"].count(marker), 1)\n        self.assertEqual(upgraded["copyContent"].count(MARKER), 1)\n\n    def test_live_cert_domain_law_requires_actionable_closeout(self) -> None:\n        text = (ROOT / "harness" / "specs" / "operator-delivery.md").read_text(encoding="utf-8")\n        self.assertIn("## Actionable runtime / live-cert closeout", text)\n        self.assertIn("remaining gaps; risks; blockers; proof ceiling; integration state", text)\n        self.assertIn("owner, dependency, exact command or operator action", text)\n        self.assertIn("genuine operator-only gate", text)\n\n    def test_generated_site_is_exact_and_contains_closeout_contract(self) -> None:\n        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")\n        self.assertEqual(actual, build_prompt_kit_registry.render())\n        self.assertIn(MARKER, actual)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")

# Permanently run the focused contract wherever freshness/actionability changes are checked.
workflow_path = ROOT / ".github" / "workflows" / "prompt-freshness-evidence.yml"
workflow = workflow_path.read_text(encoding="utf-8")
path_line = "      - 'tests/test_remote_freshness_p13_iteration.py'"
new_path_line = path_line + "\n      - 'tests/test_operational_closeout_contract.py'"
workflow = workflow.replace(path_line, new_path_line)
compile_line = "            tests/test_remote_freshness_p13_iteration.py"
workflow = workflow.replace(compile_line, compile_line + " \\\n            tests/test_operational_closeout_contract.py")
run_anchor = "          python -m unittest tests.test_green_branch_integration_policy -v"
workflow = workflow.replace(run_anchor, run_anchor + "\n          python -m unittest tests.test_operational_closeout_contract -v")
if "tests/test_operational_closeout_contract.py" not in workflow:
    raise SystemExit("permanent CI patch failed")
workflow_path.write_text(workflow, encoding="utf-8")

subprocess.run(["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"], cwd=ROOT, check=True)
