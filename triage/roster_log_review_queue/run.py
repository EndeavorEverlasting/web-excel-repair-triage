"""Orchestrate roster log review queue graft pipeline."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Optional

from triage.one_marcus_recon.path_guard import assert_output_path_allowed

from .blank_builder import build_blank_roster
from .live_cf_patcher import patch_live_cf
from .models import GraftResult
from .package_io import Package, remove_calc_chain, remove_external_links
from .preflight import run_preflight
from .provenance import build_provenance
from .queue_builder import build_review_queue
from triage.output_policy import assert_output_path_allowed

from .workbook_graft import graft_review_layer


def _write_zip(xlsx_path: Path, provenance: dict, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(xlsx_path, xlsx_path.name)
        prov_name = xlsx_path.stem.lower().replace(" ", "_") + "_provenance.json"
        z.writestr(prov_name, json.dumps(provenance, indent=2))


def _write_provenance_and_zip(
    *,
    out: Path,
    provenance: dict,
    provenance_out: Optional[str],
    zip_out: Optional[str],
) -> None:
    prov_path = provenance_out or str(out.with_suffix(".provenance.json"))
    Path(prov_path).write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    if zip_out:
        _write_zip(out, provenance, Path(zip_out))


def run(
    *,
    mode: str,
    input_path: Optional[str] = None,
    output_path: str,
    provenance_out: Optional[str] = None,
    zip_out: Optional[str] = None,
    months: Optional[list] = None,
) -> GraftResult:
    """Run graft pipeline for *mode* (blank|full|graft|review-only|live-cf-only)."""
    mode = mode.replace("graft", "full") if mode == "graft" else mode
    out = Path(output_path)

    if mode == "blank":
        # Blank mode has no source workbook, but it still must obey the repo's
        # Candidates/ and Active/ source-immutability contract before any mkdir/save.
        assert_output_path_allowed(__file__, str(out))
        out.parent.mkdir(parents=True, exist_ok=True)
        shell = build_blank_roster(out, months or [])
        data = out.read_bytes()
        data, live_stats = patch_live_cf(data, scan_path=str(out))
        pkg = Package.from_bytes(data)
        remove_calc_chain(pkg)
        remove_external_links(pkg)
        pkg.write(str(out))

        data = out.read_bytes()
        try:
            verification = run_preflight(data, require_review_layer=True)
        except ValueError as exc:
            return GraftResult(
                output_path=str(out),
                provenance={},
                live_cf_stats=live_stats,
                review_queue_rows=0,
                preflight_pass=False,
                errors=[str(exc)],
            )

        provenance = build_provenance(
            input_workbook="<generated blank roster shell>",
            output_workbook=out.name,
            method=(
                "new workbook generation: openpyxl shell + package/XML "
                "conditional-formatting append"
            ),
            live_cf_stats=live_stats,
            verification=verification,
            output_zip=Path(zip_out).name if zip_out else None,
            review_queue_rows=0,
            review_rules_rows=int(shell["review_rules_rows"]),
            cf_dictionary_rows_after=int(shell["cf_dictionary_rows"]),
            mode=mode,
            openpyxl_save_used=True,
        )
        _write_provenance_and_zip(
            out=out,
            provenance=provenance,
            provenance_out=provenance_out,
            zip_out=zip_out,
        )
        return GraftResult(
            output_path=str(out),
            provenance=provenance,
            live_cf_stats=live_stats,
            review_queue_rows=0,
            preflight_pass=True,
        )

    if not input_path:
        raise ValueError("--input is required for this mode")

    assert_output_path_allowed(input_path, output_path=output_path)
    if provenance_out:
        assert_output_path_allowed(input_path, output_path=provenance_out)
    if zip_out:
        assert_output_path_allowed(input_path, output_path=zip_out)

    input_name = Path(input_path).name
    out.parent.mkdir(parents=True, exist_ok=True)

    pkg = Package.from_path(input_path)
    scan_path = input_path

    if mode in ("full", "review-only"):
        pkg = graft_review_layer(pkg, input_path)

    queue_rows = (
        build_review_queue(input_path) if mode in ("full", "review-only") else []
    )

    data = pkg.to_bytes()
    if mode in ("full", "live-cf-only"):
        data, live_stats = patch_live_cf(data, scan_path=scan_path)
    else:
        live_stats = {}

    pkg = Package.from_bytes(data)
    remove_calc_chain(pkg)
    remove_external_links(pkg)
    pkg.write(str(out))

    data = out.read_bytes()
    require_review = mode in ("full", "review-only", "blank")
    try:
        verification = run_preflight(data, require_review_layer=require_review)
    except ValueError as exc:
        return GraftResult(
            output_path=str(out),
            provenance={},
            live_cf_stats=live_stats,
            review_queue_rows=len(queue_rows),
            preflight_pass=False,
            errors=[str(exc)],
        )

    method = {
        "full": (
            "zip/xml surgical patch: review graft + append standard CF "
            "to every Live month tab"
        ),
        "review-only": "zip/xml surgical patch: review layer graft only",
        "live-cf-only": (
            "zip/xml surgical patch: append standard CF to every Live month tab"
        ),
    }.get(mode, mode)

    provenance = build_provenance(
        input_workbook=input_name,
        output_workbook=out.name,
        method=method,
        live_cf_stats=live_stats,
        verification=verification,
        output_zip=Path(zip_out).name if zip_out else None,
        review_queue_rows=len(queue_rows),
        mode=mode,
    )
    _write_provenance_and_zip(
        out=out,
        provenance=provenance,
        provenance_out=provenance_out,
        zip_out=zip_out,
    )

    return GraftResult(
        output_path=str(out),
        provenance=provenance,
        live_cf_stats=live_stats,
        review_queue_rows=len(queue_rows),
        preflight_pass=True,
    )
