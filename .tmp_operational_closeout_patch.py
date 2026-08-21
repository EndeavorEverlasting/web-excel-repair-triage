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

POLICY_PATH = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
DOCS_PATH = ROOT / "docs" / "prompts.json"
LEDGER_PATH = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
BUILDER_PATH = ROOT / "scripts" / "build_prompt_kit_registry.py"
OPERATOR_PATH = ROOT / "harness" / "specs" / "operator-delivery.md"
TEST_PATH = ROOT / "tests" / "test_operational_closeout_contract.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "prompt-freshness-evidence.yml"
SITE_PATH = ROOT / "web" / "prompt-kit" / "index.html"
MUTATED_PATHS = (
    POLICY_PATH,
    DOCS_PATH,
    LEDGER_PATH,
    BUILDER_PATH,
    OPERATOR_PATH,
    TEST_PATH,
    WORKFLOW_PATH,
    SITE_PATH,
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_once(text: str, addition: str) -> str:
    if MARKER in text:
        return text
    return text.rstrip() + "\n\n" + addition


def strengthen_record(record: dict, *, compact_copy: bool = False) -> None:
    content = str(record["copyContent"])
    if MARKER not in content:
        if compact_copy:
            # P83 has a permanent <8k raw-source budget. Preserve its existing loop body and
            # add only the direct-consumer marker; the shared effective policy supplies the full block.
            anchor = "FINAL RESPONSE" if "FINAL RESPONSE" in content else "FINAL REPORT"
            if anchor in content:
                content = content.replace(anchor, f"{MARKER}\n{anchor}", 1)
            else:
                content = content.rstrip() + "\n" + MARKER
            if len(content) >= 8000:
                raise SystemExit(f"P83 closeout marker would breach raw copyContent budget: {len(content)}")
            record["copyContent"] = content
        else:
            record["copyContent"] = append_once(content, BLOCK)

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


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise SystemExit(f"required {label} anchor missing: {needle}")


# Preflight every owner/anchor before the first canonical write.
policy = read_json(POLICY_PATH)
docs = read_json(DOCS_PATH)
ledger = read_json(LEDGER_PATH)
builder = BUILDER_PATH.read_text(encoding="utf-8")
operator = OPERATOR_PATH.read_text(encoding="utf-8")
workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
for prompt_id in ("P03", "P07", "P48"):
    if not any(p.get("id") == prompt_id for p in docs):
        raise SystemExit(f"missing base prompt {prompt_id}")
if not any(p.get("id") == "P83" for p in ledger.get("prompts", [])):
    raise SystemExit("missing ledger prompt P83")
for needle in (
    '    "freshness_marker",\n    "integration_target",',
    '        "freshness_marker",\n        "integration_target",',
    '    freshness_marker = str(payload["freshness_marker"])',
    '    has_current_freshness = not freshness_marker or freshness_marker in copy_content',
    '    elif not has_current_integration or not has_current_freshness:',
):
    require(builder, needle, "builder")
require(operator, "\n## Evidence and artifact safety\n", "operator-delivery")
require(workflow, "      - 'tests/test_remote_freshness_p13_iteration.py'", "freshness workflow test path")
require(workflow, "      - 'registry/prompts/actionable-next-step-policy.v1.json'", "freshness workflow policy path")
require(workflow, "            tests/test_remote_freshness_p13_iteration.py", "freshness workflow compile")
require(workflow, "          python -m unittest tests.test_green_branch_integration_policy -v", "freshness workflow unittest")

# Snapshot every canonical surface so any exception restores the pre-migration tree.
snapshots: dict[Path, str | None] = {}
for path in MUTATED_PATHS:
    snapshots[path] = path.read_text(encoding="utf-8") if path.exists() else None

try:
    policy["closeout_marker"] = MARKER
    suffix_add = (
        " Before stopping, explicitly report remaining gaps, risks, blockers, proof ceiling, integration state, "
        "and the first executable continuation; do not use a generic next step when an exact action can be named."
    )
    if suffix_add.strip() not in str(policy["next_step_suffix"]):
        policy["next_step_suffix"] = str(policy["next_step_suffix"]).rstrip() + suffix_add
    policy["copy_content_appendix"] = append_once(str(policy["copy_content_appendix"]), BLOCK)
    write_json(POLICY_PATH, policy)

    for prompt_id in ("P03", "P07", "P48"):
        strengthen_record(next(p for p in docs if p.get("id") == prompt_id))
    write_json(DOCS_PATH, docs)

    p83 = next(p for p in ledger["prompts"] if p.get("id") == "P83")
    strengthen_record(p83, compact_copy=True)
    write_json(LEDGER_PATH, ledger)

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
        require(builder, needle, "patched builder")
    BUILDER_PATH.write_text(builder, encoding="utf-8")

    operator_section = """## Actionable runtime / live-cert closeout

- Every runtime or live-cert stop must state: completed/proven behavior; remaining gaps; risks; blockers; proof ceiling; integration state; and the first executable next action or ordered dependency-aware next steps.
- Each gap/risk/blocker must identify the affected target or artifact, current evidence, consequence, and the exact action or operator gate that advances it. A passing command, process start, or green CI result does not erase unobserved runtime risk.
- The next action must identify owner, dependency, exact command or operator action, expected evidence/artifact, and completion gate. Continue agent-capable work immediately; reserve handoff for a protected runtime, physical action, inaccessible credential/system, or another genuine operator-only gate.
- `none; no safe actionable work remains` is valid only when the requested proof ceiling is actually satisfied, integration/cleanup is complete or explicitly out of scope, and no known safe unproven action remains.
""".rstrip()
    if "## Actionable runtime / live-cert closeout" not in operator:
        operator = operator.replace("\n## Evidence and artifact safety\n", "\n" + operator_section + "\n\n## Evidence and artifact safety\n", 1)
    OPERATOR_PATH.write_text(operator, encoding="utf-8")

    TEST_PATH.write_text('''from __future__ import annotations\n\nimport json\nimport unittest\nfrom pathlib import Path\n\nfrom scripts import build_prompt_kit_registry\n\nROOT = Path(__file__).resolve().parents[1]\nMARKER = "OPERATIONAL CLOSEOUT / GAP-RISK CONTRACT"\n\n\nclass OperationalCloseoutContractTests(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls) -> None:\n        cls.policy = build_prompt_kit_registry.load_actionability_policy()\n        cls.effective = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_registry()}\n        cls.base = {p["id"]: p for p in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))}\n        ledger = json.loads((ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json").read_text(encoding="utf-8"))\n        cls.ledger = {p["id"]: p for p in ledger["prompts"]}\n\n    def test_shared_policy_requires_gap_risk_blocker_and_executable_continuation(self) -> None:\n        self.assertEqual(self.policy["closeout_marker"], MARKER)\n        appendix = self.policy["copy_content_appendix"]\n        for phrase in (\n            "REMAINING GAPS", "RISKS", "BLOCKERS", "PROOF CEILING",\n            "INTEGRATION STATE", "NEXT ACTION / NEXT STEPS",\n            "owner, dependency, exact command or operator action",\n            "none; no safe actionable work remains",\n        ):\n            self.assertIn(phrase, appendix)\n\n    def test_operational_effective_prompts_inherit_closeout_contract(self) -> None:\n        tokens = ("BUILD", "REPAIR", "ARTIFACT", "RUNTIME", "CERT", "DEPLOY", "VERIFY", "ADVANCE")\n        selected = [p for p in self.effective.values() if any(t in str(p["type"]).upper() for t in tokens)]\n        self.assertGreater(len(selected), 0)\n        for prompt in selected:\n            with self.subTest(prompt_id=prompt["id"], prompt_type=prompt["type"]):\n                content = prompt["copyContent"]\n                self.assertIn(MARKER, content)\n                self.assertIn("REMAINING GAPS", content)\n                self.assertIn("PROOF CEILING", content)\n                self.assertIn("first executable continuation", content)\n\n    def test_p03_p07_p48_and_p83_are_strong_even_without_policy_injection(self) -> None:\n        for prompt in (self.base["P03"], self.base["P07"], self.base["P48"], self.ledger["P83"]):\n            with self.subTest(prompt_id=prompt["id"]):\n                self.assertIn(MARKER, prompt["copyContent"])\n                self.assertIn("remaining gaps, risks, blockers, proof ceiling, integration state", prompt["expectedOutput"].lower())\n                self.assertIn("Report the current gap/risk/blocker", prompt["nextStep"])\n                self.assertIn("Closeout is incomplete", prompt["proofGate"])\n        self.assertLess(len(self.ledger["P83"]["copyContent"]), 8000)\n\n    def test_builder_upgrades_legacy_appendix_missing_closeout(self) -> None:\n        prompt = dict(self.base["P07"])
        marker = self.policy["marker"]
        prompt["copyContent"] = "BASE\\n\\n" + marker + "\\n- Do not leave NEXT COMMAND blank.\\n\\n" + self.policy["integration_marker"] + "\\n- merge.\\n\\n" + self.policy["freshness_marker"] + "\\n- fetch."
        upgraded = build_prompt_kit_registry.apply_actionability_policy(prompt, self.policy)
        self.assertIn(MARKER, upgraded["copyContent"])
        self.assertEqual(upgraded["copyContent"].count(marker), 1)
        self.assertEqual(upgraded["copyContent"].count(MARKER), 1)

    def test_live_cert_domain_law_requires_actionable_closeout(self) -> None:
        text = (ROOT / "harness" / "specs" / "operator-delivery.md").read_text(encoding="utf-8")
        self.assertIn("## Actionable runtime / live-cert closeout", text)
        self.assertIn("remaining gaps; risks; blockers; proof ceiling; integration state", text)
        self.assertIn("owner, dependency, exact command or operator action", text)
        self.assertIn("genuine operator-only gate", text)

    def test_generated_site_is_exact_and_contains_closeout_contract(self) -> None:
        actual = (ROOT / "web" / "prompt-kit" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(actual, build_prompt_kit_registry.render())
        self.assertIn(MARKER, actual)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

    test_path_line = "      - 'tests/test_remote_freshness_p13_iteration.py'"
    workflow = workflow.replace(test_path_line, test_path_line + "\n      - 'tests/test_operational_closeout_contract.py'")
    policy_path_line = "      - 'registry/prompts/actionable-next-step-policy.v1.json'"
    if "      - 'registry/prompts/repository-work-ledger-prompts.v1.json'" not in workflow:
        workflow = workflow.replace(policy_path_line, policy_path_line + "\n      - 'registry/prompts/repository-work-ledger-prompts.v1.json'")
    compile_line = "            tests/test_remote_freshness_p13_iteration.py"
    workflow = workflow.replace(compile_line, compile_line + " \\\n            tests/test_operational_closeout_contract.py")
    run_anchor = "          python -m unittest tests.test_green_branch_integration_policy -v"
    workflow = workflow.replace(run_anchor, run_anchor + "\n          python -m unittest tests.test_operational_closeout_contract -v")
    if workflow.count("tests/test_operational_closeout_contract.py") < 3:
        raise SystemExit("permanent CI patch did not wire closeout test into both path filters and compile")
    require(workflow, "python -m unittest tests.test_operational_closeout_contract -v", "freshness workflow closeout unittest")
    if workflow.count("registry/prompts/repository-work-ledger-prompts.v1.json") < 2:
        raise SystemExit("permanent CI patch did not wire the P83 registry into both trigger lists")
    WORKFLOW_PATH.write_text(workflow, encoding="utf-8")

    subprocess.run(["python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html"], cwd=ROOT, check=True)
except BaseException:
    for path, original in snapshots.items():
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(original, encoding="utf-8")
    raise

# ci-trigger: artifact-bridge-pass-2
