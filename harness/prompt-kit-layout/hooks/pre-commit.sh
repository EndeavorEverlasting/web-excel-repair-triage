#!/usr/bin/env sh
set -eu
python3 scripts/validate_prompt_kit_layout_harness.py --summary
python3 -m unittest tests.test_prompt_kit_layout_harness
