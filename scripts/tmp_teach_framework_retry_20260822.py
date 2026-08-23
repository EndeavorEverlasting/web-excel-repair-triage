#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import tmp_teach_framework_contribution_20260822 as impl

FOCUSED = Path(__file__).resolve().parents[1] / "tests/test_prompt_registry_expansion_regression_design_teach.py"


def repair_existing_expectations() -> None:
    text = FOCUSED.read_text(encoding="utf-8")

    old_pair = '            "DIAGNOSTIC CHECK",\n            "PRACTICAL HARNESS",\n'
    new_pair = '            "CONCEPTUAL TRADE-OFF / MECHANISM",\n            "CODE DIAGNOSTIC / EDGE CASE",\n'
    if old_pair in text:
        text = text.replace(old_pair, new_pair, 1)
    elif new_pair not in text:
        raise SystemExit("teach checkpoint assertion anchor not found")

    old_mastery = '            "MASTERED requires demonstrated retrieval and practical application",\n'
    new_mastery = '            "VERIFY BEFORE WRITING THE LEARNING RECORD",\n'
    if old_mastery in text:
        text = text.replace(old_mastery, new_mastery, 1)
    elif new_mastery not in text:
        raise SystemExit("teach mastery assertion anchor not found")

    FOCUSED.write_text(text, encoding="utf-8")


def patch_route_test_mutator() -> None:
    original = impl.base.route_and_test

    def routed(receipt: dict) -> None:
        original(receipt)
        text = FOCUSED.read_text(encoding="utf-8")
        old = '            "exactly two learner checkpoints",\n'
        new = '            "EXACTLY TWO LEARNER CHECKPOINTS",\n'
        if old in text:
            text = text.replace(old, new, 1)
        elif new not in text:
            raise SystemExit("routed teach checkpoint count assertion not found")
        FOCUSED.write_text(text, encoding="utf-8")

    impl.base.route_and_test = routed


if __name__ == "__main__":
    repair_existing_expectations()
    patch_route_test_mutator()
    impl.main()
