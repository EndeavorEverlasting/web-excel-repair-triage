from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sync_operant_external_resources as sync  # noqa: E402
from scripts import validate_operant_external_resources as validator  # noqa: E402

CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"
GAPS = ROOT / "registry" / "resources" / "operant-external-resource-gaps.v1.json"
RUNTIME = ROOT / "docs" / "prompt-kit-external-resources.js"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
PORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"


class OperantExternalResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.index = json.loads(INDEX.read_text(encoding="utf-8"))
        cls.gaps = json.loads(GAPS.read_text(encoding="utf-8"))
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.site = SITE.read_text(encoding="utf-8")

    def test_registered_donors_and_roots_are_explicit(self) -> None:
        sources = {item["id"]: item for item in self.contract["sources"]}
        self.assertEqual(sources["deepseek-harness"]["repository"], "deepseek-ai/deepseek-harness")
        self.assertEqual(sources["deepseek-harness"]["expected_default_branch"], "master")
        self.assertEqual(sources["deepseek-harness"]["resource_root"], ".agents/skills")
        self.assertEqual(sources["anthropic-skills"]["repository"], "anthropics/skills")
        self.assertEqual(sources["anthropic-skills"]["expected_default_branch"], "main")
        self.assertEqual(sources["anthropic-skills"]["resource_root"], "skills")

    def test_index_is_metadata_only_commit_pinned_and_bounded(self) -> None:
        self.assertTrue(self.contract["projection"]["metadata_only"])
        self.assertFalse(self.contract["projection"]["copy_upstream_skill_body"])
        floors = {row["id"]: row for row in self.index["source_floor"]}
        self.assertEqual(set(floors), {"deepseek-harness", "anthropic-skills"})
        self.assertLessEqual(len(self.index["resources"]), self.contract["projection"]["maximum_entries"])
        self.assertLessEqual(INDEX.stat().st_size, self.contract["projection"]["maximum_index_bytes"])
        for resource in self.index["resources"]:
            floor = floors[resource["source_id"]]
            self.assertIn(f"/blob/{floor['resolved_sha']}/", resource["url"])
            self.assertNotIn("copyContent", resource)
            self.assertNotIn("body", resource)
            self.assertLessEqual(len(resource["search_terms"]), self.contract["projection"]["maximum_search_terms_per_resource"])

    def test_missing_coverage_points_external_and_routes_prompt_review(self) -> None:
        external = [r for r in self.index["resources"] if r["coverage"]["disposition"] == "POINT_TO_EXTERNAL"]
        self.assertEqual(len(external), len(self.gaps["actions"]))
        self.assertFalse(self.gaps["policy"]["automatic_prompt_authoring"])
        self.assertEqual(self.gaps["policy"]["promotion_owner_prompt"], "P79")
        for resource in external:
            self.assertEqual(resource["coverage"]["prompt_action"], "REVIEW_ADD_PROMPT")
        for action in self.gaps["actions"]:
            self.assertEqual(action["user_disposition"], "POINT_TO_EXTERNAL")
            self.assertEqual(action["prompt_action"], "REVIEW_ADD_PROMPT")
            self.assertEqual(action["promotion_owner_prompt"], "P79")

    def test_existing_coverage_never_requests_duplicate_prompt(self) -> None:
        covered = [r for r in self.index["resources"] if r["coverage"]["disposition"] != "POINT_TO_EXTERNAL"]
        for resource in covered:
            self.assertEqual(resource["coverage"]["prompt_action"], "NO_NEW_PROMPT")
            self.assertTrue(resource["coverage"]["target_id"])

    def test_resource_runtime_is_lazy_and_paginated(self) -> None:
        self.assertIn("var OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE=40", self.runtime)
        self.assertIn("function loadExternalResources()", self.runtime)
        self.assertIn("function openExternalResources()", self.runtime)
        self.assertIn("loadExternalResources().then", self.runtime)
        open_start = self.runtime.index("function openExternalResources()")
        self.assertGreater(self.runtime.index("loadExternalResources().then"), open_start)
        prefix = self.runtime[:open_start]
        self.assertNotIn("loadExternalResources().then", prefix)
        self.assertIn("resources.v1.json", self.runtime)
        self.assertIn("externalResourcePage+1", self.runtime)

    def test_main_generated_html_embeds_runtime_not_catalog_records(self) -> None:
        self.assertIn("operant-external-resources/v1", self.site)
        self.assertIn("resources.v1.json", self.site)
        sample = self.index["resources"][: min(20, len(self.index["resources"]))]
        for resource in sample:
            self.assertNotIn(resource["url"], self.site)


    def test_release_packages_include_sidecar_without_embedding_records(self) -> None:
        pages = PAGES_WORKFLOW.read_text(encoding="utf-8")
        portable = PORTABLE_BUILDER.read_text(encoding="utf-8")
        self.assertIn('cp web/prompt-kit/resources.v1.json "$SITE_ROOT/prompt-kit/resources.v1.json"', pages)
        self.assertIn('cmp "$SITE_ROOT/prompt-kit/resources.v1.json" web/prompt-kit/resources.v1.json', pages)
        self.assertIn('RESOURCE_INDEX_NAME = "resources.v1.json"', portable)
        self.assertIn('resource_source_path = repo_root / "web" / "prompt-kit" / RESOURCE_INDEX_NAME', portable)
        self.assertIn('resource_sidecar_matches_canonical', portable)

    def test_token_match_is_deterministic_and_conservative(self) -> None:
        query = sync.tokens("code-review")
        self.assertEqual(sync.coverage_score(query, sync.tokens("Code Review")), 1.0)
        self.assertEqual(sync.coverage_score(query, sync.tokens("PDF generation")), 0.0)
        candidates = [
            ("P9", "Code Review", sync.tokens("Code Review")),
            ("P2", "Code Review", sync.tokens("Code Review")),
        ]
        self.assertEqual(sync.best_match(query, candidates)[0], "P2")

    def test_full_validator_accepts_current_projection(self) -> None:
        result = validator.validate()
        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["lazy_fetch"])
        self.assertEqual(result["resources"], len(self.index["resources"]))


if __name__ == "__main__":
    unittest.main()
