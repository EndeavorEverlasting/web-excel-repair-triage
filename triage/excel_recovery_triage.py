"""Automate Excel recovery-log parsing and targeted OOXML package triage.

The command is read-only. It correlates a desktop Excel recovery log with the
referenced workbook parts, parses all XML and relationship parts, and emits
machine-readable JSON plus an operator-facing Markdown report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Sequence
from xml.etree import ElementTree as ET

RECOVERY_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_PART_RE = re.compile(r"/(?:[^\s<'\"]+/)*[^\s<'\"]+?\.xml(?:\.rels)?", re.IGNORECASE)


@dataclass(frozen=True)
class RecoveryEntry:
    action: str
    message: str
    part: str = ""


@dataclass(frozen=True)
class PartFinding:
    part: str
    present: bool
    size_bytes: int = 0
    sha256: str = ""
    parse_status: str = "NOT_APPLICABLE"
    parse_error: str = ""
    referenced_by_recovery_log: bool = False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_part(part: str) -> str:
    return part.strip().lstrip("/")


def _extract_part(message: str) -> str:
    match = _PART_RE.search(message)
    return _normalize_part(match.group(0)) if match else ""


def parse_recovery_log_text(text: str) -> dict:
    """Parse an Excel ``recoveryLog`` XML document into normalized entries."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        return {
            "parsed": False,
            "parse_error": f"{type(exc).__name__}: {exc}",
            "log_file_name": "",
            "summary": "",
            "entries": [],
        }

    def _text(path: str) -> str:
        node = root.find(path)
        return (node.text or "").strip() if node is not None else ""

    entries: list[RecoveryEntry] = []
    containers = (
        ("removed_part", f"{{{RECOVERY_NS}}}removedParts", f"{{{RECOVERY_NS}}}removedPart"),
        ("removed_record", f"{{{RECOVERY_NS}}}removedRecords", f"{{{RECOVERY_NS}}}removedRecord"),
        ("repaired_record", f"{{{RECOVERY_NS}}}repairedRecords", f"{{{RECOVERY_NS}}}repairedRecord"),
    )
    for action, container_tag, item_tag in containers:
        container = root.find(container_tag)
        if container is None:
            continue
        for item in container.findall(item_tag):
            message = (item.text or "").strip()
            entries.append(RecoveryEntry(action=action, message=message, part=_extract_part(message)))

    return {
        "parsed": True,
        "parse_error": "",
        "log_file_name": _text(f"{{{RECOVERY_NS}}}logFileName"),
        "summary": _text(f"{{{RECOVERY_NS}}}summary"),
        "entries": [asdict(entry) for entry in entries],
    }


def parse_recovery_log(path: str | Path) -> dict:
    source = Path(path)
    payload = parse_recovery_log_text(source.read_text(encoding="utf-8-sig", errors="replace"))
    payload["source_path"] = str(source)
    return payload


def _parse_xml_part(raw: bytes) -> tuple[str, str]:
    if not raw:
        return "FAIL", "empty XML part"
    try:
        ET.fromstring(raw)
    except ET.ParseError as exc:
        return "FAIL", f"{type(exc).__name__}: {exc}"
    return "PASS", ""


def _part_finding(name: str, raw: bytes, *, referenced: bool) -> PartFinding:
    if name.lower().endswith((".xml", ".rels")):
        parse_status, parse_error = _parse_xml_part(raw)
    else:
        parse_status, parse_error = "NOT_APPLICABLE", ""
    return PartFinding(
        part=name,
        present=True,
        size_bytes=len(raw),
        sha256=_sha256(raw),
        parse_status=parse_status,
        parse_error=parse_error,
        referenced_by_recovery_log=referenced,
    )


def _styles_dxf_diagnostics(zf: zipfile.ZipFile, names: set[str]) -> dict:
    result = {
        "styles_present": "xl/styles.xml" in names,
        "styles_parse_status": "NOT_RUN",
        "styles_parse_error": "",
        "declared_dxf_count": None,
        "actual_dxf_count": None,
        "cf_dxf_references": [],
        "out_of_range_dxf_references": [],
    }
    if "xl/styles.xml" not in names:
        return result

    styles_raw = zf.read("xl/styles.xml")
    status, error = _parse_xml_part(styles_raw)
    result["styles_parse_status"] = status
    result["styles_parse_error"] = error
    if status != "PASS":
        return result

    styles_root = ET.fromstring(styles_raw)
    ns = {"m": RECOVERY_NS}
    dxfs = styles_root.find("m:dxfs", ns)
    actual = len(list(dxfs)) if dxfs is not None else 0
    declared_raw = dxfs.attrib.get("count") if dxfs is not None else None
    declared = int(declared_raw) if declared_raw and declared_raw.isdigit() else None
    result["declared_dxf_count"] = declared
    result["actual_dxf_count"] = actual

    references: list[dict] = []
    invalid: list[dict] = []
    for part in sorted(name for name in names if name.startswith("xl/worksheets/") and name.endswith(".xml")):
        raw = zf.read(part)
        status, _ = _parse_xml_part(raw)
        if status != "PASS":
            continue
        root = ET.fromstring(raw)
        for rule in root.findall(".//m:cfRule", ns):
            raw_id = rule.attrib.get("dxfId")
            if raw_id is None:
                continue
            try:
                dxf_id = int(raw_id)
            except ValueError:
                record = {"part": part, "dxf_id": raw_id, "reason": "not_integer"}
                references.append(record)
                invalid.append(record)
                continue
            record = {"part": part, "dxf_id": dxf_id}
            references.append(record)
            if dxf_id < 0 or dxf_id >= actual:
                invalid.append({**record, "reason": "out_of_range", "dxf_count": actual})
    result["cf_dxf_references"] = references
    result["out_of_range_dxf_references"] = invalid
    return result


