#!/usr/bin/env python3
"""Canonical repository-native update generator entrypoint."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import repo_native_update_lib as lib


def _resolve_receipt_path(raw: str | None) -> Path:
    target = Path(raw) if raw else lib.DEFAULT_RECEIPT_PATH
    if not target.is_absolute():
        target = ROOT / target
    resolved = target.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise lib.RepoNativeUpdateError(
            "receipt path must stay within the repository root"
        ) from exc
    return resolved


def validate_input_for_surface(surface: dict[str, Any]) -> dict[str, Any]:
    input_path = ROOT / str(surface["input_path"])
    if not input_path.is_file():
        raise lib.RepoNativeUpdateError(
            f"missing input for surface {surface['id']}: {surface['input_path']}"
        )
    payload = lib.load_json(input_path)
    if surface["id"] == "canary-constants":
        return lib.validate_canary_constants_input(payload)
    raise lib.RepoNativeUpdateError(
        f"no input validator registered for surface: {surface['id']}"
    )


def generate_surface_text(surface: dict[str, Any], payload: dict[str, Any]) -> str:
    if surface["id"] == "canary-constants":
        return lib.build_canary_constants_module(
            payload,
            surface_id=str(surface["id"]),
            input_relative=str(surface["input_path"]),
        )
    raise lib.RepoNativeUpdateError(
        f"no generator registered for surface: {surface['id']}"
    )


def generate_surface(
    surface: dict[str, Any],
    *,
    check_only: bool,
    receipt_path: Path,
) -> int:
    contract = lib.load_contract()
    lib.validate_surface_shape(surface)
    payload = validate_input_for_surface(surface)
    content = lib.normalize_newlines(generate_surface_text(surface, payload))
    input_path = ROOT / str(surface["input_path"])

    output_relatives = [
        lib.assert_safe_relative_path(item) for item in surface["owned_outputs"]
    ]
    output_paths: list[str] = []
    output_sha256: dict[str, str] = {}
    statuses: list[str] = []

    for relative in output_relatives:
        destination = lib.resolve_owned_output(relative, surface, contract=contract)
        output_paths.append(relative)
        existing = destination.read_text(encoding="utf-8") if destination.is_file() else None
        existing_normalized = (
            lib.normalize_newlines(existing) if existing is not None else None
        )

        if check_only:
            if existing_normalized == content:
                statuses.append("check_pass")
                output_sha256[relative] = lib.sha256_text(content)
            else:
                statuses.append("check_fail")
                output_sha256[relative] = lib.sha256_text(
                    existing_normalized or ""
                )
            continue

        if existing_normalized == content:
            statuses.append("unchanged")
            output_sha256[relative] = lib.sha256_text(content)
            continue

        lib.atomic_write_text(destination, content)
        statuses.append("generated")
        output_sha256[relative] = lib.sha256_text(content)

    if "check_fail" in statuses:
        status = "check_fail"
    elif check_only:
        status = "check_pass"
    elif "generated" in statuses:
        status = "generated"
    else:
        status = "unchanged"

    receipt = lib.build_receipt(
        contract=contract,
        surface=surface,
        input_path=input_path,
        output_paths=output_paths,
        output_sha256=output_sha256,
        status=status,
    )
    lib.write_receipt(receipt, receipt_path)

    if check_only:
        return 2 if status == "check_fail" else 0
    return 0


def cmd_validate_input(surface_id: str) -> int:
    contract = lib.load_contract()
    surface = lib.resolve_surface(contract, surface_id)
    lib.validate_surface_shape(surface)
    validate_input_for_surface(surface)
    return 0


def cmd_generate(
    surface_id: str,
    *,
    check_only: bool,
    receipt_raw: str | None,
) -> int:
    contract = lib.load_contract()
    surface = lib.resolve_surface(contract, surface_id)
    receipt_path = _resolve_receipt_path(receipt_raw)
    return generate_surface(surface, check_only=check_only, receipt_path=receipt_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate owned outputs for a surface")
    generate.add_argument("--surface", required=True)
    generate.add_argument(
        "--check",
        action="store_true",
        help="Compare generated content without writing owned outputs",
    )
    generate.add_argument("--receipt", help="Receipt output path")

    validate = subparsers.add_parser(
        "validate-input", help="Validate canonical input for a surface"
    )
    validate.add_argument("--surface", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            return cmd_generate(
                args.surface,
                check_only=args.check,
                receipt_raw=args.receipt,
            )
        if args.command == "validate-input":
            return cmd_validate_input(args.surface)
        raise lib.RepoNativeUpdateError(f"unsupported command: {args.command}")
    except lib.RepoNativeUpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
