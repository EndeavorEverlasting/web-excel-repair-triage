from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p67_source_faithfulness_eval",
    ROOT / "scripts/evaluate_p67_source_faithfulness.py",
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

PAIR_FIXTURE = ROOT / "tests/fixtures/p67_source_faithfulness/opencode_p122_pair.v1.json"


class P67SourceFaithfulnessEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pair = MOD._load_pair_fixture(PAIR_FIXTURE)
        cls.source_path, cls.source = MOD._source_fixture(cls.pair)
        cls.p100 = MOD._load_p100()
        cls.cases = {
            item["id"]: MOD.materialize_case(item, cls.source)
            for item in cls.pair["cases"]
        }

    def test_pair_is_p67_owned_and_anchors_the_exact_p100_history(self):
        self.assertEqual(self.pair["owner"], "P67")
        self.assertEqual(self.pair["guard_owner"], "P100")
        self.assertEqual(
            self.pair["source_fixture"],
            "tests/fixtures/p100_closeout_replay/opencode_p122_closeout_01ac559.v1.json",
        )
        self.assertEqual(self.source["candidate_sha"], "01ac559ac5ff774978a0cdedcb27f9b816bfb9d4")
        present = self.cases["present-authoritative-context"]
        self.assertIn("feat/gemini-youtube-ingestion-prompt-20260827", present["observed_closeout_text"])
        self.assertEqual(
            [item["id"] for item in present["authoritative_evidence"]],
            ["deterministic-test-floor-red", "acknowledged-p122-identity-conflict"],
        )
        self.assertEqual(present["authoritative_evidence"][0]["run_id"], 33086093122)

    def test_missing_and_present_prompts_keep_source_truth_separated(self):
        missing_prompt = MOD.build_prompt(self.cases["missing-authoritative-context"], self.p100)
        present_prompt = MOD.build_prompt(self.cases["present-authoritative-context"], self.p100)

        self.assertNotIn("33086093122", missing_prompt)
        self.assertNotIn("feat/gemini-youtube-ingestion-prompt-20260827", missing_prompt)
        self.assertIn("NONE SUPPLIED", missing_prompt)
        self.assertNotIn("Expected reason vocabulary for this case", missing_prompt)
        self.assertNotIn("Missing authoritative evidence must be GROUND", missing_prompt)

        self.assertIn("33086093122", present_prompt)
        self.assertIn("feat/gemini-youtube-ingestion-prompt-20260827", present_prompt)
        self.assertIn("FAITHFULNESS_CONTEXT_IGNORED closure failure", present_prompt)

    def test_correct_paired_diagnosis_passes_the_deterministic_oracle(self):
        responses = {
            "missing-authoritative-context": (
                "DECISION: GROUND\n"
                "CLASSIFICATION: FACTUALITY_CONTEXT_MISSING\n"
                "REMEDIATION: TARGETED_GROUNDING\n"
                "REASONS: missing_authoritative_evidence\n"
            ),
            "present-authoritative-context": (
                "DECISION: CONTINUE\n"
                "CLASSIFICATION: FAITHFULNESS_CONTEXT_IGNORED\n"
                "REMEDIATION: REANCHOR_EXISTING_CONTEXT\n"
                "REASONS: acknowledged_identity_conflict, required_gate_failure\n"
            ),
        }
        report = MOD.evaluate_responses(
            self.pair,
            self.source,
            self.p100,
            responses,
            evidence_class="synthetic",
            runtime={"mode": "unit-test"},
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["evidence_class"], "synthetic")
        self.assertTrue(all(item["status"] == "PASS" for item in report["cases"]))
        self.assertIn("deterministic oracle only", report["proof_ceiling"])

    def test_present_context_terminal_recurrence_fails_as_faithfulness(self):
        response = (
            "DECISION: TERMINAL\n"
            "CLASSIFICATION: NONE\n"
            "REMEDIATION: NONE\n"
            "REASONS: none\n"
        )
        result = MOD.score_response(
            self.cases["present-authoritative-context"],
            response,
            self.source,
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("decision expected CONTINUE" in error for error in result["errors"]))
        self.assertTrue(
            any(
                "classification expected FAITHFULNESS_CONTEXT_IGNORED" in error
                for error in result["errors"]
            )
        )
        self.assertTrue(
            any(
                "remediation expected REANCHOR_EXISTING_CONTEXT" in error
                for error in result["errors"]
            )
        )

    def test_missing_context_cannot_invent_hidden_run_or_branch_evidence(self):
        response = (
            "I found run 33086093122 and feat/gemini-youtube-ingestion-prompt-20260827.\n"
            "DECISION: GROUND\n"
            "CLASSIFICATION: FACTUALITY_CONTEXT_MISSING\n"
            "REMEDIATION: TARGETED_GROUNDING\n"
            "REASONS: missing_authoritative_evidence\n"
        )
        result = MOD.score_response(
            self.cases["missing-authoritative-context"],
            response,
            self.source,
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(
            set(result["hidden_evidence_mentions"]),
            {"33086093122", "feat/gemini-youtube-ingestion-prompt-20260827"},
        )
        self.assertTrue(any("invented hidden evidence" in error for error in result["errors"]))

    def test_unavailable_opencode_runtime_stays_unproven(self):
        with mock.patch.object(MOD, "resolve_runtime", return_value=(None, None)):
            report = MOD.run_opencode(
                self.pair,
                self.source,
                self.p100,
                requested_runtime="auto",
                model=None,
                timeout_seconds=10,
            )
        self.assertEqual(report["status"], "UNPROVEN")
        self.assertEqual(report["evidence_class"], "none")
        self.assertIn("OpenCode CLI not found", report["blocker"])
        self.assertIn("remains UNPROVEN", report["proof_ceiling"])

    def test_live_lane_uses_non_shell_opencode_run_and_can_emit_observed_receipt(self):
        missing = (
            "DECISION: GROUND\n"
            "CLASSIFICATION: FACTUALITY_CONTEXT_MISSING\n"
            "REMEDIATION: TARGETED_GROUNDING\n"
            "REASONS: missing_authoritative_evidence\n"
        )
        present = (
            "DECISION: CONTINUE\n"
            "CLASSIFICATION: FAITHFULNESS_CONTEXT_IGNORED\n"
            "REMEDIATION: REANCHOR_EXISTING_CONTEXT\n"
            "REASONS: required_gate_failure,acknowledged_identity_conflict\n"
        )
        calls = []

        def fake_run(command, timeout_seconds):
            calls.append((command, timeout_seconds))
            if command[1:] == ["--version"]:
                return subprocess.CompletedProcess(command, 0, stdout="1.2.3\n", stderr="")
            output = missing if len(calls) == 2 else present
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        with (
            mock.patch.object(MOD, "resolve_runtime", return_value=("opencode", "/usr/bin/opencode")),
            mock.patch.object(MOD, "_run_command", side_effect=fake_run),
        ):
            report = MOD.run_opencode(
                self.pair,
                self.source,
                self.p100,
                requested_runtime="opencode",
                model="provider/model",
                timeout_seconds=25,
            )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["evidence_class"], "target_runtime_observed")
        self.assertEqual(report["runtime"]["version"], "1.2.3")
        self.assertEqual(report["runtime"]["model_requested"], "provider/model")
        self.assertEqual(calls[1][0][:4], ["/usr/bin/opencode", "run", "--model", "provider/model"])
        self.assertEqual(calls[2][0][:4], ["/usr/bin/opencode", "run", "--model", "provider/model"])

        receipt = MOD.build_observed_receipt(
            report,
            commit_sha="a" * 40,
            fixture_path=PAIR_FIXTURE,
        )
        self.assertEqual(receipt["schema_version"], "observed-behavior-proof/v1")
        self.assertEqual(receipt["evidence_class"], "target_runtime_observed")
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertEqual(receipt["subject"]["commit_sha"], "a" * 40)
        self.assertEqual(
            receipt["subject"]["artifact"]["path"],
            "tests/fixtures/p67_source_faithfulness/opencode_p122_pair.v1.json",
        )
        self.assertEqual(len(receipt["observations"]), 2)
        self.assertTrue(all(item["occurred"] and item["passed"] for item in receipt["observations"]))

    def test_runtime_lane_is_registered_in_observed_proof_and_test_floor_manifests(self):
        observed = json.loads((ROOT / "harness/observed-proof/manifest.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(observed["model_runtime_eval"], "scripts/evaluate_p67_source_faithfulness.py")
        self.assertEqual(
            observed["model_runtime_fixture"],
            "tests/fixtures/p67_source_faithfulness/opencode_p122_pair.v1.json",
        )
        self.assertEqual(observed["model_runtime_evidence_class"], "target_runtime_observed")

        floor = json.loads((ROOT / "harness/test-floor.v1.json").read_text(encoding="utf-8"))
        self.assertIn("tests/test_p67_source_faithfulness_eval_prompt.py", floor["self_tests"])

    def test_p67_owner_already_requires_paired_factuality_faithfulness_cases(self):
        registry = MOD.build_prompt_kit_registry.load_prompt_registry()
        p67 = next(item for item in registry if item["id"] == "P67")
        for phrase in (
            "3A. EVALUATE HALLUCINATION DIAGNOSIS",
            "missing-context case",
            "present-but-ignored case",
            "Score both the failure classification",
        ):
            self.assertIn(phrase, p67["copyContent"])


if __name__ == "__main__":
    unittest.main()
