"""
triage/report.py
----------------
Build structured reports and JSON patch recipes from scan/diff/pattern results.
"""
from __future__ import annotations
import datetime
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.gate_checks import GateReport
from triage.diff import DiffReport
from triage.patterns import Pattern


@dataclass
class PatchOp:
    """A single patch instruction."""
    id: str = field(default_factory=lambda: f"p{uuid.uuid4().hex[:6]}")
    part: str = ""
    operation: str = ""  # literal_replace | append_block | delete_part | set_part
    description: str = ""
    # literal_replace
    match: Optional[str] = None
    replacement: Optional[str] = None
    occurrence: int = 1
    # append_block
    anchor: Optional[str] = None
    block: Optional[str] = None
    position: str = "before"  # before | after
    # set_part
    content: Optional[str] = None

    def to_dict(self) -> dict:
        d: Dict[str, Any] = {
            "id": self.id,
            "part": self.part,
            "operation": self.operation,
            "description": self.description,
        }
        if self.operation == "literal_replace":
            d["match"] = self.match
            d["replacement"] = self.replacement
            d["occurrence"] = self.occurrence
        elif self.operation == "append_block":
            d["anchor"] = self.anchor
            d["block"] = self.block
            d["position"] = self.position
        elif self.operation == "set_part":
            d["content"] = self.content
        return d


@dataclass
class PatchRecipe:
    source_file: str
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    version: str = "1"
    patches: List[PatchOp] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "source_file": self.source_file,
            "created_at": self.created_at,
            "patches": [p.to_dict() for p in self.patches],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ──────────────────────────────────────────────────────────────────────
# Recipe builders – translate gate findings + patterns into PatchOps
# ──────────────────────────────────────────────────────────────────────

