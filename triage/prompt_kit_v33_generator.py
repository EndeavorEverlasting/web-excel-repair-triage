"""Generate one validated AI Harness Prompt Kit V33 workbook and delivery bundle.

This is the canonical V33 generation entrypoint. It accepts either a read-only
source workbook or a bundle containing exactly one workbook, delegates prompt
content and workbook mutation to the declarative finalizer/layout contracts, and
preserves non-workbook support files in the generated delivery bundle.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import re
import shutil
import tempfile
import zipfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence

from triage.prompt_kit_operability_contract import validate_prompt_kit_operability
from triage.prompt_kit_v33_artifact_contract import validate_artifact
from triage.prompt_kit_v33_copy_surface_contract import validate_v33_copy_surfaces
from triage.prompt_kit_v33_finalizer import DEFAULT_SPEC_PATH, finalize_workbook
from triage.prompt_kit_v33_layout_finalizer import canonicalize_layout
from triage.prompt_kit_v33_prompt_contract import validate_prompt_contract
from triage.web_excel_compatibility_rules import inspect_web_excel_package
from triage.workbook_package_hygiene import validate_workbook_package
from triage.worksheet_cell_integrity import inspect_worksheet_cell_integrity
from triage.xlsx_utils import fix_inlinestr

DEFAULT_OUTPUT_DIR = Path("Outputs") / "prompt-kit-v33"
DEFAULT_OUTPUT_NAME = "AI_Harness_Prompt_Kit_v33.xlsx"
MANIFEST_NAME = "AI_Harness_Prompt_Kit_v33_manifest.json"
REPORT_NAMES = {
    "finalizer": "finalize-report.json",
    "layout": "layout-report.json",
    "artifact_contract": "artifact-contract-report.json",
    "copy_surface_bounds": "copy-surface-bounds-report.json",
    "package_hygiene": "package-hygiene-report.json",
    "operability": "operability-report.json",
    "worksheet_integrity": "worksheet-integrity-report.json",
    "web_excel_compatibility": "web-excel-compatibility-report.json",
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _safe_member(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    member = PurePosixPath(normalized)
    if member.is_absolute() or not member.parts or any(part in {"", ".", ".."} for part in member.parts):
        raise ValueError(f"source bundle contains unsafe member path: {name!r}")
    return member


def _source_workbook(
    source: Path,
    temp_dir: Path,
) -> tuple[Path, dict[str, bytes]]:
    suffix = source.suffix.lower()
    if suffix == ".xlsx":
        return source, {}
    if suffix != ".zip":
        raise ValueError("source must be an .xlsx workbook or .zip bundle")

    with zipfile.ZipFile(source) as archive:
        members = {
            str(_safe_member(info.filename)): info
            for info in archive.infolist()
            if not info.is_dir()
        }
        workbook_names = [name for name in members if name.lower().endswith(".xlsx")]
        if len(workbook_names) != 1:
            raise ValueError(
                "source bundle must contain exactly one workbook; "
                f"found {sorted(workbook_names)}"
            )
        workbook_name = workbook_names[0]
        workbook_path = temp_dir / "source.xlsx"
        workbook_path.write_bytes(archive.read(members[workbook_name]))
        extras = {
            name: archive.read(info)
            for name, info in members.items()
            if name != workbook_name
        }
    return workbook_path, extras


def _validate_output_name(output_name: str) -> str:
    if Path(output_name).name != output_name or not output_name.lower().endswith(".xlsx"):
        raise ValueError("output_name must be a plain .xlsx filename")
    return output_name


def _backup_existing(paths: Sequence[Path], output_dir: Path) -> str | None:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup_dir = output_dir / "backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    for path in existing:
        shutil.move(str(path), str(backup_dir / path.name))
    return str(backup_dir)


def _relationship_owner_directory(relationship_part: str) -> str:
    if relationship_part == "_rels/.rels":
        return ""
    directory, filename = posixpath.split(relationship_part)
    if not directory.endswith("/_rels") or not filename.endswith(".rels"):
        return ""
    owner_directory = directory[: -len("/_rels")]
    owner_part = posixpath.join(owner_directory, filename[: -len(".rels")])
    return posixpath.dirname(owner_part)


def _normalize_internal_relationship_targets(path: Path) -> None:
    """Rewrite openpyxl's package-absolute internal Targets as OPC relatives."""
    original = path.read_bytes()
    changed = False
    with zipfile.ZipFile(io.BytesIO(original), "r") as source:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output:
            for info in source.infolist():
                data = source.read(info.filename)
                if info.filename.endswith(".rels") and b'Target="/' in data:
                    base = _relationship_owner_directory(info.filename)

                    def replace(match: re.Match[bytes]) -> bytes:
                        nonlocal changed
                        absolute = match.group(2).decode("utf-8").lstrip("/")
                        relative = posixpath.relpath(absolute, start=base or ".")
                        changed = True
                        return match.group(1) + relative.encode("utf-8") + match.group(3)

                    data = re.sub(rb'(\bTarget=")/([^"#]+)(")', replace, data)
                output.writestr(info, data)
    if changed:
        path.write_bytes(buffer.getvalue())


