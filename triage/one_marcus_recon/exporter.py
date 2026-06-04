"""Orchestrates the recon relink pipeline and writes the delivery package."""
from __future__ import annotations

import csv
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from triage.xlsx_utils import fix_inlinestr

from . import date_inference as di
from . import formula_relink as fr
from . import preflight as pf
from .generator import build_workbook, load_snapshot
from .models import ReconChange, ReconReport
from .operational_checks import run_operational_checks
from .package_cleanup import (
    Package,
    broken_relationship_targets,
    remove_calc_chain,
    remove_external_links,
)

from .style_pass import apply_style_pass

_DATED_PN = re.compile(r"^\s*\d{1,2}-\d{1,2}-\d{4}\s+part\s+numbers\s*$", re.IGNORECASE)


@dataclass
class ReconResult:
    report: ReconReport
    outputs: Dict[str, str] = field(default_factory=dict)


def _sidecar_base(output_path: str) -> Path:
    out = Path(output_path)
    stem = out.stem
    if stem.endswith("_WEBSAFE"):
        stem = stem[: -len("_WEBSAFE")]
    return out.with_name(stem)


def run_recon(
    input_path: str,
    *,
    output_path: str,
    cli_date: str = "auto",
    part_number_tab: Optional[str] = None,
    pivot_tab: Optional[str] = None,
    dry_run: bool = False,
    strict: bool = False,
) -> ReconResult:
    report = ReconReport(input_workbook=str(Path(input_path).resolve()), dry_run=dry_run, mode="relink")

    pkg = Package.from_path(input_path)
    wb_xml = pkg.text("xl/workbook.xml")
    sheet_names = fr.workbook_sheet_names(wb_xml)
    report.pivot_tab = pivot_tab or (sheet_names[0] if sheet_names else "")

    # --- date inference ---
    chosen, candidates, warnings = di.infer_update_date(
        input_path, cli_date, sheet_names, strict=strict
    )
    report.inferred_update_date = chosen.date_iso
    report.date_source = chosen.source
    report.date_candidates = [
        {"date": c.date_iso, "source": c.source, "raw": c.raw} for c in candidates
    ]
    report.warnings.extend(warnings)
    target_label = chosen.tab_label
    report.final_part_number_tab = target_label

    # --- pick + rename the source Part Numbers tab ---
    source_tab = fr.choose_source_tab(
        sheet_names,
        explicit_tab=part_number_tab,
        chosen_date_iso=chosen.date_iso,
        target_label=target_label,
    )
    if source_tab:
        wb_xml, renamed = fr.rename_tab(wb_xml, source_tab, target_label)
        if renamed:
            report.renamed_tabs.append(f"{source_tab} -> {target_label}")
            report.add_change(
                ReconChange("rename_tab", f"{source_tab} -> {target_label}", source_tab, 1)
            )
    else:
        report.warnings.append("no Part Numbers candidate tab detected")

    extra_source = source_tab if (source_tab and not _DATED_PN.match(source_tab)) else None

    # --- rewrite formulas across worksheets ---
    total_scanned = total_patched = total_localized = 0
    remaining_ext: List[str] = []
    for ws in pkg.worksheet_parts():
        text = pkg.text(ws)
        new_text, scanned, patched, localized, ext = fr.rewrite_sheet_formulas(
            text, target_label, extra_source
        )
        total_scanned += scanned
        total_patched += patched
        total_localized += localized
        remaining_ext.extend(ext)
        if new_text != text:
            pkg.set_text(ws, new_text)
    # Defined names can also carry references.
    wb_xml = re.sub(
        r"(<definedName\b[^>]*>)(.*?)(</definedName>)",
        lambda m: m.group(1)
        + fr._rewrite_refs_in_text(m.group(2), target_label, extra_source)[0]
        + m.group(3),
        wb_xml,
        flags=re.DOTALL,
    )
    pkg.set_text("xl/workbook.xml", wb_xml)

    report.formula_cells_scanned = total_scanned
    report.formula_cells_patched = total_patched
    report.stale_tab_references_removed = total_patched
    if total_patched:
        report.add_change(
            ReconChange("rewrite_formula", f"repointed to '{target_label}'", count=total_patched)
        )
    if total_localized:
        report.add_change(
            ReconChange("localize_external", "dropped external index prefix", count=total_localized)
        )

    # --- package cleanup ---
    if remove_calc_chain(pkg):
        report.calc_chain_removed = True
        report.add_change(ReconChange("remove_part", "xl/calcChain.xml"))

    # Only strip external link parts when nothing still references them.
    if remaining_ext:
        report.remaining_external_links = sorted(set(remaining_ext))
        report.warnings.append(
            "external references remain after rewrite; external link parts preserved"
        )
    else:
        removed = remove_external_links(pkg)
        if removed:
            report.external_link_parts_removed = removed
            for n in removed:
                report.add_change(ReconChange("remove_part", n))

    # --- write patched workbook (or temp for dry-run preflight) ---
    base = _sidecar_base(output_path)
    out_dir = base.parent
    if not dry_run:
        pkg.write(output_path)
        report.output_workbook = str(Path(output_path).resolve())
        scan_path = output_path
        cleanup_tmp = None
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp.write(pkg.to_bytes())
        tmp.close()
        scan_path = tmp.name
        cleanup_tmp = tmp.name

    # Web Excel safety: eliminate any inlineStr tokens (surgical zip patch).
    fix_inlinestr(scan_path)

    # --- preflight ---
    pre = pf.run_preflight(scan_path, target_part_number_tab=target_label)
    report.webexcel_preflight_pass = pre.preflight_pass
    report.formula_error_scan = pre.error_value_failures
    report.remaining_stale_tab_references = pre.stale_dated_refs
    if pre.token_failures:
        report.warnings.append(f"stop-ship tokens: {pre.token_failures}")
    if pre.broken_relationships:
        report.warnings.append(f"broken relationships: {pre.broken_relationships}")
    report.remaining_external_links = sorted(
        set(report.remaining_external_links) | set(pre.external_link_parts)
    )

    result = ReconResult(report=report)
    if dry_run:
        if cleanup_tmp:
            Path(cleanup_tmp).unlink(missing_ok=True)
        return result

    # --- sidecars ---
    out_dir.mkdir(parents=True, exist_ok=True)
    pre_path = out_dir / f"{base.name}_preflight.json"
    manifest_path = out_dir / f"{base.name}_manifest.json"
    review_path = out_dir / f"{base.name}_review_queue.csv"
    carry_path = out_dir / f"{base.name}_carryover.md"
    zip_path = out_dir / f"{base.name}_DELIVERY.zip"

    pre_path.write_text(json.dumps(pre.to_dict(), indent=2), encoding="utf-8")
    manifest = {
        "input_workbook": report.input_workbook,
        "output_workbook": report.output_workbook,
        "inferred_update_date": report.inferred_update_date,
        "date_source": report.date_source,
        "final_part_number_tab": report.final_part_number_tab,
        "pivot_tab": report.pivot_tab,
        "renamed_tabs": report.renamed_tabs,
        "formula_cells_scanned": report.formula_cells_scanned,
        "formula_cells_patched": report.formula_cells_patched,
        "external_link_parts_removed": report.external_link_parts_removed,
        "calc_chain_removed": report.calc_chain_removed,
        "webexcel_preflight_pass": report.webexcel_preflight_pass,
        "sidecars": {
            "preflight": str(pre_path.resolve()),
            "review_queue": str(review_path.resolve()),
            "carryover": str(carry_path.resolve()),
            "delivery_zip": str(zip_path.resolve()),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_review_queue(review_path, report, pre)

    from triage.sidecar_html.adapters import one_marcus_sections
    from triage.sidecar_html.portal import build_run_portal

    portal_path = build_run_portal(
        out_dir,
        title="1 Marcus Recon — Run Review",
        subtitle=report.input_workbook,
        sections=one_marcus_sections(manifest),
    )
    manifest["html_portal"] = str(portal_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_carryover(carry_path, report, pre)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(output_path, Path(output_path).name)
        z.write(pre_path, pre_path.name)
        z.write(manifest_path, manifest_path.name)
        z.write(review_path, review_path.name)
        z.write(carry_path, carry_path.name)
        z.write(portal_path, portal_path.name)

    result.outputs = {
        "workbook": str(Path(output_path).resolve()),
        "preflight": str(pre_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "review_queue": str(review_path.resolve()),
        "carryover": str(carry_path.resolve()),
        "delivery_zip": str(zip_path.resolve()),
        "html_portal": str(portal_path.resolve()),
    }
    return result


def run_generate(
    input_path: str,
    *,
    output_path: str,
    cli_date: str = "auto",
    part_number_tab: Optional[str] = None,
    dry_run: bool = False,
    strict: bool = False,
) -> ReconResult:
    """Clean-render a full recon workbook from an integrated source spreadsheet."""
    report = ReconReport(
        input_workbook=str(Path(input_path).resolve()),
        dry_run=dry_run,
        mode="generate",
        pivot_tab="1M Recon Pivot Module",
    )
    snapshot = load_snapshot(
        input_path,
        cli_date=cli_date,
        part_number_tab=part_number_tab,
        strict=strict,
    )
    report.inferred_update_date = snapshot.inferred_date
    report.date_source = snapshot.date_source
    report.final_part_number_tab = "Part Numbers"
    report.rollup_key_count = len(snapshot.rollup_keys)
    report.warnings.extend(snapshot.warnings)
    if not snapshot.rollup_keys:
        report.warnings.append("no rollup keys found in included Part Numbers rows")

    if dry_run:
        report.add_change(
            ReconChange(
                "generate",
                f"would render {len(snapshot.rollup_keys)} rollup keys to {output_path}",
                count=len(snapshot.rollup_keys),
            )
        )
        return ReconResult(report=report)

    build_workbook(snapshot, output_path, source_path=input_path)
    apply_style_pass(output_path)
    fix_inlinestr(output_path)
    report.output_workbook = str(Path(output_path).resolve())

    pre = pf.run_preflight(output_path, target_part_number_tab="Part Numbers")
    report.webexcel_preflight_pass = pre.preflight_pass
    report.formula_error_scan = pre.error_value_failures
    report.remaining_stale_tab_references = pre.stale_dated_refs

    ops = run_operational_checks(output_path)
    report.operational_pass = ops.operational_pass
    report.operational_failures = list(ops.failures)

    result = ReconResult(report=report)
    base = _sidecar_base(output_path)
    out_dir = base.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pre_path = out_dir / f"{base.name}_preflight.json"
    manifest_path = out_dir / f"{base.name}_manifest.json"
    review_path = out_dir / f"{base.name}_review_queue.csv"
    carry_path = out_dir / f"{base.name}_carryover.md"
    zip_path = out_dir / f"{base.name}_DELIVERY.zip"
    ops_path = out_dir / f"{base.name}_operational.json"

    pre_payload = pre.to_dict()
    pre_payload["operational"] = ops.to_dict()
    pre_path.write_text(json.dumps(pre_payload, indent=2), encoding="utf-8")
    ops_path.write_text(json.dumps(ops.to_dict(), indent=2), encoding="utf-8")

    manifest = {
        "mode": "generate",
        "input_workbook": report.input_workbook,
        "output_workbook": report.output_workbook,
        "inferred_update_date": report.inferred_update_date,
        "date_source": report.date_source,
        "final_part_number_tab": report.final_part_number_tab,
        "pivot_tab": report.pivot_tab,
        "rollup_key_count": len(snapshot.rollup_keys),
        "webexcel_preflight_pass": report.webexcel_preflight_pass,
        "operational_pass": report.operational_pass,
        "operational_failures": report.operational_failures,
        "sidecars": {
            "preflight": str(pre_path.resolve()),
            "operational": str(ops_path.resolve()),
            "review_queue": str(review_path.resolve()),
            "carryover": str(carry_path.resolve()),
            "delivery_zip": str(zip_path.resolve()),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _write_review_queue_generate(review_path, report, pre, ops)
    _write_carryover_generate(carry_path, report, pre, ops)

    from triage.sidecar_html.adapters import one_marcus_sections
    from triage.sidecar_html.portal import build_run_portal

    portal_path = build_run_portal(
        out_dir,
        title="1 Marcus Recon — Generate Review",
        subtitle=report.input_workbook,
        sections=one_marcus_sections(manifest),
    )
    manifest["html_portal"] = str(portal_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(output_path, Path(output_path).name)
        z.write(pre_path, pre_path.name)
        z.write(ops_path, ops_path.name)
        z.write(manifest_path, manifest_path.name)
        z.write(review_path, review_path.name)
        z.write(carry_path, carry_path.name)
        z.write(portal_path, portal_path.name)

    result.outputs = {
        "workbook": str(Path(output_path).resolve()),
        "preflight": str(pre_path.resolve()),
        "operational": str(ops_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "review_queue": str(review_path.resolve()),
        "carryover": str(carry_path.resolve()),
        "delivery_zip": str(zip_path.resolve()),
        "html_portal": str(portal_path.resolve()),
    }
    return result


def _write_review_queue_generate(
    path: Path,
    report: ReconReport,
    pre: pf.ReconPreflight,
    ops,
) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "detail"])
        for fail in ops.failures:
            w.writerow(["operational_failure", fail])
        for err in report.formula_error_scan:
            w.writerow(["formula_error", err])
        for tok in pre.token_failures:
            w.writerow(["stop_ship_token", tok])
        for warn in report.warnings:
            w.writerow(["warning", warn])


def _write_carryover_generate(
    path: Path,
    report: ReconReport,
    pre: pf.ReconPreflight,
    ops,
) -> None:
    lines = [
        f"# 1 Marcus Recon Generate — {report.inferred_update_date}",
        "",
        f"- Input: `{Path(report.input_workbook).name}`",
        f"- Output: `{Path(report.output_workbook).name}`",
        f"- Part Numbers tab: `{report.final_part_number_tab}`",
        f"- Package preflight: **{report.webexcel_preflight_pass}**",
        f"- Operational pass: **{report.operational_pass}**",
        "",
        "## Operational failures",
        "",
    ]
    if ops.failures:
        lines.extend(f"- {f}" for f in ops.failures)
    else:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_review_queue(path: Path, report: ReconReport, pre: pf.ReconPreflight) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "detail"])
        for ref in report.remaining_stale_tab_references:
            w.writerow(["stale_dated_reference", ref])
        for ext in report.remaining_external_links:
            w.writerow(["remaining_external_link", ext])
        for err in report.formula_error_scan:
            w.writerow(["formula_error", err])
        for tok in pre.token_failures:
            w.writerow(["stop_ship_token", tok])
        for rel in pre.broken_relationships:
            w.writerow(["broken_relationship", rel])
        for warn in report.warnings:
            w.writerow(["warning", warn])


def _write_carryover(path: Path, report: ReconReport, pre: pf.ReconPreflight) -> None:
    lines = [
        f"# 1 Marcus Recon Carryover — {report.inferred_update_date}",
        "",
        f"- Input: `{Path(report.input_workbook).name}`",
        f"- Output: `{Path(report.output_workbook).name if report.output_workbook else '(dry-run)'}`",
        f"- Update date: {report.inferred_update_date} (source: {report.date_source})",
        f"- Target Part Numbers tab: `{report.final_part_number_tab}`",
        f"- Pivot tab: `{report.pivot_tab}`",
        f"- Preflight pass: **{report.webexcel_preflight_pass}**",
        "",
        "## Changes applied",
        "",
        f"- Renamed tabs: {report.renamed_tabs or 'none'}",
        f"- Formula cells scanned: {report.formula_cells_scanned}",
        f"- Formula references repointed: {report.formula_cells_patched}",
        f"- External link parts removed: {report.external_link_parts_removed or 'none'}",
        f"- calcChain removed: {report.calc_chain_removed}",
        "",
        "## Review queue",
        "",
        f"- Remaining stale dated refs: {report.remaining_stale_tab_references or 'none'}",
        f"- Remaining external links: {report.remaining_external_links or 'none'}",
        f"- Formula errors: {report.formula_error_scan or 'none'}",
        f"- Warnings: {report.warnings or 'none'}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
