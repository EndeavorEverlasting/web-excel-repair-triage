"""Preflight checks for roster log review queue graft output."""
from __future__ import annotations

import io
import re
import zipfile
from typing import Any, Dict, List

from triage.xlsx_utils import read_text, sheet_name_map

from .priority_allocator import load_cf_markers

INSERTED_SHEETS = (
    "Review Dashboard",
    "Review Queue",
    "Review Rules",
    "CF Dictionary",
)

_FRAGILE_MARKERS = (
    ("tableParts", r"<tableParts\b"),
    ("comments", r"<legacyDrawing\b|<commentList\b"),
    ("hyperlinks", r"<hyperlinks\b"),
    ("legacyDrawing", r"<legacyDrawing\b"),
)


def _first_sheet_name(xlsx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        wb = read_text(z, "xl/workbook.xml")
    m = re.search(r'<sheet\b[^>]*name="([^"]+)"', wb)
    return m.group(1) if m else ""


def _inserted_sheet_fragile_objects(xlsx_bytes: bytes) -> Dict[str, Dict[str, bool]]:
    result: Dict[str, Dict[str, bool]] = {}
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        name_map = sheet_name_map(z)
        part_by_name = {v: k for k, v in name_map.items()}
        for sheet in INSERTED_SHEETS:
            part = part_by_name.get(sheet)
            flags = {k: False for k, _ in _FRAGILE_MARKERS}
            if part and part in z.namelist():
                xml = read_text(z, part)
                for key, pat in _FRAGILE_MARKERS:
                    flags[key] = bool(re.search(pat, xml))
            result[sheet] = flags
    return result


def _live_tabs_missing_markers(xlsx_bytes: bytes) -> List[str]:
    markers = load_cf_markers()
    missing: List[str] = []
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        name_map = sheet_name_map(z)
        for part, name in name_map.items():
            if not name.startswith("Live - "):
                continue
            xml = read_text(z, part)
            if not any(m in xml for m in markers):
                missing.append(name)
    return missing


def _has_external_links(xlsx_bytes: bytes) -> bool:
    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        if any(n.startswith("xl/externalLinks/") for n in z.namelist()):
            return True
        if "xl/workbook.xml" in z.namelist():
            wb = read_text(z, "xl/workbook.xml")
            if "externalReference" in wb:
                return True
    return False


def run_preflight(
    xlsx_bytes: bytes,
    *,
    require_review_layer: bool = True,
) -> Dict[str, Any]:
    """Return verification block; raises ValueError if stop-ship checks fail."""
    errors: List[str] = []
    first = _first_sheet_name(xlsx_bytes)
    if require_review_layer and first != "Review Dashboard":
        errors.append(f"review_dashboard_first: expected 'Review Dashboard', got {first!r}")

    missing_cf = _live_tabs_missing_markers(xlsx_bytes)
    if missing_cf:
        errors.append(f"live_cf_global_present: missing markers on {missing_cf}")

    if _has_external_links(xlsx_bytes):
        errors.append("no_external_links: external link parts found")

    fragile = _inserted_sheet_fragile_objects(xlsx_bytes) if require_review_layer else {}

    if require_review_layer:
        for sheet, flags in fragile.items():
            if any(flags.values()):
                errors.append(f"inserted_sheets_clean: {sheet} has fragile objects {flags}")

    verification: Dict[str, Any] = {
        "review_dashboard_first": first == "Review Dashboard",
        "no_external_links": not _has_external_links(xlsx_bytes),
        "inserted_sheet_fragile_objects": fragile,
        "all_live_tabs_patched": len(missing_cf) == 0,
        "live_tabs_patched_count": 0,
    }

    with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as z:
        name_map = sheet_name_map(z)
        verification["live_tabs_patched_count"] = sum(
            1 for n in name_map.values() if n.startswith("Live - ")
        )

    if errors:
        raise ValueError("; ".join(errors))

    return verification
