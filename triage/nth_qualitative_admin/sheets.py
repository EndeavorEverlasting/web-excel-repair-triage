"""Worksheet renderers for the qualitative admin NTH profile."""
from __future__ import annotations

from typing import Any, Mapping

from .model import Cell, _excel_serial, _month_day, _num, _parse_date, _planned_day_label, _short_month_day, derive_metrics
from .xml_writer import _add_merged, _completed_billing_status, _sheet_title_prefix, _worksheet_xml

def _dashboard(spec: Mapping[str, Any], metrics: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Executive Dashboard"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    prefix = _sheet_title_prefix(spec)
    _add_merged(rows, merges, "A1:L1", s["title"], f"{prefix} — Neuron Track Hours Executive Dashboard")
    if spec["mode"] == "month_to_date":
        subtitle = (
            f"Admin MTD view through {_month_day(spec['through_date'])} using direct paid attendance plus qualitative work context. "
            f"Planned {_month_day(spec['planned_date'])} work is visible but not posted as paid time."
        )
    else:
        subtitle = "Admin view of recorded paid hours with grounded work context. Direct attendance is quantitative; operational work is described qualitatively."
    _add_merged(rows, merges, "A2:L2", s["subtitle"], subtitle)

    if spec["mode"] == "completed_month":
        kpis = [
            ("A4:B4", "A5:B6", "RECORDED NTH", metrics["total_paid_hours"], s["kpi_label_blue"], s["kpi_value_blue"]),
            ("C4:D4", "C5:D6", "SHIFT RECORDS", metrics["completed_shift_records"], s["kpi_label_blue"], s["kpi_value_blue"]),
            ("E4:G4", "E5:G6", "PRIOR BASELINE", spec.get("prior_baseline") if spec.get("prior_baseline") is not None else "NOT PROVIDED", s["kpi_label_completed"], s["kpi_value_completed"]),
            ("H4:L4", "H5:L6", "BILLING STATUS", _completed_billing_status(metrics["total_paid_hours"], spec.get("prior_baseline")), s["kpi_label_completed"], s["kpi_value_completed"]),
        ]
    else:
        kpis = [
            ("A4:B4", "A5:B6", "MTD PAID HOURS", metrics["total_paid_hours"], s["kpi_label_blue"], s["kpi_value_blue"]),
            ("C4:D4", "C5:D6", "COMPLETED SHIFTS", metrics["completed_shift_records"], s["kpi_label_blue"], s["kpi_value_blue"]),
            ("E4:G4", "E5:G6", "THROUGH", _short_month_day(spec["through_date"]), s["kpi_label_green"], s["kpi_value_green"]),
            ("H4:I4", "H5:I6", "MTD STATUS", spec["mtd_status"], s["kpi_label_green"], s["kpi_value_green"]),
            ("J4:L4", "J5:L6", _planned_day_label(spec["planned_date"]), "PLANNED — NOT POSTED", s["kpi_label_green"], s["kpi_value_yellow"]),
        ]
    for label_ref, value_ref, label, value, label_style, value_style in kpis:
        _add_merged(rows, merges, label_ref, label_style, label)
        _add_merged(rows, merges, value_ref, value_style, value)

    _add_merged(rows, merges, "A8:D8", s["section_title"], "Technician Paid-Hour Tracking")
    _add_merged(rows, merges, "G8:L8", s["section_title"], "Operational Support Model")
    rows[9] = [
        Cell("A9", s["table_header_left"], "Technician"),
        Cell("B9", s["table_header_middle"], "Paid Hours"),
        Cell("C9", s["table_header_right"], "Shift Count"),
        Cell("G9", s["table_header_left"], "Theme"),
        Cell("H9", s["table_header_middle"], "Grounded readout"),
        Cell("I9", s["table_header_middle"]), Cell("J9", s["table_header_middle"]), Cell("K9", s["table_header_middle"]), Cell("L9", s["table_header_right"]),
    ]

    techs = metrics["technicians"]
    for idx, item in enumerate(techs, start=10):
        rows.setdefault(idx, []).extend([
            Cell(f"A{idx}", s["body_left"], item["technician"]),
            Cell(f"B{idx}", s["body_hours"], item["paid_hours"]),
            Cell(f"C{idx}", s["body_right"], item["shift_count"]),
        ])
    total_row = 10 + len(techs)
    rows.setdefault(total_row, []).extend([
        Cell(f"A{total_row}", s["total_left"], "TOTAL"),
        Cell(f"B{total_row}", s["total_hours"], metrics["total_paid_hours"]),
        Cell(f"C{total_row}", s["total_right"], metrics["completed_shift_records"]),
    ])

    themes = spec["operational_themes"]
    for offset, item in enumerate(themes):
        r = 10 + offset
        last = offset == len(themes) - 1
        left = s["wrapped_total_left"] if last else s["wrapped_left"]
        mid = s["wrapped_total_middle"] if last else s["wrapped_middle"]
        right = s["wrapped_total_right"] if last else s["wrapped_right"]
        rows.setdefault(r, []).append(Cell(f"G{r}", left, item["theme"]))
        _add_merged(rows, merges, f"H{r}:L{r}", mid, item["readout"])
        rows[r] = [cell if cell.ref != f"L{r}" else Cell(f"L{r}", right) for cell in rows[r]]

    second_section = max(18, 10 + max(len(techs) + 1, len(themes)) + 3)
    _add_merged(rows, merges, f"A{second_section}:D{second_section}", s["section_title"], "Daily Paid-Hour Record")
    _add_merged(rows, merges, f"G{second_section}:L{second_section}", s["section_title"], "Executive Readout")
    header = second_section + 1
    rows[header] = [
        Cell(f"A{header}", s["table_header_left"], "Date"),
        Cell(f"B{header}", s["table_header_middle"], "Day"),
        Cell(f"C{header}", s["table_header_middle"], "Paid Hours"),
        Cell(f"D{header}", s["table_header_right"], "Shifts"),
        Cell(f"G{header}", s["table_header_left"], "Finding"),
        Cell(f"H{header}", s["table_header_middle"], "Management interpretation"),
        Cell(f"I{header}", s["table_header_middle"]), Cell(f"J{header}", s["table_header_middle"]), Cell(f"K{header}", s["table_header_middle"]), Cell(f"L{header}", s["table_header_right"]),
    ]

    daily = metrics["daily"]
    for offset, item in enumerate(daily):
        r = header + 1 + offset
        last = offset == len(daily) - 1
        rows.setdefault(r, []).extend([
            Cell(f"A{r}", s["date_last"] if last else s["date_left"], _excel_serial(item["date"]), "n"),
            Cell(f"B{r}", s["day_last"] if last else s["date_middle"], item["day"]),
            Cell(f"C{r}", s["hours_last"] if last else s["body_hours"], item["paid_hours"]),
            Cell(f"D{r}", s["count_last"] if last else s["body_right"], item["shift_count"]),
        ])

    if spec["mode"] == "completed_month":
        readout: list[dict[str, str]] = [
            {
                "finding": "Recorded month",
                "management_interpretation": f"{_num(metrics['total_paid_hours'])} paid hours across {metrics['completed_shift_records']} shift records.",
            }
        ]
        if spec.get("prior_baseline") is not None:
            readout.append(
                {
                    "finding": "Billing reconciliation",
                    "management_interpretation": f"The current NTH record is {_num(metrics['total_paid_hours'])}; the prior billing baseline is {_num(spec['prior_baseline'])} and {_completed_billing_status(metrics['total_paid_hours'], spec['prior_baseline']).split(' — ',1)[0].lower()} needs to be reflected in review.",
                }
            )
        readout.extend(spec.get("executive_readout", []))
        presentation = "Use paid hours by date/technician as the quantitative record. Describe workstreams qualitatively unless direct task/time evidence supports a split."
    else:
        tech_text = ", ".join(
            f"{item['technician']} {_num(item['paid_hours'])}h"
            for item in techs if item["paid_hours"]
        )
        readout = [
            {
                "finding": "MTD paid control",
                "management_interpretation": f"{_num(metrics['total_paid_hours'])} paid hours across {metrics['completed_shift_records']} completed shifts through {_short_month_day(spec['through_date'])}" + (f": {tech_text}." if tech_text else "."),
            }
        ]
        readout.extend(spec.get("executive_readout", []))
        presentation = "Admin reporting stays quantitative for paid attendance and qualitative for workstream context; no task-hour split is inferred."
    readout = [item for item in readout if str(item.get("finding", "")).casefold() != "presentation rule"]
    readout.append({"finding": "Presentation rule", "management_interpretation": presentation})
    for offset, item in enumerate(readout):
        r = header + 1 + offset
        last = offset == len(readout) - 1
        left = s["wrapped_total_left"] if last else s["wrapped_left"]
        mid = s["wrapped_total_middle"] if last else s["wrapped_middle"]
        right = s["wrapped_total_right"] if last else s["wrapped_right"]
        rows.setdefault(r, []).append(Cell(f"G{r}", left, item["finding"]))
        _add_merged(rows, merges, f"H{r}:L{r}", mid, item["management_interpretation"])
        rows[r] = [cell if cell.ref != f"L{r}" else Cell(f"L{r}", right) for cell in rows[r]]
    return _worksheet_xml(widths, rows, merges)


def _visual_summary(spec: Mapping[str, Any], metrics: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Visual Summary"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:J1", s["title"], f"{_sheet_title_prefix(spec)} — Visual Summary")
    _add_merged(rows, merges, "A2:J2", s["subtitle"], profile["language_profiles"]["visual_summary"]["fixed_subtitle"])
    rows[4] = [
        Cell("A4", s["detail_header_left"], "Technician"),
        Cell("B4", s["detail_header_middle"], "Paid Hours"),
        Cell("C4", s["detail_header_right"], "Shift Count"),
        Cell("F4", s["detail_header_left"], "Date"),
        Cell("G4", s["detail_header_middle"], "Day"),
        Cell("H4", s["detail_header_middle"], "Paid Hours"),
        Cell("I4", s["detail_header_right"], "Shift Count"),
    ]
    techs = metrics["technicians"]
    for offset, item in enumerate(techs):
        r = 5 + offset
        rows.setdefault(r, []).extend([
            Cell(f"A{r}", s["body_left"], item["technician"]),
            Cell(f"B{r}", s["body_hours"], item["paid_hours"]),
            Cell(f"C{r}", s["body_right"], item["shift_count"]),
        ])
    total_row = 5 + len(techs)
    rows.setdefault(total_row, []).extend([
        Cell(f"A{total_row}", s["total_left"], "TOTAL"),
        Cell(f"B{total_row}", s["total_hours"], metrics["total_paid_hours"]),
        Cell(f"C{total_row}", s["total_right"], metrics["completed_shift_records"]),
    ])
    daily = metrics["daily"]
    for offset, item in enumerate(daily):
        r = 5 + offset
        last = offset == len(daily) - 1
        rows.setdefault(r, []).extend([
            Cell(f"F{r}", s["date_last"] if last else s["date_left"], _excel_serial(item["date"]), "n"),
            Cell(f"G{r}", s["day_last"] if last else s["date_middle"], item["day"]),
            Cell(f"H{r}", s["hours_last"] if last else s["body_hours"], item["paid_hours"]),
            Cell(f"I{r}", s["count_last"] if last else s["body_right"], item["shift_count"]),
        ])
    return _worksheet_xml(widths, rows, merges)


def _detail_sheet(spec: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["NTH Detail"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:F1", s["title"], f"{_sheet_title_prefix(spec)} — Neuron Track Hours Detail")
    _add_merged(rows, merges, "A2:F2", s["subtitle"], profile["language_profiles"]["detail"]["fixed_subtitle"])
    rows[4] = [
        Cell("A4", s["detail_header_left"], "Date"),
        Cell("B4", s["detail_header_middle"], "Day"),
        Cell("C4", s["detail_header_middle"], "Technician"),
        Cell("D4", s["detail_header_middle"], "Paid Hours"),
        Cell("E4", s["detail_header_middle"], "Program / Assignment"),
        Cell("F4", s["detail_header_right"], "Qualitative Work Context"),
    ]
    detail = spec["detail_rows"]
    for offset, item in enumerate(detail):
        r = 5 + offset
        last = offset == len(detail) - 1
        rows[r] = [
            Cell(f"A{r}", s["wrapped_date_total"] if last else s["wrapped_date_left"], _excel_serial(item["date"]), "n"),
            Cell(f"B{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["date"].strftime("%a")),
            Cell(f"C{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["technician"]),
            Cell(f"D{r}", s["wrapped_hours_total"] if last else s["wrapped_hours_middle"], item["paid_hours"]),
            Cell(f"E{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["program_assignment"]),
            Cell(f"F{r}", s["wrapped_total_right"] if last else s["wrapped_right"], item["qualitative_work_context"]),
        ]
    return _worksheet_xml(widths, rows, merges)


def _operational_themes(spec: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Operational Themes"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:C1", s["title"], f"{_sheet_title_prefix(spec)} — Operational Themes")
    _add_merged(rows, merges, "A2:C2", s["subtitle"], profile["language_profiles"]["operational_themes"]["fixed_subtitle"])
    rows[4] = [
        Cell("A4", s["detail_header_left"], "Operational Theme"),
        Cell("B4", s["detail_header_middle"], "Evidence-Bounded Readout"),
        Cell("C4", s["detail_header_right"], "Why It Matters to NTH"),
    ]
    items = spec["operational_themes"]
    for offset, item in enumerate(items):
        r = 5 + offset
        last = offset == len(items) - 1
        rows[r] = [
            Cell(f"A{r}", s["wrapped_total_left"] if last else s["wrapped_left"], item["theme"]),
            Cell(f"B{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["readout"]),
            Cell(f"C{r}", s["wrapped_total_right"] if last else s["wrapped_right"], item["why"]),
        ]
    return _worksheet_xml(widths, rows, merges)


def _billing_support(spec: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Billing Support Context"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:C1", s["title"], f"{spec['month_label']} — Billing Support Context")
    _add_merged(rows, merges, "A2:C2", s["subtitle"], profile["language_profiles"]["billing_support_context"]["fixed_subtitle"])
    rows[4] = [
        Cell("A4", s["detail_header_left"], "Control / context"),
        Cell("B4", s["detail_header_right"], "Grounded statement"),
    ]
    items = spec["billing_support_context"]
    auto_items: list[dict[str, Any]] = [
        {"control": f"{spec['month_label'].split()[0]} NTH", "statement": f"{_num(derive_metrics(spec)['total_paid_hours'])} paid hours across {derive_metrics(spec)['completed_shift_records']} shift records."}
    ]
    if spec.get("prior_baseline") is not None:
        auto_items.append({"control": "Prior billing baseline", "statement": f"{_num(spec['prior_baseline'])}; compare against the current recorded NTH before external use."})
    seen = {item["control"].casefold() for item in auto_items}
    all_items = auto_items + [item for item in items if item["control"].casefold() not in seen]
    for offset, item in enumerate(all_items):
        r = 5 + offset
        last = offset == len(all_items) - 1
        rows[r] = [
            Cell(f"A{r}", s["wrapped_total_left"] if last else s["wrapped_left"], item["control"]),
            Cell(f"B{r}", s["wrapped_total_right"] if last else s["wrapped_right"], item["statement"]),
        ]
    boundary_row = 5 + len(all_items) + 2
    _add_merged(rows, merges, f"A{boundary_row}:C{boundary_row}", s["section_title"], "External-use boundary")
    _add_merged(rows, merges, f"A{boundary_row+1}:C{boundary_row+3}", s["boundary_note"], spec["external_use_boundary"])
    return _worksheet_xml(widths, rows, merges)


def _carryover(spec: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Carryover & Planned Work"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:G1", s["title"], f"{spec['month_label']} — Carryover & Planned Work")
    _add_merged(rows, merges, "A2:G2", s["subtitle"], profile["language_profiles"]["carryover_planned_work"]["fixed_subtitle"])
    headers = ["Planned Date", "Owner", "Carryover / Planned Item", "Project", "Paid Hours Posted", "Status", "Context"]
    rows[4] = [
        Cell("A4", s["detail_header_left"], headers[0]),
        *[Cell(f"{col}4", s["detail_header_middle"], header) for col, header in zip("BCDEF", headers[1:6])],
        Cell("G4", s["detail_header_right"], headers[6]),
    ]
    items = spec["carryover_planned_work"]
    for offset, item in enumerate(items):
        r = 5 + offset
        last = offset == len(items) - 1
        d = _parse_date(item["planned_date"], f"carryover_planned_work[{offset}].planned_date")
        rows[r] = [
            Cell(f"A{r}", s["wrapped_date_total"] if last else s["wrapped_date_left"], _excel_serial(d), "n"),
            Cell(f"B{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["owner"]),
            Cell(f"C{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["item"]),
            Cell(f"D{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["project"]),
            Cell(f"E{r}", s["wrapped_hours_total"] if last else s["wrapped_hours_middle"], 0),
            Cell(f"F{r}", s["wrapped_total_middle"] if last else s["wrapped_middle"], item["status"]),
            Cell(f"G{r}", s["wrapped_total_right"] if last else s["wrapped_right"], item["context"]),
        ]
    return _worksheet_xml(widths, rows, merges)


def _technical_scope(spec: Mapping[str, Any], profile: Mapping[str, Any]) -> bytes:
    s = profile["visual_contract"]["style_ids"]
    widths = profile["sheet_profiles"]["Configuration & Inventory Context"]["columns"]
    rows: dict[int, list[Cell]] = {}
    merges: list[str] = []
    _add_merged(rows, merges, "A1:B1", s["title"], f"{spec['month_label']} — Technical Scope Context")
    _add_merged(rows, merges, "A2:B2", s["subtitle"], profile["language_profiles"]["technical_scope_context"]["fixed_subtitle"])
    rows[4] = [
        Cell("A4", s["detail_header_left"], "Control / event"),
        Cell("B4", s["detail_header_right"], "Grounded statement"),
    ]
    items = spec["technical_scope_context"]
    for offset, item in enumerate(items):
        r = 5 + offset
        last = offset == len(items) - 1
        rows[r] = [
            Cell(f"A{r}", s["wrapped_total_left"] if last else s["wrapped_left"], item["control"]),
            Cell(f"B{r}", s["wrapped_total_right"] if last else s["wrapped_right"], item["statement"]),
        ]
    closing_row = 5 + len(items) + 2
    _add_merged(rows, merges, f"A{closing_row}:B{closing_row+3}", s["boundary_note"], spec["technical_scope_closing_note"])
    return _worksheet_xml(widths, rows, merges)

