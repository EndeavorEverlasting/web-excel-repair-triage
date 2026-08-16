#!/usr/bin/env python3
"""Validate progressive-disclosure context architecture and hard bloat ceilings."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "harness" / "contracts" / "context-architecture.v1.json"


class ContextArchitectureError(RuntimeError):
    pass


def load_contract() -> dict:
    try:
        payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContextArchitectureError("missing context architecture contract") from exc
    except json.JSONDecodeError as exc:
        raise ContextArchitectureError(f"invalid context architecture JSON: {exc}") from exc
    if payload.get("schema_version") != "triage.harness.context-architecture/v1":
        raise ContextArchitectureError("unsupported context architecture schema")
    return payload


def read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise ContextArchitectureError(f"missing routed context file: {relative_path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ContextArchitectureError(f"empty routed context file: {relative_path}")
    return text


def approx_tokens(chars: int, divisor: int) -> int:
    return math.ceil(chars / divisor)


def validate(payload: dict) -> dict:
    divisor = int(payload["token_estimate"]["chars_per_token"])
    metrics: dict[str, dict[str, int | float]] = {}

    if payload.get("default_entrypoints") != ["AGENTS.md", "harness/CONTEXT.md"]:
        raise ContextArchitectureError("default context entrypoints drifted")

    budgets = payload.get("hard_char_budgets", {})
    for relative_path, max_chars in budgets.items():
        text = read(relative_path)
        chars = len(text)
        if chars > int(max_chars):
            raise ContextArchitectureError(
                f"{relative_path} exceeds hard context budget: {chars}>{max_chars} chars"
            )
        baseline = int(payload.get("baseline_chars", {}).get(relative_path, chars))
        reduction = round((1 - chars / baseline) * 100, 1) if baseline else 0.0
        metrics[relative_path] = {
            "chars": chars,
            "approx_tokens": approx_tokens(chars, divisor),
            "hard_max_chars": int(max_chars),
            "baseline_chars": baseline,
            "reduction_percent": reduction,
        }

    agents = read("AGENTS.md")
    router = read("harness/CONTEXT.md")
    codebase = read("CODEBASE_MAP.md")
    skills = read("SKILLS.md")

    for phrase in payload["required_router_phrases"]:
        if phrase not in router:
            raise ContextArchitectureError(f"context router missing phrase: {phrase}")

    for forbidden in payload["forbidden_default_bundle_fragments"]:
        for path, text in (
            ("harness/CONTEXT.md", router),
            ("CODEBASE_MAP.md", codebase),
            ("SKILLS.md", skills),
        ):
            if forbidden.casefold() in text.casefold():
                raise ContextArchitectureError(
                    f"{path} reintroduced eager context bundle: {forbidden}"
                )

    for spec in payload["binding_specs"].values():
        read(spec)
        if spec not in agents:
            raise ContextArchitectureError(
                f"AGENTS.md does not incorporate binding spec: {spec}"
            )

    required_agents = (
        "single repository governance authority",
        "Progressive disclosure",
        "Do **not** preload",
        "one exact next command",
    )
    for phrase in required_agents:
        if phrase not in agents:
            raise ContextArchitectureError(f"AGENTS.md missing universal rule: {phrase}")

    if "harness/CONTEXT.md" not in codebase or "harness/CONTEXT.md" not in skills:
        raise ContextArchitectureError("root indexes do not route through harness/CONTEXT.md")
    if "selection index" not in skills:
        raise ContextArchitectureError("SKILLS.md is no longer selection-only")

    default_chars = len(agents) + len(router)
    report = {
        "schema_version": "triage.context-architecture-report/v1",
        "status": "PASS",
        "default_entrypoints": payload["default_entrypoints"],
        "default_chars": default_chars,
        "default_approx_tokens": approx_tokens(default_chars, divisor),
        "soft_50000_token_target": payload["layers"]["50000"]["soft_max_approx_tokens"],
        "metrics": metrics,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        report = validate(load_contract())
    except ContextArchitectureError as exc:
        print(f"Context architecture validation: FAIL: {exc}", file=sys.stderr)
        return 1
    if args.output:
        target = Path(args.output)
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        print(
            "Context architecture: PASS "
            f"default≈{report['default_approx_tokens']} tokens; "
            + ", ".join(
                f"{path}={item['chars']} chars"
                for path, item in report["metrics"].items()
            )
        )
    elif not args.output:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
