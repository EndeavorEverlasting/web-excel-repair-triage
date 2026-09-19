from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts import evidence_spine_route_receipt as route_receipt

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "harness/evals/fixtures/evidence-spine-route-receipt-cases.v1.json"


class EvidenceSpineRouteReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(CASES.read_text(encoding="utf-8"))

    def test_every_declared_case_is_executed_and_matches_destination_semantics(self) -> None:
        self.assertEqual(
            self.fixture["schema_version"],
            "evidence-spine-route-receipt-cases/v1",
        )
        cases = self.fixture["cases"]
        self.assertGreaterEqual(len(cases), 3)
        seen: set[str] = set()
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["id"], seen)
                seen.add(case["id"])
                receipt = route_receipt.build_route_receipt(**case["input"])
                route_receipt.validate_route_receipt(receipt)
                for key, expected in case["expected"].items():
                    self.assertEqual(receipt["destination"][key], expected)

    def test_same_input_is_byte_stable_and_idempotent(self) -> None:
        payload = self.fixture["cases"][0]["input"]
        first = route_receipt.build_route_receipt(**payload)
        second = route_receipt.build_route_receipt(**payload)
        self.assertEqual(first, second)
        self.assertEqual(
            route_receipt.compare_idempotency(first, second),
            "IDEMPOTENT_NOOP",
        )

    def test_same_route_id_with_changed_semantics_is_conflict_without_state_mutation(self) -> None:
        payload = dict(self.fixture["cases"][0]["input"])
        first = route_receipt.build_route_receipt(**payload)
        changed = route_receipt.build_route_receipt(
            **{**payload, "prompt_id": "P08"}
        )
        self.assertEqual(
            first["idempotency"]["key"],
            changed["idempotency"]["key"],
        )
        self.assertNotEqual(
            first["idempotency"]["semantic_sha256"],
            changed["idempotency"]["semantic_sha256"],
        )
        self.assertEqual(
            route_receipt.compare_idempotency(first, changed),
            "IDEMPOTENCY_CONFLICT",
        )

    def test_distinct_route_ids_are_distinct_idempotency_domains(self) -> None:
        payload = dict(self.fixture["cases"][0]["input"])
        first = route_receipt.build_route_receipt(**payload)
        second = route_receipt.build_route_receipt(
            **{**payload, "route_id": "route.case.other"}
        )
        self.assertEqual(
            route_receipt.compare_idempotency(first, second),
            "DISTINCT",
        )

    def test_invalid_inputs_fail_closed(self) -> None:
        valid = dict(self.fixture["cases"][0]["input"])
        cases = (
            {"prompt_id": "BAD"},
            {"prompt_revision": ""},
            {"route_id": "../escape"},
            {"source_surface": "contains spaces"},
            {"provenance": "authoritative"},
            {"destination": 42},
        )
        for change in cases:
            with self.subTest(change=change), self.assertRaises(route_receipt.RouteReceiptError):
                route_receipt.build_route_receipt(**{**valid, **change})

    def test_validation_recomputes_identity_and_destination_semantics(self) -> None:
        receipt = route_receipt.build_route_receipt(**self.fixture["cases"][0]["input"])
        mutations = []

        bad_digest = copy.deepcopy(receipt)
        bad_digest["idempotency"]["semantic_sha256"] = "0" * 64
        mutations.append(bad_digest)

        bad_key = copy.deepcopy(receipt)
        bad_key["idempotency"]["key"] = "idem_" + "0" * 64
        mutations.append(bad_key)

        bad_receipt = copy.deepcopy(receipt)
        bad_receipt["receipt_id"] = "route_" + "0" * 24
        mutations.append(bad_receipt)

        promoted_inference = route_receipt.build_route_receipt(**self.fixture["cases"][1]["input"])
        promoted_inference["destination"]["authoritative"] = True
        promoted_inference["destination"]["effective_destination"] = "cursor-agent"
        mutations.append(promoted_inference)

        extra = copy.deepcopy(receipt)
        extra["actor_id"] = "forbidden-identity"
        mutations.append(extra)

        for payload in mutations:
            with self.subTest(payload=payload), self.assertRaises(route_receipt.RouteReceiptError):
                route_receipt.validate_route_receipt(payload)

    def test_receipt_is_actor_neutral_and_has_no_route_state_or_outcome_authority(self) -> None:
        receipt = route_receipt.build_route_receipt(**self.fixture["cases"][0]["input"])
        encoded = json.dumps(receipt, sort_keys=True).lower()
        for forbidden in (
            "actor_id",
            "session_id",
            "user_id",
            "state_version",
            "compare_and_set",
            "mutation_allowed",
            "route_version",
            "outcome",
            "raw_prompt",
            "raw_response",
            "transcript",
            "clipboard",
        ):
            self.assertNotIn(forbidden, encoded)
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "receipt_id",
                "route_id",
                "prompt_id",
                "prompt_revision",
                "source_surface",
                "destination",
                "idempotency",
            },
        )


if __name__ == "__main__":
    unittest.main()
