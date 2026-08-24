#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
DRAFT = ROOT / ".prompt-contrib" / "test-floor-evolution-draft.json"
TARGET_NAME = "Risk-Driven Test Floor Evolution Executor"


def run(*args: str, capture: bool = False) -> str:
    proc = subprocess.run(
        list(args),
        cwd=ROOT,
        text=True,
        check=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return proc.stdout if capture else ""


def helper_add() -> dict:
    inspect = run(sys.executable, "scripts/prompt_registry_ops.py", "inspect", capture=True)
    print(inspect, end="")
    receipt_text = run(
        sys.executable,
        "scripts/prompt_registry_ops.py",
        "add",
        "--input",
        str(DRAFT.relative_to(ROOT)),
        "--registry",
        "spec-architecture-prompts",
        capture=True,
    )
    print(receipt_text, end="")
    receipt = json.loads(receipt_text)
    outputs = ROOT / "Outputs"
    outputs.mkdir(exist_ok=True)
    (outputs / "test-floor-evolution-prompt-inspect.json").write_text(inspect, encoding="utf-8")
    (outputs / "test-floor-evolution-prompt-add-receipt.json").write_text(
        receipt_text, encoding="utf-8"
    )
    if receipt.get("status") != "added" or not receipt.get("site_parity"):
        raise SystemExit(f"helper did not produce an added/parity receipt: {receipt}")
    return receipt


def strengthen_p112(new_id: str) -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompts = payload["prompts"]
    p112 = next(p for p in prompts if p.get("id") == "P112")
    evolution = next(p for p in prompts if p.get("name") == TARGET_NAME)
    if evolution["id"] != new_id:
        raise SystemExit(f"helper identity mismatch: {evolution['id']} != {new_id}")

    p112["nextStep"] = (
        "Keep the proven unattended test gate as the repository's normal evidence floor. "
        f"When that floor is already trustworthy and the goal is to proactively deepen regression coverage or harden the next evidence-backed risk seam, hand it to {new_id} Risk-Driven Test Floor Evolution Executor. "
        "Route a failing established CI lane to P32; when the operator also wants an exact green revision automatically merged, released, or deployed, hand the proven test floor to P105 rather than adding promotion authority here."
    )

    content = p112["copyContent"]
    old_stop = "further expansion would be a separate test-coverage project rather than this bootstrap."
    new_stop = (
        f"further expansion is a separate test-evolution project: hand the established floor to {new_id} Risk-Driven Test Floor Evolution Executor rather than stretching this bootstrap indefinitely."
    )
    if old_stop not in content:
        raise SystemExit("P112 bootstrap stop sentence drifted")
    content = content.replace(old_stop, new_stop, 1)

    old_owner = (
        "This prompt owns creation/strengthening of the unattended automated-test floor. P105 owns validated promotion after that floor exists; hand off there only when automated push/merge/release/deploy is actually desired."
    )
    new_owner = (
        "This prompt owns creation/strengthening of the unattended automated-test floor. "
        f"Use {new_id} Risk-Driven Test Floor Evolution Executor when a trustworthy floor already exists and the mission is proactive risk-ranked regression growth rather than bootstrap. "
        "P105 owns validated promotion after that floor exists; hand off there only when automated push/merge/release/deploy is actually desired."
    )
    if old_owner not in content:
        raise SystemExit("P112 owner-boundary sentence drifted")
    p112["copyContent"] = content.replace(old_owner, new_owner, 1)

    REGISTRY.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"strengthened P112 -> {new_id}")


