from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    overrides_path = Path("registry/prompts/prompt-overrides.v1.json")
    payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
    content = p13["copyContent"]

    old_class = "- MISSING_PARALLELISM — an independent lane should have been delegated or prepared for a Sub-Part Agent."
    new_class = "- MISSING_PARALLELISM — an independent lane should have been dispatched through P07 when usable worker capacity and collision-safe independence were available."
    if old_class not in content:
        raise SystemExit("P13 missing-parallelism class marker moved")
    content = content.replace(old_class, new_class, 1)

    old_regression = "- explicit Sub-Part Agent plan or serialized-dependency reason;"
    new_regression = "- actual P07 dispatch evidence when worker capacity and collision-safe lanes exist, or the exact unavailable-capability limitation when they do not;"
    if old_regression not in content:
        raise SystemExit("P13 regression parallel marker moved")
    content = content.replace(old_regression, new_regression, 1)

    p13["copyContent"] = content
    overrides_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    test_path = Path("tests/test_skill_prompt_registry.py")
    tests = test_path.read_text(encoding="utf-8")
    anchor = '            "no stopping at plan/status while safe action remains",\n'
    addition = '            "actual P07 dispatch evidence when worker capacity and collision-safe lanes exist",\n'
    if addition not in tests:
        if anchor not in tests:
            raise SystemExit("P13 focused expected-phrase anchor moved")
        tests = tests.replace(anchor, anchor + addition, 1)

    routing_anchor = "        for routing_phrase in (\n"
    guard = (
        '        self.assertNotIn("explicit Sub-Part Agent plan or serialized-dependency reason", content)\n'
        '        self.assertNotIn("prepared for a Sub-Part Agent", content)\n\n'
    )
    if guard not in tests:
        if routing_anchor not in tests:
            raise SystemExit("P13 routing assertion anchor moved")
        tests = tests.replace(routing_anchor, guard + routing_anchor, 1)
    test_path.write_text(tests, encoding="utf-8")

    for stale in (
        "explicit Sub-Part Agent plan or serialized-dependency reason",
        "prepared for a Sub-Part Agent",
    ):
        if stale in content:
            raise SystemExit(f"stale plan-only phrase remains: {stale}")


if __name__ == "__main__":
    main()