def inspect_workbook(path: str | Path, referenced_parts: Iterable[str] = ()) -> dict:
    """Read-only inspection of every XML/rels part plus recovery-referenced parts."""
    workbook = Path(path)
    referenced = {_normalize_part(part) for part in referenced_parts if part}
    result = {
        "path": str(workbook),
        "exists": workbook.exists(),
        "size_bytes": workbook.stat().st_size if workbook.exists() else 0,
        "sha256": "",
        "zip_status": "NOT_RUN",
        "zip_error": "",
        "parts": [],
        "referenced_parts_missing": [],
        "xml_parse_failures": [],
        "styles_and_cf": {},
    }
    if not workbook.exists():
        result["zip_status"] = "FAIL"
        result["zip_error"] = "workbook does not exist"
        return result

    workbook_bytes = workbook.read_bytes()
    result["sha256"] = _sha256(workbook_bytes)
    try:
        zf = zipfile.ZipFile(workbook)
    except zipfile.BadZipFile as exc:
        result["zip_status"] = "FAIL"
        result["zip_error"] = f"{type(exc).__name__}: {exc}"
        return result

    with zf:
        result["zip_status"] = "PASS"
        names = set(zf.namelist())
        findings: list[PartFinding] = []
        for name in sorted(names):
            if not name.lower().endswith((".xml", ".rels")) and name not in referenced:
                continue
            findings.append(_part_finding(name, zf.read(name), referenced=name in referenced))
        for part in sorted(referenced - names):
            findings.append(PartFinding(part=part, present=False, referenced_by_recovery_log=True))
            result["referenced_parts_missing"].append(part)
        result["parts"] = [asdict(finding) for finding in findings]
        result["xml_parse_failures"] = [
            {"part": finding.part, "error": finding.parse_error}
            for finding in findings
            if finding.parse_status == "FAIL"
        ]
        result["styles_and_cf"] = _styles_dxf_diagnostics(zf, names)
    return result


def _root_cause_candidates(recovery_logs: Sequence[dict], workbook: dict) -> list[dict]:
    candidates: list[dict] = []
    entries = [entry for log in recovery_logs for entry in log.get("entries", [])]
    actions_by_part: dict[str, set[str]] = {}
    for entry in entries:
        part = entry.get("part", "")
        if part:
            actions_by_part.setdefault(part, set()).add(entry.get("action", ""))

    parse_failures = {item["part"]: item["error"] for item in workbook.get("xml_parse_failures", [])}
    styles = workbook.get("styles_and_cf", {})
    if "xl/styles.xml" in parse_failures or styles.get("styles_parse_status") == "FAIL":
        candidates.append({
            "code": "STYLES_XML_UNREADABLE",
            "confidence": "HIGH",
            "evidence": parse_failures.get("xl/styles.xml") or styles.get("styles_parse_error"),
            "impact": "Excel cannot resolve style indexes; cell records across many sheets may be removed.",
        })
    if actions_by_part.get("xl/styles.xml") and any(
        part.startswith("xl/worksheets/") and "removed_record" in actions
        for part, actions in actions_by_part.items()
    ):
        candidates.append({
            "code": "STYLE_TABLE_FAILURE_CASCADES_TO_CELLS",
            "confidence": "HIGH",
            "evidence": "Recovery log removed styles.xml and cell records from worksheets.",
            "impact": "Worksheet cells referencing the unreadable style table are discarded during repair.",
        })
    if any("repaired_record" in actions for part, actions in actions_by_part.items() if part.startswith("xl/worksheets/")):
        candidates.append({
            "code": "CONDITIONAL_FORMATTING_REPAIRED",
            "confidence": "HIGH",
            "evidence": "Recovery log reports repaired worksheet conditional formatting.",
            "impact": "The workbook is failed for delivery even if Excel can display a repaired copy.",
        })
    invalid_dxf = styles.get("out_of_range_dxf_references") or []
    if invalid_dxf:
        candidates.append({
            "code": "CF_DXF_REFERENCE_OUT_OF_RANGE",
            "confidence": "HIGH",
            "evidence": invalid_dxf,
            "impact": "Conditional-formatting rules reference differential styles that do not exist.",
        })
    return candidates


