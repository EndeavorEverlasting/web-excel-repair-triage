"""Compare candidate and repaired workbooks for cell-level semantic loss.

Part-level OOXML diffs are useful for diagnosis but can hide the operational
impact of an Excel repair. This module asks a narrower acceptance question:
did a non-empty cell, formula, or string payload present in the candidate
silently disappear or materially change in the repaired copy?

The comparison is intentionally conservative. It resolves inline/shared
strings and formula presence, while ignoring style-only cells and small numeric
serialization differences.
"""
from __future__ import annotations

import argparse
import json
import math
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


@dataclass(frozen=True)
class CellPayload:
    formula_present: bool
    formula_text: str | None
    kind: str
    value: str | float | bool | None


@dataclass(frozen=True)
class SemanticFinding:
    kind: str
    sheet: str
    cell: str
    candidate: object
    repaired: object


@dataclass
class SemanticPreservationReport:
    candidate_path: str
    repaired_path: str
    findings: list[SemanticFinding] = field(default_factory=list)
    candidate_sheet_count: int = 0
    repaired_sheet_count: int = 0

    @property
    def pass_all(self) -> bool:
        return not self.findings

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for finding in self.findings:
            out[finding.kind] = out.get(finding.kind, 0) + 1
        return out

    def to_dict(self) -> dict:
        return {
            "candidate": self.candidate_path,
            "repaired": self.repaired_path,
            "pass": self.pass_all,
            "counts": self.counts(),
            "candidate_sheet_count": self.candidate_sheet_count,
            "repaired_sheet_count": self.repaired_sheet_count,
            "findings": [asdict(item) for item in self.findings],
        }


def _sheet_map(z: zipfile.ZipFile) -> dict[str, str]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in rels.findall(f"{{{_PKG_REL}}}Relationship")
    }
    result: dict[str, str] = {}
    sheets = wb.find(f"{{{_MAIN}}}sheets")
    if sheets is None:
        return result
    for sheet in sheets:
        rid = sheet.attrib[f"{{{_DOC_REL}}}id"]
        target = targets[rid].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        result[sheet.attrib["name"]] = target
    return result


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in si.iter(f"{{{_MAIN}}}t"))
        for si in root.findall(f"{{{_MAIN}}}si")
    ]


def _numeric(raw: str | None) -> str | float | None:
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except ValueError:
        return raw


def _cells(
    z: zipfile.ZipFile,
    sheet_part: str,
    shared: list[str],
) -> dict[str, CellPayload]:
    root = ET.fromstring(z.read(sheet_part))
    out: dict[str, CellPayload] = {}
    for cell in root.findall(f".//{{{_MAIN}}}sheetData/{{{_MAIN}}}row/{{{_MAIN}}}c"):
        ref = cell.attrib.get("r")
        if not ref:
            continue
        kind = cell.attrib.get("t", "n")
        formula = cell.find(f"{{{_MAIN}}}f")
        formula_present = formula is not None
        formula_text = formula.text if formula is not None and formula.text else None

        if kind == "inlineStr":
            value: str | float | bool | None = "".join(
                node.text or "" for node in cell.iter(f"{{{_MAIN}}}t")
            )
            normalized_kind = "string"
        else:
            value_node = cell.find(f"{{{_MAIN}}}v")
            raw = value_node.text if value_node is not None else None
            if kind == "s" and raw not in (None, ""):
                try:
                    value = shared[int(raw)]
                except (ValueError, IndexError):
                    value = f"<invalid-shared-string-index:{raw}>"
                normalized_kind = "string"
            elif kind == "str":
                value = raw or ""
                normalized_kind = "string"
            elif kind == "b":
                value = raw == "1"
                normalized_kind = "bool"
            elif kind == "e":
                value = raw
                normalized_kind = "error"
            else:
                value = _numeric(raw)
                normalized_kind = "number"

        if formula_present or value not in (None, ""):
            out[ref] = CellPayload(
                formula_present=formula_present,
                formula_text=formula_text,
                kind=normalized_kind,
                value=value,
            )
    return out


def _same_numeric(a: object, b: object) -> bool:
    if not isinstance(a, (int, float)) or isinstance(a, bool):
        return False
    if not isinstance(b, (int, float)) or isinstance(b, bool):
        return False
    return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-12)


