from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


ROOT = Path(__file__).resolve().parents[1]


class RemoteFreshnessAndP13IterationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {
            item["id"]: item
            for item in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        }
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.effective = {
            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()
        }
        cls.operator_delivery = (ROOT / "harness" / "specs" / "operator-delivery.md").read_text(encoding="utf-8")

    def test_shared_operational_policy_requires_fresh_remote_floor(self) -> None:
        marker = self.policy["freshness_marker"]
        appendix = self.policy["copy_content_appendix"]
        self.assertEqual(marker, "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT")
        self.assertIn("git fetch --all --prune --tags", appendix)
        self.assertIn("git pull --ff-only", appendix)
        self.assertIn("Re-fetch before final exact-head validation/integration", appendix)
        self.assertIn("never force-reset", appendix)
        self.assertIn("FRESH EVIDENCE FLOOR", appendix)
        self.assertIn("owning contracts/specs/profiles/registries/generators", appendix)
        self.assertIn("registered artifact manifests/reports", appendix)
        self.assertIn("versioned proof", appendix)
        self.assertIn("Post-integration verification is containment-based, not head-equality-based", appendix)
        self.assertIn("git merge-base --is-ancestor", appendix)
        self.assertIn("Do not fail merely because the default branch advanced", appendix)
        self.assertIn("not an ancestor of the refreshed default head", appendix)

        # Representative build/repair executors must inherit freshness from one shared owner.
        for prompt_id in ("P01", "P03", "P07", "P14", "P17", "P18", "P83"):
            with self.subTest(prompt_id=prompt_id):
                content = self.effective[prompt_id]["copyContent"]
                self.assertIn(marker, content)
                self.assertIn("git fetch --all --prune --tags", content)

    def test_builder_upgrades_old_appendix_that_lacks_freshness(self) -> None:
        base = dict(self.raw["P07"])
        marker = self.policy["marker"]
        integration = self.policy["integration_marker"]
        freshness = self.policy["freshness_marker"]
        base["copyContent"] = (
            "BASE PROMPT\n\n"
            + marker
            + "\n- Do not leave NEXT COMMAND blank.\n\n"
            + integration
            + "\n- Treat integration as completion."
        )
        upgraded = build_prompt_kit_registry.apply_actionability_policy(base, self.policy)
        content = upgraded["copyContent"]
        self.assertIn(freshness, content)
        self.assertEqual(content.count(marker), 1)
        self.assertEqual(content.count(integration), 1)

    def test_p07_raw_source_refreshes_and_reconciles_before_building(self) -> None:
        p07 = self.raw["P07"]
        content = p07["copyContent"]
        self.assertIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("refs/remotes/origin/HEAD", content)
        self.assertIn("git pull --ff-only", content)
        self.assertIn("Re-fetch immediately before final exact-head validation/integration", content)
        self.assertIn("never force-reset, force-pull, or overwrite unique", content)
        self.assertIn("refreshed and reconciled remote/default-branch floor", p07["expectedOutput"])
        self.assertIn("refreshed before implementation", p07["proofGate"])

    def test_p13_prototypes_rules_and_rules_out_stale_branch_before_doctrine(self) -> None:
        p13 = self.raw["P13"]
        content = p13["copyContent"]
        self.assertIn("REMOTE TRUTH FIRST", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("already-fixed mainline state", content)
        self.assertIn("ITERATIVE RULE PROTOTYPE LOOP", content)
        self.assertIn("PROTOTYPE -> TEST -> CRITIQUE -> REVISE", content)
        self.assertIn("counterexample", content)
        self.assertIn("Prefer executable enforcement over prose", content)
        self.assertIn("Do not manufacture revisions", content)
        self.assertIn("Do not ask the user to compare rule wording", content)
        self.assertIn("Stale branch state is ruled out before inventing doctrine", p13["proofGate"])
        self.assertIn("smallest enforceable repo doctrine", p13["sprintRole"])


    def test_every_build_repair_or_artifact_prompt_inherits_fresh_evidence_floor(self) -> None:
        build_like = [
            prompt
            for prompt in self.effective.values()
            if any(token in str(prompt["type"]).upper() for token in ("BUILD", "REPAIR", "ARTIFACT"))
        ]
        self.assertGreater(len(build_like), 0)
        for prompt in build_like:
            with self.subTest(prompt_id=prompt["id"], prompt_type=prompt["type"]):
                content = prompt["copyContent"]
                self.assertIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", content)
                self.assertIn("current/open/recent overlapping branches and PRs", content)
                self.assertIn("FRESH EVIDENCE FLOOR", content)
                self.assertIn("registered artifact manifests/reports", content)
                self.assertIn("current canonical generator/template/schema", content)

    def test_p48_and_live_cert_domain_law_pin_fresh_code_artifact_and_evidence(self) -> None:
        p48 = self.raw["P48"]
        content = p48["copyContent"]
        self.assertIn("FRESH REPOSITORY + EVIDENCE FLOOR BEFORE LIVE CERT", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("current/open/recent overlapping branches and PRs", content)
        self.assertIn("artifact path plus manifest/hash", content)
        self.assertIn("current validators/tests/CI conclusions", content)
        self.assertIn("prior live-cert receipts", content)
        self.assertIn("invalidate the affected proof", content)
        self.assertIn("freshness gate", p48["proofGate"].lower())

        domain = self.operator_delivery
        self.assertIn("## Freshness gate for live certification", domain)
        self.assertIn("git fetch --all --prune --tags", domain)
        self.assertIn("current/open/recent overlapping PRs and branches", domain)
        self.assertIn("artifact path and manifest/hash", domain)
        self.assertIn("Prior evidence remains useful history", domain)
        self.assertIn("mark affected proof stale", domain)


if __name__ == "__main__":
    unittest.main()
