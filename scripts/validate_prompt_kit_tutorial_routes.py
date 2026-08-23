#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import build_prompt_kit_registry

ROOT = Path(__file__).resolve().parents[1]
GUIDED = ROOT / "docs" / "prompt-kit-guided-recommendations.js"

REQUIRED_MARKERS = (
    "var FIXED_PROMPT_FINDER_QUESTIONS=[",
    "var PROMPT_FINDER_MAX_QUESTIONS=5",
    "var ADAPTIVE_CANDIDATE_LIMIT=6",
    "function scorePromptFinderCandidates(answers)",
    "function renderAdaptiveQuestion()",
    "Something else — show every prompt",
    "function renderSpecialistQuestion()",
    "function specialistPrompts(query)",
    "if(!q)return PROMPTS.slice().sort",
    "return sharedSearch(q)",
    "S.selectedPromptId=b.getAttribute('data-finder-specialist-prompt')",
    "function resultItemsForSelectedPrompt()",
    "PROMPTS.find(function(prompt){return prompt.id===S.selectedPromptId})",
)

FORBIDDEN_MARKERS = (
    "slice(0,5)",
    "var R=",
    "NEXT_PROMPT_MAP",
)


def audit() -> dict[str, object]:
    guided = GUIDED.read_text(encoding="utf-8")
    prompts = build_prompt_kit_registry.load_prompt_kit_registry()
    ids = [str(prompt["id"]) for prompt in prompts]
    missing_markers = [marker for marker in REQUIRED_MARKERS if marker not in guided]
    forbidden_markers = [marker for marker in FORBIDDEN_MARKERS if marker in guided]
    duplicate_ids = sorted({prompt_id for prompt_id in ids if ids.count(prompt_id) > 1})

    # The optional fifth question renders PROMPTS itself when the filter is empty.
    # Therefore every current registry record is directly selectable without a
    # hard-coded prompt-ID routing table.
    fallback_is_complete = not missing_markers and not duplicate_ids
    routes = [
        {
            "prompt_id": prompt_id,
            "route": "adaptive_specialist_fallback",
            "reachable": fallback_is_complete,
        }
        for prompt_id in ids
    ]
    unreachable = [item["prompt_id"] for item in routes if not item["reachable"]]

    return {
        "contract": "prompt-kit-tutorial-route-coverage/v1",
        "prompt_count": len(prompts),
        "fixed_questions": 3,
        "default_questions": 4,
        "max_questions": 5,
        "adaptive_candidate_limit": 6,
        "reachable_count": len(prompts) - len(unreachable),
        "unreachable": unreachable,
        "duplicate_prompt_ids": duplicate_ids,
        "missing_markers": missing_markers,
        "forbidden_markers": forbidden_markers,
        "ready": not unreachable and not duplicate_ids and not missing_markers and not forbidden_markers,
        "routes": routes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary:
        summary = {key: value for key, value in report.items() if key != "routes"}
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
