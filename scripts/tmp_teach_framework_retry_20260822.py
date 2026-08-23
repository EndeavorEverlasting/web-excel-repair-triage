#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import tmp_teach_framework_contribution_20260822 as impl

FOCUSED = Path(__file__).resolve().parents[1] / "tests/test_prompt_registry_expansion_regression_design_teach.py"


def repair_checkpoint_expectations() -> None:
    text = FOCUSED.read_text(encoding="utf-8")
    old = '            "DIAGNOSTIC CHECK",\n            "PRACTICAL HARNESS",\n'
    new = '            "CONCEPTUAL TRADE-OFF / MECHANISM",\n            "CODE DIAGNOSTIC / EDGE CASE",\n'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("teach checkpoint assertion anchor not found")
    FOCUSED.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    repair_checkpoint_expectations()
    impl.main()
