#!/usr/bin/env python3
"""Adapt one GitHub repository_dispatch event into the provider-neutral AFK router."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import prompt_kit_afk_signal_router as router  # noqa: E402

DISPATCH_ACTION = "operant-friction-receipt"


class AdapterError(ValueError):
    """Raised when the provider event is not the contracted friction dispatch."""


def extract_receipt(event: object) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise AdapterError("repository dispatch event must be a JSON object")
    if event.get("action") != DISPATCH_ACTION:
        raise AdapterError(f"unsupported repository dispatch action: {event.get('action')!r}")
    payload = event.get("client_payload")
    if not isinstance(payload, dict):
        raise AdapterError("repository dispatch client_payload must be a JSON object")
    if payload.get("event_type") != "operant_friction":
        raise AdapterError("repository dispatch client_payload must be an operant_friction receipt")
    return dict(payload)


def route_repository_dispatch(
    event: object,
    *,
    state_path: Path,
    requests_dir: Path,
    worker_argv: list[str] | None = None,
) -> dict[str, Any]:
    receipt = extract_receipt(event)
    return router.route_signal(
        receipt,
        state_path=state_path,
        requests_dir=requests_dir,
        worker_argv=worker_argv,
    )


def read_event(path: str) -> object:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--event",
        default=os.environ.get("GITHUB_EVENT_PATH"),
        help="GitHub repository_dispatch event JSON path; defaults to GITHUB_EVENT_PATH",
    )
    parser.add_argument("--state", type=Path, default=Path("Outputs/prompt-kit-afk/state.json"))
    parser.add_argument("--requests-dir", type=Path, default=Path("Outputs/prompt-kit-afk/work-requests"))
    parser.add_argument(
        "--worker-argv-json",
        default=os.environ.get("PROMPT_KIT_AFK_WORKER_ARGV_JSON"),
        help="Optional provider-neutral worker argv JSON containing {request} exactly once",
    )
    args = parser.parse_args(argv)
    if not args.event:
        print("Operant friction repository-dispatch adapter failed: --event or GITHUB_EVENT_PATH is required", file=sys.stderr)
        return 2
    try:
        result = route_repository_dispatch(
            read_event(args.event),
            state_path=args.state,
            requests_dir=args.requests_dir,
            worker_argv=router.parse_worker_argv(args.worker_argv_json),
        )
    except (OSError, json.JSONDecodeError, AdapterError, router.RoutingError) as exc:
        print(f"Operant friction repository-dispatch adapter failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 3 if result.get("status") == "BLOCKED_WORKER_FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
