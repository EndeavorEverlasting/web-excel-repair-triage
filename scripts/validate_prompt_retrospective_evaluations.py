#!/usr/bin/env python3
"""Validate review-only retrospective prompt evaluations.

This validator is intentionally fail-closed around historical authorship:
current Prompt Kit coverage may prove current gap coverage, but it cannot
retroactively prove whether an earlier prompt was reused, hybridized, or
manually authored.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "harness" / "contracts" / "prompt-retrospective-evaluation.v1.json"
DEFAULT_REGISTER = ROOT / "harness" / "evals" / "prompt-retrospective" / "recent-candidates.v1.json"
PROMPT_ID_RE = re.compile(r"^P\d{2,4}$")
ONE_LINE_MAX = 320


class RetrospectiveValidationError(ValueError):
    """Raised when retrospective evaluation data violates the contract."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RetrospectiveValidationError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RetrospectiveValidationError(f"JSON root must be an object: {path}")
    return payload


def require_one_line(value: Any, field: str, *, max_length: int = ONE_LINE_MAX) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RetrospectiveValidationError(f"{field} must be a non-empty string")
    text = value.strip()
    if "\n" in text or "\r" in text or len(text) > max_length:
        raise RetrospectiveValidationError(f"{field} must be one line <= {max_length} chars")
    return text


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "prompt-retrospective-evaluation/v1":
        raise RetrospectiveValidationError("unsupported retrospective evaluation contract")
    authority = contract.get("authority")
    if not isinstance(authority, dict):
        raise RetrospectiveValidationError("contract.authority must be an object")
    if authority.get("evaluation") != "review-only":
        raise RetrospectiveValidationError("retrospective evaluation must remain review-only")
    if authority.get("prompt_registry_mutation") is not False:
        raise RetrospectiveValidationError("retrospective evaluation cannot mutate prompt registry")
    if authority.get("prompt_identity_allocation") is not False:
        raise RetrospectiveValidationError("retrospective evaluation cannot allocate prompt identities")

    dimensions = contract.get("dimensions")
    expected = {"use_case_relevance", "productivity", "prompt_kit_gap", "authorship_origin"}
    if not isinstance(dimensions, dict) or set(dimensions) != expected:
        raise RetrospectiveValidationError("contract dimensions must be exactly the four retrospective dimensions")
    for name, definition in dimensions.items():
        if not isinstance(definition, dict):
            raise RetrospectiveValidationError(f"dimension {name} must be an object")
        levels = definition.get("levels")
        if not isinstance(levels, dict) or set(levels) != {"1", "2", "3", "4", "5"}:
            raise RetrospectiveValidationError(f"dimension {name} must define levels 1..5")

    confidence = contract.get("confidence")
    levels = confidence.get("levels") if isinstance(confidence, dict) else None
    if not isinstance(levels, dict) or set(levels) != {"HIGH", "MEDIUM", "LOW", "NONE"}:
        raise RetrospectiveValidationError("confidence levels must be HIGH/MEDIUM/LOW/NONE")


def _authorship_labels(contract: dict[str, Any]) -> dict[int, str]:
    levels = contract["dimensions"]["authorship_origin"]["levels"]
    labels: dict[int, str] = {}
    for key, value in levels.items():
        if not isinstance(value, dict):
            raise RetrospectiveValidationError("authorship levels must be objects")
        labels[int(key)] = require_one_line(value.get("label"), f"authorship level {key}.label", max_length=80)
    return labels


