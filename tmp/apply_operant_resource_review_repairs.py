#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Portable artifact must package the resource sidecar beside index.html.
portable = ROOT / "scripts" / "serve_prompt_kit_portable.py"
replace_once(
    portable,
    'CLOSING_BODY = "</body>"\n',
    'CLOSING_BODY = "</body>"\nRESOURCE_INDEX_NAME = "resources.v1.json"\n',
)
replace_once(
    portable,
    '    require_output_path(repo_root, output_path)\n    require_output_path(repo_root, manifest_path)\n\n    source_bytes = require_file(source_path, "canonical Prompt Kit site")\n    runtime_bytes = require_file(runtime_path, "portable Favorites runtime")\n',
    '    require_output_path(repo_root, output_path)\n    require_output_path(repo_root, manifest_path)\n    resource_source_path = source_path.parent / RESOURCE_INDEX_NAME\n    resource_output_path = output_path.parent / RESOURCE_INDEX_NAME\n    require_output_path(repo_root, resource_output_path)\n\n    source_bytes = require_file(source_path, "canonical Prompt Kit site")\n    runtime_bytes = require_file(runtime_path, "portable Favorites runtime")\n    resource_bytes = require_file(resource_source_path, "canonical Operant resource index")\n',
)
replace_once(
    portable,
    '    artifact_backup = backup_existing_output(repo_root, output_path)\n    output_path.parent.mkdir(parents=True, exist_ok=True)\n    output_path.write_bytes(artifact_bytes)\n\n    receipt: dict[str, Any] = {\n',
    '    artifact_backup = backup_existing_output(repo_root, output_path)\n    resource_backup = backup_existing_output(repo_root, resource_output_path)\n    output_path.parent.mkdir(parents=True, exist_ok=True)\n    output_path.write_bytes(artifact_bytes)\n    resource_output_path.write_bytes(resource_bytes)\n\n    receipt: dict[str, Any] = {\n',
)
replace_once(
    portable,
    '        "artifact": {\n            "path": str(output_path.relative_to(repo_root)),\n            "sha256": sha256_bytes(artifact_bytes),\n            "bytes": len(artifact_bytes),\n        },\n        "backups": {\n            "artifact": str(artifact_backup.relative_to(repo_root)) if artifact_backup else None,\n            "manifest": None,\n        },\n',
    '        "artifact": {\n            "path": str(output_path.relative_to(repo_root)),\n            "sha256": sha256_bytes(artifact_bytes),\n            "bytes": len(artifact_bytes),\n        },\n        "resource_index": {\n            "source_path": str(resource_source_path.relative_to(repo_root)),\n            "path": str(resource_output_path.relative_to(repo_root)),\n            "sha256": sha256_bytes(resource_bytes),\n            "bytes": len(resource_bytes),\n        },\n        "backups": {\n            "artifact": str(artifact_backup.relative_to(repo_root)) if artifact_backup else None,\n            "resource_index": str(resource_backup.relative_to(repo_root)) if resource_backup else None,\n            "manifest": None,\n        },\n',
)
replace_once(
    portable,
    '            "health_hash_matches_served_artifact": True,\n            "overwrite_backup_required": True,\n',
    '            "health_hash_matches_served_artifact": True,\n            "resource_sidecar_matches_canonical": True,\n            "overwrite_backup_required": True,\n',
)
replace_once(
    portable,
    '    print(f"PROMPT_KIT_PORTABLE_MANIFEST={manifest_path}")\n    print(f"PROMPT_KIT_PORTABLE_URL={origin}")\n',
    '    print(f"PROMPT_KIT_PORTABLE_MANIFEST={manifest_path}")\n    print(f"PROMPT_KIT_PORTABLE_RESOURCES={output_path.parent / RESOURCE_INDEX_NAME}")\n    print(f"PROMPT_KIT_PORTABLE_URL={origin}")\n',
)

# Portability contract + validator now own the sidecar too.
policy_path = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
portable_rule = policy["artifact_rules"]["portable_runtime_artifact"]
portable_rule["resource_sidecar"] = "Outputs/prompt-kit-portable/resources.v1.json"
policy["integration"]["external_resource_sidecar"] = "web/prompt-kit/resources.v1.json"
policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

