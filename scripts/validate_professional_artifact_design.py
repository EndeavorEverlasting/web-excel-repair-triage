#!/usr/bin/env python3
"""Validate the professional artifact product-design contract and its Prompt Kit seam."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "professional-artifact-design.v1.json"
DRAFT = ROOT / "harness" / "fixtures" / "prompt-contributions" / "professional-artifact-archetype-builder.draft.json"
CASES = ROOT / "harness" / "fixtures" / "prompt-contributions" / "professional-artifact-archetype-builder.regression-cases.json"
CONTEXT = ROOT / "harness" / "CONTEXT.md"

REQUIRED_PRINCIPLES = {
    "semantic_truth_before_style",
    "visual_authority_precedence",
    "scene_architecture_before_decoration",
    "motion_has_semantic_job",
    "evidence_illustration_boundary",
    "composition_before_palette",
    "prototype_render_compare",
    "durable_backport",
}
REQUIRED_HARD_FAILURES = {
    "collision_or_overflow",
    "generic_blank_canvas_default",
    "palette_only_polish",
    "motion_without_meaning",
    "teleporting_continuity",
    "evidence_illustration_conflation",
    "unreadable_density",
    "single_layout_everywhere",
}
REQUIRED_UPSTREAM = {
    "revealjs-auto-animate",
    "revealjs-backgrounds",
    "slidev-animations-components",
    "motion-canvas-scenes",
    "remotion-transition-series",
    "pptxgenjs-masters-notes",
}
REQUIRED_CASES = {f"PAAB{i:03d}" for i in range(13, 20)}
REQUIRED_PROMPT_PHRASES = (
    "sequence of scenes",
    "one dominant message per frame",
    "stable element identities",
    "semantic transition plan",
    "authentic evidence separately from illustrative scenery",
    "collisions/overflow",
    "SCENE/MOTION",
)
FORBIDDEN_PROJECT_TERMS = ("PAXSTORE", "Kiosk4", "NYC H&H")


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(rows: list[dict]) -> set[str]:
    return {str(row.get("id", "")) for row in rows}


def validate() -> dict:
    contract = load_json(CONTRACT)
    draft = load_json(DRAFT)
    cases = load_json(CASES)
    context = CONTEXT.read_text(encoding="utf-8")

    if contract.get("schema_version") != "professional-artifact-design/v1":
        raise ValidationError("unexpected professional artifact design schema")
    if contract.get("owner") != "P01":
        raise ValidationError("P01 must own the professional artifact design harness contract")

    missing_principles = REQUIRED_PRINCIPLES - _ids(contract.get("principles", []))
    if missing_principles:
        raise ValidationError(f"missing design principles: {sorted(missing_principles)}")

    missing_failures = REQUIRED_HARD_FAILURES - _ids(contract.get("hard_failures", []))
    if missing_failures:
        raise ValidationError(f"missing hard failures: {sorted(missing_failures)}")

    upstream = {row.get("id"): row for row in contract.get("upstream_prior_art", [])}
    missing_upstream = REQUIRED_UPSTREAM - set(upstream)
    if missing_upstream:
        raise ValidationError(f"missing P97 prior-art mechanics: {sorted(missing_upstream)}")
    for source_id in REQUIRED_UPSTREAM:
        row = upstream[source_id]
        if row.get("evidence_state") != "OBSERVED_IMPLEMENTED":
            raise ValidationError(f"{source_id} must retain OBSERVED_IMPLEMENTED evidence semantics")
        if row.get("disposition") not in {"ADOPT", "ADAPT"}:
            raise ValidationError(f"{source_id} must be ADOPT or ADAPT")
        if not str(row.get("source", "")).startswith("https://"):
            raise ValidationError(f"{source_id} must retain a concrete upstream URL")

    serialized = json.dumps(contract, ensure_ascii=False)
    leaked = [term for term in FORBIDDEN_PROJECT_TERMS if term in serialized]
    if leaked:
        raise ValidationError(f"project-specific terms leaked into reusable contract: {leaked}")

    copy = str(draft.get("copyContent", ""))
    missing_phrases = [phrase for phrase in REQUIRED_PROMPT_PHRASES if phrase not in copy]
    if missing_phrases:
        raise ValidationError(f"candidate prompt missing cinematic product-design phrases: {missing_phrases}")
    if len(copy) > 12000:
        raise ValidationError(f"candidate copyContent exceeds protected contribution ceiling: {len(copy)}")

    case_ids = {str(row.get("id", "")) for row in cases.get("cases", [])}
    missing_cases = REQUIRED_CASES - case_ids
    if missing_cases:
        raise ValidationError(f"missing cinematic regression cases: {sorted(missing_cases)}")

    if "professional-artifact-design.v1.json" not in context:
        raise ValidationError("50k context router does not expose professional artifact design contract")
    if "presentation design quality" not in context.lower():
        raise ValidationError("50k context router lacks presentation design quality route")

    scene = contract.get("presentation_cinematic", {}).get("scene_contract", {})
    for field in (
        "dominant_message",
        "visual_anchor",
        "spatial_layers",
        "evidence_staging",
        "continuity_identity",
        "transition_intent",
        "deck_rhythm",
        "static_fallback",
    ):
        if not str(scene.get(field, "")).strip():
            raise ValidationError(f"scene contract missing {field}")

    return {
        "state": "PASS",
        "contract": str(CONTRACT.relative_to(ROOT)),
        "owner": contract["owner"],
        "principle_count": len(contract["principles"]),
        "hard_failure_count": len(contract["hard_failures"]),
        "upstream_prior_art_count": len(contract["upstream_prior_art"]),
        "cinematic_regression_case_count": len(REQUIRED_CASES),
        "candidate_copy_chars": len(copy),
        "proof_ceiling": contract["proof_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        result = validate()
    except (OSError, ValueError, ValidationError) as exc:
        if args.summary:
            print(f"professional-artifact-design: FAIL — {exc}")
        else:
            print(json.dumps({"state": "FAIL", "error": str(exc)}, indent=2))
        return 1
    if args.summary:
        print(
            "professional-artifact-design: PASS — "
            f"{result['principle_count']} principles, "
            f"{result['hard_failure_count']} hard failures, "
            f"{result['upstream_prior_art_count']} upstream mechanics, "
            f"{result['cinematic_regression_case_count']} cinematic regressions, "
            f"{result['candidate_copy_chars']} prompt chars"
        )
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
