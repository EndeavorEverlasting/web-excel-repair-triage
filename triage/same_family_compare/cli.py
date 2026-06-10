"""CLI for same-family artifact comparison."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from triage.same_family_compare.compare import CompareError, run_same_family_compare, write_compare_outputs
from triage.same_family_compare.readiness import build_submission_readiness, write_submission_readiness
from triage.output_policy import allocate_run_dir, assert_out_dir_allowed
from triage.same_family_compare.scan import scan_intake, write_scan_outputs

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve(p: str, base: Path) -> Path:
    pp = Path(p)
    return pp if pp.is_absolute() else (base / pp).resolve()


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="triage.same_family_compare")
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--intake-root", default=None, help="ArtifactIntake/YYYY-MM-DD for scan-only")
    ap.add_argument("--scan-only", action="store_true")
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--candidate", default=None)
    ap.add_argument("--family", default=None)
    ap.add_argument("--months", nargs="*", default=None)
    ap.add_argument("--out-dir", default=None, help="Run dir under artifacts/same_family_compare/")
    ap.add_argument("--expect-neuron-tab", default=None)
    ap.add_argument("--browser-excel-status", default="UNKNOWN")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve() if args.repo_root else _REPO_ROOT
    if args.out_dir:
        out_dir = assert_out_dir_allowed(_resolve(args.out_dir, root))
    else:
        slug = "scan" if args.scan_only else "compare"
        out_dir = allocate_run_dir(
            "same_family_compare", slug, root=root, writable_root="artifacts"
        )

    if args.scan_only:
        if not args.intake_root:
            ap.error("--scan-only requires --intake-root")
        scan = scan_intake(_resolve(args.intake_root, root))
        paths = write_scan_outputs(scan, out_dir)
        print(json.dumps({"scan": scan["family_grouping"], "outputs": {k: str(v) for k, v in paths.items()}}, indent=2))
        return 0

    if not args.baseline or not args.candidate:
        ap.error("Compare mode requires --baseline and --candidate")

    try:
        result = run_same_family_compare(
            _resolve(args.baseline, root),
            _resolve(args.candidate, root),
            family=args.family,
            months=args.months,
            expect_neuron_tab=args.expect_neuron_tab,
        )
    except CompareError as exc:
        print(json.dumps({"pass": False, "error": str(exc)}, indent=2))
        return 1

    write_compare_outputs(result, out_dir)
    readiness = build_submission_readiness(
        same_family_pass=result.get("pass"),
        browser_excel_status=args.browser_excel_status,
        blockers=[] if result.get("pass") else ["same_family_compare_failed"],
    )
    write_submission_readiness(readiness, out_dir / "submission_readiness.md")
    print(json.dumps({"pass": result.get("pass"), "out_dir": str(out_dir)}, indent=2))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
