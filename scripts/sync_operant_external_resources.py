#!/usr/bin/env python3
"""Build Operant's compact external-resource index from registered public donors."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_prompt_kit_registry  # noqa: E402

CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
DEFAULT_INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"
DEFAULT_GAPS = ROOT / "registry" / "resources" / "operant-external-resource-gaps.v1.json"
SKILLS_ROOT = ROOT / ".ai" / "skills"
API_ROOT = "https://api.github.com"
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "agent", "agents", "dsh", "for", "from", "in", "of", "on",
    "skill", "skills", "the", "to", "using", "with",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def github_json(path: str) -> Any:
    request = urllib.request.Request(
        API_ROOT + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "OperantExternalResourceSync/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub request failed for {path}: {exc}") from exc


def tokens(value: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(value.lower()) if token not in STOPWORDS and len(token) > 1}


def display_title(slug: str) -> str:
    return " ".join(piece.capitalize() for piece in re.split(r"[-_]+", slug) if piece)


def skill_titles() -> list[tuple[str, str, set[str]]]:
    rows: list[tuple[str, str, set[str]]] = []
    for path in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        title = path.parent.name
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        rows.append((path.parent.name, title, tokens(title + " " + path.parent.name)))
    return rows


def prompt_titles() -> list[tuple[str, str, set[str]]]:
    rows: list[tuple[str, str, set[str]]] = []
    for prompt in build_prompt_kit_registry.load_prompt_kit_registry():
        prompt_id = str(prompt["id"])
        title = str(prompt["name"])
        keywords = " ".join(str(item) for item in prompt.get("keywords", []))
        rows.append((prompt_id, title, tokens(title + " " + keywords)))
    return rows


def coverage_score(query: set[str], candidate: set[str]) -> float:
    if not query or not candidate:
        return 0.0
    return len(query & candidate) / max(1, min(len(query), len(candidate)))


def best_match(query: set[str], candidates: list[tuple[str, str, set[str]]]) -> tuple[str | None, str | None, float]:
    best_id: str | None = None
    best_title: str | None = None
    best = 0.0
    for candidate_id, candidate_title, candidate_tokens in candidates:
        score = coverage_score(query, candidate_tokens)
        if score > best or (score == best and score > 0 and (best_id is None or candidate_id < best_id)):
            best_id, best_title, best = candidate_id, candidate_title, score
    return best_id, best_title, round(best, 3)


def enumerate_source(source: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo = str(source["repository"])
    repository = github_json(f"/repos/{repo}")
    default_branch = str(repository["default_branch"])
    expected = str(source["expected_default_branch"])
    if default_branch != expected:
        raise ValueError(f"{repo} default branch changed: expected {expected}, observed {default_branch}")
    branch = github_json(f"/repos/{repo}/branches/{default_branch}")
    sha = str(branch["commit"]["sha"])
    tree_sha = str(branch["commit"]["commit"]["tree"]["sha"])
    tree = github_json(f"/repos/{repo}/git/trees/{tree_sha}?recursive=1")
    if tree.get("truncated"):
        raise ValueError(f"{repo} recursive Git tree was truncated")

    root = str(source["resource_root"]).rstrip("/")
    filename = str(source["resource_filename"])
    prefix = root + "/"
    suffix = "/" + filename
    resources: list[dict[str, Any]] = []
    for item in tree.get("tree", []):
        path = str(item.get("path", ""))
        if item.get("type") != "blob" or not path.startswith(prefix) or not path.endswith(suffix):
            continue
        relative = path[len(prefix):-len(suffix)]
        if not relative or "/" in relative:
            continue
        slug = relative
        title = display_title(slug)
        resources.append({
            "id": f"{source['id']}:{slug}",
            "source_id": source["id"],
            "source_repo": repo,
            "source_sha": sha,
            "kind": source["resource_kind"],
            "slug": slug,
            "title": title,
            "path": path,
            "url": f"https://github.com/{repo}/blob/{sha}/{path}",
        })
    resources.sort(key=lambda row: (str(row["title"]).lower(), str(row["id"])))
    receipt = {
        "id": source["id"],
        "repository": repo,
        "default_branch": default_branch,
        "resolved_sha": sha,
        "resource_root": root,
        "resource_count": len(resources),
    }
    return receipt, resources


def build_projection(contract: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt_candidates = prompt_titles()
    skill_candidates = skill_titles()
    threshold = float(contract["coverage"]["match_threshold"])
    max_terms = int(contract["projection"]["maximum_search_terms_per_resource"])
    receipts: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for source in contract["sources"]:
        receipt, source_resources = enumerate_source(source)
        receipts.append(receipt)
        for resource in source_resources:
            query = tokens(str(resource["title"]) + " " + str(resource["slug"]))
            prompt_id, prompt_title, prompt_score = best_match(query, prompt_candidates)
            skill_id, skill_title, skill_score = best_match(query, skill_candidates)
            coverage: dict[str, Any]
            if prompt_id is not None and prompt_score >= threshold and prompt_score >= skill_score:
                coverage = {
                    "disposition": contract["coverage"]["existing_prompt_disposition"],
                    "target_id": prompt_id,
                    "target_title": prompt_title,
                    "score": prompt_score,
                    "prompt_action": contract["coverage"]["existing_coverage_prompt_action"],
                }
            elif skill_id is not None and skill_score >= threshold:
                coverage = {
                    "disposition": contract["coverage"]["existing_skill_disposition"],
                    "target_id": skill_id,
                    "target_title": skill_title,
                    "score": skill_score,
                    "prompt_action": contract["coverage"]["existing_coverage_prompt_action"],
                }
            else:
                coverage = {
                    "disposition": contract["coverage"]["external_only_disposition"],
                    "target_id": None,
                    "target_title": None,
                    "score": max(prompt_score, skill_score),
                    "prompt_action": contract["coverage"]["missing_prompt_action"],
                }
                gaps.append({
                    "resource_id": resource["id"],
                    "source_id": resource["source_id"],
                    "title": resource["title"],
                    "url": resource["url"],
                    "user_disposition": contract["coverage"]["external_only_disposition"],
                    "prompt_action": contract["coverage"]["missing_prompt_action"],
                    "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
                    "best_internal_score": max(prompt_score, skill_score),
                })
            search_terms = sorted(query)[:max_terms]
            resource["search_terms"] = search_terms
            resource["coverage"] = coverage
            resources.append(resource)

    resources.sort(key=lambda row: (str(row["source_id"]), str(row["title"]).lower(), str(row["id"])))
    gaps.sort(key=lambda row: (str(row["source_id"]), str(row["title"]).lower(), str(row["resource_id"])))
    maximum_entries = int(contract["projection"]["maximum_entries"])
    if len(resources) > maximum_entries:
        raise ValueError(f"resource count {len(resources)} exceeds maximum_entries {maximum_entries}")

    summary = {
        "source_count": len(receipts),
        "resource_count": len(resources),
        "point_to_existing_prompt": sum(r["coverage"]["disposition"] == "POINT_TO_EXISTING_PROMPT" for r in resources),
        "point_to_existing_skill": sum(r["coverage"]["disposition"] == "POINT_TO_EXISTING_SKILL" for r in resources),
        "point_to_external": sum(r["coverage"]["disposition"] == "POINT_TO_EXTERNAL" for r in resources),
        "review_add_prompt": len(gaps),
    }
    index = {
        "schema_version": "operant-external-resource-index/v1",
        "source_floor": receipts,
        "summary": summary,
        "resources": resources,
    }
    gap_ledger = {
        "schema_version": "operant-external-resource-gap-ledger/v1",
        "source_floor": receipts,
        "policy": {
            "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
            "automatic_prompt_authoring": contract["coverage"]["automatic_prompt_authoring"],
            "rule": contract["coverage"]["rule"],
        },
        "summary": summary,
        "actions": gaps,
    }
    payload_bytes = len((json.dumps(index, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    maximum_bytes = int(contract["projection"]["maximum_index_bytes"])
    if payload_bytes > maximum_bytes:
        raise ValueError(f"resource index bytes {payload_bytes} exceeds maximum_index_bytes {maximum_bytes}")
    return index, gap_ledger


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--gaps-output", type=Path, default=DEFAULT_GAPS)
    parser.add_argument("--check", action="store_true", help="Fail if live donors do not reproduce the selected tracked outputs.")
    args = parser.parse_args(argv)
    try:
        contract = load_json(args.contract)
        index, gaps = build_projection(contract)
        expected_index = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
        expected_gaps = json.dumps(gaps, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            actual_index = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
            actual_gaps = args.gaps_output.read_text(encoding="utf-8") if args.gaps_output.exists() else ""
            if actual_index != expected_index or actual_gaps != expected_gaps:
                print("OPERANT_EXTERNAL_RESOURCE_DRIFT=1")
                return 1
            print("OPERANT_EXTERNAL_RESOURCE_DRIFT=0")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(expected_index, encoding="utf-8")
            args.gaps_output.parent.mkdir(parents=True, exist_ok=True)
            args.gaps_output.write_text(expected_gaps, encoding="utf-8")
        print(f"OPERANT_EXTERNAL_RESOURCE_COUNT={index['summary']['resource_count']}")
        print(f"OPERANT_EXTERNAL_RESOURCE_GAPS={index['summary']['review_add_prompt']}")
        for source in index["source_floor"]:
            print(f"OPERANT_DONOR={source['id']}@{source['resolved_sha']} resources={source['resource_count']}")
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Operant external resource sync failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
