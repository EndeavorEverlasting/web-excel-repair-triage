"""
NW PRJ roster reader — evidence extractor only.

Reads tech / date / punch / hours evidence from the Active Roster Log. This
module is intentionally dumb: it does not decide authority, does not apply
Rich hours protection, does not classify issue types, and does not build
dashboard rows. Resolution and authority logic live in
``triage.nw_prj_target_classifier``.

The lower-level wide-form parsing of the roster workbook is handled by
``triage.roster_parser``. This module wraps that output into the NW PRJ
evidence shape and preserves note-bearing punch text that ``roster_parser``
strips during numeric time conversion.

Status: scaffolded for feature/nw-prj-ingest-admin-roster-rows. Implementations
raise NotImplementedError until the ingestion PR lands.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class RosterEvidence:
    """One evidence record extracted from the Active Roster Log.

    Fields:
      tech:              staff name as written in the roster row.
      date:              ISO-like date string for the column this punch came from.
      project:           raw project name from the roster's project column. The
                         classifier decides whether overrides apply.
      clock_in_raw:      original clock-in cell text, including any appended
                         note (e.g. "9:28:00 AM/ Bonita"). ``None`` if blank.
      clock_out_raw:     original clock-out cell text. ``None`` if blank.
      clock_in_hours:    decimal hours form of the clock-in time, or ``None``
                         if the cell was blank or unparseable.
      clock_out_hours:   decimal hours form of the clock-out time, or ``None``.
      gross_hours:       clock-out minus clock-in in hours, or ``None``.
      lunch_deduction:   policy lunch deduction in hours, or ``None``.
      net_hours:         gross minus lunch in hours, or ``None``.
      long_shift:        whether net hours qualify as a long shift per policy.
      in_note:           note portion of ``clock_in_raw`` (text after the time),
                         uninterpreted. Time goes to calculation, note goes to
                         context.
      out_note:          note portion of ``clock_out_raw``, uninterpreted.
      source_path:       absolute path of the roster workbook that produced this
                         evidence record.
    """

    tech: str
    date: str
    project: str
    clock_in_raw: Optional[str]
    clock_out_raw: Optional[str]
    clock_in_hours: Optional[float]
    clock_out_hours: Optional[float]
    gross_hours: Optional[float]
    lunch_deduction: Optional[float]
    net_hours: Optional[float]
    long_shift: bool
    in_note: str = ""
    out_note: str = ""
    source_path: str = ""


def read_roster_log(path: str | Path) -> List[RosterEvidence]:
    """Extract evidence rows from an Active Roster Log workbook.

    Contract:
      * Returns one ``RosterEvidence`` per (staff, date) pair with any punch
        activity. Days with no punches at all are omitted.
      * Note-bearing punches are preserved verbatim in ``clock_in_raw`` /
        ``clock_out_raw`` and additionally split into ``in_note`` / ``out_note``
        for downstream context. Time parsing follows ``triage.roster_parser``
        rules: appended note text after the time is stripped from numeric
        conversion but is not discarded.
      * Lunch deduction and long-shift policy come from
        ``triage.roster_parser._lunch_deduction``. This reader does not
        re-implement that policy.
      * Raises ``triage.roster_parser.RosterParseError`` if the workbook does
        not match the expected wide-form layout.
      * Does not classify issue types, does not decide project authority,
        does not flag mismatches.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("read_roster_log is scaffolded; implementation pending")


def split_note_bearing_punch(cell_text: str) -> tuple[str, str]:
    """Split a roster punch cell into ``(time_text, note_text)``.

    The time portion is whatever precedes the first ``/`` (or equivalent
    separator). The note portion is the remainder, with surrounding whitespace
    stripped. Either portion may be empty.

    This utility is used by ``read_roster_log`` to preserve note context that
    the underlying time parser strips. Pure-time cells return ``(cell_text, "")``.

    Implementation is pending the ingestion PR.
    """
    raise NotImplementedError("split_note_bearing_punch is scaffolded; implementation pending")
