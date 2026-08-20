"""Minimal deterministic OOXML primitives for qualitative admin NTH workbooks."""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from .model import Cell, THEME_PATH, _num, load_profile

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

def _cell_xml(cell: Cell) -> str:
    attrs = [f'r="{cell.ref}"', f's="{cell.style}"']
    if cell.value is None:
        return f"<c {' '.join(attrs)}/>"
    kind = cell.kind or ("n" if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool) else "str")
    if kind == "n":
        attrs.append('t="n"'); value = _num(cell.value)
    else:
        attrs.append('t="str"'); value = escape(str(cell.value))
    return f"<c {' '.join(attrs)}><v>{value}</v></c>"

def _row_xml(row_num: int, cells: Sequence[Cell], *, title: bool = False) -> str:
    attrs = f'r="{row_num}"' + (' ht="30" customHeight="1"' if title else '')
    return f"<row {attrs}>" + "".join(_cell_xml(cell) for cell in cells) + "</row>"

def _letters(start: str, end: str) -> list[str]:
    def n(col: str) -> int:
        out=0
        for ch in col: out=out*26+ord(ch.upper())-64
        return out
    def col(num: int) -> str:
        chars=[]
        while num:
            num,rem=divmod(num-1,26); chars.append(chr(65+rem))
        return "".join(reversed(chars))
    return [col(i) for i in range(n(start),n(end)+1)]

def _merged_cells(ref: str, row: int, style: int, value: Any) -> list[Cell]:
    start,end=ref.split(":")
    start_col=re.match(r"[A-Z]+",start).group(0); end_col=re.match(r"[A-Z]+",end).group(0)  # type: ignore[union-attr]
    start_row=int(re.search(r"\d+",start).group(0)); end_row=int(re.search(r"\d+",end).group(0))  # type: ignore[union-attr]
    cells=[]
    for r in range(start_row,end_row+1):
        for col in _letters(start_col,end_col):
            cells.append(Cell(f"{col}{r}",style,value if (r==row and col==start_col) else None))
    return cells

def _columns_xml(widths: Sequence[float]) -> str:
    return "<cols>"+"".join(f'<col min="{idx}" max="{idx}" width="{_num(width)}" customWidth="1"/>' for idx,width in enumerate(widths,1))+"</cols>"

def _worksheet_xml(widths: Sequence[float], rows: Mapping[int, Sequence[Cell]], merges: Sequence[str]) -> bytes:
    sheet_rows="".join(_row_xml(r,rows[r],title=(r==1)) for r in sorted(rows))
    merge_xml=(f'<mergeCells count="{len(merges)}">'+"".join(f'<mergeCell ref="{ref}"/>' for ref in merges)+"</mergeCells>") if merges else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<worksheet xmlns="{MAIN_NS}"><sheetFormatPr defaultRowHeight="15"/>{_columns_xml(widths)}<sheetData>{sheet_rows}</sheetData>{merge_xml}</worksheet>').encode("utf-8")

def _add_merged(rows: dict[int,list[Cell]], merges: list[str], ref: str, style: int, value: Any) -> None:
    merges.append(ref)
    start_row=int(re.search(r"\d+",ref.split(":",1)[0]).group(0))  # type: ignore[union-attr]
    for cell in _merged_cells(ref,start_row,style,value):
        row_num=int(re.search(r"\d+",cell.ref).group(0)); rows.setdefault(row_num,[]).append(cell)  # type: ignore[union-attr]

def _sheet_title_prefix(spec: Mapping[str, Any]) -> str:
    return f"{spec['month_label']} MTD" if spec["mode"]=="month_to_date" else spec["month_label"]

def _completed_billing_status(total: float, baseline: float | None) -> str:
    if baseline is None: return f"NO PRIOR BASELINE PROVIDED — current NTH {_num(total)}"
    state="ALIGNED" if abs(total-baseline)<1e-9 else "REVIEW"
    return f"{state} — current NTH {_num(total)}; prior baseline {_num(baseline)}"

def _sheet_names(spec: Mapping[str, Any]) -> list[str]:
    return [name.replace("{month_label}",spec["month_label"]) for name in load_profile()["mode_contracts"][spec["mode"]]["sheet_order"]]

def _workbook_xml(sheet_names: Sequence[str]) -> bytes:
    sheets="".join(f'<sheet name="{escape(name)}" sheetId="{idx}" r:id="rId{idx}"/>' for idx,name in enumerate(sheet_names,1))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<workbook xmlns="{MAIN_NS}" xmlns:r="{REL_NS}"><sheets>{sheets}</sheets></workbook>').encode("utf-8")

def _workbook_rels(sheet_count: int) -> bytes:
    rels=[f'<Relationship Id="rId{idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{idx}.xml"/>' for idx in range(1,sheet_count+1)]
    rels.extend([f'<Relationship Id="rId{sheet_count+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',f'<Relationship Id="rId{sheet_count+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>',f'<Relationship Id="rId{sheet_count+3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'])
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<Relationships xmlns="{PKG_REL_NS}">'+"".join(rels)+"</Relationships>").encode("utf-8")

def _root_rels() -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<Relationships xmlns="{PKG_REL_NS}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>').encode("utf-8")

def _content_types(sheet_count: int) -> bytes:
    overrides=['<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>','<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>','<Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>','<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>']
    overrides.extend(f'<Override PartName="/xl/worksheets/sheet{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for idx in range(1,sheet_count+1))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'<Types xmlns="{CONTENT_NS}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'+"".join(overrides)+'</Types>').encode("utf-8")

def _zip_write(zf: ZipFile, name: str, data: bytes) -> None:
    info=ZipInfo(name,date_time=(1980,1,1,0,0,0)); info.compress_type=ZIP_DEFLATED; info.external_attr=0o600<<16; zf.writestr(info,data)
