"""Metadata and comparison result models."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ArtifactMetadata:
    path: str
    artifact_family: str = "unknown"
    artifact_role: str = "unknown"
    audience: str = "internal"  # admin | client | internal
    engine: str = "unknown"
    engine_version: str = ""
    source_workbook_name: Optional[str] = None
    source_workbook_sha256: Optional[str] = None
    month_set: List[str] = field(default_factory=list)
    variant: Optional[str] = None
    schema_version: str = "1"
    preflight_profile: Optional[str] = None
    browser_excel_status: str = "UNKNOWN"
    generated_at: Optional[str] = None
    comparison_baseline: bool = False
    output_sha256: Optional[str] = None

    def required_for_compare(self) -> List[str]:
        missing = []
        if self.artifact_family in ("", "unknown"):
            missing.append("artifact_family")
        if not self.month_set and self.artifact_family in (
            "admin_billing_summary", "nw_prj_hours", "neuron_track_hours",
        ):
            missing.append("month_set")
        return missing

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
