import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_layout_validator():
    spec = importlib.util.spec_from_file_location("layout_validator", ROOT / "scripts/validate_prompt_kit_layout_harness.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PromptKitMainlineDeliveryTests(unittest.TestCase):
    def test_p13_declares_sprint_and_isolates_subpart_agents(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        for phrase in (
            "SPRINT DECLARATION BEFORE MUTATION",
            "repository and branch/worktree",
            "owned scope and forbidden scope",
            "validation order",
            "proof ceiling",
            "mutation authority",
            "dedicated branch and isolated worktree",
            "waiting lanes and their explicit start gates",
            "shared-surface owner",
            "final convergence owner",
        ):
            self.assertIn(phrase, copy)

    def test_p13_requires_continuous_mainline_convergence(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        self.assertIn("recurring pain", p13["sprintRole"])
        self.assertIn("current default branch", p13["expectedOutput"])
        self.assertIn("bounded fixed point", p13["nextStep"])
        self.assertIn("branch or PR alone is insufficient", p13["proofGate"])
        for phrase in (
            "P13 CONTINUOUS MAINLINE CONVERGENCE",
            "REFRESH -> SELECT NEXT GATE -> EXECUTE -> PREVENT -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE",
            "Do not create a feature branch merely because P13 fired",
            "branch, worktree, commit, push, open PR, review-ready state, or green CI",
            "merge the exact validated owned head into the current default branch",
            "verify that the intended change is present there",
            "deliberate second pass",
            "Do not stop merely because one bounded slice merged",
            "bounded fixed point",
        ):
            self.assertIn(phrase, copy)
        self.assertLess(len(copy), 18000)

    def test_p13_does_not_absorb_hallucination_diagnostic_role(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"].lower()
        self.assertIn("recover the repeated failure from evidence", copy)
        self.assertNotIn("factuality hallucination", copy)
        self.assertNotIn("faithfulness hallucination", copy)
        self.assertNotIn("dumb zone", copy)

    def test_p13_routes_specialized_failures_without_absorbing_their_doctrine(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        self.assertIn("specialist repair routed", p13["expectedOutput"])
        self.assertIn("specialist failure mode is routed to its canonical owner", p13["proofGate"])
        for phrase in (
            "SPECIALIZED OWNER ROUTING — REFER, DO NOT DUPLICATE",
            "route diagnosis to P100",
            "route the prevention layer to P101",
            "route to P68",
            "route to P76",
            "route verification to P83",
            "route certification to P48",
            "Routing is not a stopping condition",
            "Do not copy the specialist prompt's full checklist into P13",
        ):
            self.assertIn(phrase, copy)

        ai = load_json("registry/prompts/ai-engineering-level-up-prompts.v1.json")
        ai_ids = {item["id"] for item in ai["prompts"]}
        self.assertTrue({"P68", "P100", "P101"}.issubset(ai_ids))
        spec = load_json("registry/prompts/spec-architecture-prompts.v1.json")
        spec_ids = {item["id"] for item in spec["prompts"]}
        self.assertIn("P76", spec_ids)
        base = load_json("docs/prompts.json")
        base_ids = {item["id"] for item in base}
        self.assertIn("P48", base_ids)
        ledger = load_json("registry/prompts/repository-work-ledger-prompts.v1.json")
        ledger_ids = {item["id"] for item in ledger["prompts"]}
        self.assertIn("P83", ledger_ids)
        self.assertLess(len(copy), 18000)

    def test_p65_can_route_repeated_friction_without_browser_finder(self):
        payload = load_json("registry/prompts/tutorial-discovery-prompts.v1.json")
        p65 = next(item for item in payload["prompts"] if item["id"] == "P65")
        self.assertIn("P13 Repeated Friction", p65["copyContent"])
        self.assertIn("repeated friction or urgency", p65["copyContent"])

    def test_generic_path_search_is_not_a_p13_synonym(self):
        source = (ROOT / "build_prompt_kit.py").read_text(encoding="utf-8")
        self.assertNotIn('"critical path": "P13"', source)

    def test_layout_harness_is_registered_at_root(self):
        manifest = load_json("harness/manifest.v1.json")
        capabilities = load_json("harness/capabilities.v1.json")
        triggers = load_json("harness/triggers.v1.json")
        self.assertIn("prompt_kit_responsive_layout", manifest["domain_contracts"])
        self.assertTrue(any(item["id"] == "prompt-kit-responsive-layout" for item in capabilities["capabilities"]))
        self.assertTrue(any(item["id"] == "prompt-kit-responsive-overlap" for item in triggers["triggers"]))

    def test_layout_validator_fails_closed_on_malformed_shapes(self):
        validator = load_layout_validator()
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            manifest = td / "manifest.json"
            contract = td / "contract.json"
            manifest.write_text(json.dumps({"components": []}), encoding="utf-8")
            contract.write_text(json.dumps({"viewports": ["bad"], "requirements": [42], "strict_acceptance": []}), encoding="utf-8")
            errors, _, _ = validator.validate(False, manifest, contract)
            self.assertTrue(errors)
            self.assertTrue(any("must be" in error or "invalid" in error for error in errors))

    def test_layout_strict_gate_requires_all_viewports_and_real_geometry(self):
        validator = load_layout_validator()
        manifest = ROOT / "harness/prompt-kit-layout/manifest.v1.json"
        contract_path = ROOT / "harness/prompt-kit-layout/contracts/responsive-header-overlap.v1.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            pending = td / "pending.json"
            pending.write_text(json.dumps(contract), encoding="utf-8")
            errors, _, _ = validator.validate(True, manifest, pending, td / "missing-geometry.json")
            self.assertTrue(any("status must be implemented" in error for error in errors))
            self.assertTrue(any("geometry receipt is required" in error for error in errors))

            contract["implementation_status"] = "implemented"
            contract["strict_acceptance"]["all_viewports_required"] = False
            bad_acceptance = td / "bad-acceptance.json"
            bad_acceptance.write_text(json.dumps(contract), encoding="utf-8")
            errors, _, _ = validator.validate(False, manifest, bad_acceptance)
            self.assertIn("strict acceptance must require all declared viewports", errors)

            contract["strict_acceptance"]["all_viewports_required"] = True
            implemented = td / "implemented.json"
            implemented.write_text(json.dumps(contract), encoding="utf-8")
            receipt = {
                "contract_id": contract["contract_id"],
                "browser_engine": "synthetic-test-fixture",
                "viewports": [
                    {
                        "id": item["id"], "width": item["width"], "height": item["height"],
                        "brand_search_intersections": 0,
                        "filter_search_intersections": 0,
                        "header_escape": False,
                        "horizontal_overflow_pixels": 0,
                        "responsive_reflow": True,
                        "touch_targets_usable": True,
                    }
                    for item in contract["viewports"]
                ],
            }
            geometry = td / "geometry.json"
            geometry.write_text(json.dumps(receipt), encoding="utf-8")
            errors, _, _ = validator.validate(True, manifest, implemented, geometry)
            self.assertEqual([], errors)

    def test_p11_and_p15_compose_with_canonical_cicd_without_role_collapse(self):
        prompts = {item["id"]: item for item in load_json("docs/prompts.json")}
        p11 = prompts["P11"]
        p15 = prompts["P15"]
        for phrase in (
            "CI/CD COMPOSITION CONTRACT",
            "same validation logic locally and in CI",
            "offline/synthetic boundary",
            "Application or product end-to-end tests",
            "required validator reported SKIP is not a successful CI gate",
        ):
            self.assertIn(phrase, p11["copyContent"])
        for phrase in (
            "CANONICAL PROMOTION PIPELINE CONTRACT",
            "canonical GitHub Actions/CI/CD promotion workflow",
            "Pin the candidate head SHA",
            "skipped required harness or E2E gates",
            "Automated push/merge/release is permitted only",
            "verify containment of the proven integration SHA",
        ):
            self.assertIn(phrase, p15["copyContent"])
        self.assertEqual(p11["class"], "VALIDATE / GATE")
        self.assertEqual(p15["class"], "MERGE / RELEASE")

    def test_repo_quick_access_explains_mainline_deployment_gate(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Open the Prompt Kit", readme)
        self.assertIn("feature-branch Pages checks are previews only", readme)
        workflow = (ROOT / ".github/workflows/prompt-kit-pages.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [main]", workflow)
        self.assertIn("Deploy Prompt Kit to GitHub Pages", workflow)


if __name__ == "__main__":
    unittest.main()
