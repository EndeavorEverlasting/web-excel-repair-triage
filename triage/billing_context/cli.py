from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .exporters import (
    build_output_manifest,
    create_zip_bundle,
    export_internal_detail,
    export_mismatches,
    export_monthly_summary,
    export_neuron_project_hours,
    scan_forbidden_text,
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
    parser.add_argument("--include-tracker-import", action="store_true")
    parser.add_argument("--internal-xlsx", action="store_true")
    parser.add_argument("--zip", action="store_true", help="Bundle all outputs into a single ZIP")
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
            include_tracker_import=args.include_tracker_import,
        ),
        export_monthly_summary(
            entries,
            5,
            str(out_dir / "May_2026_Billing_Summary_CONTEXTUALIZED_CHARTED_WEBSAFE.xlsx"),
            include_tracker_import=args.include_tracker_import,
        ),
    ]

    outputs["project_hours"] = xlsx_paths[0]
    outputs["april_summary"] = xlsx_paths[1]
    outputs["may_summary"] = xlsx_paths[2]

    mismatches_json = str(out_dir / "billing_context_mismatches.json")
    mismatches_csv = str(out_dir / "billing_context_mismatches.csv")
    export_mismatches(mismatches, mismatches_json, mismatches_csv)
    outputs["mismatches_json"] = mismatches_json
    outputs["mismatches_csv"] = mismatches_csv

    if args.internal_xlsx:
        internal_path = str(out_dir / "billing_context_internal_detail.xlsx")
        outputs["internal_detail"] = export_internal_detail(entries, internal_path)

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
        for issue in scan_forbidden_text(path):
            stop_ship.append(f"{Path(path).name} forbidden text: {issue}")

    if args.zip:
        zip_path = str(out_dir / f"billing_context_artifacts_{date.today().isoformat()}.zip")
        create_zip_bundle(list(outputs.values()), zip_path)
        outputs["zip_bundle"] = zip_path

    manifest = build_output_manifest(outputs)
    missing = [m for m in manifest if not m["exists"]]
    if missing:
        stop_ship.extend(f"Missing output artifact: {m['name']} -> {m['path']}" for m in missing)

    if stop_ship:
        print(json.dumps({"stop_ship": stop_ship, "manifest": manifest}, indent=2), file=sys.stderr)
        sys.exit(1)

    print(
        json.dumps(
            {
                "outputs": outputs,
                "manifest": manifest,
                "entry_count": len(entries),
                "total_hours": round(sum(e.hours for e in entries), 2),
                "mismatch_count": len(mismatches),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
