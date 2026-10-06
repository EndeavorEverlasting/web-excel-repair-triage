from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prompt_invocation_composition.py"
CONTRACT = ROOT / "harness/contracts/prompt-invocation-composition.v1.json"

spec = importlib.util.spec_from_file_location("prompt_invocation_composition", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class PromptInvocationCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def request(self, invocations, facets, **facts):
        return {
            "schema_version": "prompt-invocation-request/v1",
            "invocations": invocations,
            "task_facets": facets,
            "facts": facts,
        }

    def test_contract_validates_and_has_prior_art(self) -> None:
        self.assertEqual(mod.validate_contract(self.contract), [])
        self.assertGreaterEqual(len(self.contract["p97_prior_art"]), 4)
        self.assertIn("authority_divergence_guard", self.contract["mathematical_model"])

    def test_contract_validation_rejects_missing_authority_invariant(self) -> None:
        contract = json.loads(json.dumps(self.contract))
        del contract["mathematical_model"]["authority_source_invariant"]
        errors = mod.validate_contract(contract)
        self.assertIn(
            "mathematical_model.authority_source_invariant must be a non-empty string",
            errors,
        )

    def test_invocation_projects_instead_of_importing_everything(self) -> None:
        result = mod.compose(
            self.request(["P01", "P07"], ["harness.integrity"]),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P01"])
        self.assertEqual(result["selected"][0]["residual_facets"], ["harness.integrity"])
        self.assertEqual(result["suppressed"][0]["prompt_id"], "P07")

    def test_orthogonal_hybrid_linearizes_without_super_authority(self) -> None:
        result = mod.compose(
            self.request(
                ["P82", "P08", "P07", "P04", "P01"],
                [
                    "harness.integrity",
                    "planning.factor",
                    "execution.repository_mutation",
                    "proof.live_runtime",
                    "iteration.empirical",
                ],
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P01", "P04", "P07", "P08", "P82"])
        self.assertEqual(result["authority_effect"], "NO_AUTHORITY_EXPANSION")
        self.assertIn(["P04", "P07"], result["precedence_edges"])
        self.assertIn(["P07", "P08"], result["precedence_edges"])

    def test_p05_preserves_bounded_recovery_when_factoring_artifact_absent(self) -> None:
        result = mod.compose(
            self.request(
                ["P05"],
                ["planning.pack", "planning.runtime_partition"],
                p04_factoring_artifact_state="ABSENT",
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P05"])
        self.assertEqual(result["pushback"][0]["code"], "P05_BOUNDED_RECOVERY_FACTORING")
        self.assertEqual(result["selected"][0]["inherited_facets"], [])
        self.assertEqual(
            result["selected"][0]["residual_facets"],
            ["planning.pack", "planning.runtime_partition"],
        )

    def test_p05_pack_only_does_not_invent_runtime_partition(self) -> None:
        result = mod.compose(
            self.request(
                ["P05"],
                ["planning.pack"],
                p04_factoring_artifact_state="ABSENT",
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P05"])
        self.assertEqual(result["selected"][0]["projected_facets"], ["planning.pack"])
        self.assertEqual(result["selected"][0]["inherited_facets"], [])
        self.assertEqual(result["selected"][0]["residual_facets"], ["planning.pack"])

    def test_full_factoring_task_routes_p04_before_p05_without_invented_facets(self) -> None:
        result = mod.compose(
            self.request(
                ["P05"],
                ["planning.factor", "planning.pack"],
                p04_factoring_artifact_state="ABSENT",
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "ROUTE_REQUIRED")
        self.assertEqual(result["linearization"], ["P04", "P05"])
        self.assertEqual(result["pushback"][0]["code"], "ROUTE_P04_THEN_P05")
        p04 = next(x for x in result["selected"] if x["prompt_id"] == "P04")
        self.assertEqual(p04["projected_facets"], ["planning.factor"])
        self.assertEqual(p04["residual_facets"], ["planning.factor"])
        self.assertNotIn("planning.runtime_partition", p04["projected_facets"])

    def test_p05_consumes_current_p04_artifact_without_reinvoking_p04(self) -> None:
        result = mod.compose(
            self.request(
                ["P05"],
                ["planning.pack", "planning.runtime_partition"],
                p04_factoring_artifact_state="ACCEPTED_CURRENT",
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P05"])
        self.assertEqual(result["pushback"][0]["code"], "P05_CONSUME_P04_ARTIFACT")
        self.assertEqual(result["selected"][0]["residual_facets"], ["planning.pack"])
        self.assertEqual(
            result["selected"][0]["inherited_facets"],
            ["planning.runtime_partition"],
        )

    def test_current_p04_artifact_does_not_invent_unprojected_inheritance(self) -> None:
        result = mod.compose(
            self.request(
                ["P05"],
                ["planning.pack"],
                p04_factoring_artifact_state="ACCEPTED_CURRENT",
            ),
            self.contract,
        )
        self.assertEqual(result["linearization"], ["P05"])
        self.assertEqual(result["selected"][0]["inherited_facets"], [])
        self.assertEqual(result["selected"][0]["residual_facets"], ["planning.pack"])

    def test_current_p04_artifact_subtracts_shared_intersection_from_both_invocations(self) -> None:
        result = mod.compose(
            self.request(
                ["P04", "P05"],
                ["planning.pack", "planning.runtime_partition"],
                p04_factoring_artifact_state="ACCEPTED_CURRENT",
            ),
            self.contract,
        )
        self.assertEqual(result["state"], "COMPOSED")
        self.assertEqual(result["linearization"], ["P05"])
        suppressed = {row["prompt_id"]: row for row in result["suppressed"]}
        self.assertEqual(
            suppressed["P04"]["state"],
            "INVOKED_NO_APPLICABLE_RESIDUAL",
        )
        self.assertEqual(
            suppressed["P04"]["inherited_facets"],
            ["planning.runtime_partition"],
        )

    def test_p05_missing_artifact_fact_fails_context_deterministically(self) -> None:
        result = mod.compose(
            self.request(["P05"], ["planning.pack"]),
            self.contract,
        )
        self.assertEqual(result["state"], "INSUFFICIENT_CONTEXT")
        self.assertEqual(result["pushback"][0]["code"], "P04_ARTIFACT_STATE_REQUIRED")

    def test_unresolved_overlap_fails_closed(self) -> None:
        contract = json.loads(json.dumps(self.contract))
        contract["prompt_facets"]["P01"].append("collision.demo")
        contract["prompt_facets"]["P07"].append("collision.demo")
        result = mod.compose(
            self.request(["P01", "P07"], ["collision.demo"]),
            contract,
        )
        self.assertEqual(result["state"], "INCOHERENT_INVOCATION")
        self.assertEqual(result["pushback"][-1]["code"], "UNRESOLVED_OVERLAP")

    def test_pair_rule_does_not_cover_future_undeclared_overlap(self) -> None:
        contract = json.loads(json.dumps(self.contract))
        contract["prompt_facets"]["P04"].append("planning.future_shared")
        contract["prompt_facets"]["P05"].append("planning.future_shared")
        result = mod.compose(
            self.request(
                ["P04", "P05"],
                [
                    "planning.pack",
                    "planning.runtime_partition",
                    "planning.future_shared",
                ],
                p04_factoring_artifact_state="ACCEPTED_CURRENT",
            ),
            contract,
        )
        self.assertEqual(result["state"], "INCOHERENT_INVOCATION")
        self.assertEqual(result["pushback"][-1]["code"], "UNDECLARED_PAIR_OVERLAP")
        self.assertEqual(result["pushback"][-1]["facets"], ["planning.future_shared"])

    def test_precedence_cycle_fails_closed(self) -> None:
        request = self.request(
            ["P04", "P07"],
            ["planning.factor", "execution.repository_mutation"],
        )
        request["explicit_precedence"] = [["P07", "P04"]]
        result = mod.compose(request, self.contract)
        self.assertEqual(result["state"], "INCOHERENT_INVOCATION")
        self.assertEqual(result["pushback"][-1]["code"], "PRECEDENCE_CYCLE")

    def test_self_precedence_cycle_fails_closed(self) -> None:
        request = self.request(["P01"], ["harness.integrity"])
        request["explicit_precedence"] = [["P01", "P01"]]
        result = mod.compose(request, self.contract)
        self.assertEqual(result["state"], "INCOHERENT_INVOCATION")
        self.assertEqual(result["pushback"][-1]["code"], "PRECEDENCE_CYCLE")

    def test_disjoint_invocation_order_has_canonical_linearization(self) -> None:
        a = mod.compose(
            self.request(["P82", "P01"], ["iteration.empirical", "harness.integrity"]),
            self.contract,
        )
        b = mod.compose(
            self.request(["P01", "P82"], ["iteration.empirical", "harness.integrity"]),
            self.contract,
        )
        self.assertEqual(a["linearization"], ["P01", "P82"])
        self.assertEqual(a["linearization"], b["linearization"])


if __name__ == "__main__":
    unittest.main()
