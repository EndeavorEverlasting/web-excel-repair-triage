"""Web Excel compatibility checks for generated XLSX packages.

These checks catch package-level issues that desktop Excel may repair silently but
Excel for the web may reject or render unpredictably.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import re
import zipfile


@dataclass(frozen=True)
class WebExcelIssue:
    code: str
    message: str
    part: str = ""


def _read_text(zf: zipfile.ZipFile, name: str) -> str:
    return zf.read(name).decode("utf-8", errors="ignore")


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
            rel_parent = "/".join(rel_name.split("/")[:-2]) + "/"
            targets_under_drawings = False
            for tm in re.finditer(r'Target="([^"]+)"', rel_text):
                target = tm.group(1)
                resolved = target if target.startswith("/") else rel_parent + target
                if "drawings/charts/" in resolved:
                    targets_under_drawings = True
                    break
            if targets_under_drawings or "/xl/drawings/charts/" in rel_text or "drawings/charts/" in rel_text:
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
