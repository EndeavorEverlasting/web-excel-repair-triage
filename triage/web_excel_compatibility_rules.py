"""Web Excel compatibility checks for generated XLSX packages.

These checks catch package-level issues that desktop Excel may repair silently but
Excel for the web may reject or render unpredictably.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class WebExcelIssue:
    code: str
    message: str
    part: str = ""


def _read_text(zf: zipfile.ZipFile, name: str) -> str:
    return zf.read(name).decode("utf-8", errors="ignore")


def _relationship_base(rel_name: str) -> str:
    if rel_name == "_rels/.rels":
        return ""
    if "/_rels/" not in rel_name or not rel_name.endswith(".rels"):
        return ""
    prefix, rel_file = rel_name.split("/_rels/", 1)
    source_part = f"{prefix}/{rel_file[:-5]}"
    return posixpath.dirname(source_part)


def _relationship_targets(zf: zipfile.ZipFile, rel_name: str) -> List[tuple[str, str]]:
    try:
        root = ET.fromstring(zf.read(rel_name))
    except ET.ParseError:
        return []

    rels = list(root.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"))
    rels.extend(root.findall("Relationship"))

    targets: List[tuple[str, str]] = []
    for rel in rels:
        target = rel.attrib.get("Target", "")
        if not target or rel.attrib.get("TargetMode", "").lower() == "external":
            continue
        targets.append((target, rel.attrib.get("Id", "")))
    return targets


def _resolve_target(rel_name: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(_relationship_base(rel_name), target)).lstrip("/")


def inspect_web_excel_package(path: str | Path) -> List[WebExcelIssue]:
    """Return Web Excel compatibility issues for an XLSX package.

    Rules intentionally inspect the package itself, not just workbook semantics.
    """
    issues: List[WebExcelIssue] = []
    path = Path(path)

    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return [WebExcelIssue("invalid_zip", "Workbook is not a valid .xlsx zip package.")]

    with zf:
        names = set(zf.namelist())

        for name in names:
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                ET.fromstring(zf.read(name))
            except ET.ParseError as exc:
                issues.append(WebExcelIssue("xml_parse_error", f"XML part failed to parse: {exc}.", name))

        if "[Content_Types].xml" not in names:
            issues.append(WebExcelIssue("missing_content_types", "Missing [Content_Types].xml."))
        else:
            ct = _read_text(zf, "[Content_Types].xml")
            if 'Extension="xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"' in ct:
                issues.append(WebExcelIssue(
                    "bad_xml_default_content_type",
                    "Default .xml content type must not be workbook-main. Use application/xml and explicit overrides.",
                    "[Content_Types].xml",
                ))
            if 'PartName="/xl/workbook.xml"' not in ct or "spreadsheetml.sheet.main+xml" not in ct:
                issues.append(WebExcelIssue(
                    "missing_workbook_content_type_override",
                    "Workbook part must have an explicit spreadsheetml.sheet.main+xml override.",
                    "[Content_Types].xml",
                ))

        for rel_name in [name for name in names if name.endswith(".rels")]:
            for target, rel_id in _relationship_targets(zf, rel_name):
                issue_part = f"{rel_name}#{rel_id}" if rel_id else rel_name
                if target.startswith("/"):
                    issues.append(WebExcelIssue(
                        "absolute_internal_relationship_target",
                        "Unexpected absolute internal relationship target.",
                        issue_part,
                    ))
                resolved = _resolve_target(rel_name, target)
                if resolved.startswith("../") or resolved == "..":
                    issues.append(WebExcelIssue(
                        "relationship_target_escapes_package",
                        f"Relationship target escapes package root: {target}.",
                        issue_part,
                    ))
                    continue
                if resolved.startswith("xl/drawings/charts/"):
                    issues.append(WebExcelIssue(
                        "drawing_rel_targets_chart_under_drawings",
                        "Drawing chart relationship resolves under xl/drawings/charts/.",
                        issue_part,
                    ))
                if resolved not in names:
                    issues.append(WebExcelIssue(
                        "missing_relationship_target",
                        f"Relationship target does not resolve in package: {target} -> {resolved}.",
                        issue_part,
                    ))

        if any(name.startswith("xl/drawings/charts/") for name in names):
            issues.append(WebExcelIssue(
                "chart_parts_under_drawings",
                "Chart parts must live under xl/charts/chartN.xml, not xl/drawings/charts/.",
                "xl/drawings/charts/",
            ))

        chart_parts = [name for name in names if name.startswith("xl/charts/chart") and name.endswith(".xml")]
        drawing_chart_rels = [name for name in names if name.startswith("xl/drawings/_rels/") and name.endswith(".rels")]
        for rel_name in drawing_chart_rels:
            rel_text = _read_text(zf, rel_name)
            if "/xl/drawings/charts/" in rel_text or "drawings/charts/" in rel_text:
                issues.append(WebExcelIssue(
                    "drawing_rel_targets_chart_under_drawings",
                    "Drawing chart relationships must target ../charts/chartN.xml or /xl/charts/chartN.xml.",
                    rel_name,
                ))
            chart_rel_count = rel_text.count("/officeDocument/2006/relationships/chart")
            if chart_rel_count and not chart_parts:
                issues.append(WebExcelIssue(
                    "chart_relationship_without_chart_parts",
                    "Drawing has chart relationships but no xl/charts/chartN.xml parts were found.",
                    rel_name,
                ))

        if any("calcChain" in name for name in names):
            issues.append(WebExcelIssue("calc_chain_present", "Remove stale xl/calcChain.xml before Web Excel submission.", "xl/calcChain.xml"))

        if any(name.startswith("xl/externalLinks/") for name in names):
            issues.append(WebExcelIssue("external_links_present", "Remove external workbook links before Web Excel submission.", "xl/externalLinks/"))

        table_names = []
        for name in names:
            if name.startswith("xl/tables/table") and name.endswith(".xml"):
                txt = _read_text(zf, name)
                m = re.search(r'\bname="([^"]+)"', txt)
                if m:
                    table_names.append((m.group(1), name))
        seen = set()
        for table_name, part in table_names:
            if table_name in seen:
                issues.append(WebExcelIssue("duplicate_table_name", f"Duplicate table name: {table_name}.", part))
            seen.add(table_name)

        for name in names:
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            txt = _read_text(zf, name)
            if 't="inlineStr"' in txt or "<is>" in txt:
                issues.append(WebExcelIssue("inline_string_cells_present", "Use shared strings instead of inlineStr cell storage.", name))
            if "ns0:" in txt or "xmlns:ns0" in txt:
                issues.append(WebExcelIssue("ns0_namespace_pollution", "Remove ns0 namespace pollution from XML serialization.", name))
            if any(err in txt for err in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A")):
                issues.append(WebExcelIssue("formula_error_text_present", "Workbook package contains formula error text.", name))

    return issues


def assert_web_excel_compatible(path: str | Path) -> None:
    """Raise AssertionError with readable messages if package is not Web Excel-safe."""
    issues = inspect_web_excel_package(path)
    if issues:
        detail = "\n".join(f"- {i.code}: {i.message} [{i.part}]" for i in issues)
        raise AssertionError(f"Workbook is not Web Excel compatible:\n{detail}")
