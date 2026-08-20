#!/usr/bin/env python3
"""Validate the qualitative admin NTH profile or one generated workbook."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.nth_qualitative_admin.builder import MAIN_NS, PROFILE_PATH, THEME_PATH, load_profile, validate_spec
from triage.nth_qualitative_admin.style_template import canonical_styles_xml
from triage.nth_qualitative_admin.validator import validate_workbook

NS = {"x": MAIN_NS}


def validate_profile() -> dict:
    profile = load_profile()
    if len(profile.get("reference_fingerprints", [])) != 2:
        raise ValueError("qualitative admin profile must pin both completed-month and MTD reference fingerprints")
    styles = ET.fromstring(canonical_styles_xml())
    fonts = styles.find("x:fonts", NS)
    if fonts is None or {item.attrib["val"] for item in fonts.findall(".//x:name", NS)} != {"Carlito"}:
        raise ValueError("canonical style table must remain Carlito")
    cell_xfs = styles.find("x:cellXfs", NS)
    if cell_xfs is None or int(cell_xfs.attrib.get("count", "0")) != 140:
        raise ValueError("canonical style table must preserve 140 stable style IDs")
    if not THEME_PATH.is_file() or not THEME_PATH.read_bytes().strip():
        raise ValueError("canonical theme template is missing")
    return {
        "schema_version": "nth-qualitative-admin-profile-validation/v1",
        "status": "PASS",
        "profile": str(PROFILE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "profile_id": profile["profile_id"],
        "reference_fingerprints": len(profile["reference_fingerprints"]),
        "font_family": profile["visual_contract"]["font_family"],
        "formula_policy": profile["authority"]["workbook_formula_policy"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-only", action="store_true")
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = validate_profile()
        if not args.profile_only:
            if not args.workbook or not args.spec:
                parser.error("--workbook and --spec are required unless --profile-only is used")
            spec = validate_spec(json.loads(args.spec.read_text(encoding="utf-8")))
            report = validate_workbook(args.workbook, spec)
    except Exception as exc:
        print(f"NTH qualitative admin validation: FAIL: {exc}", file=sys.stderr)
        return 1
    if args.summary:
        print(f"NTH qualitative admin validation: PASS ({report.get('profile_id', 'nth-qualitative-admin')})")
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