validator = ROOT / "scripts" / "validate_prompt_kit_portability.py"
replace_once(
    validator,
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\n',
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\nRESOURCE_INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"\n',
)
replace_once(
    validator,
    '    if runtime_artifact.get("manifest") != "Outputs/prompt-kit-portable/manifest.json":\n        fail("portable artifact manifest path drift")\n',
    '    if runtime_artifact.get("manifest") != "Outputs/prompt-kit-portable/manifest.json":\n        fail("portable artifact manifest path drift")\n    if runtime_artifact.get("resource_sidecar") != "Outputs/prompt-kit-portable/resources.v1.json":\n        fail("portable resource sidecar path drift")\n',
)
replace_once(
    validator,
    '    artifact_bytes = artifact_path.read_bytes()\n    runtime = runtime_bytes.decode("utf-8").strip()\n',
    '    artifact_bytes = artifact_path.read_bytes()\n    resource_path = artifact_path.parent / "resources.v1.json"\n    if not resource_path.is_file():\n        fail(f"portable resource sidecar is missing: {resource_path}")\n    canonical_resource_bytes = RESOURCE_INDEX.read_bytes()\n    resource_bytes = resource_path.read_bytes()\n    if resource_bytes != canonical_resource_bytes:\n        fail("portable resource sidecar differs from tracked canonical index")\n    runtime = runtime_bytes.decode("utf-8").strip()\n',
)
replace_once(
    validator,
    '        "artifact": sha256_bytes(artifact_bytes),\n    }\n',
    '        "artifact": sha256_bytes(artifact_bytes),\n        "resource_index": sha256_bytes(resource_bytes),\n    }\n',
)
replace_once(
    validator,
    '        "canonical_site_untouched",\n        "overwrite_backup_required",\n',
    '        "canonical_site_untouched",\n        "resource_sidecar_matches_canonical",\n        "overwrite_backup_required",\n',
)
replace_once(
    validator,
    '        "bytes": len(artifact_bytes),\n    }\n\n\ndef validate_repository_surfaces',
    '        "bytes": len(artifact_bytes),\n        "resource_index": str(resource_path),\n        "resource_index_sha256": expected_hashes["resource_index"],\n        "resource_index_bytes": len(resource_bytes),\n    }\n\n\ndef validate_repository_surfaces',
)
replace_once(
    validator,
    '            "build_portable_artifact",\n            "Cache-Control",\n',
    '            "build_portable_artifact",\n            "RESOURCE_INDEX_NAME",\n            "resource_sidecar_matches_canonical",\n            "PROMPT_KIT_PORTABLE_RESOURCES",\n            "Cache-Control",\n',
)

# GitHub Pages package must ship and byte-check the sidecar.
pages = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
replace_once(
    pages,
    '          python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\n          cp -R web/prompt-kit-mobile/. "$SITE_ROOT/"\n',
    '          python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\n          cp web/prompt-kit/resources.v1.json "$SITE_ROOT/prompt-kit/resources.v1.json"\n          cp -R web/prompt-kit-mobile/. "$SITE_ROOT/"\n',
)
replace_once(
    pages,
    '          test -s "$SITE_ROOT/prompt-kit/index.html"\n          test -s "$SITE_ROOT/roster-log-v2/index.html"\n',
    '          test -s "$SITE_ROOT/prompt-kit/index.html"\n          test -s "$SITE_ROOT/prompt-kit/resources.v1.json"\n          test -s "$SITE_ROOT/roster-log-v2/index.html"\n',
)
replace_once(
    pages,
    '          cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\n          cmp "$SITE_ROOT/roster-log-v2/index.html" web/roster-log-v2/index.html\n',
    '          cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\n          cmp "$SITE_ROOT/prompt-kit/resources.v1.json" web/prompt-kit/resources.v1.json\n          cmp "$SITE_ROOT/roster-log-v2/index.html" web/roster-log-v2/index.html\n',
)

# Pages contract test protects packaged-sidecar parity.
pages_test = ROOT / "tests" / "test_prompt_kit_pages.py"
replace_once(
    pages_test,
    '            \'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\',\n            \'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\',\n',
    '            \'python scripts/build_prompt_kit_registry.py --output "$SITE_ROOT/prompt-kit/index.html"\',\n            \'cp web/prompt-kit/resources.v1.json "$SITE_ROOT/prompt-kit/resources.v1.json"\',\n            \'test -s "$SITE_ROOT/prompt-kit/resources.v1.json"\',\n            \'cmp "$SITE_ROOT/prompt-kit/index.html" web/prompt-kit/index.html\',\n            \'cmp "$SITE_ROOT/prompt-kit/resources.v1.json" web/prompt-kit/resources.v1.json\',\n',
)

