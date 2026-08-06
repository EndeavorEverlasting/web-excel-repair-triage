#!/usr/bin/env python3
"""Fail-closed Prompt Kit portability contract validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "harness" / "contracts" / "prompt-kit-portability.v1.json"
DOCTRINE = ROOT / "docs" / "PROMPT_KIT_PORTABILITY.md"
RUNTIME = ROOT / "docs" / "prompt-kit-favorites-portability.js"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
SITE = ROOT / "web" / "prompt-kit" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "prompt-kit-web.yml"
MANIFEST = ROOT / "harness" / "manifest.v1.json"
README = ROOT / "web" / "README.md"

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


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(payload, dict):
        fail(f"expected JSON object: {path.relative_to(ROOT)}")
    return payload


def require_text(path: Path, phrases: tuple[str, ...]) -> str:
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    for phrase in phrases:
        if phrase not in text:
            fail(f"{path.relative_to(ROOT)} missing required marker: {phrase}")
    return text


def validate_policy(policy: dict) -> None:
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
    if favorites.get("export_schema") != "prompt-kit-favorites/v1":
        fail("favorites export schema drift")
    if favorites.get("max_import_bytes") != 65536:
        fail("favorites import size limit drift")
    if favorites.get("controls") != ["Export Favorites", "Import Favorites"]:
        fail("favorites controls drift")
    if favorites.get("import_behavior") != "merge_deduplicate_normalize_preserve_unknown_ids":
        fail("favorites import behavior drift")

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


def validate_repository_surfaces() -> dict:
    policy = load_json(POLICY)
    validate_policy(policy)

    doctrine = require_text(
        DOCTRINE,
        (
            "Standard AI",
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
            "prompt-kit-favorites/v1",
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
    builder = require_text(
        BUILDER,
        (
            "PORTABILITY_RUNTIME",
            "prompt-kit-favorites-portability.js",
            "_embed_portability_runtime",
            "html.count(marker) != 1",
        ),
    )
    site = require_text(
        SITE,
        (
            "prompt-kit-favorites/v1",
            "favoritePortabilityControls",
            "Export Favorites",
            "Import Favorites",
        ),
    )
    workflow = require_text(
        WORKFLOW,
        (
            "scripts/validate_prompt_kit_portability.py",
            "tests/test_prompt_kit_portability.py",
            "docs/prompt-kit-favorites-portability.js",
            "Validate portable Favorites and harness discipline",
        ),
    )
    manifest = require_text(
        MANIFEST,
        (
            '"prompt_kit_portability"',
            "harness/contracts/prompt-kit-portability.v1.json",
            "python scripts/validate_prompt_kit_portability.py --summary",
        ),
    )
    readme = require_text(
        README,
        (
            "Portable Favorites",
            "docs/prompt-kit-favorites-portability.js",
            "prompt-kit-favorites/v1",
        ),
    )

    return {
        "schema_version": "prompt-kit-portability-validation-result/v1",
        "status": "PASS",
        "policy": str(POLICY.relative_to(ROOT)),
        "runtime": str(RUNTIME.relative_to(ROOT)),
        "generated_site": str(SITE.relative_to(ROOT)),
        "generated_site_sha256": hashlib.sha256(site.encode("utf-8")).hexdigest(),
        "checks": {
            "policy": True,
            "doctrine": bool(doctrine),
            "runtime": bool(runtime),
            "builder": bool(builder),
            "generated_site": bool(site),
            "workflow": bool(workflow),
            "manifest": bool(manifest),
            "agent_entry_surface": bool(readme),
        },
        "proof_ceiling": policy.get("proof_ceiling"),
    }


def output_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    outputs = (ROOT / "Outputs").resolve()
    try:
        resolved.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("validation output must remain under Outputs/") from exc
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        result = validate_repository_surfaces()
        destination = output_path(args.output)
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if args.summary:
            print(
                "Prompt Kit portability: PASS "
                f"({result['generated_site_sha256'][:12]}, "
                f"{len(result['checks'])} checks)"
            )
        return 0
    except (OSError, ValueError) as exc:
        print(f"Prompt Kit portability: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
