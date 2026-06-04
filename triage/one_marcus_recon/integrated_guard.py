"""Detect integrated multi-sheet workbooks unsuitable for clean-render generate mode."""
from __future__ import annotations

from typing import List, Tuple

import openpyxl

from .config import EXPECTED_SHEETS


class IntegratedWorkbookError(ValueError):
    """Raised when generate mode is invoked on a full integrated workbook."""


def inspect_workbook_sheets(path: str) -> List[str]:
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def assert_generate_allowed(input_path: str) -> List[str]:
    """Refuse generate on integrated workbooks; return sheet names when allowed."""
    names = inspect_workbook_sheets(input_path)
    if len(names) > len(EXPECTED_SHEETS):
        raise IntegratedWorkbookError(
            f"integrated workbook has {len(names)} sheets; "
            f"use relink mode to preserve sheets (generate destroys non-target tabs)"
        )
    extra = [n for n in names if n not in EXPECTED_SHEETS]
    if extra:
        raise IntegratedWorkbookError(
            f"unexpected sheets {extra}; use relink mode for integrated workbooks"
        )
    return names
