"""Config loaders and layout constants for the One Marcus recon generator."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

from triage.spreadsheet_style import style_config

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INVENTORY_VISUAL_PATH = _REPO_ROOT / "configs" / "inventory_visual_aid_chart_v1.json"

EXPECTED_SHEETS: Tuple[str, ...] = ("Part Numbers", "1M Recon Pivot Module")
PIVOT_SHEET = "1M Recon Pivot Module"
PART_NUMBERS_SHEET = "Part Numbers"

TECH_COL_START = 1  # A
TECH_COL_END = 18  # R
HELPER_COL_START = 19  # S
HELPER_COL_END = 29  # AC

PN_HEADER_ROW = 1
PN_DATA_START = 2
PN_DATA_END = 500

ROLLUP_HEADER_ROW = 12
ROLLUP_DATA_START = 13
ROLLUP_DATA_END = 190

# Part Numbers helper column indices (1-based).
COL_PIVOT_KEY = 19  # S PivotPartKey
COL_QTY_NUM = 20  # T QtyNum
COL_INCLUDE = 26  # Z IncludeFlag

FORBIDDEN_WORKBOOK_TEXT = (
    "%20",
    "web excel-safe",
    "webexcel-safe",
    "websafe",
    "excel for web safe",
)

ROLLUP_HEADERS: Tuple[str, ...] = (
    "Inventory Rollup by Item",
    "Total Qty",
    "Visual",
    "Lines",
    "Redeployable",
    "Hold Qty",
    "Verify Qty",
    "Cleanup Lines",
)


@lru_cache(maxsize=1)
def load_inventory_visual_config() -> Dict[str, Any]:
    with _INVENTORY_VISUAL_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def visual_font_color() -> str:
    cfg = load_inventory_visual_config()
    return str(cfg.get("executive_visual_field", {}).get("font_color", "FF2563EB"))


def load_style_config() -> Dict[str, Any]:
    return style_config()
