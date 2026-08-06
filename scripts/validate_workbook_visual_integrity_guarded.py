#!/usr/bin/env python3
"""Guarded entry point for workbook visual-integrity validation.

The core validator remains the OOXML implementation. This entry point enforces
runtime contracts that cannot be optional: protected output allocation,
style-only baseline presence, and bounded date/person striping semantics.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "Outputs"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import validate_workbook_visual_integrity as core

SUPPORTED_RULE_TYPES = {
    "profile_palette",
    "defense_tab_sections",
    "chrome_contract",
    "forbid_unbounded_striping",
    "range_fill",
    "same_key_style",
    "semantic_rows",
    "boundary",
    "paired_range_fill",
    "layout",
    "style_only_baseline",
}


class GuardError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GuardError(f"missing JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GuardError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GuardError(f"JSON root must be an object: {path}")
    return value


def _relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def guard_output(output: Path | None, inputs: list[Path]) -> Path | None:
    if output is None:
        return None
    target = output.resolve()
    for input_path in inputs:
        if target == input_path.resolve():
            raise GuardError("validation report must not overwrite an input workbook, profile, or baseline")
    repo = ROOT.resolve()
    approved = OUTPUT_ROOT.resolve()
    if _relative_to(target, repo) and not _relative_to(target, approved):
        raise GuardError("validation reports written inside the repository must be under Outputs/")
    return target


def guard_profile(profile: dict[str, Any], *, baseline_supplied: bool) -> None:
    rules = profile.get("rules", [])
    if not isinstance(rules, list):
        raise GuardError("profile rules must be an array")
    unknown = sorted(
        {str(rule.get("type")) for rule in rules if rule.get("type") not in SUPPORTED_RULE_TYPES}
    )
    if unknown:
        raise GuardError(f"unsupported visual rule types: {unknown}")

    style_only = [rule for rule in rules if rule.get("type") == "style_only_baseline"]
    if style_only and not baseline_supplied:
        raise GuardError("a profile with style_only_baseline requires --baseline at runtime")

    stripe_guards = [rule for rule in rules if rule.get("type") == "forbid_unbounded_striping"]
    if not stripe_guards:
        return
    forbidden = {
        str(item).casefold()
        for guard in stripe_guards
        for item in guard.get("forbidden", [])
    }
    exceptions = profile.get("exceptions", [])
    for rule in rules:
        if rule.get("type") != "same_key_style":
            continue
        semantic = str(rule.get("key_semantic", "")).casefold()
        if not semantic:
            raise GuardError(
                f"same_key_style rule {rule.get('id')} must declare key_semantic when striping guards exist"
            )
        if semantic not in forbidden:
            continue
        rows = rule.get("rows")
        sheet = rule.get("sheet")
        bounded = any(
            item.get("type") == "legacy_date_band"
            and item.get("bounded_sheet") == sheet
            and item.get("bounded_rows") == rows
            for item in exceptions
        )
        if not bounded:
            raise GuardError(
                f"unbounded {semantic} striping is forbidden for rule {rule.get('id')}"
            )


def _guard_registered_profiles() -> None:
    registry = _load(ROOT / "harness" / "workbook-visual-integrity" / "registry.json")
    for relative in registry.get("profiles", []):
        profile = _load(ROOT / str(relative))
        # Static profile audit proves rule shape. Runtime baseline presence is
        # enforced only when validating a concrete workbook.
        guard_profile_static(profile)


def guard_profile_static(profile: dict[str, Any]) -> None:
    rules = profile.get("rules", [])
    if not isinstance(rules, list):
        raise GuardError("profile rules must be an array")
    unknown = sorted(
        {str(rule.get("type")) for rule in rules if rule.get("type") not in SUPPORTED_RULE_TYPES}
    )
    if unknown:
        raise GuardError(f"unsupported visual rule types: {unknown}")
    stripe_guards = [rule for rule in rules if rule.get("type") == "forbid_unbounded_striping"]
    if not stripe_guards:
        return
    forbidden = {
        str(item).casefold()
        for guard in stripe_guards
        for item in guard.get("forbidden", [])
    }
    exceptions = profile.get("exceptions", [])
    for rule in rules:
        if rule.get("type") != "same_key_style":
            continue
        semantic = str(rule.get("key_semantic", "")).casefold()
        if not semantic:
            raise GuardError(
                f"same_key_style rule {rule.get('id')} must declare key_semantic when striping guards exist"
            )
        if semantic in forbidden:
            bounded = any(
                item.get("type") == "legacy_date_band"
                and item.get("bounded_sheet") == rule.get("sheet")
                and item.get("bounded_rows") == rule.get("rows")
                for item in exceptions
            )
            if not bounded:
                raise GuardError(
                    f"unbounded {semantic} striping is forbidden for rule {rule.get('id')}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run guarded workbook visual-integrity validation.")
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--validate-profiles", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        guard_output(
            args.output,
            [path for path in (args.workbook, args.profile, args.baseline) if path is not None],
        )
        if args.validate_profiles:
            if args.workbook or args.profile or args.baseline:
                raise GuardError("--validate-profiles cannot be combined with workbook arguments")
            _guard_registered_profiles()
        else:
            if args.workbook is None or args.profile is None:
                raise GuardError("--workbook and --profile are required")
            guard_profile(_load(args.profile), baseline_supplied=args.baseline is not None)
    except GuardError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    delegated: list[str] = []
    if args.workbook:
        delegated += ["--workbook", str(args.workbook)]
    if args.profile:
        delegated += ["--profile", str(args.profile)]
    if args.baseline:
        delegated += ["--baseline", str(args.baseline)]
    if args.validate_profiles:
        delegated.append("--validate-profiles")
    if args.output:
        delegated += ["--output", str(args.output)]
    if args.summary:
        delegated.append("--summary")
    return core.main(delegated)


if __name__ == "__main__":
    raise SystemExit(main())
