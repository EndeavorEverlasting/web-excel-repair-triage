"""CF priority allocation for operator Live CF append."""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path
from typing import List

from triage.xlsx_utils import read_text, sheet_parts, sheet_name_map

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs" / "roster_log_review_queue"


def load_cf_markers() -> List[str]:
    path = _CONFIG_DIR / "cf_markers.json"
    if not path.exists():
        return [
            'AND($A3<>"",$B3="")',
            'OR($C3="",$D3="")',
            'MOD($D3-$C3,1)*24>=12',
            'SEARCH("PTO"',
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("formula_substrings", []))


def _sheet_has_operator_cf(xml: str, markers: List[str]) -> bool:
    if not markers:
        return False
    return any(m in xml for m in markers)


def max_operator_priority(xlsx_bytes: bytes, markers: List[str] | None = None) -> int:
    """Highest priority among existing operator CF rules (marker match)."""
    markers = markers or load_cf_markers()
    max_pri = 0
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        for part in sheet_parts(z):
            xml = read_text(z, part)
            if not _sheet_has_operator_cf(xml, markers):
                continue
            for block in re.findall(
                r"<conditionalFormatting\b[^>]*>.*?</conditionalFormatting>",
                xml,
                re.DOTALL,
            ):
                if not any(m in block for m in markers):
                    continue
                for pri in re.findall(r'priority="(\d+)"', block):
                    max_pri = max(max_pri, int(pri))
    return max_pri


def next_priority_start(xlsx_bytes: bytes) -> int:
    """Next priority for appended operator CF (1 if none present)."""
    mx = max_operator_priority(xlsx_bytes)
    return 1 if mx == 0 else mx + 1


def live_sheet_names_in_order(xlsx_bytes: bytes) -> List[str]:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        name_map = sheet_name_map(z)
        wb = read_text(z, "xl/workbook.xml")
        names: List[str] = []
        for m in re.finditer(r'<sheet\b[^>]*name="([^"]+)"', wb):
            n = m.group(1)
            if n.startswith("Live - "):
                names.append(n)
        # preserve workbook.xml order; filter only Live tabs
        return names


def sheet_part_for_name(xlsx_bytes: bytes, sheet_name: str) -> str:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        for part, name in sheet_name_map(z).items():
            if name == sheet_name:
                return part
    raise KeyError(sheet_name)


def count_cf_groups(xlsx_bytes: bytes, sheet_name: str) -> int:
    part = sheet_part_for_name(xlsx_bytes, sheet_name)
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        xml = read_text(z, part)
    return len(re.findall(r"<conditionalFormatting\b", xml))
