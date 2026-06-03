"""
triage/xlsx_utils.py
--------------------
Shared helpers for reading and manipulating .xlsx (OOXML ZIP) packages.
Used by gate_checks, dv_engine, cf_engine, and other triage modules.
"""
from __future__ import annotations

import html as _html
import io
import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ─────────────────────── ZIP / part helpers ───────────────────────


def read_text(z: zipfile.ZipFile, name: str) -> str:
    """Read a ZIP part as UTF-8 text (lossy)."""
    return z.read(name).decode("utf-8", errors="ignore")


def read_bytes(z: zipfile.ZipFile, name: str) -> bytes:
    """Read a ZIP part as raw bytes."""
    return z.read(name)


def sheet_parts(z: zipfile.ZipFile) -> List[str]:
    """Return sorted list of worksheet part paths in the ZIP."""
    return sorted(
        n for n in z.namelist()
        if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
    )


def table_parts(z: zipfile.ZipFile) -> List[str]:
    """Return sorted list of table part paths in the ZIP."""
    return sorted(
        n for n in z.namelist()
        if n.startswith("xl/tables/table") and n.endswith(".xml")
    )


# ─────────────────────── sheet-name mapping ───────────────────────


def _normalize_rel_target(target: str) -> str:
    """Normalize a .rels Target attribute to a ZIP part-ish path.

    Excel writes worksheet relationship targets in multiple forms:
    - "worksheets/sheet1.xml" (relative)
    - "xl/worksheets/sheet1.xml" (already rooted)
    - "/xl/worksheets/sheet1.xml" (absolute, leading slash)
    """
    t = (target or "").strip().replace("\\", "/")
    # Relationship Targets may be absolute within the package (leading '/').
    # ZIP member names never start with '/'.
    while t.startswith("/"):
        t = t[1:]
    return t


def sheet_name_map(z: zipfile.ZipFile) -> Dict[str, str]:
    """Return {part_path: sheet_display_name} mapping.

    Parses workbook.xml + workbook.xml.rels to resolve rId → part.
    """
    wb = read_text(z, "xl/workbook.xml")
    rels = read_text(z, "xl/_rels/workbook.xml.rels")

    # rId → target
    # Attribute order in workbook.xml.rels is not stable (Target may precede Id).
    rid_target: Dict[str, str] = {}
    for m in re.finditer(r"<Relationship\b[^>]*>", rels):
        frag = m.group(0)
        rid = get_attr(frag, "Id")
        target = get_attr(frag, "Target")
        if rid and target:
            rid_target[rid] = _normalize_rel_target(target)

    # sheet name → rId
    mapping: Dict[str, str] = {}
    for m in re.finditer(r"<sheet\b[^>]*>", wb):
        frag = m.group(0)
        name = get_attr(frag, "name")
        rid = get_attr(frag, "r:id")
        if not name or not rid:
            continue
        target = rid_target.get(rid, "")
        if not target:
            continue
        part = target if target.startswith("xl/") else ("xl/" + target)
        mapping[part] = name

    return mapping


def sheet_index_map(z: zipfile.ZipFile) -> Dict[str, int]:
    """Return {part_path: 0-based tab index} mapping."""
    wb = read_text(z, "xl/workbook.xml")
    rels = read_text(z, "xl/_rels/workbook.xml.rels")

    rid_target: Dict[str, str] = {}
    for m in re.finditer(r"<Relationship\b[^>]*>", rels):
        frag = m.group(0)
        rid = get_attr(frag, "Id")
        target = get_attr(frag, "Target")
        if rid and target:
            rid_target[rid] = _normalize_rel_target(target)

    result: Dict[str, int] = {}
    sheet_tags = list(re.finditer(r"<sheet\b[^>]*>", wb))
    for idx, m in enumerate(sheet_tags):
        frag = m.group(0)
        rid = get_attr(frag, "r:id")
        if not rid:
            continue
        target = rid_target.get(rid, "")
        if not target:
            continue
        part = target if target.startswith("xl/") else ("xl/" + target)
        result[part] = idx

    return result


# ─────────────────────── cell / column helpers ───────────────────────


def col_to_num(col: str) -> int:
    """A→1, B→2, …, Z→26, AA→27, …"""
    n = 0
    for ch in col.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n: int) -> str:
    """1→A, 2→B, …, 26→Z, 27→AA, …"""
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def parse_ref(ref: str) -> Optional[Tuple[str, int, str, int]]:
    """Parse 'A1:Z99' → ('A', 1, 'Z', 99) or None."""
    m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", ref)
    if not m:
        return None
    return m.group(1), int(m.group(2)), m.group(3), int(m.group(4))


def max_row(xml: str) -> int:
    """Find the highest row number referenced in a sheet XML."""
    rows = [int(m.group(1)) for m in re.finditer(r'<row[^>]*\br="(\d+)"', xml)]
    return max(rows) if rows else 0


# ─────────────────── XML block extraction ────────────────────


