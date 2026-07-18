"""Generate the final AI Harness Prompt Kit V33 workbook and delivery bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from .prompt_kit_copy_range_links import apply_copy_range_links
from .prompt_kit_v33_ooxml import (
    OPPORTUNITY_DISCOVERY,
    PROMPT_SUFFIX,
    PromptRange,
    _root,
    _set_formula,
    _sheet_map,
    _xml,
    finalize_workbook,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_workbook(source: Path, temp_dir: Path) -> Tuple[Path, Dict[str, bytes]]:
    if source.suffix.lower() == ".xlsx":
        return source, {}
    if source.suffix.lower() != ".zip":
        raise ValueError("source must be an .xlsx workbook or .zip bundle")
    with zipfile.ZipFile(source) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
        if len(names) != 1:
            raise ValueError(f"source bundle must contain exactly one workbook; found {names}")
        workbook = temp_dir / Path(names[0]).name
        workbook.write_bytes(archive.read(names[0]))
        extras = {name: archive.read(name) for name in archive.namelist() if name != names[0] and not name.endswith("/")}
    return workbook, extras


def _materialize_copy_range_formula_cells(
    workbook_path: Path,
    prompt_ranges: Sequence[PromptRange],
) -> None:
    """Create the two canonical copy-range cells before strict link validation.

    Real accepted prompt-kit sources already contain these label cells. Synthetic
    and older generator inputs may not. The generator owns materializing them;
    the standalone package patcher remains fail-closed when a source omits the
    required copy surface.
    """
    with zipfile.ZipFile(workbook_path, "r") as source:
        infos = source.infolist()
        parts = {info.filename: source.read(info.filename) for info in infos}
    _, sheets = _sheet_map(parts)
    replacements: dict[str, bytes] = {}
    for item in prompt_ranges:
        part = sheets.get(item.sheet)
        if not part:
            raise ValueError(f"prompt worksheet part missing: {item.sheet}")
        root = _root(parts, part)
        target = f"'{item.sheet}'!{item.range}"
        label = f"Copy {item.range} only"
        _set_formula(root, "C1", target, label)
        _set_formula(root, f"C{item.last_row}", target, label)
        replacements[part] = _xml(root)

    fd, temporary_name = tempfile.mkstemp(
        prefix=workbook_path.stem + "-copy-range-",
        suffix=".xlsx",
        dir=str(workbook_path.parent),
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(workbook_path, "r") as source, zipfile.ZipFile(temporary, "w") as target:
            for info in source.infolist():
                target.writestr(info, replacements.get(info.filename, source.read(info.filename)))
        os.replace(temporary, workbook_path)
    finally:
        temporary.unlink(missing_ok=True)


def generate_v33(source: Path, output_dir: Path, gnhf_build_prompt: str = "P39") -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prompt-kit-v33-") as temp:
        source_workbook, extras = _source_workbook(source, Path(temp))
        workbook = output_dir / "AI_Harness_Prompt_Kit_v33.xlsx"
        prompt_ranges = finalize_workbook(source_workbook, workbook, gnhf_build_prompt)
        _materialize_copy_range_formula_cells(workbook, prompt_ranges)
        copy_range_links = apply_copy_range_links(workbook, workbook, prompt_ranges)
        manifest_path = output_dir / "AI_Harness_Prompt_Kit_v33_manifest.json"
        bundle = output_dir / "AI_Harness_Prompt_Kit_v33_bundle.zip"
        manifest = {
            "schema_version": 1,
            "artifact": "AI_Harness_Prompt_Kit_v33",
            "source": str(source),
            "source_sha256": _sha256(source),
            "workbook": str(workbook),
            "workbook_sha256": _sha256(workbook),
            "bundle": str(bundle),
            "prompt_ranges": [asdict(item) for item in prompt_ranges],
            "copy_range_links": copy_range_links.to_dict(),
            "copy_range_link_contract": {
                "cells_per_prompt": 2,
                "top_cell": "C1",
                "bottom_cell": "C<last_prompt_row>",
                "target": "same prompt sheet full A1:A<last_prompt_row> range",
                "implementation": "package-preserving OOXML cell patch with calc-chain synchronization",
            },
            "cream_tab_sheets": ["Prompt_Library", OPPORTUNITY_DISCOVERY, "P07_COPY_SAFE", f"{gnhf_build_prompt}{PROMPT_SUFFIX}"],
            "protected_sheets": "all",
            "editable_range": f"{OPPORTUNITY_DISCOVERY}!A1:R100",
            "workbook_structure_locked": True,
            "gnhf_build_prompt": gnhf_build_prompt,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(workbook, workbook.name)
            archive.write(manifest_path, manifest_path.name)
            for name, data in sorted(extras.items()):
                if not name.lower().endswith(".xlsx") and Path(name).name != manifest_path.name:
                    archive.writestr(name, data)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out-dir", default="Outputs/prompt_kit_v33")
    parser.add_argument("--gnhf-build-prompt", default="P39")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_v33(Path(args.source), Path(args.out_dir), args.gnhf_build_prompt)
    except Exception as exc:
        print(f"V33 generation failed: {exc}")
        return 1
    print(json.dumps(result, indent=2) if args.json else f"Generated: {result['workbook']}\nBundle: {result['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
