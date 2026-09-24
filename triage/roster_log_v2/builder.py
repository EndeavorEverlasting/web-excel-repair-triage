"""Generate the Roster Log V2 workbook from normalized JSON state."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict

from triage.xlsx_utils import fix_inlinestr

from .preflight import preflight_roster_v2
from .report import report_snapshot
from .schema import ALLOCATION_BASES, normalize_state, reconcile_state


def _iso_date(value: str):
    return date.fromisoformat(value)


def build_roster_workbook(
    payload: Dict[str, Any],
    output_path: str | Path,
    *,
    require_reconciled: bool = False,
) -> Dict[str, Any]:
    """Build a protected derived snapshot without mutating any predecessor.

    The website/JSON state is the editable authority. Attendance owns paid time;
    ``default_project`` is only fallback metadata; normalized Project Allocations
    are the actual project ledger and sole source for deterministic reporting.
    Change state in the website/JSON and regenerate instead of hand-editing XLSX.
    """
    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    state = normalize_state(payload)
    reconciliation = reconcile_state(state)
    report = report_snapshot(state)
    if require_reconciled:
        bad = [row for row in reconciliation if not row.reconciled]
        if bad:
            raise ValueError("require_reconciled requested with unresolved allocation variance")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.remove(wb.active)

    header_fill = PatternFill("solid", fgColor="163A5F")
    accent_fill = PatternFill("solid", fgColor="DDEBF7")
    ok_fill = PatternFill("solid", fgColor="E2F0D9")
    warn_fill = PatternFill("solid", fgColor="FFF2CC")
    bad_fill = PatternFill("solid", fgColor="FCE4D6")
    header_font = Font(bold=True, color="FFFFFF")
    wrap = Alignment(vertical="top", wrap_text=True)

    dashboard = wb.create_sheet("Dashboard")
    dashboard.append(["Roster Log V2", "Normalized attendance + first-class project allocation ledger"])
    dashboard.append(["State", "DERIVED SNAPSHOT — edit website/JSON and regenerate; do not hand-edit this workbook"])
    dashboard.append(["Attendance days", report["attendance_days"]])
    dashboard.append(["Paid hours", report["paid_hours"]])
    dashboard.append(["Allocation rows", report["allocation_rows"]])
    dashboard.append(["Allocated hours", report["allocated_hours"]])
    dashboard.append(["Allocation variance", report["variance"]])
    dashboard.append(["Multi-project days", report["multi_project_days"]])
    dashboard.append(["Days requiring allocation repair", report["unreconciled_days"]])
    dashboard.append(["Rule", "Default / fallback project is used only when a paid day has no explicit project allocations."])
    dashboard.append(["Rule", "Once explicit allocations exist, those rows — not the attendance default — define actual project membership."])
    dashboard.append(["Rule", "Multi-project days are normal; only unreconciled allocation arithmetic is a review condition."])
    dashboard.column_dimensions["A"].width = 34
    dashboard.column_dimensions["B"].width = 100
    dashboard.freeze_panes = "A2"
    for cell in dashboard[1]:
        cell.fill = header_fill
        cell.font = header_font

    attendance = wb.create_sheet("Attendance")
    attendance_headers = [
        "Date",
        "Staff",
        "Clock In",
        "Clock Out",
        "Paid Hours",
        "Default / Fallback Project",
        "Project Mode",
        "Allocated Hours",
        "Variance",
        "Reconciled?",
        "Notes",
    ]
    attendance.append(attendance_headers)
    for raw in state["attendance"]:
        attendance.append(
            [
                _iso_date(raw["date"]),
                raw["staff"],
                raw.get("clock_in", ""),
                raw.get("clock_out", ""),
                raw["paid_hours"],
                raw["default_project"],
                None,
                None,
                None,
                None,
                raw.get("notes", ""),
            ]
        )

    allocations = wb.create_sheet("Project Allocations")
    allocation_headers = [
        "Allocation ID",
        "Date",
        "Staff",
        "Project / Billing Scope",
        "Allocation Basis",
        "Workstream",
        "Allocated Hours",
        "Status",
        "Notes",
        "Distinct Project First?",
    ]
    allocations.append(allocation_headers)
    for raw in state["allocations"]:
        allocations.append(
            [
                raw["allocation_id"],
                _iso_date(raw["date"]),
                raw["staff"],
                raw["project"],
                raw["basis"],
                raw.get("workstream", ""),
                raw["hours"],
                raw.get("status", "RECONCILED"),
                raw.get("notes", ""),
                None,
            ]
        )

    # Hidden helper: mark only the first date+staff+project occurrence so two
    # workstream rows for one project do not become a false MULTI day.
    for row in range(2, allocations.max_row + 1):
        allocations.cell(row, 10).value = (
            f'=IF(OR(B{row}="",C{row}="",D{row}=""),0,'
            f'IF(COUNTIFS($B$2:B{row},B{row},$C$2:C{row},C{row},$D$2:D{row},D{row})=1,1,0))'
        )
    allocations.column_dimensions["J"].hidden = True

    # The XLSX is a generated snapshot, so these bounded formulas only need to
    # cover the state that produced this artifact. New state is entered in the
    # website/JSON and regenerated; the workbook is protected below.
    alloc_last_row = max(len(state["allocations"]) + 1, 2)
    for row in range(2, max(attendance.max_row, 201) + 1):
        attendance.cell(row, 7).value = (
            f'=IF(OR(A{row}="",B{row}=""),"",IF('
            f'SUMIFS(\'Project Allocations\'!$J$2:$J${alloc_last_row},'
            f'\'Project Allocations\'!$B$2:$B${alloc_last_row},A{row},'
            f'\'Project Allocations\'!$C$2:$C${alloc_last_row},B{row})>1,"MULTI","SINGLE"))'
        )
        attendance.cell(row, 8).value = (
            f'=SUMIFS(\'Project Allocations\'!$G$2:$G${alloc_last_row},'
            f'\'Project Allocations\'!$B$2:$B${alloc_last_row},A{row},'
            f'\'Project Allocations\'!$C$2:$C${alloc_last_row},B{row})'
        )
        attendance.cell(row, 9).value = f'=IF(OR(A{row}="",B{row}=""),"",E{row}-H{row})'
        attendance.cell(row, 10).value = f'=IF(I{row}="","",IF(ABS(I{row})<=0.01,"YES","NO"))'
    attendance.freeze_panes = "A2"
    attendance.auto_filter.ref = f"A1:K{max(attendance.max_row, 2)}"
    for column, width in {
        "A": 13, "B": 24, "C": 11, "D": 11, "E": 12, "F": 38,
        "G": 14, "H": 15, "I": 12, "J": 13, "K": 42,
    }.items():
        attendance.column_dimensions[column].width = width
    for row in attendance.iter_rows(min_row=2, max_row=attendance.max_row, min_col=1, max_col=1):
        row[0].number_format = "yyyy-mm-dd"

    allocations.freeze_panes = "A2"
    allocations.auto_filter.ref = f"A1:I{max(allocations.max_row, 2)}"
    widths = [24, 13, 24, 40, 18, 36, 15, 18, 48]
    for idx, width in enumerate(widths, 1):
        allocations.column_dimensions[chr(64 + idx)].width = width
    for row in allocations.iter_rows(min_row=2, max_row=allocations.max_row, min_col=2, max_col=2):
        row[0].number_format = "yyyy-mm-dd"

    project_report = wb.create_sheet("Project Report")
    project_report.append(["Project", "Allocated Hours", "Days", "Staff", "Allocation Rows"])
    for row in report["projects"]:
        project_report.append([
            row["project"],
            row["allocated_hours"],
            row["day_count"],
            row["staff_count"],
            row["allocation_count"],
        ])
    project_report.append(["TOTAL", report["allocated_hours"], None, None, report["allocation_rows"]])
    project_report.freeze_panes = "A2"
    project_report.auto_filter.ref = f"A1:E{max(project_report.max_row - 1, 2)}"
    for column, width in {"A": 44, "B": 18, "C": 12, "D": 12, "E": 18}.items():
        project_report.column_dimensions[column].width = width

    dictionaries = wb.create_sheet("Dictionaries")
    dictionaries.append(["Projects", "Workstreams", "Allocation Status", "Allocation Basis"])
    projects = list(dict.fromkeys(
        [str(x) for x in state.get("projects", []) if str(x).strip()]
        + [r["default_project"] for r in state["attendance"] if r["default_project"]]
        + [r["project"] for r in state["allocations"]]
    ))
    workstreams = list(dict.fromkeys(
        [str(x) for x in state.get("workstreams", []) if str(x).strip()]
        + [str(r.get("workstream") or "") for r in state["allocations"] if str(r.get("workstream") or "").strip()]
    ))
    statuses = ["RECONCILED", "DRAFT", "PENDING CLOSE"]
    bases = list(ALLOCATION_BASES)
    for idx in range(max(len(projects), len(workstreams), len(statuses), len(bases), 1)):
        dictionaries.append([
            projects[idx] if idx < len(projects) else None,
            workstreams[idx] if idx < len(workstreams) else None,
            statuses[idx] if idx < len(statuses) else None,
            bases[idx] if idx < len(bases) else None,
        ])
    dictionaries.freeze_panes = "A2"
    dictionaries.column_dimensions["A"].width = 44
    dictionaries.column_dimensions["B"].width = 40
    dictionaries.column_dimensions["C"].width = 20
    dictionaries.column_dimensions["D"].width = 20

    # Retain range-backed validation metadata as documentation for consumers of
    # the generated artifact even though the snapshot sheets are protected.
    if projects:
        default_dv = DataValidation(type="list", formula1=f"=Dictionaries!$A$2:$A${len(projects)+1}", allow_blank=True)
        alloc_project_dv = DataValidation(type="list", formula1=f"=Dictionaries!$A$2:$A${len(projects)+1}", allow_blank=False)
        attendance.add_data_validation(default_dv)
        allocations.add_data_validation(alloc_project_dv)
        default_dv.add("F2:F1000")
        alloc_project_dv.add("D2:D2000")
    basis_dv = DataValidation(type="list", formula1=f"=Dictionaries!$D$2:$D${len(bases)+1}", allow_blank=False)
    allocations.add_data_validation(basis_dv)
    basis_dv.add("E2:E2000")
    if workstreams:
        workstream_dv = DataValidation(type="list", formula1=f"=Dictionaries!$B$2:$B${len(workstreams)+1}", allow_blank=True)
        allocations.add_data_validation(workstream_dv)
        workstream_dv.add("F2:F2000")
    status_dv = DataValidation(type="list", formula1="=Dictionaries!$C$2:$C$4", allow_blank=False)
    allocations.add_data_validation(status_dv)
    status_dv.add("H2:H2000")

    review = wb.create_sheet("Review Queue")
    review.append(["Date", "Staff", "Rule", "Paid Hours", "Allocated Hours", "Variance", "Action"])
    for rec in reconciliation:
        if rec.reconciled:
            continue
        review.append([
            _iso_date(rec.work_date),
            rec.staff,
            "ALLOCATION_VARIANCE",
            rec.paid_hours,
            rec.allocated_hours,
            rec.variance,
            "Adjust project allocation rows in the website/JSON, then regenerate this snapshot.",
        ])
    review.freeze_panes = "A2"
    for column, width in {"A": 13, "B": 24, "C": 24, "D": 14, "E": 16, "F": 12, "G": 76}.items():
        review.column_dimensions[column].width = width

    readme = wb.create_sheet("Read Me")
    readme_rows = [
        ["Roster Log V2 operating contract"],
        ["This XLSX is a protected DERIVED SNAPSHOT. The website/JSON state is the editable authority; make changes there and regenerate rather than hand-editing this workbook."],
        ["Default / Fallback Project is attendance metadata. It creates a DEFAULT allocation only when a paid day has no explicit allocation rows."],
        ["Once explicit Project Allocations exist, those rows define actual project membership. The attendance default must not be reported as additional project work."],
        ["Allocation Basis is explicit: DEFAULT = fallback-created; EXPLICIT = intentionally entered allocation; OVERRIDE = intentional correction of a default or prior classification."],
        ["Multi-project days are supported. Add one Project Allocations row per project/workstream that should receive part of the attendance day in the website/JSON state."],
        ["A multi-project day is not an error. The review condition is arithmetic: allocated hours must reconcile to paid attendance."],
        ["Project Mode counts distinct projects, not allocation-row count; two workstream rows for one project remain SINGLE."],
        ["The Project Report is a deterministic build-time projection of the same normalized Project Allocations. Regeneration is the update mechanism."],
        ["Attendance owns paid hours. Project Allocations explain where those hours belong; allocation rows cannot create additional paid hours."],
        ["This system does not manufacture an 80/20 split or second-guess a deliberate full-day project decision."],
        ["The prior roster remains untouched. Promote V2 to CURRENT only after the operator confirms the website workflow is functional."],
    ]
    for row in readme_rows:
        readme.append(row)
    readme.column_dimensions["A"].width = 124
    readme.freeze_panes = "A2"

    for ws in (attendance, allocations, project_report, dictionaries, review):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = wrap
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = wrap

    attendance.conditional_formatting.add("J2:J1000", FormulaRule(formula=['$J2="YES"'], fill=ok_fill))
    attendance.conditional_formatting.add("J2:J1000", FormulaRule(formula=['$J2="NO"'], fill=bad_fill))
    attendance.conditional_formatting.add("G2:G1000", FormulaRule(formula=['$G2="MULTI"'], fill=accent_fill))
    review.conditional_formatting.add("A2:G1000", FormulaRule(formula=['$C2="ALLOCATION_VARIANCE"'], fill=warn_fill))

    # Prevent the generated workbook from becoming a second mutable authority.
    # No password is used: protection is an explicit UX/ownership guardrail, not
    # a security control. Regeneration from canonical JSON is the mutation path.
    for ws in wb.worksheets:
        ws.protection.sheet = True

    wb.save(out)
    wb.close()

    fix_inlinestr(str(out))
    preflight = preflight_roster_v2(out)
    if not preflight["preflight_pass"]:
        raise ValueError(f"Roster Log V2 preflight failed: {preflight['errors']}")

    return {
        "path": str(out),
        "schema_version": state["schema_version"],
        "report_version": report["report_version"],
        "workbook_authority": "DERIVED / PUBLISH-ONLY",
        "attendance_days": report["attendance_days"],
        "allocation_rows": report["allocation_rows"],
        "paid_hours": report["paid_hours"],
        "allocated_hours": report["allocated_hours"],
        "multi_project_days": report["multi_project_days"],
        "project_count": len(report["projects"]),
        "project_report": report["projects"],
        "reconciled_days": sum(1 for row in reconciliation if row.reconciled),
        "unreconciled_days": report["unreconciled_days"],
        "preflight": preflight,
    }
