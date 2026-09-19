#!/usr/bin/env sh
set -eu
python3 scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python3 -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
