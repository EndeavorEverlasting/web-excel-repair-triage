from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.evaluate_delivery_signoff_trigger import evaluate_trigger

ROOT = Path(__file__).parents[1]
CONFIG = json.loads((ROOT / "triggers/delivery-signoff-generation.json").read_text(encoding="utf-8"))
FIXTURES = Path(__file__).parent / "fixtures" / "delivery_signoff_trigger"


@pytest.mark.parametrize("fixture", sorted(FIXTURES.glob("*.json")), ids=lambda path: path.stem)
def test_typed_trigger_decisions(fixture: Path) -> None:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    result = evaluate_trigger(CONFIG, payload["request"])
    for key, value in payload["expected"].items():
        assert result[key] == value


def test_deny_precedence_wins_when_allow_also_matches() -> None:
    request = {
        "request_text": "Generate a delivery sign-off",
        "task_kind": "labor_reconstruction",
        "input_schema": "delivery-signoff-spec/v1",
    }
    result = evaluate_trigger(CONFIG, request)
    assert result["decision"] == "deny"
    assert result["rule_id"] == "labor-only-task"
