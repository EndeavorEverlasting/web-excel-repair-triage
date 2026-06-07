"""Build company-style Project Team workbook from roster + visual donor."""
from __future__ import annotations

from pathlib import Path
from typing import List

from triage.admin_billing_summary.models import DailyRecord
from triage.nw_prj_admin_log.grid import (
    ProjectTeamGridError,
    ensure_dates_present,
    find_data_header_row,
    write_records_to_grid,
)
from triage.nw_prj_admin_log.reader import month_span_bounds, required_grid_dates
from triage.nw_prj_admin_log.visual_donor import apply_layout_rules, prepare_donor_workbook
from triage.xlsx_utils import fix_inlinestr

DELIVERY_NAME_TEMPLATE = (
    "Candidate_Admin_Log_NW_PRJ_Tech_Hours_PROJECT_TEAM_COMPANY_STYLE_from_Roster_{date}.xlsx"
)


def delivery_filename(run_date: str | None = None) -> str:
    from datetime import date as _date
    d = run_date or _date.today().isoformat()
    return DELIVERY_NAME_TEMPLATE.format(date=d)


def export_project_team_workbook(
    *,
    roster_records: List[DailyRecord],
    month_keys: List[str],
    visual_donor_path: str | Path,
    output_path: str | Path,
) -> str:
    prepare_donor_workbook(visual_donor_path, output_path)

    import openpyxl

    span_start, span_end = month_span_bounds(month_keys)
    required = required_grid_dates(month_keys, roster_records)

    wb = openpyxl.load_workbook(output_path)
    if "Project Team" not in wb.sheetnames:
        wb.close()
        raise ProjectTeamGridError("missing Project Team sheet")
    ws = wb["Project Team"]
    hdr_row = find_data_header_row(ws)
    if hdr_row is None:
        wb.close()
        raise ProjectTeamGridError("Project Team: Techs header row not found")
    sub_hdr_row = hdr_row + 1
    ensure_dates_present(ws, hdr_row, sub_hdr_row, required)
    write_records_to_grid(ws, roster_records, span_start=span_start, span_end=span_end)
    wb.save(output_path)
    wb.close()

    apply_layout_rules(output_path)
    fix_inlinestr(str(output_path))
    return str(Path(output_path).resolve())
