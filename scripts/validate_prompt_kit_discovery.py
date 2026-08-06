#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-discovery.v1.json"
JS = ROOT / "docs" / "prompt-kit.js"
GUIDED_JS = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
BUILDER = ROOT / "build_prompt_kit.py"
REGISTRY_BUILDER = ROOT / "scripts" / "build_prompt_kit_registry.py"
DISPLAY_ORDER = ROOT / "registry" / "prompts" / "prompt-display-order.v1.json"
TUTORIAL_PROMPTS = ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json"
TUTORIAL = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
REQUIRED_IDS = {
    "section_heading_contrast",
    "ranked_search",
    "synonym_routing",
    "body_noise_suppression",
    "local_favorites",
    "favorites_first",
    "favorite_accessibility",
    "guided_questionnaire",
    "metadata_recommendations",
    "stable_identity_resequence",
    "registry_prompt_fallback",
    "generated_site_parity",
}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def audit() -> dict[str, object]:
    payload = _load_json(CONTRACT)
    js = JS.read_text(encoding="utf-8")
    guided_js = GUIDED_JS.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")
    registry_builder = REGISTRY_BUILDER.read_text(encoding="utf-8")
    deployed = DEPLOYED.read_text(encoding="utf-8")
    tutorial = TUTORIAL.read_text(encoding="utf-8")
    order = _load_json(DISPLAY_ORDER)
    extension = _load_json(TUTORIAL_PROMPTS)
    ids = {item["id"] for item in payload.get("requirements", [])}
    missing: list[str] = []

    if payload.get("schema_version") != "prompt-kit-discovery-contract/v1":
        missing.append("schema_version")
    if ids != REQUIRED_IDS:
        missing.append("requirement_ids")

    base_markers = {
        "section_heading_contrast": ".section-divider .section-toggle{color:var(--text-primary)",
        "ranked_search": "function scorePromptForQuery(p,q,synIds)",
        "synonym_routing": "function synonymPromptIdsForQuery(q)",
        "body_noise_suppression": "strongFloor=maxScore>=40?10:1",
        "local_favorites": "promptKit.favoritePromptIds.v1",
        "favorites_first": "name:'Favorites',glow:'#fbbf24'",
        "favorite_accessibility": "favBtn.setAttribute('aria-pressed'",
    }
    for requirement_id, marker in base_markers.items():
        if marker not in js:
            missing.append(requirement_id)

    guided_markers = {
        "guided_questionnaire": (
            "PROMPT_FINDER_QUESTIONS",
            "Find My Prompt",
            "Primary recommendation",
            "slice(0,3)",
            "promptFinderBtn",
            "prompt-header-actions",
            "actions.appendChild(addButton)",
        ),
        "metadata_recommendations": (
            "PROMPTS.find",
            "registered(",
            "copyPrompt(",
            "showPromptDetail(",
        ),
        "stable_identity_resequence": (
            "discoveryRank",
            "window.promptSequenceValue=rank",
        ),
    }
    for requirement_id, markers in guided_markers.items():
        if any(marker not in guided_js for marker in markers):
            missing.append(requirement_id)
    if "replaceChild(button,old)" in guided_js:
        missing.append("guided_questionnaire")

    if "var SYNONYMS=" not in deployed or "SYNONYMS = {" not in builder:
        missing.append("synonym_source")

    if not isinstance(order, dict) or order.get("schema_version") != "prompt-display-order/v1":
        missing.append("display_order_schema")
    promoted = order.get("promoted_prompt_ids", []) if isinstance(order, dict) else []
    if (
        not isinstance(promoted, list)
        or not promoted
        or promoted[0] != "P65"
        or len(promoted) != len(set(promoted))
        or order.get("fallback") != "sequence_ascending"
    ):
        missing.append("stable_identity_resequence")
    for marker in ("discoveryRank", "apply_display_order", "prompt-display-order/v1"):
        if marker not in registry_builder:
            missing.append("stable_identity_resequence")
            break

    prompts = extension.get("prompts", []) if isinstance(extension, dict) else []
    by_id = {
        item.get("id"): item
        for item in prompts
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if (
        extension.get("schema_version") != "prompt-registry-extension/v1"
        or "P64" not in by_id
        or "P65" not in by_id
        or "one concise question at a time" not in by_id.get("P65", {}).get("copyContent", "")
        or "RANK TUTORIAL PATHS WORTH SPRINTING" not in by_id.get("P64", {}).get("copyContent", "")
        or "Conversational fallback" not in tutorial
    ):
        missing.append("registry_prompt_fallback")

    if js not in deployed or guided_js not in deployed:
        missing.append("generated_site_parity")
    for marker in ('"id": "P64"', '"id": "P65"', "Find My Prompt"):
        if marker not in deployed:
            missing.append("generated_site_parity")
            break

    missing = list(dict.fromkeys(missing))
    return {
        "contract": payload.get("contract_id"),
        "requirements": len(REQUIRED_IDS),
        "promoted_prompts": len(promoted) if isinstance(promoted, list) else 0,
        "guided_prompts": sorted(by_id),
        "ready": not missing,
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    report = audit()
    if args.summary:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
