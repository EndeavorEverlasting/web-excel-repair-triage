from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_lua_harness


class LuaHarnessContractTests(unittest.TestCase):
    def load(self, relative_path: str) -> dict:
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def test_current_repository_lua_harness_passes(self) -> None:
        validate_lua_harness.validate_repository()
        self.assertEqual(validate_lua_harness.main(["--summary"]), 0)

    def test_contract_keeps_host_in_control(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        architecture = contract["architecture"]
        self.assertEqual(architecture["embedding_model"], "language-as-library")
        self.assertTrue(architecture["host_owns_main_loop"])
        self.assertFalse(architecture["script_owns_main_loop"])
        self.assertEqual(architecture["performance_critical_code_owner"], "host")
        self.assertEqual(architecture["dynamic_logic_owner"], "lua")

    def test_contract_requires_isolated_states_and_host_error_cleanup(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        self.assertTrue(contract["state_isolation"]["independent_vm_states"])
        self.assertTrue(contract["state_isolation"]["state_destroy_isolated"])
        self.assertTrue(contract["state_isolation"]["explicit_release_required"])
        self.assertTrue(contract["error_handling"]["host_catches_script_errors"])
        self.assertTrue(contract["error_handling"]["host_owns_rollback"])
        self.assertTrue(contract["error_handling"]["cleanup_on_error"])

    def test_contract_is_default_deny_and_allow_listed(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        sandbox = contract["sandbox"]
        self.assertFalse(sandbox["default_os_library"])
        self.assertFalse(sandbox["default_io_library"])
        self.assertFalse(sandbox["default_native_module_loading"])
        self.assertEqual(sandbox["host_api_policy"], "allow-list")
        self.assertTrue(sandbox["expose_only_required_host_functions"])

    def test_contract_preserves_minimal_execution_and_type_discipline(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        execution = contract["execution"]
        self.assertTrue(execution["precompiled_bytecode_allowed"])
        self.assertTrue(execution["small_interpreter_dispatch_preferred"])
        self.assertFalse(execution["jit_required"])
        self.assertTrue(execution["deoptimization_requires_reconstructible_state"])
        self.assertTrue(contract["type_system"]["runtime_type_checks"])
        self.assertTrue(contract["type_system"]["internal_type_discipline_required"])
        self.assertEqual(contract["design_philosophy"]["indexing"], "lua-1-based")
        self.assertTrue(contract["ai_auditability"]["human_auditable_generated_code"])
        self.assertTrue(contract["ai_auditability"]["hidden_mechanisms_forbidden"])

    def test_unsafe_os_library_mutation_fails_closed(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        mutated = copy.deepcopy(contract)
        mutated["sandbox"]["default_os_library"] = True
        with self.assertRaisesRegex(
            validate_lua_harness.LuaHarnessValidationError,
            "sandbox",
        ):
            validate_lua_harness.validate_contract_payload(mutated)

    def test_script_owned_main_loop_mutation_fails_closed(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        mutated = copy.deepcopy(contract)
        mutated["architecture"]["host_owns_main_loop"] = False
        mutated["architecture"]["script_owns_main_loop"] = True
        with self.assertRaisesRegex(
            validate_lua_harness.LuaHarnessValidationError,
            "architecture",
        ):
            validate_lua_harness.validate_contract_payload(mutated)

    def test_jit_cannot_become_mandatory_by_registry_drift(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        mutated = copy.deepcopy(contract)
        mutated["execution"]["jit_required"] = True
        with self.assertRaisesRegex(
            validate_lua_harness.LuaHarnessValidationError,
            "execution",
        ):
            validate_lua_harness.validate_contract_payload(mutated)

    def test_harness_does_not_claim_product_runtime(self) -> None:
        contract = self.load("harness/lua/contracts/lua-embedding-readiness.v1.json")
        mutated = copy.deepcopy(contract)
        mutated["runtime_status"] = "implemented"
        with self.assertRaisesRegex(
            validate_lua_harness.LuaHarnessValidationError,
            "must not claim",
        ):
            validate_lua_harness.validate_contract_payload(mutated)

    def test_machine_registries_have_single_owner(self) -> None:
        capability = self.load("harness/lua/capabilities.v1.json")["capabilities"][0]
        trigger = self.load("harness/lua/triggers.v1.json")["triggers"][0]
        self.assertEqual(capability["id"], "lua-embedding-readiness")
        self.assertEqual(capability["trigger_ids"], [trigger["id"]])
        self.assertEqual(trigger["capability_id"], capability["id"])
        self.assertEqual(trigger["skill"], capability["skill"])

    def test_report_is_machine_readable_and_keeps_runtime_unimplemented(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "lua-readiness.json"
            self.assertEqual(
                validate_lua_harness.main(["--output", str(report_path), "--summary"]),
                0,
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], "lua-embedding-readiness-report/v1")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["runtime_status"], "not_implemented")
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(all(item["status"] == "PASS" for item in report["checks"]))

    def test_repository_local_report_must_live_under_outputs(self) -> None:
        with self.assertRaisesRegex(
            validate_lua_harness.LuaHarnessValidationError,
            "under Outputs",
        ):
            validate_lua_harness.resolve_report_target(Path("harness/lua/runtime.json"))
        target = validate_lua_harness.resolve_report_target(
            Path("Outputs/lua-embedding-readiness.json")
        )
        self.assertEqual(target, (ROOT / "Outputs" / "lua-embedding-readiness.json").resolve())


if __name__ == "__main__":
    unittest.main()
