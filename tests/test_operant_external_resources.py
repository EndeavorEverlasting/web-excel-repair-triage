from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import search_operant_external_catalog as catalog_search  # noqa: E402
from scripts import sync_operant_external_resources as sync  # noqa: E402
from scripts import validate_operant_external_resources as validator  # noqa: E402

CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"
GAPS = ROOT / "registry" / "resources" / "operant-external-resource-gaps.v1.json"
RUNTIME = ROOT / "docs" / "prompt-kit-external-resources.js"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
PORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"

FIXTURE_CSV = """act,prompt,for_devs,type,contributor
Code Review,"Review this pull request for correctness and regressions.",TRUE,TEXT,fixture
Linux Terminal,"Act as a linux terminal and reply with command output only.",TRUE,TEXT,fixture
PDF Generation,"Create a PDF report from spreadsheet rows.",FALSE,TEXT,fixture
"""


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
        self.assertEqual(set(sources), {"deepseek-harness", "prompts-chat", "mattpocock-skills"})
        self.assertEqual(sources["deepseek-harness"]["repository"], "deepseek-ai/deepseek-harness")
        self.assertEqual(sources["deepseek-harness"]["enumeration"], "git_skill_tree")
        self.assertEqual(sources["prompts-chat"]["repository"], "f/prompts.chat")
        self.assertEqual(sources["prompts-chat"]["enumeration"], "catalog_csv")
        self.assertEqual(sources["prompts-chat"]["resource_filename"], "prompts.csv")
        self.assertEqual(sources["prompts-chat"]["license"]["prompt_data"], "CC0-1.0")
        self.assertEqual(sources["mattpocock-skills"]["repository"], "mattpocock/skills")
        self.assertEqual(sources["mattpocock-skills"]["max_depth"], 2)
        self.assertFalse(self.contract["projection"]["catalog_csv_projects_rows_into_index"])
        self.assertIn(
            "registered_external_source_or_catalog_search",
            self.contract["coverage"]["p79_external_evidence"]["required_before_add"],
        )

    def test_index_is_metadata_only_commit_pinned_and_bounded(self) -> None:
        self.assertTrue(self.contract["projection"]["metadata_only"])
        self.assertFalse(self.contract["projection"]["copy_upstream_skill_body"])
        floors = {row["id"]: row for row in self.index["source_floor"]}
        self.assertEqual(set(floors), {"deepseek-harness", "prompts-chat", "mattpocock-skills"})
        self.assertEqual(floors["prompts-chat"]["enumeration"], "catalog_csv")
        self.assertEqual(floors["prompts-chat"]["catalog_path"], "prompts.csv")
        self.assertGreaterEqual(int(floors["prompts-chat"]["catalog_entry_count"]), 1)
        self.assertEqual(int(floors["prompts-chat"]["resource_count"]), 0)
        self.assertEqual(floors["prompts-chat"]["search_mode"], "on_demand")
        self.assertEqual(int(self.index["summary"]["catalog_entries_indexed"]), 0)
        self.assertLessEqual(len(self.index["resources"]), self.contract["projection"]["maximum_entries"])
        self.assertLessEqual(INDEX.stat().st_size, self.contract["projection"]["maximum_index_bytes"])
        for resource in self.index["resources"]:
            self.assertNotEqual(resource["source_id"], "prompts-chat")
            floor = floors[resource["source_id"]]
            self.assertEqual(resource["source_sha"], floor["resolved_sha"])
            self.assertNotIn("copyContent", resource)
            self.assertNotIn("body", resource)
            self.assertNotIn("contentPreview", resource)
            self.assertIn(f"/blob/{floor['resolved_sha']}/", resource["url"])
            self.assertLessEqual(
                len(resource["search_terms"]),
                self.contract["projection"]["maximum_search_terms_per_resource"],
            )

    def test_missing_coverage_points_external_and_routes_prompt_review(self) -> None:
        external = [r for r in self.index["resources"] if r["coverage"]["disposition"] == "POINT_TO_EXTERNAL"]
        self.assertEqual(len(external), len(self.gaps["actions"]))
        self.assertFalse(self.gaps["policy"]["automatic_prompt_authoring"])
        self.assertEqual(self.gaps["policy"]["promotion_owner_prompt"], "P79")
        for resource in external:
            self.assertEqual(resource["coverage"]["prompt_action"], "REVIEW_ADD_PROMPT")
            self.assertNotEqual(resource["source_id"], "prompts-chat")
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

    def test_catalog_search_fixture_is_deterministic_and_non_authoring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "prompts.csv"
            fixture.write_text(FIXTURE_CSV, encoding="utf-8")
            before_index = INDEX.read_text(encoding="utf-8")
            before_gaps = GAPS.read_text(encoding="utf-8")
            result = catalog_search.search_catalog(
                contract=self.contract,
                source=next(item for item in self.contract["sources"] if item["id"] == "prompts-chat"),
                query_text="code review regressions",
                limit=5,
                sha="fixture",
                catalog_file=fixture,
            )
            self.assertEqual(result["schema_version"], "operant-external-catalog-search/v1")
            self.assertFalse(result["automatic_prompt_authoring"])
            self.assertGreaterEqual(result["hit_count"], 1)
            self.assertEqual(result["hits"][0]["title"], "Code Review")
            self.assertIn(result["hits"][0]["disposition"], {"REFERENCE_ONLY", "ADAPT"})
            self.assertEqual(result["hits"][0]["prompt_action"], "NO_AUTO_AUTHOR")
            self.assertEqual(INDEX.read_text(encoding="utf-8"), before_index)
            self.assertEqual(GAPS.read_text(encoding="utf-8"), before_gaps)

    def test_catalog_search_cli_keeps_ci_defaults_off_ordinary_search(self) -> None:
        search_cfg = self.contract["catalog_search"]
        self.assertEqual(
            catalog_search.resolve_cli_search_inputs(
                live_proof=False,
                source=None,
                query="linux terminal",
                limit=None,
                catalog_cfg=search_cfg,
            ),
            ("prompts-chat", "linux terminal", 10),
        )
        self.assertEqual(
            catalog_search.resolve_cli_search_inputs(
                live_proof=True,
                source=None,
                query=None,
                limit=None,
                catalog_cfg=search_cfg,
            ),
            ("prompts-chat", str(search_cfg["ci_proof_query"]), int(search_cfg["ci_proof_limit"])),
        )
        with self.assertRaises(ValueError):
            catalog_search.resolve_cli_search_inputs(
                live_proof=False,
                source=None,
                query=None,
                limit=None,
                catalog_cfg=search_cfg,
            )
        with self.assertRaises(ValueError):
            catalog_search.resolve_cli_search_inputs(
                live_proof=True,
                source=None,
                query=None,
                limit=0,
                catalog_cfg=search_cfg,
            )
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "prompts.csv"
            fixture.write_text(FIXTURE_CSV, encoding="utf-8")
            self.assertEqual(
                catalog_search.main(["--catalog-file", str(fixture), "--summary"]),
                2,
            )

    def test_catalog_search_live_proof_budget_is_contracted_and_enforced(self) -> None:
        search_cfg = self.contract["catalog_search"]
        self.assertEqual(search_cfg["default_source_id"], "prompts-chat")
        self.assertGreater(float(search_cfg["maximum_live_search_seconds"]), 0)
        self.assertTrue(search_cfg["live_proof_required_in_refresh_workflow"])
        self.assertTrue(str(search_cfg["ci_proof_query"]).strip())
        workflow = (ROOT / ".github" / "workflows" / "operant-external-resource-refresh.yml").read_text(encoding="utf-8")
        active_workflow = validator.active_workflow_text(workflow)
        self.assertIn("scripts/search_operant_external_catalog.py", active_workflow)
        self.assertIn("--live-proof", active_workflow)
        self.assertIn("catalog-search-live-proof.json", active_workflow)
        self.assertEqual(catalog_search.live_fetch_timeout_seconds(30), 30)
        self.assertEqual(catalog_search.live_fetch_timeout_seconds(0.4), 1)
        with self.assertRaises(ValueError):
            catalog_search.catalog_search_budget_seconds({}, float("inf"))
        with self.assertRaises(ValueError):
            catalog_search.catalog_search_budget_seconds({}, float("nan"))
        with self.assertRaises(validator.ValidationError):
            validator.require_finite_positive("nan", "catalog_search.maximum_live_search_seconds")
        with self.assertRaises(validator.ValidationError):
            validator.require_finite_positive("30", "catalog_search.maximum_live_search_seconds")
        with self.assertRaises(validator.ValidationError):
            validator.require_finite_positive(True, "catalog_search.maximum_live_search_seconds")
        with self.assertRaises(validator.ValidationError):
            validator.require_positive_int(-1, "catalog_search.ci_proof_limit")
        with self.assertRaises(validator.ValidationError):
            validator.require_positive_int(True, "catalog_search.ci_proof_limit")
        self.assertNotIn(
            "--live-proof",
            validator.active_workflow_text("# python scripts/search_operant_external_catalog.py --live-proof\n"),
        )
        self.assertNotIn(
            "--live-proof",
            validator.active_workflow_text("echo ignored # --live-proof catalog-search-live-proof.json\n"),
        )
        boundary = catalog_search.build_live_proof_receipt(
            contract=self.contract,
            result={
                "source_id": "prompts-chat",
                "query": "code review",
                "resolved_sha": "fixture",
                "catalog_path": "prompts.csv",
                "catalog_entry_count": 3,
                "hit_count": 1,
                "hits": [{"title": "Code Review"}],
            },
            elapsed_seconds=30.0004,
            budget_seconds=30,
            mode="fixture",
        )
        self.assertEqual(boundary["elapsed_seconds"], 30.0)
        self.assertFalse(boundary["within_budget"])
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "prompts.csv"
            fixture.write_text(FIXTURE_CSV, encoding="utf-8")
            receipt_path = Path(tmp) / "receipt.json"
            code = catalog_search.main([
                "--catalog-file",
                str(fixture),
                "--live-proof",
                "--summary",
                "--max-seconds",
                "5",
                "--receipt-output",
                str(receipt_path),
            ])
            self.assertEqual(code, 0)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["schema_version"], "operant-external-catalog-search-live-proof/v1")
            self.assertEqual(receipt["mode"], "fixture")
            self.assertEqual(receipt["query"], str(search_cfg["ci_proof_query"]))
            self.assertTrue(receipt["within_budget"])
            self.assertLessEqual(float(receipt["elapsed_seconds"]), float(receipt["budget_seconds"]))
            over_budget = catalog_search.main([
                "--catalog-file",
                str(fixture),
                "--live-proof",
                "--max-seconds",
                "0.000001",
            ])
            self.assertEqual(over_budget, 1)

    def test_full_validator_accepts_current_projection(self) -> None:
        result = validator.validate()
        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["lazy_fetch"])
        self.assertEqual(result["resources"], len(self.index["resources"]))
        self.assertEqual(result["catalog_sources"], 1)


if __name__ == "__main__":
    unittest.main()
