#!/usr/bin/env python3
"""Fail-closed Aptos font validator for Excel for Web artifacts and producers."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "configs" / "webexcel_fonts_v1.json"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"m": MAIN_NS}
OUTPUT_ROOT = ROOT / "Outputs"


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


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _font_name(font: ET.Element) -> str:
    name = font.find("m:name", NS)
    value = name.get("val") if name is not None else None
    return value.strip() if value else ""


def _styles_inventory(raw: bytes) -> tuple[list[str], str | None, str]:
    root = ET.fromstring(raw)
    fonts_node = root.find("m:fonts", NS)
    fonts = [_font_name(font) for font in fonts_node.findall("m:font", NS)] if fonts_node is not None else []

    font_id: int | None = None
    location = "xl/styles.xml#default-style"

    normal = root.find("m:cellStyles/m:cellStyle[@name='Normal']", NS)
    style_xfs = root.find("m:cellStyleXfs", NS)
    if normal is not None and style_xfs is not None:
        try:
            xf_id = int(normal.get("xfId", "0"))
            xfs = style_xfs.findall("m:xf", NS)
            if 0 <= xf_id < len(xfs):
                font_id = int(xfs[xf_id].get("fontId", "0"))
                location = f"xl/styles.xml#cellStyles/Normal->cellStyleXfs[{xf_id}]/@fontId"
        except ValueError:
            font_id = None

    if font_id is None:
        cell_xfs = root.find("m:cellXfs", NS)
        first = cell_xfs.find("m:xf", NS) if cell_xfs is not None else None
        if first is not None:
            try:
                font_id = int(first.get("fontId", "0"))
                location = "xl/styles.xml#cellXfs[0]/@fontId"
            except ValueError:
                font_id = None

    if font_id is None and style_xfs is not None:
        first = style_xfs.find("m:xf", NS)
        if first is not None:
            try:
                font_id = int(first.get("fontId", "0"))
                location = "xl/styles.xml#cellStyleXfs[0]/@fontId"
            except ValueError:
                font_id = None

    default_font = fonts[font_id] if font_id is not None and 0 <= font_id < len(fonts) else None
    if font_id is not None:
        location = f"{location}={font_id}"
    return fonts, default_font, location


def _iter_font_declarations(member: str, raw: bytes) -> Iterator[tuple[str, str]]:
    """Yield explicit font declarations without treating ordinary cell text as fonts."""
    root = ET.fromstring(raw)
    counters: dict[str, int] = {}

    def walk(element: ET.Element, parent_local: str | None = None) -> Iterator[tuple[str, str]]:
        local = _local_name(element.tag)
        counters[local] = counters.get(local, 0) + 1
        index = counters[local]
        value: str | None = None

        if local == "name" and parent_local == "font":
            value = element.get("val")
        elif local == "rFont":
            value = element.get("val")
        elif local == "latin":
            value = element.get("typeface")
        elif local in {"defRPr", "rPr", "endParaRPr"}:
            value = element.get("typeface")

        if value:
            value = value.strip()
            # +mj-lt / +mn-lt are theme references, not explicit typefaces.
            if value and not value.startswith("+"):
                yield f"{member}#{local}[{index}]", value

        for child in list(element):
            yield from walk(child, local)

    yield from walk(root)


def _violation(rule_id: str, location: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "location": location, "message": message}


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_output_path(output: Path, workbooks: Iterable[Path] = ()) -> Path:
    target = output.resolve()
    repo = ROOT.resolve()
    output_root = OUTPUT_ROOT.resolve()

    for workbook in workbooks:
        if target == workbook.resolve():
            raise FontValidationError("report output must not overwrite a workbook input")

    if _is_relative_to(target, repo) and not _is_relative_to(target, output_root):
        relative = target.relative_to(repo).as_posix()
        raise FontValidationError(
            f"report output inside the repository must be under Outputs/: {relative}"
        )
    return target


def inspect_workbook(path: Path, policy: dict[str, Any]) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix not in {item.lower() for item in policy["supported_extensions"]}:
        raise FontValidationError(f"unsupported workbook extension: {path}")
    if not path.is_file():
        raise FontValidationError(f"workbook does not exist: {path}")

    allowed = {item.casefold() for item in policy["allowed_explicit_fonts"]}
    forbidden = {item.casefold(): item for item in policy["forbidden_fonts"]}
    violations: list[dict[str, str]] = []
    declarations: list[tuple[str, str]] = []

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            styles_path = "xl/styles.xml"
            if styles_path not in names:
                violations.append(
                    _violation(
                        "WEBFONT002",
                        styles_path,
                        "Workbook styles.xml is missing; Aptos default cannot be proved.",
                    )
                )
                style_fonts: list[str] = []
                default_font = None
                default_location = styles_path
            else:
                style_fonts, default_font, default_location = _styles_inventory(
                    archive.read(styles_path)
                )

            for member in sorted(name for name in names if name.lower().endswith(".xml")):
                raw = archive.read(member)
                try:
                    declarations.extend(_iter_font_declarations(member, raw))
                except ET.ParseError as exc:
                    raise FontValidationError(
                        f"invalid OOXML XML part {member} in {path}: {exc}"
                    ) from exc
    except zipfile.BadZipFile as exc:
        raise FontValidationError(f"invalid OOXML ZIP package: {path}") from exc
    except ET.ParseError as exc:
        raise FontValidationError(f"invalid styles XML in {path}: {exc}") from exc

    expected_default = str(policy["default_font"])
    if default_font is None or default_font.casefold() != expected_default.casefold():
        violations.append(
            _violation(
                "WEBFONT002",
                default_location,
                f"Workbook default explicit font must be {expected_default}; "
                f"found {default_font or '<missing>'}.",
            )
        )

    for location, font_name in declarations:
        folded = font_name.casefold()
        if folded in forbidden:
            violations.append(
                _violation(
                    "WEBFONT001",
                    location,
                    f"Forbidden explicit font {forbidden[folded]} is declared.",
                )
            )
        if folded not in allowed:
            violations.append(
                _violation(
                    "WEBFONT003",
                    location,
                    f"Explicit font {font_name} is outside the approved Aptos family.",
                )
            )

    # Keep unnamed style-table fonts fail-closed; they are explicit font records.
    for index, font_name in enumerate(style_fonts):
        if not font_name:
            violations.append(
                _violation(
                    "WEBFONT003",
                    f"xl/styles.xml#fonts[{index}]",
                    "Explicit font entry has no name.",
                )
            )

    unique: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in violations:
        key = (item["rule_id"], item["location"], item["message"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    explicit_fonts = list(dict.fromkeys(font_name for _, font_name in declarations))
    return {
        "schema": "webexcel-font-artifact-result/v1",
        "path": str(path),
        "filename": path.name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
        "default_font": default_font,
        "explicit_fonts": explicit_fonts,
        "font_declarations": [
            {"location": location, "font": font_name}
            for location, font_name in declarations
        ],
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
                            f"Workbook producer/configuration source contains "
                            f"forbidden font token {font}.",
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
        workbooks = [path.resolve() for path in args.workbook]
        output = _validate_output_path(args.output, workbooks) if args.output else None
        report = build_report(
            policy=policy,
            workbooks=workbooks,
            scan_source=args.scan_source,
        )
    except FontValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.summary:
        print(
            f"{report['status']}: Aptos WebExcel font validation; "
            f"artifacts={report['artifact_count']} violations={report['violation_count']}"
        )
        if output:
            print(output)
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