# Portable focused test proves the actual copied bytes and receipt.
portable_test = ROOT / "tests" / "test_prompt_kit_portability.py"
replace_once(
    portable_test,
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\n',
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\nRESOURCE_INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"\n',
)
replace_once(
    portable_test,
    '            self.assertTrue(receipt["guardrails"]["canonical_site_untouched"])\n            self.assertTrue(receipt["guardrails"]["overwrite_backup_required"])\n            validated = validator.validate_artifact(artifact, manifest)\n',
    '            resource_artifact = artifact.parent / "resources.v1.json"\n            self.assertEqual(resource_artifact.read_bytes(), RESOURCE_INDEX.read_bytes())\n            self.assertEqual(receipt["resource_index"]["path"], str(resource_artifact.relative_to(ROOT)))\n            self.assertTrue(receipt["guardrails"]["canonical_site_untouched"])\n            self.assertTrue(receipt["guardrails"]["resource_sidecar_matches_canonical"])\n            self.assertTrue(receipt["guardrails"]["overwrite_backup_required"])\n            validated = validator.validate_artifact(artifact, manifest)\n',
)
replace_once(
    portable_test,
    '            self.assertEqual(validated["bytes"], receipt["artifact"]["bytes"])\n',
    '            self.assertEqual(validated["bytes"], receipt["artifact"]["bytes"])\n            self.assertEqual(validated["resource_index_sha256"], receipt["resource_index"]["sha256"])\n',
)

# Resource unit test protects exact packaging markers and strict identity checks.
resource_test = ROOT / "tests" / "test_operant_external_resources.py"
replace_once(
    resource_test,
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\n',
    'SITE = ROOT / "web" / "prompt-kit" / "index.html"\nPAGES_WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"\nPORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"\n',
)
insert = '''\n    def test_release_packages_include_sidecar_without_embedding_records(self) -> None:\n        pages = PAGES_WORKFLOW.read_text(encoding="utf-8")\n        portable = PORTABLE_BUILDER.read_text(encoding="utf-8")\n        self.assertIn('cp web/prompt-kit/resources.v1.json "$SITE_ROOT/prompt-kit/resources.v1.json"', pages)\n        self.assertIn('cmp "$SITE_ROOT/prompt-kit/resources.v1.json" web/prompt-kit/resources.v1.json', pages)\n        self.assertIn('RESOURCE_INDEX_NAME = "resources.v1.json"', portable)\n        self.assertIn('resource_sidecar_matches_canonical', portable)\n\n'''
marker = '    def test_token_match_is_deterministic_and_conservative(self) -> None:\n'
text = resource_test.read_text(encoding="utf-8")
if 'test_release_packages_include_sidecar_without_embedding_records' not in text:
    if marker not in text:
        raise SystemExit("resource test insertion anchor missing")
    resource_test.write_text(text.replace(marker, insert + marker, 1), encoding="utf-8")

