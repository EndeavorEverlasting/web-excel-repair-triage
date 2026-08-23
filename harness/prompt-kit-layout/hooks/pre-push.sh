#!/usr/bin/env sh
set -eu
python scripts/validate_prompt_kit_layout_harness.py --summary
python -m unittest tests.test_prompt_kit_layout_harness -v
git diff --check
