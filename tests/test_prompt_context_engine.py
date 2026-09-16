from __future__ import annotations

import unittest

from scripts import prompt_context_engine as engine
from scripts import prompt_language_compiler as compiler


class PromptContextEngineTests(unittest.TestCase):
    def test_profile_precedence_run_beats_prompt_and_user(self) -> None:
        result = engine.resolve_execution_profile(
            explicit_run_override="efficient",
            prompt_override="exhaustive",
            user_default="exhaustive",
            product_default="exhaustive",
        )
        self.assertEqual(result["resolution"]["resolved_from"], "explicit_run_override")
        self.assertEqual(result["profile"]["profile"], "efficient")

    def test_profile_precedence_prompt_beats_user(self) -> None:
        result = engine.resolve_execution_profile(
            prompt_override="efficient",
            user_default="exhaustive",
        )
        self.assertEqual(result["resolution"]["resolved_from"], "prompt_override")
        self.assertEqual(result["profile"]["profile"], "efficient")

    def test_product_default_when_no_overrides(self) -> None:
        result = engine.resolve_execution_profile()
        self.assertEqual(result["resolution"]["resolved_from"], "product_default")
        self.assertEqual(result["profile"]["profile"], "exhaustive")

    def test_project_context_from_owner_artifacts(self) -> None:
        context = engine.project_prompt_context(
            repository_head="602df5086c61d81382eb2835dcb119eaa71d4ae5",
            owned_scope=["harness/prompt-compilation/**"],
            active_contracts=["prompt-parallel-dispatch/v1"],
            dispatch_receipt={
                "observed_parallelism": True,
                "graph_width": 2,
                "safe_capacity": 2,
                "dependency_ready_width": 2,
                "adapters_probed": ["native_subagent", "local_process"],
            },
            continuation_disposition={"disposition": "continue", "rationale": "work remains"},
            outcome_receipts=[{"result": "FAILURE", "classification": {"primary": "execution"}}],
            recurrence_findings=[
                {
                    "contract_failure_id": "contract.parallel_dispatch.execution_missing",
                    "state": "confirmed_recurrence",
                }
            ],
            effective_prompt_identity="P07",
        )
        compiler.validate_context(context)
        self.assertEqual(context["execution"]["parallel_width"], 2)
        self.assertFalse(context["evidence"]["open_recovery"])
        self.assertIn("observed_parallelism", context["evidence"]["known_acceptance_gates"])
        self.assertIn(
            "contract.parallel_dispatch.execution_missing",
            context["history"]["relevant_recurrences"],
        )
        self.assertIn("dispatch_receipt_read", context["source_adapters"])

    def test_recovery_disposition_sets_open_recovery(self) -> None:
        context = engine.project_prompt_context(
            repository_head="602df5086c61d81382eb2835dcb119eaa71d4ae5",
            owned_scope=["scripts/prompt_context_engine.py"],
            continuation_disposition={"disposition": "recover"},
        )
        self.assertTrue(context["evidence"]["open_recovery"])

    def test_projected_context_compiles_with_language_engine(self) -> None:
        semantics = compiler.load_json(
            compiler.ROOT
            / "harness/prompt-compilation/fixtures/TC06-parallelism-modality/semantics.json"
        )
        profile = engine.resolve_execution_profile(explicit_run_override="exhaustive")["profile"]
        context = engine.project_prompt_context(
            repository_head="602df5086c61d81382eb2835dcb119eaa71d4ae5",
            owned_scope=["harness/prompt-compilation/**"],
            dispatch_receipt={
                "graph_width": 2,
                "safe_capacity": 2,
                "dependency_ready_width": 2,
                "observed_parallelism": False,
                "adapters_probed": ["native_subagent"],
            },
            effective_prompt_identity="P07",
        )
        result = compiler.render(semantics, profile, context)
        self.assertEqual(result["receipt"]["activated_obligations"], ["parallel_dispatch"])
        self.assertIn("MUST dispatch independent lanes in parallel", result["effective_prompt"])

    def test_adapters_do_not_accept_event_bus_payload_as_context_root(self) -> None:
        # project_prompt_context never places raw events onto the context object.
        context = engine.project_prompt_context(
            repository_head="602df5086c61d81382eb2835dcb119eaa71d4ae5",
            owned_scope=["x"],
        )
        self.assertNotIn("events", context)
        self.assertNotIn("event_bus", context)


if __name__ == "__main__":
    unittest.main()
