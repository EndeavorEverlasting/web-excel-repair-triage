#!/usr/bin/env python3
"""Fail-closed external prior-art gate for new Prompt Kit identities."""
from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "operant-external-resource-intake.v1.json"
INDEX = ROOT / "web" / "prompt-kit" / "resources.v1.json"
RECEIPT_SCHEMA = "prompt-registry-external-prior-art/v1"
DEFAULT_HIT_LIMIT = 5

from scripts import search_operant_external_catalog as catalog_search  # noqa: E402
from scripts import sync_operant_external_resources as sync  # noqa: E402


class PriorArtGateError(RuntimeError):
    """The ADD path cannot prove required external prior-art evidence."""


def _query_text(draft: dict[str, Any]) -> str:
    parts = [str(draft.get("name", "")).strip()]
    keywords = draft.get("keywords")
    if isinstance(keywords, list):
        parts.extend(str(item).strip() for item in keywords if str(item).strip())
    query = " ".join(part for part in parts if part).strip()
    if not sync.tokens(query):
        raise PriorArtGateError("external prior-art query is empty")
    return query


def _source_floor(index: dict[str, Any], source_id: str) -> dict[str, Any]:
    floor = catalog_search.floor_for(index, source_id)
    if not isinstance(floor, dict):
        raise PriorArtGateError(f"registered external source lacks pinned floor: {source_id}")
    sha = str(floor.get("resolved_sha", ""))
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise PriorArtGateError(f"registered external source has invalid pinned SHA: {source_id}")
    return floor


def _candidate_tokens(
    candidate_id: str | None, candidates: list[tuple[str, str, set[str]]]
) -> set[str]:
    if candidate_id is None:
        return set()
    for row_id, _title, row_tokens in candidates:
        if row_id == candidate_id:
            return set(row_tokens)
    return set()


def _internal_comparison(
    query_tokens: set[str], max_terms: int
) -> tuple[dict[str, Any], list[str]]:
    prompt_candidates = sync.prompt_titles()
    skill_candidates = sync.skill_titles()
    prompt_id, prompt_title, prompt_score = sync.best_match(query_tokens, prompt_candidates)
    skill_id, skill_title, skill_score = sync.best_match(query_tokens, skill_candidates)
    if prompt_score >= skill_score:
        best_kind = "prompt"
        best_id = prompt_id
        best_title = prompt_title
        best_score = prompt_score
        covered_terms = _candidate_tokens(prompt_id, prompt_candidates)
    else:
        best_kind = "skill"
        best_id = skill_id
        best_title = skill_title
        best_score = skill_score
        covered_terms = _candidate_tokens(skill_id, skill_candidates)
    residual = sorted(query_tokens - covered_terms)[:max_terms]
    return (
        {
            "kind": best_kind if best_id else None,
            "id": best_id,
            "title": best_title,
            "score": best_score,
            "prompt_id": prompt_id,
            "prompt_title": prompt_title,
            "prompt_score": prompt_score,
            "skill_id": skill_id,
            "skill_title": skill_title,
            "skill_score": skill_score,
        },
        residual,
    )


