"""
triage/patterns.py
------------------
Repair-diff pattern interpreter.
Given a DiffReport, detect which "repair recipe" pattern Excel-for-Web applied
so we can propose the inverse patch.

Patterns detected:
  CF_DXFID_CLONE   – Excel cloned/renumbered dxfIds in cfRules
  DXFS_INSERTION   – Excel inserted <dxf> entries into styles.xml
  SHAREDSTRINGS_REBUILD – sharedStrings.xml was rewritten
  TABLE_STYLE_NORM – table*.xml was normalised (style name changed)
  CALCCHAIN_DROP   – xl/calcChain.xml was removed entirely
  SHARED_REF_TRIM  – shared formula ref= bbox was trimmed to actual rows
  RELS_CLEANUP     – a .rels part was rewritten (target added/removed)
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional

from triage.diff import DiffReport, PartDelta


@dataclass
class Pattern:
    name: str
    description: str
    affected_parts: List[str]
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"
    suggested_patch: Optional[str] = None  # human-readable recipe hint


def detect_calcchain_drop(diff: DiffReport) -> Optional[Pattern]:
    for p in diff.removed:
        if p.name == "xl/calcChain.xml":
            return Pattern(
                name="CALCCHAIN_DROP",
                description="Excel removed xl/calcChain.xml during repair. "
                             "The calcChain had entries pointing to non-formula cells.",
                affected_parts=["xl/calcChain.xml"],
                confidence="HIGH",
                suggested_patch="delete_part: xl/calcChain.xml",
            )
    return None


def detect_dxfs_insertion(diff: DiffReport) -> Optional[Pattern]:
    for p in diff.changed:
        if p.name != "xl/styles.xml":
            continue
        if not p.xml_diff:
            continue
        added_dxf = sum(1 for ln in p.xml_diff.splitlines() if ln.startswith("+") and "<dxf" in ln)
        changed_count = sum(1 for ln in p.xml_diff.splitlines() if ln.startswith("+") and 'count="' in ln)
        if added_dxf > 0:
            return Pattern(
                name="DXFS_INSERTION",
                description=f"Excel inserted {added_dxf} <dxf> element(s) into xl/styles.xml "
                             f"and updated dxfs/@count. Likely triggered by cfRule dxfId references "
                             f"pointing beyond the declared dxf pool.",
                affected_parts=["xl/styles.xml"],
                confidence="HIGH" if changed_count > 0 else "MEDIUM",
                suggested_patch="append_block: insert missing <dxf> entries before </dxfs>, "
                                 "then literal_replace dxfs count= to match new total.",
            )
    return None


def detect_cf_dxfid_clone(diff: DiffReport) -> Optional[Pattern]:
    for p in diff.changed:
        if not p.name.startswith("xl/worksheets/sheet"):
            continue
        if not p.xml_diff:
            continue
        minus_dxf = sum(1 for ln in p.xml_diff.splitlines() if ln.startswith("-") and "dxfId=" in ln)
        plus_dxf = sum(1 for ln in p.xml_diff.splitlines() if ln.startswith("+") and "dxfId=" in ln)
        if minus_dxf > 0 and plus_dxf > 0:
            return Pattern(
                name="CF_DXFID_CLONE",
                description=f"Excel renumbered dxfId values in conditional formatting rules "
                             f"({minus_dxf} removed, {plus_dxf} added lines). "
                             f"Affected part: {p.name}",
                affected_parts=[p.name, "xl/styles.xml"],
                confidence="HIGH",
                suggested_patch="literal_replace: update each dxfId= in cfRule to reference valid index "
                                 "within dxfs pool, or append missing dxf entries.",
            )
    return None


def detect_sharedstrings_rebuild(diff: DiffReport) -> Optional[Pattern]:
    for p in diff.changed:
        if p.name == "xl/sharedStrings.xml":
            return Pattern(
                name="SHAREDSTRINGS_REBUILD",
                description="Excel rebuilt xl/sharedStrings.xml. This often happens when si/t "
                             "elements have illegal control characters or malformed XML.",
                affected_parts=["xl/sharedStrings.xml"],
                confidence="MEDIUM",
                suggested_patch="check_illegal_control_chars gate, then strip or encode offending bytes.",
            )
    return None


def detect_table_style_norm(diff: DiffReport) -> Optional[Pattern]:
    hits = [p for p in diff.changed if p.name.startswith("xl/tables/table") and p.name.endswith(".xml")]
    if hits:
        return Pattern(
            name="TABLE_STYLE_NORM",
            description=f"Excel normalised {len(hits)} table XML part(s). "
                         "Common cause: tableStyleInfo name pointing to a non-existent style, "
                         "or tableColumn/@name containing linefeeds.",
            affected_parts=[p.name for p in hits],
            confidence="MEDIUM",
            suggested_patch="literal_replace: set tableStyleInfo name= to a built-in style "
                             "(e.g. TableStyleMedium9), strip linefeeds from tableColumn name=.",
        )
    return None


def detect_shared_ref_trim(diff: DiffReport) -> Optional[Pattern]:
    hits = [p for p in diff.changed if p.name.startswith("xl/worksheets/sheet")]
    for p in hits:
        if not p.xml_diff:
            continue
        if any("ref=" in ln and ln.startswith(("-", "+")) for ln in p.xml_diff.splitlines()):
            return Pattern(
                name="SHARED_REF_TRIM",
                description=f"Excel adjusted shared formula ref= bounding boxes in {p.name}. "
                             "Declared bbox extended beyond actual data rows (OOB) or "
                             "mismatched participating cells.",
                affected_parts=[p.name],
                confidence="HIGH",
                suggested_patch="literal_replace: update ref= attribute on shared formula base cell "
                                 "to match actual bounding box of all si= siblings.",
            )
    return None


def detect_rels_cleanup(diff: DiffReport) -> Optional[Pattern]:
    hits = [p for p in diff.changed if p.name.endswith(".rels")]
    if hits:
        return Pattern(
            name="RELS_CLEANUP",
            description=f"Excel rewrote {len(hits)} relationship part(s): "
                         + ", ".join(p.name for p in hits) + ". "
                         "Missing or orphaned relationship targets are common triggers.",
            affected_parts=[p.name for p in hits],
            confidence="MEDIUM",
            suggested_patch="check rels_missing_targets gate; add or remove Relationship entries to match.",
        )
    return None


# ─── aggregate ───────────────────────────────────────────────────────────────

def detect_all(diff: DiffReport) -> List[Pattern]:
    """Run all pattern detectors; return list of matched Patterns."""
    detectors = [
        detect_calcchain_drop,
        detect_dxfs_insertion,
        detect_cf_dxfid_clone,
        detect_sharedstrings_rebuild,
        detect_table_style_norm,
        detect_shared_ref_trim,
        detect_rels_cleanup,
    ]
    results: List[Pattern] = []
    for fn in detectors:
        try:
            p = fn(diff)
            if p:
                results.append(p)
        except Exception:
            pass
    return results

