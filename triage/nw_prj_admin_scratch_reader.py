"""
NW PRJ admin scratch reader — evidence extractor only.

Reads tech / date / hours / cell-reference evidence from a manual admin scratch
workbook. This module is intentionally dumb: it does not decide authority, does
not apply Rich hours protection, does not classify issue types, and does not
build dashboard rows. Resolution and authority logic live in
``triage.nw_prj_target_classifier``.

Status: scaffolded for feature/nw-prj-ingest-admin-roster-rows. Implementations
raise NotImplementedError until the ingestion PR lands.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class AdminScratchEvidence:
    """One evidence record extracted from an admin scratch workbook.

    Cell references are preserved verbatim so the classifier can map proposed
    edits back to the originating workbook coordinates without re-reading.

    Fields:
      tech:            staff name as written in the scratch cell.
      date:            ISO-like date string as written in the scratch cell.
      source_workbook: file name of the admin scratch workbook (no path).
      source_sheet:    sheet name the row was read from.
      source_row:      1-based row index inside ``source_sheet``.
      in_cell:         A1-style coordinate of the clock-in cell, if present.
      out_cell:        A1-style coordinate of the clock-out cell, if present.
      total_cell:      A1-style coordinate of the daily-total cell, if present.
      in_value:        raw clock-in cell value, stringified, untrimmed of notes.
      out_value:       raw clock-out cell value, stringified, untrimmed of notes.
      total_value:     parsed numeric daily total if the cell is numeric.
      notes:           raw adjacent note text (e.g. "/ Bonita"), uninterpreted.
    """

    tech: str
    date: str
    source_workbook: str
    source_sheet: str
    source_row: int
    in_cell: str = ""
    out_cell: str = ""
    total_cell: str = ""
    in_value: Optional[str] = None
    out_value: Optional[str] = None
    total_value: Optional[float] = None
    notes: str = ""


def read_admin_scratch(path: str | Path) -> List[AdminScratchEvidence]:
    """Extract evidence rows from a manual admin scratch workbook.

    Contract:
      * Returns one ``AdminScratchEvidence`` per tech/date/row observed.
      * Empty rows are skipped.
      * Note-bearing punches keep both the time portion (in ``in_value`` /
        ``out_value`` as the raw cell text) and the note portion (in ``notes``).
        Splitting and time parsing belong to downstream callers, not here.
      * Does not interpret authority, does not flag mismatches, does not infer
        project assignment.
      * Raises ``FileNotFoundError`` if ``path`` does not exist.
      * Raises ``RuntimeError`` if the workbook cannot be opened by openpyxl.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("read_admin_scratch is scaffolded; implementation pending")


def read_official_admin(path: str | Path) -> List[AdminScratchEvidence]:
    """Extract evidence rows from an official admin workbook.

    Same evidence shape as ``read_admin_scratch``. The classifier is responsible
    for treating ``official_admin_workbook`` as a lower authority than
    ``manual_admin_scratch`` per the schema's ``input_hierarchy``. This reader
    does not enforce that ordering.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("read_official_admin is scaffolded; implementation pending")
