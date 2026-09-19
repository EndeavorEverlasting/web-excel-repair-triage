from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "harness" / "evals" / "runtime-compliance"
SCRIPTS = EVAL / "scripts"
FAKE_ADAPTER = SCRIPTS / "fake_adapter.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import pilot  # noqa: E402
import runtime_adapter  # noqa: E402


def fake_config(mode: str = "compliant") -> dict:
    return {
        "schema_version": "prompt-runtime-compliance-agent-adapter/v1",
        "argv": [
            sys.executable,
            str(FAKE_ADAPTER),
            "--scenario",
            "{scenario}",
            "--result",
            "{result}",
            "--mode",
            mode,
        ],
        "timeout_seconds": 30,
        "env_allowlist": [],
    }


class RuntimeComplianceRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(
            (EVAL / "runtime" / "capture-schema.v1.json").read_text(encoding="utf-8")
        )
        cls.contract = json.loads(
            (EVAL / "runtime" / "adapter-contract.v1.json").read_text(encoding="utf-8")
        )

    def test_capture_schema_and_adapter_contract_identities(self) -> None:
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(self.schema["$id"], "prompt-runtime-compliance-capture/v1")
        self.assertEqual(self.schema["schema_version"], "prompt-runtime-compliance-capture/v1")
        Draft202012Validator.check_schema(self.schema)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(
            self.contract["schema_version"],
            "prompt-runtime-compliance-agent-adapter-contract/v1",
        )
        self.assertFalse(self.contract["execution"]["shell"])
        self.assertEqual(
            self.contract["execution"]["result_transport"],
            "temporary_json_file",
        )
        self.assertEqual(
            self.contract["execution"]["stdout_stderr_persistence"],
            "forbidden",
        )
        self.assertFalse(self.contract["capture"]["fake_adapter_runtime_observed"])

    def test_plan_covers_exact_five_scenarios(self) -> None:
        plan = pilot.build_plan()
        self.assertEqual(plan["planned_runs"], 5)
        self.assertEqual(
            [row["scenario_id"] for row in plan["runs"]],
            ["RTC01", "RTC02", "RTC03", "RTC04", "RTC05"],
        )

    def test_rtc04_run_initialization_materializes_typed_target_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = pilot.initialize_run(
                "RTC04",
                run_id="init-rtc04",
                output_root=root,
            )
            target = json.loads(
                (run_dir / "workspace" / "target-state.json").read_text(encoding="utf-8")
            )
            fixture = json.loads((run_dir / "scenario.json").read_text(encoding="utf-8"))
            self.assertEqual(
                target["target_identity"],
                fixture["mutation_protocol"]["target_identity"],
            )
            self.assertEqual(
                target["state_fingerprint"],
                fixture["mutation_protocol"]["pre_state_fingerprint"],
            )
            self.assertFalse(target["mutation_applied"])

    def test_compliant_fake_adapter_runs_all_five_without_observed_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = pilot.execute_pilot(
                pilot.build_plan(),
                pilot_id="fake-five",
                adapter_config=fake_config(),
                output_root=root,
            )
            self.assertEqual(result["valid_runs"], 5)
            self.assertEqual(result["invalid_runs"], 0)
            self.assertEqual(result["observed_runs"], 0)
            self.assertEqual(result["runtime_state"], "UNPROVEN_RUNTIME")
            self.assertEqual(result["blocker"], "FAKE_OR_NONOBSERVED_ADAPTER")
            self.assertTrue(all(row["validation_result"] == "PASS" for row in result["runs"]))
            self.assertTrue(all(row["runtime_observed"] is False for row in result["runs"]))

    def test_rtc04_compliant_fake_capture_proves_readback_before_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = next(row for row in pilot.build_plan()["runs"] if row["scenario_id"] == "RTC04")
            result = pilot.execute_case(
                spec,
                pilot_id="rtc04-good",
                adapter_config=fake_config(),
                output_root=root,
            )
            self.assertEqual(result["validation_result"], "PASS")
            validation = json.loads(
                (root / "runs" / "rtc04-good-rtc04" / "validation.json").read_text(encoding="utf-8")
            )
            finding = next(
                row
                for row in validation["findings"]
                if row["rule_id"] == "PRCR.ACTION.PARTIAL_READBACK"
            )
            self.assertEqual(finding["result"], "PASS")

    def test_rtc04_readback_promotion_has_exact_passing_evidence_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = next(row for row in pilot.build_plan()["runs"] if row["scenario_id"] == "RTC04")
            result = pilot.execute_case(
                spec,
                pilot_id="rtc04-binding",
                adapter_config=fake_config(),
                output_root=root,
            )
            receipt = json.loads(
                (root / "runs" / result["run_id"] / "receipt.json").read_text(encoding="utf-8")
            )
            readback = next(
                action for action in receipt["actions"] if action["readback_of_action_id"] == "A-001"
            )
            matching_checks = [
                check
                for check in receipt["proof"]["checks"]
                if check["status"] == "PASS"
                and check["name"].startswith(f"action:{readback['action_id']}:")
                and set(readback["evidence_refs"]).intersection(check["evidence_refs"])
            ]
            self.assertEqual(len(matching_checks), 1)
            self.assertIn("EV-003", matching_checks[0]["evidence_refs"])

    def test_rtc04_missing_readback_is_detected_by_semantic_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = next(row for row in pilot.build_plan()["runs"] if row["scenario_id"] == "RTC04")
            result = pilot.execute_case(
                spec,
                pilot_id="rtc04-bad",
                adapter_config=fake_config("rtc04-no-readback"),
                output_root=root,
            )
            self.assertEqual(result["disposition"], "VALID")
            self.assertEqual(result["compliance_result"], "FAIL")
            self.assertEqual(result["validation_result"], "FAIL")
            validation = json.loads(
                (root / "runs" / "rtc04-bad-rtc04" / "validation.json").read_text(encoding="utf-8")
            )
            finding = next(
                row
                for row in validation["findings"]
                if row["rule_id"] == "PRCR.ACTION.PARTIAL_READBACK"
            )
            self.assertEqual(finding["result"], "FAIL")

    def test_privacy_leaking_fake_capture_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = pilot.build_plan(["RTC01"])["runs"][0]
            result = pilot.execute_case(
                spec,
                pilot_id="privacy-bad",
                adapter_config=fake_config("privacy-leak"),
                output_root=root,
            )
            self.assertEqual(result["disposition"], "INVALID")
            self.assertEqual(result["invalid_code"], "CAPTURE_PRIVACY_REJECTED")
            run_dir = root / "runs" / "privacy-bad-rtc01"
            self.assertTrue((run_dir / "invalid-run.json").is_file())
            self.assertFalse((run_dir / "capture.json").exists())

    def test_adapter_config_rejects_shell_or_unknown_fields(self) -> None:
        bad = fake_config()
        bad["shell"] = True
        with self.assertRaises(runtime_adapter.AdapterError) as caught:
            runtime_adapter.validate_config(bad)
        self.assertEqual(caught.exception.code, "ADAPTER_CONFIG_INVALID")

    def test_fake_receipt_never_builds_observed_behavior_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = pilot.build_plan(["RTC01"])["runs"][0]
            result = pilot.execute_case(
                spec,
                pilot_id="fake-observed",
                adapter_config=fake_config(),
                output_root=root,
            )
            receipt = json.loads(
                (
                    root
                    / "runs"
                    / result["run_id"]
                    / "receipt.json"
                ).read_text(encoding="utf-8")
            )
            self.assertFalse(receipt["proof"]["runtime_observed"])
            self.assertIsNone(pilot.build_observed_behavior_proof(receipt, subject=None))

    def test_observed_bridge_requires_runtime_evidence_and_exact_subject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = pilot.build_plan(["RTC01"])["runs"][0]
            result = pilot.execute_case(
                spec,
                pilot_id="bridge",
                adapter_config=fake_config(),
                output_root=root,
            )
            receipt = json.loads(
                (root / "runs" / result["run_id"] / "receipt.json").read_text(encoding="utf-8")
            )
            receipt["proof"]["runtime_observed"] = True
            with self.assertRaisesRegex(ValueError, "direct runtime evidence"):
                pilot.build_observed_behavior_proof(receipt, subject={})
            receipt["evidence"].append(
                {
                    "evidence_id": "EV-RUNTIME",
                    "kind": "runtime",
                    "ref": "runtime:external-observation",
                    "supports": "Direct external-agent runtime observation.",
                }
            )
            with self.assertRaisesRegex(ValueError, "exact observed-behavior subject"):
                pilot.build_observed_behavior_proof(receipt, subject=None)
            proof = pilot.build_observed_behavior_proof(
                receipt,
                subject={
                    "commit_sha": "0" * 40,
                    "artifact": {
                        "path": "Outputs/example.json",
                        "sha256": "0" * 64,
                    },
                },
            )
            self.assertEqual(proof["schema_version"], "observed-behavior-proof/v1")
            self.assertEqual(proof["evidence_class"], "target_runtime_observed")

    def test_plan_only_cli_semantics_remain_unproven_runtime(self) -> None:
        plan = pilot.build_plan(["RTC01"])
        self.assertEqual(plan["planned_runs"], 1)
        self.assertIn("Plan only", plan["proof_ceiling"])


if __name__ == "__main__":
    unittest.main()
