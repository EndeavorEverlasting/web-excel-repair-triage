import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_artifact_derivation_harness as guard


class ArtifactDerivationHarnessTests(unittest.TestCase):
    def test_static_harness_is_complete(self):
        self.assertEqual(guard.validate_static_harness()["status"], "PASS")

    def test_create_uses_existing_artifact_as_read_only_source(self):
        result = guard.validate_envelope(intent="create_new", sources=["path:Candidates/June_NTH.xlsx"], output="path:Outputs/June_NTH_candidate.xlsx")
        self.assertFalse(result["source_mutation_allowed"])
        self.assertEqual(result["source_policy"], "read_only_reference")

    def test_create_rejects_same_identity(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(intent="create_new", sources=["drive:SOURCE123"], output="drive:SOURCE123")

    def test_create_rejects_existing_output(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(intent="create_new", sources=["drive:SOURCE123"], output="path:Outputs/June_NTH_candidate.xlsx", output_exists=True)

    def test_protected_inputs_cannot_be_create_outputs(self):
        for target in ("path:Candidates/new.xlsx", "path:Active/new.xlsx"):
            with self.assertRaises(guard.ValidationError):
                guard.validate_envelope(intent="create_new", sources=[], output=target)

    def test_create_language_defaults_to_create_even_when_reference_is_current(self):
        self.assertEqual(guard.classify_intent("create a June Neuron Track Hours artifact using the current June workbook"), "create_new")
        self.assertEqual(guard.classify_intent("repair the current workbook"), "create_new")

    def test_update_requires_explicit_operator_intent(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(intent="update_existing", sources=["drive:SOURCE123"], output="drive:SOURCE123")
        result = guard.validate_envelope(intent="update_existing", sources=["drive:SOURCE123"], output="drive:SOURCE123", explicit_update=True)
        self.assertTrue(result["source_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
