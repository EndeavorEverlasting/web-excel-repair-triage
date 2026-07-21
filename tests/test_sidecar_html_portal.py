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


def test_portal_escapes_closing_script_in_payload(tmp_path):
    """A </script> payload in section data must be neutralised, not emitted raw.

    The embedded JSON lives inside a <script> block; an unescaped </script> in
    any value would close that block early and allow injected markup to run.
    """
    payload = PortalSection(
        id="xss",
        title="XSS test",
        tab="overview",
        kind="kpis",
        items=[{"label": "attack", "value": "</script><script>alert(1)</script>"}],
    )
    html = build_run_portal(
        tmp_path, "Payload Portal", sections=[payload]
    ).read_text(encoding="utf-8")
    # Raw closing-tag payload must not appear verbatim (it would break the embed).
    assert "</script><script>alert(1)</script>" not in html
    # The dangerous "</" sequence is neutralised to "<\/".
    assert "<\\/script>" in html


def test_portal_surfaces_semantic_failure(tmp_path):
    """Preflight JSON with semantic_integrity FAIL must appear in rendered HTML."""
    json_path = tmp_path / "preflight_semantic_fail.json"
    json_path.write_text(
        json.dumps({
            "preflight_pass": False,
            "artifact": "test.xlsx",
            "semantic_integrity": "FAIL",
            "sentinel_failures": ["Start Here!A1 is blank", "generic_column_strings_only:all_shared_strings_are_ColumnN"],
            "generic_column_strings_only": True,
            "meaningful_shared_string_ratio": 0.0,
            "excel_for_web_manual_check": "NOT_PROVEN",
        }),
        encoding="utf-8",
    )
    sections = [
        PortalSection(
            id="pf",
            title="Preflight",
            tab="preflight",
            kind="preflight",
            json_path=str(json_path),
        ),
    ]
    path = build_run_portal(tmp_path, "Semantic Failure Portal", sections=sections)
    html = path.read_text(encoding="utf-8")
    assert "semantic_integrity" in html
    assert "FAIL" in html
    assert "sentinel_failures" in html
    assert "NOT_PROVEN" in html


def test_admin_billing_manifest_portal(tmp_path_factory):
    from tests.fixtures.admin_billing_summary.builders import build
    from triage.admin_billing_summary.cli import run

    fx = build(Path(__file__).resolve().parent / "fixtures" / "admin_billing_summary")
    root = tmp_path_factory.mktemp("portal_repo")
    out = root / "Outputs" / "admin_billing_summary" / "portal_run"
    out.mkdir(parents=True)
    manifest = run(
        roster_log=str(fx["roster"]),
        out_dir=str(out),
        repo_root=root,
        months=["2026-04"],
        websafe=True,
    )
    portal = Path(manifest["html_portal"])
    assert portal.is_file()
    assert "Admin Billing Summary" in portal.read_text(encoding="utf-8")
