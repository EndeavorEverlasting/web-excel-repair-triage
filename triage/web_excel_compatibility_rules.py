"""Read-only Excel-for-Web package-shape checks for generated XLSX workbooks."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Sequence
from xml.etree import ElementTree as ET

from triage.prompt_kit_common import NS, resolve_relationship_target, workbook_sheet_map, xml_root


@dataclass(frozen=True)
class WebExcelIssue:
    code: str
    message: str
    part: str = ""


def _read_text(zf: zipfile.ZipFile, name: str) -> str:
    return zf.read(name).decode("utf-8", errors="ignore")


def _relationship_targets(zf: zipfile.ZipFile, rel_name: str):
    try:
        root = ET.fromstring(zf.read(rel_name))
    except ET.ParseError:
        return []
    result = []
    for rel in root:
        target = rel.attrib.get("Target", "")
        if not target or rel.attrib.get("TargetMode", "").lower() == "external":
            continue
        result.append((rel.attrib.get("Id", ""), target))
    return result


_XML_PREFIX = r"[A-Za-z_][\w.-]*"
_NAMESPACE_DECL_RE = re.compile(rf"\bxmlns:({_XML_PREFIX})\s*=\s*(['\"]).*?\2", re.DOTALL)
_MC_PREFIX_LIST_RE = re.compile(
    rf"(?:\b{_XML_PREFIX}:)?(?:Ignorable|MustUnderstand)\s*=\s*(['\"])(.*?)\1",
    re.DOTALL,
)
_MC_QNAME_LIST_RE = re.compile(
    rf"(?:\b{_XML_PREFIX}:)?(?:ProcessContent|PreserveAttributes|PreserveElements)\s*=\s*(['\"])(.*?)\1",
    re.DOTALL,
)
_MC_CHOICE_REQUIRES_RE = re.compile(
    rf"<(?:{_XML_PREFIX}:)?Choice\b[^>]*?\bRequires\s*=\s*(['\"])(.*?)\1",
    re.DOTALL,
)


def _markup_compatibility_prefix_issues(zf: zipfile.ZipFile) -> List[WebExcelIssue]:
    """Reject lexical QName prefixes used by Office MC attributes but undeclared in the XML part.

    XML parsers do not validate namespace prefixes stored inside attribute values such as
    ``mc:Ignorable=\"x15 xr\"`` or ``mc:Choice Requires=\"x15\"``. A serializer can
    therefore rename namespace declarations to ``ns1``/``ns2`` while leaving those
    strings untouched, producing well-formed XML that Office cannot process.
    """
    issues: List[WebExcelIssue] = []
    for name in sorted(n for n in zf.namelist() if n.endswith(".xml")):
        text = _read_text(zf, name)
        declared = {match.group(1) for match in _NAMESPACE_DECL_RE.finditer(text)}
        declared.add("xml")
        referenced: list[tuple[str, str]] = []
        for match in _MC_PREFIX_LIST_RE.finditer(text):
            referenced.extend(("markup-compatibility prefix list", token) for token in match.group(2).split())
        for match in _MC_CHOICE_REQUIRES_RE.finditer(text):
            referenced.extend(("AlternateContent Choice Requires", token) for token in match.group(2).split())
        for match in _MC_QNAME_LIST_RE.finditer(text):
            for token in match.group(2).split():
                if ":" in token:
                    referenced.append(("markup-compatibility QName list", token.split(":", 1)[0]))
        seen = set()
        for source, prefix in referenced:
            key = (source, prefix)
            if not prefix or prefix in declared or key in seen:
                continue
            seen.add(key)
            issues.append(WebExcelIssue(
                "undeclared_markup_compatibility_prefix",
                f"{source} references undeclared namespace prefix {prefix!r}; XML may parse while Excel refuses the package.",
                name,
            ))
    return issues


def _formula_cells(zf: zipfile.ZipFile) -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    for sheet, part in workbook_sheet_map(zf).items():
        root = xml_root(zf, part)
        for cell in root.findall(".//m:c", NS):
            if cell.find("m:f", NS) is not None:
                result.add((sheet, cell.attrib.get("r", "")))
    return result


def _calc_chain_issues(zf: zipfile.ZipFile) -> List[WebExcelIssue]:
    if "xl/calcChain.xml" not in zf.namelist():
        return []
    workbook = xml_root(zf, "xl/workbook.xml")
    sheet_names_by_id = {
        sheet.attrib.get("sheetId", ""): sheet.attrib.get("name", "")
        for sheet in workbook.findall("m:sheets/m:sheet", NS)
        if sheet.attrib.get("sheetId")
    }
    formulas = _formula_cells(zf)
    issues: List[WebExcelIssue] = []
    root = xml_root(zf, "xl/calcChain.xml")
    for entry in root.findall("m:c", NS):
        sheet_id = entry.attrib.get("i", "")
        ref = entry.attrib.get("r", "")
        if not sheet_id.isdigit():
            issues.append(WebExcelIssue("invalid_calc_chain_sheet_id", f"Invalid calcChain sheetId {sheet_id!r}.", "xl/calcChain.xml"))
            continue
        sheet = sheet_names_by_id.get(sheet_id)
        if not sheet:
            issues.append(WebExcelIssue("calc_chain_sheet_id_not_found", f"calcChain sheetId {sheet_id} is not present in xl/workbook.xml.", "xl/calcChain.xml"))
            continue
        if (sheet, ref) not in formulas:
            issues.append(WebExcelIssue("stale_calc_chain_entry", f"calcChain entry {sheet}!{ref} does not point to a formula cell.", "xl/calcChain.xml"))
    return issues


def inspect_web_excel_package(path: str | Path) -> List[WebExcelIssue]:
    """Return package findings; an empty list is static compatibility evidence only."""
    issues: List[WebExcelIssue] = []
    workbook = Path(path)
    try:
        zf = zipfile.ZipFile(workbook)
    except (FileNotFoundError, zipfile.BadZipFile):
        return [WebExcelIssue("invalid_zip", "Workbook is missing or is not a valid .xlsx ZIP package.")]

    with zf:
        names = set(zf.namelist())
        for name in sorted(names):
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                ET.fromstring(zf.read(name))
            except ET.ParseError as exc:
                issues.append(WebExcelIssue("xml_parse_error", f"XML part failed to parse: {exc}.", name))

        issues.extend(_markup_compatibility_prefix_issues(zf))

        if "[Content_Types].xml" not in names:
            issues.append(WebExcelIssue("missing_content_types", "Missing [Content_Types].xml."))
        else:
            content_types = _read_text(zf, "[Content_Types].xml")
            if 'Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"' in content_types:
                issues.append(WebExcelIssue("bad_xml_default_content_type", "Default .xml content type must not be workbook-main; use application/xml plus explicit overrides.", "[Content_Types].xml"))
            if 'PartName="/xl/workbook.xml"' not in content_types or "spreadsheetml.sheet.main+xml" not in content_types:
                issues.append(WebExcelIssue("missing_workbook_content_type_override", "Workbook part must have an explicit spreadsheetml.sheet.main+xml override.", "[Content_Types].xml"))

        for rel_name in sorted(name for name in names if name.endswith(".rels")):
            for rel_id, target in _relationship_targets(zf, rel_name):
                issue_part = f"{rel_name}#{rel_id}" if rel_id else rel_name
                if target.startswith("#"):
                    continue
                if target.startswith("/"):
                    issues.append(WebExcelIssue("absolute_internal_relationship_target", "Unexpected absolute internal relationship target.", issue_part))
                resolved = resolve_relationship_target(rel_name, target)
                if resolved == ".." or resolved.startswith("../"):
                    issues.append(WebExcelIssue("relationship_target_escapes_package", f"Relationship target escapes package root: {target}.", issue_part))
                    continue
                if resolved.startswith("xl/drawings/charts/"):
                    issues.append(WebExcelIssue("drawing_rel_targets_chart_under_drawings", "Drawing chart relationship resolves under xl/drawings/charts/.", issue_part))
                if resolved not in names:
                    issues.append(WebExcelIssue("missing_relationship_target", f"Relationship target does not resolve in package: {target} -> {resolved}.", issue_part))

        if any(name.startswith("xl/drawings/charts/") for name in names):
            issues.append(WebExcelIssue("chart_parts_under_drawings", "Chart parts must live under xl/charts/chartN.xml, not xl/drawings/charts/.", "xl/drawings/charts/"))
        if any(name.startswith("xl/externalLinks/") for name in names):
            issues.append(WebExcelIssue("external_links_present", "Remove external workbook links before Web Excel submission.", "xl/externalLinks/"))

        table_names = []
        for name in names:
            if name.startswith("xl/tables/table") and name.endswith(".xml"):
                match = re.search(r'\bname="([^"]+)"', _read_text(zf, name))
                if match:
                    table_names.append((match.group(1), name))
        seen = set()
        for table_name, part in table_names:
            if table_name in seen:
                issues.append(WebExcelIssue("duplicate_table_name", f"Duplicate table name: {table_name}.", part))
            seen.add(table_name)

        for name in sorted(names):
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            text = _read_text(zf, name)
            if 't="inlineStr"' in text or "<is>" in text:
                issues.append(WebExcelIssue("inline_string_cells_present", "Use shared strings instead of inlineStr cell storage.", name))
            if "ns0:" in text or "xmlns:ns0" in text:
                issues.append(WebExcelIssue("ns0_namespace_pollution", "Remove ns0 namespace pollution from XML serialization.", name))
            if any(error in text for error in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")):
                issues.append(WebExcelIssue("formula_error_text_present", "Workbook package contains formula error text.", name))
            if re.search(r'<f\b[^>]*\bt="(?:array|shared)"', text):
                issues.append(WebExcelIssue("shared_or_array_formula_present", "Shared or array formula structures require a specific accepted workbook profile.", name))
            if any(token in text for token in ("_xlfn.", "_xlws.", "_xlpm.")):
                issues.append(WebExcelIssue("future_formula_namespace_token", "Future/dynamic formula namespace token detected.", name))

        issues.extend(_calc_chain_issues(zf))
    return issues


def assert_web_excel_compatible(path: str | Path) -> None:
    issues = inspect_web_excel_package(path)
    if issues:
        detail = "\n".join(f"- {issue.code}: {issue.message} [{issue.part}]" for issue in issues)
        raise AssertionError(f"Workbook is not statically Web Excel compatible:\n{detail}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    issues = inspect_web_excel_package(args.workbook)
    payload = {"compatible": not issues, "issues": [asdict(issue) for issue in issues]}
    print(json.dumps(payload, indent=2) if args.json else ("PASS" if not issues else "\n".join(f"FAIL {issue.code}: {issue.message} [{issue.part}]" for issue in issues)))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
