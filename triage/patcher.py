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
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class PatchError(Exception):
    pass


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

    for patch in recipe.get("patches", []):
        pid = patch.get("id", "?")
        part = patch.get("part")
        op = patch.get("operation")

        if op == "delete_part":
            if part in parts:
                deleted.add(part)
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

    # Write output ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in parts.items():
            if name not in deleted:
                zout.writestr(name, data)

    Path(output_path).write_bytes(buf.getvalue())

    if errors:
        raise PatchError("Patch completed with errors:\n" + "\n".join(errors))

    return output_path


def apply_recipe_from_file(source_path: str, recipe_path: str, output_path: Optional[str] = None) -> str:
    with open(recipe_path, "r", encoding="utf-8") as f:
        recipe = json.load(f)
    return apply_recipe(source_path, recipe, output_path)

