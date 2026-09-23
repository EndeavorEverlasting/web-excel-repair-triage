from __future__ import annotations

import json
import subprocess
import tempfile
import unittest

import build_prompt_kit
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "docs" / "prompt-kit.js"
BASE_REGISTRY = ROOT / "docs" / "prompts.json"
REPO_LEDGER = ROOT / "registry" / "prompts" / "repository-work-ledger-prompts.v1.json"
P143_SYNONYMS = (
    "repository convergence",
    "repo convergence",
    "multi-repo convergence",
    "donor sources",
    "convergence plan",
    "capability disposition",
    "destination repository plan",
    "typed bootstrap manifest",
)
PROPOSAL_STATES = ("operator_proposed", "planner_selected")
PROVIDER_STATES = ("UNVERIFIED", "AVAILABLE", "EXISTS_OWNED", "EXISTS_CONFLICT")
AUTHORITY_STATES = ("operator_approved", "execution_authorization")


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

    def test_case_c_validated_manifest_routes_by_typed_destination_state(self) -> None:
        p143 = _load_p143()
        self.assertIn("validated p55-bootstrap-handoff/v1 manifest already exists", p143["useWhen"])
        self.assertIn("P55_CREATE routes to P55", p143["useWhen"])
        self.assertIn("INTEGRATE_EXISTING routes to P07/P16/P21", p143["useWhen"])
        self.assertEqual(build_prompt_kit.SYNONYMS["bootstrap"], "P55")

    def test_case_d_ordinary_cross_repo_integration_is_not_p143(self) -> None:
        self.assertEqual(build_prompt_kit.SYNONYMS["cross repo"], "P16")
        self.assertNotEqual(build_prompt_kit.SYNONYMS["cross repo"], "P143")
        p143 = _load_p143()
        self.assertIn("ordinary one-repo integration/PR merge (P16/P21/P07)", p143["useWhen"])

    def test_case_e_uncertain_destination_keeps_state_dimensions_separate(self) -> None:
        p143 = _load_p143()
        self.assertIn("destination proposal", p143["useWhen"])
        self.assertIn("provider state", p143["useWhen"])
        self.assertIn("execution authorization", p143["useWhen"])
        self.assertIn("operator_proposed", p143["copyContent"])
        self.assertIn("provider evidence never creates authorization", p143["proofGate"])


    def test_generated_search_preserves_p55_p143_precedence_without_prefix_leakage(self) -> None:
        js = JS.read_text(encoding="utf-8")
        start = js.index("function normalizeSearchText")
        end = js.index("function promptSequenceValue")
        helpers = js[start:end]
        prompts = {
            prompt["id"]: prompt
            for prompt in build_prompt_kit_registry.load_prompt_kit_registry()
            if prompt["id"] in {"P55", "P143"}
        }
        fields = (
            "id", "seq", "name", "type", "class", "useWhen",
            "sprintRole", "proofGate", "copyContent", "keywords",
        )
        payload = [
            {key: prompts[prompt_id].get(key) for key in fields}
            for prompt_id in ("P55", "P143")
        ]
        script = (
            "var SYNONYMS=" + json.dumps(build_prompt_kit.SYNONYMS) + ";\n"
            "function promptSequenceValue(p){var raw=String((p&&p.seq)||((p&&p.id)||''));"
            "var n=parseInt(raw.replace(/\\D/g,''),10);return isNaN(n)?Number.MAX_SAFE_INTEGER:n}\n"
            + helpers
            + "\nvar prompts=" + json.dumps(payload) + ";\n"
            + "var queries=['repository convergence','combine repositories','bootstrap'];\n"
            + "var out={};queries.forEach(function(q){out[q]=filterPromptsForQuery(prompts,q).map(function(p){return p.id})});\n"
            + "var synonymOnly={};['operator','cleanup','cursor','closeout','compiler','cluster','consolidate','combine repository']"
            + ".forEach(function(q){synonymOnly[q]=synonymPromptIdsForQuery(q)});\n"
            + "process.stdout.write(JSON.stringify({ranked:out,synonymOnly:synonymOnly}));\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "p143_search_regression.js"
            script_path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                ["node", str(script_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        result = json.loads(completed.stdout)
        self.assertEqual(result["ranked"]["repository convergence"][0], "P143")
        self.assertNotIn("P143", result["synonymOnly"].get("combine repository", []))
        self.assertEqual(result["ranked"]["bootstrap"][0], "P55")
        for query, ids in result["synonymOnly"].items():
            self.assertNotIn("P143", ids, f"{query!r} must not leak through a short P143 synonym")


class TokenCorridorEvidenceStateTests(unittest.TestCase):
    def test_operator_proposed_name_remains_proposal_not_provider_fact(self) -> None:
        p143 = _load_p143()
        copy_content = p143["copyContent"]
        self.assertIn("operator_proposed: named by the operator; not a provider fact", copy_content)

    def test_proposal_provider_and_authority_states_are_orthogonal(self) -> None:
        p143 = _load_p143()
        copy_content = p143["copyContent"]
        for state in PROPOSAL_STATES + PROVIDER_STATES + AUTHORITY_STATES:
            self.assertIn(state, copy_content, f"missing typed state {state}")
        self.assertIn("AVAILABLE is not EXISTS_OWNED", copy_content)
        self.assertIn("Provider evidence never creates authority", copy_content)
        self.assertIn("p55-bootstrap-handoff/v1", copy_content)

    def test_donor_public_visibility_does_not_imply_destination_public(self) -> None:
        p143 = _load_p143()
        self.assertIn(
            "Public donors do not imply a public destination",
            p143["copyContent"],
        )
        self.assertIn(
            "provider evidence never creates authorization",
            p143["proofGate"],
        )

    def test_p55_create_route_does_not_mint_mutation_authority(self) -> None:
        p143 = _load_p143()
        self.assertIn("P55 must still enforce operator_approved and execution_authorization before mutation", p143["copyContent"])
        self.assertIn("provider evidence never creates authorization", p143["proofGate"])


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
        self.assertNotIn("strength.mainline_convergence", owned)
        self.assertIn("strength.plan_durability", owned)
        mainline = [
            row for row in profile[0]["direct_assignments"]
            if row["capability_id"] == "strength.mainline_convergence"
        ]
        self.assertEqual(len(mainline), 1)
        self.assertEqual(mainline[0]["presence"], "REQUIRED")
        self.assertEqual(mainline[0]["ownership"], "SECONDARY")
        self.assertEqual(mainline[0]["capability_relation"], "GUARDS")


if __name__ == "__main__":
    unittest.main()
