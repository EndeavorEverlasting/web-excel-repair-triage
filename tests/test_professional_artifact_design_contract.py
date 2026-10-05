import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_professional_artifact_design as validator


class ProfessionalArtifactDesignContractTests(unittest.TestCase):
    def test_full_contract_connected(self) -> None:
        result = validator.validate()
        self.assertEqual(result["state"], "PASS")
        self.assertEqual(result["owner"], "P01")
        self.assertGreaterEqual(result["principle_count"], 8)
        self.assertGreaterEqual(result["hard_failure_count"], 8)

    def test_p97_prior_art_is_evidence_typed_and_bounded(self) -> None:
        contract = validator.load_json(validator.CONTRACT)
        rows = {row["id"]: row for row in contract["upstream_prior_art"]}
        self.assertEqual(set(rows), validator.REQUIRED_UPSTREAM)
        for row in rows.values():
            self.assertEqual(row["evidence_state"], "OBSERVED_IMPLEMENTED")
            self.assertIn(row["disposition"], {"ADOPT", "ADAPT"})
            self.assertTrue(row["source"].startswith("https://"))

    def test_cinematic_prompt_seam_is_specific(self) -> None:
        draft = validator.load_json(validator.DRAFT)
        copy = draft["copyContent"]
        for phrase in validator.REQUIRED_PROMPT_PHRASES:
            self.assertIn(phrase, copy)
        self.assertLessEqual(len(copy), 12000)
        self.assertIn("palette is not a substitute for composition", copy.lower())

    def test_regressions_cover_each_scenario_independently(self) -> None:
        cases = validator.load_json(validator.CASES)["cases"]
        indexed = {row["id"]: row for row in cases}
        for case_id, terms in validator.REQUIRED_CASE_TERMS.items():
            self.assertIn(case_id, indexed)
            row_text = json.dumps(indexed[case_id], ensure_ascii=False).lower()
            for term in terms:
                self.assertIn(term.lower(), row_text, f"{case_id} missing {term}")

    def test_json_root_must_be_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(validator.ValidationError, "JSON object root"):
                validator.load_json(path)

    def test_copy_content_must_be_string(self) -> None:
        real = validator.load_json(validator.DRAFT)
        malformed = dict(real)
        malformed["copyContent"] = list(validator.REQUIRED_PROMPT_PHRASES)

        def fake_load(path):
            if path == validator.DRAFT:
                return malformed
            return validator.load_json(path)

        original = validator.load_json
        def routed(path):
            if path == validator.DRAFT:
                return malformed
            return original(path)

        with mock.patch.object(validator, "load_json", side_effect=routed):
            with self.assertRaisesRegex(validator.ValidationError, "copyContent must be"):
                validator.validate()

    def test_every_scene_contract_field_is_enforced(self) -> None:
        real = validator.load_json(validator.CONTRACT)
        for field in ("environment_or_metaphor", "density_budget"):
            broken = json.loads(json.dumps(real))
            del broken["presentation_cinematic"]["scene_contract"][field]
            original = validator.load_json

            def routed(path, broken=broken, original=original):
                if path == validator.CONTRACT:
                    return broken
                return original(path)

            with mock.patch.object(validator, "load_json", side_effect=routed):
                with self.assertRaisesRegex(validator.ValidationError, f"scene contract missing {field}"):
                    validator.validate()

    def test_contract_is_project_neutral(self) -> None:
        contract = validator.CONTRACT.read_text(encoding="utf-8")
        for term in validator.FORBIDDEN_PROJECT_TERMS:
            self.assertNotIn(term, contract)


if __name__ == "__main__":
    unittest.main()
