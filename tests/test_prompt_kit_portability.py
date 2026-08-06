from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"


class PromptKitPortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.builder = BUILDER.read_text(encoding="utf-8")
        cls.site = SITE.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_standard_ai_context_and_execution_loop_are_fail_closed(self) -> None:
        self.assertEqual(self.policy["prompt_surface"], "standard-ai")
        self.assertEqual(
            set(self.policy["required_context"]),
            {
                "repository",
                "branch_or_worktree",
                "pr_or_sprint",
                "lane",
                "owned_scope",
                "forbidden_scope",
                "expected_artifacts",
                "validation_order",
            },
        )
        self.assertEqual(
            self.policy["execution_loop"],
            [
                "request",
                "evidence_review",
                "bounded_decision",
                "repository_or_github_mutation",
                "artifacts",
                "validation",
                "report",
                "next_decision",
            ],
        )
        fallback = self.policy["directory_gate"]["connected_github_fallback"]
        self.assertEqual(fallback["allowed_when"], "network_clone_unavailable")
        self.assertEqual(fallback["mutation_surface"], "connected_github_branch")
        self.assertEqual(
            fallback["bounded_local_reconstruction"],
            ["generator", "validator", "focused_tests"],
        )

    def test_prompt_library_link_and_sparse_navigation_contract(self) -> None:
        prompt_library = self.policy["artifact_rules"]["prompt_library"]
        self.assertEqual(
            prompt_library["linked_prompt_columns"],
            [chr(code) for code in range(ord("B"), ord("O") + 1)],
        )
        self.assertEqual(prompt_library["reserved_navigation_columns"], ["A", "P"])
        sparse = prompt_library["sparse_navigation"]
        self.assertEqual(sparse["allowed_cadences"], [10, 5, 2])
        self.assertTrue(sparse["fail_closed_when_no_allowed_divisor"])

        def cadence(count: int) -> int:
            for value in sparse["allowed_cadences"]:
                if count % value == 0:
                    return value
            raise ValueError("no allowed cadence")

        self.assertEqual(cadence(60), 10)
        self.assertEqual(cadence(30), 10)
        self.assertEqual(cadence(14), 2)
        with self.assertRaises(ValueError):
            cadence(13)

    def test_sequential_prompt_suite_is_exact(self) -> None:
        self.assertEqual(
            self.policy["sequential_prompt_suite"],
            {
                "P03": "unknown_repository_intake_and_first_action",
                "P06": "repository_and_pr_cleanup",
                "P07": "general_implementation",
                "P14": "broken_pr_repair",
                "P15": "merge_or_release",
                "P20": "selected_opportunity_discovery_row",
                "P12": "closeout",
            },
        )

    def test_builder_embeds_portability_runtime_and_site_is_current(self) -> None:
        self.assertIn("PORTABILITY_RUNTIME", self.builder)
        self.assertIn("_embed_portability_runtime", self.builder)
        self.assertIn("html.count(marker) != 1", self.builder)
        for marker in (
            "prompt-kit-favorites/v1",
            "favoritePortabilityControls",
            "Export Favorites",
            "Import Favorites",
        ):
            self.assertIn(marker, self.runtime)
            self.assertIn(marker, self.site)

    def test_runtime_payload_merge_legacy_and_rejection_behavior(self) -> None:
        node_script = r"""
const fs=require('fs');
globalThis.PROMPTS=[{id:'P03'},{id:'P06'},{id:'P07'}];
globalThis.favoritePromptIds={P03:true};
globalThis.localStorage={data:{},getItem(k){return this.data[k]||null},setItem(k,v){this.data[k]=v}};
globalThis.saveFavoritePromptIds=function(){globalThis.saved=true};
globalThis.render=function(){globalThis.rendered=true};
const source=fs.readFileSync('docs/prompt-kit-favorites-portability.js','utf8');
eval(source);
const api=globalThis.PromptKitFavoritesPortability;
const payload=api.buildPayload();
if(payload.schema_version!=='prompt-kit-favorites/v1')throw new Error('schema');
if(JSON.stringify(payload.favorite_prompt_ids)!=='["P03"]')throw new Error('export ids');
const parsed=api.parsePayload(JSON.stringify({schema_version:'prompt-kit-favorites/v1',favorite_prompt_ids:['p06','P03','P999','P06']}));
if(JSON.stringify(parsed.favorite_prompt_ids)!=='["P03","P06","P999"]')throw new Error('normalize');
const result=api.mergeFavorites(parsed.favorite_prompt_ids);
if(!globalThis.favoritePromptIds.P03||!globalThis.favoritePromptIds.P06||!globalThis.favoritePromptIds.P999)throw new Error('merge');
if(JSON.stringify(result.unknown_prompt_ids)!=='["P999"]')throw new Error('unknown preservation');
const legacy=api.parsePayload('["p07","P03"]');
if(legacy.schema_version!=='legacy-array/v0')throw new Error('legacy');
let rejected=false;
try{api.parsePayload(JSON.stringify({schema_version:'wrong/v1',favorite_prompt_ids:[]}))}catch(error){rejected=true}
if(!rejected)throw new Error('schema rejection');
rejected=false;
try{api.parsePayload(' '.repeat(65537))}catch(error){rejected=true}
if(!rejected)throw new Error('size rejection');
console.log('PORTABILITY_RUNTIME_PASS');
"""
        completed = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PORTABILITY_RUNTIME_PASS", completed.stdout)

    def test_workflow_executes_portability_gate(self) -> None:
        for marker in (
            "docs/prompt-kit-favorites-portability.js",
            "harness/contracts/prompt-kit-portability.v1.json",
            "scripts/validate_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability.py",
            "Validate portable Favorites and harness discipline",
        ):
            self.assertIn(marker, self.workflow)


if __name__ == "__main__":
    unittest.main()
