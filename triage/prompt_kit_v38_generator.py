"""Generate the package-preserving AI Harness Prompt Kit V38 artifact.

V38 is derived from the field-open V37 package. The generator delegates the
only workbook mutation to :mod:`triage.prompt_kit_copy_range_links`, which may
change prompt worksheet parts and the existing calculation chain only. Local
coding-agent prompts are emitted as delivery-bundle support files so workbook
topology and field-open package lineage remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from .prompt_kit_copy_range_links import apply_copy_range_links
from .prompt_kit_v38_prompt_assets import materialize_prompt_assets

ARTIFACT_NAME = "AI_Harness_Prompt_Kit_v38"
DEFAULT_OUTPUT_DIR = "Outputs/prompt_kit_v38"
DEFAULT_EXPECTED_PROMPTS = 45


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_workbook(source: Path, temp_dir: Path) -> Tuple[Path, Dict[str, bytes]]:
    if source.suffix.lower() == ".xlsx":
        return source, {}
    if source.suffix.lower() != ".zip":
        raise ValueError("source must be a V37 .xlsx workbook or a .zip bundle containing exactly one workbook")
    with zipfile.ZipFile(source) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".xlsx")]
        if len(names) != 1:
            raise ValueError(f"source bundle must contain exactly one workbook; found {names}")
        workbook = temp_dir / Path(names[0]).name
        workbook.write_bytes(archive.read(names[0]))
        extras = {
            name: archive.read(name)
            for name in archive.namelist()
            if name != names[0] and not name.endswith("/")
        }
    return workbook, extras


def _validate_changed_parts(changed_parts: Sequence[str]) -> None:
    invalid = [
        part
        for part in changed_parts
        if part != "xl/calcChain.xml" and not part.startswith("xl/worksheets/")
    ]
    if invalid:
        raise ValueError(f"V38 changed forbidden package parts: {invalid}")


def generate_v38(
    source: Path,
    output_dir: Path,
    expected_prompt_count: int = DEFAULT_EXPECTED_PROMPTS,
) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    if expected_prompt_count < 1:
        raise ValueError("expected_prompt_count must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="prompt-kit-v38-") as temporary:
        source_workbook, extras = _source_workbook(source, Path(temporary))
        workbook = output_dir / f"{ARTIFACT_NAME}.xlsx"
        result = apply_copy_range_links(source_workbook, workbook)
        _validate_changed_parts(result.changed_parts)

        if result.prompt_count != expected_prompt_count:
            raise ValueError(
                f"V38 requires {expected_prompt_count} prompt tabs; discovered {result.prompt_count}"
            )
        expected_links = 2 * expected_prompt_count
        if result.links_written != expected_links:
            raise ValueError(
                f"V38 requires {expected_links} copy-range links; wrote {result.links_written}"
            )

        idempotent = Path(temporary) / f"{ARTIFACT_NAME}-idempotent.xlsx"
        second = apply_copy_range_links(workbook, idempotent)
        if workbook.read_bytes() != idempotent.read_bytes():
            raise ValueError("V38 generator is not byte-idempotent")
        if second.changed_parts:
            raise ValueError(f"idempotent V38 pass unexpectedly changed parts: {second.changed_parts}")

        prompt_assets = materialize_prompt_assets(output_dir)
        manifest_path = output_dir / f"{ARTIFACT_NAME}_manifest.json"
        bundle_path = output_dir / f"{ARTIFACT_NAME}_bundle.zip"
        manifest = {
            "schema_version": 1,
            "artifact": ARTIFACT_NAME,
            "generator": "triage.prompt_kit_v38_generator",
            "source_authority": "field-open V37 package",
            "source": str(source),
            "source_sha256": _sha256(source),
            "source_workbook_sha256": _sha256(source_workbook),
            "workbook": str(workbook),
            "workbook_sha256": _sha256(workbook),
            "bundle": str(bundle_path),
            "expected_prompt_count": expected_prompt_count,
            "copy_range_links": result.to_dict(),
            "prompt_assets": [asset.to_dict() for asset in prompt_assets],
            "package_contract": {
                "allowed_changed_parts": [
                    "xl/worksheets/<prompt-sheet>.xml",
                    "xl/calcChain.xml when already present",
                ],
                "zip_member_set_preserved": True,
                "zip_member_order_preserved": True,
                "unrelated_parts_byte_identical": True,
                "whole_workbook_serializer_forbidden": True,
                "new_prompts_are_bundle_support_files": True,
            },
            "byte_idempotent": True,
            "proof_level": "static_package_validation",
            "proof_ceiling": (
                "V38 generation, exact copy-range formulas, calculation-chain integrity, "
                "package-boundary preservation, prompt-asset validation, and byte idempotence. "
                "Excel for Web opening, click-selection, and execution by a local coding agent "
                "remain operator runtime and field gates."
            ),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        generated_names = {workbook.name, manifest_path.name}
        generated_names.update(Path(asset.output).name for asset in prompt_assets)
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(workbook, workbook.name)
            archive.write(manifest_path, manifest_path.name)
            for asset in prompt_assets:
                asset_path = Path(asset.output)
                archive.write(asset_path, asset_path.name)
            for name, data in sorted(extras.items()):
                if not name.lower().endswith(".xlsx") and Path(name).name not in generated_names:
                    archive.writestr(name, data)

    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--expected-prompt-count", type=int, default=DEFAULT_EXPECTED_PROMPTS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_v38(
            Path(args.source),
            Path(args.out_dir),
            expected_prompt_count=args.expected_prompt_count,
        )
    except Exception as exc:
        print(f"V38 generation failed: {exc}")
        return 1
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Generated: {result['workbook']}\nBundle: {result['bundle']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
