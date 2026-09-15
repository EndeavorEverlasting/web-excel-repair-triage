#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
TEST = ROOT / "tests" / "test_actionable_prompt_registry.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"{label} anchor missing")
    return text.replace(old, new, 1)


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    suffix = policy["next_step_suffix"]
    suffix = replace_once(
        suffix,
        "PR, status, branch, or log inspection alone is invalid when safe executable work remains.",
        "PR, status, branch, or log inspection alone is invalid when safe, executable, progress-bearing work remains.",
        "suffix continuation",
    )
    suffix = replace_once(
        suffix,
        "Any SAFE & EXECUTABLE item disproves `none; no safe actionable work remains` and must be advanced.",
        "Any SAFE & EXECUTABLE item that is progress-bearing disproves `none; no safe actionable work remains` and must be advanced; merely runnable bookkeeping does not.",
        "suffix SAFE classification",
    )
    policy["next_step_suffix"] = suffix

    appendix = policy["copy_content_appendix"]
    appendix = replace_once(
        appendix,
        "- When safe executable work remains, do not stop at opening or reopening a PR, displaying already-reported status, listing branches or commits, showing logs, repeating a path, asking the operator to continue, or telling the operator to wait.",
        "- When safe, executable, progress-bearing work remains, do not stop at opening or reopening a PR, displaying already-reported status, listing branches or commits, showing logs, repeating a path, asking the operator to continue, or telling the operator to wait.",
        "appendix continuation",
    )
    appendix = replace_once(
        appendix,
        "- Use `none; no safe actionable work remains` only after all authorized work is complete, validation has actually run, commit and push or PR state are reported, cleanup or preserved-work state is reported, and no safe unproven action remains.",
        "- Use `none; no safe actionable work remains` only after all authorized work is complete, validation has actually run, commit and push or PR state are reported, cleanup or preserved-work state is reported, and no safe, executable, progress-bearing unproven action remains.",
        "appendix terminal condition",
    )
    policy["copy_content_appendix"] = appendix
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    test = TEST.read_text(encoding="utf-8")
    anchor = '        suffix = self.policy["next_step_suffix"]\n'
    if 'self.assertNotIn("when safe executable work remains", suffix)' not in test:
        insertion = (
            '        self.assertNotIn("when safe executable work remains", suffix)\n'
            '        self.assertNotIn("Any SAFE & EXECUTABLE item disproves", suffix)\n'
            '        self.assertIn("safe, executable, progress-bearing work remains", suffix)\n'
            '        self.assertIn("SAFE & EXECUTABLE item that is progress-bearing", suffix)\n\n'
        )
        if anchor not in test:
            raise SystemExit("test suffix anchor missing")
        test = test.replace(anchor, anchor + insertion, 1)
    TEST.write_text(test, encoding="utf-8")
    print("quiescence contradiction tightened")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
