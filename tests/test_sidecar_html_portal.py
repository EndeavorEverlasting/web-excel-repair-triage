"""HTML sidecar portal tests."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from triage.sidecar_html.portal import PortalSection, build_run_portal


def test_build_portal_from_fixture_csv_json(tmp_path):
    csv_path = tmp_path / "review.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Category", "Tech", "Note"])
        w.writeheader()
        w.writerow({"Category": "long_shift", "Tech": "Solo Vant", "Note": "17h"})

    json_path = tmp_path / "preflight.json"
    json_path.write_text(
        json.dumps({"preflight_pass": True, "artifact": "test.xlsx"}),
        encoding="utf-8",
    )

    sections = [
        PortalSection(
            id="kpi",
            title="KPIs",
            tab="overview",
            kind="kpis",
            items=[{"label": "Rows", "value": 1}],
        ),
        PortalSection(
            id="review",
            title="Review",
            tab="review",
            kind="table",
            csv_path=str(csv_path),
            badge_column="Category",
        ),
        PortalSection(
            id="pf",
            title="Preflight",
            tab="preflight",
            kind="preflight",
            json_path=str(json_path),
        ),
    ]
    path = build_run_portal(tmp_path, "Test Portal", sections=sections)
    html = path.read_text(encoding="utf-8")
    assert path.name == "index.html"
    assert "Test Portal" in html
    assert "long_shift" in html
    assert "preflight_pass" in html
    assert "<\\/script>" not in html or "</script>" in html  # escaped payload


def test_admin_billing_manifest_portal(tmp_path_factory):
    from tests.fixtures.admin_billing_summary.builders import build
    from triage.admin_billing_summary.cli import run

    fx = build(Path(__file__).resolve().parent / "fixtures" / "admin_billing_summary")
    out = tmp_path_factory.mktemp("portal_out")
    manifest = run(
        roster_log=str(fx["roster"]),
        out_dir=str(out),
        months=["2026-04"],
        websafe=True,
    )
    portal = Path(manifest["html_portal"])
    assert portal.is_file()
    assert "Admin Billing Summary" in portal.read_text(encoding="utf-8")
