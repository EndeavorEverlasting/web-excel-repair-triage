"""Doctrine rules for the NW PRJ billing summary.

Encodes the billing pipeline contract:
- Friday is the reporting batch marker; weekend work rolls to the next Friday.
- Overrides / resolved worked-project beat default assignment (done in reader).
- Raw notes are evidence, not authority; note-bearing rows go to review.
- Non-member names are excluded from Project Team totals by default.
- Rich/Richard Perez full or long admin days are not downgraded to partial on
  an afternoon clock-out alone (requires explicit exception evidence).
- Partial hours, missing roster, mismatches, note rows route to the review queue.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import List

from .models import BillingRow, ReviewFlag

# Names that are not Neuron/Admin Project Team members by default. They must not
# be pulled into Project Team totals just because a template lists them.
EXCLUDED_NAME_TOKENS = ("yostinn minaya", "steven marques", "inventory")

# Names whose full/long admin days are protected from afternoon-clockout downgrade.
PINNED_FULL_DAY_TOKENS = ("rich perez", "richard perez")

# Gross-hours floor below which a non-pinned row is treated as partial for review.
PARTIAL_THRESHOLD_HOURS = 4.0


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def is_excluded_name(name: str) -> bool:
    n = _norm(name)
    return any(tok in n for tok in EXCLUDED_NAME_TOKENS)


def is_pinned_full_day(name: str) -> bool:
    n = _norm(name)
    return any(tok in n for tok in PINNED_FULL_DAY_TOKENS)


def friday_batch(d: date) -> date:
    """Return the reporting Friday for a date.

    Mon-Fri map to that week's Friday; Sat/Sun roll to the next Friday.
    """
    offset = 4 - d.weekday()
    if d.weekday() >= 5:  # Saturday or Sunday
        offset += 7
    return d + timedelta(days=offset)


def classify_rows(rows: List[BillingRow]) -> tuple[List[BillingRow], List[ReviewFlag]]:
    """Split excluded names out of Project Team rows and build review flags.

    Returns (kept_rows, review_flags). Excluded-name rows are removed from the
    admin/Project Team set and recorded as review flags instead.
    """
    kept: List[BillingRow] = []
    flags: List[ReviewFlag] = []

    for row in rows:
        if is_excluded_name(row.staff):
            flags.append(
                ReviewFlag(
                    category="excluded_name",
                    staff=row.staff,
                    detail=(
                        f"{row.staff} is not a Project Team member by default; "
                        f"excluded from admin totals ({row.project})."
                    ),
                    date_iso=row.date.isoformat(),
                )
            )
            continue

        pinned = is_pinned_full_day(row.staff)

        # Partial hours: a truly incomplete punch pair is routed to review and
        # kept out of the clean admin set (it has no resolvable hours).
        if row.partial:
            flags.append(
                ReviewFlag(
                    category="partial_hours",
                    staff=row.staff,
                    detail=f"Incomplete punch pair on {row.date.isoformat()} "
                    f"(clock_in={row.clock_in or 'blank'}, clock_out={row.clock_out or 'blank'}).",
                    date_iso=row.date.isoformat(),
                )
            )
            continue

        # A short gross day flags for review too, EXCEPT for pinned full-day
        # names (Rich Perez guard) which are not downgraded on hours alone.
        if row.gross_hours < PARTIAL_THRESHOLD_HOURS and not pinned:
            flags.append(
                ReviewFlag(
                    category="partial_hours",
                    staff=row.staff,
                    detail=f"Short day {row.gross_hours:.2f}h on {row.date.isoformat()} "
                    "(below partial threshold).",
                    date_iso=row.date.isoformat(),
                )
            )

        if row.note:
            flags.append(
                ReviewFlag(
                    category="note_bearing",
                    staff=row.staff,
                    detail=f"Punch note on {row.date.isoformat()}: {row.note}",
                    date_iso=row.date.isoformat(),
                )
            )

        kept.append(row)

    return kept, flags
