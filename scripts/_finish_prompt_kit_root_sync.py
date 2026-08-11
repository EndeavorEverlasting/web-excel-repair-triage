#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_ID = "prompt-kit-responsive-layout-audit"
TEST_ID = "prompt-kit-responsive-layout-tests"
AUDIT_CMD = "python scripts/validate_prompt_kit_layout_harness.py --summary"
TEST_CMD = "python -m unittest tests.test_prompt_kit_layout_harness -v"
HEADER_CMD = "python tests/test_prompt_kit_header_contract.py"
SKILL = ".ai/skills/prompt-kit-responsive-layout/SKILL.md"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def dump(rel: str, value) -> None:
    (ROOT / rel).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def normalize_validation_order() -> None:
    manifest = load("harness/manifest.v1.json")
    order = manifest["validation_order"]
    order[:] = [item for item in order if item not in {AUDIT_CMD, TEST_CMD}]
    anchor = order.index(HEADER_CMD)
    order[anchor:anchor] = [AUDIT_CMD, TEST_CMD]
    dump("harness/manifest.v1.json", manifest)

    validators = load("harness/validators.v1.json")
    for profile in ("harness", "pre_push"):
        ids = validators["profiles"][profile]
        ids[:] = [item for item in ids if item not in {AUDIT_ID, TEST_ID}]
        header_id = ids.index("prompt-kit-header-contract")
        ids[header_id:header_id] = [AUDIT_ID, TEST_ID]
    dump("harness/validators.v1.json", validators)


def index_skill() -> None:
    path = ROOT / "SKILLS.md"
    text = path.read_text(encoding="utf-8")
    if SKILL in text:
        return
    anchor = "## Required skill-file sections"
    if anchor not in text:
        raise SystemExit("SKILLS.md required-sections anchor missing")
    section = """### Prompt Kit responsive layout audit

- **Path:** `.ai/skills/prompt-kit-responsive-layout/SKILL.md`
- **Trigger:** `prompt-kit-responsive-overlap`
- **Capability:** `prompt-kit-responsive-layout`
- **Use when:** Prompt Kit brand, search, filter, or navigation controls overlap, escape the header, overflow horizontally, or need strict responsive proof.
- **Proof boundary:** Static source/artifact checks do not prove browser geometry; strict no-overlap proof requires the registered all-viewport geometry receipt.
- **Primary validation:** `python scripts/validate_prompt_kit_layout_harness.py --summary` and `python -m unittest tests.test_prompt_kit_layout_harness -v`; strict geometry uses `--require-implementation --geometry-report Outputs/prompt-kit-layout-geometry.json`.

"""
    text = text.replace(anchor, section + anchor, 1)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    normalize_validation_order()
    index_skill()


if __name__ == "__main__":
    main()
