#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PROMPT_KIT_E2E_PORT:-8765}"
TMP="$(mktemp -d)"
cleanup(){ if [[ -n "${SERVER_PID:-}" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi; rm -rf "$TMP"; }
trap cleanup EXIT
cd "$ROOT"
python -m http.server "$PORT" --bind 127.0.0.1 --directory web >"$TMP/server.log" 2>&1 &
SERVER_PID=$!
for _ in $(seq 1 30); do curl -fsS "http://127.0.0.1:${PORT}/prompt-kit/index.html" >/dev/null && break; sleep 1; done
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
if [[ -z "$CHROME" ]]; then echo 'APPLICATION_E2E_BLOCKED: no Chromium/Chrome executable' >&2; exit 20; fi
"$CHROME" --headless --no-sandbox --disable-gpu --virtual-time-budget=2000 --dump-dom "http://127.0.0.1:${PORT}/prompt-kit/index.html" >"$TMP/dom.html" 2>"$TMP/chrome.log"
grep -F 'data-prompt-kit-feedback-runtime="v1"' "$TMP/dom.html" >/dev/null
grep -F 'AI Prompt Kit' "$TMP/dom.html" >/dev/null
printf '{"schema_version":"prompt-kit-browser-e2e-receipt/v1","status":"PASS","surface":"browser","url":"http://127.0.0.1:%s/prompt-kit/index.html"}\n' "$PORT"
