#!/usr/bin/env python3
import json
from pathlib import Path
from src.calc import add, scale

out = Path("generated/result.json")
payload = {
    "sum_example": add(2, 3),
    "scale_example": scale(3),
    "formula": "a+b",
}
out.write_text(json.dumps(payload) + "\n", encoding="utf-8")
print("wrote", out)
