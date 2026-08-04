#!/usr/bin/env python3
"""Fail-closed Aptos font validator for Excel for Web artifacts and producers."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "configs" / "webexcel_fonts_v1.json"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"m": MAIN_NS}


class FontValidationError(RuntimeError):
    pass


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FontValidationError(f"missing font policy: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FontValidationError(f"invalid font policy JSON: {path}: {exc}") from exc
    if policy.get("schema") != "webexcel-font-policy/v1":
        raise FontValidationError("unsupported font policy schema")
    if policy.get("default_font") != "Aptos":
        raise FontValidationError("policy default_font must be Aptos")
    if "Carlito" not in policy.get("forbidden_fonts", []):
        raise FontValidationError("policy must explicitly forbid Carlito")
    return policy


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _font_names_from_styles(raw: bytes) -> list[str]:
    root = ET.fromstring(raw)
    fonts = root.find("m:fonts", NS)
    if fonts is None:
        return []
    names: list[str] = []
    for font in fonts.findall("m:font", NS):
        name = font.find("m:name", NS)
        value = name.get("val") if name is not None else None
        if value:
            names.append(value.strip())
        else:
            names.append("")
    return names


def _violation(rule_id: str, location: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "location": location, "message": message}


def inspect_workbook(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix not in {item.lower() for item in policy["supported_extensions"]}:
        raise FontValidationError(f"unsupported workbook extension: {path}")
    if not path.is_file():
        raise FontValidationError(f"workbook does not exist: {path}")

    allowed = {item.casefold() for item in policy["allowed_explicit_fonts"]}
    forbidden = {item.casefold(): item for item in policy["forbidden_fonts"]}
    violations: list[dict[str, str]] = []
    package_hits: set[tuple[str, str]] = set()

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            styles_path = "xl/styles.xml"
            if styles_path not in names:
                violations.append(
                    _violation("WEBFONT002", styles_path, "Workbook styles.xml is missing; Aptos default cannot be proved.")
                )
                explicit_fonts: list[str] = []
            else:
                explicit_fonts = _font_names_from_styles(archive.read(styles_path))

            for member in sorted(name for name in names if name.lower().endswith((".xml", ".rels"))):
                raw = archive.read(member)
                lowered = raw.lower()
                for folded, display in forbidden.items():
                    token = display.encode("utf-8").lower()
                    if token in lowered and (member, folded) not in package_hits:
                        package_hits.add((member, folded))
                        violations.append(
                            _violation("WEBFONT001", member, f"Forbidden explicit font {display} is present in the OOXML package.")
                        )
    except zipfile.BadZipFile as exc:
        raise FontValidationError(f"invalid OOXML ZIP package: {path}") from exc
    except ET.ParseError as exc:
        raise FontValidationError(f"invalid styles XML in {path}: {exc}") from exc

    default_font = explicit_fonts[0] if explicit_fonts else None
    expected_default = str(policy["default_font"])
    if default_font is None or default_font.casefold() != expected_default.casefold():
        violations.append(
            _violation(
                "WEBFONT002",
                "xl/styles.xml#fonts[0]",
                f"Workbook default explicit font must be {expected_default}; found {default_font or '<missing>'}.",
            )
        )

    for index, font_name in enumerate(explicit_fonts):
        if not font_name:
            violations.append(
                _violation("WEBFONT003", f"xl/styles.xml#fonts[{index}]", "Explicit font entry has no name.")
            )
            continue
        if font_name.casefold() not in allowed:
            violations.append(
                _violation(
                    "WEBFONT003",
                    f"xl/styles.xml#fonts[{index}]",
                    f"Explicit font {font_name} is outside the approved Aptos family.",
                )
            )

    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in violations:
        key = (item["rule_id"], item["location"], item["message"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return {
        "schema": "webexcel-font-artifact-result/v1",
        "path": str(path),
        "filename": path.name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "default_font": default_font,
        "explicit_fonts": explicit_fonts,
        "violation_count": len(unique),
        "violations": unique,
        "status": "PASS" if not unique else "FAIL",
    }


def _iter_source_files(policy: dict[str, Any]) -> Iterable[Path]:
    scan = policy["source_scan"]
    extensions = {item.lower() for item in scan["extensions"]}
    excluded = {Path(item).as_posix() for item in scan.get("excluded_paths", [])}
    for root_name in scan["roots"]:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(ROOT).as_posix()
            if relative in excluded or path.suffix.lower() not in extensions:
                continue
            yield path


def inspect_sources(policy: dict[str, Any]) -> dict[str, Any]:
    forbidden = [item for item in policy["forbidden_fonts"]]
    violations: list[dict[str, str]] = []
    scanned = 0
    for path in _iter_source_files(policy):
        scanned += 1
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT).as_posix()
        for line_number, line in enumerate(lines, start=1):
            folded = line.casefold()
            for font in forbidden:
                if font.casefold() in folded:
                    violations.append(
                        _violation(
                            "WEBFONT004",
                            f"{relative}:{line_number}",
                            f"Workbook producer/configuration source contains forbidden font token {font}.",
                        )
                    )
    return {
        "schema": "webexcel-font-source-result/v1",
        "scanned_file_count": scanned,
        "violation_count": len(violations),
        "violations": violations,
        "status": "PASS" if not violations else "FAIL",
    }


def build_report(
    *, policy: dict[str, Any], workbooks: list[Path], scan_source: bool
) -> dict[str, Any]:
    artifact_results = [inspect_workbook(path, policy) for path in workbooks]
    source_result = inspect_sources(policy) if scan_source else None
    violation_count = sum(item["violation_count"] for item in artifact_results)
    if source_result:
        violation_count += source_result["violation_count"]
    return {
        "schema": "webexcel-font-validation-result/v1",
        "policy_id": policy["policy_id"],
        "default_font": policy["default_font"],
        "artifact_count": len(artifact_results),
        "artifacts": artifact_results,
        "source_scan": source_result,
        "violation_count": violation_count,
        "status": "PASS" if violation_count == 0 else "FAIL",
        "proof_ceiling": policy["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Aptos font compatibility for Excel for Web artifacts and sources."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--workbook", action="append", type=Path, default=[])
    parser.add_argument("--scan-source", action="store_true")
    parser.add_argument("--require-workbook", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        policy = load_policy(args.policy)
        if args.require_workbook and not args.workbook:
            raise FontValidationError("at least one --workbook is required")
        if not args.workbook and not args.scan_source:
            raise FontValidationError("provide --workbook and/or --scan-source")
        report = build_report(
            policy=policy,
            workbooks=[path.resolve() for path in args.workbook],
            scan_source=args.scan_source,
        )
    except FontValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        print(
            f"{report['status']}: Aptos WebExcel font validation; "
            f"artifacts={report['artifact_count']} violations={report['violation_count']}"
        )
        if args.output:
            print(args.output)
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
