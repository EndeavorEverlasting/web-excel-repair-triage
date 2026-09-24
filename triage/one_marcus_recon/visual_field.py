"""Executive rollup and Visual field formula builders."""
from __future__ import annotations

from typing import List

from .config import PART_NUMBERS_SHEET, ROLLUP_DATA_START, ROLLUP_HEADER_ROW, ROLLUP_HEADERS


def visual_formula(row: int, first_data_row: int, last_data_row: int) -> str:
    """In-cell REPT bar scaled to the rollup qty column."""
    return (
        f'=IF(B{row}>0,REPT("\u2588",MAX(1,ROUND(B{row}/MAX($B${first_data_row}:$B${last_data_row})*18,0))),"")'
    )


def total_qty_formula(row: int, key_cell: str, pn_tab: str, pn_last_row: int) -> str:
    return (
        f'=SUMIFS(\'{pn_tab}\'!$T$2:$T${pn_last_row},'
        f'\'{pn_tab}\'!$Z$2:$Z${pn_last_row},"Include",'
        f'\'{pn_tab}\'!$S$2:$S${pn_last_row},{key_cell})'
    )


def line_count_formula(row: int, key_cell: str, pn_tab: str, pn_last_row: int) -> str:
    return (
        f'=COUNTIFS(\'{pn_tab}\'!$Z$2:$Z${pn_last_row},"Include",'
        f'\'{pn_tab}\'!$S$2:$S${pn_last_row},{key_cell})'
    )


def write_rollup_table(
    ws,
    keys: List[str],
    *,
    pn_tab: str = PART_NUMBERS_SHEET,
    pn_last_row: int = 500,
) -> int:
    """Write rollup headers and data rows; return last data row index."""
    for col, title in enumerate(ROLLUP_HEADERS, start=1):
        ws.cell(ROLLUP_HEADER_ROW, col, title)
    if not keys:
        return ROLLUP_DATA_START - 1
    first = ROLLUP_DATA_START
    last = ROLLUP_DATA_START + len(keys) - 1
    for i, key in enumerate(keys):
        row = ROLLUP_DATA_START + i
        ws.cell(row, 1, key)
        key_ref = f"A{row}"
        ws.cell(row, 2, total_qty_formula(row, key_ref, pn_tab, pn_last_row))
        ws.cell(row, 3, visual_formula(row, first, last))
        ws.cell(row, 4, line_count_formula(row, key_ref, pn_tab, pn_last_row))
    return last
