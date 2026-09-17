from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import validate_prompt_retrospective_evaluations as retrospective

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-retrospective-evaluation.v1.json"
REGISTER = ROOT / "harness" / "evals" / "prompt-retrospective" / "recent-candidates.v1.json"


class PromptRetrospectiveEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.register = json.loads(REGISTER.read_text(encoding="utf-8"))
        retrospective.validate_contract(cls.contract)

    def test_current_register_passes(self) -> None:
        summary = retrospective.validate_register(copy.deepcopy(self.register), self.contract)
        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["unresolved_authorship"], 3)
        self.assertEqual(summary["priority_policy"], "UNCOMPUTED_UNTIL_WEIGHTING_APPROVED")

    def test_current_p00_match_does_not_retroactively_prove_authorship(self) -> None:
        record = self.register["records"][0]
        self.assertEqual(record["prompt_anchor"], "INSTALL GOVERNANCE DOCTRINE NOW")
        self.assertEqual(record["kit_assessment"]["matched_prompt_ids"], ["P00"])
        self.assertEqual(record["ratings"]["prompt_kit_gap"]["score"], 1)
        self.assertIsNone(record["ratings"]["authorship_origin"]["score"])
        self.assertEqual(record["ratings"]["authorship_origin"]["confidence"], "NONE")
        self.assertEqual(record["authorship_profile"]["comparison_basis"], "CURRENT_ONLY")
        self.assertEqual(
            record["authorship_profile"]["historical_origin_status"],
            "NEEDS_CONTEMPORANEOUS_KIT_REF",
        )

    def test_hybrid_authorship_is_first_class(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["evidence"].append({
            "id": "ev-hybrid",
            "kind": "historical_registry",
            "ref": "synthetic:historical-kit@abc123#P79",
            "supports": ["authorship_origin"],
            "summary": "Synthetic fixture proves both canonical doctrine and manual additions.",
        })
        record["ratings"]["authorship_origin"] = {
            "score": 3,
            "confidence": "MEDIUM",
            "rationale": "Canonical doctrine and manually authored constraints both materially shape the prompt.",
            "evidence_refs": ["ev-hybrid"],
        }
        record["authorship_profile"].update({
            "origin_label": "HYBRID",
            "comparison_basis": "MIXED",
            "contemporaneous_prompt_kit_ref": "synthetic-kit@abc123",
            "matched_prompt_ids": ["P79"],
            "match_kind": "DOCTRINE_ONLY",
            "manual_novelty_signals": ["synthetic manual constraint"],
        })
        summary = retrospective.validate_register(register, self.contract)
        self.assertEqual(summary["status"], "PASS")

    def test_hybrid_requires_canonical_and_manual_evidence(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["ratings"]["authorship_origin"] = {
            "score": 3,
            "confidence": "LOW",
            "rationale": "Attempt to classify hybrid without a matched canonical owner.",
            "evidence_refs": ["ev-p03-historical"],
        }
        record["authorship_profile"].update({
            "origin_label": "HYBRID",
            "matched_prompt_ids": [],
            "match_kind": "DOCTRINE_ONLY",
            "manual_novelty_signals": ["synthetic manual constraint"],
        })
        with self.assertRaisesRegex(retrospective.RetrospectiveValidationError, "matched Prompt Kit ID"):
            retrospective.validate_register(register, self.contract)

    def test_manual_original_requires_contemporaneous_no_match_proof(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["evidence"].append({
            "id": "ev-manual",
            "kind": "conversation_anchor",
            "ref": "synthetic:prompt-event",
            "supports": ["authorship_origin"],
            "summary": "Synthetic prompt-event evidence.",
        })
        record["ratings"]["authorship_origin"] = {
            "score": 5,
            "confidence": "LOW",
            "rationale": "Synthetic attempt to claim manual origin without contemporaneous no-match proof.",
            "evidence_refs": ["ev-manual"],
        }
        record["authorship_profile"]["origin_label"] = "MANUAL_ORIGINAL"
        record["authorship_profile"]["manual_novelty_signals"] = ["synthetic manual structure"]
        # Retained matched Prompt Kit IDs fail closed before the no-match proof gate.
        with self.assertRaisesRegex(
            retrospective.RetrospectiveValidationError,
            "MANUAL_ORIGINAL cannot retain matched Prompt Kit IDs",
        ):
            retrospective.validate_register(register, self.contract)

    def test_gap_five_requires_completed_topology_review(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["evidence"].append({
            "id": "ev-gap",
            "kind": "topology",
            "ref": "synthetic:topology-review",
            "supports": ["prompt_kit_gap"],
            "summary": "Synthetic topology evidence that is still incomplete for create-new.",
        })
        record["ratings"]["prompt_kit_gap"] = {
            "score": 5,
            "confidence": "MEDIUM",
            "rationale": "Synthetic gap claim without completed prior-art or topology evidence.",
            "evidence_refs": ["ev-gap"],
        }
        record["kit_assessment"]["disposition"] = "CREATE_NEW_REVIEW"
        record["kit_assessment"]["prior_art_complete"] = False
        record["kit_assessment"]["topology_ref"] = None
        with self.assertRaisesRegex(retrospective.RetrospectiveValidationError, "completed prior-art/topology review"):
            retrospective.validate_register(register, self.contract)

    def test_gap_one_requires_current_basis(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["kit_assessment"]["evaluation_basis"] = "CONTEMPORANEOUS"
        with self.assertRaisesRegex(retrospective.RetrospectiveValidationError, "CURRENT evaluation basis"):
            retrospective.validate_register(register, self.contract)

    def test_scored_rating_requires_evidence(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["ratings"]["productivity"] = {
            "score": 5,
            "confidence": "HIGH",
            "rationale": "Unsupported productivity score.",
            "evidence_refs": [],
        }
        with self.assertRaisesRegex(retrospective.RetrospectiveValidationError, "requires evidence"):
            retrospective.validate_register(register, self.contract)

    def test_scored_rating_rejects_cross_dimension_evidence(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["ratings"]["productivity"] = {
            "score": 4,
            "confidence": "MEDIUM",
            "rationale": "Attempt to justify productivity with evidence declared only for authorship.",
            "evidence_refs": ["ev-p03-historical"],
        }
        with self.assertRaisesRegex(retrospective.RetrospectiveValidationError, "does not support this dimension"):
            retrospective.validate_register(register, self.contract)

    def test_anchor_only_match_cannot_prove_canonical_reuse(self) -> None:
        register = copy.deepcopy(self.register)
        record = register["records"][1]
        record["ratings"]["authorship_origin"] = {
            "score": 1,
            "confidence": "MEDIUM",
            "rationale": "Attempt to classify reuse from a first-line anchor only.",
            "evidence_refs": ["ev-p03-historical"],
        }
        record["authorship_profile"]["origin_label"] = "CANONICAL_REUSE"
        # Anchor-only matches are insufficient for CANONICAL_REUSE (requires EXACT).
        with self.assertRaisesRegex(
            retrospective.RetrospectiveValidationError,
            "CANONICAL_REUSE requires matched Prompt Kit ID and exact full-prompt match",
        ):
            retrospective.validate_register(register, self.contract)

    def test_no_composite_priority_is_defined(self) -> None:
        self.assertEqual(
            self.contract["record_contract"]["priority_policy"],
            "UNCOMPUTED_UNTIL_WEIGHTING_APPROVED",
        )
        joined = " ".join(self.contract["independence_rules"]).lower()
        self.assertIn("do not calculate a composite priority score", joined)
        self.assertIn("manual authorship is not inherently more productive", joined)


if __name__ == "__main__":
    unittest.main()
