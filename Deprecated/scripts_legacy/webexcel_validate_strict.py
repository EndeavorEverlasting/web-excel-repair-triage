#!/usr/bin/env python3
"""
webexcel_validate_strict.py
Strict, local, no-Excel, no-reserialization validator for "will Excel for Web likely repair this workbook?"

Usage:
  python webexcel_validate_strict.py path/to/CANDIDATE.xlsx
Outputs:
  - Human summary to stdout
  - JSON report alongside workbook: <name>.webexcel_report.json
Exit codes:
  0 = no findings (not a guarantee of Web clean)
  2 = findings detected
"""

import json
import re
import sys
import zipfile
import hashlib
from collections import defaultdict
from xml.etree import ElementTree as ET

STOPSHIP_TOKENS = ("_xlfn.", "_xludf.", "_xlpm.")

# ---------- helpers ----------

def sha256_bytes(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def read_zip_bytes(z: zipfile.ZipFile, name: str) -> bytes:
    return z.read(name)

def read_zip_text(z: zipfile.ZipFile, name: str) -> str:
    return z.read(name).decode("utf-8", errors="ignore")

def is_xml(name: str) -> bool:
    return name.lower().endswith(".xml")

def safe_parse_xml(name: str, raw: bytes):
    """
    Parse XML just to verify well-formedness.
    NOTE: We never write XML back. Parsing is read-only.
    """
    try:
        # ET can choke on some namespaces if bytes include leading BOM; decode->encode stabilizes.
        text = raw.decode("utf-8", errors="ignore")
        ET.fromstring(text)
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"

def find_illegal_xml_control_chars(raw: bytes):
    """
    XML 1.0 disallows most control chars except TAB(0x09), LF(0x0A), CR(0x0D).
    """
    bad = []
    for i, b in enumerate(raw):
        if b < 0x20 and b not in (0x09, 0x0A, 0x0D):
            bad.append((i, b))
            if len(bad) >= 20:
                break
    return bad

def parse_rels_targets(rels_xml: str):
    """
    Return list of Target paths from a .rels part.
    Handles TargetMode="External" by skipping.
    """
    targets = []
    # Keep it simple: regex parse is sufficient for targets.
    for m in re.finditer(r'<Relationship\b[^>]*?>', rels_xml):
        tag = m.group(0)
        if 'TargetMode="External"' in tag or "TargetMode='External'" in tag:
            continue
        tm = re.search(r'\bTarget="([^"]+)"', tag)
        if not tm:
            tm = re.search(r"\bTarget='([^']+)'", tag)
        if tm:
            targets.append(tm.group(1))
    return targets

def norm_target(base_part: str, target: str) -> str:
    """
    Normalize a Relationship Target relative to the .rels location.
    Example:
      base_part: xl/_rels/workbook.xml.rels
      target: worksheets/sheet1.xml
      -> xl/worksheets/sheet1.xml
    """
    # Relationship targets in OOXML are relative to the .rels part folder.
    base_dir = base_part.rsplit("/", 1)[0]  # e.g. xl/_rels
    # The "owner" folder is base_dir's parent (e.g. xl), because rels live in *_rels.
    owner_dir = base_dir.rsplit("/", 1)[0] if "/" in base_dir else ""
    # Resolve ./ and ../ manually
    path = (owner_dir + "/" + target).replace("//", "/")
    parts = []
    for p in path.split("/"):
        if p == "..":
            if parts:
                parts.pop()
        elif p == "." or p == "":
            continue
        else:
            parts.append(p)
    return "/".join(parts)

# ---------- gates from your workflow, plus a few strict ones ----------

def scan_stopship_tokens(z: zipfile.ZipFile):
    hits = []
    for name in z.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            s = read_zip_text(z, name)
            for m in re.finditer(r"<f\b[^>]*>(.*?)</f>", s, flags=re.DOTALL):
                ftxt = m.group(1)
                for tok in STOPSHIP_TOKENS:
                    if tok in ftxt:
                        hits.append({"part": name, "token": tok})
    return hits

def scan_cf_ref_hits(z: zipfile.ZipFile):
    hits = []
    for name in z.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            s = read_zip_text(z, name)
            for m in re.finditer(r"<conditionalFormatting\b.*?</conditionalFormatting>", s, flags=re.DOTALL):
                if "#REF!" in m.group(0):
                    hits.append({"part": name})
                    break
    return hits

def scan_tablecolumn_lf(z: zipfile.ZipFile):
    hits = []
    for name in z.namelist():
        if name.startswith("xl/tables/table") and name.endswith(".xml"):
            raw = read_zip_bytes(z, name)
            idx = 0
            while True:
                j = raw.find(b'name="', idx)
                if j < 0:
                    break
                j += len(b'name="')
                k = raw.find(b'"', j)
                if k < 0:
                    break
                val = raw[j:k]
                if b"\n" in val or b"\r" in val:
                    hits.append({"part": name})
                    break
                idx = k + 1
    return hits

def max_row(sheet_xml: str) -> int:
    rows = [int(m.group(1)) for m in re.finditer(r'<row[^>]*\br="(\d+)"', sheet_xml)]
    return max(rows) if rows else 0

def cell_to_col_row(cell: str):
    m = re.match(r"^([A-Z]+)(\d+)$", cell)
    if not m:
        return None
    return m.group(1), int(m.group(2))

def col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n

def num_to_col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def parse_ref(ref: str):
    m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", ref)
    if not m:
        return None
    c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
    return c1, r1, c2, r2

def scan_shared_ref_oob_and_bbox_mismatch_cellbounded(z: zipfile.ZipFile):
    """
    Cell-bounded version:
      - Identify each <c r="X"> ... </c>
      - Within that cell, look for an <f ...>...</f>
      - If t="shared" and has si, record:
          * if it has ref=, that's the base declaration for that si (in this sheet)
          * add cell to si cell list
      - Validate:
          * OOB: declared ref end row <= max row
          * BBox: declared ref bbox equals actual bbox over all cells using that si in that sheet
    """
    oob = []
    bbox = []

    sheet_parts = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
    for part in sheet_parts:
        s = read_zip_text(z, part)
        mrow = max_row(s)

        si_cells = defaultdict(list)  # si -> [cell refs]
        si_declared = {}              # si -> declared ref bbox (base)

        # Iterate cells bounded by </c>
        for cm in re.finditer(r'<c\b[^>]*\br="([^"]+)"[^>]*>(.*?)</c>', s, flags=re.DOTALL):
            cell = cm.group(1)
            inner = cm.group(2)
            fm = re.search(r"<f\b([^>]*)>(.*?)</f>", inner, flags=re.DOTALL)
            if not fm:
                continue
            f_attrs = fm.group(1)
            if 't="shared"' not in f_attrs and "t='shared'" not in f_attrs:
                continue
            sim = re.search(r'\bsi="(\d+)"', f_attrs) or re.search(r"\bsi='(\d+)'", f_attrs)
            if not sim:
                continue
            si = sim.group(1)
            si_cells[si].append(cell)
            refm = re.search(r'\bref="([^"]+)"', f_attrs) or re.search(r"\bref='([^']+)'", f_attrs)
            if refm:
                si_declared[si] = refm.group(1)

        for si, ref in si_declared.items():
            pr = parse_ref(ref)
            if pr:
                _, r1, _, r2 = pr
                if r2 > mrow:
                    oob.append({"part": part, "sheet_max_row": mrow, "ref": ref, "si": si})

        for si, cells in si_cells.items():
            if si not in si_declared:
                continue
            declared = si_declared[si]
            pr = parse_ref(declared)
            if not pr:
                continue

            cols = []
            rows = []
            for c in cells:
                cr = cell_to_col_row(c)
                if not cr:
                    continue
                col, row = cr
                cols.append(col_to_num(col))
                rows.append(row)
            if not cols or not rows:
                continue

            cmin, cmax = min(cols), max(cols)
            rmin, rmax = min(rows), max(rows)
            actual = f"{num_to_col(cmin)}{rmin}:{num_to_col(cmax)}{rmax}"

            dc1, dr1, dc2, dr2 = pr
            dnorm = f"{dc1}{dr1}:{dc2}{dr2}"

            if actual != dnorm:
                bbox.append({"part": part, "si": si, "declared_ref": dnorm, "actual_ref": actual})

    return oob, bbox

def scan_calcchain_invalid_cellbounded(z: zipfile.ZipFile):
    invalid = []
    if "xl/calcChain.xml" not in z.namelist():
        return invalid

    calc = read_zip_text(z, "xl/calcChain.xml")
    entries = re.findall(r'<c\b[^>]*\br="([^"]+)"[^>]*\bi="(\d+)"[^>]*/>', calc)

    for cell, i in entries:
        sheet_part = f"xl/worksheets/sheet{i}.xml"
        if sheet_part not in z.namelist():
            invalid.append({"sheet_part": sheet_part, "cell": cell, "reason": "missing_sheet_part"})
            continue
        s = read_zip_text(z, sheet_part)
        # Cell-bounded check: look for <c r="cell"> ... <f ...> inside that cell.
        pat = rf'<c\b[^>]*\br="{re.escape(cell)}"[^>]*>(.*?)</c>'
        m = re.search(pat, s, flags=re.DOTALL)
        if not m:
            invalid.append({"sheet_part": sheet_part, "cell": cell, "reason": "missing_cell"})
            continue
        inner = m.group(1)
        if not re.search(r"<f\b", inner):
            invalid.append({"sheet_part": sheet_part, "cell": cell, "reason": "no_formula_at_target"})
    return invalid

def scan_xml_wellformed(z: zipfile.ZipFile):
    bad = []
    for name in z.namelist():
        if is_xml(name):
            raw = read_zip_bytes(z, name)
            err = safe_parse_xml(name, raw)
            if err:
                bad.append({"part": name, "error": err})
    return bad

def scan_illegal_control_chars(z: zipfile.ZipFile):
    bad = []
    for name in z.namelist():
        if is_xml(name):
            raw = read_zip_bytes(z, name)
            hits = find_illegal_xml_control_chars(raw)
            if hits:
                bad.append({"part": name, "examples": hits})
    return bad

def scan_rels_missing_targets(z: zipfile.ZipFile):
    missing = []
    all_parts = set(z.namelist())
    rels_parts = [n for n in z.namelist() if n.endswith(".rels")]
    for rels in rels_parts:
        rels_xml = read_zip_text(z, rels)
        for t in parse_rels_targets(rels_xml):
            target_part = norm_target(rels, t)
            if target_part not in all_parts:
                missing.append({"rels": rels, "target": t, "resolved": target_part})
    return missing

def scan_styles_dxf_integrity(z: zipfile.ZipFile):
    """
    Check:
      - styles.xml exists
      - dxfs/@count matches number of <dxf> children
      - all cfRule dxfId values are within [0, dxf_count-1]
    """
    issues = []
    if "xl/styles.xml" not in z.namelist():
        return [{"part": "xl/styles.xml", "issue": "missing_styles"}]

    styles_raw = read_zip_bytes(z, "xl/styles.xml")
    styles_txt = styles_raw.decode("utf-8", errors="ignore")

    # Count actual <dxf> tags
    actual = len(re.findall(r"<dxf\b", styles_txt))
    m = re.search(r"<dxfs\b[^>]*\bcount=\"(\d+)\"", styles_txt)
    declared = int(m.group(1)) if m else None

    if declared is not None and declared != actual:
        issues.append({"part": "xl/styles.xml", "issue": "dxfs_count_mismatch", "declared": declared, "actual": actual})

    dxf_count = actual

    # Scan all sheets for dxfId usage in cfRules
    for name in z.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            s = read_zip_text(z, name)
            for m2 in re.finditer(r"<cfRule\b[^>]*\bdxfId=\"(\d+)\"", s):
                did = int(m2.group(1))
                if did < 0 or did >= dxf_count:
                    issues.append({"part": name, "issue": "cf_dxfId_out_of_range", "dxfId": did, "dxf_count": dxf_count})
    return issues

def scan_workbook_activeTab_mapping(z: zipfile.ZipFile):
    """
    Report activeTab and map it to sheet name + sheet part.
    Not an error gate, but logged for triage discipline.
    """
    out = {}
    if "xl/workbook.xml" not in z.namelist() or "xl/_rels/workbook.xml.rels" not in z.namelist():
        return out

    wb = read_zip_text(z, "xl/workbook.xml")
    rels = read_zip_text(z, "xl/_rels/workbook.xml.rels")

    # activeTab
    m = re.search(r"<workbookView\b[^>]*\bactiveTab=\"(\d+)\"", wb)
    if not m:
        return out
    active = int(m.group(1))
    out["activeTab"] = active

    # sheet order: list of (name, r:id)
    sheets = []
    for sm in re.finditer(r"<sheet\b[^>]*\bname=\"([^\"]+)\"[^>]*\br:id=\"([^\"]+)\"[^>]*/>", wb):
        sheets.append((sm.group(1), sm.group(2)))

    if 0 <= active < len(sheets):
        sheet_name, rid = sheets[active]
        out["activeSheetName"] = sheet_name
        out["activeSheetRid"] = rid
        # rid -> target
        rid_m = re.search(rf'Id="{re.escape(rid)}"\s+Type="[^"]+"\s+Target="([^"]+)"', rels)
        if rid_m:
            out["activeSheetTarget"] = "xl/" + rid_m.group(1)
    out["sheetCount"] = len(sheets)
    return out

# ---------- main ----------

def validate(path: str):
    report = {
        "file": path,
        "gates": {},
        "triage": {},
        "notes": [
            "This tool cannot guarantee Excel for Web will open without repair; it only detects common structural hazards.",
            "All parsing is read-only; no files are written except the JSON report."
        ],
    }

    with zipfile.ZipFile(path, "r") as z:
        oob, bbox = scan_shared_ref_oob_and_bbox_mismatch_cellbounded(z)
        calc_invalid = scan_calcchain_invalid_cellbounded(z)
        stopship = scan_stopship_tokens(z)
        cf_ref = scan_cf_ref_hits(z)
        tbl_lf = scan_tablecolumn_lf(z)

        xml_bad = scan_xml_wellformed(z)
        ctrl_bad = scan_illegal_control_chars(z)
        rels_missing = scan_rels_missing_targets(z)
        styles_issues = scan_styles_dxf_integrity(z)
        active_map = scan_workbook_activeTab_mapping(z)

    report["gates"]["shared_ref_oob_count"] = len(oob)
    report["gates"]["shared_ref_bbox_mismatch_count"] = len(bbox)
    report["gates"]["calcchain_invalid_count"] = len(calc_invalid)
    report["gates"]["stopship_token_hits_count"] = len(stopship)
    report["gates"]["cf_ref_hits_count"] = len(cf_ref)
    report["gates"]["tablecolumn_lf_hits_count"] = len(tbl_lf)

    report["gates"]["xml_wellformed_errors_count"] = len(xml_bad)
    report["gates"]["illegal_control_chars_count"] = len(ctrl_bad)
    report["gates"]["rels_missing_targets_count"] = len(rels_missing)
    report["gates"]["styles_dxf_integrity_issues_count"] = len(styles_issues)

    # Keep samples small
    report["samples"] = {
        "shared_ref_oob": oob[:25],
        "shared_ref_bbox_mismatch": bbox[:25],
        "calcchain_invalid": calc_invalid[:25],
        "stopship_hits": stopship[:25],
        "cf_ref_hits": cf_ref[:25],
        "tablecolumn_lf_hits": tbl_lf[:25],
        "xml_wellformed_errors": xml_bad[:10],
        "illegal_control_chars": ctrl_bad[:10],
        "rels_missing_targets": rels_missing[:20],
        "styles_dxf_integrity": styles_issues[:25],
    }

    report["triage"]["workbookView"] = active_map

    # Decide pass/fail on any non-zero gate except triage mapping.
    failing = any(v for k, v in report["gates"].items() if isinstance(v, int) and v != 0)
    return report, failing

def main():
    if len(sys.argv) != 2:
        print("Usage: python webexcel_validate_strict.py YOUR_FILE.xlsx")
        sys.exit(2)

    path = sys.argv[1]
    report, failing = validate(path)

    # Write JSON report
    out_path = path + ".webexcel_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("FILE:", report["file"])
    for k in (
        "shared_ref_oob_count",
        "shared_ref_bbox_mismatch_count",
        "calcchain_invalid_count",
        "stopship_token_hits_count",
        "cf_ref_hits_count",
        "tablecolumn_lf_hits_count",
        "xml_wellformed_errors_count",
        "illegal_control_chars_count",
        "rels_missing_targets_count",
        "styles_dxf_integrity_issues_count",
    ):
        print(f"{k}: {report['gates'][k]}")

    wbv = report["triage"].get("workbookView", {})
    if wbv:
        print("activeTab:", wbv.get("activeTab"))
        print("activeSheetName:", wbv.get("activeSheetName"))
        print("activeSheetTarget:", wbv.get("activeSheetTarget"))

    print("JSON report:", out_path)

    sys.exit(2 if failing else 0)

if __name__ == "__main__":
    main()
