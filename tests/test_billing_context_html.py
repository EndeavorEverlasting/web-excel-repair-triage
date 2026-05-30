from datetime import date, time
from pathlib import Path

from triage.billing_context.html_dashboard import export_html_dashboard
from triage.billing_context.models import WorkEntry


def test_html_dashboard_exports(tmp_path):
    entries = [
        WorkEntry(
            source="x.xlsx",
            sheet_name="May",
            row_number=2,
            tech="Example Tech",
            work_date=date(2026, 5, 30),
            start_time=time(9, 0),
            end_time=time(17, 0),
            hours=8,
            original_assignment="Neuron Installation",
            work_context="Inventory Management",
            context_reason="May+ Saturday rule applied.",
        )
    ]

    out = tmp_path / "dashboard.html"
    export_html_dashboard(entries, [], str(out))

    text = out.read_text(encoding="utf-8")
    assert "Billing Context Dashboard" in text
    assert "Inventory Management" in text
    assert "no Office license required" in text
    assert "https://" not in text
