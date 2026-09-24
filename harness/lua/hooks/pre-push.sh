#!/bin/sh
set -eu

LUA_REPORT="${TMPDIR:-/tmp}/web-excel-lua-embedding-readiness.json"
python3 scripts/validate_lua_harness.py --output "$LUA_REPORT" --summary
python3 -m unittest tests.test_lua_harness_contract -v
python3 scripts/validate_harness.py --report "${TMPDIR:-/tmp}/web-excel-harness-completeness-lua.json"
python3 -m unittest tests.test_harness_contract -v
python3 -m triage.gitignore_hygiene
git diff --check
