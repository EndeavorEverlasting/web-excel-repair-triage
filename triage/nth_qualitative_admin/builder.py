"""Deterministic qualitative admin Neuron Track Hours workbook orchestration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping
from zipfile import ZipFile

from .model import PROFILE_PATH, ROOT, QualitativeAdminError, derive_metrics, load_profile, validate_spec
from .sheets import _billing_support, _carryover, _dashboard, _detail_sheet, _operational_themes, _technical_scope, _visual_summary
from .style_template import canonical_styles_xml
from .xml_writer import MAIN_NS, THEME_PATH, _content_types, _root_rels, _sheet_names, _workbook_rels, _workbook_xml, _zip_write

def workbook_filename(spec: Mapping[str, Any]) -> str:
    month_name, year = spec["month_label"].split()
    mtd = "_MTD" if spec["mode"] == "month_to_date" else ""
    return f"ADMIN_SHARE_NTH_{month_name}_{year}{mtd}_QUALITATIVE_CURRENT_{spec['artifact_date'].isoformat()}.xlsx"


def _safe_output_dir(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    outputs = (ROOT / "Outputs").resolve()
    try:
        resolved.relative_to(outputs)
    except ValueError as exc:
        raise QualitativeAdminError("repository-local generated artifacts must be written under Outputs/") from exc
    return resolved


def _profile_digest() -> str:
    return hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()


def build_workbook(spec: Mapping[str, Any], output_path: str | Path) -> dict[str, Any]:
    normalized = validate_spec(spec)
    profile = load_profile()
    metrics = derive_metrics(normalized)
    names = _sheet_names(normalized)
    sheets: list[bytes] = [
        _dashboard(normalized, metrics, profile),
        _visual_summary(normalized, metrics, profile),
        _detail_sheet(normalized, profile),
        _operational_themes(normalized, profile),
    ]
    if normalized["mode"] == "completed_month":
        sheets.append(_billing_support(normalized, profile))
    else:
        sheets.extend([_carryover(normalized, profile), _technical_scope(normalized, profile)])
    if len(sheets) != len(names):
        raise RuntimeError("sheet construction drifted from mode profile")

    candidate = Path(output_path).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    safe_parent = _safe_output_dir(candidate.parent)
    path = (safe_parent / candidate.name).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w") as zf:
        _zip_write(zf, "[Content_Types].xml", _content_types(len(sheets)))
        _zip_write(zf, "_rels/.rels", _root_rels())
        _zip_write(zf, "xl/workbook.xml", _workbook_xml(names))
        _zip_write(zf, "xl/_rels/workbook.xml.rels", _workbook_rels(len(sheets)))
        _zip_write(zf, "xl/styles.xml", canonical_styles_xml())
        _zip_write(zf, "xl/theme/theme1.xml", THEME_PATH.read_bytes())
        _zip_write(zf, "xl/sharedStrings.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><sst xmlns="{MAIN_NS}"/>'.encode("utf-8"))
        for idx, xml in enumerate(sheets, 1):
            _zip_write(zf, f"xl/worksheets/sheet{idx}.xml", xml)

    return {
        "schema_version": "nth-qualitative-admin-build/v1",
        "profile_id": profile["profile_id"],
        "profile_sha256": _profile_digest(),
        "reference_fingerprints": profile["reference_fingerprints"],
        "mode": normalized["mode"],
        "month_key": normalized["month_key"],
        "month_label": normalized["month_label"],
        "artifact_date": normalized["artifact_date"].isoformat(),
        "workbook": str(path),
        "sheet_names": names,
        "detail_row_count": len(normalized["detail_rows"]),
        "total_paid_hours": metrics["total_paid_hours"],
        "completed_shift_records": metrics["completed_shift_records"],
        "formula_policy": "zero worksheet formulas; quantitative cells are build-time values derived from detail_rows",
        "proof_ceiling": "deterministic package/style/language profile and evidence-packet reconciliation; not roster-source verification, FUN acceptance, or operator/client acceptance",
    }


def build_package(spec: Mapping[str, Any], out_dir: str | Path) -> dict[str, Any]:
    normalized = validate_spec(spec)
    output_dir = _safe_output_dir(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook = output_dir / workbook_filename(normalized)
    manifest = build_workbook(normalized, workbook)
    # Import locally to keep the builder usable without a circular module import at load time.
    from .validator import validate_workbook

    validation = validate_workbook(workbook, normalized)
    validation_path = workbook.with_suffix(".validation.json")
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    manifest["validation"] = str(validation_path)
    manifest["validation_pass"] = validation["status"] == "PASS"
    manifest_path = workbook.with_suffix(".manifest.json")
    manifest["manifest"] = str(manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
