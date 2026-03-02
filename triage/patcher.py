"""
triage/patcher.py
-----------------
Patch engine.  Applies a JSON patch recipe to a candidate .xlsx
WITHOUT full XML reserialization.  All mutations are byte-level.

Supported operations
--------------------
  literal_replace  – find first (or nth) occurrence of `match` bytes, replace
                     with `replacement` bytes.  Byte-preserving outside match.
  append_block     – find `anchor` bytes; insert `block` immediately before
                     (position="before") or after (position="after") it.
  delete_part      – remove the ZIP entry entirely (e.g. calcChain.xml).
  set_part         – write `content` verbatim as a new/replaced ZIP entry.

Recipe JSON schema (see report.py for generation):
{
  "version": "1",
  "source_file": "candidate.xlsx",
  "patches": [
    {
      "id": "p001",
      "part": "xl/styles.xml",
      "operation": "literal_replace",
      "description": "...",
      "match": "count=\"5\"",
      "replacement": "count=\"7\"",
      "occurrence": 1          // optional, default 1
    },
    {
      "id": "p002",
      "part": "xl/styles.xml",
      "operation": "append_block",
      "description": "...",
      "anchor": "</dxfs>",
      "block": "<dxf></dxf>",
      "position": "before"     // "before" | "after"
    },
    {
      "id": "p003",
      "part": "xl/calcChain.xml",
      "operation": "delete_part",
      "description": "Drop calcChain so Excel rebuilds it cleanly."
    }
  ]
}
"""
from __future__ import annotations
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class PatchError(Exception):
    pass


class PatchWarning(Exception):
    """
    Raised when the patch engine wrote a valid output file but skipped one or
    more stub placeholder patches (REVIEW_REQUIRED / FILL_IN_*) that require
    human editing before they can be applied.

    Attributes
    ----------
    output_path : str
        Path of the successfully-written patched file.
    skipped : list[str]
        Human-readable descriptions of every skipped stub.
    """
    def __init__(self, message: str, output_path: str, skipped: list):
        super().__init__(message)
        self.output_path = output_path
        self.skipped = skipped


# Placeholder values emitted by recipe_from_patterns() and recipe_from_gates()
# for patches that need human review before they can be applied literally.
STUB_PLACEHOLDERS: frozenset[str] = frozenset({
    "<REVIEW_REQUIRED>",
    "<FILL_IN_LINEFEED_VALUE>",
    "<FILL_IN_CLEAN_VALUE>",
})


def _encode(s: str | bytes) -> bytes:
    return s.encode("utf-8") if isinstance(s, str) else s


def _literal_replace(data: bytes, match: bytes, replacement: bytes, occurrence: int = 1) -> bytes:
    """Replace the nth occurrence (1-based) of *match* with *replacement*."""
    idx = -1
    for _ in range(occurrence):
        idx = data.find(match, idx + 1)
        if idx == -1:
            raise PatchError(f"literal_replace: match not found (occurrence {occurrence}): {match[:80]!r}")
    return data[:idx] + replacement + data[idx + len(match):]


def _append_block(data: bytes, anchor: bytes, block: bytes, position: str = "before") -> bytes:
    """Insert *block* immediately before or after *anchor*."""
    idx = data.find(anchor)
    if idx == -1:
        raise PatchError(f"append_block: anchor not found: {anchor[:80]!r}")
    if position == "before":
        insert_at = idx
    elif position == "after":
        insert_at = idx + len(anchor)
    else:
        raise PatchError(f"append_block: unknown position '{position}'; use 'before' or 'after'.")
    return data[:insert_at] + block + data[insert_at:]


def _apply_one(data: bytes, patch: Dict[str, Any]) -> Optional[bytes]:
    """
    Apply a single patch operation to *data*.
    Returns None if operation is delete_part (caller handles removal).
    """
    op = patch.get("operation")
    if op == "literal_replace":
        return _literal_replace(
            data,
            _encode(patch["match"]),
            _encode(patch.get("replacement", "")),
            int(patch.get("occurrence", 1)),
        )
    elif op == "append_block":
        return _append_block(
            data,
            _encode(patch["anchor"]),
            _encode(patch["block"]),
            patch.get("position", "before"),
        )
    elif op == "delete_part":
        return None  # signal deletion
    elif op == "set_part":
        return _encode(patch["content"])
    else:
        raise PatchError(f"Unknown operation: {op!r}")


def _rels_path_for(part: str) -> str:
    """
    Return the OPC .rels file path that owns *part*.
    e.g. "xl/calcChain.xml" → "xl/_rels/workbook.xml.rels"
         "xl/worksheets/sheet1.xml" → "xl/worksheets/_rels/sheet1.xml.rels"
    """
    p = Path(part.replace("/", "\\"))
    return str(p.parent / "_rels" / (p.name + ".rels")).replace("\\", "/")