def _canonicalize_package(path: Path) -> None:
    """Make generated package metadata stable for identical source inputs."""
    original = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(original), "r") as source:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output:
            for source_info in sorted(source.infolist(), key=lambda item: item.filename):
                data = source.read(source_info.filename)
                if source_info.filename == "docProps/core.xml":
                    data = re.sub(
                        rb'(<dcterms:(?:created|modified)\b[^>]*>)[^<]*(</dcterms:(?:created|modified)>)',
                        rb'\g<1>2000-01-01T00:00:00Z\g<2>',
                        data,
                    )
                info = zipfile.ZipInfo(source_info.filename, date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                output.writestr(info, data)
    path.write_bytes(buffer.getvalue())


def _normalize_openpyxl_package(path: Path) -> None:
    fix_inlinestr(str(path))
    _normalize_internal_relationship_targets(path)
    _canonicalize_package(path)


def _run_validators(workbook: Path) -> dict[str, dict]:
    artifact = validate_artifact(workbook)
    copy_surfaces = validate_v33_copy_surfaces(workbook)
    package = validate_workbook_package(workbook)
    operability = validate_prompt_kit_operability(workbook)
    integrity_issues = inspect_worksheet_cell_integrity(workbook)
    web_issues = inspect_web_excel_package(workbook)
    reports = {
        "artifact_contract": artifact.to_dict(),
        "copy_surface_bounds": copy_surfaces.to_dict(),
        "package_hygiene": package.to_dict(),
        "operability": operability.to_dict(),
        "worksheet_integrity": {
            "valid": not integrity_issues,
            "issues": [asdict(issue) for issue in integrity_issues],
        },
        "web_excel_compatibility": {
            "valid": not web_issues,
            "issues": [asdict(issue) for issue in web_issues],
        },
    }
    failures = []
    if not artifact.passed:
        failures.append("artifact contract")
    if not copy_surfaces.passed:
        failures.append("copy-surface bounds")
    if not package.package_valid:
        failures.append("package hygiene")
    if not operability.valid:
        failures.append("operability contract")
    if integrity_issues:
        failures.append("worksheet integrity")
    if web_issues:
        failures.append("Web Excel compatibility")
    if failures:
        raise RuntimeError("generated workbook validation failed: " + ", ".join(failures))
    return reports


def generate_v33(
    source: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    output_name: str = DEFAULT_OUTPUT_NAME,
    spec_path: Path = DEFAULT_SPEC_PATH,
) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    output_name = _validate_output_name(output_name)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)

    source_hash_before = _sha256(source)
    output_dir.mkdir(parents=True, exist_ok=True)
    final_workbook = output_dir / output_name
    if source == final_workbook.resolve():
        raise ValueError("output must not overwrite the source workbook")

    prompt_contract = validate_prompt_contract(spec_path)
    if not prompt_contract.passed:
        raise RuntimeError("prompt source contract failed: " + "; ".join(prompt_contract.findings))

    bundle_name = f"{Path(output_name).stem}_bundle.zip"
    final_manifest = output_dir / MANIFEST_NAME
    final_bundle = output_dir / bundle_name
    final_reports = {name: output_dir / filename for name, filename in REPORT_NAMES.items()}
    final_paths = [final_workbook, final_manifest, final_bundle, *final_reports.values()]

    with tempfile.TemporaryDirectory(prefix="prompt-kit-v33-") as temporary:
        temp_dir = Path(temporary)
        source_workbook, support_files = _source_workbook(source, temp_dir)
        reserved_names = {path.name for path in final_paths}
        collisions = sorted(
            name for name in support_files if PurePosixPath(name).name in reserved_names
        )
        if collisions:
            raise ValueError(f"source bundle support files collide with generated outputs: {collisions}")

        staged_workbook = temp_dir / output_name
        finalize_result = finalize_workbook(source_workbook, staged_workbook, spec_path)
        layout_result = canonicalize_layout(staged_workbook, spec_path)
        _normalize_openpyxl_package(staged_workbook)
        validator_reports = _run_validators(staged_workbook)

        staged_reports = {name: temp_dir / filename for name, filename in REPORT_NAMES.items()}
        _write_json(staged_reports["finalizer"], finalize_result.to_dict())
        _write_json(staged_reports["layout"], layout_result.to_dict())
        for name, payload in validator_reports.items():
            _write_json(staged_reports[name], payload)

        support_manifest = [
            {
                "path": name,
                "sha256": _sha256_bytes(data),
                "size": len(data),
            }
            for name, data in sorted(support_files.items())
        ]
        manifest = {
            "schema_version": 1,
            "artifact": "AI_Harness_Prompt_Kit_v33",
            "source": str(source),
            "source_type": "bundle" if source.suffix.lower() == ".zip" else "workbook",
            "source_sha256": source_hash_before,
            "source_immutable": True,
            "workbook": str(final_workbook),
            "workbook_sha256": _sha256(staged_workbook),
            "bundle": str(final_bundle),
            "prompt_ids": [f"P{number:02d}" for number in range(50)],
            "prompt_ranges": dict(layout_result.prompt_ranges),
            "protected_sheets": "all",
            "editable_ranges": dict(layout_result.editable_ranges),
            "workbook_structure_locked": True,
            "support_files": support_manifest,
            "contract_authority": json.loads(spec_path.read_text(encoding="utf-8"))["contract_authority"],
            "reports": {name: str(final_reports[name]) for name in REPORT_NAMES},
            "validators": {name: "PASS" for name in validator_reports},
            "proof_ceiling": (
                "deterministic workbook generation, package structure, exact copy ranges, "
                "source immutability, prompt payloads, links, formatting, and protection; "
                "Excel Desktop/Web interaction and operator acceptance remain runtime gates"
            ),
        }
        staged_manifest = temp_dir / MANIFEST_NAME
        _write_json(staged_manifest, manifest)
        staged_bundle = temp_dir / bundle_name
        with zipfile.ZipFile(staged_bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(staged_workbook, output_name)
            archive.write(staged_manifest, MANIFEST_NAME)
            for name, report_path in staged_reports.items():
                archive.write(report_path, REPORT_NAMES[name])
            for name, data in sorted(support_files.items()):
                archive.writestr(name, data)

        if _sha256(source) != source_hash_before:
            raise RuntimeError("source changed during generation; refusing delivery")

        backup_dir = _backup_existing(final_paths, output_dir)
        shutil.move(str(staged_workbook), str(final_workbook))
        shutil.move(str(staged_manifest), str(final_manifest))
        shutil.move(str(staged_bundle), str(final_bundle))
        for name, staged_report in staged_reports.items():
            shutil.move(str(staged_report), str(final_reports[name]))

    manifest["backup_directory"] = backup_dir
    manifest["bundle_sha256"] = _sha256(final_bundle)
    # The sidecar can record the bundle hash without creating a circular hash
    # dependency inside the already-built bundle.
    _write_json(final_manifest, manifest)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--output-name", default=DEFAULT_OUTPUT_NAME)
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC_PATH)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = generate_v33(
            args.source,
            args.out_dir,
            output_name=args.output_name,
            spec_path=args.spec,
        )
    except (FileNotFoundError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        print(json.dumps(payload, indent=2) if args.json else f"FAIL: {exc}")
        return 1
    print(json.dumps(result, indent=2) if args.json else f"Generated: {result['workbook']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
