"""Range-backed list validation helpers for mutable workbook vocabularies.

This module extends :mod:`triage.dv_engine` rather than creating a second data-
validation engine. Use it when a dropdown vocabulary is expected to evolve and
therefore must have one canonical worksheet range instead of repeated inline
lists that can drift across cells or workbook generations.
"""
from __future__ import annotations

from triage.dv_engine import DVRule


def normalize_range_formula(source_formula: str) -> str:
    """Return an OOXML-compatible list-range formula without a leading ``=``.

    Google Sheets API calls express range-backed validation as ``='Sheet'!$A$1:$A$9``.
    OOXML ``formula1`` stores the equivalent reference without the leading equals
    sign. Keeping that normalization here prevents callers from duplicating the
    provider-specific distinction.
    """
    formula = str(source_formula or "").strip()
    if formula.startswith("="):
        formula = formula[1:].strip()
    if not formula or "!" not in formula:
        raise ValueError("range-backed list validation requires a worksheet range reference")
    if formula.startswith('"') and formula.endswith('"'):
        raise ValueError("range-backed list validation must not use an inline quoted list")
    return formula


def make_range_list_validation(
    sheet_part: str,
    sqref: str,
    source_formula: str,
    sheet_name: str = "",
    *,
    prompt: str = "Choose a value from the canonical worksheet dictionary.",
) -> DVRule:
    """Create one strict-looking OOXML list rule backed by a worksheet range.

    ``DVRule`` remains the canonical rendering/apply primitive. This helper only
    centralizes how a mutable list source is represented so generators and repair
    flows do not fall back to duplicated inline values.
    """
    return DVRule(
        category="list",
        sheet_part=sheet_part,
        sheet_name=sheet_name,
        sqref=sqref,
        dv_type="list",
        allow_blank=True,
        show_input=True,
        show_error=True,
        prompt=prompt,
        formula1=normalize_range_formula(source_formula),
    )