def validate_rating(
    name: str,
    rating: Any,
    *,
    evidence_supports: dict[str, set[str]],
    confidence_levels: set[str],
) -> tuple[int | None, str]:
    if not isinstance(rating, dict):
        raise RetrospectiveValidationError(f"rating {name} must be an object")
    allowed = {"score", "confidence", "rationale", "evidence_refs"}
    if set(rating) != allowed:
        raise RetrospectiveValidationError(f"rating {name} fields must be exactly {sorted(allowed)}")
    score = rating.get("score")
    confidence = rating.get("confidence")
    if score is not None and (type(score) is not int or not 1 <= score <= 5):
        raise RetrospectiveValidationError(f"rating {name}.score must be null or integer 1..5")
    if confidence not in confidence_levels:
        raise RetrospectiveValidationError(f"rating {name}.confidence is invalid")
    require_one_line(rating.get("rationale"), f"rating {name}.rationale")
    refs = rating.get("evidence_refs")
    if not isinstance(refs, list) or any(not isinstance(item, str) or not item for item in refs):
        raise RetrospectiveValidationError(f"rating {name}.evidence_refs must be a string list")
    if len(refs) != len(set(refs)):
        raise RetrospectiveValidationError(f"rating {name}.evidence_refs must be unique")
    unknown = set(refs) - set(evidence_supports)
    if unknown:
        raise RetrospectiveValidationError(f"rating {name} references unknown evidence: {sorted(unknown)}")
    wrong_dimension = [ref for ref in refs if name not in evidence_supports[ref]]
    if wrong_dimension:
        raise RetrospectiveValidationError(
            f"rating {name} references evidence that does not support this dimension: {sorted(wrong_dimension)}"
        )
    if score is None and confidence != "NONE":
        raise RetrospectiveValidationError(f"rating {name} cannot have confidence without a score")
    if score is not None and confidence == "NONE":
        raise RetrospectiveValidationError(f"rating {name} with a score requires non-NONE confidence")
    if score is not None and not refs:
        raise RetrospectiveValidationError(f"rating {name} with a score requires evidence")
    return score, str(confidence)


