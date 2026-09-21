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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.operant_external_resource_paths import normalize_resource_root, resource_path_parts  # noqa: E402

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
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a finite positive number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValidationError(f"{field} must be a finite positive number")
    return number


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{field} must be a positive integer")
    return value


def active_workflow_text(workflow: str) -> str:
    lines: list[str] = []
    for line in workflow.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if " #" in line:
            line = line.split(" #", 1)[0].rstrip()
        lines.append(line)
    return "\n".join(lines)



def validate_capability_watch_contract(
    contract: dict[str, Any],
    impact_edges: dict[str, Any],
    active_workflow: str,
) -> None:
    watch = contract.get("capability_watch")
    if not isinstance(watch, dict) or watch.get("schema_version") != "operant-upstream-capability-watch/v1":
        raise ValidationError("capability_watch contract block is missing or unsupported")

    identity = watch.get("identity")
    if not isinstance(identity, dict):
        raise ValidationError("capability_watch.identity is required")
    if identity.get("repository_revision_field") != "source_sha":
        raise ValidationError("capability_watch repository revision must remain source_sha provenance")
    if identity.get("capability_identity_field") != "resource_identity":
        raise ValidationError("capability_watch capability identity must remain resource_identity")
    if identity.get("capability_identity_algorithm") != "git_blob_sha":
        raise ValidationError("capability_watch identity must use git_blob_sha")

    kernel = watch.get("kernel")
    expected_entrypoints = {
        "new_watch_state",
        "observe_capability",
        "record_routing_result",
        "transition_event_id",
    }
    if not isinstance(kernel, dict) or kernel.get("path") != "scripts/upstream_capability_watch.py":
        raise ValidationError("capability_watch kernel path is missing or incorrect")
    if set(kernel.get("entrypoints", [])) != expected_entrypoints:
        raise ValidationError("capability_watch kernel entrypoints are incomplete")
    if not CAPABILITY_WATCH_KERNEL.is_file():
        raise ValidationError("capability_watch kernel file is missing")

    state = watch.get("state")
    required_state = {
        "last_observed_identity",
        "last_processed_identity",
        "last_observed_repository_revision",
        "status",
    }
    if not isinstance(state, dict) or set(state.get("required_fields", [])) != required_state:
        raise ValidationError("capability_watch state fields are incomplete")
    if state.get("initial_status") != "UNSEEN":
        raise ValidationError("capability_watch initial status must be UNSEEN")

    events = watch.get("events")
    if not isinstance(events, dict) or events.get("schema_version") != "upstream-capability-changed/v1":
        raise ValidationError("capability_watch event schema is missing or unsupported")
    if events.get("transition_key_fields") != [
        "source_id",
        "resource_id",
        "previous_processed_identity",
        "observed_identity",
    ]:
        raise ValidationError("capability_watch dedupe key must bind source/capability and previous/current identity")
    if events.get("event_id_algorithm") != "sha256(canonical transition_key_fields)":
        raise ValidationError("capability_watch event identity algorithm is unsupported")
    if events.get("raw_donor_body_allowed") is not False:
        raise ValidationError("capability_watch events must not persist raw donor bodies")
    if events.get("zero_impact_event_retained") is not True:
        raise ValidationError("capability_watch must retain zero-impact events")

    promotion = watch.get("promotion")
    if not isinstance(promotion, dict):
        raise ValidationError("capability_watch promotion policy is required")
    transitions = {
        tuple(item)
        for item in promotion.get("allowed_transitions", [])
        if isinstance(item, list) and len(item) == 2
    }
    required_transitions = {
        ("UNSEEN", "CURRENT"),
        ("CURRENT", "UPSTREAM_CHANGED"),
        ("EVALUATING", "UPSTREAM_CHANGED"),
        ("CANDIDATE", "UPSTREAM_CHANGED"),
        ("DECLINED", "UPSTREAM_CHANGED"),
        ("INTEGRATED", "UPSTREAM_CHANGED"),
        ("UPSTREAM_CHANGED", "EVALUATING"),
        ("EVALUATING", "CANDIDATE"),
        ("EVALUATING", "DECLINED"),
        ("CANDIDATE", "INTEGRATED"),
        ("DECLINED", "CURRENT"),
        ("INTEGRATED", "CURRENT"),
    }
    missing = required_transitions - transitions
    if missing:
        formatted = ", ".join(f"{source} -> {target}" for source, target in sorted(missing))
        raise ValidationError("capability_watch missing required transition(s): " + formatted)
    if ("UPSTREAM_CHANGED", "INTEGRATED") in transitions:
        raise ValidationError("capability_watch must not promote UPSTREAM_CHANGED directly to INTEGRATED")
    if ["UPSTREAM_CHANGED", "INTEGRATED"] not in promotion.get("forbidden_direct_transitions", []):
        raise ValidationError("capability_watch must explicitly forbid UPSTREAM_CHANGED -> INTEGRATED")
    if promotion.get("automatic_prompt_authoring") is not False:
        raise ValidationError("capability_watch must not auto-author prompts")

    impact = watch.get("impact_edges")
    if not isinstance(impact, dict) or impact.get("registry") != "registry/resources/upstream-capability-impact-edges.v1.json":
        raise ValidationError("capability_watch impact-edge registry path is missing or incorrect")
    if impact.get("missing_edge_status") != "NO_IMPACT_EDGE":
        raise ValidationError("capability_watch missing-edge status must remain NO_IMPACT_EDGE")
    if impact_edges.get("schema_version") != "upstream-capability-impact-edges/v1":
        raise ValidationError("unsupported capability-watch impact-edge registry schema")
    policy = impact_edges.get("policy")
    if not isinstance(policy, dict) or policy.get("zero_edge_is_valid") is not True:
        raise ValidationError("capability-watch impact-edge registry must permit zero-edge events")
    if policy.get("zero_edge_status") != "NO_IMPACT_EDGE":
        raise ValidationError("capability-watch impact-edge registry must use NO_IMPACT_EDGE")
    if policy.get("donor_change_never_grants_local_mutation_authority") is not True:
        raise ValidationError("donor changes must never grant local mutation authority")
    unique_fields = policy.get("unique_key_fields")
    required_edge_fields = impact_edges.get("edge_schema", {}).get("required_fields")
    if not isinstance(unique_fields, list) or not unique_fields:
        raise ValidationError("capability-watch impact-edge unique key is missing")
    if not isinstance(required_edge_fields, list) or not required_edge_fields:
        raise ValidationError("capability-watch impact-edge required fields are missing")
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, ...]] = set()
    for edge in impact_edges.get("edges", []):
        if not isinstance(edge, dict):
            raise ValidationError("capability-watch impact edge must be an object")
        missing_fields = [field for field in required_edge_fields if not str(edge.get(field, "")).strip()]
        if missing_fields:
            raise ValidationError("capability-watch impact edge missing field(s): " + ", ".join(missing_fields))
        edge_id = str(edge["edge_id"])
        if edge_id in seen_ids:
            raise ValidationError(f"duplicate capability-watch impact edge id: {edge_id}")
        seen_ids.add(edge_id)
        key = tuple(str(edge.get(field, "")) for field in unique_fields)
        if key in seen_keys:
            raise ValidationError("duplicate capability-watch impact edge mapping")
        seen_keys.add(key)

    for marker in (
        "scripts/upstream_capability_watch.py",
        "registry/resources/upstream-capability-impact-edges.v1.json",
        "tests/test_upstream_capability_watch.py",
        "tests.test_upstream_capability_watch",
    ):
        if marker not in active_workflow:
            raise ValidationError(f"refresh workflow missing capability-watch marker: {marker}")

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
            root = normalize_resource_root(source.get("resource_root", "."))
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
        parts = resource_path_parts(
            path=path,
            resource_root=source["resource_root"],
            resource_filename=source["resource_filename"],
        )
        if parts is None:
            raise ValidationError(f"resource path escapes configured donor root: {item.get('id')}")
        max_depth = int(source.get("max_depth", 1)) if str(source.get("enumeration", "git_skill_tree")) == "git_skill_tree" else None
        if max_depth is not None:
            if len(parts) > max_depth:
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
