"""Detect legacy-comment VML identity collisions in OOXML workbooks.

Excel legacy comments ("notes") are rendered through VML drawing parts.  A
workbook can be well-formed XML and have every relationship target present,
while still reusing the same VML shape ids / idmap block in two different note
drawings.  Excel may then repair the workbook and re-index one drawing.

The scanner is read-only.  The optional repair path re-indexes only colliding
VML drawing identities in a copied workbook and then re-runs the scanner.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

_REL_VML = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing"
_REL_COMMENTS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"

_SHAPE_ID_RE = re.compile(r'\bid="(_x0000_s(\d+))"')
_IDMAP_RE = re.compile(r'<(?:\w+:)?idmap\b[^>]*\bdata="([^"]+)"', re.IGNORECASE)
_REL_RE = re.compile(r'<Relationship\b([^>]*)/?>', re.IGNORECASE)
_ATTR_RE = re.compile(r'([A-Za-z_:][A-Za-z0-9_.:-]*)="([^"]*)"')


class VmlCollisionRepairError(RuntimeError):
    """Raised when a colliding VML drawing cannot be re-indexed safely."""


@dataclass(frozen=True)
class VmlPartInventory:
    part: str
    idmap_data: tuple[str, ...] = ()
    shape_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CollisionFinding:
    kind: str
    value: str
    parts: tuple[str, ...]
    detail: str


@dataclass
class VmlCommentIntegrityReport:
    path: str
    vml_parts: list[VmlPartInventory] = field(default_factory=list)
    findings: list[CollisionFinding] = field(default_factory=list)
    relationship_notes: list[dict] = field(default_factory=list)

    @property
    def pass_all(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "pass": self.pass_all,
            "vml_parts": [asdict(item) for item in self.vml_parts],
            "findings": [asdict(item) for item in self.findings],
            "relationship_notes": self.relationship_notes,
        }


def _text(z: zipfile.ZipFile, name: str) -> str:
    return z.read(name).decode("utf-8", errors="ignore")


def _normalize_target(rels_path: str, target: str) -> str:
    """Resolve an OPC relationship target to a ZIP part name."""
    if target.startswith("/"):
        return target.lstrip("/")
    if "://" in target:
        return target

    pieces = rels_path.split("/")
    if "_rels" in pieces:
        idx = pieces.index("_rels")
        filename = pieces[-1]
        if filename.endswith(".rels"):
            filename = filename[:-5]
        owner = pieces[:idx] + [filename]
    else:
        owner = pieces

    base = owner[:-1]
    for segment in target.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if base:
                base.pop()
        else:
            base.append(segment)
    return "/".join(base)


def _relationship_inventory(z: zipfile.ZipFile) -> tuple[set[str], list[dict]]:
    """Return VML parts that are worksheet-linked plus comment relationship notes."""
    linked_vml: set[str] = set()
    notes: list[dict] = []
    names = set(z.namelist())

    for rels_path in sorted(
        n for n in names
        if n.startswith("xl/worksheets/_rels/") and n.endswith(".rels")
    ):
        xml = _text(z, rels_path)
        for match in _REL_RE.finditer(xml):
            attrs = dict(_ATTR_RE.findall(match.group(1)))
            rel_type = attrs.get("Type", "")
            target = attrs.get("Target", "")
            if not target:
                continue
            resolved = _normalize_target(rels_path, target)
            if rel_type == _REL_VML:
                if resolved in names:
                    linked_vml.add(resolved)
                notes.append({
                    "rels": rels_path,
                    "relationship": "vmlDrawing",
                    "id": attrs.get("Id"),
                    "target": target,
                    "resolved": resolved,
                    "absolute_target": target.startswith("/"),
                    "exists": resolved in names,
                })
            elif rel_type == _REL_COMMENTS:
                notes.append({
                    "rels": rels_path,
                    "relationship": "comments",
                    "id": attrs.get("Id"),
                    "target": target,
                    "resolved": resolved,
                    "absolute_target": target.startswith("/"),
                    "exists": resolved in names,
                })

    return linked_vml, notes


def _collision_findings(parts: Iterable[VmlPartInventory]) -> list[CollisionFinding]:
    shape_owners: dict[str, set[str]] = defaultdict(set)
    idmap_owners: dict[str, set[str]] = defaultdict(set)

    for item in parts:
        for shape_id in set(item.shape_ids):
            shape_owners[shape_id].add(item.part)
        for data in set(item.idmap_data):
            idmap_owners[data].add(item.part)

    findings: list[CollisionFinding] = []
    for shape_id, owners in sorted(shape_owners.items()):
        if len(owners) > 1:
            parts_tuple = tuple(sorted(owners))
            findings.append(CollisionFinding(
                kind="duplicate_vml_shape_id",
                value=shape_id,
                parts=parts_tuple,
                detail=(
                    "The same legacy-comment VML shape id appears in more than one "
                    "worksheet-linked VML drawing. Excel repair pairs have been observed "
                    "re-indexing one drawing to a different shape-id block."
                ),
            ))

    for data, owners in sorted(idmap_owners.items()):
        if len(owners) > 1:
            parts_tuple = tuple(sorted(owners))
            findings.append(CollisionFinding(
                kind="duplicate_vml_idmap_data",
                value=data,
                parts=parts_tuple,
                detail=(
                    "Multiple legacy-comment VML drawings claim the same o:idmap data block. "
                    "This is a strong companion signal when duplicate _x0000_s#### ids are also present."
                ),
            ))
    return findings


def _next_free_idmap_block(parts: Iterable[VmlPartInventory], reserved: set[str]) -> int:
    numeric = [int(v) for part in parts for v in part.idmap_data if str(v).isdigit()]
    candidate = max(numeric, default=0) + 1
    while str(candidate) in reserved:
        candidate += 1
    return candidate


def _reindex_vml_xml(xml: str, block: int) -> tuple[str, dict[str, str]]:
    """Assign one VML drawing to a fresh idmap block and unique shape ids."""
    idmap_matches = list(_IDMAP_RE.finditer(xml))
    if len(idmap_matches) != 1:
        raise VmlCollisionRepairError(
            f"expected exactly one VML idmap record, found {len(idmap_matches)}"
        )

    shape_matches = list(_SHAPE_ID_RE.finditer(xml))
    if not shape_matches:
        raise VmlCollisionRepairError("colliding VML part has no _x0000_s#### shape ids")

    replacement_map: dict[str, str] = {}
    next_shape = block * 1024 + 1
    for match in shape_matches:
        old = match.group(1)
        if old not in replacement_map:
            replacement_map[old] = f"_x0000_s{next_shape}"
            next_shape += 1

    def replace_shape(match: re.Match[str]) -> str:
        old = match.group(1)
        return f'id="{replacement_map[old]}"'

    rewritten = _SHAPE_ID_RE.sub(replace_shape, xml)
    rewritten = _IDMAP_RE.sub(
        lambda m: m.group(0).replace(f'data="{m.group(1)}"', f'data="{block}"'),
        rewritten,
        count=1,
    )
    return rewritten, replacement_map


def repair_vml_comment_collisions(source: str | Path, destination: str | Path) -> dict:
    """Re-index colliding worksheet-linked VML note drawings in a copied workbook.

    The source is never overwritten. Only colliding VML drawing parts are
    changed. Comment text/cell references and worksheet relationships are left
    untouched. This is structural repair only; Excel-for-Web acceptance still
    requires the repo's normal acceptance gates.
    """
    source = Path(source)
    destination = Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("destination must differ from source")

    pre = scan_vml_comment_integrity(source)
    if pre.pass_all:
        shutil.copyfile(source, destination)
        return {
            "source": str(source),
            "destination": str(destination),
            "reindexed_parts": [],
            "post_pass": True,
        }

    # Keep the first owner of each collision stable and re-index later parts.
    reindex_parts: set[str] = set()
    for finding in pre.findings:
        owners = list(finding.parts)
        if owners:
            reindex_parts.update(owners[1:])

    if not reindex_parts:
        raise VmlCollisionRepairError(
            "collision report did not identify a repairable later VML owner"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as handle:
        temp_path = Path(handle.name)

    reserved_idmaps = {v for part in pre.vml_parts for v in part.idmap_data}
    changes: list[dict] = []

    try:
        with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename in reindex_parts:
                    block = _next_free_idmap_block(pre.vml_parts, reserved_idmaps)
                    reserved_idmaps.add(str(block))
                    xml = data.decode("utf-8")
                    rewritten, shape_map = _reindex_vml_xml(xml, block)
                    data = rewritten.encode("utf-8")
                    changes.append({
                        "part": info.filename,
                        "new_idmap_data": str(block),
                        "shape_id_map": shape_map,
                    })
                zout.writestr(info, data)

        post = scan_vml_comment_integrity(temp_path)
        if not post.pass_all:
            raise VmlCollisionRepairError(
                "VML repair output still fails integrity checks: "
                + json.dumps(post.to_dict(), sort_keys=True)
            )
        temp_path.replace(destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise

    return {
        "source": str(source),
        "destination": str(destination),
        "reindexed_parts": changes,
        "post_pass": True,
    }


def scan_vml_comment_integrity(path: str | Path) -> VmlCommentIntegrityReport:
    """Inspect worksheet-linked VML note drawings for package-wide identity collisions."""
    path = str(path)
    report = VmlCommentIntegrityReport(path=path)
    with zipfile.ZipFile(path, "r") as z:
        linked_vml, rel_notes = _relationship_inventory(z)
        report.relationship_notes = rel_notes

        for part in sorted(linked_vml):
            xml = _text(z, part)
            shape_ids = tuple(match.group(1) for match in _SHAPE_ID_RE.finditer(xml))
            idmap_data = tuple(match.group(1) for match in _IDMAP_RE.finditer(xml))
            report.vml_parts.append(VmlPartInventory(
                part=part,
                idmap_data=idmap_data,
                shape_ids=shape_ids,
            ))

        report.findings = _collision_findings(report.vml_parts)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check legacy-comment VML drawings for duplicate shape ids / idmap blocks."
    )
    parser.add_argument("workbook", help="Path to .xlsx workbook")
    parser.add_argument(
        "--repair-out",
        help="Write a copy with colliding VML note drawings re-indexed",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = scan_vml_comment_integrity(args.workbook)
    payload: dict = {"scan": report.to_dict()}
    exit_code = 0 if report.pass_all else 1
    if args.repair_out:
        payload["repair"] = repair_vml_comment_collisions(args.workbook, args.repair_out)
        exit_code = 0

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        state = "PASS" if report.pass_all else "FAIL"
        print(f"{state}: {args.workbook}")
        for item in report.vml_parts:
            print(
                f"  {item.part}: idmap={list(item.idmap_data)} shapes={list(item.shape_ids)}"
            )
        for finding in report.findings:
            print(f"  - {finding.kind}: {finding.value} -> {', '.join(finding.parts)}")
        if "repair" in payload:
            print(f"  repaired: {payload['repair']['destination']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
