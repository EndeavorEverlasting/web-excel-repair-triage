#!/usr/bin/env python3
"""Validate Operant external-resource contracts, projection budgets, and prompt-gap routing."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"
GAPS = ROOT / "registry" / "resources" / "operant-external-resource-gaps.v1.json"
RUNTIME = ROOT / "docs" / "prompt-kit-external-resources.js"
BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
SITE = ROOT / "web" / "prompt-kit" / "index.html"


class ValidationError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def require_finite_positive(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise ValidationError(f"{field} must be a finite positive number")
    return number


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{field} must be a positive integer")
    return value


def active_workflow_text(workflow: str) -> str:
    return "\n".join(line for line in workflow.splitlines() if not line.lstrip().startswith("#"))


def validate() -> dict[str, Any]:
    contract = load(CONTRACT)
    index = load(INDEX)
    gaps = load(GAPS)
    if contract.get("schema_version") != "operant-external-resource-intake/v1":
        raise ValidationError("unsupported external resource contract schema")
    if index.get("schema_version") != "operant-external-resource-index/v1":
        raise ValidationError("unsupported external resource index schema")
    if gaps.get("schema_version") != "operant-external-resource-gap-ledger/v1":
        raise ValidationError("unsupported external resource gap schema")
    if contract.get("projection", {}).get("catalog_csv_projects_rows_into_index") is not False:
        raise ValidationError("catalog_csv must not project rows into the public index")
    evidence = contract.get("coverage", {}).get("p79_external_evidence")
    if not isinstance(evidence, dict) or "registered_external_source_or_catalog_search" not in evidence.get("required_before_add", []):
        raise ValidationError("coverage.p79_external_evidence must require catalog/source search before ADD")
    catalog_search = contract.get("catalog_search")
    if not isinstance(catalog_search, dict):
        raise ValidationError("catalog_search contract block is required")
    require_finite_positive(catalog_search.get("maximum_live_search_seconds"), "catalog_search.maximum_live_search_seconds")
    require_positive_int(catalog_search.get("ci_proof_limit"), "catalog_search.ci_proof_limit")
    if not str(catalog_search.get("ci_proof_query", "")).strip():
        raise ValidationError("catalog_search.ci_proof_query is required")
    if catalog_search.get("live_proof_required_in_refresh_workflow") is not True:
        raise ValidationError("catalog_search.live_proof_required_in_refresh_workflow must remain true")
    workflow = (ROOT / ".github" / "workflows" / "operant-external-resource-refresh.yml").read_text(encoding="utf-8")
    active_workflow = active_workflow_text(workflow)
    for marker in (
        "scripts/search_operant_external_catalog.py",
        "--live-proof",
        "catalog-search-live-proof.json",
    ):
        if marker not in active_workflow:
            raise ValidationError(f"refresh workflow missing live catalog-search proof marker: {marker}")

    configured = {str(source["id"]): source for source in contract.get("sources", [])}
    floors = index.get("source_floor", [])
    if not configured or len(floors) != len(configured):
        raise ValidationError("source floor does not cover every configured donor exactly once")
    floor_ids = {str(source.get("id", "")) for source in floors}
    if floor_ids != set(configured):
        raise ValidationError("source floor IDs differ from configured donor IDs")
    catalog_floors = 0
    for floor in floors:
        source = configured[str(floor["id"])]
        if floor.get("repository") != source.get("repository"):
            raise ValidationError(f"repository mismatch for donor {floor['id']}")
        if floor.get("default_branch") != source.get("expected_default_branch"):
            raise ValidationError(f"default branch mismatch for donor {floor['id']}")
        sha = str(floor.get("resolved_sha", ""))
        if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
            raise ValidationError(f"invalid resolved SHA for donor {floor['id']}")
        enumeration = str(source.get("enumeration", "git_skill_tree"))
        if str(floor.get("enumeration", "git_skill_tree")) != enumeration:
            raise ValidationError(f"enumeration mismatch for donor {floor['id']}")
        if enumeration == "catalog_csv":
            catalog_floors += 1
            root = str(source.get("resource_root", ".")).rstrip("/")
            expected_path = str(source["resource_filename"]) if root in {"", "."} else f"{root}/{source['resource_filename']}"
            if floor.get("catalog_path") != expected_path:
                raise ValidationError(f"catalog_path mismatch for donor {floor['id']}")
            if int(floor.get("catalog_entry_count", -1)) < 1:
                raise ValidationError(f"catalog_entry_count missing for donor {floor['id']}")
            if int(floor.get("resource_count", -1)) != 0:
                raise ValidationError(f"catalog donor must project zero resource rows: {floor['id']}")
            if floor.get("search_mode") != "on_demand":
                raise ValidationError(f"catalog donor must declare on_demand search: {floor['id']}")

    resources = index.get("resources")
    if not isinstance(resources, list) or not resources:
        raise ValidationError("external resource index must contain resources")
    projection = contract["projection"]
    if len(resources) > int(projection["maximum_entries"]):
        raise ValidationError("resource count exceeds maximum_entries")
    if INDEX.stat().st_size > int(projection["maximum_index_bytes"]):
        raise ValidationError("resource index exceeds maximum_index_bytes")
    if len({str(item.get("id")) for item in resources}) != len(resources):
        raise ValidationError("resource IDs must be unique")

    dispositions = {
        contract["coverage"]["existing_prompt_disposition"],
        contract["coverage"]["existing_skill_disposition"],
        contract["coverage"]["external_only_disposition"],
    }
    pinned = 0
    external_resources: dict[str, dict[str, Any]] = {}
    for item in resources:
        source_id = str(item.get("source_id", ""))
        floor = next((row for row in floors if row["id"] == source_id), None)
        if floor is None:
            raise ValidationError(f"resource references unknown source: {source_id}")
        source = configured[source_id]
        if str(source.get("enumeration", "git_skill_tree")) == "catalog_csv":
            raise ValidationError(f"catalog_csv source must not emit projected resources: {item.get('id')}")
        repo = str(floor["repository"])
        sha = str(floor["resolved_sha"])
        path = str(item.get("path", ""))
        expected_prefix = str(source["resource_root"]).rstrip("/") + "/"
        expected_suffix = "/" + str(source["resource_filename"])
        if not path.startswith(expected_prefix) or not path.endswith(expected_suffix):
            raise ValidationError(f"resource path escapes configured donor root: {item.get('id')}")
        max_depth = int(source.get("max_depth", 1)) if str(source.get("enumeration", "git_skill_tree")) == "git_skill_tree" else None
        if max_depth is not None:
            relative = path[len(expected_prefix) : -len(expected_suffix)]
            parts = [part for part in relative.split("/") if part]
            if not parts or len(parts) > max_depth:
                raise ValidationError(f"resource path depth exceeds configured max_depth: {item.get('id')}")
            exclude = {str(seg) for seg in source.get("exclude_root_segments", [])}
            if parts[0] in exclude:
                raise ValidationError(f"resource path uses excluded root segment: {item.get('id')}")
        if item.get("source_repo") != repo or item.get("source_sha") != sha:
            raise ValidationError(f"resource source identity differs from donor floor: {item.get('id')}")
        url_mode = str(source.get("url_mode", "github_blob"))
        if url_mode == "github_blob":
            expected_url = f"https://github.com/{repo}/blob/{sha}/{path}"
        elif url_mode == "public_template":
            expected_url = str(source["url_template"]).format(
                slug=str(item.get("slug", "")),
                sha=sha,
                path=path,
                repository=repo,
            )
        else:
            raise ValidationError(f"unsupported url_mode for donor {source_id}: {url_mode}")
        if item.get("url") != expected_url:
            raise ValidationError(f"resource URL differs from configured donor URL mode: {item.get('id')}")
        if "contentPreview" in item or "body" in item or "copyContent" in item:
            raise ValidationError(f"resource embeds upstream body content: {item.get('id')}")
        pinned += 1
        terms = item.get("search_terms")
        if not isinstance(terms, list) or len(terms) > int(projection["maximum_search_terms_per_resource"]):
            raise ValidationError(f"invalid search-term budget: {item.get('id')}")
        coverage = item.get("coverage")
        if not isinstance(coverage, dict) or coverage.get("disposition") not in dispositions:
            raise ValidationError(f"invalid coverage disposition: {item.get('id')}")
        if coverage["disposition"] == contract["coverage"]["external_only_disposition"]:
            external_resources[str(item["id"])] = item
            if coverage.get("prompt_action") != contract["coverage"]["missing_prompt_action"]:
                raise ValidationError(f"external-only resource lacks prompt review action: {item.get('id')}")
            if coverage.get("target_id") is not None or coverage.get("target_title") is not None:
                raise ValidationError(f"external-only resource unexpectedly claims internal target: {item.get('id')}")
        else:
            if coverage.get("prompt_action") != contract["coverage"]["existing_coverage_prompt_action"]:
                raise ValidationError(f"covered resource incorrectly requests prompt addition: {item.get('id')}")
            if not str(coverage.get("target_id") or "").strip() or not str(coverage.get("target_title") or "").strip():
                raise ValidationError(f"covered resource lacks internal target identity: {item.get('id')}")

    actions = gaps.get("actions")
    if not isinstance(actions, list):
        raise ValidationError("gap ledger actions must be a list")
    action_ids = [str(action.get("resource_id", "")) for action in actions]
    if len(action_ids) != len(set(action_ids)):
        raise ValidationError("gap ledger resource IDs must be unique")
    if set(action_ids) != set(external_resources):
        raise ValidationError("gap ledger resource identities differ from external-only resources")
    for action in actions:
        resource = external_resources[str(action["resource_id"])]
        expected = {
            "source_id": resource["source_id"],
            "title": resource["title"],
            "url": resource["url"],
            "user_disposition": contract["coverage"]["external_only_disposition"],
            "prompt_action": contract["coverage"]["missing_prompt_action"],
            "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
        }
        for field, value in expected.items():
            if action.get(field) != value:
                raise ValidationError(f"gap ledger action mismatch for {action['resource_id']}: {field}")
    if gaps.get("source_floor") != floors:
        raise ValidationError("gap ledger source floor differs from public index")
    if gaps.get("policy", {}).get("automatic_prompt_authoring") is not False:
        raise ValidationError("automatic donor-to-prompt authoring must remain disabled")

    runtime = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "operant-external-resources/v1",
        "resources.v1.json",
        "loadExternalResources",
        "renderExternalResourcePage",
        "OPERANT_EXTERNAL_RESOURCE_PAGE_SIZE",
    ):
        if marker not in runtime:
            raise ValidationError(f"resource runtime missing marker: {marker}")
    eager_markers = ("loadExternalResources();", "fetch('resources.v1.json')")
    for marker in eager_markers:
        if marker in runtime:
            raise ValidationError(f"resource runtime contains eager-load marker: {marker}")

    builder = BUILDER.read_text(encoding="utf-8")
    if "prompt-kit-external-resources.js" not in builder:
        raise ValidationError("Prompt Kit builder does not embed the external-resource runtime")
    site = SITE.read_text(encoding="utf-8")
    if "operant-external-resources/v1" not in site:
        raise ValidationError("generated Prompt Kit site lacks the external-resource runtime")
    for resource in resources[: min(20, len(resources))]:
        if str(resource["url"]) in site:
            raise ValidationError("generated main page embeds donor resource records instead of lazy sidecar")

    summary = index.get("summary", {})
    if int(summary.get("resource_count", -1)) != len(resources):
        raise ValidationError("index summary resource_count mismatch")
    if int(summary.get("review_add_prompt", -1)) != len(actions):
        raise ValidationError("index summary review_add_prompt mismatch")
    if int(summary.get("catalog_sources", -1)) != catalog_floors:
        raise ValidationError("index summary catalog_sources mismatch")
    if int(summary.get("catalog_entries_indexed", -1)) != 0:
        raise ValidationError("catalog entries must remain unindexed in the public sidecar")
    return {
        "status": "valid",
        "sources": len(floors),
        "catalog_sources": catalog_floors,
        "resources": len(resources),
        "pinned_urls": pinned,
        "external_only": len(external_resources),
        "index_bytes": INDEX.stat().st_size,
        "page_size": projection["default_render_page_size"],
        "lazy_fetch": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate()
    except (OSError, KeyError, TypeError, ValueError, ValidationError) as exc:
        print(f"Operant external resource validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=None if args.summary else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