def _projected_hits(
    *,
    index: dict[str, Any],
    source_id: str,
    query_tokens: set[str],
    max_terms: int,
    limit: int,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for resource in index.get("resources", []):
        if not isinstance(resource, dict) or str(resource.get("source_id")) != source_id:
            continue
        haystack = " ".join(
            [
                str(resource.get("title", "")),
                *[str(item) for item in resource.get("search_terms", []) if isinstance(item, str)],
            ]
        )
        hit_tokens = sync.tokens(haystack)
        score = sync.coverage_score(query_tokens, hit_tokens)
        if score <= 0:
            continue
        coverage = resource.get("coverage") if isinstance(resource.get("coverage"), dict) else {}
        ranked.append(
            {
                "title": resource.get("title"),
                "path": resource.get("path"),
                "url": resource.get("url"),
                "score": round(score, 3),
                "commonality_terms": sorted(query_tokens & hit_tokens)[:max_terms],
                "coverage_disposition": coverage.get("disposition"),
                "internal_target_id": coverage.get("target_id"),
                "internal_target_title": coverage.get("target_title"),
            }
        )
    ranked.sort(key=lambda item: (-float(item["score"]), str(item.get("title", "")).casefold()))
    return ranked[:limit]


def require_external_prior_art(draft: dict[str, Any]) -> dict[str, Any]:
    """Search every registered external source before a new prompt identity is allocated."""
    try:
        contract = sync.load_json(CONTRACT)
        index = sync.load_json(INDEX)
        evidence = contract.get("coverage", {}).get("p79_external_evidence")
        required_evidence = evidence.get("required_before_add", []) if isinstance(evidence, dict) else []
        required_markers = {
            "registered_external_source_or_catalog_search",
            "commonality_extraction_against_existing_owners",
            "distinct_residual_proof",
        }
        if not required_markers.issubset(set(required_evidence)):
            raise PriorArtGateError("external-resource contract no longer defines the full pre-ADD evidence gate")

        query_text = _query_text(draft)
        query_tokens = sync.tokens(query_text)
        max_terms = int(contract["projection"]["maximum_search_terms_per_resource"])
        internal_best, residual = _internal_comparison(query_tokens, max_terms)
        if not residual:
            raise PriorArtGateError(
                "new prompt has no distinct residual against the strongest current internal owner; strengthen instead"
            )

        sources = contract.get("sources")
        if not isinstance(sources, list) or not sources:
            raise PriorArtGateError("no registered external sources are configured")
        source_ids = [str(source.get("id", "")) for source in sources if isinstance(source, dict)]
        if len(source_ids) != len(sources) or any(not source_id for source_id in source_ids):
            raise PriorArtGateError("every registered external source must have a non-empty id")
        if len(source_ids) != len(set(source_ids)):
            raise PriorArtGateError("registered external source ids must be unique")
        configured_ids = set(source_ids)

        catalog_cfg = contract.get("catalog_search", {})
        budget = catalog_search.catalog_search_budget_seconds(contract)
        catalog_limit = int(catalog_cfg.get("ci_proof_limit", DEFAULT_HIT_LIMIT))
        source_receipts: list[dict[str, Any]] = []
        for source in sources:
            if not isinstance(source, dict):
                raise PriorArtGateError("registered external source must be an object")
            source_id = str(source["id"])
            floor = _source_floor(index, source_id)
            enumeration = str(source.get("enumeration", ""))
            if enumeration == "catalog_csv":
                result, elapsed = catalog_search.run_timed_search(
                    contract=contract,
                    source=catalog_search.load_source(contract, source_id),
                    query_text=query_text,
                    limit=catalog_limit,
                    sha=str(floor["resolved_sha"]),
                    catalog_file=None,
                    fetch_timeout=catalog_search.live_fetch_timeout_seconds(budget),
                )
                if elapsed > budget:
                    raise PriorArtGateError(
                        f"registered catalog search exceeded budget for {source_id}: {elapsed:.3f}s > {budget}s"
                    )
                source_receipts.append(
                    {
                        "source_id": source_id,
                        "repository": source.get("repository"),
                        "resolved_sha": floor["resolved_sha"],
                        "search_mode": "pinned_catalog_live_fetch",
                        "hit_count": int(result["hit_count"]),
                        "elapsed_seconds": round(elapsed, 3),
                        "hits": [
                            {
                                "title": hit.get("title"),
                                "url": hit.get("url"),
                                "score": hit.get("score"),
                                "commonality_terms": hit.get("commonality_terms", []),
                                "distinct_residual_terms": hit.get("distinct_residual_terms", []),
                                "best_internal": hit.get("best_internal"),
                                "disposition": hit.get("disposition"),
                            }
                            for hit in result.get("hits", [])[:catalog_limit]
                        ],
                    }
                )
            elif enumeration == "git_skill_tree":
                hits = _projected_hits(
                    index=index,
                    source_id=source_id,
                    query_tokens=query_tokens,
                    max_terms=max_terms,
                    limit=DEFAULT_HIT_LIMIT,
                )
                source_receipts.append(
                    {
                        "source_id": source_id,
                        "repository": source.get("repository"),
                        "resolved_sha": floor["resolved_sha"],
                        "search_mode": "pinned_metadata_projection",
                        "hit_count": len(hits),
                        "hits": hits,
                    }
                )
            else:
                raise PriorArtGateError(
                    f"unsupported registered external source enumeration for ADD gate: {source_id}={enumeration}"
                )

        searched_ids = {str(item["source_id"]) for item in source_receipts}
        if len(source_receipts) != len(source_ids) or searched_ids != configured_ids:
            missing = sorted(configured_ids - searched_ids)
            raise PriorArtGateError(f"not every registered external source was searched exactly once: {missing}")

        return {
            "schema_version": RECEIPT_SCHEMA,
            "query": query_text,
            "promotion_owner_prompt": contract["coverage"]["promotion_owner_prompt"],
            "required_evidence": list(required_evidence),
            "internal_best_match": internal_best,
            "distinct_residual_terms": residual,
            "sources": source_receipts,
            "all_registered_sources_searched": True,
            "automatic_prompt_authoring": False,
            "authority": "external_prior_art_is_reference_only_until_operant_adoption",
        }
    except PriorArtGateError:
        raise
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise PriorArtGateError(f"external prior-art search failed closed: {exc}") from exc
