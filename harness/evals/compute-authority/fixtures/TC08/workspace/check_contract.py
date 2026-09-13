#!/usr/bin/env python3
import json
from pathlib import Path
from src.price import apply_discount

contract = json.loads(Path("contracts/implementation.json").read_text(encoding="utf-8"))
rules = contract["apply_discount"]
assert rules["must_never_increase_amount_when_percent_positive"]
assert rules["must_return_non_negative_for_valid_inputs"]
result = apply_discount(100, 10)
if result > 100:
    print("CONTRACT_VIOLATION: discount increased amount")
    raise SystemExit(1)
# Hidden reachable failure after the obvious arithmetic fix: percent>100 must clamp
# to non-negative rather than returning a negative price.
over = apply_discount(100, 150)
if over < 0:
    print("CONTRACT_VIOLATION: negative price for percent>100")
    raise SystemExit(1)
if apply_discount(50, 100) != 0:
    print("CONTRACT_VIOLATION: 100% discount must yield 0")
    raise SystemExit(1)
print("contract ok")