def compare_semantics(
    candidate_path: str | Path,
    repaired_path: str | Path,
) -> SemanticPreservationReport:
    candidate_path = str(candidate_path)
    repaired_path = str(repaired_path)
    report = SemanticPreservationReport(candidate_path, repaired_path)

    with zipfile.ZipFile(candidate_path, "r") as cand, zipfile.ZipFile(
        repaired_path, "r"
    ) as repaired:
        cand_sheets = _sheet_map(cand)
        rep_sheets = _sheet_map(repaired)
        report.candidate_sheet_count = len(cand_sheets)
        report.repaired_sheet_count = len(rep_sheets)
        cand_shared = _shared_strings(cand)
        rep_shared = _shared_strings(repaired)

        for sheet_name in sorted(cand_sheets):
            if sheet_name not in rep_sheets:
                report.findings.append(SemanticFinding(
                    kind="missing_sheet",
                    sheet=sheet_name,
                    cell="",
                    candidate=cand_sheets[sheet_name],
                    repaired=None,
                ))
                continue

            cand_cells = _cells(cand, cand_sheets[sheet_name], cand_shared)
            rep_cells = _cells(repaired, rep_sheets[sheet_name], rep_shared)
            for ref, cand_payload in sorted(cand_cells.items()):
                rep_payload = rep_cells.get(ref)
                if rep_payload is None:
                    report.findings.append(SemanticFinding(
                        kind="lost_cell_payload",
                        sheet=sheet_name,
                        cell=ref,
                        candidate=asdict(cand_payload),
                        repaired=None,
                    ))
                    continue

                if cand_payload.formula_present and not rep_payload.formula_present:
                    report.findings.append(SemanticFinding(
                        kind="lost_formula",
                        sheet=sheet_name,
                        cell=ref,
                        candidate=asdict(cand_payload),
                        repaired=asdict(rep_payload),
                    ))
                    continue

                if (
                    cand_payload.formula_text
                    and rep_payload.formula_text
                    and cand_payload.formula_text != rep_payload.formula_text
                ):
                    report.findings.append(SemanticFinding(
                        kind="changed_formula_text",
                        sheet=sheet_name,
                        cell=ref,
                        candidate=cand_payload.formula_text,
                        repaired=rep_payload.formula_text,
                    ))
                    continue

                if cand_payload.formula_present or rep_payload.formula_present:
                    # Cached values can change on recalculation; formula presence is
                    # the semantic contract unless both formula texts are explicit.
                    continue

                if cand_payload.kind == "string" and rep_payload.kind == "string":
                    if cand_payload.value != rep_payload.value:
                        report.findings.append(SemanticFinding(
                            kind="changed_string",
                            sheet=sheet_name,
                            cell=ref,
                            candidate=cand_payload.value,
                            repaired=rep_payload.value,
                        ))
                elif cand_payload.kind == "number" and rep_payload.kind == "number":
                    if not _same_numeric(cand_payload.value, rep_payload.value):
                        report.findings.append(SemanticFinding(
                            kind="changed_number",
                            sheet=sheet_name,
                            cell=ref,
                            candidate=cand_payload.value,
                            repaired=rep_payload.value,
                        ))
                elif (
                    cand_payload.value != rep_payload.value
                    or cand_payload.kind != rep_payload.kind
                ):
                    report.findings.append(SemanticFinding(
                        kind="changed_typed_value",
                        sheet=sheet_name,
                        cell=ref,
                        candidate=asdict(cand_payload),
                        repaired=asdict(rep_payload),
                    ))

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare candidate/repaired workbooks for cell-level semantic loss."
    )
    parser.add_argument("candidate")
    parser.add_argument("repaired")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-findings", type=int, default=200)
    args = parser.parse_args(argv)

    report = compare_semantics(args.candidate, args.repaired)
    payload = report.to_dict()
    if len(payload["findings"]) > args.max_findings:
        payload["findings"] = payload["findings"][: args.max_findings]
        payload["findings_truncated"] = True

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{'PASS' if report.pass_all else 'FAIL'}: semantic preservation")
        print(json.dumps(report.counts(), sort_keys=True))
        for finding in report.findings[: args.max_findings]:
            print(f"  {finding.kind}: {finding.sheet}!{finding.cell}")
    return 0 if report.pass_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
