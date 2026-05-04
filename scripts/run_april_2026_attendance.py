"""
scripts/run_april_2026_attendance.py
-------------------------------------
Sample run: parse the Active Roster Log for April 2026 and generate
a complete monthly attendance report.

Usage:
    python scripts/run_april_2026_attendance.py

Output:
    billing_runs/2026-04/attendance/attendance_week_2026-04-01.xlsx
    billing_runs/2026-04/run_manifest.json
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from triage.roster_parser import parse_roster, RosterParseError
from triage.attendance_report import generate_attendance_report


def _fmt(decimal_hours: float) -> str:
    """Format decimal hours as HH:MM (e.g. 23.75 → '23:45')."""
    hh = int(decimal_hours)
    mm = int(round((decimal_hours - hh) * 60))
    return f"{hh:02d}:{mm:02d}"

ROSTER_FILE = ROOT / "attached_assets" / (
    "Active_Roster_Log_5_1_2026_Billing_April_Pack_(1)_1777807743057.xlsx"
)

TARGET_MONTH  = "April 2026"
REPORT_START  = date(2026, 4, 1)
REPORT_END    = date(2026, 4, 30)


def main() -> None:
    print(f"Parsing roster: {ROSTER_FILE.name}")

    malformed: list[str] = []
    overnight: list[dict] = []
    try:
        records = parse_roster(
            str(ROSTER_FILE),
            target_month=TARGET_MONTH,
            malformed_out=malformed,
            overnight_out=overnight,
        )
    except RosterParseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Records parsed : {len(records)}")
    print(f"Staff found    : {len({r['staff'] for r in records})}")
    print(f"Projects       : {sorted({r['project'] for r in records if r['project']})}")

    if malformed:
        print(f"\nWarnings ({len(malformed)} malformed rows skipped):")
        for w in malformed:
            print(f"  - {w}")
    else:
        print("No malformed rows.")

    if overnight:
        print(f"\nOvernight shifts detected ({len(overnight)} record(s) — review recommended):")
        for ov in overnight:
            ci_s = _fmt(ov["clock_in"])
            co_s = _fmt(ov["clock_out"])
            print(
                f"  - {ov['staff']:<32} {ov['date'].isoformat()}  "
                f"in {ci_s} → out {co_s}  "
                f"gross {ov['gross_hours']:.2f}h  net {ov['net_hours']:.2f}h"
            )
    else:
        print("No overnight shifts detected.")

    long_shifts = [r for r in records if r.get("long_shift")]
    if long_shifts:
        print(f"\nLong shifts — possible data errors ({len(long_shifts)} record(s)):")
        for rec in long_shifts:
            ci_s = _fmt(rec["clock_in"])
            co_s = _fmt(rec["clock_out"])
            overnight_tag = " overnight" if rec["clock_out"] < rec["clock_in"] else ""
            print(
                f"  - {rec['staff']:<32} {rec['date'].isoformat()}  "
                f"in {ci_s} → out {co_s}  "
                f"gross {rec['gross_hours']:.2f}h  net {rec['net_hours']:.2f}h"
                f"{overnight_tag}"
            )
    else:
        print("No long shifts detected.")

    print(f"\nNet hours per staff ({TARGET_MONTH}):")
    from collections import defaultdict
    by_staff: dict[str, float] = defaultdict(float)
    for r in records:
        by_staff[r["staff"]] += r["net_hours"]
    for staff, hrs in sorted(by_staff.items()):
        print(f"  {staff:<32}  {hrs:>7.2f} hrs")
    print(f"  {'TOTAL':<32}  {sum(by_staff.values()):>7.2f} hrs")

    print(f"\nGenerating attendance report ({REPORT_START} – {REPORT_END}) …")
    out_path = generate_attendance_report(
        records=records,
        week_start=REPORT_START,
        week_end=REPORT_END,
        out_root=str(ROOT / "billing_runs"),
        run_id=f"april-2026-full-month",
        input_paths=[str(ROSTER_FILE)],
    )
    print(f"Report written : {out_path}")


if __name__ == "__main__":
    main()
