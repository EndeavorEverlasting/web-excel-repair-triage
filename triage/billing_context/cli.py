from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .exporters import (
    export_mismatches,
    export_monthly_summary,
    export_neuron_project_hours,
    scan_leadership_language,
    scan_workbook_errors,
)
from .html_dashboard import export_html_dashboard
from .reconcile import (
    build_task_context_index,
    extract_track_hours,
    find_all_mismatches,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate contextualized April/May billing artifacts and browser dashboard."
    )
    parser.add_argument("--track-hours", required=True)
    parser.add_argument("--april-context", required=True)
    parser.add_argument("--roster-log")
    parser.add_argument("--admin-copy")
    parser.add_argument("--dashboard")
    parser.add_argument("--out-dir", default="Outputs")
    parser.add_argument("--html", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    task_index = build_task_context_index(args.april_context)
    entries = extract_track_hours(args.track_hours, task_index)
    mismatches = find_all_mismatches(
        entries,
        roster_path=args.roster_log,
        admin_path=args.admin_copy,
        dashboard_path=args.dashboard,
    )

    outputs: dict[str, str] = {}

    xlsx_paths = [
        export_neuron_project_hours(
            entries,
            str(out_dir / "Neuron_Project_Hours_April_May_2026_CONTEXTUALIZED_WEBSAFE.xlsx"),
        ),
        export_monthly_summary(
            entries,
            4,
            str(out_dir / "April_2026_Billing_Summary_CONTEXTUALIZED_CHARTED_WEBSAFE.xlsx"),
        ),
        export_monthly_summary(
            entries,
            5,
            str(out_dir / "May_2026_Billing_Summary_CONTEXTUALIZED_CHARTED_WEBSAFE.xlsx"),
        ),
    ]

    outputs["project_hours"] = xlsx_paths[0]
    outputs["april_summary"] = xlsx_paths[1]
    outputs["may_summary"] = xlsx_paths[2]

    export_mismatches(
        mismatches,
        str(out_dir / "billing_context_mismatches.json"),
        str(out_dir / "billing_context_mismatches.csv"),
    )
    outputs["mismatches_json"] = str(out_dir / "billing_context_mismatches.json")
    outputs["mismatches_csv"] = str(out_dir / "billing_context_mismatches.csv")

    if args.html:
        outputs["html_dashboard"] = export_html_dashboard(
            entries,
            mismatches,
            str(out_dir / "billing_context_dashboard.html"),
        )

    stop_ship: list[str] = []
    for path in xlsx_paths:
        for sheet, coord, val in scan_workbook_errors(path):
            stop_ship.append(f"{Path(path).name} {sheet}!{coord}: {val}")
        for issue in scan_leadership_language(path):
            stop_ship.append(f"{Path(path).name} blocked language: {issue}")

    if stop_ship:
        print(json.dumps({"stop_ship": stop_ship}, indent=2), file=sys.stderr)
        sys.exit(1)

    print(
        json.dumps(
            {
                "outputs": outputs,
                "entry_count": len(entries),
                "total_hours": round(sum(e.hours for e in entries), 2),
                "mismatch_count": len(mismatches),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
