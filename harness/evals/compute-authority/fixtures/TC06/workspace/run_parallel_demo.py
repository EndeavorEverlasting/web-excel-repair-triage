#!/usr/bin/env python3
"""Optional helper showing real concurrent lane dispatch for this fixture."""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

LANES = [
    [sys.executable, "-m", "unittest", "tests.test_core", "-v"],
    [sys.executable, "check_docs.py"],
    [sys.executable, "check_generated.py"],
]

def run(cmd):
    return cmd, subprocess.call(cmd)

with ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run, LANES))
for cmd, rc in results:
    print(cmd, "->", rc)
raise SystemExit(0 if all(rc == 0 for _, rc in results) else 1)
