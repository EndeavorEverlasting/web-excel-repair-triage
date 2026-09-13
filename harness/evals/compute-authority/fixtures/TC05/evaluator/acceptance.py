#!/usr/bin/env python3
"""Evaluator-only acceptance quality checker. Never copy into agent workspace."""
import ast
import sys
from pathlib import Path

workspace = Path.cwd()
if str(workspace) not in sys.path:
    sys.path.insert(0, str(workspace))

src = Path("src/names.py").read_text(encoding="utf-8")
tree = ast.parse(src)
funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
names = [f.name for f in funcs]
issues = []
if "tmp1" in names:
    issues.append("readability_tmp1")
if "do_strip" in names and "strip_again" in names:
    issues.append("duplicate_helpers")
test = Path("tests/test_names.py").read_text(encoding="utf-8")
if "test_empty" not in test:
    issues.append("missing_edge_test")
from src.names import normalize_name
assert normalize_name("  Ada   Lovelace ") == "ada lovelace"
assert normalize_name("   ") == ""
assert normalize_name("") == ""
print("acceptance issues:", issues if issues else "none")
raise SystemExit(1 if issues else 0)
