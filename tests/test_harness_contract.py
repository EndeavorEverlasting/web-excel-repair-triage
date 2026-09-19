from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import evaluate_prompt_language
import validate_harness
import validate_operator_command_envelope
import validate_prompt_kit_cross_device_access


class HarnessContractTests(unittest.TestCase):
    def load(self, relative_path: str) -> dict:
        return json.loads(
            (ROOT / relative_path).read_text(encoding="utf-8")
        )

    def test_full_harness_validator_passes(self) -> None:
        self.assertEqual(validate_harness.main([]), 0)

    def test_harness_report_is_written_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "harness-report.json"
            self.assertEqual(
                validate_harness.main(["--report", str(report_path)]),
                0,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(
            report["schema_version"],
            "harness-completeness-report/v1",
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(report["checks"])
        self.assertTrue(
            all(item["status"] == "PASS" for item in report["checks"])
        )
        self.assertEqual(
            report["counts"]["components"],
            len(validate_harness.REQUIRED_COMPONENT_IDS),
        )
        self.assertEqual(
            report["counts"]["workflows"],
            len(validate_harness.REQUIRED_WORKFLOW_IDS),
        )
        self.assertEqual(
            report["counts"]["artifacts"],
            len(validate_harness.REQUIRED_ARTIFACT_IDS),
        )
        self.assertEqual(
            report["counts"]["validators"],
            len(validate_harness.REQUIRED_VALIDATOR_IDS),
        )

    def test_manifest_registers_every_required_harness_surface(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        self.assertEqual(
            manifest["schema_version"], "web-excel-harness/v1"
        )
        self.assertEqual(manifest["default_branch"], "main")
        self.assertEqual(
            set(manifest["components"]),
            validate_harness.REQUIRED_COMPONENT_IDS,
        )
        for path in manifest["components"].values():
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual(
            set(manifest["skills"]),
            {
                capability["skill"]
                for capability in self.load(
                    "harness/capabilities.v1.json"
                )["capabilities"]
            },
        )

    def test_cross_device_prompt_kit_access_is_registered_and_executable(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        contract = manifest["domain_contracts"]["prompt_kit_cross_device_access"]
        self.assertEqual(
            contract["contract"],
            "harness/contracts/prompt-kit-cross-device-access.v1.json",
        )
        self.assertEqual(
            contract["validator"],
            "scripts/validate_prompt_kit_cross_device_access.py",
        )
        self.assertEqual(
            contract["contract_tests"],
            "tests/test_prompt_kit_cross_device_access.py",
        )
        self.assertEqual(
            contract["harness_gate"],
            "python scripts/validate_prompt_kit_cross_device_access.py --summary",
        )
        self.assertEqual(validate_prompt_kit_cross_device_access.main([]), 0)

    def test_operator_command_envelope_is_registered_and_executable(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        contract = manifest["domain_contracts"]["operator_command_envelope"]
        self.assertEqual(
            contract["contract"],
            "harness/contracts/operator-command-envelope.v1.json",
        )
        self.assertEqual(
            contract["validator"],
            "scripts/validate_operator_command_envelope.py",
        )
        self.assertEqual(
            contract["contract_tests"],
            "tests/test_operator_command_envelope.py",
        )
        self.assertEqual(
            contract["template"],
            "harness/templates/Invoke-RemoteHarnessProof.ps1",
        )
        self.assertEqual(validate_operator_command_envelope.main([]), 0)

    def test_machine_registries_are_complete_and_connected(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        workflows = self.load("harness/workflows.v1.json")
        artifacts = self.load("harness/artifacts.v1.json")
        validators = self.load("harness/validators.v1.json")

        self.assertEqual(
            {item["id"] for item in workflows["workflows"]},
            validate_harness.REQUIRED_WORKFLOW_IDS,
        )
        self.assertEqual(
            {item["id"] for item in artifacts["artifacts"]},
            validate_harness.REQUIRED_ARTIFACT_IDS,
        )
        validator_by_id = {
            item["id"]: item for item in validators["validators"]
        }
        self.assertEqual(
            set(validator_by_id),
            validate_harness.REQUIRED_VALIDATOR_IDS,
        )
        self.assertEqual(
            [
                validator_by_id[validator_id]["command"]
                for validator_id in validators["profiles"]["harness"]
            ],
            manifest["validation_order"],
        )
        self.assertEqual(
            validators["profiles"]["pre_push"],
            validators["profiles"]["harness"],
        )

    def test_workflows_have_scope_failure_and_handoff_contracts(self) -> None:
        workflows = self.load("harness/workflows.v1.json")["workflows"]
        for workflow in workflows:
            self.assertTrue(workflow["document"].startswith("WORKFLOW.md#"))
            self.assertTrue(workflow["trigger"])
            self.assertTrue(workflow["owned_scope"])
            self.assertTrue(workflow["forbidden_scope"])
            self.assertTrue(workflow["entry_points"])
            self.assertTrue(workflow["failure_policy"])
            self.assertTrue(workflow["handoff_fields"])

    def test_artifact_registry_protects_inputs_and_resolves_outputs(self) -> None:
        payload = self.load("harness/artifacts.v1.json")
        self.assertEqual(
            payload["protected_paths"], ["Candidates/", "Active/"]
        )
        kinds = {artifact["kind"] for artifact in payload["artifacts"]}
        self.assertEqual(kinds, {"tracked", "runtime"})
        for artifact in payload["artifacts"]:
            path = artifact["canonical_path"]
            self.assertFalse(path.startswith("Candidates/"))
            self.assertFalse(path.startswith("Active/"))
            if artifact["kind"] == "runtime":
                self.assertTrue(path.startswith("Outputs/"))

    def test_prompt_kit_artifact_registers_cross_device_delivery_surfaces(self) -> None:
        artifacts = self.load("harness/artifacts.v1.json")["artifacts"]
        site = next(item for item in artifacts if item["id"] == "prompt-kit-website")
        self.assertIn(
            "https://endeavoreverlasting.github.io/web-excel-repair-triage/afk-agent-flow/",
            site["delivery_surfaces"],
        )
        self.assertIn(
            "https://endeavoreverlasting.github.io/web-excel-repair-triage/",
            site["delivery_surfaces"],
        )
        self.assertIn("Open-Latest-PromptKit.cmd", site["delivery_surfaces"])

    def test_capabilities_and_triggers_have_unique_connected_owners(self) -> None:
        capabilities = self.load(
            "harness/capabilities.v1.json"
        )["capabilities"]
        triggers = self.load("harness/triggers.v1.json")["triggers"]
        capability_by_id = {item["id"]: item for item in capabilities}
        self.assertEqual(
            set(capability_by_id),
            validate_harness.REQUIRED_CAPABILITY_IDS,
        )
        self.assertEqual(
            {item["id"] for item in triggers},
            validate_harness.REQUIRED_TRIGGER_IDS,
        )
        for trigger in triggers:
            capability = capability_by_id[trigger["capability_id"]]
            self.assertEqual(trigger["skill"], capability["skill"])
            self.assertIn(trigger["id"], capability["trigger_ids"])

    def test_every_active_skill_is_indexed_and_structured(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        index = (ROOT / "SKILLS.md").read_text(encoding="utf-8")
        for skill_path in manifest["skills"]:
            self.assertIn(skill_path, index)
            skill = (ROOT / skill_path).read_text(encoding="utf-8")
            for section in validate_harness.REQUIRED_SKILL_SECTIONS:
                self.assertIn(section, skill)

    def test_prompt_language_audit_covers_every_effective_prompt(self) -> None:
        report = evaluate_prompt_language.evaluate_registry()
        self.assertTrue(report["coverage_complete"])
        self.assertEqual(
            report["prompt_count"], report["effective_prompt_count"]
        )
        self.assertEqual(
            report["prompt_count"], report["disposition_count"]
        )
        self.assertEqual(report["error_count"], 0)
        self.assertIn(
            "P62", {item["prompt_id"] for item in report["prompts"]}
        )

    def test_acquisition_contract_is_preservation_first(self) -> None:
        manifest = self.load("harness/manifest.v1.json")
        safety = manifest["technician_acquisition"]["safety"]
        self.assertTrue(safety["clone_when_absent"])
        self.assertTrue(safety["fast_forward_only"])
        self.assertTrue(safety["refuse_dirty_worktree"])
        self.assertTrue(safety["refuse_divergence"])
        self.assertFalse(safety["force_push"])
        self.assertFalse(safety["destructive_reset"])
        self.assertFalse(safety["embedded_credentials"])


    def test_execution_boundary_use_case_routes_intent_first(self) -> None:
        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]
        triggers = self.load("harness/triggers.v1.json")["triggers"]
        workflows = self.load("harness/workflows.v1.json")["workflows"]
        validators = {
            item["id"]
            for item in self.load("harness/validators.v1.json")["validators"]
        }
        intent = "agents stop at arbitrary boundaries instead of continuing"

        matches = []
        for capability in capabilities:
            for use_case in capability.get("use_cases", []):
                aliases = {
                    str(alias).casefold()
                    for alias in use_case.get("intent_aliases", [])
                }
                if intent.casefold() in aliases:
                    matches.append((capability, use_case))

        self.assertEqual(len(matches), 1)
        capability, use_case = matches[0]
        self.assertEqual(capability["id"], "harness-infrastructure-maintenance")
        self.assertEqual(use_case["id"], "execution-boundary-continuation")

        trigger = next(
            item
            for item in triggers
            if item["id"] == use_case["primary_trigger_id"]
        )
        self.assertEqual(trigger["capability_id"], capability["id"])
        self.assertIn(intent, trigger["intent_aliases"])

        workflow = next(
            item for item in workflows if item["id"] == use_case["workflow_id"]
        )
        self.assertEqual(trigger["workflow"], workflow["document"])
        self.assertIn(capability["id"], workflow["capability_ids"])
        self.assertIn(use_case["id"], workflow["use_case_ids"])
        self.assertEqual(trigger["skill"], capability["skill"])
        self.assertEqual(use_case["skill"], capability["skill"])

        participants = {
            item["role"]: item["path"] for item in use_case["participants"]
        }
        for role in (
            "contract",
            "taxonomy",
            "prompt-semantics",
            "implementation",
            "shared-policy",
            "evidence-artifact",
            "validator",
            "regression-test",
        ):
            self.assertIn(role, participants)
            self.assertTrue((ROOT / participants[role]).is_file(), participants[role])

        self.assertIn(
            "harness/evals/execution-boundaries/boundary-regression-matrix.v1.json",
            use_case["expected_artifacts"],
        )
        self.assertTrue(set(use_case["validator_ids"]).issubset(validators))

    def test_execution_boundary_use_case_routes_implementation_first(self) -> None:
        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]
        resource = "scripts/execution_boundary_engine.py"

        owners = []
        for capability in capabilities:
            for use_case in capability.get("use_cases", []):
                participant_paths = {
                    item["path"] for item in use_case.get("participants", [])
                }
                if resource in participant_paths:
                    owners.append((capability, use_case))

        self.assertEqual(len(owners), 1)
        capability, use_case = owners[0]
        self.assertEqual(capability["id"], "harness-infrastructure-maintenance")
        self.assertEqual(use_case["primary_trigger_id"], "harness-infrastructure-change")
        self.assertIn(
            "Agents stop at material or arbitrary boundaries",
            use_case["originating_user_intent"],
        )

        related_paths = {
            item["path"] for item in use_case["participants"]
        }
        for path in (
            "harness/contracts/execution-boundary-enforcement.v1.json",
            "harness/prompt-compilation/semantics/P07.json",
            "registry/prompts/actionable-next-step-policy.v1.json",
            "harness/evals/execution-boundaries/boundary-regression-matrix.v1.json",
            "scripts/validate_execution_boundary_enforcement.py",
            "tests/test_execution_boundary_enforcement_prompt.py",
        ):
            self.assertIn(path, related_paths)

        for human_route in (
            "harness/CONTEXT.md",
            "CODEBASE_MAP.md",
            "CAPABILITIES.md",
            "TRIGGERS.md",
            "WORKFLOW.md",
        ):
            self.assertIn(
                "execution-boundary-continuation",
                (ROOT / human_route).read_text(encoding="utf-8"),
                human_route,
            )


    def test_runtime_compliance_use_case_routes_intent_first(self) -> None:
        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]
        triggers = self.load("harness/triggers.v1.json")["triggers"]
        workflows = self.load("harness/workflows.v1.json")["workflows"]
        artifacts = {
            item["id"]: item
            for item in self.load("harness/artifacts.v1.json")["artifacts"]
        }
        validators = {
            item["id"]
            for item in self.load("harness/validators.v1.json")["validators"]
        }
        intent = "prompt strengthening sprint"

        matches = []
        for capability in capabilities:
            for use_case in capability.get("use_cases", []):
                aliases = {
                    str(alias).casefold()
                    for alias in use_case.get("intent_aliases", [])
                }
                if intent.casefold() in aliases:
                    matches.append((capability, use_case))

        self.assertEqual(len(matches), 1)
        capability, use_case = matches[0]
        self.assertEqual(capability["id"], "skill-evaluation")
        self.assertEqual(use_case["id"], "prompt-strengthening-runtime-compliance")

        trigger = next(
            item
            for item in triggers
            if item["id"] == use_case["primary_trigger_id"]
        )
        workflow = next(
            item for item in workflows if item["id"] == use_case["workflow_id"]
        )
        self.assertEqual(trigger["capability_id"], capability["id"])
        self.assertIn(intent, trigger["intent_aliases"])
        self.assertIn(use_case["id"], trigger["use_case_ids"])
        self.assertEqual(trigger["workflow"], workflow["document"])
        self.assertIn(capability["id"], workflow["capability_ids"])
        self.assertIn(use_case["id"], workflow["use_case_ids"])

        participant_paths = {
            item["path"] for item in use_case["participants"]
        }
        for path in (
            "harness/evals/PROMPT_RUNTIME_COMPLIANCE_PILOT_PLAN.md",
            "harness/evals/runtime-compliance/scripts/pilot.py",
            "scripts/validate_prompt_runtime_compliance_receipt.py",
        ):
            self.assertIn(path, participant_paths)
            self.assertIn(path, workflow["entry_points"])

        self.assertEqual(use_case["artifact_ids"], ["prompt-runtime-compliance-evidence"])
        artifact = artifacts["prompt-runtime-compliance-evidence"]
        self.assertEqual(
            artifact["primary_artifact"],
            "Outputs/repository-ai-evals/runtime-compliance/pilot-receipt.json",
        )
        self.assertEqual(
            artifact["schema"],
            "prompt-runtime-compliance-pilot-receipt/v1",
        )
        self.assertEqual(
            artifact["schema_owner"],
            "harness/evals/runtime-compliance/scripts/pilot.py",
        )
        self.assertIn(artifact["validator"], use_case["validator_ids"])
        self.assertTrue(set(use_case["validator_ids"]).issubset(validators))
        validator_registry = self.load("harness/validators.v1.json")
        self.assertIn(
            "prompt-runtime-compliance-receipt-audit",
            validator_registry["profiles"]["required_checks"],
        )
        self.assertEqual(workflow["validation_profile"], "required_checks")
        self.assertTrue(
            set(use_case["validator_ids"]).issubset(
                set(validator_registry["profiles"][workflow["validation_profile"]])
            )
        )

    def test_runtime_compliance_use_case_routes_implementation_first(self) -> None:
        capabilities = self.load("harness/capabilities.v1.json")["capabilities"]

        for resource in (
            "harness/evals/runtime-compliance/scripts/pilot.py",
            "scripts/validate_prompt_runtime_compliance_receipt.py",
        ):
            owners = []
            for capability in capabilities:
                for use_case in capability.get("use_cases", []):
                    participant_paths = {
                        item["path"] for item in use_case.get("participants", [])
                    }
                    if resource in participant_paths:
                        owners.append((capability, use_case))

            self.assertEqual(len(owners), 1, resource)
            capability, use_case = owners[0]
            self.assertEqual(capability["id"], "skill-evaluation")
            self.assertEqual(
                use_case["id"],
                "prompt-strengthening-runtime-compliance",
            )
            self.assertEqual(
                use_case["primary_trigger_id"],
                "skill-quality-unproven",
            )
            self.assertIn(
                "Strengthen Prompt Kit execution behavior",
                use_case["originating_user_intent"],
            )
            self.assertEqual(
                use_case["validator_ids"],
                ["prompt-runtime-compliance-receipt-audit"],
            )

    def test_prompt_language_mutation_precedes_runtime_proof(self) -> None:
        triggers = self.load("harness/triggers.v1.json")["triggers"]
        proof_trigger = next(
            item for item in triggers if item["id"] == "skill-quality-unproven"
        )
        language_trigger = next(
            item for item in triggers if item["id"] == "prompt-language-change"
        )
        exclusion = (
            "canonical prompt wording or shared policy still needs mutation before an "
            "evaluable strengthened candidate exists; route prompt-language-change first, "
            "then return for runtime proof"
        )
        self.assertIn(exclusion, proof_trigger["forbidden_conditions"])
        self.assertEqual(language_trigger["capability_id"], "prompt-language-audit")
        self.assertEqual(proof_trigger["capability_id"], "skill-evaluation")

    def test_workflow_validation_profiles_resolve(self) -> None:
        workflows = self.load("harness/workflows.v1.json")["workflows"]
        profiles = self.load("harness/validators.v1.json")["profiles"]
        for workflow in workflows:
            with self.subTest(workflow=workflow["id"]):
                self.assertIn(workflow["validation_profile"], profiles)

    def test_hooks_use_registered_profiles_and_staged_tree(self) -> None:
        validators = self.load("harness/validators.v1.json")
        self.assertEqual(
            validators["hooks"]["pre_commit"]["index_mode"],
            "staged-tree",
        )
        self.assertEqual(
            validators["hooks"]["pre_commit"]["profile"],
            validate_harness.PRE_COMMIT_SNAPSHOT_PROFILE,
        )
        self.assertEqual(
            validators["profiles"][validate_harness.PRE_COMMIT_SNAPSHOT_PROFILE],
            list(validate_harness.PRE_COMMIT_SNAPSHOT_VALIDATOR_IDS),
        )
        self.assertEqual(
            validators["profiles"]["pre_commit"],
            ["staged-artifact-hygiene"]
            + list(validate_harness.PRE_COMMIT_SNAPSHOT_VALIDATOR_IDS)
            + ["patch-hygiene-staged"],
        )
        pre_commit = (ROOT / ".githooks" / "pre-commit").read_text(
            encoding="utf-8"
        )
        for phrase in (
            validate_harness.PRE_COMMIT_ADAPTER_GATES[0],
            "git checkout-index --all --prefix=",
            'cd "$staged_tree"',
            validate_harness.PRE_COMMIT_PROFILE_RUNNER,
            validate_harness.PRE_COMMIT_PROFILE_REPORT,
            validate_harness.PRE_COMMIT_ADAPTER_GATES[1],
        ):
            self.assertIn(phrase, pre_commit)
        self.assertLess(
            pre_commit.index(validate_harness.PRE_COMMIT_ADAPTER_GATES[0]),
            pre_commit.index("git checkout-index --all --prefix="),
        )
        self.assertLess(
            pre_commit.index(validate_harness.PRE_COMMIT_PROFILE_RUNNER),
            pre_commit.index(validate_harness.PRE_COMMIT_ADAPTER_GATES[1]),
        )

        self.assertEqual(
            validators["hooks"]["pre_push"]["profile"],
            "pre_push",
        )
        self.assertEqual(
            validators["hooks"]["pre_push"]["index_mode"],
            "working-tree",
        )
        pre_push = (ROOT / ".githooks" / "pre-push").read_text(
            encoding="utf-8"
        )
        for command in validate_harness.PRE_PUSH_PRESERVED_COMMANDS:
            self.assertIn(command, pre_push)

        self.assertIn(validate_harness.PRE_PUSH_PROFILE_RUNNER, pre_push)
        self.assertIn(validate_harness.PRE_PUSH_PROFILE_REPORT, pre_push)

        validator_by_id = {
            item["id"]: item for item in validators["validators"]
        }
        for profile_name, hook_text in (
            (validate_harness.PRE_COMMIT_SNAPSHOT_PROFILE, pre_commit),
            ("pre_push", pre_push),
        ):
            for validator_id in validators["profiles"][profile_name]:
                self.assertNotIn(
                    validator_by_id[validator_id]["command"],
                    hook_text,
                    f"registered {profile_name} validator duplicated in hook: {validator_id}",
                )

    def test_tracked_file_probe_is_bounded_noninteractive_and_byte_mode(self) -> None:
        fake = SimpleNamespace(
            returncode=0,
            stdout=b"harness/manifest.v1.json\0scripts/validate_harness.py\0",
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake_root = Path(temporary)
            (fake_root / ".git").mkdir()
            with mock.patch.object(
                validate_harness, "ROOT", fake_root
            ), mock.patch.object(
                validate_harness, "_TRACKED_PATHS_CACHE", None
            ), mock.patch.object(
                validate_harness.subprocess, "run", return_value=fake
            ) as run:
                validate_harness.require_tracked("harness/manifest.v1.json")
                args, kwargs = run.call_args
                self.assertEqual(args[0], ["git", "ls-files", "-z"])
                self.assertEqual(kwargs["cwd"], validate_harness.ROOT)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(kwargs["stdout"], subprocess.PIPE)
        self.assertIs(kwargs["stderr"], subprocess.DEVNULL)
        self.assertFalse(kwargs["check"])
        self.assertEqual(
            kwargs["timeout"], validate_harness.GIT_PROBE_TIMEOUT_SECONDS
        )
        self.assertNotIn("text", kwargs)
        self.assertNotIn("encoding", kwargs)

    def test_tracked_file_probe_timeout_fails_closed(self) -> None:
        timeout = subprocess.TimeoutExpired(
            cmd=["git", "ls-files", "-z"],
            timeout=validate_harness.GIT_PROBE_TIMEOUT_SECONDS,
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake_root = Path(temporary)
            (fake_root / ".git").mkdir()
            with mock.patch.object(
                validate_harness, "ROOT", fake_root
            ), mock.patch.object(
                validate_harness, "_TRACKED_PATHS_CACHE", None
            ), mock.patch.object(
                validate_harness.subprocess, "run", side_effect=timeout
            ):
                with self.assertRaisesRegex(
                    validate_harness.HarnessValidationError,
                    "timed out",
                ):
                    validate_harness.require_tracked(
                        "harness/manifest.v1.json"
                    )

    def test_repository_local_report_must_use_outputs(self) -> None:
        with self.assertRaisesRegex(
            validate_harness.HarnessValidationError,
            "must be written under Outputs",
        ):
            validate_harness._resolve_report_target(
                Path("harness/reports/runtime.json")
            )
        target = validate_harness._resolve_report_target(
            Path("Outputs/harness-completeness-report.json")
        )
        self.assertEqual(
            target,
            (
                validate_harness.ROOT
                / "Outputs"
                / "harness-completeness-report.json"
            ).resolve(),
        )


if __name__ == "__main__":
    unittest.main()
