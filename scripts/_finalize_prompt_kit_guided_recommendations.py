#!/usr/bin/env python3
"""One-time canonical Prompt Kit generation for the guided-recommendations branch.

The branch-only workflow runs this file after all durable sources are committed.
This file and its workflow remove themselves before the generated artifact commit.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Trigger the already-registered branch workflow after its workflow-file commit.
subprocess.run(
    [
        "python",
        "scripts/build_prompt_kit_registry.py",
        "--output",
        "web/prompt-kit/index.html",
    ],
    cwd=ROOT,
    check=True,
)

(ROOT / ".github" / "workflows" / "prompt-kit-branch-regenerate.yml").unlink()
Path(__file__).unlink()
