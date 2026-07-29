#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "prompt-kit-discovery.v1.json"
JS = ROOT / "docs" / "prompt-kit.js"
BUILDER = ROOT / "build_prompt_kit.py"
DEPLOYED = ROOT / "web" / "prompt-kit" / "index.html"
REQUIRED_IDS = {
    "section_heading_contrast",
    "ranked_search",
    "synonym_routing",
    "body_noise_suppression",
    "local_favorites",
    "favorites_first",
    "favorite_accessibility",
    "generated_site_parity",
}


def audit() -> dict[str, object]:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    js = JS.read_text(encoding="utf-8")
    builder = BUILDER.read_text(encoding="utf-8")
    deployed = DEPLOYED.read_text(encoding="utf-8")
    ids = {item["id"] for item in payload.get("requirements", [])}
    missing: list[str] = []
    if payload.get("schema_version") != "prompt-kit-discovery-contract/v1":
        missing.append("schema_version")
    if ids != REQUIRED_IDS:
        missing.append("requirement_ids")
    markers = {
        "section_heading_contrast": ".section-divider .section-toggle{color:var(--text-primary)",
        "ranked_search": "function scorePromptForQuery(p,q,synIds)",
        "synonym_routing": "function synonymPromptIdsForQuery(q)",
        "body_noise_suppression": "strongFloor=maxScore>=40?10:1",
        "local_favorites": "promptKit.favoritePromptIds.v1",
        "favorites_first": "name:'Favorites',glow:'#fbbf24'",
        "favorite_accessibility": "favBtn.setAttribute('aria-pressed'",
    }
    for requirement_id, marker in markers.items():
        if marker not in js:
            missing.append(requirement_id)
    if "var SYNONYMS=" not in deployed or "SYNONYMS = {" not in builder:
        missing.append("synonym_source")
    if js not in deployed:
        missing.append("generated_site_parity")
    return {
        "contract": payload.get("contract_id"),
        "requirements": len(REQUIRED_IDS),
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
