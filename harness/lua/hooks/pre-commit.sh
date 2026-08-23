#!/bin/sh
set -eu

# Focused Lua harness gate fragment. The repository root pre-commit hook remains
# the canonical installed hook; this fragment documents and exercises the Lua
# checks without taking ownership of another harness writer's shared hook.
python scripts/validate_lua_harness.py --summary
python -m unittest tests.test_lua_harness_contract -v
git diff --cached --check
