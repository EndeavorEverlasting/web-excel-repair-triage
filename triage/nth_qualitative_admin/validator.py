"""Static package/profile validator for qualitative admin NTH workbooks."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .builder import MAIN_NS, PROFILE_PATH, THEME_PATH, load_profile
from .style_template import canonical_styles_xml

NS = {"x": MAIN_NS}


class QualitativeAdminValidationError(RuntimeError):
    """Raised when a generated workbook drifts from the qualitative-admin contract."""


def _expected_members(sheet_count: int) -> set[str]:
    base = {
        "[Content_Types].xml", "_rels/.rels", "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/theme/theme1.xml",
        "xl/sharedStrings.xml",
    }
    base.update(f"xl/worksheets/sheet{idx}.xml" for idx in range(1, sheet_count + 1))
    return base


def _sheet_names(zf: ZipFile) -> list[str]:
    root = ET.fromstring(zf.read("xl/workbook.xml"))
    return [item.attrib["name"] for item in root.findall(".//x:sheets/x:sheet", NS)]


def _role_for_sheet(name: str) -> str:
    return "NTH Detail" if name.endswith(" NTH Detail") else name


def _widths(root: ET.Element) -> list[float]:
    return [float(col.attrib["width"]) for col in root.findall(".//x:cols/x:col", NS)]


def _merges(root: ET.Element) -> list[str]:
    return [item.attrib["ref"] for item in root.findall(".//x:mergeCells/x:mergeCell", NS)]


def validate_workbook(path: str | Path, spec: Mapping[str, Any] | None = None) -> dict[str, Any]:
    workbook = Path(path)
    profile = load_profile()
    if not workbook.is_file():
        raise QualitativeAdminValidationError(f"workbook not found: {workbook}")

    findings: list[dict[str, Any]] = []
    with ZipFile(workbook) as zf:
        names = _sheet_names(zf)
        expected = _expected_members(len(names))
        actual = set(zf.namelist())
        if actual != expected:
            raise QualitativeAdminValidationError(
                f"OOXML member set drifted; missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
            )
        if zf.read("xl/styles.xml") != canonical_styles_xml():
            raise QualitativeAdminValidationError("styles.xml drifted from canonical generated style table")
        if zf.read("xl/theme/theme1.xml") != THEME_PATH.read_bytes():
            raise QualitativeAdminValidationError("theme1.xml drifted from committed canonical theme template")
        shared = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        if list(shared) or (shared.text or "").strip():
            raise QualitativeAdminValidationError("sharedStrings.xml must remain present and empty")

        formula_count = 0
        for idx, sheet_name in enumerate(names, 1):
            root = ET.fromstring(zf.read(f"xl/worksheets/sheet{idx}.xml"))
            formulas = len(root.findall(".//x:f", NS))
            formula_count += formulas
            for forbidden in (
                ".//x:dimension", ".//x:autoFilter", ".//x:conditionalFormatting",
                ".//x:dataValidations", ".//x:drawing", ".//x:sheetViews", ".//x:pane",
            ):
                if root.findall(forbidden, NS):
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} contains forbidden worksheet structure: {forbidden}"
                    )
            sheet_format = root.find("x:sheetFormatPr", NS)
            if sheet_format is None or float(sheet_format.attrib.get("defaultRowHeight", "0")) != 15:
                raise QualitativeAdminValidationError(f"{sheet_name} default row height must be 15")
            title_row = root.find(".//x:sheetData/x:row[@r='1']", NS)
            if title_row is None or float(title_row.attrib.get("ht", "0")) != 30:
                raise QualitativeAdminValidationError(f"{sheet_name} title row height must be 30")
            role = _role_for_sheet(sheet_name)
            actual_merges = set(_merges(root))
            merge_cfg = profile.get("merge_contract", {}).get(role)
            if isinstance(merge_cfg, list):
                static = {item for item in merge_cfg if not item.startswith("dynamic ")}
                if static - actual_merges:
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} is missing required merge ranges: {sorted(static-actual_merges)}"
                    )
            elif role == "Executive Dashboard" and isinstance(merge_cfg, dict):
                required = set(merge_cfg["common"])
                required.update(
                    merge_cfg["month_to_date_kpis"] if spec is not None and spec.get("mode") == "month_to_date"
                    else merge_cfg["completed_kpis"]
                )
                if required - actual_merges:
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} is missing required dashboard merge ranges: {sorted(required-actual_merges)}"
                    )
            expected_profile = profile["sheet_profiles"].get(role)
            if expected_profile:
                got = _widths(root)
                wanted = [float(value) for value in expected_profile["columns"]]
                if got != wanted:
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} column widths drifted: got={got} expected={wanted}"
                    )
            findings.append({"sheet":sheet_name,"columns":_widths(root),"merge_count":len(_merges(root)),"formula_count":formulas})
        if formula_count:
            raise QualitativeAdminValidationError(f"worksheet formula policy violated: found {formula_count} formula nodes")

        strings: list[str] = []
        for idx in range(1, len(names) + 1):
            root = ET.fromstring(zf.read(f"xl/worksheets/sheet{idx}.xml"))
            strings.extend((node.text or "") for node in root.findall(".//x:c[@t='str']/x:v", NS))
        joined = "\n".join(strings)
        for key, cfg in profile["language_profiles"].items():
            fixed = cfg.get("fixed_subtitle")
            if not fixed or fixed in joined:
                continue
            if key == "billing_support_context" and "Billing Support Context" not in names:
                continue
            if key in {"carryover_planned_work", "technical_scope_context"} and "Carryover & Planned Work" not in names:
                continue
            raise QualitativeAdminValidationError(f"missing fixed language posture: {key}")

        if spec is not None:
            expected_names = [item.replace("{month_label}", spec["month_label"]) for item in profile["mode_contracts"][spec["mode"]]["sheet_order"]]
            if names != expected_names:
                raise QualitativeAdminValidationError(f"sheet order drifted: got={names} expected={expected_names}")
            detail_sheet = next(name for name in names if name.endswith(" NTH Detail"))
            detail_idx = names.index(detail_sheet) + 1
            detail_root = ET.fromstring(zf.read(f"xl/worksheets/sheet{detail_idx}.xml"))
            data_rows = [row for row in detail_root.findall(".//x:sheetData/x:row", NS) if int(row.attrib["r"]) >= 5]
            if len(data_rows) != len(spec["detail_rows"]):
                raise QualitativeAdminValidationError(
                    f"detail row reconciliation failed: workbook={len(data_rows)} evidence={len(spec['detail_rows'])}"
                )

    return {
        "schema_version": "nth-qualitative-admin-validation/v1", "status": "PASS",
        "profile_id": profile["profile_id"],
        "profile_path": str(PROFILE_PATH.relative_to(PROFILE_PATH.parents[2])).replace("\\", "/"),
        "workbook": str(workbook), "sheet_count": len(findings), "formula_count": 0,
        "shared_strings": "present_and_empty", "minimal_package_members": True,
        "canonical_style_template": True, "canonical_theme_template": True, "sheets": findings,
        "proof_ceiling": "static OOXML/style/language-profile validation; not source-evidence or operator/client acceptance",
    }
