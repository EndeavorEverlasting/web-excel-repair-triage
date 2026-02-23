"""
triage/gate_checks.py
---------------------
Battery of structural gate checks for OOXML / Excel-for-Web compatibility.
All checks are READ-ONLY (no XML reserialization, no file writes).

Each check returns a list[dict] of findings (empty = pass).
The top-level run_all() bundles them into a GateReport.
"""
from __future__ import annotations
import re
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List

STOPSHIP_TOKENS = ("_xlfn.", "_xludf.", "_xlpm.", "AGGREGATE(")


# ─────────────────────────── helpers ────────────────────────────

def _txt(z: zipfile.ZipFile, name: str) -> str:
    return z.read(name).decode("utf-8", errors="ignore")

def _raw(z: zipfile.ZipFile, name: str) -> bytes:
    return z.read(name)

def _sheets(z: zipfile.ZipFile) -> List[str]:
    return [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]

def _max_row(xml: str) -> int:
    rows = [int(m.group(1)) for m in re.finditer(r'<row[^>]*\br="(\d+)"', xml)]
    return max(rows) if rows else 0

def _col_to_num(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n

def _num_to_col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def _parse_ref(ref: str):
    m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", ref)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3), int(m.group(4))


# ─────────────────────────── individual gates ────────────────────────────

def check_stopship_tokens(z: zipfile.ZipFile) -> List[dict]:
    hits: List[dict] = []
    for name in _sheets(z):
        s = _txt(z, name)
        for m in re.finditer(r"<f\b[^>]*>(.*?)</f>", s, re.DOTALL):
            for tok in STOPSHIP_TOKENS:
                if tok in m.group(1):
                    hits.append({"part": name, "token": tok, "formula_snippet": m.group(1)[:120]})
    return hits


def check_cf_ref_hits(z: zipfile.ZipFile) -> List[dict]:
    hits: List[dict] = []
    for name in _sheets(z):
        s = _txt(z, name)
        for m in re.finditer(r"<conditionalFormatting\b.*?</conditionalFormatting>", s, re.DOTALL):
            if "#REF!" in m.group(0):
                hits.append({"part": name, "snippet": m.group(0)[:200]})
                break
    return hits


def check_tablecolumn_lf(z: zipfile.ZipFile) -> List[dict]:
    hits: List[dict] = []
    for name in z.namelist():
        if name.startswith("xl/tables/table") and name.endswith(".xml"):
            raw = _raw(z, name)
            idx = 0
            while True:
                j = raw.find(b'name="', idx)
                if j < 0:
                    break
                j += 6
                k = raw.find(b'"', j)
                if k < 0:
                    break
                val = raw[j:k]
                if b"\n" in val or b"\r" in val:
                    hits.append({"part": name, "value": val.decode("utf-8", errors="replace")})
                    break
                idx = k + 1
    return hits


def check_calcchain_invalid(z: zipfile.ZipFile) -> List[dict]:
    invalid: List[dict] = []
    if "xl/calcChain.xml" not in z.namelist():
        return invalid
    calc = _txt(z, "xl/calcChain.xml")
    entries = re.findall(r'<c\b[^>]*\br="([^"]+)"[^>]*\bi="(\d+)"[^>]*/>', calc)
    # Build per-sheet cell→has_formula index using split (O(n), no DOTALL backtracking)
    sheet_cache: dict[str, set] = {}
    for cell, i in entries:
        part = f"xl/worksheets/sheet{i}.xml"
        if part not in sheet_cache:
            if part not in z.namelist():
                sheet_cache[part] = None  # type: ignore[assignment]
            else:
                formula_cells: set[str] = set()
                s = _txt(z, part)
                for chunk in s.split("</c>"):
                    cm = re.search(r'<c\b[^>]*\br="([A-Z]+\d+)"', chunk)
                    if cm and "<f" in chunk[cm.end():]:
                        formula_cells.add(cm.group(1))
                sheet_cache[part] = formula_cells  # type: ignore[assignment]
        pool = sheet_cache[part]
        if pool is None:
            invalid.append({"sheet_part": part, "cell": cell, "reason": "missing_sheet_part"})
        elif cell not in pool:
            invalid.append({"sheet_part": part, "cell": cell, "reason": "no_formula_at_target"})
    return invalid


def _iter_cells(xml: str):
    """
    Yield (cell_ref, f_attrs_string) for every shared-formula cell.
    Uses split on '</c>' to avoid catastrophic backtracking on large sheets.
    """
    _CELL_REF = re.compile(r'<c\b[^>]*\br="([A-Z]+\d+)"')
    _F_TAG    = re.compile(r'<f\b([^>]*)>', re.DOTALL)
    for chunk in xml.split("</c>"):
        # Find the last <c ...> opening in this chunk
        cell_m = None
        for cell_m in _CELL_REF.finditer(chunk):
            pass  # keep last match (the actual cell open tag)
        if cell_m is None:
            continue
        cell = cell_m.group(1)
        # Formula must appear after the <c ...> tag
        after_c = chunk[cell_m.end():]
        fm = _F_TAG.search(after_c)
        if fm:
            yield cell, fm.group(1)


def check_shared_ref(z: zipfile.ZipFile) -> tuple[List[dict], List[dict]]:
    """Returns (oob_list, bbox_mismatch_list).  O(n) cell scan; no DOTALL backtracking."""
    oob: List[dict] = []
    bbox: List[dict] = []
    for part in _sheets(z):
        s = _txt(z, part)
        mrow = _max_row(s)
        si_cells: dict[str, list] = defaultdict(list)
        si_decl: dict[str, str] = {}
        for cell, fa in _iter_cells(s):
            if 't="shared"' not in fa and "t='shared'" not in fa:
                continue
            si_m = re.search(r'\bsi="(\d+)"', fa) or re.search(r"\bsi='(\d+)'", fa)
            if not si_m:
                continue
            si = si_m.group(1)
            si_cells[si].append(cell)
            ref_m = re.search(r'\bref="([^"]+)"', fa) or re.search(r"\bref='([^']+)'", fa)
            if ref_m:
                si_decl[si] = ref_m.group(1)
        for si, ref in si_decl.items():
            pr = _parse_ref(ref)
            if pr and pr[3] > mrow:
                oob.append({"part": part, "si": si, "ref": ref, "sheet_max_row": mrow})
        for si, cells in si_cells.items():
            if si not in si_decl:
                continue
            pr = _parse_ref(si_decl[si])
            if not pr:
                continue
            nums = [(_col_to_num(re.match(r'^([A-Z]+)(\d+)$', c).group(1)),
                     int(re.match(r'^([A-Z]+)(\d+)$', c).group(2)))
                    for c in cells if re.match(r'^([A-Z]+)(\d+)$', c)]
            if not nums:
                continue
            cmin = min(n[0] for n in nums); cmax = max(n[0] for n in nums)
            rmin = min(n[1] for n in nums); rmax = max(n[1] for n in nums)
            actual = f"{_num_to_col(cmin)}{rmin}:{_num_to_col(cmax)}{rmax}"
            declared = f"{pr[0]}{pr[1]}:{pr[2]}{pr[3]}"
            if actual != declared:
                bbox.append({"part": part, "si": si, "declared_ref": declared, "actual_ref": actual})
    return oob, bbox


def check_styles_dxf(z: zipfile.ZipFile) -> List[dict]:
    issues: List[dict] = []
    if "xl/styles.xml" not in z.namelist():
        return [{"part": "xl/styles.xml", "issue": "missing_styles"}]
    txt = _txt(z, "xl/styles.xml")
    actual = len(re.findall(r"<dxf\b", txt))
    m = re.search(r'<dxfs\b[^>]*\bcount="(\d+)"', txt)
    declared = int(m.group(1)) if m else None
    if declared is not None and declared != actual:
        issues.append({"part": "xl/styles.xml", "issue": "dxfs_count_mismatch", "declared": declared, "actual": actual})
    for name in _sheets(z):
        s = _txt(z, name)
        for m2 in re.finditer(r'<cfRule\b[^>]*\bdxfId="(\d+)"', s):
            did = int(m2.group(1))
            if did < 0 or did >= actual:
                issues.append({"part": name, "issue": "cf_dxfId_out_of_range", "dxfId": did, "dxf_count": actual})
    return issues


def check_xml_wellformed(z: zipfile.ZipFile) -> List[dict]:
    from xml.etree import ElementTree as ET
    bad: List[dict] = []
    for name in z.namelist():
        if name.lower().endswith(".xml"):
            raw = _raw(z, name)
            try:
                ET.fromstring(raw.decode("utf-8", errors="ignore"))
            except Exception as e:
                bad.append({"part": name, "error": f"{type(e).__name__}: {e}"})
    return bad


def check_illegal_control_chars(z: zipfile.ZipFile) -> List[dict]:
    bad: List[dict] = []
    for name in z.namelist():
        if name.lower().endswith(".xml"):
            raw = _raw(z, name)
            examples = [(i, b) for i, b in enumerate(raw) if b < 0x20 and b not in (0x09, 0x0A, 0x0D)][:10]
            if examples:
                bad.append({"part": name, "examples": examples})
    return bad


def check_rels_missing(z: zipfile.ZipFile) -> List[dict]:
    missing: List[dict] = []
    all_parts = set(z.namelist())
    for rels in [n for n in z.namelist() if n.endswith(".rels")]:
        txt = _txt(z, rels)
        for m in re.finditer(r"<Relationship\b[^>]*>", txt):
            tag = m.group(0)
            if "External" in tag:
                continue
            tm = re.search(r'\bTarget="([^"]+)"', tag)
            if not tm:
                continue
            target = tm.group(1)
            base = rels.rsplit("/", 1)[0]
            owner = base.rsplit("/", 1)[0] if "/" in base else ""
            resolved = "/".join(p for p in (owner + "/" + target).replace("//", "/").split("/")
                                if p not in ("", "."))
            if resolved not in all_parts:
                missing.append({"rels": rels, "target": target, "resolved": resolved})
    return missing


def check_workbook_activetab(z: zipfile.ZipFile) -> dict:
    out: dict[str, Any] = {}
    if "xl/workbook.xml" not in z.namelist():
        return out
    wb = _txt(z, "xl/workbook.xml")
    m = re.search(r'<workbookView\b[^>]*\bactiveTab="(\d+)"', wb)
    if not m:
        return out
    active = int(m.group(1))
    out["activeTab"] = active
    sheets = re.findall(r'<sheet\b[^>]*\bname="([^"]+)"[^>]*\br:id="([^"]+)"[^>]*/>', wb)
    out["sheetCount"] = len(sheets)
    if 0 <= active < len(sheets):
        out["activeSheetName"] = sheets[active][0]
        out["activeSheetRid"] = sheets[active][1]
    return out


# ─────────────────────────── aggregate runner ────────────────────────────

@dataclass
class GateReport:
    path: str
    stopship: List[dict] = field(default_factory=list)
    cf_ref: List[dict] = field(default_factory=list)
    tablecolumn_lf: List[dict] = field(default_factory=list)
    calcchain_invalid: List[dict] = field(default_factory=list)
    shared_ref_oob: List[dict] = field(default_factory=list)
    shared_ref_bbox: List[dict] = field(default_factory=list)
    styles_dxf: List[dict] = field(default_factory=list)
    xml_wellformed: List[dict] = field(default_factory=list)
    illegal_control: List[dict] = field(default_factory=list)
    rels_missing: List[dict] = field(default_factory=list)
    activetab: dict = field(default_factory=dict)

    def failing_gates(self) -> Dict[str, int]:
        return {k: len(v) for k, v in {
            "stopship_tokens":      self.stopship,
            "cf_ref_hits":          self.cf_ref,
            "tablecolumn_lf":       self.tablecolumn_lf,
            "calcchain_invalid":    self.calcchain_invalid,
            "shared_ref_oob":       self.shared_ref_oob,
            "shared_ref_bbox":      self.shared_ref_bbox,
            "styles_dxf_integrity": self.styles_dxf,
            "xml_wellformed":       self.xml_wellformed,
            "illegal_control_chars":self.illegal_control,
            "rels_missing_targets": self.rels_missing,
        }.items() if v}

    @property
    def pass_all(self) -> bool:
        return not self.failing_gates()

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.pass_all,
            "failing_gates": self.failing_gates(),
            "samples": {
                "stopship": self.stopship[:25],
                "cf_ref": self.cf_ref[:25],
                "tablecolumn_lf": self.tablecolumn_lf[:25],
                "calcchain_invalid": self.calcchain_invalid[:25],
                "shared_ref_oob": self.shared_ref_oob[:25],
                "shared_ref_bbox": self.shared_ref_bbox[:25],
                "styles_dxf": self.styles_dxf[:25],
                "xml_wellformed": self.xml_wellformed[:10],
                "illegal_control": self.illegal_control[:10],
                "rels_missing": self.rels_missing[:20],
            },
            "triage": {"activetab": self.activetab},
        }


def run_all(path: str) -> GateReport:
    """Run the full gate battery against *path*. Returns a GateReport."""
    rpt = GateReport(path=path)
    with zipfile.ZipFile(path, "r") as z:
        rpt.stopship = check_stopship_tokens(z)
        rpt.cf_ref = check_cf_ref_hits(z)
        rpt.tablecolumn_lf = check_tablecolumn_lf(z)
        rpt.calcchain_invalid = check_calcchain_invalid(z)
        rpt.shared_ref_oob, rpt.shared_ref_bbox = check_shared_ref(z)
        rpt.styles_dxf = check_styles_dxf(z)
        rpt.xml_wellformed = check_xml_wellformed(z)
        rpt.illegal_control = check_illegal_control_chars(z)
        rpt.rels_missing = check_rels_missing(z)
        rpt.activetab = check_workbook_activetab(z)
    return rpt

