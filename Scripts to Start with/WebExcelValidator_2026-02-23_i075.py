import re
import zipfile
from collections import defaultdict

STOPSHIP_TOKENS = ("_xlfn.", "_xludf.", "_xlpm.")

def read_zip_text(z: zipfile.ZipFile, name: str) -> str:
    return z.read(name).decode("utf-8", errors="ignore")

def max_row(sheet_xml: str) -> int:
    rows = [int(m.group(1)) for m in re.finditer(r'<row[^>]*\br="(\d+)"', sheet_xml)]
    return max(rows) if rows else 0

def cell_to_col_row(cell: str):
    m = re.match(r'^([A-Z]+)(\d+)$', cell)
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
    m = re.match(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$', ref)
    if not m:
        return None
    c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
    return c1, r1, c2, r2

def scan_shared_ref_oob_and_bbox_mismatch(xlsx_path: str):
    """
    Returns:
      oob_issues: list[(sheet_part, sheet_max_row, ref, si)]
      bbox_mismatch: list[(sheet_part, si, declared_ref, actual_ref)]
    """
    oob_issues = []
    bbox_mismatch = []

    with zipfile.ZipFile(xlsx_path, "r") as z:
        sheet_parts = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
        for part in sheet_parts:
            s = read_zip_text(z, part)
            mrow = max_row(s)

            si_cells = defaultdict(list)   # si -> list of cell refs
            si_declared = {}               # si -> declared ref from base

            # Capture cell reference for each formula block
            for m in re.finditer(r'<c\b[^>]*\br="([^"]+)"[^>]*>.*?<f\b([^>]*)>.*?</f>', s, flags=re.DOTALL):
                cell = m.group(1)
                f_attrs = m.group(2)

                if 't="shared"' not in f_attrs:
                    continue

                si_m = re.search(r'\bsi="(\d+)"', f_attrs)
                if not si_m:
                    continue
                si = si_m.group(1)
                si_cells[si].append(cell)

                ref_m = re.search(r'\bref="([^"]+)"', f_attrs)
                if ref_m:
                    si_declared[si] = ref_m.group(1)

            # OOB check: declared end row must not exceed sheet max row
            for si, ref in si_declared.items():
                pr = parse_ref(ref)
                if pr:
                    _, r1, _, r2 = pr
                    if r2 > mrow:
                        oob_issues.append((part, mrow, ref, si))

            # BBox mismatch: declared bbox must match actual bbox of all cells using that si
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
                    bbox_mismatch.append((part, si, dnorm, actual))

    return oob_issues, bbox_mismatch

def scan_calcchain_invalid(xlsx_path: str):
    """
    calcChain entries must point to existing formula cells (<c r="X"><f ...>)
    """
    invalid = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        if "xl/calcChain.xml" not in z.namelist():
            return invalid

        calc = read_zip_text(z, "xl/calcChain.xml")
        entries = re.findall(r'<c\b[^>]*\br="([^"]+)"[^>]*\bi="(\d+)"[^>]*/>', calc)

        for cell, i in entries:
            sheet_part = f"xl/worksheets/sheet{i}.xml"
            if sheet_part not in z.namelist():
                invalid.append((sheet_part, cell, "missing_sheet_part"))
                continue
            s = read_zip_text(z, sheet_part)
            pattern = rf'<c\b[^>]*\br="{re.escape(cell)}"[^>]*>.*?<f\b'
            if not re.search(pattern, s, flags=re.DOTALL):
                invalid.append((sheet_part, cell, "no_formula_at_target"))

    return invalid

def scan_stopship_tokens(xlsx_path: str):
    hits = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                s = read_zip_text(z, name)
                for m in re.finditer(r'<f\b[^>]*>(.*?)</f>', s, flags=re.DOTALL):
                    ftxt = m.group(1)
                    for tok in STOPSHIP_TOKENS:
                        if tok in ftxt:
                            hits.append((name, tok))
    return hits

def scan_cf_ref_hits(xlsx_path: str):
    hits = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        for name in z.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                s = read_zip_text(z, name)
                for m in re.finditer(r'<conditionalFormatting\b.*?</conditionalFormatting>', s, flags=re.DOTALL):
                    block = m.group(0)
                    if "#REF!" in block:
                        hits.append(name)
                        break
    return hits

def scan_tablecolumn_lf(xlsx_path: str):
    hits = []
    with zipfile.ZipFile(xlsx_path, "r") as z:
        for name in z.namelist():
            if name.startswith("xl/tables/table") and name.endswith(".xml"):
                raw = z.read(name)  # bytes (important)
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
                        hits.append(name)
                        break
                    idx = k + 1
    return hits

def validate(xlsx_path: str):
    oob, bbox = scan_shared_ref_oob_and_bbox_mismatch(xlsx_path)
    calc_invalid = scan_calcchain_invalid(xlsx_path)
    stopship = scan_stopship_tokens(xlsx_path)
    cf_ref = scan_cf_ref_hits(xlsx_path)
    tbl_lf = scan_tablecolumn_lf(xlsx_path)

    print("FILE:", xlsx_path)
    print("shared_ref_oob_count:", len(oob))
    for i in oob[:20]:
        print("  OOB:", i)

    print("shared_ref_bbox_mismatch_count:", len(bbox))
    for i in bbox[:20]:
        print("  BBOX:", i)

    print("calcchain_invalid_count:", len(calc_invalid))
    for i in calc_invalid[:20]:
        print("  CALC:", i)

    print("stopship_token_hits_count:", len(stopship))
    for i in stopship[:20]:
        print("  STOPSHIP:", i)

    print("cf_ref_hits_count:", len(cf_ref))
    for i in cf_ref[:20]:
        print("  CF_REF:", i)

    print("tablecolumn_lf_hits_count:", len(tbl_lf))
    for i in tbl_lf[:20]:
        print("  TBL_LF:", i)

if __name__ == "__main__":
    # Replace with your candidate path
    validate("""CANDIDATE_DeploymentTracker_vNext10_2026-02-23_i075_webfix_sharedRef_sheet7_sheet12_v12_noop.xlsx""")
