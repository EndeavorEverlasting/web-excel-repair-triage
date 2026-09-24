from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import prompt_registry_external_prior_art as gate  # noqa: E402

CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"


class ExternalPriorArtGateRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))

    def test_source_floor_rejects_non_hexadecimal_sha(self) -> None:
        bad_index = {
            "source_floor": [
                {"id": "bad-source", "resolved_sha": "z" * 40},
            ]
        }
        with self.assertRaisesRegex(gate.PriorArtGateError, "invalid pinned SHA"):
            gate._source_floor(bad_index, "bad-source")

    def test_internal_residual_uses_full_selected_candidate_tokens(self) -> None:
        prompt_candidates = [("P999", "Display Name", {"display", "keywordonly"})]
        with mock.patch.object(gate.sync, "prompt_titles", return_value=prompt_candidates), mock.patch.object(
            gate.sync, "skill_titles", return_value=[]
        ):
            best, residual = gate._internal_comparison({"keywordonly"}, 12)
        self.assertEqual(best["id"], "P999")
        self.assertEqual(best["score"], 1.0)
        self.assertEqual(residual, [])

    def test_duplicate_registered_source_ids_fail_closed(self) -> None:
        contract = json.loads(json.dumps(self.contract))
        contract["sources"].append(dict(contract["sources"][0]))
        with mock.patch.object(gate.sync, "load_json", side_effect=[contract, self.index]), mock.patch.object(
            gate, "_internal_comparison", return_value=({}, ["quokka"])
        ):
            with self.assertRaisesRegex(gate.PriorArtGateError, "source ids must be unique"):
                gate.require_external_prior_art(
                    {
                        "name": "Quokka Prior Art Gate",
                        "keywords": ["quokka"],
                    }
                )


if __name__ == "__main__":
    unittest.main()