# Browser proof: current tracked root + >40 pagination + actual portable package.
browser = ROOT / "tests" / "prompt_kit_external_resources_browser_proof.py"
replace_once(
    browser,
    'import subprocess\nimport threading\n',
    'import subprocess\nimport sys\nimport threading\n',
)
replace_once(
    browser,
    '    source_shas = {row["id"]: row["resolved_sha"] for row in expected["source_floor"]}\n    resource_requests: list[str] = []\n',
    '    source_shas = {row["id"]: row["resolved_sha"] for row in expected["source_floor"]}\n    portable_root = ROOT / "Outputs" / "observed-proof" / "external-resource-portable"\n    portable_root.mkdir(parents=True, exist_ok=True)\n    subprocess.run(\n        [\n            sys.executable,\n            str(ROOT / "scripts" / "serve_prompt_kit_portable.py"),\n            "--build-only",\n            "--output",\n            str(portable_root / "index.html"),\n            "--manifest",\n            str(portable_root / "manifest.json"),\n        ],\n        cwd=ROOT,\n        check=True,\n        capture_output=True,\n        text=True,\n    )\n    resource_requests: list[str] = []\n',
)
replace_once(
    browser,
    '            page.keyboard.press("Escape")\n            closed_by_escape = page.locator("#operantExternalResources").evaluate("el => el.hidden")\n            screenshot.parent.mkdir(parents=True, exist_ok=True)\n',
    '''            search.fill("")\n            page.evaluate("""() => {\n              const base=window.externalResourceIndex.resources.slice();\n              const expanded=[];\n              for(let i=0;i<85;i++){const source=base[i%base.length];expanded.push(Object.assign({},source,{id:source.id+'-proof-'+i,title:source.title+' proof '+i}))}\n              window.externalResourceIndex=Object.assign({},window.externalResourceIndex,{summary:Object.assign({},window.externalResourceIndex.summary,{resource_count:85}),resources:expanded});\n              window.externalResourcePage=0;\n              window.OperantExternalResources.render();\n            }""")\n            first_page_rows = page.locator(".operant-resource-row").count()\n            page.locator(".operant-resource-next").click()\n            second_page_rows = page.locator(".operant-resource-row").count()\n            page.locator(".operant-resource-next").click()\n            third_page_rows = page.locator(".operant-resource-row").count()\n            page.locator(".operant-resource-prev").click()\n            previous_page_rows = page.locator(".operant-resource-row").count()\n\n            page.keyboard.press("Escape")\n            closed_by_escape = page.locator("#operantExternalResources").evaluate("el => el.hidden")\n\n            portable_request_floor = len(resource_requests)\n            page.goto(f"http://127.0.0.1:{port}/Outputs/observed-proof/external-resource-portable/index.html",wait_until="domcontentloaded")\n            page.wait_for_timeout(100)\n            portable_initial_requests = len(resource_requests)-portable_request_floor\n            page.locator("#externalResourcesButton").click()\n            page.wait_for_function(\n                """expected => {const count=document.querySelector('.operant-resource-count');return !!(count && count.textContent.includes(expected+' indexed'));}""",\n                arg=expected_count,\n                timeout=5000,\n            )\n            portable_loaded_requests = len(resource_requests)-portable_request_floor\n            portable_rows = page.locator(".operant-resource-row").count()\n\n            screenshot.parent.mkdir(parents=True, exist_ok=True)\n''',
)
replace_once(
    browser,
    '        {\n            "id": "escape_closes_resources",\n',
    '''        {\n            "id": "pagination_remains_bounded",\n            "event": "next/previous pagination never renders more than one configured resource page",\n            "occurred": True,\n            "passed": first_page_rows == 40 and second_page_rows == 40 and third_page_rows == 5 and previous_page_rows == 40,\n            "first_page_rows": first_page_rows,\n            "second_page_rows": second_page_rows,\n            "third_page_rows": third_page_rows,\n            "previous_page_rows": previous_page_rows,\n            "synthetic_catalog_count": 85,\n        },\n        {\n            "id": "portable_package_serves_sidecar",\n            "event": "portable packaging includes the canonical resource sidecar and keeps lazy loading",\n            "occurred": True,\n            "passed": portable_initial_requests == 0 and portable_loaded_requests == 1 and portable_rows == expected_page,\n            "initial_resource_requests": portable_initial_requests,\n            "loaded_resource_requests": portable_loaded_requests,\n            "rendered_rows": portable_rows,\n        },\n        {\n            "id": "escape_closes_resources",\n''',
)
replace_once(
    browser,
    '            "status": "PASS" if by_id["render_is_bounded"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["render_is_bounded"],\n',
    '            "status": "PASS" if by_id["render_is_bounded"]["passed"] and by_id["pagination_remains_bounded"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["render_is_bounded", "pagination_remains_bounded"],\n',
)
replace_once(
    browser,
    '            "status": "PASS" if by_id["search_preserves_pinned_source_navigation"]["passed"] and by_id["escape_closes_resources"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["search_preserves_pinned_source_navigation", "escape_closes_resources"],\n',
    '            "status": "PASS" if by_id["search_preserves_pinned_source_navigation"]["passed"] and by_id["portable_package_serves_sidecar"]["passed"] and by_id["escape_closes_resources"]["passed"] else "FAIL",\n            "required_evidence_class": "browser_runtime_observed",\n            "observation_ids": ["search_preserves_pinned_source_navigation", "portable_package_serves_sidecar", "escape_closes_resources"],\n',
)

print("OPERANT_RESOURCE_REVIEW_REPAIRS_APPLIED=1")
