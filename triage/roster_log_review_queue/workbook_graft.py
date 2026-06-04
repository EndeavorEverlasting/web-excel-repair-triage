"""Workbook graft: insert/reorder review layer sheets (Stage A)."""
from __future__ import annotations

from .package_io import Package


def graft_review_layer(pkg: Package, input_path: str) -> Package:
    """Insert or update Review Dashboard-first review tabs.

    Stage A follow-up: XML graft from blessed templates.
    """
    _ = input_path
    return pkg
