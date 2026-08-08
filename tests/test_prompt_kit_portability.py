from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
CANONICAL_BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
PORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"
VALIDATOR = ROOT / "scripts" / "validate_prompt_kit_portability.py"
PORTABLE_LAUNCHER = ROOT / "scripts" / "Open-LatestPromptKitPortable.ps1"
WINDOWS_ENTRY = ROOT / "Open-Latest-PromptKit.cmd"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
EXPECTED_ORIGIN = "http://127.0.0.1:8765/"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PromptKitPortabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(POLICY.read_text(encoding="utf-8"))
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.canonical_builder = CANONICAL_BUILDER.read_text(encoding="utf-8")
        cls.portable_builder = PORTABLE_BUILDER.read_text(encoding="utf-8")
        cls.portable_launcher = PORTABLE_LAUNCHER.read_text(encoding="utf-8")
        cls.windows_entry = WINDOWS_ENTRY.read_text(encoding="utf-8")
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

    def test_favorites_stable_origin_and_transfer_contract(self) -> None:
        favorites = self.policy["favorites_portability"]
        self.assertEqual(favorites["stable_origin"], EXPECTED_ORIGIN)
        self.assertEqual(favorites["browser_storage_key"], "promptKit.favoritePromptIds.v1")
        self.assertEqual(favorites["export_schema"], "prompt-kit-favorites/v1")
        self.assertEqual(favorites["max_import_bytes"], 65536)
        self.assertEqual(favorites["controls"], ["Export Favorites", "Import Favorites"])
        self.assertIn("bind_loopback_only", favorites["security"])
        self.assertIn("disable_browser_cache", favorites["security"])
        self.assertIn("never_execute_imported_content", favorites["security"])

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

    def test_portable_builder_preserves_canonical_site_and_emits_receipt(self) -> None:
        portable = load_module("prompt_kit_portable_builder", PORTABLE_BUILDER)
        validator = load_module("prompt_kit_portability_validator", VALIDATOR)
        outputs = ROOT / "Outputs"
        outputs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=outputs) as temporary:
            temporary_path = Path(temporary)
            artifact = temporary_path / "index.html"
            manifest = temporary_path / "manifest.json"
            source_before = SITE.read_bytes()
            receipt = portable.build_portable_artifact(
                repo_root=ROOT,
                source_path=SITE,
                runtime_path=RUNTIME,
                output_path=artifact,
                manifest_path=manifest,
                origin=EXPECTED_ORIGIN,
            )
            self.assertEqual(SITE.read_bytes(), source_before)
            artifact_text = artifact.read_text(encoding="utf-8")
            for marker in (
                "prompt-kit-favorites/v1",
                "favoritePortabilityControls",
                "Export Favorites",
                "Import Favorites",
                "Tutorial · Find My Prompt",
                "prompt-card-actions",
            ):
                self.assertIn(marker, artifact_text)
            self.assertEqual(receipt["stable_origin"], EXPECTED_ORIGIN)
            self.assertTrue(receipt["guardrails"]["canonical_site_untouched"])
            self.assertTrue(receipt["guardrails"]["overwrite_backup_required"])
            validated = validator.validate_artifact(artifact, manifest)
            self.assertEqual(validated["sha256"], receipt["artifact"]["sha256"])
            self.assertEqual(validated["bytes"], receipt["artifact"]["bytes"])

    def test_existing_generated_output_is_backed_up_before_replacement(self) -> None:
        portable = load_module("prompt_kit_portable_backup", PORTABLE_BUILDER)
        with tempfile.TemporaryDirectory() as temporary:
            repo_root = Path(temporary)
            output = repo_root / "Outputs" / "prompt-kit-portable" / "index.html"
            output.parent.mkdir(parents=True)
            output.write_text("old portable artifact", encoding="utf-8")
            backup = portable.backup_existing_output(repo_root, output)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertTrue(backup.is_file())
            self.assertEqual(backup.read_text(encoding="utf-8"), "old portable artifact")
            self.assertTrue(
                backup.is_relative_to(repo_root / "Outputs" / "backups" / "prompt-kit-portable")
            )

    def test_portable_builder_rejects_duplicate_injection_and_non_loopback(self) -> None:
        portable = load_module("prompt_kit_portable_builder_rejection", PORTABLE_BUILDER)
        outputs = ROOT / "Outputs"
        outputs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=outputs) as temporary:
            temporary_path = Path(temporary)
            duplicate = temporary_path / "duplicate.html"
            duplicate.write_text(
                "<html><body><script>prompt-kit-favorites/v1</script></body></html>",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate injection"):
                portable.build_portable_artifact(
                    repo_root=ROOT,
                    source_path=duplicate,
                    runtime_path=RUNTIME,
                    output_path=temporary_path / "output.html",
                    manifest_path=temporary_path / "manifest.json",
                    origin=EXPECTED_ORIGIN,
                )
        self.assertEqual(
            portable.main(
                [
                    "--repo-root",
                    str(ROOT),
                    "--host",
                    "0.0.0.0",
                    "--build-only",
                ]
            ),
            2,
        )

    def test_runtime_payload_merge_legacy_and_rejection_behavior(self) -> None:
        node_script = r"""
const fs=require('fs');
globalThis.PROMPTS=[{id:'P03'},{id:'P06'},{id:'P07'}];
globalThis.favoritePromptIds={P03:true};
globalThis.localStorage={data:{},getItem(k){return this.data[k]||null},setItem(k,v){this.data[k]=v},removeItem(k){delete this.data[k]}};
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

    def test_launcher_reuses_pinned_acquisition_and_opens_stable_origin(self) -> None:
        for marker in (
            "$StableHost = '127.0.0.1'",
            '$StableUrl = "http://${StableHost}:$Port/"',
            "$AcquireBootstrapCommit = 'd61ff0c165c5647f4607a32e85e1171d6b898501'",
            "$AcquireBootstrapBlob = '674130635ed70b5e57a3784f26511d932f63adb3'",
            "Import-AcquisitionFunctions",
            "Update-RepositorySafely",
            "serve_prompt_kit_portable.py",
            "validate_prompt_kit_portability.py",
            "Start-PortableServer",
        ):
            self.assertIn(marker, self.portable_launcher)
        for marker in (
            "BOOTSTRAP_COMMIT=9c7809cfe4dab62bb30b5ba9d12f6e204125d03c",
            "BOOTSTRAP_BLOB=b6e4f1fd2d2771370d3b23d355a7a0f4301aa2bc",
            "api.github.com/repos/EndeavorEverlasting/web-excel-repair-triage/contents/scripts/Open-LatestPromptKitPortable.ps1",
        ):
            self.assertIn(marker, self.windows_entry)
        self.assertIn("Open-LatestPromptKitPortable.ps1", self.windows_entry)
        self.assertNotIn("raw.githubusercontent.com/EndeavorEverlasting/web-excel-repair-triage/main/scripts/Open-LatestPromptKitPortable.ps1", self.windows_entry)

    def test_powershell_launcher_parses_when_pwsh_is_available(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        if not pwsh:
            self.skipTest("PowerShell is not installed in this test environment")
        command = (
            "$ErrorActionPreference='Stop';"
            "$null=[scriptblock]::Create((Get-Content -Raw "
            "'scripts/Open-LatestPromptKitPortable.ps1'));"
            "Write-Host 'PORTABLE_POWERSHELL_PARSE_PASS'"
        )
        completed = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-Command", command],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("PORTABLE_POWERSHELL_PARSE_PASS", completed.stdout)

    def test_canonical_builder_and_site_remain_separate_from_runtime_injection(self) -> None:
        self.assertIn("build_prompt_kit.build_html", self.canonical_builder)
        self.assertNotIn("_embed_portability_runtime", self.canonical_builder)
        self.assertNotIn("prompt-kit-favorites/v1", self.site)
        self.assertIn("AI Harness Prompt Kit", self.site)

    def test_workflow_builds_uploads_and_validates_portable_artifact(self) -> None:
        for marker in (
            "scripts/serve_prompt_kit_portable.py",
            "scripts/validate_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability_regressions.py",
            "Build portable Prompt Kit runtime artifact",
            "Validate portable Favorites and harness discipline",
            "prompt-kit-portable-runtime",
        ):
            self.assertIn(marker, self.workflow)


if __name__ == "__main__":
    unittest.main()
