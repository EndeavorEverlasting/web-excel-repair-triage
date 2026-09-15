#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
GREEN_TEST = ROOT / "tests" / "test_green_branch_integration_policy.py"

OLD = "- Do not merge when a required gate is pending or failing, the head moved after validation, an unresolved dependency/review/conflict/protection rule remains, authorization is absent, or the merge would carry unrelated, unreviewed, unsafe, private, secret, or forbidden-scope work."
NEW = "- Do not merge when a required gate is pending or failing, the branch head moved after validation and proof-relevant inputs changed or proof relevance cannot be established, an unresolved dependency/review/conflict/protection rule remains, authorization is absent, or the merge would carry unrelated, unreviewed, unsafe, private, secret, or forbidden-scope work."


def main() -> int:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    appendix = policy["copy_content_appendix"]
    if NEW not in appendix:
        if OLD not in appendix:
            raise SystemExit("appendix head-movement clause drifted")
        appendix = appendix.replace(OLD, NEW, 1)
    policy["copy_content_appendix"] = appendix
    POLICY.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    text = GREEN_TEST.read_text(encoding="utf-8")
    marker = '        self.assertNotIn("the branch head moved after the evidence used to declare it green\\n", exceptions + "\\n")\n'
    addition = (
        '        self.assertNotIn("the head moved after validation,", appendix)\n'
        '        self.assertIn("the branch head moved after validation and proof-relevant inputs changed or proof relevance cannot be established", appendix)\n'
    )
    if addition.strip() not in text:
        if marker not in text:
            raise SystemExit("green integration regression anchor missing")
        text = text.replace(marker, marker + addition, 1)
    GREEN_TEST.write_text(text, encoding="utf-8")
    print("appendix proof-relevance merge gate scoped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
