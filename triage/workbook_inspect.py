"""Lightweight workbook inspection utilities.

Purpose: quickly detect "blank tab" symptoms without opening Excel by
counting rows/cells and key blocks (CF/DV/tableParts) in sheet XML.

No XML parser; works on raw OOXML bytes for fidelity.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from triage.xlsx_utils import read_bytes, read_text, sheet_index_map, sheet_name_map


@dataclass(frozen=True)
class SheetStats:
    index: int
    name: str
    part: str
    bytes_len: int
    row_tags: int
    cell_tags: int
    table_parts: int
    cf_blocks: int
    dv_blocks: int
    empty_sheetdata: bool


def _active_tab_index(workbook_xml: str) -> Optional[int]:
    m = re.search(r'<workbookView[^>]*\bactiveTab="(\d+)"', workbook_xml)
    return int(m.group(1)) if m else None


def _sheet_xml_stats(raw: bytes, *, idx: int, name: str, part: str) -> SheetStats:
    """Compute quick counts from raw XML bytes.

    We avoid full UTF-8 decoding for speed; the tags we count are ASCII.
    """
    # <sheetData/> can appear with optional space: <sheetData />
    empty_sheetdata = (b"<sheetData/>" in raw) or (b"<sheetData />" in raw)
    return SheetStats(
        index=idx,
        name=name,
        part=part,
        bytes_len=len(raw),
        row_tags=raw.count(b"<row"),
        cell_tags=raw.count(b"<c"),
        table_parts=raw.count(b"<tablePart"),
        cf_blocks=raw.count(b"<conditionalFormatting"),
        dv_blocks=raw.count(b"<dataValidations"),
        empty_sheetdata=empty_sheetdata,
    )


def inspect_workbook(path: str | Path) -> Dict[str, object]:
    """Return a dict summary suitable for JSON serialization."""
    p = Path(path)
    with zipfile.ZipFile(p, "r") as z:
        wb_xml = read_text(z, "xl/workbook.xml")
        active = _active_tab_index(wb_xml)

        part_to_name = sheet_name_map(z)
        part_to_idx = sheet_index_map(z)

        sheets: List[SheetStats] = []
        for part, idx in sorted(part_to_idx.items(), key=lambda kv: kv[1]):
            if part not in z.namelist():
                continue
            name = part_to_name.get(part, part)
            raw = read_bytes(z, part)
            sheets.append(_sheet_xml_stats(raw, idx=idx, name=name, part=part))

    return {
        "path": str(p),
        "activeTab": active,
        "sheetCount": len(sheets),
        "sheets": [s.__dict__ for s in sheets],
    }


def _print_summary(path: str | Path, *, name_filter: Optional[str] = None) -> None:
    info = inspect_workbook(path)
    sheets = info["sheets"]
    active = info.get("activeTab")
    print(f"\n== {info['path']}")
    print(f"sheets={info['sheetCount']} activeTab={active}")
    for s in sheets:
        nm = s["name"]
        if name_filter and (name_filter.lower() not in nm.lower()):
            continue
        flags = []
        if active is not None and s["index"] == active:
            flags.append("ACTIVE")
        if s["cell_tags"] == 0 or s["empty_sheetdata"]:
            flags.append("EMPTY")
        if re.search("deploy", nm, re.I):
            flags.append("DEPLOY?")
        flag_s = (" [" + ",".join(flags) + "]") if flags else ""
        print(
            f"  {s['index']:02d} {nm:45s} cells={s['cell_tags']:6d} rows={s['row_tags']:5d} "
            f"CF={s['cf_blocks']:4d} DV={s['dv_blocks']:3d} tblParts={s['table_parts']:3d}{flag_s}"
        )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help=".xlsx files to inspect")
    ap.add_argument("--filter", default=None, help="only print sheets whose name contains this substring")
    args = ap.parse_args()

    for p in args.paths:
        _print_summary(p, name_filter=args.filter)
