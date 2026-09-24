import tempfile
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
        result = guard.validate_envelope(
            intent="create_new",
            sources=["path:Candidates/June_NTH.xlsx"],
            output="path:Outputs/June_NTH_candidate.xlsx",
        )
        self.assertFalse(result["source_mutation_allowed"])
        self.assertEqual(result["source_policy"], "read_only_reference")

    def test_create_rejects_same_remote_identity_before_existence_probe(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(
                intent="create_new",
                sources=["drive:SOURCE123"],
                output="drive:SOURCE123",
            )

    def test_path_aliases_canonicalize_to_same_identity(self):
        self.assertEqual(
            guard.normalize_identity("path:Outputs/candidate.xlsx"),
            guard.normalize_identity("path:Outputs/a/../candidate.xlsx"),
        )

    def test_traversal_cannot_bypass_protected_input_or_collision(self):
        for target in (
            "path:Outputs/../Candidates/source.xlsx",
            "repo:Outputs/../Active/source.xlsx",
        ):
            with self.assertRaises(guard.ValidationError):
                guard.validate_envelope(
                    intent="create_new",
                    sources=["path:Candidates/source.xlsx"],
                    output=target,
                )

    def test_create_detects_existing_local_output_without_caller_flag(self):
        outputs = ROOT / "Outputs"
        outputs.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="artifact-derivation-existing-",
            suffix=".xlsx",
            dir=outputs,
            delete=False,
        ) as handle:
            target = Path(handle.name)
        try:
            with self.assertRaises(guard.ValidationError):
                guard.validate_envelope(
                    intent="create_new",
                    sources=[],
                    output=f"path:{target}",
                )
        finally:
            target.unlink(missing_ok=True)

    def test_remote_create_requires_explicit_provider_existence_result(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(
                intent="create_new",
                sources=["drive:SOURCE123"],
                output="drive:PROSPECTIVE456",
            )
        result = guard.validate_envelope(
            intent="create_new",
            sources=["drive:SOURCE123"],
            output="drive:PROSPECTIVE456",
            output_exists=False,
        )
        self.assertFalse(result["source_mutation_allowed"])

    def test_caller_cannot_lie_about_local_output_existence(self):
        outputs = ROOT / "Outputs"
        outputs.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="artifact-derivation-existing-",
            suffix=".xlsx",
            dir=outputs,
            delete=False,
        ) as handle:
            target = Path(handle.name)
        try:
            with self.assertRaises(guard.ValidationError):
                guard.validate_envelope(
                    intent="create_new",
                    sources=[],
                    output=f"path:{target}",
                    output_exists=False,
                )
        finally:
            target.unlink(missing_ok=True)

    def test_protected_inputs_cannot_be_create_outputs(self):
        for target in ("path:Candidates/new.xlsx", "path:Active/new.xlsx"):
            with self.assertRaises(guard.ValidationError):
                guard.validate_envelope(intent="create_new", sources=[], output=target)

    def test_create_language_defaults_to_create_even_when_reference_is_current(self):
        self.assertEqual(
            guard.classify_intent(
                "create a June Neuron Track Hours artifact using the current June workbook"
            ),
            "create_new",
        )
        self.assertEqual(
            guard.classify_intent("repair the current workbook"), "create_new"
        )

    def test_negated_or_mixed_update_language_cannot_authorize_mutation(self):
        for text in (
            "do not repair this workbook",
            "never overwrite the current workbook",
            "create a new workbook; do not update the current one",
            "build a derivative by updating the reference",
        ):
            self.assertEqual(
                guard.classify_intent(text, explicit_update=True), "create_new"
            )

    def test_explicit_unambiguous_update_can_be_classified(self):
        self.assertEqual(
            guard.classify_intent(
                "update the current workbook in place", explicit_update=True
            ),
            "update_existing",
        )

    def test_update_requires_explicit_operator_intent(self):
        with self.assertRaises(guard.ValidationError):
            guard.validate_envelope(
                intent="update_existing",
                sources=["drive:SOURCE123"],
                output="drive:SOURCE123",
            )
        result = guard.validate_envelope(
            intent="update_existing",
            sources=["drive:SOURCE123"],
            output="drive:SOURCE123",
            explicit_update=True,
        )
        self.assertTrue(result["source_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()