def validate_evidence(items: Any, contract: dict[str, Any]) -> dict[str, set[str]]:
    if not isinstance(items, list):
        raise RetrospectiveValidationError("record.evidence must be a list")
    allowed_kinds = set(contract["record_contract"]["evidence_kinds"])
    supports_by_id: dict[str, set[str]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise RetrospectiveValidationError(f"evidence[{index}] must be an object")
        required = {"id", "kind", "ref", "supports", "summary"}
        if set(item) != required:
            raise RetrospectiveValidationError(f"evidence[{index}] fields must be exactly {sorted(required)}")
        evidence_id = require_one_line(item.get("id"), f"evidence[{index}].id", max_length=160)
        if evidence_id in supports_by_id:
            raise RetrospectiveValidationError(f"duplicate evidence id: {evidence_id}")
        if item.get("kind") not in allowed_kinds:
            raise RetrospectiveValidationError(f"evidence[{index}].kind is invalid")
        require_one_line(item.get("ref"), f"evidence[{index}].ref", max_length=240)
        require_one_line(item.get("summary"), f"evidence[{index}].summary")
        supports = item.get("supports")
        valid_supports = set(contract["record_contract"]["rating_dimensions"])
        if not isinstance(supports, list) or not supports or any(value not in valid_supports for value in supports):
            raise RetrospectiveValidationError(f"evidence[{index}].supports must name retrospective dimensions")
        if len(supports) != len(set(supports)):
            raise RetrospectiveValidationError(f"evidence[{index}].supports must be unique")
        supports_by_id[evidence_id] = set(supports)
    return supports_by_id


def validate_prompt_ids(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not PROMPT_ID_RE.fullmatch(item) for item in value):
        raise RetrospectiveValidationError(f"{field} must be a list of Prompt Kit IDs")
    if len(value) != len(set(value)):
        raise RetrospectiveValidationError(f"{field} must be unique")
    return list(value)


def _rating_evidence(record: dict[str, Any], dimension: str) -> list[dict[str, Any]]:
    refs = set(record["ratings"][dimension]["evidence_refs"])
    return [item for item in record["evidence"] if item["id"] in refs]


def _registry_evidence_matches_prompt(item: dict[str, Any], prompt_ids: list[str]) -> bool:
    ref = item["ref"]
    return any(ref.endswith(f"#{prompt_id}") for prompt_id in prompt_ids)


def validate_record(record: Any, contract: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise RetrospectiveValidationError("record must be an object")
    required = {
        "candidate_id", "status", "project", "prompt_anchor", "prompt_event_date",
        "prompt_event_window", "work_outcome", "ratings", "authorship_profile",
        "kit_assessment", "evidence",
    }
    if set(record) != required:
        raise RetrospectiveValidationError(f"record fields must be exactly {sorted(required)}")

    require_one_line(record.get("candidate_id"), "candidate_id", max_length=160)
    require_one_line(record.get("project"), "project", max_length=160)
    require_one_line(record.get("prompt_anchor"), "prompt_anchor", max_length=160)
    require_one_line(record.get("prompt_event_window"), "prompt_event_window", max_length=80)
    require_one_line(record.get("work_outcome"), "work_outcome")
    if record.get("prompt_event_date") is not None:
        require_one_line(record.get("prompt_event_date"), "prompt_event_date", max_length=32)
    if record.get("status") not in contract["record_contract"]["allowed_statuses"]:
        raise RetrospectiveValidationError("record.status is invalid")

    evidence_supports = validate_evidence(record["evidence"], contract)
    ratings = record.get("ratings")
    dimensions = contract["record_contract"]["rating_dimensions"]
    if not isinstance(ratings, dict) or set(ratings) != set(dimensions):
        raise RetrospectiveValidationError("record.ratings must contain exactly the four retrospective dimensions")
    confidence_levels = set(contract["record_contract"]["confidence_levels"])
    scored: dict[str, tuple[int | None, str]] = {
        name: validate_rating(
            name,
            ratings[name],
            evidence_supports=evidence_supports,
            confidence_levels=confidence_levels,
        )
        for name in dimensions
    }

    profile = record.get("authorship_profile")
    if not isinstance(profile, dict):
        raise RetrospectiveValidationError("authorship_profile must be an object")
    profile_fields = {
        "origin_label", "comparison_basis", "contemporaneous_prompt_kit_ref",
        "current_prompt_kit_ref", "matched_prompt_ids", "match_kind",
        "manual_novelty_signals", "historical_origin_status",
    }
    if set(profile) != profile_fields:
        raise RetrospectiveValidationError("authorship_profile fields are invalid")
    if profile.get("comparison_basis") not in contract["authorship_evidence_policy"]["comparison_basis"]:
        raise RetrospectiveValidationError("authorship_profile.comparison_basis is invalid")
    if profile.get("match_kind") not in contract["authorship_evidence_policy"]["match_kind"]:
        raise RetrospectiveValidationError("authorship_profile.match_kind is invalid")
    matched_ids = validate_prompt_ids(profile.get("matched_prompt_ids"), "authorship_profile.matched_prompt_ids")
    novelty = profile.get("manual_novelty_signals")
    if not isinstance(novelty, list) or any(not isinstance(item, str) or not item.strip() for item in novelty):
        raise RetrospectiveValidationError("manual_novelty_signals must be a string list")
    if len(novelty) != len(set(novelty)):
        raise RetrospectiveValidationError("manual_novelty_signals must be unique")
    require_one_line(profile.get("historical_origin_status"), "authorship_profile.historical_origin_status", max_length=160)
    if profile.get("current_prompt_kit_ref") is not None:
        require_one_line(profile.get("current_prompt_kit_ref"), "authorship_profile.current_prompt_kit_ref", max_length=160)
    if profile.get("contemporaneous_prompt_kit_ref") is not None:
        require_one_line(profile.get("contemporaneous_prompt_kit_ref"), "authorship_profile.contemporaneous_prompt_kit_ref", max_length=160)

    authorship_score, authorship_confidence = scored["authorship_origin"]
    labels = _authorship_labels(contract)
    expected_label = "UNRESOLVED" if authorship_score is None else labels[authorship_score]
    if profile.get("origin_label") != expected_label:
        raise RetrospectiveValidationError(
            f"authorship origin_label must be {expected_label} for score {authorship_score}"
        )

    authorship_evidence = _rating_evidence(record, "authorship_origin")
    historical_authorship_evidence = [item for item in authorship_evidence if item["kind"] == "historical_registry"]
    matching_historical_evidence = [
        item
        for item in historical_authorship_evidence
        if _registry_evidence_matches_prompt(item, matched_ids)
    ]

    if authorship_score is not None:
        if profile.get("comparison_basis") not in {"CONTEMPORANEOUS", "MIXED"}:
            raise RetrospectiveValidationError("scored authorship requires contemporaneous comparison evidence")
        if not profile.get("contemporaneous_prompt_kit_ref"):
            raise RetrospectiveValidationError("scored authorship requires contemporaneous Prompt Kit ref")
    if authorship_score == 1:
        if not matched_ids or profile.get("match_kind") != "EXACT":
            raise RetrospectiveValidationError("CANONICAL_REUSE requires matched Prompt Kit ID and exact full-prompt match")
        if novelty:
            raise RetrospectiveValidationError("CANONICAL_REUSE cannot include manual novelty signals")
        if not matching_historical_evidence:
            raise RetrospectiveValidationError("CANONICAL_REUSE requires matching historical_registry evidence")
    if authorship_score == 2:
        if not matched_ids or profile.get("match_kind") not in {"EXACT", "MATERIAL"}:
            raise RetrospectiveValidationError("REUSE_DOMINANT requires matched Prompt Kit ID and exact/material match")
        if not novelty:
            raise RetrospectiveValidationError("REUSE_DOMINANT requires manual tailoring signals")
        if not matching_historical_evidence:
            raise RetrospectiveValidationError("REUSE_DOMINANT requires matching historical_registry evidence")
    if authorship_score == 3:
        if not matched_ids:
            raise RetrospectiveValidationError("HYBRID authorship requires a matched Prompt Kit ID")
        if not novelty:
            raise RetrospectiveValidationError("HYBRID authorship requires manual novelty signals")
        if profile.get("match_kind") not in {"MATERIAL", "DOCTRINE_ONLY"}:
            raise RetrospectiveValidationError("HYBRID authorship requires material/doctrine Prompt Kit evidence")
        if not matching_historical_evidence:
            raise RetrospectiveValidationError("HYBRID authorship requires matching historical_registry evidence")
    if authorship_score == 4:
        if not matched_ids or profile.get("match_kind") != "DOCTRINE_ONLY":
            raise RetrospectiveValidationError("MANUAL_DOMINANT requires a matched doctrine-only Prompt Kit influence")
        if not novelty:
            raise RetrospectiveValidationError("MANUAL_DOMINANT requires manual novelty signals")
        if not matching_historical_evidence:
            raise RetrospectiveValidationError("MANUAL_DOMINANT requires matching historical_registry evidence")
    if authorship_score == 5:
        if matched_ids:
            raise RetrospectiveValidationError("MANUAL_ORIGINAL cannot retain matched Prompt Kit IDs")
        if profile.get("match_kind") != "NONE":
            raise RetrospectiveValidationError("MANUAL_ORIGINAL requires no material contemporaneous match")
        if not novelty:
            raise RetrospectiveValidationError("MANUAL_ORIGINAL requires manual novelty signals")
        if not historical_authorship_evidence:
            raise RetrospectiveValidationError("MANUAL_ORIGINAL requires historical_registry no-match evidence")
    if authorship_confidence == "HIGH":
        if profile.get("comparison_basis") not in {"CONTEMPORANEOUS", "MIXED"}:
            raise RetrospectiveValidationError("HIGH authorship confidence requires contemporaneous evidence")
        if not profile.get("contemporaneous_prompt_kit_ref"):
            raise RetrospectiveValidationError("HIGH authorship confidence requires contemporaneous Prompt Kit ref")
    if profile.get("comparison_basis") in {"CONTEMPORANEOUS", "MIXED"} and not profile.get("contemporaneous_prompt_kit_ref"):
        raise RetrospectiveValidationError("contemporaneous comparison basis requires contemporaneous Prompt Kit ref")

    kit = record.get("kit_assessment")
    if not isinstance(kit, dict):
        raise RetrospectiveValidationError("kit_assessment must be an object")
    kit_fields = {"evaluation_basis", "prior_art_complete", "topology_ref", "matched_prompt_ids", "disposition"}
    if set(kit) != kit_fields:
        raise RetrospectiveValidationError("kit_assessment fields are invalid")
    if kit.get("evaluation_basis") not in {"CURRENT", "CONTEMPORANEOUS"}:
        raise RetrospectiveValidationError("kit_assessment.evaluation_basis is invalid")
    if type(kit.get("prior_art_complete")) is not bool:
        raise RetrospectiveValidationError("kit_assessment.prior_art_complete must be boolean")
    kit_matches = validate_prompt_ids(kit.get("matched_prompt_ids"), "kit_assessment.matched_prompt_ids")
    if kit.get("disposition") not in contract["gap_policy"]["dispositions"]:
        raise RetrospectiveValidationError("kit_assessment.disposition is invalid")
    if kit.get("topology_ref") is not None:
        require_one_line(kit.get("topology_ref"), "kit_assessment.topology_ref", max_length=240)

    gap_score, _gap_confidence = scored["prompt_kit_gap"]
    gap_evidence = _rating_evidence(record, "prompt_kit_gap")
    current_gap_evidence = [item for item in gap_evidence if item["kind"] in {"current_registry", "topology"}]
    if gap_score is not None:
        if kit.get("evaluation_basis") != "CURRENT":
            raise RetrospectiveValidationError("scored Prompt Kit gap requires CURRENT evaluation basis")
        if not current_gap_evidence:
            raise RetrospectiveValidationError("scored Prompt Kit gap requires current registry or topology evidence")
    if gap_score == 1:
        matching_current_evidence = [
            item
            for item in current_gap_evidence
            if item["kind"] == "current_registry" and _registry_evidence_matches_prompt(item, kit_matches)
        ]
        if not kit_matches or kit.get("disposition") != "NO_KIT_CHANGE":
            raise RetrospectiveValidationError("gap score 1 requires matched current owner and NO_KIT_CHANGE")
        if not matching_current_evidence:
            raise RetrospectiveValidationError("gap score 1 requires current_registry evidence for the matched current owner")
    if gap_score == 5:
        topology_evidence = [
            item
            for item in gap_evidence
            if item["kind"] == "topology" and item["ref"] == kit.get("topology_ref")
        ]
        if not kit.get("prior_art_complete") or not kit.get("topology_ref") or kit.get("disposition") != "CREATE_NEW_REVIEW":
            raise RetrospectiveValidationError("gap score 5 requires completed prior-art/topology review and CREATE_NEW_REVIEW")
        if not topology_evidence:
            raise RetrospectiveValidationError("gap score 5 requires topology evidence matching topology_ref")
    if kit.get("disposition") == "CREATE_NEW_REVIEW" and not kit.get("prior_art_complete"):
        raise RetrospectiveValidationError("CREATE_NEW_REVIEW requires completed prior-art review")


def validate_register(register: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    if register.get("schema_version") != contract["record_contract"]["schema_version"]:
        raise RetrospectiveValidationError("unsupported retrospective register schema")
    if register.get("contract") != "harness/contracts/prompt-retrospective-evaluation.v1.json":
        raise RetrospectiveValidationError("register must bind the canonical retrospective contract")
    require_one_line(register.get("evaluation_id"), "evaluation_id", max_length=160)
    require_one_line(register.get("evaluation_time"), "evaluation_time", max_length=80)
    if register.get("authority") != "REVIEW_ONLY":
        raise RetrospectiveValidationError("register authority must remain REVIEW_ONLY")
    if register.get("priority_policy") != contract["record_contract"]["priority_policy"]:
        raise RetrospectiveValidationError("priority policy must remain explicitly uncomputed")
    records = register.get("records")
    if not isinstance(records, list) or not records:
        raise RetrospectiveValidationError("register.records must be a non-empty list")
    ids: set[str] = set()
    for record in records:
        validate_record(record, contract)
        candidate_id = record["candidate_id"]
        if candidate_id in ids:
            raise RetrospectiveValidationError(f"duplicate candidate_id: {candidate_id}")
        ids.add(candidate_id)
    return {
        "schema_version": register["schema_version"],
        "evaluation_id": register["evaluation_id"],
        "records": len(records),
        "scored_ratings": sum(
            1
            for record in records
            for rating in record["ratings"].values()
            if rating["score"] is not None
        ),
        "unresolved_authorship": sum(
            1 for record in records if record["ratings"]["authorship_origin"]["score"] is None
        ),
        "authority": register["authority"],
        "priority_policy": register["priority_policy"],
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--input", type=Path, default=DEFAULT_REGISTER)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    contract = load_json(args.contract)
    validate_contract(contract)
    register = load_json(args.input)
    summary = validate_register(register, contract)
    if args.summary:
        print(
            "prompt-retrospective: PASS "
            f"records={summary['records']} "
            f"scored={summary['scored_ratings']} "
            f"unresolved_authorship={summary['unresolved_authorship']} "
            f"authority={summary['authority']} "
            f"priority={summary['priority_policy']}"
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
