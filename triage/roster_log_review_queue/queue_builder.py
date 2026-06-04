"""Build Review Queue rows by scanning Live/Assignments sheets (read-only)."""
from __future__ import annotations

from pathlib import Path
from typing import List

from .models import ReviewQueueRow

# Full queue builder is Stage A follow-up; export scaffold for CLI wiring.


def build_review_queue(input_path: str) -> List[ReviewQueueRow]:
    """Scan roster and return deterministic review queue rows.

    Stage A implementation will reuse admin_billing_summary reader precedence.
    """
    _ = Path(input_path)
    return []
