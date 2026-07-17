"""Narrow package-preserving OOXML primitives for the segmented V39 generator.

This module intentionally exposes no prompt numbering, prompt taxonomy, V39
composition, or generator entrypoint. Semantic section ownership lives only in
``triage.prompt_kit_v39_generator`` and the two V39 prompt-contract files.

The implementation module is quarantined because it originated during an
abandoned numbering experiment. Only the generic package functions explicitly
re-exported below are supported; its former prompt IDs and generator functions
are not authority and must not be invoked.
"""
from __future__ import annotations

from ._prompt_kit_v39_package_primitives_impl import (
    APP_NS,
    CELL_RE,
    CONTENT_TYPES_NS,
    LIBRARY_FIELDS,
    LIBRARY_FORMULA_RE,
    MAIN_NS,
    NS,
    PKG_REL_NS,
    PROMPT_SHEET_RE,
    REL_NS,
    SHEET_PART_RE,
    VT_NS,
    WorkbookParts,
    _append_hyperlinks,
    _append_library_rows,
    _append_workbook_sheets,
    _cell_display,
    _cell_parts,
    _cells,
    _find_library_rows,
    _formula,
    _formula_cells,
    _make_prompt_sheet,
    _prompt_payload,
    _prompt_rows_and_ranges,
    _read_workbook,
    _rebuild_calc_chain,
    _root,
    _shared_strings,
    _source_workbook,
    _update_app_properties,
    _write_package,
    _xml,
)

__all__ = [
    "APP_NS",
    "CELL_RE",
    "CONTENT_TYPES_NS",
    "LIBRARY_FIELDS",
    "LIBRARY_FORMULA_RE",
    "MAIN_NS",
    "NS",
    "PKG_REL_NS",
    "PROMPT_SHEET_RE",
    "REL_NS",
    "SHEET_PART_RE",
    "VT_NS",
    "WorkbookParts",
    "_append_hyperlinks",
    "_append_library_rows",
    "_append_workbook_sheets",
    "_cell_display",
    "_cell_parts",
    "_cells",
    "_find_library_rows",
    "_formula",
    "_formula_cells",
    "_make_prompt_sheet",
    "_prompt_payload",
    "_prompt_rows_and_ranges",
    "_read_workbook",
    "_rebuild_calc_chain",
    "_root",
    "_shared_strings",
    "_source_workbook",
    "_update_app_properties",
    "_write_package",
    "_xml",
]
