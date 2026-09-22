from __future__ import annotations

import json
import unittest

import build_prompt_kit
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
BASE_REGISTRY = ROOT / "docs" / "prompts.json"
REPO_LEDGER = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
P143_SYNONYMS = (
    "repository convergence",
    "repo convergence",
    "multi-repo convergence",
    "a+b to c",
    "donor sources",
    "convergence plan",
    "capability disposition",
    "destination repository plan",
    "typed bootstrap manifest",
    "operator_proposed",
)
EVIDENCE_LADDER = (
    "operator_proposed",
    "planner_selected",
    "provider_verified",
    "operator_approved",
    "execution_authorization",
)


def _load_p143() -> dict:
    payload = json.loads(REPO_LEDGER.read_text(encoding="utf-8"))
    matches = [row for row in payload["prompts"] if row.get("id") == "P143"]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one P143 record, found {len(matches)}")
    return matches[0]


def _load_p55() -> dict:
    payload = json.loads(BASE_REGISTRY.read_text(encoding="utf-8"))
    matches = [row for row in payload if row.get("id") == "P55"]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one P55 record, found {len(matches)}")
    return matches[0]


class RepositoryConvergenceRoutingTests(unittest.TestCase):
    def test_case_a_simple_create_routes_to_p55(self) -> None:
        self.assertEqual(build_prompt_kit.SYNONYMS["bootstrap"], "P55")
        self.assertEqual(build_prompt_kit.SYNONYMS["github cli"], "P55")
        p55 = _load_p55()
        self.assertEqual(p55["name"], "GitHub CLI Repository Bootstrapper")
        self.assertIn("single-repository creation", p55["useWhen"])

    def test_case_b_a_plus_b_to_c_routes_to_p143(self) -> None:
        for synonym in P143_SYNONYMS:
            with self.subTest(synonym=synonym):
                self.assertEqual(build_prompt_kit.SYNONYMS[synonym], "P143")
        p143 = _load_p143()
        self.assertEqual(p143["name"], "Repository Convergence Planner")
        self.assertEqual(p143["type"], "CONSOLIDATE + EXECUTE")
        self.assertEqual(p143["class"], "CROSS-REPO / CONVERGENCE PLAN")
        self.assertIn("A and B", p143["useWhen"])
        self.assertIn("typed P55 bootstrap manifest", p143["keywords"])

    def test_case_c_already_planned_manifest_returns_to_p55(self) -> None:
        p143 = _load_p143()
        self.assertIn("after a typed P55 manifest already exists", p143["useWhen"])
        self.assertIn("route to P55", p143["useWhen"])
        self.assertEqual(build_prompt_kit.SYNONYMS["bootstrap"], "P55")

    def test_case_d_ordinary_cross_repo_integration_is_not_p143(self) -> None:
        self.assertEqual(build_prompt_kit.SYNONYMS["cross repo"], "P16")
        self.assertNotEqual(build_prompt_kit.SYNONYMS["cross repo"], "P143")
        p143 = _load_p143()
        self.assertIn("ordinary one-repo integration or PR merge (P16/P21/P07)", p143["useWhen"])

    def test_case_e_uncertain_destination_stays_operator_proposed(self) -> None:
        p143 = _load_p143()
        self.assertIn("operator_proposed", p143["useWhen"])
        self.assertIn("operator_proposed is never promoted to proven", p143["proofGate"])


class TokenCorridorEvidenceStateTests(unittest.TestCase):
    def test_tokencorridor_name_remains_operator_proposed(self) -> None:
        p143 = _load_p143()
        copy_content = p143["copyContent"]
        self.assertIn("TokenCorridor", copy_content)
        self.assertIn(
            "TokenCorridor and any other operator-proposed destination name remain operator_proposed",
            copy_content,
        )

    def test_evidence_ladder_is_ordered_and_not_silently_promoted(self) -> None:
        p143 = _load_p143()
        copy_content = p143["copyContent"]
        positions = []
        for state in EVIDENCE_LADDER:
            self.assertIn(state, copy_content, f"missing evidence state {state}")
            positions.append(copy_content.index(state))
        self.assertEqual(positions, sorted(positions), "evidence ladder must stay ordered")
        self.assertIn("Never promote an evidence state silently", copy_content)

    def test_donor_public_visibility_does_not_imply_destination_public(self) -> None:
        p143 = _load_p143()
        self.assertIn(
            "Public donor repositories do not imply a public destination",
            p143["copyContent"],
        )
        self.assertIn(
            "donor public visibility does not imply destination public visibility",
            p143["proofGate"],
        )

    def test_p55_fields_not_claimed_resolved_while_authorization_outstanding(self) -> None:
        p143 = _load_p143()
        self.assertIn(
            "Claim all P55 fields are resolved while execution_authorization is unresolved",
            p143["copyContent"],
        )
        self.assertIn(
            "P55 fields are not reported fully resolved while authorization is outstanding",
            p143["proofGate"],
        )


class P55OwnershipBoundaryTests(unittest.TestCase):
    def test_p55_use_when_excludes_multi_repo_convergence(self) -> None:
        p55 = _load_p55()
        self.assertIn("single-repository creation and publish only", p55["useWhen"])
        self.assertIn("routes to P143 first", p55["useWhen"])
        self.assertIn("hands repository creation and publish execution to this prompt", p55["useWhen"])

    def test_p55_does_not_claim_convergence_plan_ownership(self) -> None:
        p55 = _load_p55()
        self.assertNotIn("owns multi-repository convergence", p55["useWhen"])
        self.assertNotIn("A+B", p55["useWhen"])

    def test_p143_profile_is_accepted_and_owns_planning_capabilities(self) -> None:
        prompts = build_prompt_kit_registry.load_prompt_kit_registry()
        by_id = {prompt["id"]: prompt for prompt in prompts}
        self.assertIn("P143", by_id)
        self.assertEqual(by_id["P143"]["name"], "Repository Convergence Planner")
        profiles = json.loads(
            (ROOT / "harness" / "prompt-topology" / "prompt-capability-profiles.v1.json").read_text(
                encoding="utf-8"
            )
        )
        profile = [row for row in profiles["profiles"] if row.get("prompt_id") == "P143"]
        self.assertEqual(len(profile), 1)
        self.assertEqual(profile[0]["profile_status"], "ACCEPTED")
        owned = {
            row["capability_id"]
            for row in profile[0]["direct_assignments"]
            if row.get("ownership") == "PRIMARY"
        }
        self.assertIn("strength.mainline_convergence", owned)
        self.assertIn("strength.plan_durability", owned)


if __name__ == "__main__":
    unittest.main()
