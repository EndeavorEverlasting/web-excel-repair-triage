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

ROSTER_FILE = ROOT / "attached_assets" / (
    "Active_Roster_Log_5_1_2026_Billing_April_Pack_(1)_1777807743057.xlsx"
)

TARGET_MONTH  = "April 2026"
REPORT_START  = date(2026, 4, 1)
REPORT_END    = date(2026, 4, 30)


def main() -> None:
    print(f"Parsing roster: {ROSTER_FILE.name}")

    malformed: list[str] = []
    try:
        records = parse_roster(
            str(ROSTER_FILE),
            target_month=TARGET_MONTH,
            malformed_out=malformed,
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
