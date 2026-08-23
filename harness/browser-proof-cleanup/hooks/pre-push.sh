#!/usr/bin/env sh
set -eu
python scripts/validate_prompt_kit_browser_proof_cleanup.py --summary
python -m unittest tests.test_prompt_kit_browser_proof_cleanup_harness -v