def build_report(workbook_path: str | Path, recovery_log_paths: Sequence[str | Path] = ()) -> dict:
    logs = [parse_recovery_log(path) for path in recovery_log_paths]
    referenced_parts = [
        entry.get("part", "")
        for log in logs
        for entry in log.get("entries", [])
        if entry.get("part")
    ]
    workbook = inspect_workbook(workbook_path, referenced_parts)
    entries = [entry for log in logs for entry in log.get("entries", [])]
    stop_ship_reasons: list[str] = []
    if any(not log.get("parsed") for log in logs):
        stop_ship_reasons.append("recovery_log_parse_failed")
    if entries:
        stop_ship_reasons.append("excel_recovery_actions_observed")
    if workbook.get("zip_status") != "PASS":
        stop_ship_reasons.append("invalid_or_missing_xlsx_package")
    if workbook.get("xml_parse_failures"):
        stop_ship_reasons.append("xml_part_parse_failure")
    if workbook.get("referenced_parts_missing"):
        stop_ship_reasons.append("recovery_referenced_part_missing")
    if (workbook.get("styles_and_cf") or {}).get("out_of_range_dxf_references"):
        stop_ship_reasons.append("conditional_formatting_dxf_reference_invalid")

    verdict = "STOP_SHIP" if stop_ship_reasons else "STATIC_PACKAGE_PASS"
    achieved_proof = "desktop_excel_repair_observed" if entries else "static_package_inspection"
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "stop_ship_reasons": stop_ship_reasons,
        "achieved_proof": achieved_proof,
        "proof_ceiling": (
            "Desktop Excel recovery evidence plus read-only package triage. "
            "Does not prove a repaired or replacement workbook is acceptable."
            if entries
            else "Read-only static package triage only; no Desktop Excel or Excel for Web acceptance proof."
        ),
        "workbook": workbook,
        "recovery_logs": logs,
        "root_cause_candidates": _root_cause_candidates(logs, workbook),
    }


def render_markdown(report: dict) -> str:
    workbook = report["workbook"]
    lines = [
        "# Excel Recovery Triage",
        "",
        f"- **Verdict:** `{report['verdict']}`",
        f"- **Workbook:** `{workbook['path']}`",
        f"- **SHA-256:** `{workbook.get('sha256', '')}`",
        f"- **Proof reached:** `{report['achieved_proof']}`",
        f"- **Proof ceiling:** {report['proof_ceiling']}",
        "",
        "## Stop-ship reasons",
        "",
    ]
    reasons = report.get("stop_ship_reasons") or []
    lines.extend([f"- `{reason}`" for reason in reasons] or ["- None from the supplied evidence."])
    lines.extend(["", "## Recovery actions", ""])
    entries = [entry for log in report.get("recovery_logs", []) for entry in log.get("entries", [])]
    if entries:
        lines.append("| Action | Part | Message |")
        lines.append("|---|---|---|")
        for entry in entries:
            message = entry.get("message", "").replace("|", "\\|")
            lines.append(f"| {entry.get('action', '')} | `{entry.get('part', '')}` | {message} |")
    else:
        lines.append("- No recovery log actions supplied.")
    lines.extend(["", "## XML failures", ""])
    failures = workbook.get("xml_parse_failures") or []
    if failures:
        lines.append("| Part | Error |")
        lines.append("|---|---|")
        for failure in failures:
            escaped_error = failure["error"].replace("|", "\\|")
            lines.append(f"| `{failure['part']}` | {escaped_error} |")
    else:
        lines.append("- No XML parse failures detected by this static inspection.")
    lines.extend(["", "## Root-cause candidates", ""])
    candidates = report.get("root_cause_candidates") or []
    if candidates:
        for candidate in candidates:
            lines.append(f"### {candidate['code']} ({candidate['confidence']})")
            lines.append("")
            lines.append(f"- Evidence: `{candidate['evidence']}`")
            lines.append(f"- Impact: {candidate['impact']}")
            lines.append("")
    else:
        lines.append("- No root-cause candidate reached the configured evidence threshold.")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", help="Path to the original workbook that Excel opened or repaired.")
    parser.add_argument(
        "--recovery-log",
        action="append",
        default=[],
        help="Excel recoveryLog XML path. Repeat for multiple logs.",
    )
    parser.add_argument("--json-out", help="Write the full machine-readable report to this path.")
    parser.add_argument("--markdown-out", help="Write the operator-facing report to this path.")
    parser.add_argument("--print-json", action="store_true", help="Print the full JSON report to stdout.")
    args = parser.parse_args(argv)

    report = build_report(args.workbook, args.recovery_log)
    if args.json_out:
        target = Path(args.json_out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown_out:
        target = Path(args.markdown_out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_markdown(report), encoding="utf-8")

    if args.print_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{report['verdict']}: {args.workbook}")
        for reason in report["stop_ship_reasons"]:
            print(f"- {reason}")
    return 0 if report["verdict"] == "STATIC_PACKAGE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
