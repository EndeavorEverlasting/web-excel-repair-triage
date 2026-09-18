#!/usr/bin/env python3
"""Cursor hook/receipt adapter for the local failure-observatory prototype."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.failure_observatory import (
    ObservatoryError,
    adapt_cursor_hook,
    apply_signal,
    compile_capsule,
    load_state,
    receipt_signal,
    save_state,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "harness/contracts/execution-boundary-enforcement.v1.json"
TAXONOMY = ROOT / "harness/contracts/execution-boundary-taxonomy.v1.json"


def _load_contract(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local zero-content Cursor failure observatory prototype.")
    parser.add_argument("--state", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    hook = sub.add_parser("hook")
    hook.add_argument("hook_name")
    receipt = sub.add_parser("receipt")
    receipt.add_argument("--prompt-id", required=True)
    receipt.add_argument("--release", required=True)
    receipt.add_argument("--proof-state", required=True)
    sub.add_parser("capsule")
    sub.add_parser("reset")
    args = parser.parse_args()

    if args.command == "reset":
        if args.state.exists():
            args.state.unlink()
        return 0

    architecture = _load_contract(ARCHITECTURE)
    taxonomy = _load_contract(TAXONOMY)
    state = load_state(args.state)
    try:
        if args.command == "hook":
            raw = json.load(sys.stdin)
            state = apply_signal(
                state,
                adapt_cursor_hook(args.hook_name, raw),
                architecture,
                taxonomy,
            )
            save_state(args.state, state)
            return 0
        if args.command == "receipt":
            state = apply_signal(
                state,
                receipt_signal(args.prompt_id, args.release, args.proof_state),
                architecture,
                taxonomy,
            )
            save_state(args.state, state)
            return 0
        sys.stdout.write(json.dumps(compile_capsule(state), sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    except (ObservatoryError, json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"FAILURE OBSERVATORY: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
