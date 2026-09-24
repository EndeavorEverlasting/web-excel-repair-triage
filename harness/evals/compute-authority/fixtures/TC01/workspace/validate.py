#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print("+", " ".join(cmd))
    return subprocess.call(cmd)

rc = 0
rc |= run([sys.executable, "-m", "unittest", "tests.test_add", "-v"])
rc |= run([sys.executable, "-m", "unittest", "tests.test_edge", "-v"])
generated = json.loads(Path("generated/result.json").read_text(encoding="utf-8"))
from src.calc import add, scale
expected = {
    "sum_example": add(2, 3),
    "scale_example": scale(3),
    "formula": "a+b",
}
if generated != expected:
    print("GENERATED_DRIFT:", generated, "!=", expected)
    rc |= 1
else:
    print("generated parity ok")
raise SystemExit(rc)