def recipe_from_gates(gate: GateReport) -> PatchRecipe:
    """
    Auto-generate minimal patch operations from a GateReport alone
    (no diff required).  Produces safe, conservative suggestions.

    Now generates *concrete* literal_replace patches for shared_ref_bbox
    issues (actual ref= values are known from the gate scan) instead of
    placeholder stubs.
    """
    recipe = PatchRecipe(source_file=gate.path)

    # 1. calcChain invalid entries → drop calcChain
    if gate.calcchain_invalid:
        recipe.patches.append(PatchOp(
            part="xl/calcChain.xml",
            operation="delete_part",
            description=f"Drop xl/calcChain.xml ({len(gate.calcchain_invalid)} invalid entries). "
                         "Excel will rebuild it on next open.",
        ))

    # 2. shared_ref_bbox → generate a concrete literal_replace per mismatch
    #    The ref= value on the shared-formula base cell is unique enough to
    #    match safely (these ranges are never reused in other XML contexts).
    for issue in gate.shared_ref_bbox:
        declared = issue["declared_ref"]
        actual   = issue["actual_ref"]
        part     = issue["part"]
        si       = issue["si"]
        recipe.patches.append(PatchOp(
            part=part,
            operation="literal_replace",
            description=(f"Fix shared formula si={si} ref= bbox: "
                         f'"{declared}" → "{actual}" in {part}.'),
            match=f'ref="{declared}"',
            replacement=f'ref="{actual}"',
            occurrence=1,
        ))

    # 3. shared_ref_oob → clamp ref= end-row to sheet max row
    for issue in gate.shared_ref_oob:
        ref      = issue.get("ref", "")
        part     = issue.get("part", "")
        max_row  = issue.get("sheet_max_row", 0)
        si       = issue.get("si", "?")
        # Parse the ref and clamp last row
        import re as _re
        m = _re.match(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$', ref)
        if m and max_row:
            clamped = f'{m.group(1)}{m.group(2)}:{m.group(3)}{max_row}'
            recipe.patches.append(PatchOp(
                part=part,
                operation="literal_replace",
                description=(f"Clamp shared formula si={si} OOB ref= "
                             f'"{ref}" → "{clamped}" (sheet max row {max_row}).'),
                match=f'ref="{ref}"',
                replacement=f'ref="{clamped}"',
                occurrence=1,
            ))

    # 4. dxfs count mismatch → fix count attribute
    for issue in gate.styles_dxf:
        if issue.get("issue") == "dxfs_count_mismatch":
            declared = issue["declared"]
            actual = issue["actual"]
            recipe.patches.append(PatchOp(
                part="xl/styles.xml",
                operation="literal_replace",
                description=f"Fix dxfs/@count: declared {declared}, actual {actual}.",
                match=f'count="{declared}"',
                replacement=f'count="{actual}"',
                occurrence=1,
            ))
            break  # only one <dxfs> element

    # 5. tableColumn linefeed → hint only (we can't safely auto-fix without knowing the value)
    for hit in gate.tablecolumn_lf:
        recipe.patches.append(PatchOp(
            part=hit["part"],
            operation="literal_replace",
            description="Strip linefeed from tableColumn name= attribute. "
                         "Set match/replacement manually after inspecting the part.",
            match="<FILL_IN_LINEFEED_VALUE>",
            replacement="<FILL_IN_CLEAN_VALUE>",
        ))

    return recipe


def _extract_dxf_block_from_diff(xml_diff: Optional[str]) -> Optional[str]:
    """
    Mine added <dxf> elements from a unified diff of xl/styles.xml.
    Returns a string of the added <dxf>...</dxf> elements suitable for
    inserting before </dxfs>, or None if not found.
    """
    if not xml_diff:
        return None
    import re as _re
    added_lines = [ln[1:] for ln in xml_diff.splitlines() if ln.startswith("+")]
    block = "\n".join(added_lines)
    # Collect all <dxf> ... </dxf> elements from the added lines
    dxfs = _re.findall(r"<dxf\b[^>]*>.*?</dxf>", block, _re.DOTALL)
    if not dxfs:
        # Try single-line / self-closing <dxf/>
        dxfs = _re.findall(r"<dxf\b[^>]*/?>", block)
    return "\n".join(dxfs) if dxfs else None


def _extract_count_from_diff(xml_diff: Optional[str]) -> Optional[tuple]:
    """
    Extract (old_count, new_count) for dxfs @count attribute from diff.
    Returns (old, new) strings or None.
    """
    if not xml_diff:
        return None
    import re as _re
    old_m = _re.search(r'^-.*dxfs[^>]*count="(\d+)"', xml_diff, _re.MULTILINE)
    new_m = _re.search(r'^\+.*dxfs[^>]*count="(\d+)"', xml_diff, _re.MULTILINE)
    if old_m and new_m:
        return old_m.group(1), new_m.group(1)
    return None


def _read_part_from_zip(zip_path: str, part_name: str) -> Optional[bytes]:
    """Read a single part from a ZIP file, returning None if not found."""
    try:
        import zipfile as _zf
        with _zf.ZipFile(zip_path, "r") as z:
            if part_name in z.namelist():
                return z.read(part_name)
    except Exception:
        pass
    return None


def recipe_from_patterns(
    source_file: str,
    patterns: List[Pattern],
    diff_report: Optional["DiffReport"] = None,  # type: ignore[name-defined]
) -> PatchRecipe:
    """
    Translate detected diff patterns into patch operations.
    More precise than gate-only recipes because we have the actual diff.

    When *diff_report* is provided, concrete XML content is mined from the
    diff so patches are ready-to-apply rather than placeholder stubs.
    """
    # Build a quick lookup: part name → PartDelta
    diff_map: Dict[str, Any] = {}
    if diff_report is not None:
        for pd in diff_report.parts:
            diff_map[pd.name] = pd

    recipe = PatchRecipe(source_file=source_file)
    for p in patterns:
        if p.name == "CALCCHAIN_DROP":
            recipe.patches.append(PatchOp(
                part="xl/calcChain.xml",
                operation="delete_part",
                description=p.description,
            ))

        elif p.name == "DXFS_INSERTION":
            # Best strategy: replace xl/styles.xml wholesale with the repaired
            # version's bytes.  This avoids the count-mismatch that arises when
            # we append all N dxf elements from the repaired file instead of
            # only the delta.  The repaired file's styles.xml is byte-identical
            # to what Excel-for-Web would produce, so it is safe to use verbatim.
            repaired_styles: Optional[bytes] = None
            if diff_report is not None:
                repaired_styles = _read_part_from_zip(
                    diff_report.repaired_path, "xl/styles.xml"
                )

            if repaired_styles is not None:
                recipe.patches.append(PatchOp(
                    part="xl/styles.xml",
                    operation="set_part",
                    description=(p.description +
                                 " — xl/styles.xml replaced wholesale from repaired file "
                                 "(safest: avoids count-mismatch)."),
                    content=repaired_styles.decode("utf-8", errors="replace"),
                ))
            else:
                # Fallback: append_block stub
                recipe.patches.append(PatchOp(
                    part="xl/styles.xml",
                    operation="append_block",
                    description=p.description + " — Fill in <dxf> content from repaired file diff.",
                    anchor="</dxfs>",
                    block="<!-- INSERT_DXF_ELEMENTS_HERE -->",
                    position="before",
                ))

        elif p.name == "CF_DXFID_CLONE":
            # Excel renumbered dxfIds in cfRules.  The safest fix is to replace
            # each affected worksheet part wholesale from the repaired file.
            # This avoids computing the exact dxfId remapping table.
            for part in p.affected_parts:
                repaired_bytes: Optional[bytes] = None
                if diff_report is not None:
                    repaired_bytes = _read_part_from_zip(
                        diff_report.repaired_path, part
                    )
                if repaired_bytes is not None:
                    recipe.patches.append(PatchOp(
                        part=part,
                        operation="set_part",
                        description=(f"[CF_DXFID_CLONE] Replace {part} wholesale from "
                                     "repaired file to fix dxfId renumbering."),
                        content=repaired_bytes.decode("utf-8", errors="replace"),
                    ))
                else:
                    recipe.patches.append(PatchOp(
                        part=part,
                        operation="literal_replace",
                        description=f"[CF_DXFID_CLONE] {p.description} — Manual review required.",
                        match="<REVIEW_REQUIRED>",
                        replacement="<REVIEW_REQUIRED>",
                    ))

        elif p.name in ("SHARED_REF_TRIM", "TABLE_STYLE_NORM",
                         "SHAREDSTRINGS_REBUILD", "RELS_CLEANUP"):
            # These require human review; emit a stub
            for part in p.affected_parts:
                recipe.patches.append(PatchOp(
                    part=part,
                    operation="literal_replace",
                    description=f"[{p.name}] {p.description} — Manual review required. "
                                  "Set match/replacement from the XML diff.",
                    match="<REVIEW_REQUIRED>",
                    replacement="<REVIEW_REQUIRED>",
                ))
    return recipe


def merge_recipes(*recipes: PatchRecipe) -> PatchRecipe:
    """Merge multiple PatchRecipes, deduplicating by (part, operation, match)."""
    seen: set = set()
    merged = PatchRecipe(source_file=recipes[0].source_file if recipes else "")
    for r in recipes:
        for p in r.patches:
            key = (p.part, p.operation, p.match)
            if key not in seen:
                seen.add(key)
                merged.patches.append(p)
    return merged


def save_report(data: dict, path: str) -> None:
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_recipe(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

