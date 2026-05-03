"""
triage/billing_summary_generator.py
------------------------------------
Build the monthly billing summary .xlsx from roster records + parsed invoices.

Output sheets (matching Agilant Admins template):
  1. "Billing Summary - {Mon YYYY}"
       - Monthly Rollup block (side-by-side with Hours by Project)
       - Daily Billing Detail section
  2. "Invoice Pivots - Candidate"
       - Monthly Invoice Totals + Totals by Category (side by side)
       - Totals by PO Number | Totals by Project | Totals by Vendor/Crew (side by side)

Output path: billing_runs/YYYY-MM/workbook/billing_summary_{YYYY-MM}.xlsx
Also writes:  billing_runs/YYYY-MM/run_manifest.json

Raises RuntimeError (not silently falls back) if required inputs are malformed.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def generate_billing_summary(
    records: List[Dict[str, Any]],
    invoices: List[Dict[str, Any]],
    billing_month: str,
    out_root: str = "billing_runs",
    run_id: Optional[str] = None,
    input_paths: Optional[List[str]] = None,
) -> str:
    """
    Generate the monthly billing summary workbook.

    Parameters
    ----------
    records       : list of dicts from roster_parser.parse_roster()
    invoices      : list of dicts from invoice_parser.parse_invoices()
    billing_month : 'YYYY-MM', e.g. '2026-04'
    out_root      : root folder (default 'billing_runs')
    run_id        : optional run identifier
    input_paths   : list of source file paths for the manifest

    Returns
    -------
    Absolute path to the generated .xlsx file.
    Raises RuntimeError if records is empty.
    """
    if not records:
        raise RuntimeError(
            f"No roster records provided for {billing_month}. "
            "Cannot generate billing summary from empty data."
        )

    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise RuntimeError("openpyxl is required: pip install openpyxl")

    year_s, month_s = billing_month.split("-")
    month_label = date(int(year_s), int(month_s), 1).strftime("%B %Y")

    # ── Aggregate roster data ──────────────────────────────────────────────────
    gross_total = sum(r["gross_hours"]     for r in records)
    lunch_total = sum(r["lunch_deduction"] for r in records)
    net_total   = sum(r["net_hours"]       for r in records)
    daily_rows  = len(records)

    all_staff: Set[str] = {r["staff"] for r in records}

    # Hours by project
    project_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"gross": 0.0, "lunch": 0.0, "net": 0.0,
                 "techs": set(), "daily_rows": 0}
    )
    for rec in records:
        proj = rec["project"] or "Unassigned / Review"
        project_map[proj]["gross"]      += rec["gross_hours"]
        project_map[proj]["lunch"]      += rec["lunch_deduction"]
        project_map[proj]["net"]        += rec["net_hours"]
        project_map[proj]["techs"].add(rec["staff"])
        project_map[proj]["daily_rows"] += 1

    # Sort records and projects for display
    sorted_records = sorted(records, key=lambda r: (r["date"], r["staff"]))
    sorted_projects = sorted(project_map.items())

    # ── Aggregate invoice data ─────────────────────────────────────────────────
    inv_by_month: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"trucking": 0.0, "labor": 0.0, "courier": 0.0, "other": 0.0,
                 "count": 0, "pos": set()}
    )
    po_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"trucking": 0.0, "labor": 0.0, "courier": 0.0, "other": 0.0,
                 "total": 0.0, "count": 0, "notes": ""}
    )
    project_inv_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0.0, "count": 0}
    )
    vendor_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"trucking": 0.0, "labor": 0.0, "courier": 0.0, "other": 0.0,
                 "total": 0.0, "count": 0}
    )
    category_map: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"trucking": 0.0, "labor": 0.0, "courier": 0.0, "other": 0.0,
                 "count": 0, "total": 0.0}
    )

    # Category → descriptive project bucket (matches roster project buckets)
    _CATEGORY_TO_PROJECT = {
        "trucking": "Delivery / Transport / Disposal",
        "courier":  "Delivery / Transport / Disposal",
        "labor":    "Neuron Deployments",
        "other":    "Unassigned / Review",
    }

    for inv in invoices:
        inv_total_amt = float(inv.get("total") or 0)
        po     = inv.get("po_number") or "Unknown"
        vendor = inv["vendor"]

        # Service month: parse from service_date/service_window if present.
        # service_window may be a date range like "Feb 7 - 8, 2026" or
        # "Feb 14 - 15, 2026"; extract the FIRST date token to determine month.
        svc = inv.get("service_date") or inv.get("service_window") or ""
        inv_month = billing_month  # default fallback
        if svc:
            import re as _re
            # Normalise: take the portion before any " - " range separator,
            # then strip trailing whitespace/punctuation.
            svc_first = _re.split(r"\s*[-–—]\s*\d", svc.strip())[0].strip()
            # If the first token already has a 4-digit year, use it directly.
            # Otherwise, we need to append the year from the end of the original string.
            if not _re.search(r"\b\d{4}\b", svc_first):
                year_m = _re.search(r"\b(\d{4})\b", svc)
                if year_m:
                    svc_first = svc_first.rstrip(",. ") + ", " + year_m.group(1)
            for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d", "%m/%d/%Y",
                        "%b %d %Y", "%B %d %Y"):
                try:
                    parsed_date = datetime.strptime(svc_first.strip(), fmt)
                    inv_month = parsed_date.strftime("%Y-%m")
                    break
                except ValueError:
                    continue

        inv_by_month[inv_month]["count"] += 1
        inv_by_month[inv_month]["pos"].add(po)
        po_map[po]["count"] += 1
        vendor_map[vendor]["count"] += 1
        category_map[vendor]["count"] += 1

        # Aggregate categories from individual line items so that invoices
        # with mixed categories (e.g. trucking + labor on same invoice) are
        # split correctly across trucking/labor/courier/other columns.
        line_items = inv.get("line_items") or []
        if line_items:
            li_sum: Dict[str, float] = {"trucking": 0.0, "labor": 0.0,
                                         "courier": 0.0, "other": 0.0}
            for item in line_items:
                item_cat = item.get("category") or "other"
                if item_cat not in li_sum:
                    item_cat = "other"
                li_sum[item_cat] += float(item.get("amount") or 0)

            # Scale line-item totals to match the invoice total (preserves
            # accuracy when line-item sum ≠ invoice total due to rounding/taxes).
            li_raw_sum = sum(li_sum.values())
            if li_raw_sum > 0 and abs(li_raw_sum - inv_total_amt) / li_raw_sum > 0.001:
                scale = inv_total_amt / li_raw_sum
                li_sum = {k: v * scale for k, v in li_sum.items()}
        else:
            # Fallback: entire invoice goes to invoice-level category
            fallback_cat = inv.get("cost_category") or "other"
            li_sum = {"trucking": 0.0, "labor": 0.0, "courier": 0.0, "other": 0.0}
            li_sum[fallback_cat if fallback_cat in li_sum else "other"] = inv_total_amt

        for cat, amt in li_sum.items():
            if amt == 0:
                continue
            inv_by_month[inv_month][cat] += amt
            po_map[po][cat]              += amt
            vendor_map[vendor][cat]      += amt
            category_map[vendor][cat]    += amt

        po_map[po]["total"]              += inv_total_amt
        vendor_map[vendor]["total"]      += inv_total_amt
        category_map[vendor]["total"]    += inv_total_amt

        # Populate project_inv_map: dominant category of this invoice
        # determines the project bucket (by largest category amount).
        dom_cat = max(li_sum, key=li_sum.get) if any(li_sum.values()) else "other"
        proj_bucket = _CATEGORY_TO_PROJECT.get(dom_cat, "Unassigned / Review")
        project_inv_map[proj_bucket]["total"] += inv_total_amt
        project_inv_map[proj_bucket]["count"] += 1

    inv_total = sum(
        d.get("trucking", 0) + d.get("labor", 0) + d.get("courier", 0) + d.get("other", 0)
        for d in inv_by_month.values()
    )

    # ── Build workbook ─────────────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    ws1 = wb.create_sheet(f"Billing Summary - {month_label}")
    ws2 = wb.create_sheet("Invoice Pivots - Candidate")

    # ── Style helpers ─────────────────────────────────────────────────────────
    C_DARK   = "0E4C2F"
    C_MED    = "1A5C38"
    C_SUB    = "0D3320"
    C_ALT    = "0A1A10"
    C_TOTAL  = "0A3020"
    C_WHITE  = "FFFFFF"
    C_YELLOW = "FFC107"

    def _fill(hex_color: str) -> PatternFill:
        return PatternFill("solid", fgColor=hex_color)

    def _font(bold=False, size=10, color=C_WHITE) -> Font:
        return Font(bold=bold, size=size, color=color)

    def _align(h="left", v="center", wrap=False) -> Alignment:
        return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

    def cell(ws, row, col, value=None, bold=False, size=10, color=C_WHITE,
             fill=None, h="left", v="center", wrap=False, fmt=None):
        c = ws.cell(row=row, column=col, value=value)
        c.font      = Font(bold=bold, size=size, color=color)
        c.alignment = Alignment(horizontal=h, vertical=v, wrap_text=wrap)
        if fill:
            c.fill = _fill(fill)
        if fmt:
            c.number_format = fmt
        return c

    def hdr(ws, row, col, value, span=1, fill=C_MED, bold=True, h="center"):
        if span > 1:
            ws.merge_cells(start_row=row, start_column=col,
                           end_row=row, end_column=col + span - 1)
        return cell(ws, row, col, value, bold=bold, fill=fill, h=h)

    # ════════════════════════════════════════════════════════════════════════════
    # SHEET 1: Billing Summary
    # ════════════════════════════════════════════════════════════════════════════

    # Row 1: Title
    ws1.merge_cells("A1:J1")
    cell(ws1, 1, 1, f"{month_label} Billing Summary - Candidate", bold=True, size=13,
         fill=C_DARK, h="center")
    ws1.row_dimensions[1].height = 22

    # Row 2: Subtitle
    ws1.merge_cells("A2:J2")
    cell(ws1, 2, 1,
         "Separating Logistics from Device Integration; Including Lunch Deductions",
         size=9, fill=C_SUB, h="left")
    ws1.row_dimensions[2].height = 14

    # Row 4: Section headers (side by side)
    hdr(ws1, 4, 1, "Monthly Rollup",   span=4, fill=C_MED)
    hdr(ws1, 4, 6, "Hours by Project", span=6, fill=C_MED)
    ws1.row_dimensions[4].height = 18

    # Row 5: Column headers
    for ci, h_val in enumerate(["Metric", "Value", "Basis", "Notes"], 1):
        hdr(ws1, 5, ci, h_val, fill=C_SUB)
    for ci, h_val in enumerate(
        ["Project", "Tech Count", "Daily Rows", "Gross Hours", "Lunch Deducted", "Net Billable Hours"],
        6
    ):
        hdr(ws1, 5, ci, h_val, fill=C_SUB, h="center")
    ws1.row_dimensions[5].height = 16

    # Rows 6-10: Rollup data (left) + project data (right, up to 5 rows)
    rollup_data = [
        ("Gross hours",          round(gross_total, 2), "Live " + month_label,
         "Before lunch deduction"),
        ("Lunch deducted",       round(lunch_total, 2), "Policy rule",
         "0 under 6h; 0.5 from 6 to <8h; 1.0 at 8h+"),
        ("Net billable hours",   round(net_total,   2), "Gross - lunch",
         "Use this for billing unless company policy says otherwise"),
        (f"Techs with {month_label} hours",
         len(all_staff), "Live " + month_label, ""),
        ("Daily work rows",      daily_rows,            "Live " + month_label, ""),
    ]

    # Build the project display list: real projects + TOTAL sentinel.
    # Up to 4 real projects fit in rows 6-9; TOTAL lands at row 10 (right side)
    # to match the Agilant template layout exactly.
    # If there are more than 4 real projects the extras overflow to extra_row.
    total_sentinel = {
        "gross":     gross_total,
        "lunch":     lunch_total,
        "net":       net_total,
        "techs":     all_staff,
        "daily_rows": daily_rows,
        "_is_total": True,
    }
    proj_rows = list(sorted_projects)           # real projects

    # Build a 5-slot display list so TOTAL always lands at row 10 (ri=4).
    # Slots 0-3 hold real projects; slot 4 is always TOTAL.
    real_slots: list = (proj_rows[:4] + [None, None, None, None])[:4]
    proj_display = real_slots + [("TOTAL", total_sentinel)]

    for i in range(6, 11):
        ri = i - 6
        alt = C_ALT if i % 2 == 0 else None

        # Left: rollup
        metric, value, basis, notes = rollup_data[ri]
        cell(ws1, i, 1, metric, fill=alt or "", h="left")
        cell(ws1, i, 2, value,  fill=alt or "", h="right", bold=True)
        cell(ws1, i, 3, basis,  fill=alt or "", h="left")
        cell(ws1, i, 4, notes,  fill=alt or "", h="left", size=9)

        # Right: project slot (may be None = empty, or a (name, pdata) tuple)
        entry = proj_display[ri]
        if entry is not None:
            proj, pdata = entry
            is_total = pdata.get("_is_total", False)
            proj_fill = C_TOTAL if is_total else (alt or "")
            cell(ws1, i, 6,  proj,                       fill=proj_fill, h="left",   bold=is_total)
            cell(ws1, i, 7,  len(pdata["techs"]),        fill=proj_fill, h="center", bold=is_total)
            cell(ws1, i, 8,  pdata["daily_rows"],        fill=proj_fill, h="center", bold=is_total)
            cell(ws1, i, 9,  round(pdata["gross"], 2),   fill=proj_fill, h="right",  bold=is_total)
            cell(ws1, i, 10, round(pdata["lunch"], 2),   fill=proj_fill, h="right",  bold=is_total)
            cell(ws1, i, 11, round(pdata["net"],   2),   fill=proj_fill, h="right",  bold=is_total)
        ws1.row_dimensions[i].height = 15

    # Overflow: any real projects beyond slot 4 go at extra_row (≥11)
    extra_row = 11
    if len(proj_rows) > 4:
        for proj, pdata in proj_rows[4:]:
            cell(ws1, extra_row, 6,  proj,                  h="left")
            cell(ws1, extra_row, 7,  len(pdata["techs"]),   h="center")
            cell(ws1, extra_row, 8,  pdata["daily_rows"],   h="center")
            cell(ws1, extra_row, 9,  round(pdata["gross"],2), h="right")
            cell(ws1, extra_row, 10, round(pdata["lunch"],2), h="right")
            cell(ws1, extra_row, 11, round(pdata["net"],  2), h="right", bold=True)
            extra_row += 1
        # TOTAL after overflow
        cell(ws1, extra_row, 6,  "TOTAL",              bold=True, fill=C_TOTAL)
        cell(ws1, extra_row, 7,  len(all_staff),        bold=True, fill=C_TOTAL, h="center")
        cell(ws1, extra_row, 8,  daily_rows,            bold=True, fill=C_TOTAL, h="center")
        cell(ws1, extra_row, 9,  round(gross_total,2),  bold=True, fill=C_TOTAL, h="right")
        cell(ws1, extra_row, 10, round(lunch_total,2),  bold=True, fill=C_TOTAL, h="right")
        cell(ws1, extra_row, 11, round(net_total, 2),   bold=True, fill=C_TOTAL, h="right")
        extra_row += 1

    # ── Val Weekly Hours | Val Daily Detail (side by side) ─────────────────────
    val_start = max(11, extra_row)

    # Compute weekly buckets from records
    from collections import defaultdict as _dd
    import datetime as _dt
    weekly: dict = _dd(lambda: {"gross": 0.0, "lunch": 0.0, "net": 0.0,
                                 "projects": set(), "days": set()})
    for rec in sorted_records:
        d = rec["date"]
        mon = d - _dt.timedelta(days=d.weekday())
        fri = mon + _dt.timedelta(days=4)
        wk = mon
        label = f"{mon.strftime('%b %-d')}–{fri.strftime('%-d')}"
        weekly[wk]["label"] = label
        weekly[wk]["gross"] += rec["gross_hours"]
        weekly[wk]["lunch"] += rec["lunch_deduction"]
        weekly[wk]["net"]   += rec["net_hours"]
        weekly[wk]["projects"].add(rec["project"] or "Unassigned")
        weekly[wk]["days"].add(d)

    hdr(ws1, val_start, 1, "Val Weekly Hours", span=8, fill=C_MED)
    hdr(ws1, val_start, 9, "Val Daily Detail", span=7, fill=C_MED)
    ws1.row_dimensions[val_start].height = 18

    val_hdr = val_start + 1
    for ci, h_val in enumerate(
        ["Week", "Date Range", "Projects", "Days Worked",
         "Gross Hours", "Lunch Deducted", "Net Billable Hours"],
        1
    ):
        hdr(ws1, val_hdr, ci, h_val, fill=C_SUB, h="center")
    for ci, h_val in enumerate(
        ["Date", "Project", "Clock In", "Clock Out",
         "Gross Hours", "Lunch Deducted", "Net Billable Hours"],
        9
    ):
        hdr(ws1, val_hdr, ci, h_val, fill=C_SUB, h="center")
    ws1.row_dimensions[val_hdr].height = 15

    def _ftime(h):
        if h is None:
            return ""
        hh = int(h)
        mm = int(round((h - hh) * 60))
        return f"{hh:02d}:{mm:02d}"

    val_data = val_hdr + 1
    sorted_weekly = sorted(weekly.items())
    for wk_mon, wdata in sorted_weekly:
        alt = C_ALT if (val_data % 2 == 0) else None
        cell(ws1, val_data, 1, wk_mon.strftime("%Y-%m-%d"),        fill=alt or "")
        cell(ws1, val_data, 2, wdata.get("label", ""),              fill=alt or "")
        cell(ws1, val_data, 3, ", ".join(sorted(wdata["projects"])), fill=alt or "", size=8)
        cell(ws1, val_data, 4, len(wdata["days"]),                  fill=alt or "", h="center")
        cell(ws1, val_data, 5, round(wdata["gross"], 2),            fill=alt or "", h="right")
        cell(ws1, val_data, 6, round(wdata["lunch"], 2),            fill=alt or "", h="right")
        cell(ws1, val_data, 7, round(wdata["net"],   2),            fill=alt or "", h="right", bold=True)
        wk_recs = [r for r in sorted_records
                   if (r["date"] - _dt.timedelta(days=r["date"].weekday())) == wk_mon]
        if wk_recs:
            dr = wk_recs[0]
            cell(ws1, val_data, 9,  dr["date"].strftime("%b %d, %Y"),  fill=alt or "")
            cell(ws1, val_data, 10, dr["project"],                      fill=alt or "")
            cell(ws1, val_data, 11, _ftime(dr["clock_in"]),             fill=alt or "", h="right")
            cell(ws1, val_data, 12, _ftime(dr["clock_out"]),            fill=alt or "", h="right")
            cell(ws1, val_data, 13, round(dr["gross_hours"],     2),    fill=alt or "", h="right")
            cell(ws1, val_data, 14, round(dr["lunch_deduction"], 1),    fill=alt or "", h="right")
            cell(ws1, val_data, 15, round(dr["net_hours"],       2),    fill=alt or "", h="right", bold=True)
        ws1.row_dimensions[val_data].height = 15
        val_data += 1

    # TOTAL row for weekly validation
    cell(ws1, val_data, 1, "TOTAL", bold=True, fill=C_TOTAL)
    cell(ws1, val_data, 4, sum(len(w["days"]) for w in weekly.values()), bold=True, fill=C_TOTAL, h="center")
    cell(ws1, val_data, 5, round(gross_total, 2), bold=True, fill=C_TOTAL, h="right")
    cell(ws1, val_data, 6, round(lunch_total, 2), bold=True, fill=C_TOTAL, h="right")
    cell(ws1, val_data, 7, round(net_total,   2), bold=True, fill=C_TOTAL, h="right")
    val_data += 1

    # ── Trucking / Logistics Invoice Cost Placeholder ─────────────────────────
    trucking_invs = [inv for inv in invoices
                     if inv.get("cost_category") in ("trucking", "courier")]
    if trucking_invs:
        truck_start = val_data + 1
        hdr(ws1, truck_start, 1,
            "Trucking / Logistics Invoice Cost Placeholder", span=11, fill=C_MED)
        ws1.row_dimensions[truck_start].height = 18

        truck_hdr = truck_start + 1
        for ci, h_val in enumerate(
            ["Invoice / Cost Item", "Vendor", "Date / Range", "Project Bucket",
             "Amount ($)", "Status", "Notes"],
            1
        ):
            hdr(ws1, truck_hdr, ci, h_val, fill=C_SUB, h="center")
        ws1.row_dimensions[truck_hdr].height = 15

        truck_data = truck_hdr + 1
        for inv in trucking_invs:
            alt = C_ALT if (truck_data % 2 == 0) else None
            inv_label = (inv.get("invoice_number") or
                         f"{inv['vendor']} invoice {inv.get('service_date','')}")
            proj_bucket = ("Delivery / Transport / Disposal"
                           if inv.get("cost_category") in ("trucking","courier")
                           else "Unassigned")
            cell(ws1, truck_data, 1, inv_label,                         fill=alt or "")
            cell(ws1, truck_data, 2, inv["vendor"],                      fill=alt or "")
            cell(ws1, truck_data, 3, inv.get("service_date") or "",      fill=alt or "")
            cell(ws1, truck_data, 4, proj_bucket,                        fill=alt or "")
            cell(ws1, truck_data, 5, round(float(inv.get("total") or 0), 2),
                 fill=alt or "", h="right", bold=True)
            cell(ws1, truck_data, 6, "Completed Invoice",                fill=alt or "")
            cell(ws1, truck_data, 7, f"PO {inv.get('po_number','?')} | Net 30 | {inv.get('currency','USD')}",
                 fill=alt or "", size=9)
            ws1.row_dimensions[truck_data].height = 14
            truck_data += 1
        val_data = truck_data + 1

    # ── Daily Billing Detail ───────────────────────────────────────────────────
    detail_start = val_data + 2  # always below the val/trucking sections
    hdr(ws1, detail_start, 1, "Daily Billing Detail with Lunch Deduction",
        span=11, fill=C_MED)
    ws1.row_dimensions[detail_start].height = 18

    detail_hdr_row = detail_start + 1
    for ci, h_val in enumerate(
        ["Staff Name", "Date", "Week", "Project", "Clock In", "Clock Out",
         "Gross Hours", "Lunch Deduction", "Net Billable Hours", "Source / Rule"],
        1
    ):
        hdr(ws1, detail_hdr_row, ci, h_val, fill=C_SUB, h="center")
    ws1.row_dimensions[detail_hdr_row].height = 15

    detail_data_row = detail_hdr_row + 1
    for i, rec in enumerate(sorted_records):
        alt = C_ALT if i % 2 == 0 else None
        d = rec["date"]
        week_mon = d - _dt.timedelta(days=d.weekday())
        week_fri = week_mon + _dt.timedelta(days=4)
        week_label = f"{week_mon.strftime('%b %-d')}–{week_fri.strftime('%-d')}"

        row_vals = [
            rec["staff"],
            d.strftime("%b %d, %Y"),
            week_label,
            rec["project"],
            _ftime(rec["clock_in"]),
            _ftime(rec["clock_out"]),
            round(rec["gross_hours"],     2),
            round(rec["lunch_deduction"], 1),
            round(rec["net_hours"],       2),
            "Live " + month_label + "; lunch rule applied",
        ]
        for ci, val in enumerate(row_vals, 1):
            cell(ws1, detail_data_row, ci, val,
                 fill=alt or "", h="right" if ci >= 7 else "left",
                 bold=(ci == 9))
        ws1.row_dimensions[detail_data_row].height = 14
        detail_data_row += 1

    # TOTAL row for detail
    cell(ws1, detail_data_row, 1, "TOTAL", bold=True, fill=C_TOTAL)
    cell(ws1, detail_data_row, 7, round(gross_total, 2), bold=True, fill=C_TOTAL, h="right")
    cell(ws1, detail_data_row, 8, round(lunch_total, 2), bold=True, fill=C_TOTAL, h="right")
    cell(ws1, detail_data_row, 9, round(net_total,   2), bold=True, fill=C_TOTAL, h="right")

    # Column widths for sheet 1
    ws1.column_dimensions["A"].width = 22
    ws1.column_dimensions["B"].width = 14
    ws1.column_dimensions["C"].width = 18
    ws1.column_dimensions["D"].width = 22
    ws1.column_dimensions["E"].width = 10
    ws1.column_dimensions["F"].width = 10
    ws1.column_dimensions["G"].width = 14
    ws1.column_dimensions["H"].width = 16
    ws1.column_dimensions["I"].width = 18
    ws1.column_dimensions["J"].width = 30
    ws1.column_dimensions["K"].width = 18
    ws1.freeze_panes = "A6"

    # ════════════════════════════════════════════════════════════════════════════
    # SHEET 2: Invoice Pivots - Candidate
    # ════════════════════════════════════════════════════════════════════════════

    # Row 1: Title
    ws2.merge_cells("A1:M1")
    cell(ws2, 1, 1, "Invoice Pivot Summary - Candidate", bold=True, size=13,
         fill=C_DARK, h="center")
    ws2.row_dimensions[1].height = 22

    # Row 2: Subtitle
    ws2.merge_cells("A2:M2")
    cell(ws2, 2, 1,
         "Monthly invoice aggregation from the invoice ledger.",
         size=9, fill=C_SUB)
    ws2.row_dimensions[2].height = 14

    # Row 4: Monthly Invoice Totals (cols 1-8) + Totals by Category (cols 10-14)
    # col 9 is intentionally blank — matches Agilant template layout.
    hdr(ws2, 4, 1,  "Monthly Invoice Totals", span=8, fill=C_MED)
    hdr(ws2, 4, 10, "Totals by Category",     span=5, fill=C_MED)
    ws2.row_dimensions[4].height = 18

    # Row 5: Column headers
    for ci, h_val in enumerate(
        ["Service Month", "Invoice Count", "Trucking", "Labor", "Courier", "Other", "Total", "PO Count"],
        1
    ):
        hdr(ws2, 5, ci, h_val, fill=C_SUB, h="center")
    for ci, h_val in enumerate(
        ["Invoice Category", "Invoice Count", "Trucking", "Labor", "Total"],
        10
    ):
        hdr(ws2, 5, ci, h_val, fill=C_SUB, h="center")
    ws2.row_dimensions[5].height = 16

    # Monthly totals rows
    mit_row = 6
    grand_truck = grand_labor = grand_courier = grand_other = 0.0
    grand_count = 0
    all_po_sets: Set[str] = set()

    for inv_month, mdata in sorted(inv_by_month.items()):
        t_ = mdata["trucking"]; l_ = mdata["labor"]
        c_ = mdata["courier"];  o_ = mdata["other"]
        tot = t_ + l_ + c_ + o_
        cnt = mdata["count"]
        pos = mdata["pos"]
        grand_truck   += t_; grand_labor  += l_
        grand_courier += c_; grand_other  += o_
        grand_count   += cnt; all_po_sets |= pos
        alt = C_ALT if (mit_row % 2 == 0) else None

        try:
            month_date = datetime.strptime(inv_month, "%Y-%m")
            month_disp = month_date.strftime("%B %Y")
        except Exception:
            month_disp = inv_month

        cell(ws2, mit_row, 1, month_disp, fill=alt or "")
        cell(ws2, mit_row, 2, cnt,           fill=alt or "", h="center")
        cell(ws2, mit_row, 3, round(t_,  2), fill=alt or "", h="right")
        cell(ws2, mit_row, 4, round(l_,  2), fill=alt or "", h="right")
        cell(ws2, mit_row, 5, round(c_,  2), fill=alt or "", h="right")
        cell(ws2, mit_row, 6, round(o_,  2), fill=alt or "", h="right")
        cell(ws2, mit_row, 7, round(tot, 2), fill=alt or "", h="right", bold=True)
        cell(ws2, mit_row, 8, len(pos),       fill=alt or "", h="center")
        ws2.row_dimensions[mit_row].height = 15
        mit_row += 1

    # TOTAL row for Monthly Invoice Totals
    grand_tot = grand_truck + grand_labor + grand_courier + grand_other
    cell(ws2, mit_row, 1, "TOTAL", bold=True, fill=C_TOTAL)
    cell(ws2, mit_row, 2, grand_count,           bold=True, fill=C_TOTAL, h="center")
    cell(ws2, mit_row, 3, round(grand_truck,  2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, mit_row, 4, round(grand_labor,  2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, mit_row, 5, round(grand_courier,2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, mit_row, 6, round(grand_other,  2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, mit_row, 7, round(grand_tot,    2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, mit_row, 8, len(all_po_sets),       bold=True, fill=C_TOTAL, h="center")
    mit_row += 2

    # Vendor/Category block (right side, rows 6+) — cols 10-14 match template.
    # Template vendor section: Vendor/Crew | Invoice Count | Trucking | Labor | Total
    # col 9 is blank (gap), matching the Agilant template layout.
    cat_row = 6
    for vendor, vdata in sorted(vendor_map.items()):
        alt = C_ALT if (cat_row % 2 == 0) else None
        cell(ws2, cat_row, 10, vendor,                      fill=alt or "")
        cell(ws2, cat_row, 11, vdata["count"],               fill=alt or "", h="center")
        cell(ws2, cat_row, 12, round(vdata["trucking"], 2),  fill=alt or "", h="right")
        cell(ws2, cat_row, 13, round(vdata["labor"],    2),  fill=alt or "", h="right")
        cell(ws2, cat_row, 14, round(vdata["total"],    2),  fill=alt or "", h="right", bold=True)
        ws2.row_dimensions[cat_row].height = 15
        cat_row += 1

    # ── Three side-by-side sections: PO | Project | Vendor ───────────────────
    # Template R13: PO at col 1, Project at col 6, Vendor/Crew at col 10.
    # Cols 5 and 9 are blank gaps — matches Agilant template exactly.
    section_row = mit_row
    hdr(ws2, section_row, 1,  "Totals by PO Number",    span=4, fill=C_MED)
    hdr(ws2, section_row, 6,  "Totals by Project",      span=3, fill=C_MED)
    hdr(ws2, section_row, 10, "Totals by Vendor / Crew", span=5, fill=C_MED)
    ws2.row_dimensions[section_row].height = 18
    section_row += 1

    # Sub-headers (template R14)
    for ci, h_val in enumerate(["PO Number", "Invoice Count", "Total", "Notes"], 1):
        hdr(ws2, section_row, ci, h_val, fill=C_SUB, h="center")
    for ci, h_val in enumerate(["Project", "Invoice Count", "Total"], 6):
        hdr(ws2, section_row, ci, h_val, fill=C_SUB, h="center")
    # Template vendor sub-headers: Vendor/Crew, Invoice Count, Trucking, Labor, Total (5 cols)
    for ci, h_val in enumerate(["Vendor / Crew", "Invoice Count", "Trucking", "Labor", "Total"], 10):
        hdr(ws2, section_row, ci, h_val, fill=C_SUB, h="center")
    ws2.row_dimensions[section_row].height = 16
    section_row += 1

    po_items   = sorted(po_map.items())
    proj_inv_items = list(sorted(project_inv_map.items())) if project_inv_map else []
    vendor_items = sorted(vendor_map.items())

    max_rows = max(len(po_items), max(len(proj_inv_items), 1), len(vendor_items))
    for i in range(max_rows):
        alt = C_ALT if i % 2 == 0 else None
        r = section_row + i

        if i < len(po_items):
            po, pdata = po_items[i]
            cell(ws2, r, 1, po,                     fill=alt or "")
            cell(ws2, r, 2, pdata["count"],          fill=alt or "", h="center")
            cell(ws2, r, 3, round(pdata["total"],2), fill=alt or "", h="right", bold=True)
            cell(ws2, r, 4, "",                      fill=alt or "")

        if i < len(proj_inv_items):
            proj, pdata_proj = proj_inv_items[i]
            inv_count = pdata_proj["count"] if isinstance(pdata_proj, dict) else "-"
            proj_total = pdata_proj["total"] if isinstance(pdata_proj, dict) else pdata_proj
            cell(ws2, r, 6, proj,                    fill=alt or "")
            cell(ws2, r, 7, inv_count,               fill=alt or "", h="center")
            cell(ws2, r, 8, round(proj_total, 2),    fill=alt or "", h="right", bold=True)

        if i < len(vendor_items):
            vendor, vdata = vendor_items[i]
            cell(ws2, r, 10, vendor,                      fill=alt or "")
            cell(ws2, r, 11, vdata["count"],               fill=alt or "", h="center")
            cell(ws2, r, 12, round(vdata["trucking"], 2),  fill=alt or "", h="right")
            cell(ws2, r, 13, round(vdata["labor"],    2),  fill=alt or "", h="right")
            cell(ws2, r, 14, round(vdata["total"],    2),  fill=alt or "", h="right", bold=True)

        ws2.row_dimensions[r].height = 15

    # Grand total row for three-section block
    total_r = section_row + max_rows
    cell(ws2, total_r, 1,  "TOTAL", bold=True, fill=C_TOTAL)
    cell(ws2, total_r, 2,  sum(p["count"] for p in po_map.values()), bold=True, fill=C_TOTAL, h="center")
    cell(ws2, total_r, 3,  round(sum(p["total"] for p in po_map.values()), 2), bold=True, fill=C_TOTAL, h="right")
    cell(ws2, total_r, 10, "TOTAL", bold=True, fill=C_TOTAL)
    cell(ws2, total_r, 11, sum(v["count"] for v in vendor_map.values()), bold=True, fill=C_TOTAL, h="center")
    cell(ws2, total_r, 14, round(sum(v["total"] for v in vendor_map.values()), 2), bold=True, fill=C_TOTAL, h="right")

    # Column widths for sheet 2 (14 content columns + extra for audit notes)
    ws2.column_dimensions["A"].width = 18
    ws2.column_dimensions["B"].width = 14
    ws2.column_dimensions["C"].width = 14
    ws2.column_dimensions["D"].width = 22
    ws2.column_dimensions["E"].width = 6
    ws2.column_dimensions["F"].width = 22
    ws2.column_dimensions["G"].width = 14
    ws2.column_dimensions["H"].width = 14
    ws2.column_dimensions["I"].width = 6
    ws2.column_dimensions["J"].width = 24
    ws2.column_dimensions["K"].width = 14
    ws2.column_dimensions["L"].width = 14
    ws2.column_dimensions["M"].width = 14
    ws2.column_dimensions["N"].width = 14
    ws2.freeze_panes = "A6"

    # ── Structural assertions (fail hard if layout drifts from template) ──────
    def _assert_billing_structure(ws) -> None:
        """Raise RuntimeError if required cells deviate from the Agilant template contract.

        Rows 4-10 are fixed (they come before the project-overflow section).
        'Val Weekly Hours' / 'Val Daily Detail' can shift down when there are
        more than 4 project rows — so those are found dynamically by scanning.
        """
        errors = []
        # Fixed-position checks (rows 4-10 never shift)
        fixed_checks = {
            (4, 1): "Monthly Rollup",
            (4, 6): "Hours by Project",
            (5, 1): "Metric",
            (5, 6): "Project",
            (10, 6): "TOTAL",
        }
        for (r, c), expected in fixed_checks.items():
            actual = str(ws.cell(r, c).value or "").strip()
            if actual != expected:
                errors.append(f"R{r}C{c}: expected {expected!r}, got {actual!r}")

        # Dynamic-position checks: find 'Val Weekly Hours' by scanning col 1
        val_weekly_row = None
        for row in ws.iter_rows(min_row=11, max_row=ws.max_row, min_col=1, max_col=1):
            for c in row:
                if str(c.value or "").strip() == "Val Weekly Hours":
                    val_weekly_row = c.row
                    break
            if val_weekly_row:
                break

        if val_weekly_row is None:
            errors.append("'Val Weekly Hours' section header not found in col 1")
        else:
            # 'Val Daily Detail' must be on the same row at col 9
            val_daily = str(ws.cell(val_weekly_row, 9).value or "").strip()
            if val_daily != "Val Daily Detail":
                errors.append(
                    f"R{val_weekly_row}C9: expected 'Val Daily Detail', got {val_daily!r}"
                )

        if errors:
            raise RuntimeError(
                "Generated workbook does not match Agilant template structure:\n"
                + "\n".join(f"  {e}" for e in errors)
            )

    def _assert_pivot_structure(ws2) -> None:
        """Raise RuntimeError if Invoice Pivots sheet deviates from the Agilant template.

        Verified against:
        attached_assets/Agilant_Admins_April_2026_Billing_Summary_PO176759_Neurons_*.xlsx
        Invoice Pivots - Candidate sheet (inspected via openpyxl).

        Template column layout:
          R4  C1  = 'Monthly Invoice Totals'   (spans cols 1-8)
          R4  C10 = 'Totals by Category'        (spans cols 10-14)
          R5  C1  = 'Service Month'
          R5  C2  = 'Invoice Count'
          R5  C3  = 'Trucking'
          R5  C7  = 'Total'
          R5  C10 = 'Invoice Category'
          R5  C14 = 'Total'
        Three-section area (dynamic row, check sub-header positions relative to
        the first occurrence of 'Totals by PO Number'):
          PO section starts at col 1, Project at col 6, Vendor/Crew at col 10.
          Sub-headers: PO Number (C1), Project (C6), Vendor/Crew (C10).
        """
        errors = []

        # Row 4 fixed checks
        r4_checks = {
            (4, 1):  "Monthly Invoice Totals",
            (4, 10): "Totals by Category",
        }
        for (r, c), expected in r4_checks.items():
            actual = str(ws2.cell(r, c).value or "").strip()
            if actual != expected:
                errors.append(f"Pivot R{r}C{c}: expected {expected!r}, got {actual!r}")

        # Row 5 header checks (monthly section)
        r5_monthly = {
            (5, 1): "Service Month",
            (5, 2): "Invoice Count",
            (5, 3): "Trucking",
            (5, 7): "Total",
        }
        r5_cat = {
            (5, 10): "Invoice Category",
            (5, 14): "Total",
        }
        for checks_dict in (r5_monthly, r5_cat):
            for (r, c), expected in checks_dict.items():
                actual = str(ws2.cell(r, c).value or "").strip()
                if actual != expected:
                    errors.append(f"Pivot R{r}C{c}: expected {expected!r}, got {actual!r}")

        # Locate the "Totals by PO Number" section header (dynamic row)
        po_section_row = None
        for row in ws2.iter_rows(min_row=6, max_row=ws2.max_row):
            for cell_ in row:
                if str(cell_.value or "").strip() == "Totals by PO Number":
                    po_section_row = cell_.row
                    break
            if po_section_row:
                break

        if po_section_row is None:
            errors.append("Pivot: 'Totals by PO Number' section header not found")
        else:
            # Section header row: PO at C1, Project at C6, Vendor/Crew at C10
            section_checks = {
                (po_section_row, 1):  "Totals by PO Number",
                (po_section_row, 6):  "Totals by Project",
                (po_section_row, 10): "Totals by Vendor / Crew",
            }
            for (r, c), expected in section_checks.items():
                actual = str(ws2.cell(r, c).value or "").strip()
                if actual != expected:
                    errors.append(f"Pivot R{r}C{c}: expected {expected!r}, got {actual!r}")

            # Sub-header row (one below section header)
            sub_row = po_section_row + 1
            sub_checks = {
                (sub_row, 1):  "PO Number",
                (sub_row, 6):  "Project",
                (sub_row, 10): "Vendor / Crew",
                (sub_row, 12): "Trucking",
                (sub_row, 13): "Labor",
                (sub_row, 14): "Total",
            }
            for (r, c), expected in sub_checks.items():
                actual = str(ws2.cell(r, c).value or "").strip()
                if actual != expected:
                    errors.append(f"Pivot R{r}C{c}: expected {expected!r}, got {actual!r}")

        if errors:
            raise RuntimeError(
                "Generated Invoice Pivots sheet does not match Agilant template:\n"
                + "\n".join(f"  {e}" for e in errors)
            )

    _assert_billing_structure(ws1)
    _assert_pivot_structure(ws2)

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir  = Path(out_root) / billing_month / "workbook"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"billing_summary_{billing_month}.xlsx"
    wb.save(str(out_path))

    # ── Manifest (status: "generated" — UI updates to "pass"/"fail" after gate check) ─
    resolved_run_id = run_id or f"billing-{billing_month}-{int(time.time())}"
    _write_manifest(
        out_root      = out_root,
        billing_month = billing_month,
        run_id        = resolved_run_id,
        inputs        = input_paths or [],
        outputs       = [str(out_path)],
        status        = "generated",
        meta          = {
            "billing_month":  billing_month,
            "roster_records": len(records),
            "invoices":       len(invoices),
            "gross_hours":    round(gross_total, 2),
            "net_hours":      round(net_total,   2),
            "invoice_total":  round(inv_total,   2),
        },
    )

    return str(out_path)


def update_manifest_status(
    out_root: str,
    billing_month: str,
    status: str,
    gate_status: str = "",
    failures: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
) -> None:
    """Update an existing manifest's status after gate validation."""
    import json as _json
    manifest_path = Path(out_root) / billing_month / "run_manifest.json"
    if not manifest_path.exists():
        return
    try:
        data = _json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data["status"]             = status
    data["gate_status"]        = gate_status
    data["gate_failures"]      = failures or []
    data["gate_warnings"]      = warnings or []
    data["validated_at"]       = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path.write_text(
        _json.dumps(data, indent=2, default=str), encoding="utf-8"
    )


def _write_manifest(
    out_root: str,
    billing_month: str,
    run_id: str,
    inputs: List[str],
    outputs: List[str],
    status: str,
    meta: Dict[str, Any],
) -> None:
    run_dir = Path(out_root) / billing_month
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id":    run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status":    status,
        "inputs":    inputs,
        "outputs":   outputs,
        **meta,
    }
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8"
    )