def extract_blocks(xml: str, tag: str) -> List[str]:
    """Extract all occurrences of <tag …>…</tag> from XML text."""
    pattern = rf"<{tag}\b[^>]*>.*?</{tag}>"
    return re.findall(pattern, xml, re.DOTALL)


def extract_blocks_with_pos(xml: str, tag: str) -> List[Tuple[str, int, int]]:
    """Extract (block_text, start, end) for each <tag>…</tag> occurrence."""
    pattern = rf"<{tag}\b[^>]*>.*?</{tag}>"
    return [(m.group(0), m.start(), m.end()) for m in re.finditer(pattern, xml, re.DOTALL)]


def extract_self_closing(xml: str, tag: str) -> List[str]:
    """Extract all <tag … /> self-closing elements."""
    pattern = rf"<{tag}\b[^/]*/>"
    return re.findall(pattern, xml, re.DOTALL)


def get_attr(xml_fragment: str, attr: str) -> Optional[str]:
    """Extract the value of an attribute from an XML fragment."""
    m = re.search(rf'{attr}="([^"]*)"', xml_fragment)
    return m.group(1) if m else None


# ─────────────────────── inlineStr repair ───────────────────────────


def fix_inlinestr(path: str) -> None:
    """
    Post-process an openpyxl-generated XLSX to eliminate all inlineStr tokens.

    Web Excel treats ``inlineStr`` as a stop-ship token. Rewrites worksheet XMLs
    in-place and rebuilds sharedStrings when needed.
    """
    _IS_FULL = re.compile(
        rb'(<c\b[^>]*?)\s+t="inlineStr"([^>]*?)><is><t([^>]*)>(.*?)</t></is></c>',
        re.DOTALL,
    )
    _IS_EMPTY = re.compile(rb'\s+t="inlineStr"(?=[^<]*?/>|[^<]*?></c>)')

    p = Path(path)
    original = p.read_bytes()

    with zipfile.ZipFile(io.BytesIO(original), "r") as zin:
        names = zin.namelist()
        str_table: List[str] = []
        str_index: Dict[str, int] = {}

        if "xl/sharedStrings.xml" in names:
            ss_xml = zin.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
            for m in re.finditer(r"<t[^>]*?>(.*?)</t>", ss_xml, re.DOTALL):
                s = _html.unescape(m.group(1))
                if s not in str_index:
                    str_index[s] = len(str_table)
                    str_table.append(s)

        def _get_or_add(s: str) -> int:
            if s not in str_index:
                str_index[s] = len(str_table)
                str_table.append(s)
            return str_index[s]

        patched: Dict[str, bytes] = {}
        for name in names:
            if not (name.startswith("xl/worksheets/sheet") and name.endswith(".xml")):
                continue
            raw = zin.read(name)
            if b"inlineStr" not in raw:
                continue

            def _replace_full(m: re.Match) -> bytes:
                prefix = m.group(1) + m.group(2)
                value = _html.unescape(m.group(4).decode("utf-8", errors="ignore"))
                idx = _get_or_add(value)
                return prefix + b' t="s"><v>' + str(idx).encode() + b"</v></c>"

            fixed = _IS_FULL.sub(_replace_full, raw)
            fixed = _IS_EMPTY.sub(b"", fixed)
            if fixed != raw:
                patched[name] = fixed

        if not patched:
            return

        def _ss_item(s: str) -> str:
            preserve = ' xml:space="preserve"' if s != s.strip() else ""
            return f"<si><t{preserve}>{_xml_escape(s)}</t></si>"

        ss_items = "".join(_ss_item(s) for s in str_table)
        total_refs = 0
        for name in names:
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                raw_ws = patched.get(name) or zin.read(name)
                total_refs += raw_ws.count(b't="s"')
        unique = len(str_table)
        new_ss = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            f' count="{total_refs or unique}" uniqueCount="{unique}">{ss_items}</sst>'
        ).encode("utf-8")

        need_new_ss = "xl/sharedStrings.xml" not in names and bool(str_table)
        extra: Dict[str, bytes] = {}
        if need_new_ss:
            extra["xl/sharedStrings.xml"] = new_ss
            ct_name = "[Content_Types].xml"
            if ct_name in names:
                ct = zin.read(ct_name).decode("utf-8")
                if "sharedStrings" not in ct:
                    ct = ct.replace(
                        "</Types>",
                        '<Override PartName="/xl/sharedStrings.xml"'
                        ' ContentType="application/vnd.openxmlformats-officedocument'
                        ".spreadsheetml.sharedStrings+xml\"/></Types>",
                    )
                    extra[ct_name] = ct.encode("utf-8")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                if name in patched:
                    zout.writestr(name, patched[name])
                elif name == "xl/sharedStrings.xml":
                    zout.writestr(name, new_ss)
                elif name in extra:
                    zout.writestr(name, extra[name])
                else:
                    zout.writestr(name, zin.read(name))
            for name, data in extra.items():
                if name not in names:
                    zout.writestr(name, data)

        p.write_bytes(buf.getvalue())


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

