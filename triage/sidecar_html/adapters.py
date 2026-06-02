"""Build PortalSection lists per artifact engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from triage.sidecar_html.portal import PortalSection


def admin_billing_sections(manifest: Dict[str, Any], out_dir: Path) -> List[PortalSection]:
    sections: List[PortalSection] = []
    sections.append(PortalSection(
        id="run-meta",
        title="Run metadata",
        tab="overview",
        kind="kpis",
        items=[
            {"label": "Engine", "value": manifest.get("engine", "")},
            {"label": "Generated UTC", "value": manifest.get("generated_utc", "")},
            {"label": "Format", "value": manifest.get("format", "")},
        ],
    ))
    for mk, mo in (manifest.get("per_month") or {}).items():
        sections.append(PortalSection(
            id=f"kpi-{mk}",
            title=mo.get("month_name", mk),
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Total net hours", "value": mo.get("total_net")},
                {"label": "Neuron net", "value": mo.get("neuron_net")},
                {"label": "Rows", "value": mo.get("row_count")},
                {"label": "Malformed", "value": mo.get("malformed_count", 0)},
            ],
        ))
        links = []
        for variant, vo in (mo.get("outputs") or {}).items():
            wb = vo.get("workbook", "")
            if wb:
                links.append({"label": f"{mo.get('month_name')} {variant.title()}", "href": Path(wb).as_uri()})
        if links:
            sections.append(PortalSection(
                id=f"links-{mk}",
                title=f"{mo.get('month_name')} workbooks",
                tab="overview",
                kind="links",
                links=links,
            ))
        rq = mo.get("review_queue_csv")
        if rq:
            sections.append(PortalSection(
                id=f"review-{mk}",
                title=f"{mo.get('month_name')} review queue",
                tab="review",
                kind="table",
                csv_path=rq,
                badge_column="Category",
                hint="Overrides, long shifts, unassigned, malformed.",
            ))
        for variant, vo in (mo.get("outputs") or {}).items():
            pf = vo.get("preflight_json")
            if pf:
                import json as _json
                pf_data: Dict[str, Any] = {}
                try:
                    pf_data = _json.loads(Path(pf).read_text(encoding="utf-8"))
                except Exception:
                    pass
                semantic = pf_data.get("semantic_integrity", "NOT_PROVEN")
                sections.append(PortalSection(
                    id=f"pf-kpi-{mk}-{variant}",
                    title=f"Semantic gate — {mo.get('month_name')} {variant}",
                    tab="preflight",
                    kind="kpis",
                    items=[
                        {
                            "label": "Package preflight",
                            "value": "PASS" if pf_data.get("preflight_pass") else "FAIL",
                            "tone": "pass" if pf_data.get("preflight_pass") else "fail",
                        },
                        {
                            "label": "Semantic integrity",
                            "value": semantic,
                            "tone": "pass" if semantic == "PASS" else "fail",
                        },
                        {
                            "label": "Generic strings only",
                            "value": str(pf_data.get("generic_column_strings_only", "—")),
                            "tone": "fail" if pf_data.get("generic_column_strings_only") else "pass",
                        },
                        {
                            "label": "Meaningful strings ratio",
                            "value": pf_data.get("meaningful_shared_string_ratio", "—"),
                        },
                        {
                            "label": "Excel for Web",
                            "value": pf_data.get("excel_for_web_manual_check", "NOT_PROVEN"),
                            "tone": "warn",
                        },
                    ],
                ))
                sections.append(PortalSection(
                    id=f"pf-{mk}-{variant}",
                    title=f"Preflight — {mo.get('month_name')} {variant}",
                    tab="preflight",
                    kind="preflight",
                    json_path=pf,
                ))
        delta = mo.get("delta_vs_prior")
        if delta:
            delta_path = out_dir / f"{_month_stem_from_key(mk)}_Billing_Summary_Internal_delta.json"
            sections.append(PortalSection(
                id=f"delta-{mk}",
                title=f"{mo.get('month_name')} delta vs prior",
                tab="data",
                kind="delta",
                json_path=str(delta_path) if delta_path.is_file() else None,
            ))
    return sections


def _month_stem_from_key(month_key: str) -> str:
    y, m = month_key.split("-")
    from calendar import month_name
    return f"{month_name[int(m)]}_{y}"


def bonita_sections(manifest: Dict[str, Any]) -> List[PortalSection]:
    pf_pass = manifest.get("websafe_preflight_pass")
    pf_data = manifest.get("preflight_data") or {}
    semantic = pf_data.get("semantic_integrity", "NOT_PROVEN")
    sections: List[PortalSection] = [
        PortalSection(
            id="kpi",
            title="Bonita Neuron Track Hours",
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Grand total hours", "value": manifest.get("grand_total_hours")},
                {"label": "Shifts", "value": manifest.get("shift_count")},
                {"label": "Review items", "value": manifest.get("review_item_count")},
                {
                    "label": "Package preflight",
                    "value": "PASS" if pf_pass else "FAIL",
                    "tone": "pass" if pf_pass else "fail",
                },
                {
                    "label": "Semantic integrity",
                    "value": semantic,
                    "tone": "pass" if semantic == "PASS" else "fail",
                },
                {
                    "label": "Excel for Web",
                    "value": pf_data.get("excel_for_web_manual_check", "NOT_PROVEN"),
                    "tone": "warn",
                },
            ],
        ),
    ]
    for mk, pm in (manifest.get("per_month") or {}).items():
        sections.append(PortalSection(
            id=f"month-{mk}",
            title=f"{pm.get('month_name', mk)} ({pm.get('tab', '')})",
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Rows", "value": pm.get("row_count")},
                {"label": "Total hours", "value": pm.get("total_hours")},
            ],
        ))
    outs = manifest.get("outputs") or {}
    if outs.get("workbook"):
        sections.append(PortalSection(
            id="wb",
            title="Workbook",
            tab="overview",
            kind="links",
            links=[{"label": Path(outs["workbook"]).name, "href": Path(outs["workbook"]).as_uri()}],
        ))
    if outs.get("review_queue_csv"):
        sections.append(PortalSection(
            id="review",
            title="Review queue",
            tab="review",
            kind="table",
            csv_path=outs["review_queue_csv"],
            badge_column="Category",
        ))
    if outs.get("preflight_json"):
        sections.append(PortalSection(
            id="pf",
            title="Web Excel preflight",
            tab="preflight",
            kind="preflight",
            json_path=outs["preflight_json"],
        ))
    return sections


def neuron_track_sections(manifest: Dict[str, Any]) -> List[PortalSection]:
    totals = manifest.get("totals") or {}
    sections: List[PortalSection] = [
        PortalSection(
            id="kpi",
            title="Neuron Track Hours",
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Total hours", "value": totals.get("total")},
                {"label": "April", "value": totals.get("april")},
                {"label": "May", "value": totals.get("may")},
                {"label": "Go-live rows", "value": totals.get("go_live_rows")},
                {
                    "label": "Preflight",
                    "value": "PASS" if manifest.get("websafe_preflight_pass") else "FAIL",
                    "tone": "pass" if manifest.get("websafe_preflight_pass") else "fail",
                },
            ],
        ),
    ]
    outs = manifest.get("outputs") or {}
    if outs.get("workbook"):
        sections.append(PortalSection(
            id="wb",
            title="Workbook",
            tab="overview",
            kind="links",
            links=[{"label": Path(outs["workbook"]).name, "href": Path(outs["workbook"]).as_uri()}],
        ))
    if outs.get("review_queue_csv"):
        sections.append(PortalSection(
            id="review",
            title="Review flags queue",
            tab="review",
            kind="table",
            csv_path=outs["review_queue_csv"],
            badge_column="Category",
        ))
    if outs.get("preflight_json"):
        sections.append(PortalSection(
            id="pf",
            title="Web Excel preflight",
            tab="preflight",
            kind="preflight",
            json_path=outs["preflight_json"],
        ))
    if outs.get("reconciliation_json"):
        sections.append(PortalSection(
            id="recon",
            title="Reference reconciliation",
            tab="data",
            kind="json",
            json_path=outs["reconciliation_json"],
        ))
    return sections


def one_marcus_sections(manifest: Dict[str, Any]) -> List[PortalSection]:
    sections: List[PortalSection] = [
        PortalSection(
            id="kpi",
            title="1 Marcus recon",
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Formulas patched", "value": manifest.get("formula_cells_patched")},
                {"label": "Formulas scanned", "value": manifest.get("formula_cells_scanned")},
                {
                    "label": "Preflight",
                    "value": "PASS" if manifest.get("webexcel_preflight_pass") else "FAIL",
                    "tone": "pass" if manifest.get("webexcel_preflight_pass") else "fail",
                },
            ],
        ),
    ]
    side = manifest.get("sidecars") or {}
    if manifest.get("output_workbook"):
        sections.append(PortalSection(
            id="wb",
            title="WEBSAFE workbook",
            tab="overview",
            kind="links",
            links=[{
                "label": Path(manifest["output_workbook"]).name,
                "href": Path(manifest["output_workbook"]).as_uri(),
            }],
        ))
    if side.get("review_queue"):
        sections.append(PortalSection(
            id="review",
            title="Review queue",
            tab="review",
            kind="table",
            csv_path=side["review_queue"],
            badge_column="category",
        ))
    if side.get("preflight"):
        sections.append(PortalSection(
            id="pf",
            title="Preflight",
            tab="preflight",
            kind="preflight",
            json_path=side["preflight"],
        ))
    return sections


def cybernet_sections(manifest: Dict[str, Any]) -> List[PortalSection]:
    sections: List[PortalSection] = [
        PortalSection(
            id="kpi",
            title="Cybernet targets sprint",
            tab="overview",
            kind="kpis",
            items=[
                {"label": "Active targets", "value": manifest.get("total_active_targets")},
                {"label": "As of", "value": manifest.get("as_of")},
                {
                    "label": "Preflight",
                    "value": "PASS" if (manifest.get("preflight") or {}).get("webexcel_preflight_pass") else "FAIL",
                    "tone": "pass" if (manifest.get("preflight") or {}).get("webexcel_preflight_pass") else "fail",
                },
            ],
        ),
    ]
    outs = manifest.get("outputs") or {}
    if outs.get("workbook"):
        sections.append(PortalSection(
            id="wb",
            title="WEBSAFE dashboard",
            tab="overview",
            kind="links",
            links=[{"label": Path(outs["workbook"]).name, "href": Path(outs["workbook"]).as_uri()}],
        ))
    if outs.get("amb_reconciliation_csv"):
        sections.append(PortalSection(
            id="recon",
            title="AMB reconciliation",
            tab="review",
            kind="table",
            csv_path=outs["amb_reconciliation_csv"],
        ))
    if outs.get("shortage_csv"):
        sections.append(PortalSection(
            id="shortage",
            title="Shortage queue",
            tab="review",
            kind="table",
            csv_path=outs["shortage_csv"],
        ))
    if outs.get("targets_json"):
        sections.append(PortalSection(
            id="targets",
            title="Targets JSON (summary)",
            tab="data",
            kind="json",
            json_path=outs["targets_json"],
            hint="Full target list; use filters in table views above when exported as CSV.",
        ))
    return sections
