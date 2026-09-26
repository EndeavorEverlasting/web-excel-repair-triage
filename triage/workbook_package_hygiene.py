"""Read-only OOXML package hygiene report for workbook generation and repair lanes."""
from __future__ import annotations

import argparse
import json
import zipfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Sequence
from xml.etree import ElementTree as ET

from triage.copy_surface_bounds import validate_copy_surfaces
from triage.prompt_kit_common import NS, parse_ref, resolve_relationship_target, xml_root
from triage.worksheet_cell_integrity import inspect_worksheet_cell_integrity
from triage.xlsx_utils import table_parts


@dataclass
class HygieneCheck:
    name: str
    status: str
    findings: List[dict] = field(default_factory=list)
    summary: str = ""


@dataclass
class WorkbookPackageReport:
    path: str
    checks: List[HygieneCheck] = field(default_factory=list)

    @property
    def failures(self):
        return [check for check in self.checks if check.status == "FAIL"]

    @property
    def package_valid(self) -> bool:
        return not self.failures

    def to_dict(self):
        return {"path": self.path, "package_valid": self.package_valid, "checks": [asdict(check) for check in self.checks]}


def validate_workbook_package(path: str | Path, copy_surfaces: Optional[Sequence[str]] = None) -> WorkbookPackageReport:
    workbook = Path(path)
    report = WorkbookPackageReport(str(workbook.resolve()))
    if not workbook.exists():
        report.checks.append(HygieneCheck("file exists", "FAIL", [{"path": str(workbook)}]))
        return report
    try:
        with zipfile.ZipFile(workbook) as zf:
            bad_part = zf.testzip()
            report.checks.append(HygieneCheck("ZIP CRC", "PASS" if bad_part is None else "FAIL", [{"part": bad_part}] if bad_part else []))
            names = set(zf.namelist())
            parse_findings = []
            for name in sorted(names):
                if not (name.endswith(".xml") or name.endswith(".rels")):
                    continue
                try:
                    ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    parse_findings.append({"part": name, "error": str(exc)})
            report.checks.append(HygieneCheck("XML and relationship parts parse", "FAIL" if parse_findings else "PASS", parse_findings))

            relationship_findings = []
            for rel_name in sorted(name for name in names if name.endswith(".rels")):
                try:
                    root = ET.fromstring(zf.read(rel_name))
                except ET.ParseError:
                    continue
                for rel in root:
                    if rel.attrib.get("TargetMode", "").lower() == "external":
                        continue
                    target = rel.attrib.get("Target", "")
                    resolved = resolve_relationship_target(rel_name, target)
                    if target.startswith("/"):
                        relationship_findings.append({"part": rel_name, "id": rel.attrib.get("Id"), "issue": "absolute_target", "target": target})
                    elif resolved == ".." or resolved.startswith("../"):
                        relationship_findings.append({"part": rel_name, "id": rel.attrib.get("Id"), "issue": "target_escapes_package", "target": target})
                    elif resolved not in names:
                        relationship_findings.append({"part": rel_name, "id": rel.attrib.get("Id"), "issue": "missing_target", "target": target, "resolved": resolved})
            report.checks.append(HygieneCheck("internal relationship targets resolve", "FAIL" if relationship_findings else "PASS", relationship_findings))

            table_findings = []
            ids = set()
            names_seen = set()
            for part in table_parts(zf):
                root = xml_root(zf, part)
                table_id = root.attrib.get("id", "")
                table_name = root.attrib.get("name", "")
                if table_id in ids:
                    table_findings.append({"part": part, "issue": "duplicate_table_id", "value": table_id})
                ids.add(table_id)
                if table_name in names_seen:
                    table_findings.append({"part": part, "issue": "duplicate_table_name", "value": table_name})
                names_seen.add(table_name)
                columns = root.find("m:tableColumns", NS)
                column_nodes = columns.findall("m:tableColumn", NS) if columns is not None else []
                raw_count = columns.attrib.get("count", "0") if columns is not None else "0"
                try:
                    declared_count = int(raw_count)
                except ValueError:
                    declared_count = -1
                    table_findings.append({"part": part, "issue": "invalid_declared_column_count", "raw": raw_count})
                if declared_count != len(column_nodes):
                    table_findings.append({"part": part, "issue": "declared_column_count_mismatch", "declared": declared_count, "actual": len(column_nodes)})
                parsed = parse_ref(root.attrib.get("ref", ""))
                if parsed and parsed[2] - parsed[0] + 1 != len(column_nodes):
                    table_findings.append({"part": part, "issue": "range_column_count_mismatch"})
            report.checks.append(HygieneCheck("native table metadata", "FAIL" if table_findings else "PASS", table_findings, f"{len(table_parts(zf))} table parts"))

        integrity = inspect_worksheet_cell_integrity(workbook)
        report.checks.append(HygieneCheck("worksheet cell integrity", "FAIL" if integrity else "PASS", [asdict(issue) for issue in integrity]))
        if copy_surfaces is not None:
            surfaces = validate_copy_surfaces(workbook, copy_surfaces)
            surface_findings = [asdict(result) for result in surfaces if not result.valid]
            report.checks.append(HygieneCheck("copy surfaces bounded", "FAIL" if surface_findings else "PASS", surface_findings, f"{len(surfaces)} checked"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError, ValueError) as exc:
        report.checks.append(HygieneCheck("package readable", "FAIL", [{"error": str(exc)}]))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook")
    parser.add_argument("--copy-surface", action="append", dest="copy_surfaces")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = validate_workbook_package(args.workbook, args.copy_surfaces)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for check in report.checks:
            print(f"[{check.status}] {check.name}: {check.summary}")
        print(f"Result: package_valid={str(report.package_valid).lower()}")
    return 0 if report.package_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
