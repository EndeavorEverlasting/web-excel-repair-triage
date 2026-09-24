#!/bin/bash
set -e

pip install -r requirements.txt -q --disable-pip-version-check

if [ -n "$GITHUB_TOKEN" ]; then
  git -c credential.helper='!bash scripts/github-credential-helper.sh' \
      push origin main 2>&1 || echo "[post-merge] GitHub push failed (non-fatal)"
else
  echo "[post-merge] GITHUB_TOKEN not set — skipping GitHub push"
fi
