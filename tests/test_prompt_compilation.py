from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import prompt_language_compiler as compiler

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_ARCHITECTURE.md"
SPRINT = ROOT / "harness" / "prompt-compilation" / "PROMPT_COMPILATION_SPRINT_MAP.md"
FIXTURE = ROOT / "harness" / "prompt-compilation" / "fixtures" / "TC06-parallelism-modality"
P07_SEMANTICS = ROOT / "harness" / "prompt-compilation" / "semantics" / "P07.json"
EXAMPLE_CANDIDATE = (
    ROOT / "harness" / "prompt-compilation" / "examples" / "improvement-candidate.example.json"
)
CONTRACTS = {
    "semantics": ROOT / "harness" / "contracts" / "prompt-semantics.v1.json",
    "profile": ROOT / "harness" / "contracts" / "prompt-execution-profile.v1.json",
    "context": ROOT / "harness" / "contracts" / "prompt-context.v1.json",
    "receipt": ROOT / "harness" / "contracts" / "prompt-build-receipt.v1.json",
    "candidate": ROOT / "harness" / "contracts" / "prompt-improvement-candidate.v1.json",
    "policy": ROOT / "harness" / "contracts" / "prompt-language-compiler-policy.v1.json",
}


class PromptCompilationArchitectureTests(unittest.TestCase):
    def test_architecture_and_sprint_map_exist(self) -> None:
        self.assertTrue(ARCH.is_file())
        self.assertTrue(SPRINT.is_file())

    def test_preserves_p95_boundary(self) -> None:
        text = ARCH.read_text(encoding="utf-8")
        for phrase in (
            "does **not** own lifecycle events",
            "thin read-only adapters",
            "universal envelope",
            "competing Evidence Spine",
            "reviewed_pr_only",
            "prompt-semantics/v1",
            "prompt-execution-profile/v1",
            "prompt-context/v1",
        ):
            self.assertIn(phrase, text)

    def test_sprint_map_forbids_ui_and_donors(self) -> None:
        text = SPRINT.read_text(encoding="utf-8")
        for phrase in (
            "UI toggle implementation",
            "#450 / #431",
            "raw conversation ingestion",
            "universal event bus",
            "automatic PR merge",
        ):
            self.assertIn(phrase, text)


class PromptLanguageCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = compiler.load_policy()
        cls.semantics = compiler.load_json(FIXTURE / "semantics.json")
        cls.profile = compiler.load_json(FIXTURE / "profile.json")
        cls.context = compiler.load_json(FIXTURE / "context.json")

    def test_contracts_exist(self) -> None:
        for path in CONTRACTS.values():
            self.assertTrue(path.is_file(), path)

    def test_tc06_fixture_compiles_imperative_dispatch(self) -> None:
        result = compiler.render(self.semantics, self.profile, self.context, policy=self.policy)
        prompt = result["effective_prompt"]
        receipt = result["receipt"]
        self.assertEqual(receipt["activated_obligations"], ["parallel_dispatch"])
        self.assertTrue(receipt["non_weakening_passed"])
        self.assertIn("MUST dispatch independent lanes in parallel", prompt)
        self.assertIn("typed failure disposition AUTONOMY_GAP", prompt)
        self.assertIn("observed_parallel_dispatch_receipt", prompt)
        self.assertEqual(receipt["execution_profile"], "exhaustive")
        self.assertEqual(receipt["schema_version"], "prompt-build-receipt/v1")
        self.assertRegex(receipt["effective_prompt_sha256"], r"^[a-f0-9]{64}$")

    def test_p07_always_compiles_local_proof_and_mainline_convergence(self) -> None:
        semantics = compiler.load_json(P07_SEMANTICS)
        result = compiler.render(semantics, self.profile, self.context, policy=self.policy)
        prompt = result["effective_prompt"]
        self.assertEqual(
            result["receipt"]["activated_obligations"],
            ["local_proof_continuity", "mainline_convergence", "parallel_dispatch"],
        )
        for phrase in (
            "MUST establish or reuse a repository-native local validation and integration proof path before hosted CI becomes a dependency",
            "MUST bind local proof to its canonical owner, exact action or command, base and head identity, required inputs, receipt or result, and nonzero-exit propagation",
            "When hosted CI is quota-exhausted, rate-limited, unavailable, or permission-blocked, MUST continue through local proof for every gate that local proof can honestly prove",
            "MUST suppress blind retries of known non-transient hosted CI failures and preserve hosted-only gates as BLOCKED",
            "typed failure disposition LOCAL_PROOF_GAP",
            "local_proof_packet_with_owner_command_base_inputs_exit_behavior_or_named_hosted_only_gate",
            "MUST treat a validated owned branch or pull request as intermediate evidence, not completion",
            "MUST integrate the exact validated owned head into the current default branch",
            "After integration, MUST refresh default-branch truth and verify the intended change remains contained before completion",
            "typed failure disposition INTEGRATION_GAP",
            "verified_default_branch_contains_validated_owned_change_or_exact_named_merge_gate",
        ):
            self.assertIn(phrase, prompt)

    def test_p07_must_obligations_survive_efficient_profile(self) -> None:
        semantics = compiler.load_json(P07_SEMANTICS)
        efficient = {
            "schema_version": "prompt-execution-profile/v1",
            "profile": "efficient",
            "compute_policy": "minimum_sufficient_compute",
            "parallel_policy": "parallelize_when_expected_gain_exceeds_coordination_cost",
            "hypothesis_policy": "test_alternatives_only_when_materially_ambiguous",
            "validation_policy": "minimum_authoritative_acceptance_set",
            "stop_policy": "sufficient_proof_for_requested_scope",
            "non_weakenable_constraints": sorted(compiler.REQUIRED_NON_WEAKENABLE),
        }
        context = json.loads(json.dumps(self.context))
        context["execution"]["dependency_ready_width"] = 1
        context["execution"]["parallel_width"] = 1
        context["execution"]["safe_capacity"] = 1
        result = compiler.render(semantics, efficient, context, policy=self.policy)
        self.assertEqual(
            result["receipt"]["activated_obligations"],
            ["local_proof_continuity", "mainline_convergence"],
        )
        self.assertIn("LOCAL_PROOF_GAP", result["effective_prompt"])
        self.assertIn("INTEGRATION_GAP", result["effective_prompt"])

    def test_rejects_weakening_constructs_for_must_obligation(self) -> None:
        weak = (
            "Consider parallel work where useful. Agents could dispatch lanes "
            "if appropriate and may parallelize when convenient."
        )
        with self.assertRaises(compiler.PromptCompilationError) as ctx:
            compiler.render(
                self.semantics,
                self.profile,
                self.context,
                policy=self.policy,
                effective_prompt_override=weak,
            )
        self.assertIn("non-weakening validator", str(ctx.exception))

    def test_rejects_weakening_even_when_required_phrases_present(self) -> None:
        weak_but_complete = (
            "MUST dispatch independent lanes in parallel. "
            "typed failure disposition AUTONOMY_GAP. "
            "observed_parallel_dispatch_receipt. "
            "Consider parallel work where useful and may parallelize."
        )
        with self.assertRaises(compiler.PromptCompilationError) as ctx:
            compiler.render(
                self.semantics,
                self.profile,
                self.context,
                policy=self.policy,
                effective_prompt_override=weak_but_complete,
            )
        self.assertIn("non-weakening validator", str(ctx.exception))

    def test_efficient_profile_still_enforces_must_non_weakening(self) -> None:
        efficient = {
            "schema_version": "prompt-execution-profile/v1",
            "profile": "efficient",
            "compute_policy": "minimum_sufficient_compute",
            "parallel_policy": "parallelize_when_expected_gain_exceeds_coordination_cost",
            "hypothesis_policy": "test_alternatives_only_when_materially_ambiguous",
            "validation_policy": "minimum_authoritative_acceptance_set",
            "stop_policy": "sufficient_proof_for_requested_scope",
            "non_weakenable_constraints": sorted(compiler.REQUIRED_NON_WEAKENABLE),
        }
        result = compiler.render(self.semantics, efficient, self.context, policy=self.policy)
        self.assertEqual(result["receipt"]["execution_profile"], "efficient")
        self.assertEqual(result["receipt"]["activated_obligations"], ["parallel_dispatch"])
        with self.assertRaises(compiler.PromptCompilationError):
            compiler.render(
                self.semantics,
                efficient,
                self.context,
                policy=self.policy,
                effective_prompt_override="Consider parallel if appropriate.",
            )

    def test_profile_cannot_omit_non_weakenable_constraints(self) -> None:
        bad = dict(self.profile)
        bad["non_weakenable_constraints"] = ["safety", "privacy"]
        with self.assertRaises(compiler.PromptCompilationError):
            compiler.validate_profile(bad)

    def test_context_rejects_event_ownership_fields(self) -> None:
        bad = json.loads(json.dumps(self.context))
        bad["events"] = [{"id": "e1"}]
        with self.assertRaises(compiler.PromptCompilationError):
            compiler.validate_context(bad)

    def test_improvement_candidate_requires_reviewed_pr_only(self) -> None:
        candidate = compiler.compile_improvement_candidate(
            failure_identity="parallel_dispatch.modality_weakened",
            evidence_refs=["receipt-a", "finding-b"],
            affected_authority="language-engine",
            rule="MUST obligations may not compile through permissive modal verbs",
            required_regressions=["TC06-parallelism-modality"],
            candidate_id="IC-parallel-dispatch-modality-weakened",
        )
        self.assertEqual(candidate["promotion_authority"], "reviewed_pr_only")
        example = compiler.load_json(EXAMPLE_CANDIDATE)
        compiler.validate_improvement_candidate(example)

    def test_validate_fixtures_cli_path(self) -> None:
        self.assertEqual(compiler.validate_fixtures(summary=False), 0)

    def test_inactive_when_predicate_not_met(self) -> None:
        context = json.loads(json.dumps(self.context))
        context["execution"]["dependency_ready_width"] = 1
        context["execution"]["safe_capacity"] = 1
        result = compiler.render(self.semantics, self.profile, context, policy=self.policy)
        self.assertEqual(result["receipt"]["activated_obligations"], [])


if __name__ == "__main__":
    unittest.main()
