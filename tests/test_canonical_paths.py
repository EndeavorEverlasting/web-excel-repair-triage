from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_canonical_paths


class CanonicalPathContractTests(unittest.TestCase):
    def payload(self):
        return validate_canonical_paths.load_contract()

    def assert_invalid(self, payload, phrase: str) -> None:
        errors = validate_canonical_paths.validate_contract(payload)
        self.assertTrue(errors)
        self.assertIn(phrase, " | ".join(errors))

    def test_current_contract_passes(self) -> None:
        self.assertEqual(validate_canonical_paths.validate_contract(self.payload()), [])
        self.assertEqual(validate_canonical_paths.main([]), 0)

    def test_second_mutable_clone_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload())
        payload["policy"]["second_mutable_clone_allowed"] = True
        self.assert_invalid(payload, "second_mutable_clone_allowed")

    def test_hard_coded_person_path_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload())
        profile = next(
            item
            for item in payload["profiles"]
            if item["id"] == "repository-development"
        )
        profile["canonical_development_checkout"]["invented_path"] = (
            r"C:\Users\someone\Desktop\dev\web-excel-repair-triage"
        )
        self.assert_invalid(payload, "person-specific")

    def test_missing_production_use_path_declaration_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload())
        profile = next(item for item in payload["profiles"] if item["id"] == "public-web")
        del profile["production_use_path"]["applicable"]
        self.assert_invalid(payload, "production_use_path")

    def test_remote_main_cannot_promote_to_operator_observation(self) -> None:
        payload = copy.deepcopy(self.payload())
        state = payload["proof_states"][0]
        state["does_not_prove"].remove("operator_entrypoint_observes_current")
        self.assert_invalid(payload, "improperly promotes evidence")

    def test_p92_remains_deep_repair_owner(self) -> None:
        payload = copy.deepcopy(self.payload())
        payload["deep_repair_owner"]["prompt_id"] = "P00"
        self.assert_invalid(payload, "P92")


if __name__ == "__main__":
    unittest.main()
