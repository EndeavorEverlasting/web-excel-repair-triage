from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_context_architecture


class ContextArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            (ROOT / "harness/contracts/context-architecture.v1.json").read_text(
                encoding="utf-8"
            )
        )

    def test_context_validator_passes(self) -> None:
        self.assertEqual(validate_context_architecture.main(["--summary"]), 0)

    def test_default_load_is_only_governance_and_router(self) -> None:
        self.assertEqual(
            self.contract["default_entrypoints"],
            ["AGENTS.md", "harness/CONTEXT.md"],
        )
        router = (ROOT / "harness/CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Do not eagerly read", router)
        self.assertIn("50,000-foot", router)

    def test_three_zoom_layers_are_machine_bounded(self) -> None:
        layers = self.contract["layers"]
        self.assertEqual(layers["50000"]["soft_max_approx_tokens"], 1000)
        self.assertEqual(layers["30000"]["soft_max_additional_approx_tokens"], 2000)
        self.assertEqual(layers["15000"]["soft_max_additional_approx_tokens"], 4000)

    def test_hard_bloat_budgets_hold(self) -> None:
        budgets = self.contract["hard_char_budgets"]
        self.assertTrue(validate_context_architecture.REQUIRED_BUDGET_PATHS.issubset(budgets))
        for path, ceiling in budgets.items():
            self.assertLessEqual(
                len((ROOT / path).read_text(encoding="utf-8")),
                ceiling,
                path,
            )

    def test_required_budget_key_cannot_be_removed(self) -> None:
        mutated = copy.deepcopy(self.contract)
        removed = "AGENTS.md"
        mutated["hard_char_budgets"].pop(removed)
        with self.assertRaisesRegex(
            validate_context_architecture.ContextArchitectureError,
            "missing mandatory hard context budgets",
        ):
            validate_context_architecture.validate(mutated)

    def test_repository_local_reports_are_bounded_to_outputs(self) -> None:
        for path in ("Candidates/context.json", "Active/context.json", "context.json"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    validate_context_architecture.ContextArchitectureError,
                    "repository-local report must be written under Outputs/",
                ):
                    validate_context_architecture.resolve_output(path)
        self.assertEqual(
            validate_context_architecture.resolve_output("Outputs/context.json"),
            (ROOT / "Outputs/context.json").resolve(),
        )

    def test_root_indexes_route_instead_of_preloading(self) -> None:
        codebase = (ROOT / "CODEBASE_MAP.md").read_text(encoding="utf-8")
        skills = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        self.assertIn("harness/CONTEXT.md", codebase)
        self.assertIn("harness/CONTEXT.md", skills)
        self.assertIn("selection index", skills)
        self.assertIn("Do **not** preload", codebase)

    def test_binding_domain_law_is_demand_loaded_and_incorporated(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for path in self.contract["binding_specs"].values():
            self.assertTrue((ROOT / path).is_file(), path)
            self.assertIn(path, agents)

    def test_two_largest_active_skills_are_factored(self) -> None:
        for path in (
            ".ai/skills/harness-infrastructure-maintenance/SKILL.md",
            ".ai/skills/technician-prompt-kit-acquisition/SKILL.md",
        ):
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertLessEqual(text.__len__(), self.contract["hard_char_budgets"][path])
            self.assertIn("## Procedure", text)
            self.assertIn("## Proof ceiling", text)


class PromptWayfindingBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.eval_contract = json.loads(
            (ROOT / "harness/evals/prompt-wayfinding-baseline.v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.fixture = json.loads(
            (
                ROOT
                / "harness/evals/fixtures/prompt-wayfinding-route-cases.v1.json"
            ).read_text(encoding="utf-8")
        )
        cls.router = (ROOT / "harness/CONTEXT.md").read_text(encoding="utf-8")
        cls.skill = (
            ROOT / ".ai/skills/operant-external-resource-intake/SKILL.md"
        ).read_text(encoding="utf-8")
        cls.donor_contract = json.loads(
            (
                ROOT / "harness/contracts/operant-external-resource-intake.v1.json"
            ).read_text(encoding="utf-8")
        )

    def test_route_corpus_schema_kinds_and_representative_owners(self) -> None:
        self.assertEqual(
            self.fixture["schema_version"], "prompt-wayfinding-route-cases/v1"
        )
        cases = self.fixture["cases"]
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        kinds = {case["kind"] for case in cases}
        required = set(self.eval_contract["required_case_kinds"])
        self.assertTrue(required.issubset(kinds))
        by_id = {case["id"]: case for case in cases}
        expected_owners = {
            "donor-upstream-coverage": "operant-external-resource-intake",
            "prompt-admission-after-prior-art": "P79",
            "unknown-prompt-fit": "P65",
            "context-bloat-finding-owners": "P76",
            "agent-code-readability": "P124",
            "pr-standards-spec-review": "P14",
        }
        for case_id, owner in expected_owners.items():
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, by_id)
                self.assertEqual(by_id[case_id]["expected_primary_owner"], owner)
                self.assertEqual(by_id[case_id]["kind"], "positive")
        self.assertTrue(by_id["empty-query-boundary"].get("expected_empty"))
        self.assertFalse(
            by_id["mimo-donor-broad-search-baseline"]["observed_prechange"][
                "router_had_donor_row"
            ]
        )

    def test_eval_contract_metrics_invariants_and_proof_ceiling(self) -> None:
        self.assertEqual(
            self.eval_contract["schema_version"],
            "prompt-wayfinding-baseline-eval/v1",
        )
        self.assertEqual(
            self.eval_contract["target"]["default_entrypoints"],
            ["AGENTS.md", "harness/CONTEXT.md"],
        )
        self.assertEqual(self.eval_contract["owner"], "P76")
        self.assertEqual(self.eval_contract["metrics"]["correct_first_owner_min"], 1.0)
        self.assertEqual(
            self.eval_contract["metrics"][
                "max_route_hops_from_default_for_one_hop_cases"
            ],
            1,
        )
        self.assertEqual(
            self.eval_contract["metrics"][
                "max_grep_glob_search_count_for_one_hop_cases"
            ],
            0,
        )
        self.assertIn("proof_ceiling", self.eval_contract)
        self.assertIn(
            "does not claim model-general runtime behavior",
            " ".join(self.eval_contract["invariants"]),
        )

    def test_donor_prior_art_route_is_one_hop_from_default_router(self) -> None:
        router_lower = self.router.casefold()
        for phrase in (
            "donor",
            "prior-art",
            "operant-external-resource-intake",
            "prompt_registry_ops.py",
        ):
            self.assertIn(phrase.casefold(), router_lower, phrase)
        for case in self.fixture["cases"]:
            if case["id"] in (
                "donor-upstream-coverage",
                "prompt-admission-after-prior-art",
                "mimo-donor-broad-search-baseline",
            ):
                self.assertEqual(case["max_route_hops_from_default"], 1)
                self.assertEqual(case["max_grep_glob_search_count"], 0)
                for phrase in case["router_phrases"]:
                    self.assertIn(
                        phrase.casefold(), router_lower, f"{case['id']}:{phrase}"
                    )

    def test_default_router_stays_inside_hard_budget_after_route_addition(self) -> None:
        router_path = "harness/CONTEXT.md"
        contract = json.loads(
            (ROOT / "harness/contracts/context-architecture.v1.json").read_text(
                encoding="utf-8"
            )
        )
        ceiling = contract["hard_char_budgets"][router_path]
        chars = len((ROOT / router_path).read_text(encoding="utf-8"))
        self.assertLessEqual(chars, ceiling, f"{router_path}={chars}>{ceiling}")
        self.assertEqual(validate_context_architecture.main(["--summary"]), 0)

    def test_intake_skill_points_to_contract_sources_instead_of_copying_donor_list(self) -> None:
        self.assertIn(
            "harness/contracts/operant-external-resource-intake.v1.json",
            self.skill,
        )
        self.assertIn("sources[]", self.skill)
        for stale in (
            "deepseek-ai/deepseek-harness",
            "f/prompts.chat",
            "mattpocock/skills",
            "Registered donor floor (current contract)",
        ):
            self.assertNotIn(stale, self.skill, stale)
        source_ids = {source["id"] for source in self.donor_contract["sources"]}
        self.assertEqual(
            source_ids,
            {
                "deepseek-harness",
                "prompts-chat",
                "mattpocock-skills",
                "michaelshimeles-skills",
            },
        )
        self.assertEqual(len(self.donor_contract["sources"]), 4)


if __name__ == "__main__":
    unittest.main()
