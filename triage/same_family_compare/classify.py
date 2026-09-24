"""Heuristic artifact family classification."""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from triage.same_family_compare.models import ArtifactMetadata


def _sheet_names(path: Path) -> List[str]:
    try:
        with zipfile.ZipFile(path, "r") as z:
            if "xl/workbook.xml" not in z.namelist():
                return []
            text = z.read("xl/workbook.xml").decode("utf-8", errors="ignore")
        return re.findall(r'<sheet[^>]+name="([^"]+)"', text)
    except Exception:
        return []


def classify_file(path: Path) -> ArtifactMetadata:
    name = path.name.lower()
    sheets = _sheet_names(path)
    family = "unknown"
    audience = "internal"
    role = "candidate"
    profile = None
    months: List[str] = []
    variant = None

    if "active_roster_log" in name or "roster_log" in name or any(
        s.lower().startswith("live -") for s in sheets
    ):
        family = "active_roster_log"
        audience = "internal"
        role = "source_evidence"
    elif "billing_summary" in name:
        family = "admin_billing_summary"
        audience = "client" if "client" in name else (
            "admin" if "internal" in name else "admin"
        )
        role = "submission_workbook"
        profile = "admin_billing_summary"
        for m in re.finditer(r"(20\d{2})[-_](\d{2})", name):
            months.append(f"{m.group(1)}-{m.group(2)}")
        variant = "client" if "client" in name else "internal"
    elif "bonita" in name or "neuron_track" in name or "track_hours" in name:
        family = "neuron_track_hours"
        audience = "admin"
        profile = "bonita_neuron_track_hours"
        role = "submission_workbook"
    elif "nw_prj" in name and "dashboard" in name:
        family = "nw_prj_hours"
        audience = "internal"
        role = "dashboard"
    elif "web" in name and ("opened" in name or "repaired" in name or "download" in name):
        family = "web_excel_opened_copy"
        audience = "internal"
        role = "proof_copy"

    return ArtifactMetadata(
        path=str(path.resolve()),
        artifact_family=family,
        artifact_role=role,
        audience=audience,
        engine="triage",
        preflight_profile=profile,
        month_set=sorted(set(months)),
        variant=variant,
    )