def _owning_rels_file(part: str) -> str:
    """
    Return the .rels file that *contains* a Relationship pointing to *part*.
    For "xl/calcChain.xml" the owning rels is "xl/_rels/workbook.xml.rels".
    We derive this by looking at the parent directory's rels file.
    """
    p = part.replace("\\", "/")
    # Split into directory and filename
    if "/" in p:
        directory, filename = p.rsplit("/", 1)
        return f"{directory}/_rels/workbook.xml.rels"
    return "_rels/workbook.xml.rels"


def _strip_rels_entry(parts: Dict[str, bytes], deleted_part: str) -> None:
    """
    Remove the <Relationship> element(s) that reference *deleted_part* from
    every .rels file in *parts*.  Operates on the raw bytes with a simple
    split-based approach (no catastrophic backtracking).

    The Target= attribute in .rels files is relative to the owning part's
    directory, so we match on the basename of the deleted part.
    """
    dp = deleted_part.replace("\\", "/")
    basename = dp.rsplit("/", 1)[-1].encode()  # e.g. b"calcChain.xml"

    for rels_name in list(parts.keys()):
        if not rels_name.endswith(".rels"):
            continue
        data = parts[rels_name]
        if basename not in data:
            continue
        # Split on <Relationship and filter out any element whose Target
        # attribute ends with our basename.  This avoids regex backtracking.
        chunks = data.split(b"<Relationship")
        kept = [chunks[0]]
        for chunk in chunks[1:]:
            # chunk starts right after "<Relationship"
            # Find the closing /> of this element
            end = chunk.find(b"/>")
            if end == -1:
                kept.append(chunk)
                continue
            element = chunk[:end + 2]
            # Check if Target="...basename" appears in this element
            target_marker = b'Target="'
            ti = element.find(target_marker)
            if ti != -1:
                target_val_start = ti + len(target_marker)
                target_val_end = element.find(b'"', target_val_start)
                if target_val_end != -1:
                    target_val = element[target_val_start:target_val_end]
                    if target_val.endswith(basename):
                        # Skip this element (drop it)
                        kept.append(chunk[end + 2:])  # keep content after />
                        continue
            kept.append(chunk)
        new_data = b"<Relationship".join(kept)
        if new_data != data:
            parts[rels_name] = new_data


def apply_recipe(
    source_path: str,
    recipe: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """
    Apply all patches in *recipe* to *source_path*, write result to *output_path*.
    Returns the output path used.
    """
    if output_path is None:
        src = Path(source_path)
        output_path = str(src.with_stem(src.stem + "_patched"))

    # Load all parts into memory first (avoid mid-write conflicts)
    parts: Dict[str, bytes] = {}
    with zipfile.ZipFile(source_path, "r") as z:
        for name in z.namelist():
            parts[name] = z.read(name)

    deleted: set[str] = set()
    errors: List[str] = []
    skipped: List[str] = []

    for patch in recipe.get("patches", []):
        pid = patch.get("id", "?")
        part = patch.get("part")
        op = patch.get("operation")

        # ── Stub detection ────────────────────────────────────────────────
        # recipe_from_patterns() emits literal_replace stubs with sentinel
        # values (e.g. "<REVIEW_REQUIRED>") to signal that a human must fill
        # in the real match/replacement before the patch can run.  Attempting
        # a byte-level search for those sentinel strings would always fail, so
        # we skip them here and surface them as warnings, not errors.
        if op == "literal_replace":
            match_val = patch.get("match", "")
            if match_val in STUB_PLACEHOLDERS:
                desc = patch.get("description", "(no description)")
                skipped.append(f"[{pid}] STUB SKIPPED — {desc}")
                continue

        if op == "delete_part":
            if part in parts:
                deleted.add(part)
                # Also strip the <Relationship> entry that points to this part
                # from the owning .rels file so no dangling reference remains.
                _strip_rels_entry(parts, part)
            else:
                errors.append(f"[{pid}] delete_part: '{part}' not in archive (already absent?)")
            continue

        if part not in parts:
            errors.append(f"[{pid}] part '{part}' not found in archive")
            continue

        try:
            result = _apply_one(parts[part], patch)
            if result is not None:
                parts[part] = result
        except PatchError as e:
            errors.append(f"[{pid}] {e}")

    # Write output ZIP (always, so a partially-applied patch is still usable)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            if name not in deleted:
                zout.writestr(name, data)

    Path(output_path).write_bytes(buf.getvalue())

    # Hard failures → PatchError (file was written but may be incomplete)
    if errors:
        raise PatchError("Patch completed with errors:\n" + "\n".join(errors))

    # Stubs-only → PatchWarning (file is valid; human must fill placeholders)
    if skipped:
        raise PatchWarning(
            f"Patch applied — {len(skipped)} stub(s) skipped (need manual review):\n"
            + "\n".join(skipped),
            output_path=output_path,
            skipped=skipped,
        )

    return output_path


def apply_recipe_from_file(source_path: str, recipe_path: str, output_path: Optional[str] = None) -> str:
    with open(recipe_path, "r", encoding="utf-8") as f:
        recipe = json.load(f)
    return apply_recipe(source_path, recipe, output_path)

