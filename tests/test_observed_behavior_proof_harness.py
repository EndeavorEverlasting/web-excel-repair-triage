from __future__ import annotations
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("observed_proof_validator", ROOT / "scripts/validate_observed_behavior_receipt.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class ObservedBehaviorProofHarnessTests(unittest.TestCase):
    def base_receipt(self):
        artifact = ROOT / "web/prompt-kit/index.html"
        return {
            "schema_version": "observed-behavior-proof/v1",
            "verdict": "PASS",
            "evidence_class": "browser_runtime_observed",
            "subject": {
                "commit_sha": "1" * 40,
                "artifact": {
                    "path": "web/prompt-kit/index.html",
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                },
            },
            "claims": [
                {
                    "id": "ui",
                    "status": "PASS",
                    "required_evidence_class": "browser_runtime_observed",
                    "observation_ids": ["event"],
                }
            ],
            "observations": [{"id": "event", "occurred": True, "passed": True}],
        }

    def test_observed_pass_is_accepted(self):
        self.assertEqual(MOD.validate(self.base_receipt()), [])

    def test_pass_without_occurrence_fails_closed(self):
        receipt = self.base_receipt()
        receipt["observations"][0]["occurred"] = False
        self.assertTrue(any("did not occur" in e for e in MOD.validate(receipt)))

    def test_static_or_synthetic_evidence_cannot_be_promoted_to_runtime_pass(self):
        for evidence_class in ("source", "build", "synthetic"):
            receipt = self.base_receipt()
            receipt["evidence_class"] = evidence_class
            self.assertTrue(any("weaker" in e for e in MOD.validate(receipt)))

    def test_lower_observed_tier_cannot_satisfy_higher_required_tier(self):
        receipt = self.base_receipt()
        receipt["claims"][0]["required_evidence_class"] = "production_observed"
        self.assertTrue(any("requires production_observed" in e for e in MOD.validate(receipt)))

    def test_missing_artifact_is_rejected(self):
        receipt = self.base_receipt()
        receipt["subject"]["artifact"]["path"] = "does/not/exist.html"
        receipt["subject"]["artifact"]["sha256"] = "a" * 64
        self.assertTrue(any("artifact does not exist" in e for e in MOD.validate(receipt)))

    def test_non_pass_receipt_cannot_validate_as_success(self):
        for verdict in ("FAIL", "UNKNOWN", "UNPROVEN", None):
            receipt = self.base_receipt()
            receipt["verdict"] = verdict
            self.assertTrue(any("not PASS" in e for e in MOD.validate(receipt)))

    def test_prompt_owners_require_observed_outcome_gate(self):
        registry = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))
        diagnostic = next(p for p in registry["prompts"] if p["name"] == "Factuality vs Faithfulness Hallucination Diagnoser")
        for phrase in ("OBSERVED-OUTCOME CLAIM GATE", "UNKNOWN/UNPROVEN", "actual interaction", "clipboard"):
            self.assertIn(phrase, diagnostic["copyContent"])
        base = json.loads((ROOT / "docs/prompts.json").read_text(encoding="utf-8"))
        p08 = next(p for p in base if p["id"] == "P08")
        for phrase in ("OBSERVED OUTCOME BEFORE PASS", "runtime claim is UNKNOWN", "exact interaction sequence"):
            self.assertIn(phrase, p08["copyContent"])


if __name__ == "__main__":
    unittest.main()
