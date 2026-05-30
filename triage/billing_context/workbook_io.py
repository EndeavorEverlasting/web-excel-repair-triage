from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet


def load_xlsx(path: str | Path, data_only: bool = True):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Workbook not found: {p}")
    return load_workbook(p, data_only=data_only)


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("\n", " ").replace("\r", " ")


def header_map(ws: Worksheet, header_row: int = 1) -> dict[str, int]:
    headers: dict[str, int] = {}
    for cell in ws[header_row]:
        name = normalize_header(cell.value)
        if name:
            headers[name] = cell.column
    return headers


def iter_dict_rows(ws: Worksheet, header_row: int = 1) -> Iterable[dict[str, Any]]:
    headers = header_map(ws, header_row)
    reverse = {col: name for name, col in headers.items()}

    for r in range(header_row + 1, ws.max_row + 1):
        row: dict[str, Any] = {}
        empty = True
        for col, name in reverse.items():
            value = ws.cell(r, col).value
            if value not in (None, ""):
                empty = False
            row[name] = value
        if not empty:
            row["_row_number"] = r
            yield row


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return default


def sheet_names(path: str | Path) -> list[str]:
    wb = load_xlsx(path)
    names = list(wb.sheetnames)
    wb.close()
    return names
