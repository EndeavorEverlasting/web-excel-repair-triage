"""Forensic compare helper for One Marcus workbook incidents."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from triage.artifact_compare import compare_artifacts
from triage.artifact_fingerprint import fingerprint_file
from triage.diff import diff_packages


def build_incident_report(
    *,
    working: str,
    cursor_broke: Optional[str] = None,
    excel_repaired: Optional[str] = None,
    profile: str = "one_marcus_recon",
) -> Dict:
    """Fingerprint and compare operator incident workbooks."""
    report: Dict = {
        "working": _file_summary(working),
        "comparisons": [],
        "zip_diffs": [],
    }
    for label, path in (
        ("cursor_broke", cursor_broke),
        ("excel_repaired", excel_repaired),
    ):
        if not path or not Path(path).is_file():
            continue
        report[label] = _file_summary(path)
        report["comparisons"].append(
            {
                "label": f"working_vs_{label}",
                "compare": compare_artifacts(working, path, profile),
            }
        )
        diff = diff_packages(working, path)
        report["zip_diffs"].append(
            {
                "label": f"working_vs_{label}",
                **diff.to_dict(),
            }
        )
    return report


def _file_summary(path: str) -> Dict:
    fp = fingerprint_file(path)
    return {
        "path": str(Path(path).resolve()),
        "size_bytes": Path(path).stat().st_size,
        "raw_sha256": fp.raw_sha256,
        "canonical_package_sha256": fp.canonical_package_sha256,
        "semantic_sha256": fp.semantic_sha256,
        "sheet_order": fp.sheet_order,
        "sheets": fp.sheets,
        "table_count": fp.table_count,
        "chart_count": fp.chart_count,
    }


def write_incident_report(out_dir: str, report: Dict) -> Dict[str, str]:
    """Write JSON + markdown carryover for an incident folder."""
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "incident_compare.json"
    md_path = root / "incident_carryover.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_markdown_carryover(report), encoding="utf-8")
    return {"json": str(json_path.resolve()), "markdown": str(md_path.resolve())}


def _markdown_carryover(report: Dict) -> str:
    lines = [
        "# One Marcus incident compare",
        "",
        "## Working baseline",
        "",
    ]
    w = report.get("working") or {}
    lines.append(f"- Path: `{w.get('path', '')}`")
    lines.append(f"- Size: {w.get('size_bytes', 0)} bytes")
    lines.append(f"- Sheets ({len(w.get('sheet_order') or [])}): {', '.join(w.get('sheet_order') or [])}")
    lines.append(f"- Semantic SHA: `{w.get('semantic_sha256', '')}`")
    lines.append("")
    for comp in report.get("comparisons") or []:
        label = comp.get("label", "")
        c = comp.get("compare") or {}
        lines.extend(
            [
                f"## {label}",
                "",
                f"- compare_pass: **{c.get('compare_pass')}**",
                f"- semantic_sha_match: {c.get('semantic_sha_match')}",
                f"- profile_failures: {c.get('profile_failures')}",
                "",
            ]
        )
        ref = (c.get("fingerprints") or {}).get("reference", {}).get("sheets") or {}
        cand = (c.get("fingerprints") or {}).get("candidate", {}).get("sheets") or {}
        for name in sorted(set(ref) | set(cand)):
            if name not in cand:
                lines.append(f"- sheet deleted: **{name}** (baseline cells: {ref.get(name, {}).get('cell_count')})")
            elif ref.get(name, {}).get("cell_value_hash") != cand.get(name, {}).get("cell_value_hash"):
                lines.append(
                    f"- sheet delta: **{name}** "
                    f"({ref.get(name, {}).get('cell_count')} -> {cand.get(name, {}).get('cell_count')} cells)"
                )
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Forensic compare for One Marcus workbook incident.")
    ap.add_argument("--working", required=True, help="Restored working baseline workbook.")
    ap.add_argument("--cursor-broke", help="Broken generator output.")
    ap.add_argument("--excel-repaired", help="Excel-repaired broken output.")
    ap.add_argument(
        "--out-dir",
        default="Outputs/one_marcus_recon/incident_2026-06-04",
        help="Output folder for incident_compare.json and carryover.",
    )
    args = ap.parse_args(argv)
    report = build_incident_report(
        working=args.working,
        cursor_broke=args.cursor_broke,
        excel_repaired=args.excel_repaired,
    )
    paths = write_incident_report(args.out_dir, report)
    print(json.dumps({"written": paths, "working_sheets": report["working"]["sheet_order"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