def write_tests() -> None:
    existing = ROOT / "tests" / "test_afk_deterministic_testing_prompt.py"
    text = existing.read_text(encoding="utf-8")
    needle = '        self.assertIn("Route a failing established CI lane to P32", self.target["nextStep"])\n'
    addition = needle + '''        evolution = [\n            prompt for prompt in self.full\n            if prompt.get("name") == "Risk-Driven Test Floor Evolution Executor"\n        ]\n        self.assertEqual(len(evolution), 1)\n        self.assertIn(evolution[0]["id"], self.target["nextStep"])\n        self.assertIn(evolution[0]["id"], self.target["copyContent"])\n'''
    if needle not in text:
        raise SystemExit("focused P112 regression insertion point drifted")
    existing.write_text(text.replace(needle, addition, 1), encoding="utf-8")

    (ROOT / "tests" / "test_test_floor_evolution_prompt.py").write_text(
        r'''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TARGET_NAME = "Risk-Driven Test Floor Evolution Executor"


class TestFloorEvolutionPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.by_id = {prompt["id"]: prompt for prompt in cls.full}
        matches = [prompt for prompt in cls.full if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected one {TARGET_NAME!r}, found {len(matches)}")
        cls.target = matches[0]
        raw_prompts = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        raw_matches = [prompt for prompt in raw_prompts if prompt.get("name") == TARGET_NAME]
        if len(raw_matches) != 1:
            raise AssertionError(f"expected one raw {TARGET_NAME!r}, found {len(raw_matches)}")
        cls.raw = raw_matches[0]
        cls.p112 = cls.by_id["P112"]

    def test_helper_owned_identity_and_profile(self) -> None:
        self.assertRegex(self.target["id"], r"^P\d+$")
        self.assertEqual(self.target["seq"], self.target["id"][1:])
        self.assertEqual(self.target["copySheet"], f"{self.target['id']}_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "HARNESS / TEST EVOLUTION")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_trigger_is_existing_green_floor_not_bootstrap(self) -> None:
        trigger = self.target["useWhen"]
        self.assertIn("already has a canonical automated-test floor", trigger)
        self.assertIn("proactively and pragmatically deepen that floor", trigger)
        content = self.target["copyContent"]
        self.assertIn("if the repository does not yet have a trustworthy floor, use P112 first", content)
        self.assertIn("post-bootstrap test evolution", content)

    def test_risk_ranked_pragmatic_selection_beats_coverage_theater(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "BUILD A TEST-RISK LEDGER, NOT A COVERAGE WISHLIST",
            "percentage is evidence, not the objective",
            "Keep at most three active candidates",
            "cheapest maintainable test level",
            "Do not add trivial assertions merely to raise a number",
        ):
            self.assertIn(phrase, content)

    def test_iterative_prototype_and_sensitivity_proof(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PROTOTYPE THE PROTECTION AND PROVE SENSITIVITY",
            "REFRESH -> SELECT RISK -> PROTOTYPE TEST/ORACLE -> RUN -> FALSIFY",
            "replay of a known historical regression",
            "smallest isolated mutation/controlled defect",
            "Never leave the deliberate defect in the durable branch",
            "SECOND-PASS FALSIFICATION",
            "BOUNDED FIXED POINT",
        ):
            self.assertIn(phrase, content)

    def test_stale_test_cannot_override_product_truth(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("PRESERVE PRODUCT TRUTH; DO NOT MAKE TESTS THE SPEC BY ACCIDENT", content)
        self.assertIn("If the test is stale, repair the test instead of regressing correct product behavior", content)
        self.assertIn("Never weaken an assertion merely to make CI green", content)

    def test_skip_determinism_cost_and_provider_contracts(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "Unknown or newly introduced skips must not silently become green",
            "KEEP THE FLOOR DETERMINISTIC AND FAIL-CLOSED",
            "BE PRAGMATIC ABOUT SUITE COST",
            "REAL PROVIDER PROOF",
            "exact candidate revision",
            "PROVIDER-RUNTIME BLOCKED",
        ):
            self.assertIn(phrase, content)

    def test_neighbor_owners_remain_distinct_and_routed(self) -> None:
        self.assertEqual(self.by_id["P112"]["name"], "AFK Deterministic Automated Test Harness Builder")
        self.assertEqual(self.by_id["P32"]["name"], "GNHF Validation and CI Repair")
        self.assertEqual(self.by_id["P33"]["name"], "GNHF Harness Hardening")
        self.assertEqual(self.by_id["P67"]["name"], "Repository Eval Framework Builder")
        self.assertEqual(self.by_id["P105"]["name"], "Validated CI/CD Promotion Pipeline Builder")
        for owner_id in ("P112", "P32", "P33", "P67", "P105"):
            self.assertNotEqual(self.target["id"], owner_id)
        self.assertIn(self.target["id"], self.p112["nextStep"])
        self.assertIn(self.target["id"], self.p112["copyContent"])
        self.assertIn("P33: harden offline harness contracts", self.target["copyContent"])
        self.assertIn("P67: build AI/agent task-quality eval systems", self.target["copyContent"])

    def test_generated_site_contains_exact_prompt_identity(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET_NAME, html)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


def validate_pass_one() -> None:
    commands = (
        (sys.executable, "-m", "unittest", "tests.test_afk_deterministic_testing_prompt", "tests.test_test_floor_evolution_prompt", "-v"),
        (sys.executable, "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v"),
        (sys.executable, "-m", "unittest", "tests.test_actionable_prompt_registry", "-v"),
        (sys.executable, "scripts/prompt_registry_ops.py", "validate"),
        (sys.executable, "scripts/validate_prompt_kit_discovery.py", "--summary"),
        (sys.executable, "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--summary"),
        (sys.executable, "scripts/evaluate_prompt_language.py", "--summary"),
        (sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check"),
        ("git", "diff", "--check"),
    )
    for command in commands:
        run(*command)


def pass_two() -> None:
    prompts = json.loads(REGISTRY.read_text(encoding="utf-8"))["prompts"]
    by_id = {p["id"]: p for p in prompts}
    target = next(p for p in prompts if p.get("name") == TARGET_NAME)
    content = target["copyContent"]
    checks = {
        "proactive/pragmatic entry": "proactively and pragmatically deepen that floor" in target["useWhen"],
        "risk rather than vanity coverage": "percentage is evidence, not the objective" in content,
        "prototype sensitivity": "PROTOTYPE THE PROTECTION AND PROVE SENSITIVITY" in content,
        "historical regression replay": "replay of a known historical regression" in content,
        "stale-test truth boundary": "If the test is stale, repair the test instead of regressing correct product behavior" in content,
        "unexpected skip guard": "Unknown or newly introduced skips must not silently become green" in content,
        "suite cost pragmatism": "BE PRAGMATIC ABOUT SUITE COST" in content,
        "real provider proof": "REAL PROVIDER PROOF" in content,
        "bounded fixed point": "BOUNDED FIXED POINT" in content,
        "P112 bootstrap boundary": "P112: create/strengthen the initial trustworthy automated-test floor" in content,
        "P32 red-floor boundary": "P32: repair a reproducibly failing established validation/CI lane" in content,
        "P33 harness boundary": "P33: harden offline harness contracts" in content,
        "P67 eval boundary": "P67: build AI/agent task-quality eval systems" in content,
        "P105 promotion boundary": "P105: promotion automation after testing is proven" in content,
        "P112 routes forward": target["id"] in by_id["P112"]["nextStep"] and target["id"] in by_id["P112"]["copyContent"],
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise SystemExit("pass-2 gaps: " + ", ".join(missing))
    print("whole-context pass 2: fixed point reached")
    for name in checks:
        print("PASS", name)
    run(sys.executable, "-m", "unittest", "tests.test_afk_deterministic_testing_prompt", "tests.test_test_floor_evolution_prompt", "-v")
    run(sys.executable, "scripts/prompt_registry_ops.py", "validate")
    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")


def main() -> None:
    receipt = helper_add()
    strengthen_p112(str(receipt["id"]))
    write_tests()
    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    validate_pass_one()
    pass_two()
    print(json.dumps({"status": "fixed-point", "helper_receipt": receipt}, indent=2))


if __name__ == "__main__":
    main()
