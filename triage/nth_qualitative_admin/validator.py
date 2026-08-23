"""Static package/profile validator for qualitative admin NTH workbooks."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .model import PROFILE_PATH, THEME_PATH, _excel_serial, derive_metrics, load_profile
from .style_template import canonical_styles_xml
from .xml_writer import MAIN_NS

NS = {"x": MAIN_NS}


class QualitativeAdminValidationError(RuntimeError):
    """Raised when a generated workbook drifts from the qualitative-admin contract."""


def _expected_members(sheet_count: int) -> set[str]:
    base = {
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        "xl/styles.xml",
        "xl/theme/theme1.xml",
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


def _cell(root: ET.Element, ref: str) -> ET.Element:
    cell = root.find(f".//x:c[@r='{ref}']", NS)
    if cell is None:
        raise QualitativeAdminValidationError(f"missing required cell: {ref}")
    return cell


def _cell_value(root: ET.Element, ref: str) -> str | float | None:
    cell = _cell(root, ref)
    value = cell.find("x:v", NS)
    if value is None:
        return None
    text = value.text or ""
    if cell.attrib.get("t") == "n":
        try:
            number = float(text)
        except ValueError as exc:
            raise QualitativeAdminValidationError(f"{ref} is not valid numeric SpreadsheetML: {text!r}") from exc
        if not math.isfinite(number):
            raise QualitativeAdminValidationError(f"{ref} contains non-finite numeric SpreadsheetML")
        return number
    return text


def _require_value(actual: str | float | None, expected: Any, label: str) -> None:
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            actual_number = float(actual)  # type: ignore[arg-type]
            expected_number = float(expected)
        except (TypeError, ValueError) as exc:
            raise QualitativeAdminValidationError(
                f"{label} numeric reconciliation failed: workbook={actual!r} evidence={expected!r}"
            ) from exc
        if not math.isfinite(actual_number) or not math.isfinite(expected_number):
            raise QualitativeAdminValidationError(f"{label} contains non-finite numeric evidence")
        if not math.isclose(actual_number, expected_number, rel_tol=0.0, abs_tol=1e-9):
            raise QualitativeAdminValidationError(
                f"{label} reconciliation failed: workbook={actual_number} evidence={expected_number}"
            )
        return
    if actual != expected:
        raise QualitativeAdminValidationError(
            f"{label} reconciliation failed: workbook={actual!r} evidence={expected!r}"
        )


def _reconcile_detail(detail_root: ET.Element, spec: Mapping[str, Any]) -> None:
    data_rows = [
        row
        for row in detail_root.findall(".//x:sheetData/x:row", NS)
        if int(row.attrib["r"]) >= 5
    ]
    expected_rows = spec["detail_rows"]
    if len(data_rows) != len(expected_rows):
        raise QualitativeAdminValidationError(
            f"detail row reconciliation failed: workbook={len(data_rows)} evidence={len(expected_rows)}"
        )
    for offset, expected in enumerate(expected_rows, start=5):
        values = (
            (_cell_value(detail_root, f"A{offset}"), _excel_serial(expected["date"]), "date"),
            (_cell_value(detail_root, f"B{offset}"), expected["date"].strftime("%a"), "day"),
            (_cell_value(detail_root, f"C{offset}"), expected["technician"], "technician"),
            (_cell_value(detail_root, f"D{offset}"), expected["paid_hours"], "paid_hours"),
            (_cell_value(detail_root, f"E{offset}"), expected["program_assignment"], "program_assignment"),
            (_cell_value(detail_root, f"F{offset}"), expected["qualitative_work_context"], "qualitative_work_context"),
        )
        for actual, expected_value, field in values:
            _require_value(actual, expected_value, f"detail row {offset - 4} {field}")


def _reconcile_dashboard(dashboard_root: ET.Element, spec: Mapping[str, Any]) -> None:
    metrics = derive_metrics(spec)
    _require_value(_cell_value(dashboard_root, "A5"), metrics["total_paid_hours"], "dashboard total paid hours")
    _require_value(
        _cell_value(dashboard_root, "C5"),
        metrics["completed_shift_records"],
        "dashboard completed shift records",
    )

    techs = metrics["technicians"]
    for offset, expected in enumerate(techs, start=10):
        _require_value(_cell_value(dashboard_root, f"A{offset}"), expected["technician"], f"technician row {offset - 9} name")
        _require_value(_cell_value(dashboard_root, f"B{offset}"), expected["paid_hours"], f"technician row {offset - 9} paid hours")
        _require_value(_cell_value(dashboard_root, f"C{offset}"), expected["shift_count"], f"technician row {offset - 9} shift count")
    total_row = 10 + len(techs)
    _require_value(_cell_value(dashboard_root, f"A{total_row}"), "TOTAL", "technician total label")
    _require_value(_cell_value(dashboard_root, f"B{total_row}"), metrics["total_paid_hours"], "technician total paid hours")
    _require_value(_cell_value(dashboard_root, f"C{total_row}"), metrics["completed_shift_records"], "technician total shift count")

    second_section = max(18, 10 + max(len(techs) + 1, len(spec["operational_themes"])) + 3)
    first_daily_row = second_section + 2
    for index, expected in enumerate(metrics["daily"]):
        row = first_daily_row + index
        _require_value(_cell_value(dashboard_root, f"A{row}"), _excel_serial(expected["date"]), f"daily row {index + 1} date")
        _require_value(_cell_value(dashboard_root, f"B{row}"), expected["day"], f"daily row {index + 1} day")
        _require_value(_cell_value(dashboard_root, f"C{row}"), expected["paid_hours"], f"daily row {index + 1} paid hours")
        _require_value(_cell_value(dashboard_root, f"D{row}"), expected["shift_count"], f"daily row {index + 1} shift count")


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
                f"OOXML member set drifted; missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
            )
        if zf.read("xl/styles.xml") != canonical_styles_xml():
            raise QualitativeAdminValidationError("styles.xml drifted from canonical generated style table")
        theme = zf.read("xl/theme/theme1.xml")
        if theme != THEME_PATH.read_bytes():
            raise QualitativeAdminValidationError("theme1.xml drifted from committed canonical theme template")
        try:
            ET.fromstring(theme)
        except ET.ParseError as exc:
            raise QualitativeAdminValidationError(f"theme1.xml is not well-formed XML: {exc}") from exc

        shared = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        if list(shared) or (shared.text or "").strip():
            raise QualitativeAdminValidationError("sharedStrings.xml must remain present and empty")

        roots: list[ET.Element] = []
        formula_count = 0
        for idx, sheet_name in enumerate(names, 1):
            root = ET.fromstring(zf.read(f"xl/worksheets/sheet{idx}.xml"))
            roots.append(root)
            formulas = len(root.findall(".//x:f", NS))
            formula_count += formulas
            for forbidden in (
                ".//x:dimension",
                ".//x:autoFilter",
                ".//x:conditionalFormatting",
                ".//x:dataValidations",
                ".//x:drawing",
                ".//x:sheetViews",
                ".//x:pane",
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
                        f"{sheet_name} is missing required merge ranges: {sorted(static - actual_merges)}"
                    )
            elif role == "Executive Dashboard" and isinstance(merge_cfg, dict):
                required = set(merge_cfg["common"])
                required.update(
                    merge_cfg["month_to_date_kpis"]
                    if spec is not None and spec.get("mode") == "month_to_date"
                    else merge_cfg["completed_kpis"]
                )
                if required - actual_merges:
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} is missing required dashboard merge ranges: {sorted(required - actual_merges)}"
                    )
            expected_profile = profile["sheet_profiles"].get(role)
            if expected_profile:
                got = _widths(root)
                wanted = [float(value) for value in expected_profile["columns"]]
                if got != wanted:
                    raise QualitativeAdminValidationError(
                        f"{sheet_name} column widths drifted: got={got} expected={wanted}"
                    )
            findings.append(
                {
                    "sheet": sheet_name,
                    "columns": _widths(root),
                    "merge_count": len(_merges(root)),
                    "formula_count": formulas,
                }
            )
        if formula_count:
            raise QualitativeAdminValidationError(
                f"worksheet formula policy violated: found {formula_count} formula nodes"
            )

        joined = "\n".join(
            (node.text or "")
            for root in roots
            for node in root.findall(".//x:c[@t='str']/x:v", NS)
        )
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
            expected_names = [
                item.replace("{month_label}", spec["month_label"])
                for item in profile["mode_contracts"][spec["mode"]]["sheet_order"]
            ]
            if names != expected_names:
                raise QualitativeAdminValidationError(
                    f"sheet order drifted: got={names} expected={expected_names}"
                )
            detail_sheet = next(name for name in names if name.endswith(" NTH Detail"))
            detail_idx = names.index(detail_sheet)
            _reconcile_detail(roots[detail_idx], spec)
            _reconcile_dashboard(roots[0], spec)

    return {
        "schema_version": "nth-qualitative-admin-validation/v1",
        "status": "PASS",
        "profile_id": profile["profile_id"],
        "profile_path": str(PROFILE_PATH.relative_to(PROFILE_PATH.parents[2])).replace("\\", "/"),
        "workbook": str(workbook),
        "sheet_count": len(findings),
        "formula_count": 0,
        "shared_strings": "present_and_empty",
        "minimal_package_members": True,
        "canonical_style_template": True,
        "canonical_theme_template": True,
        "evidence_reconciliation": "detail_rows + dashboard totals + technician controls + daily controls",
        "sheets": findings,
        "proof_ceiling": "static OOXML/style/language-profile and supplied-evidence reconciliation; not source-evidence provenance or operator/client acceptance",
    }
