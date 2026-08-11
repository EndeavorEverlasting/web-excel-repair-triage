#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dump(rel: str, value) -> None:
    (ROOT / rel).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sync_validator_registry() -> None:
    rel = "harness/validators.v1.json"
    payload = load(rel)
    existing = {item["id"] for item in payload["validators"]}
    additions = [
        {
            "id": "prompt-kit-responsive-layout-audit",
            "class": "contract",
            "command": "python scripts/validate_prompt_kit_layout_harness.py --summary",
            "blocking": True,
            "output": "process log",
            "proof_ceiling": "Static responsive-layout harness and contract completeness proof; no browser geometry proof.",
        },
        {
            "id": "prompt-kit-responsive-layout-tests",
            "class": "test",
            "command": "python -m unittest tests.test_prompt_kit_layout_harness -v",
            "blocking": True,
            "output": "process log",
            "proof_ceiling": "Executable responsive-layout harness regression proof; strict browser geometry remains separate.",
        },
    ]
    anchor = next(i for i, item in enumerate(payload["validators"]) if item["id"] == "prompt-kit-header-contract")
    for item in reversed(additions):
        if item["id"] not in existing:
            payload["validators"].insert(anchor, item)
    for profile in ("harness", "pre_push"):
        ids = payload["profiles"][profile]
        anchor = ids.index("prompt-kit-header-contract")
        for validator_id in reversed(["prompt-kit-responsive-layout-audit", "prompt-kit-responsive-layout-tests"]):
            if validator_id not in ids:
                ids.insert(anchor, validator_id)
    dump(rel, payload)


def sync_root_validator_constants() -> None:
    path = ROOT / "scripts/validate_harness.py"
    source = path.read_text(encoding="utf-8")
    replacements = [
        (
            '    "prompt-kit-browser-proof-cleanup-powershell-smoke",\n}\nREQUIRED_CAPABILITY_IDS',
            '    "prompt-kit-browser-proof-cleanup-powershell-smoke",\n    "prompt-kit-responsive-layout-audit",\n    "prompt-kit-responsive-layout-tests",\n}\nREQUIRED_CAPABILITY_IDS',
        ),
        (
            '    "prompt-kit-browser-proof-scratch-cleanup",\n}\nREQUIRED_TRIGGER_IDS',
            '    "prompt-kit-browser-proof-scratch-cleanup",\n    "prompt-kit-responsive-layout",\n}\nREQUIRED_TRIGGER_IDS',
        ),
        (
            '    "prompt-kit-browser-proof-temp-path",\n}\nPROTECTED_PATHS',
            '    "prompt-kit-browser-proof-temp-path",\n    "prompt-kit-responsive-overlap",\n}\nPROTECTED_PATHS',
        ),
    ]
    for old, new in replacements:
        if old not in source:
            raise SystemExit(f"root harness validator synchronization marker missing: {old[:60]}")
        source = source.replace(old, new, 1)
    path.write_text(source, encoding="utf-8")


def sync_trigger_route() -> None:
    rel = "harness/triggers.v1.json"
    payload = load(rel)
    trigger = next(item for item in payload["triggers"] if item["id"] == "prompt-kit-responsive-overlap")
    trigger["workflow"] = "WORKFLOW.md#c-harness-infrastructure-change"
    dump(rel, payload)


def normalize_skill() -> None:
    path = ROOT / ".ai/skills/prompt-kit-responsive-layout/SKILL.md"
    path.write_text(
        """# Prompt Kit Responsive Layout Audit

## Trigger
Use when Prompt Kit controls overlap, clip, escape their header/container, create horizontal page overflow, behave differently across viewport widths, or strict browser no-overlap proof is requested.

## Required inputs
- repository and exact branch/commit when available;
- viewport width/height or screenshot dimensions;
- elements involved in the collision;
- whether the lane may edit product code;
- current browser/runtime evidence if any.

## Outputs
- harness validation receipt;
- focused source/generated-artifact regression proof;
- browser geometry receipt when strict product proof is actually observed;
- exact files, commit/PR evidence, proof ceiling, and next executable gate.

## Procedure
1. Read `AGENTS.md`, the root harness registration, `harness/prompt-kit-layout/manifest.v1.json`, and the responsive-header collision contract.
2. Classify the symptom: brand/search, filter/search, container escape, horizontal overflow, touch-target regression, or another bounded layout defect.
3. In a harness-only lane, update harness evidence/contracts/validators without claiming product repair.
4. In a product lane, repair the canonical authored layout source, rebuild the registered generated site, and run Prompt Kit header/mobile checks.
5. For strict browser proof, measure bounding rectangles at every declared viewport and emit the registered geometry receipt. Any forbidden intersection, escape, overflow, missing viewport, or unusable touch target fails.
6. Record runtime evidence only under `Outputs/`, report the actual proof ceiling, and hand off the next executable gate.

## Guardrails
- Never treat one screenshot, a media-query marker, or an editable implementation-status string as browser geometry proof.
- Never hand-edit `web/prompt-kit/index.html`; use the canonical builder.
- Never shrink controls below usable accessibility/touch dimensions merely to remove collisions.
- Preserve unrelated work and keep browser/live-target mutation outside a static harness lane.

## Validation
- `python scripts/validate_prompt_kit_layout_harness.py --summary`
- `python -m unittest tests.test_prompt_kit_layout_harness -v`
- Strict only with real geometry: `python scripts/validate_prompt_kit_layout_harness.py --require-implementation --geometry-report Outputs/prompt-kit-layout-geometry.json --summary`
- Rebuild/parity and header contracts when product source changes.

## Proof ceiling
Default validation proves tracked responsive-layout contracts, registration, source markers, and generated-artifact regressions only. Observed no-overlap behavior requires a validated browser-geometry receipt covering every declared viewport; production/operator acceptance remains higher proof.
""",
        encoding="utf-8",
    )


def preserve_existing_layout_test_phrase() -> None:
    path = ROOT / "scripts/validate_prompt_kit_layout_harness.py"
    text = path.read_text(encoding="utf-8")
    old = "product responsive-layout implementation is not fully proven; status must be implemented"
    new = "product responsive-layout implementation is not yet proven; status must be implemented"
    if old in text:
        text = text.replace(old, new, 1)
    if new not in text:
        raise SystemExit("layout proof wording marker missing")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    preserve_existing_layout_test_phrase()
    sync_validator_registry()
    sync_root_validator_constants()
    sync_trigger_route()
    normalize_skill()


if __name__ == "__main__":
    main()
