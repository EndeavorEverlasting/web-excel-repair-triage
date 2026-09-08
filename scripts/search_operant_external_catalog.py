#!/usr/bin/env python3
"""Deterministic on-demand search of registered catalog_csv external sources."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

csv.field_size_limit(min(sys.maxsize, 16 * 1024 * 1024))

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import sync_operant_external_resources as sync  # noqa: E402

CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"


def load_source(contract: dict[str, Any], source_id: str) -> dict[str, Any]:
    for source in contract.get("sources", []):
        if str(source.get("id")) == source_id:
            if str(source.get("enumeration")) != "catalog_csv":
                raise ValueError(f"source {source_id} is not catalog_csv")
            return source
    raise ValueError(f"unknown catalog source: {source_id}")


def floor_for(index: dict[str, Any] | None, source_id: str) -> dict[str, Any] | None:
    if not index:
        return None
    for row in index.get("source_floor", []):
        if str(row.get("id")) == source_id:
            return row
    return None


def catalog_path_for(source: dict[str, Any]) -> str:
    root = str(source.get("resource_root", ".")).rstrip("/")
    filename = str(source["resource_filename"])
    if root in {"", "."}:
        return filename
    return f"{root}/{filename}"


def read_catalog_text(*, source: dict[str, Any], sha: str, catalog_file: Path | None) -> str:
    if catalog_file is not None:
        return catalog_file.read_text(encoding="utf-8")
    catalog_path = catalog_path_for(source)
    repo = str(source["repository"])
    return sync.github_text(f"{sync.RAW_ROOT}/{repo}/{sha}/{catalog_path}")


def parse_catalog_rows(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("catalog CSV has no header")
    required = {"act", "prompt"}
    missing = required - {name.strip() for name in reader.fieldnames if name}
    if missing:
        raise ValueError(f"catalog CSV missing columns: {sorted(missing)}")
    rows: list[dict[str, str]] = []
    for index, row in enumerate(reader):
        act = str(row.get("act") or "").strip()
        prompt = str(row.get("prompt") or "").strip()
        if not act and not prompt:
            continue
        rows.append({
            "row_index": str(index),
            "act": act,
            "prompt": prompt,
            "for_devs": str(row.get("for_devs") or "").strip(),
            "type": str(row.get("type") or "").strip(),
            "contributor": str(row.get("contributor") or "").strip(),
        })
    return rows


def hit_disposition(
    *,
    query: set[str],
    hit_tokens: set[str],
    best_internal_score: float,
    threshold: float,
) -> tuple[str, set[str]]:
    residual = query - hit_tokens
    if best_internal_score >= threshold and residual:
        return "ADAPT", residual
    return "REFERENCE_ONLY", residual


def search_catalog(
    *,
    contract: dict[str, Any],
    source: dict[str, Any],
    query_text: str,
    limit: int,
    sha: str,
    catalog_file: Path | None,
) -> dict[str, Any]:
    threshold = float(contract["coverage"]["match_threshold"])
    max_terms = int(contract["projection"]["maximum_search_terms_per_resource"])
    query = sync.tokens(query_text)
    prompt_candidates = sync.prompt_titles()
    skill_candidates = sync.skill_titles()
    catalog_path = catalog_path_for(source)
    repo = str(source["repository"])
    rows = parse_catalog_rows(read_catalog_text(source=source, sha=sha, catalog_file=catalog_file))

    ranked: list[dict[str, Any]] = []
    for row in rows:
        haystack = " ".join([row["act"], row["type"], row["contributor"], row["prompt"][:240]])
        hit_tokens = sync.tokens(haystack)
        score = sync.coverage_score(query, hit_tokens)
        if score <= 0:
            continue
        prompt_id, prompt_title, prompt_score = sync.best_match(hit_tokens, prompt_candidates)
        skill_id, skill_title, skill_score = sync.best_match(hit_tokens, skill_candidates)
        best_internal = max(prompt_score, skill_score)
        disposition, residual = hit_disposition(
            query=query,
            hit_tokens=hit_tokens,
            best_internal_score=best_internal,
            threshold=threshold,
        )
        ranked.append({
            "source_id": source["id"],
            "source_repo": repo,
            "source_sha": sha,
            "catalog_path": catalog_path,
            "row_index": int(row["row_index"]),
            "title": row["act"] or f"catalog-row-{row['row_index']}",
            "type": row["type"],
            "contributor": row["contributor"],
            "url": f"https://github.com/{repo}/blob/{sha}/{catalog_path}",
            "score": round(score, 3),
            "search_terms": sorted(hit_tokens)[:max_terms],
            "commonality_terms": sorted(query & hit_tokens)[:max_terms],
            "distinct_residual_terms": sorted(residual)[:max_terms],
            "best_internal": {
                "prompt_id": prompt_id,
                "prompt_title": prompt_title,
                "prompt_score": prompt_score,
                "skill_id": skill_id,
                "skill_title": skill_title,
                "skill_score": skill_score,
                "score": best_internal,
            },
            "disposition": disposition,
            "prompt_action": "NO_AUTO_AUTHOR",
            "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
            "authority": "reference_only_until_operant_adoption",
        })

    ranked.sort(key=lambda item: (-float(item["score"]), str(item["title"]).lower(), int(item["row_index"])))
    hits = ranked[: max(0, limit)]
    return {
        "schema_version": "operant-external-catalog-search/v1",
        "source_id": source["id"],
        "query": query_text,
        "resolved_sha": sha,
        "catalog_path": catalog_path,
        "catalog_entry_count": len(rows),
        "hit_count": len(hits),
        "automatic_prompt_authoring": False,
        "policy": {
            "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
            "p79_external_evidence": contract["coverage"].get("p79_external_evidence"),
            "catalog_hit_dispositions": contract["coverage"].get("catalog_hit_dispositions"),
        },
        "hits": hits,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search a registered catalog_csv donor without projecting rows into Operant.")
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--index", type=Path, default=INDEX)
    parser.add_argument("--source", default="prompts-chat")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sha", default="")
    parser.add_argument("--catalog-file", type=Path, default=None, help="Offline fixture CSV; skips live network fetch.")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = sync.load_json(args.contract)
        source = load_source(contract, args.source)
        index = sync.load_json(args.index) if args.index.exists() else None
        floor = floor_for(index, args.source)
        sha = (args.sha or "").strip() or (str(floor.get("resolved_sha", "")) if floor else "")
        if not sha and args.catalog_file is None:
            raise ValueError("resolved SHA required: pass --sha, refresh the projection floor, or use --catalog-file")
        if not sha:
            sha = "fixture"
        result = search_catalog(
            contract=contract,
            source=source,
            query_text=args.query,
            limit=args.limit,
            sha=sha,
            catalog_file=args.catalog_file,
        )
        if args.summary:
            print(json.dumps({
                "source_id": result["source_id"],
                "resolved_sha": result["resolved_sha"],
                "catalog_entry_count": result["catalog_entry_count"],
                "hit_count": result["hit_count"],
                "top_titles": [hit["title"] for hit in result["hits"][:5]],
            }, sort_keys=True))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Operant external catalog search failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
