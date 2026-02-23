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

    # 2. dxfs count mismatch → fix count attribute
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

    # 3. tableColumn linefeed → hint only (we can't safely auto-fix without knowing the value)
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


def recipe_from_patterns(source_file: str, patterns: List[Pattern]) -> PatchRecipe:
    """
    Translate detected diff patterns into patch operations.
    More precise than gate-only recipes because we have the actual diff.
    """
    recipe = PatchRecipe(source_file=source_file)
    for p in patterns:
        if p.name == "CALCCHAIN_DROP":
            recipe.patches.append(PatchOp(
                part="xl/calcChain.xml",
                operation="delete_part",
                description=p.description,
            ))
        elif p.name == "DXFS_INSERTION":
            recipe.patches.append(PatchOp(
                part="xl/styles.xml",
                operation="append_block",
                description=p.description + " — Fill in <dxf> content from repaired file diff.",
                anchor="</dxfs>",
                block="<!-- INSERT_DXF_ELEMENTS_HERE -->",
                position="before",
            ))
        elif p.name in ("CF_DXFID_CLONE", "SHARED_REF_TRIM", "TABLE_STYLE_NORM",
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

