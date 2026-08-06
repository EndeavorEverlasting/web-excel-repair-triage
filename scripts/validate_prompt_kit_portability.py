#!/usr/bin/env python3
"""Fail-closed Prompt Kit portability contract validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"
DOCTRINE = ROOT / "docs" / "PROMPT_KIT_PORTABILITY.md"
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
CANONICAL_BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
PORTABLE_BUILDER = ROOT / "scripts" / "serve_prompt_kit_portable.py"
PORTABLE_LAUNCHER = ROOT / "scripts" / "Open-LatestPromptKitPortable.ps1"
WINDOWS_ENTRY = ROOT / "Open-Latest-PromptKit.cmd"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
HARNESS_MANIFEST = ROOT / "harness" / "manifest.v1.json"
README = ROOT / "web" / "README.md"
DEFAULT_ARTIFACT = ROOT / "Outputs" / "prompt-kit-portable" / "index.html"
DEFAULT_ARTIFACT_MANIFEST = ROOT / "Outputs" / "prompt-kit-portable" / "manifest.json"
EXPECTED_ORIGIN = "http://127.0.0.1:8765/"
RUNTIME_MARKER = "prompt-kit-favorites/v1"

REQUIRED_CONTEXT = {
    "repository",
    "branch_or_worktree",
    "pr_or_sprint",
    "lane",
    "owned_scope",
    "forbidden_scope",
    "expected_artifacts",
    "validation_order",
}
EXPECTED_LOOP = [
    "request",
    "evidence_review",
    "bounded_decision",
    "repository_or_github_mutation",
    "artifacts",
    "validation",
    "report",
    "next_decision",
]
EXPECTED_ROUTING = {
    "P03": "unknown_repository_intake_and_first_action",
    "P06": "repository_and_pr_cleanup",
    "P07": "general_implementation",
    "P14": "broken_pr_repair",
    "P15": "merge_or_release",
    "P20": "selected_opportunity_discovery_row",
    "P12": "closeout",
}


def fail(message: str) -> None:
    raise ValueError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path, *, root_relative: bool = True) -> dict[str, Any]:
    if not path.is_file():
        label = str(path.relative_to(ROOT)) if root_relative else str(path)
        fail(f"missing required file: {label}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")
    if not isinstance(payload, dict):
        fail(f"expected JSON object: {path}")
    return payload


def require_text(path: Path, phrases: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            fail(f"{path.relative_to(ROOT)} missing required marker: {phrase}")
    return text


def resolve_runtime_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != "prompt-kit-portability/v1":
        fail("unsupported portability schema")
    if policy.get("prompt_surface") != "standard-ai":
        fail("portability prompt surface must be standard-ai")
    context = set(policy.get("required_context") or [])
    if context != REQUIRED_CONTEXT:
        fail(f"required_context drift: {sorted(context ^ REQUIRED_CONTEXT)}")
    if policy.get("execution_loop") != EXPECTED_LOOP:
        fail("execution loop drift")

    fallback = policy.get("directory_gate", {}).get("connected_github_fallback", {})
    if fallback.get("allowed_when") != "network_clone_unavailable":
        fail("connected GitHub fallback activation drift")
    if fallback.get("mutation_surface") != "connected_github_branch":
        fail("connected GitHub fallback mutation surface drift")
    if fallback.get("bounded_local_reconstruction") != [
        "generator",
        "validator",
        "focused_tests",
    ]:
        fail("connected GitHub reconstruction boundary drift")

    favorites = policy.get("favorites_portability", {})
    if favorites.get("browser_storage_key") != "promptKit.favoritePromptIds.v1":
        fail("favorites storage key drift")
    if favorites.get("stable_origin") != EXPECTED_ORIGIN:
        fail("stable Favorites origin drift")
    if favorites.get("export_schema") != RUNTIME_MARKER:
        fail("favorites export schema drift")
    if favorites.get("max_import_bytes") != 65536:
        fail("favorites import size limit drift")
    if favorites.get("controls") != ["Export Favorites", "Import Favorites"]:
        fail("favorites controls drift")
    if favorites.get("import_behavior") != "merge_deduplicate_normalize_preserve_unknown_ids":
        fail("favorites import behavior drift")
    security = set(favorites.get("security") or [])
    for item in (
        "bind_loopback_only",
        "disable_browser_cache",
        "never_execute_imported_content",
        "never_modify_canonical_site_during_runtime_generation",
    ):
        if item not in security:
            fail(f"missing Favorites security guardrail: {item}")

    runtime_artifact = policy.get("artifact_rules", {}).get(
        "portable_runtime_artifact", {}
    )
    if runtime_artifact.get("path") != "Outputs/prompt-kit-portable/index.html":
        fail("portable artifact path drift")
    if runtime_artifact.get("manifest") != "Outputs/prompt-kit-portable/manifest.json":
        fail("portable artifact manifest path drift")
    if runtime_artifact.get("tracking") != "gitignored_runtime_artifact":
        fail("portable runtime artifact must remain gitignored")

    prompt_library = policy.get("artifact_rules", {}).get("prompt_library", {})
    expected_columns = [chr(code) for code in range(ord("B"), ord("O") + 1)]
    if prompt_library.get("linked_prompt_columns") != expected_columns:
        fail("Prompt Library linked columns must be B:O")
    if prompt_library.get("reserved_navigation_columns") != ["A", "P"]:
        fail("Prompt Library navigation columns must be A and P")
    sparse = prompt_library.get("sparse_navigation", {})
    if sparse.get("allowed_cadences") != [10, 5, 2]:
        fail("sparse navigation cadences must be 10, 5, 2")
    if sparse.get("selection_rule") != "largest_allowed_divisor_evenly_dividing_prompt_count":
        fail("sparse navigation selection rule drift")
    if sparse.get("fail_closed_when_no_allowed_divisor") is not True:
        fail("sparse navigation must fail closed")

    if policy.get("sequential_prompt_suite") != EXPECTED_ROUTING:
        fail("sequential prompt routing drift")


def validate_artifact(artifact_path: Path, manifest_path: Path) -> dict[str, Any]:
    if not artifact_path.is_file():
        fail(f"portable artifact is missing: {artifact_path}")
    manifest = load_json(manifest_path, root_relative=False)
    if manifest.get("schema_version") != "prompt-kit-portable-artifact/v1":
        fail("portable artifact manifest schema drift")
    if manifest.get("stable_origin") != EXPECTED_ORIGIN:
        fail("portable artifact manifest origin drift")

    source_bytes = SITE.read_bytes()
    runtime_bytes = RUNTIME.read_bytes()
    artifact_bytes = artifact_path.read_bytes()
    runtime = runtime_bytes.decode("utf-8").strip()
    source = source_bytes.decode("utf-8")
    if source.count("</script>") != 1:
        fail("canonical site must contain exactly one closing script marker")
    expected = source.replace("</script>", f"\n{runtime}\n</script>", 1).encode("utf-8")
    if artifact_bytes != expected:
        fail("portable artifact is not the exact canonical site plus tracked runtime")
    if RUNTIME_MARKER not in artifact_bytes.decode("utf-8"):
        fail("portable artifact is missing the Favorites runtime")

    expected_hashes = {
        "source": sha256_bytes(source_bytes),
        "runtime": sha256_bytes(runtime_bytes),
        "artifact": sha256_bytes(artifact_bytes),
    }
    for key, expected_hash in expected_hashes.items():
        actual_hash = str(manifest.get(key, {}).get("sha256", ""))
        if actual_hash != expected_hash:
            fail(f"portable artifact manifest {key} hash mismatch")

    guardrails = manifest.get("guardrails", {})
    for key in (
        "loopback_only",
        "cache_disabled",
        "protected_inputs_untouched",
        "canonical_site_untouched",
    ):
        if guardrails.get(key) is not True:
            fail(f"portable artifact manifest guardrail is not true: {key}")

    return {
        "artifact": str(artifact_path),
        "manifest": str(manifest_path),
        "sha256": expected_hashes["artifact"],
        "bytes": len(artifact_bytes),
    }


def validate_repository_surfaces(
    artifact_path: Path | None = None,
    artifact_manifest_path: Path | None = None,
) -> dict[str, Any]:
    policy = load_json(POLICY)
    validate_policy(policy)

    doctrine = require_text(
        DOCTRINE,
        (
            "Standard AI",
            EXPECTED_ORIGIN,
            "Export Favorites",
            "Import Favorites",
            "request -> evidence review -> bounded decision",
            "columns `B:O`",
            "columns `A` and `P`",
            "largest divisor among `10`, `5`, and `2`",
            "`P03`",
            "`P06`",
            "`P07`",
            "`P14`",
            "`P15`",
            "`P20`",
            "`P12`",
        ),
    )
    runtime = require_text(
        RUNTIME,
        (
            RUNTIME_MARKER,
            "promptKit.favoritePromptIds.v1",
            "Export Favorites",
            "Import Favorites",
            "mergePortableFavorites",
            "migrateLegacyFavoriteStorage",
            "PORTABLE_FAVORITES_MAX_BYTES=65536",
            "favorite_prompt_ids",
            "unknown_prompt_ids",
        ),
    )
    canonical_builder = require_text(
        CANONICAL_BUILDER,
        (
            "build_prompt_kit.build_html",
            "Prompt Kit check passed",
            "web/prompt-kit/index.html",
        ),
    )
    portable_builder = require_text(
        PORTABLE_BUILDER,
        (
            'SCHEMA_VERSION = "prompt-kit-portable-artifact/v1"',
            "DEFAULT_HOST = \"127.0.0.1\"",
            "DEFAULT_PORT = 8765",
            "ALLOWED_HOSTS",
            "build_portable_artifact",
            "Cache-Control",
            "canonical_site_untouched",
            "PROMPT_KIT_PORTABLE_SHA256",
        ),
    )
    portable_launcher = require_text(
        PORTABLE_LAUNCHER,
        (
            EXPECTED_ORIGIN,
            "Import-AcquisitionFunctions",
            "Update-RepositorySafely",
            "serve_prompt_kit_portable.py",
            "validate_prompt_kit_portability.py",
            "Start-PortableServer",
            "PROMPT_KIT_PORTABLE_ARTIFACT",
        ),
    )
    windows_entry = require_text(
        WINDOWS_ENTRY,
        (
            "Open-LatestPromptKitPortable.ps1",
            "Prompt Kit portable quick-open",
        ),
    )
    site = require_text(
        SITE,
        (
            "AI Harness Prompt Kit",
            "promptKit.favoritePromptIds.v1",
        ),
    )
    if RUNTIME_MARKER in site:
        fail("canonical tracked site must not contain runtime-only portability injection")
    workflow = require_text(
        WORKFLOW,
        (
            "scripts/serve_prompt_kit_portable.py",
            "scripts/validate_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability.py",
            "docs/prompt-kit-favorites-portability.js",
            "Build portable Prompt Kit runtime artifact",
            "Validate portable Favorites and harness discipline",
            "prompt-kit-portable-runtime",
        ),
    )
    manifest = require_text(
        HARNESS_MANIFEST,
        (
            '"prompt_kit_portability"',
            "harness/contracts/prompt-kit-portability.v1.json",
            "scripts/serve_prompt_kit_portable.py",
            "python scripts/validate_prompt_kit_portability.py",
        ),
    )
    readme = require_text(
        README,
        (
            "Portable Favorites",
            EXPECTED_ORIGIN,
            "docs/prompt-kit-favorites-portability.js",
            RUNTIME_MARKER,
            "Outputs/prompt-kit-portable/index.html",
        ),
    )

    artifact_result = None
    if artifact_path is not None or artifact_manifest_path is not None:
        artifact_result = validate_artifact(
            artifact_path or DEFAULT_ARTIFACT,
            artifact_manifest_path or DEFAULT_ARTIFACT_MANIFEST,
        )

    checks = {
        "policy": True,
        "doctrine": bool(doctrine),
        "runtime": bool(runtime),
        "canonical_builder": bool(canonical_builder),
        "portable_builder": bool(portable_builder),
        "portable_launcher": bool(portable_launcher),
        "windows_entry": bool(windows_entry),
        "canonical_site": bool(site),
        "workflow": bool(workflow),
        "manifest": bool(manifest),
        "agent_entry_surface": bool(readme),
        "runtime_artifact": artifact_result is not None,
    }
    return {
        "schema_version": "prompt-kit-portability-validation-result/v1",
        "status": "PASS",
        "policy": str(POLICY.relative_to(ROOT)),
        "runtime": str(RUNTIME.relative_to(ROOT)),
        "canonical_site": str(SITE.relative_to(ROOT)),
        "canonical_site_sha256": sha256_bytes(SITE.read_bytes()),
        "portable_artifact": artifact_result,
        "checks": checks,
        "proof_ceiling": policy.get("proof_ceiling"),
    }


def output_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = resolve_runtime_path(value, ROOT / value)
    outputs = (ROOT / "Outputs").resolve()
    try:
        path.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("validation output must remain under Outputs/") from exc
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--artifact")
    parser.add_argument("--manifest")
    parser.add_argument("--require-artifact", action="store_true")
    args = parser.parse_args(argv)
    try:
        artifact = resolve_runtime_path(args.artifact, DEFAULT_ARTIFACT) if args.artifact else None
        manifest = (
            resolve_runtime_path(args.manifest, DEFAULT_ARTIFACT_MANIFEST)
            if args.manifest
            else None
        )
        if args.require_artifact and artifact is None and manifest is None:
            artifact = DEFAULT_ARTIFACT
            manifest = DEFAULT_ARTIFACT_MANIFEST
        result = validate_repository_surfaces(artifact, manifest)
        destination = output_path(args.output)
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if args.summary:
            artifact_status = "artifact" if result["portable_artifact"] else "static"
            print(
                "Prompt Kit portability: PASS "
                f"({artifact_status}, {len(result['checks'])} checks, "
                f"canonical {result['canonical_site_sha256'][:12]})"
            )
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Prompt Kit portability: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
