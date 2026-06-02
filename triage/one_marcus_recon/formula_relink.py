"""Tab detection/rename and formula reference rewiring.

Operates on decoded XML text of package parts. The engine never reserializes
the workbook through a high-level library; it edits the OOXML in place so
tables, drawings, styles, filters, and validation are preserved.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# Ordered <sheet .../> tags inside xl/workbook.xml.
_SHEET_TAG = re.compile(r"<sheet\b[^>]*/>|<sheet\b[^>]*>")
_NAME_ATTR = re.compile(r'name="([^"]*)"')

# A dated Part Numbers reference inside a formula, optionally external-indexed:
#   'M-D-YYYY Part Numbers'!     or    [1]'M-D-YYYY Part Numbers'!
_DATED_REF = re.compile(
    r"(?:\[(?P<idx>\d+)\])?'(?P<name>\d{1,2}-\d{1,2}-\d{4} Part Numbers)'!"
)
# Detects an undated "Part Numbers" candidate tab title.
_UNDATED_PN = re.compile(r"^\s*part\s+numbers\b", re.IGNORECASE)
_DATED_PN = re.compile(r"^\s*\d{1,2}-\d{1,2}-\d{4}\s+part\s+numbers\s*$", re.IGNORECASE)


def workbook_sheet_names(workbook_xml: str) -> List[str]:
    """Return sheet display names in tab order."""
    names: List[str] = []
    for m in _SHEET_TAG.finditer(workbook_xml):
        nm = _NAME_ATTR.search(m.group(0))
        if nm:
            names.append(nm.group(1))
    return names


def detect_part_number_tabs(sheet_names: List[str]) -> List[str]:
    """Return all Part Numbers candidate tabs (dated first, then undated)."""
    dated = [n for n in sheet_names if _DATED_PN.match(n)]
    undated = [n for n in sheet_names if _UNDATED_PN.match(n) and n not in dated]
    return dated + undated


def choose_source_tab(
    sheet_names: List[str],
    *,
    explicit_tab: Optional[str],
    chosen_date_iso: str,
    target_label: str,
) -> Optional[str]:
    """Pick the tab to rename to ``target_label``."""
    if explicit_tab and explicit_tab in sheet_names:
        return explicit_tab
    candidates = detect_part_number_tabs(sheet_names)
    if not candidates:
        return None
    if target_label in candidates and len(candidates) == 1:
        return target_label
    # Prefer the dated tab whose date matches the chosen update date.
    y, m, d = chosen_date_iso.split("-")
    want = f"{int(m)}-{int(d)}-{int(y)} Part Numbers"
    if want in candidates:
        return want
    # Otherwise prefer the single dated candidate, else the latest dated, else
    # the first undated candidate.
    dated = [n for n in candidates if _DATED_PN.match(n)]
    if dated:
        return sorted(dated)[-1]
    return candidates[0]


def rename_tab(workbook_xml: str, old: str, new: str) -> Tuple[str, bool]:
    """Rename a sheet's display name in xl/workbook.xml. Returns (xml, changed)."""
    if old == new:
        return workbook_xml, False

    changed = False

    def _sub(m: re.Match) -> str:
        nonlocal changed
        tag = m.group(0)
        nm = _NAME_ATTR.search(tag)
        if nm and nm.group(1) == old:
            changed = True
            return tag[: nm.start(1)] + new + tag[nm.end(1) :]
        return tag

    return _SHEET_TAG.sub(_sub, workbook_xml), changed


def _rewrite_refs_in_text(
    text: str, target_label: str, extra_source: Optional[str]
) -> Tuple[str, int, int, List[str]]:
    """Rewrite dated/external Part Numbers refs to the local target tab.

    Returns (new_text, patched_count, localized_count, remaining_external_idx).
    """
    patched = 0
    localized = 0
    remaining_ext: List[str] = []

    def _sub(m: re.Match) -> str:
        nonlocal patched, localized
        idx = m.group("idx")
        replacement = f"'{target_label}'!"
        if m.group(0) != replacement:
            patched += 1
        if idx is not None:
            localized += 1
        return replacement

    text = _DATED_REF.sub(_sub, text)

    # An explicitly chosen, non-dated source tab (e.g. plain "Part Numbers").
    if extra_source and extra_source != target_label:
        esc = re.escape(extra_source)
        pat = re.compile(r"(?:\[(?P<idx>\d+)\])?'" + esc + r"'!")

        def _sub2(m: re.Match) -> str:
            nonlocal patched, localized
            if m.group("idx") is not None:
                localized += 1
            patched += 1
            return f"'{target_label}'!"

        text = pat.sub(_sub2, text)

    # Any remaining external-indexed references (could not be localized here).
    for m in re.finditer(r"\[(\d+)\]'?[^'!]*'?!", text):
        remaining_ext.append(m.group(0))

    return text, patched, localized, remaining_ext


def rewrite_sheet_formulas(
    sheet_xml: str, target_label: str, extra_source: Optional[str]
) -> Tuple[str, int, int, int, List[str]]:
    """Rewrite refs inside every <f>…</f> of a worksheet.

    Returns (new_xml, scanned, patched, localized, remaining_external).
    """
    scanned = 0
    patched_total = 0
    localized_total = 0
    remaining_ext: List[str] = []

    def _sub(m: re.Match) -> str:
        nonlocal scanned, patched_total, localized_total
        scanned += 1
        head, body, tail = m.group(1), m.group(2), m.group(3)
        new_body, patched, localized, ext = _rewrite_refs_in_text(
            body, target_label, extra_source
        )
        patched_total += patched
        localized_total += localized
        remaining_ext.extend(ext)
        return head + new_body + tail

    new_xml = re.sub(r"(<f[^>]*>)(.*?)(</f>)", _sub, sheet_xml, flags=re.DOTALL)
    return new_xml, scanned, patched_total, localized_total, remaining_ext


def find_stale_dated_refs(text: str, target_label: str) -> List[str]:
    """Return distinct dated Part Numbers refs whose date != target."""
    target_inner = target_label
    stale = set()
    for m in _DATED_REF.finditer(text):
        if m.group("name") != target_inner:
            stale.add(m.group(0))
    return sorted(stale)
