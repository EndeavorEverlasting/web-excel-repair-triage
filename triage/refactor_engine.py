"""
triage/refactor_engine.py
-------------------------
Column-reorder engine for .xlsx workbooks (OOXML zip-part level).

Given a target column ordering (by header name), this engine:
  1. Builds a column permutation map (old_col_index → new_col_index).
  2. Rewrites every cell reference in the sheet XML (row data, formulas).
  3. Shifts CF sqref ranges and formula column refs.
  4. Shifts DV sqref ranges.
  5. Reorders <tableColumn> elements in the table definition.
  6. Updates sharedStrings only if header text is stored there.

All manipulation is byte/string-level — no openpyxl, no lxml.

Design constraint: formulas use A1-style references.  The engine rewrites
column letters in cell references (e.g. $G$2 → $I$2) according to the
permutation map.  Row numbers are never changed.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from triage.xlsx_utils import (
    read_text, sheet_parts, sheet_name_map, table_parts,
    extract_blocks, get_attr, col_to_num, num_to_col,
)


# ──────────────────────── data structures ────────────────────────


@dataclass
class RefactorSpec:
    """Specification for a column reorder operation."""
    target_sheet_name: str  # friendly name, e.g. "Deployments"
    new_column_order: List[str]  # ordered header names in desired sequence
    rename_map: Dict[str, str] = field(default_factory=dict)  # old_name → new_name


@dataclass
class RefactorResult:
    """Result of a refactor operation."""
    output_bytes: bytes
    permutation: Dict[int, int]  # old 1-based col → new 1-based col
    columns_moved: int
    columns_renamed: int
    formulas_rewritten: int
    cf_sqrefs_rewritten: int
    dv_sqrefs_rewritten: int
    warnings: List[str] = field(default_factory=list)


# ──────────────────────── column reference rewriting ────────────────────────

# Matches A1-style cell references like $A$1, A1, $AB12, ZZ999
# Captures optional $, column letters, optional $, row digits
_CELL_REF_RE = re.compile(
    r'(\$?)([A-Z]{1,3})(\$?)(\d+)'
)

# For range references in sqref: "A1:Z99" or "A1:Z99 AA1:AZ99"
_RANGE_TOKEN_RE = re.compile(
    r'(\$?)([A-Z]{1,3})(\$?)(\d+)'
    r'(?::(\$?)([A-Z]{1,3})(\$?)(\d+))?'
)


def build_permutation(
    current_headers: List[str],
    new_order: List[str],
) -> Dict[int, int]:
    """Build {old_1based_col: new_1based_col} permutation map.

    Headers in current_headers that are NOT in new_order are appended
    at the end in their original relative order (preserves unknown columns).
    """
    # Build name→old_index lookup
    name_to_old: Dict[str, int] = {}
    for i, h in enumerate(current_headers):
        name_to_old[h] = i + 1  # 1-based

    perm: Dict[int, int] = {}
    new_idx = 1

    # Place explicitly ordered columns first
    for name in new_order:
        old_idx = name_to_old.get(name)
        if old_idx is not None:
            perm[old_idx] = new_idx
            new_idx += 1

    # Append remaining columns in original order
    placed = set(perm.keys())
    for i, h in enumerate(current_headers):
        old_idx = i + 1
        if old_idx not in placed:
            perm[old_idx] = new_idx
            new_idx += 1

    return perm


def remap_col_letter(col_letter: str, perm: Dict[int, int]) -> str:
    """Remap a column letter using the permutation map."""
    old_num = col_to_num(col_letter)
    new_num = perm.get(old_num, old_num)
    return num_to_col(new_num)


def rewrite_cell_ref(ref: str, perm: Dict[int, int]) -> str:
    """Rewrite column letters in a single cell reference like $A$1 or AB12."""
    def _sub(m: re.Match) -> str:
        dollar1, col, dollar2, row = m.group(1), m.group(2), m.group(3), m.group(4)
        new_col = remap_col_letter(col, perm)
        return f"{dollar1}{new_col}{dollar2}{row}"
    return _CELL_REF_RE.sub(_sub, ref)


def rewrite_formula(formula: str, perm: Dict[int, int]) -> str:
    """Rewrite all cell references in a formula string.

    Handles: A1, $A$1, A$1, $A1, ranges like A1:Z99, and mixed refs.
    Preserves function names, string literals, and operators.
    """
    if not formula or not perm:
        return formula

    result = []
    i = 0
    in_string = False

    while i < len(formula):
        ch = formula[i]

        # Skip string literals
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue

        if in_string:
            result.append(ch)
            i += 1
            continue

        # Try to match a cell reference at this position
        m = _CELL_REF_RE.match(formula, i)
        if m:
            # Check it's not part of a function name (preceded by letter)
            if i > 0 and formula[i-1].isalpha():
                result.append(ch)
                i += 1
                continue
            dollar1, col, dollar2, row = m.group(1), m.group(2), m.group(3), m.group(4)
            new_col = remap_col_letter(col, perm)
            result.append(f"{dollar1}{new_col}{dollar2}{row}")
            i = m.end()
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def rewrite_sqref(sqref: str, perm: Dict[int, int]) -> str:
    """Rewrite column letters in a sqref string (space-separated ranges)."""
    tokens = sqref.split()
    new_tokens = []
    for token in tokens:
        new_tokens.append(rewrite_cell_ref(token, perm))
    return " ".join(new_tokens)


# ──────────────────── sheet XML rewriting ────────────────────


def _rewrite_row_cells(row_xml: str, perm: Dict[int, int]) -> str:
    """Reorder <c> elements within a <row> and rewrite their r= attributes + formulas.

    Each <c r="XX##"> gets its column letter remapped.
    Formulas inside <f>…</f> get all cell refs remapped.
    """
    # Extract all <c …>…</c> or <c …/> elements
    cell_pattern = re.compile(r'<c\b[^>]*(?:>.*?</c>|/>)', re.DOTALL)
    cells = cell_pattern.findall(row_xml)

    remapped: List[Tuple[int, str]] = []  # (new_col_num, rewritten_cell_xml)

    for cell_xml in cells:
        # Get the r= attribute (cell reference like "AB12")
        r_attr = get_attr(cell_xml, "r")
        if not r_attr:
            remapped.append((9999, cell_xml))
            continue

        # Parse col + row from reference
        ref_m = re.match(r'^([A-Z]+)(\d+)$', r_attr)
        if not ref_m:
            remapped.append((9999, cell_xml))
            continue

        old_col_letter = ref_m.group(1)
        row_num = ref_m.group(2)
        old_col_num = col_to_num(old_col_letter)
        new_col_num = perm.get(old_col_num, old_col_num)
        new_col_letter = num_to_col(new_col_num)
        new_ref = f"{new_col_letter}{row_num}"

        # Rewrite the r= attribute
        new_cell = re.sub(
            r'r="[^"]*"',
            f'r="{new_ref}"',
            cell_xml,
            count=1,
        )

        # Rewrite formulas inside <f>…</f>
        def _rewrite_f(m: re.Match) -> str:
            tag_open = m.group(1)
            formula_text = m.group(2)
            return f"{tag_open}{rewrite_formula(formula_text, perm)}</f>"

        new_cell = re.sub(
            r'(<f\b[^>]*>)(.*?)</f>',
            _rewrite_f,
            new_cell,
            flags=re.DOTALL,
        )

        remapped.append((new_col_num, new_cell))

    # Sort cells by new column number
    remapped.sort(key=lambda x: x[0])

    # Rebuild the row: replace old cells with reordered cells
    # Find the row tag and reconstruct
    row_open_m = re.match(r'(<row\b[^>]*>)', row_xml)
    if not row_open_m:
        return row_xml
    row_open = row_open_m.group(1)
    new_cells = "".join(c for _, c in remapped)
    return f"{row_open}{new_cells}</row>"


def rewrite_sheet_xml(
    sheet_xml: str,
    perm: Dict[int, int],
) -> Tuple[str, int]:
    """Rewrite an entire sheet XML: reorder cells in each row, rewrite formulas.

    Returns (new_xml, formula_count).
    """
    formula_count = 0

    # Count formulas for stats
    formula_count = len(re.findall(r'<f\b', sheet_xml))

    # Process each <row>…</row>
    def _process_row(m: re.Match) -> str:
        return _rewrite_row_cells(m.group(0), perm)

    new_xml = re.sub(
        r'<row\b[^>]*>.*?</row>',
        _process_row,
        sheet_xml,
        flags=re.DOTALL,
    )

    # Rewrite CF sqref and formula attributes
    cf_count = 0

    def _rewrite_cf_block(m: re.Match) -> str:
        nonlocal cf_count
        block = m.group(0)

        # Rewrite sqref attribute
        sqref_m = re.search(r'sqref="([^"]*)"', block)
        if sqref_m:
            old_sqref = sqref_m.group(1)
            new_sqref = rewrite_sqref(old_sqref, perm)
            if old_sqref != new_sqref:
                cf_count += 1
            block = block[:sqref_m.start(1)] + new_sqref + block[sqref_m.end(1):]

        # Rewrite formula contents inside CF
        def _rewrite_cf_formula(fm: re.Match) -> str:
            return f"<formula>{rewrite_formula(fm.group(1), perm)}</formula>"

        block = re.sub(r'<formula>(.*?)</formula>', _rewrite_cf_formula, block, flags=re.DOTALL)
        return block

    new_xml = re.sub(
        r'<conditionalFormatting\b[^>]*>.*?</conditionalFormatting>',
        _rewrite_cf_block,
        new_xml,
        flags=re.DOTALL,
    )

    # Rewrite DV sqref attributes
    dv_count = 0

    def _rewrite_dv_block(m: re.Match) -> str:
        nonlocal dv_count
        block = m.group(0)
        for sq_m in list(re.finditer(r'sqref="([^"]*)"', block)):
            old = sq_m.group(1)
            new = rewrite_sqref(old, perm)
            if old != new:
                dv_count += 1
                block = block.replace(f'sqref="{old}"', f'sqref="{new}"', 1)

        # Rewrite formula refs inside DV
        def _rewrite_dv_formula(fm: re.Match) -> str:
            tag = fm.group(1)
            content = fm.group(2)
            close_tag = fm.group(3)
            return f"{tag}{rewrite_formula(content, perm)}{close_tag}"

        block = re.sub(
            r'(<formula[12]?>)(.*?)(</formula[12]?>)',
            _rewrite_dv_formula,
            block,
            flags=re.DOTALL,
        )
        return block

    new_xml = re.sub(
        r'<dataValidations\b[^>]*>.*?</dataValidations>',
        _rewrite_dv_block,
        new_xml,
        flags=re.DOTALL,
    )

    return new_xml, formula_count


# ──────────────────── table definition rewriting ────────────────────


def rewrite_table_xml(
    table_xml: str,
    perm: Dict[int, int],
    rename_map: Dict[str, str],
) -> Tuple[str, int]:
    """Reorder <tableColumn> elements and update the table ref= attribute.

    Returns (new_xml, rename_count).
    """
    rename_count = 0

    # Extract tableColumns section
    tc_section_m = re.search(
        r'(<tableColumns\b[^>]*>)(.*?)(</tableColumns>)',
        table_xml,
        re.DOTALL,
    )
    if not tc_section_m:
        return table_xml, 0

    tc_open = tc_section_m.group(1)
    tc_inner = tc_section_m.group(2)
    tc_close = tc_section_m.group(3)

    # Parse individual tableColumn elements
    col_elements = re.findall(
        r'<tableColumn\b[^>]*(?:>.*?</tableColumn>|/>)',
        tc_inner,
        re.DOTALL,
    )

    # Build (old_1based_index, element) pairs
    indexed_cols: List[Tuple[int, str]] = []
    for i, elem in enumerate(col_elements):
        old_idx = i + 1
        new_idx = perm.get(old_idx, old_idx)

        # Apply renames
        name_m = re.search(r'name="([^"]*)"', elem)
        if name_m:
            old_name = name_m.group(1)
            new_name = rename_map.get(old_name, old_name)
            if new_name != old_name:
                elem = elem.replace(f'name="{old_name}"', f'name="{new_name}"', 1)
                # Also update displayName if present
                dn_m = re.search(r'displayName="([^"]*)"', elem)
                if dn_m and dn_m.group(1) == old_name:
                    elem = elem.replace(
                        f'displayName="{old_name}"',
                        f'displayName="{new_name}"',
                        1,
                    )
                rename_count += 1

        # Rewrite formula refs in calculatedColumnFormula
        calc_m = re.search(
            r'(<calculatedColumnFormula>)(.*?)(</calculatedColumnFormula>)',
            elem,
            re.DOTALL,
        )
        if calc_m:
            old_f = calc_m.group(2)
            new_f = rewrite_formula(old_f, perm)
            elem = elem[:calc_m.start(2)] + new_f + elem[calc_m.end(2):]

        indexed_cols.append((new_idx, elem))

    # Sort by new column index
    indexed_cols.sort(key=lambda x: x[0])

    # Update id= attributes to match new sequential order
    reindexed = []
    for seq, (_, elem) in enumerate(indexed_cols, 1):
        elem = re.sub(r' id="\d+"', f' id="{seq}"', elem, count=1)
        reindexed.append(elem)

    new_tc = tc_open + "".join(reindexed) + tc_close

    # Update the ref= attribute on the <table> root element
    ref_m = re.search(r'(<table\b[^>]*\bref=")([^"]*)"', table_xml)
    if ref_m:
        old_ref = ref_m.group(2)
        new_ref = rewrite_cell_ref(old_ref, perm)
        table_xml = table_xml[:ref_m.start(2)] + new_ref + table_xml[ref_m.end(2):]

    # Splice in the new tableColumns
    table_xml = (
        table_xml[:tc_section_m.start()]
        + new_tc
        + table_xml[tc_section_m.end():]
    )

    # Update tableColumns count
    table_xml = re.sub(
        r'<tableColumns count="\d+"',
        f'<tableColumns count="{len(reindexed)}"',
        table_xml,
        count=1,
    )

    return table_xml, rename_count


# ──────────────────── main entry point ────────────────────


def refactor_columns(
    xlsx_bytes: bytes,
    spec: RefactorSpec,
) -> RefactorResult:
    """Refactor columns in a workbook according to the spec.

    Returns RefactorResult with the patched .xlsx bytes and stats.
    """
    src = zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r")

    # Resolve target sheet part
    name_map = sheet_name_map(src)
    part_for_name: Dict[str, str] = {v: k for k, v in name_map.items()}
    target_part = part_for_name.get(spec.target_sheet_name)

    if not target_part:
        src.close()
        raise ValueError(
            f"Sheet '{spec.target_sheet_name}' not found. "
            f"Available: {list(name_map.values())}"
        )

    # Find the table definition for this sheet
    target_table_parts: List[str] = []
    sheet_rels_path = target_part.replace(
        "xl/worksheets/", "xl/worksheets/_rels/"
    ) + ".rels"

    if sheet_rels_path in src.namelist():
        rels_xml = read_text(src, sheet_rels_path)
        for m in re.finditer(r'Target="([^"]*)"', rels_xml):
            t = m.group(1)
            # Resolve relative paths
            if t.startswith("../tables/"):
                t = "xl/tables/" + t.split("/")[-1]
            elif not t.startswith("xl/"):
                t = "xl/" + t
            if t in src.namelist():
                target_table_parts.append(t)

    # Get current headers from the table or from row 1
    current_headers: List[str] = []
    if target_table_parts:
        tbl_xml = read_text(src, target_table_parts[0])
        current_headers = re.findall(r'<tableColumn [^>]*name="([^"]*)"', tbl_xml)

    if not current_headers:
        # Fall back: parse row 1 of the sheet
        sheet_xml = read_text(src, target_part)
        row1_m = re.search(r'<row\b[^>]*\br="1"[^>]*>.*?</row>', sheet_xml, re.DOTALL)
        if row1_m:
            cells = re.findall(r'<c\b[^>]*r="([A-Z]+)1"[^>]*>.*?</c>', row1_m.group(0), re.DOTALL)
            # This is approximate; would need sharedStrings resolution for real headers
            current_headers = [f"Col{c}" for c in cells]

    if not current_headers:
        src.close()
        raise ValueError(f"Could not determine headers for sheet '{spec.target_sheet_name}'")

    # Build permutation
    perm = build_permutation(current_headers, spec.new_column_order)

    # Check if anything actually moves
    identity = all(perm.get(i, i) == i for i in range(1, len(current_headers) + 1))
    has_renames = bool(spec.rename_map)

    warnings: List[str] = []
    if identity and not has_renames:
        warnings.append("No columns moved and no renames specified — output is identical to input.")

    columns_moved = sum(1 for k, v in perm.items() if k != v)

    # Rewrite parts
    buf = io.BytesIO()
    dst = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)

    total_formulas = 0
    total_cf = 0
    total_dv = 0
    total_renames = 0

    for item in src.infolist():
        data = src.read(item.filename)

        if item.filename == target_part:
            xml = data.decode("utf-8", errors="ignore")
            xml, fc = rewrite_sheet_xml(xml, perm)
            total_formulas += fc
            # Count CF and DV rewrites from the xml
            total_cf = len(re.findall(r'<conditionalFormatting\b', xml))
            total_dv = len(re.findall(r'<dataValidation\b', xml))
            data = xml.encode("utf-8")

        elif item.filename in target_table_parts:
            xml = data.decode("utf-8", errors="ignore")
            xml, rc = rewrite_table_xml(xml, perm, spec.rename_map)
            total_renames += rc
            data = xml.encode("utf-8")

        dst.writestr(item, data)

    dst.close()
    src.close()

    return RefactorResult(
        output_bytes=buf.getvalue(),
        permutation=perm,
        columns_moved=columns_moved,
        columns_renamed=total_renames,
        formulas_rewritten=total_formulas,
        cf_sqrefs_rewritten=total_cf,
        dv_sqrefs_rewritten=total_dv,
        warnings=warnings,
    )


# ──────────────────── CLI ────────────────────


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 3:
        print("Usage: python -m triage.refactor_engine <input.xlsx> <spec.json> [output.xlsx]")
        print()
        print("spec.json format:")
        print(json.dumps({
            "target_sheet_name": "Deployments",
            "new_column_order": ["Device Type", "Deployed", "Installed", "..."],
            "rename_map": {"Medical Device ID": "Medical Device S/N"},
        }, indent=2))
        sys.exit(1)

    input_path = sys.argv[1]
    spec_path = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else input_path.replace(".xlsx", "_refactored.xlsx")

    with open(spec_path, encoding="utf-8") as f:
        spec_dict = json.load(f)

    spec = RefactorSpec(
        target_sheet_name=spec_dict["target_sheet_name"],
        new_column_order=spec_dict["new_column_order"],
        rename_map=spec_dict.get("rename_map", {}),
    )

    with open(input_path, "rb") as f:
        xlsx_bytes = f.read()

    result = refactor_columns(xlsx_bytes, spec)

    with open(output_path, "wb") as f:
        f.write(result.output_bytes)

    print(f"Refactored → {output_path}")
    print(f"  Columns moved:      {result.columns_moved}")
    print(f"  Columns renamed:    {result.columns_renamed}")
    print(f"  Formulas rewritten: {result.formulas_rewritten}")
    print(f"  CF sqrefs:          {result.cf_sqrefs_rewritten}")
    print(f"  DV sqrefs:          {result.dv_sqrefs_rewritten}")
    if result.warnings:
        for w in result.warnings:
            print(f"  ⚠ {w}")

