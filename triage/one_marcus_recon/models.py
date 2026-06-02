"""Data models for the 1 Marcus recon relink engine."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DateCandidate:
    """A possible recon update date and where it came from."""

    date_iso: str
    source: str  # "cli" | "filename" | "tab" | "mtime"
    raw: str = ""

    @property
    def tab_label(self) -> str:
        """Render the M-D-YYYY Part Numbers tab title (no zero padding)."""
        y, m, d = self.date_iso.split("-")
        return f"{int(m)}-{int(d)}-{int(y)} Part Numbers"


@dataclass
class ReconChange:
    """A single applied (or proposed, in dry-run) change."""

    kind: str  # "rename_tab" | "rewrite_formula" | "localize_external" | "remove_part"
    detail: str
    sheet: str = ""
    count: int = 0


@dataclass
class ReconReport:
    """Full recon report; serialized to the *_preflight.json sidecar."""

    input_workbook: str = ""
    output_workbook: str = ""
    inferred_update_date: str = ""
    date_source: str = ""
    final_part_number_tab: str = ""
    pivot_tab: str = ""
    renamed_tabs: List[str] = field(default_factory=list)
    formula_cells_scanned: int = 0
    formula_cells_patched: int = 0
    stale_tab_references_removed: int = 0
    remaining_stale_tab_references: List[str] = field(default_factory=list)
    external_link_parts_removed: List[str] = field(default_factory=list)
    remaining_external_links: List[str] = field(default_factory=list)
    calc_chain_removed: bool = False
    formula_error_scan: List[str] = field(default_factory=list)
    webexcel_preflight_pass: bool = False
    date_candidates: List[Dict] = field(default_factory=list)
    changes: List[Dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    dry_run: bool = False

    def add_change(self, change: ReconChange) -> None:
        self.changes.append(dataclasses.asdict(change))

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)
