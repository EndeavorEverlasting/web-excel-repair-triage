from __future__ import annotations

import copy
import json
import subprocess
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry as builder
from scripts import validate_prompt_kit_ontology_evidence as evidence_validator

ROOT = Path(__file__).resolve().parents[1]
CAPABILITIES = ROOT / "harness" / "capabilities.v1.json"
EVIDENCE_CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-ontology-evidence.v1.json"
HISTORY_LEDGER = ROOT / "docs" / "prompt-kit-ontology-history.v1.json"
ONTOLOGY_RUNTIME = ROOT / "docs" / "prompt-kit-ontology.js"
TEACHING_RECORD = ROOT / ".teach" / "learning-records" / "2026-08-29_prompt-kit-ontology.md"

LINEAGE = {
    "record_id": "obs-1",
    "capability_id": "skill-evaluation",
    "implementation_locator": "P62",
    "observed_at": "2026-09-05T00:00:00Z",
    "source": "unit-fixture",
    "subject_ref": "P62",
}


def _record(kind: str, **extra: object) -> dict[str, object]:
    payload = dict(LINEAGE)
    payload["record_id"] = f"obs-{kind}"
    payload["record_kind"] = kind
    payload.update(extra)
    return payload


class PromptKitOntologyViewTests(unittest.TestCase):
    def test_model_preserves_canonical_capability_contracts(self) -> None:
        registry = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
        prompts = builder.load_prompt_kit_registry()
        model = builder.build_ontology_model(prompts)

        self.assertEqual(model["schema_version"], "prompt-kit-ontology/v1")
        self.assertEqual(
            [item["id"] for item in model["capabilities"]],
            [item["id"] for item in registry["capabilities"]],
        )
        self.assertEqual(len(model["implementations"]), len(model["capabilities"]))
        self.assertTrue(
            {"prompt", "script", "launcher"}.issubset(
                {item["kind"] for item in model["implementations"]}
            )
        )
        expected = {item["id"]: item for item in registry["capabilities"]}
        actual = {item["id"]: item for item in model["capabilities"]}
        for capability_id, source in expected.items():
            with self.subTest(capability=capability_id):
                self.assertEqual(actual[capability_id]["skill"], source["skill"])
                self.assertEqual(actual[capability_id]["implementation"], source["implementation"])
                self.assertEqual(actual[capability_id]["proof_ceiling"], source["proof_ceiling"])

    def test_skill_inventory_matches_actual_skill_files(self) -> None:
        model = builder.build_ontology_model(builder.load_prompt_kit_registry())
        expected_paths = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / ".ai" / "skills").glob("*/SKILL.md")
        }
        actual_paths = {item["path"] for item in model["skills"]}
        self.assertEqual(actual_paths, expected_paths)

    def test_prompt_implementation_is_relationship_not_skill_identity(self) -> None:
        model = builder.build_ontology_model(builder.load_prompt_kit_registry())
        capability = next(
            item for item in model["capabilities"] if item["id"] == "skill-evaluation"
        )
        implementation = next(
            item
            for item in model["implementations"]
            if item["capability_id"] == "skill-evaluation"
        )
        self.assertEqual(capability["skill"], ".ai/skills/skill-evaluation/SKILL.md")
        self.assertEqual(implementation["kind"], "prompt")
        self.assertEqual(implementation["prompt_id"], "P62")
        self.assertTrue(implementation["prompt_name"])
        self.assertNotEqual(implementation["skill"], implementation["prompt_id"])

    def test_model_embeds_empty_history_without_fabricating_runs(self) -> None:
        model = builder.build_ontology_model(builder.load_prompt_kit_registry())
        evidence = model["evidence"]
        history = evidence["history"]
        self.assertEqual(evidence["schema_version"], "prompt-kit-ontology-evidence/v1")
        self.assertEqual(
            set(evidence["record_kinds"]),
            {
                "invocation",
                "run_result",
                "failure",
                "critique",
                "favorite",
                "feedback",
                "eval",
                "proof_receipt",
            },
        )
        self.assertEqual(history["schema_version"], "prompt-kit-ontology-history/v1")
        self.assertEqual(history["records"], [])
        self.assertEqual(history["count"], 0)
        self.assertTrue(history["append_only"])
        self.assertIn("does not assert that any live event occurred", history["proof_ceiling"])

    def test_render_embeds_ontology_data_and_runtime(self) -> None:
        html = builder.render()
        runtime = ONTOLOGY_RUNTIME.read_text(encoding="utf-8")
        self.assertIn("window.PROMPT_KIT_ONTOLOGY", html)
        self.assertIn("prompt-kit-ontology/v1", html)
        self.assertIn("Repository-backed agentic map", html)
        self.assertIn(runtime, html)
        self.assertIn("Declared proof, not run history.", html)
        self.assertIn("Observed history is distinct from declared proof ceilings.", html)
        self.assertIn("prompt-kit-ontology-evidence/v1", html)
        self.assertIn("promptKit.favoritePromptIds.v1", html)
        self.assertIn("MutationObserver", html)
        self.assertNotIn("separate future evidence/history layer", html)
        self.assertIn('"records":[]', html.replace(" ", ""))

    def test_evidence_history_contract_extends_mastered_ontology_without_fabricating_runs(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        history = json.loads(HISTORY_LEDGER.read_text(encoding="utf-8"))
        report = evidence_validator.validate()

        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(
            contract["relation_chain"],
            ["capability", "skill", "implementation", "invocation", "run", "evidence", "proof_ceiling"],
        )
        self.assertEqual(
            contract["authority"]["history_ledger"],
            "docs/prompt-kit-ontology-history.v1.json",
        )
        self.assertEqual(contract["record_kinds"]["favorite"]["proof_effect"], "none")
        self.assertEqual(contract["record_kinds"]["failure"]["proof_effect"], "lower_or_block")
        self.assertEqual(contract["record_kinds"]["feedback"]["raw_payload_transport"], "out_of_scope")
        self.assertEqual(history["records"], [])
        self.assertIn("does not assert that any invocation", contract["proof_ceiling"])

    def test_evidence_history_validator_rejects_preference_as_proof(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        mutated = copy.deepcopy(contract)
        mutated["record_kinds"]["favorite"]["proof_effect"] = "supports_observed_claim"

        report = evidence_validator.validate_payload(
            mutated,
            ONTOLOGY_RUNTIME.read_text(encoding="utf-8"),
            TEACHING_RECORD.read_text(encoding="utf-8"),
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("favorites must not count as proof", report["errors"])

    def test_history_validator_accepts_distinct_record_kinds(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        records = [
            _record("invocation"),
            _record("run_result"),
            _record("failure"),
            _record("critique"),
            _record("favorite"),
            _record("feedback"),
            _record("eval"),
            _record("proof_receipt", immutable=True),
        ]
        self.assertEqual(evidence_validator.validate_history_records(contract, records), [])

    def test_history_validator_rejects_favorite_record_as_proof(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        errors = evidence_validator.validate_history_records(
            contract,
            [_record("favorite", proof_effect="supports_observed_claim")],
        )
        self.assertTrue(errors)
        self.assertTrue(any("must not override favorite proof_effect" in item for item in errors))

    def test_history_validator_rejects_feedback_transport_payload(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        errors = evidence_validator.validate_history_records(
            contract,
            [_record("feedback", raw_payload={"body": "secret"})],
        )
        self.assertTrue(errors)
        self.assertTrue(any("feedback transport payloads" in item for item in errors))

    def test_history_validator_rejects_failure_that_raises_proof(self) -> None:
        contract = json.loads(EVIDENCE_CONTRACT.read_text(encoding="utf-8"))
        errors = evidence_validator.validate_history_records(
            contract,
            [_record("failure", proof_effect="supports_observed_claim")],
        )
        self.assertTrue(errors)
        self.assertTrue(
            any("must not override failure proof_effect" in item or "cannot raise proof" in item for item in errors)
        )

    def test_local_favorite_projection_is_preference_not_proof(self) -> None:
        script = """
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('docs/prompt-kit-ontology.js', 'utf8');
const sandbox = { window: {}, console };
vm.runInNewContext(source, sandbox);
const api = sandbox.window.PROMPT_KIT_ONTOLOGY_HISTORY;
if (!api) throw new Error('missing history api');
const records = api.projectLocalFavorites(
  {P62: true, P03: true},
  [{prompt_id: 'P62', capability_id: 'skill-evaluation'}]
);
if (records.length !== 2) throw new Error('count ' + records.length);
if (records.some((record) => record.proof_effect !== 'none' || record.class !== 'preference' || record.preference_signal !== true)) {
  throw new Error('favorites became proof');
}
const linked = records.find((record) => record.implementation_locator === 'P62');
const loose = records.find((record) => record.implementation_locator === 'P03');
if (!linked || linked.capability_id !== 'skill-evaluation') throw new Error('linked capability');
if (!loose || loose.capability_id !== 'unlinked') throw new Error('unlinked favorite');
if (api.LOCAL_FAVORITES_SOURCE !== 'promptKit.favoritePromptIds.v1') throw new Error('source');
if (api.proofLabel('favorite', {favorite: {proof_effect: 'none'}}) !== 'no proof') throw new Error('favorite label');
if (api.proofLabel('failure', {failure: {proof_effect: 'lower_or_block'}}).indexOf('never raises') < 0) throw new Error('failure label');
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)


if __name__ == "__main__":
    unittest.main()
