"""Data models for roster log comparison results."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class ComparisonResult:
    version: str = "1"
    generated_utc: str = ""
    left: Dict[str, Any] = field(default_factory=dict)
    right: Dict[str, Any] = field(default_factory=dict)
    verdict: Dict[str, Any] = field(default_factory=dict)
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    sections: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
