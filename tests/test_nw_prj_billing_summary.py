"""NW PRJ April/May billing summary engine tests — fixture-only, no private data."""
from __future__ import annotations

import csv
import json
import zipfile
from datetime import date
from pathlib import Path

import openpyxl
import pytest

from tests.fixtures.nw_prj_billing_summary.fixtures import (
    SAMPLE_INVOICES,
    build_fixtures,
)
from triage.nw_prj_billing_summary.classifier import friday_batch, is_excluded_name
from triage.nw_prj_billing_summary.exporter import run_export

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "nw_prj_billing_summary"
MONTHS = ["2026-04", "2026-05"]


@pytest.fixture(scope="module")
def fixtures():
    return build_fixtures(FIXTURE_DIR)


@pytest.fixture(scope="module")
def result(fixtures, tmp_path_factory):
    out = tmp_path_factory.mktemp("billing_out")
    return run_export(
        str(fixtures["roster"]),
        MONTHS,
        str(out),
        websafe=True,
        make_zip=True,
        invoices=SAMPLE_INVOICES,
    )


def _all_cell_text(wb_path: Path) -> str:
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    chunks = []
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            chunks.extend(str(c) for c in row if c is not None)
    wb.close()
    return "\n".join(chunks)


# 1. CLI/engine generates workbook + all sidecars + ZIP.
def test_generates_all_artifacts(result):
    o = result.outputs
    assert Path(o["workbook"]).exists()
    assert Path(o["manifest"]).exists()
    assert Path(o["review_queue"]).exists()
    assert Path(o["preflight"]).exists()
    assert Path(o["delivery_zip"]).exists()
    names = zipfile.ZipFile(o["delivery_zip"]).namelist()
    assert any(n.endswith(".xlsx") for n in names)


# 2. April and May rows are both represented.
def test_both_months_present(result):
    keys = {ms.month_key for ms in result.report.month_summaries}
    assert keys == {"2026-04", "2026-05"}
    months_in_rows = {r.month_key for r in result.report.rows}
    assert months_in_rows == {"2026-04", "2026-05"}


# 3. Friday batch mapping for weekdays.
def test_friday_batch_weekday():
    assert friday_batch(date(2026, 4, 1)) == date(2026, 4, 3)   # Wed -> that Fri
    assert friday_batch(date(2026, 5, 1)) == date(2026, 5, 1)   # Fri -> itself


# 4. Weekend rows roll to the next Friday batch.
def test_weekend_rolls_to_next_friday(result):
    assert friday_batch(date(2026, 4, 4)) == date(2026, 4, 10)  # Sat -> next Fri
    assert friday_batch(date(2026, 5, 2)) == date(2026, 5, 8)
    carol = [r for r in result.report.rows if r.staff == "Carol Tech"][0]
    assert carol.weekend is True
    assert carol.friday_batch == date(2026, 4, 10)


# 5. Note-bearing punch cells parse without failing (hours still computed).
def test_note_bearing_punch_parses(result):
    beta = [r for r in result.report.rows if r.staff == "Beta Tech"][0]
    assert beta.gross_hours == 4.0
    assert "Bonita" in beta.note


# 6. Notes preserved in review data but not in the admin workbook.
def test_notes_in_review_not_in_workbook(result):
    cats = {(f.category, f.staff) for f in result.report.review_flags}
    assert ("note_bearing", "Beta Tech") in cats
    text = _all_cell_text(Path(result.outputs["workbook"]))
    assert "Bonita" not in text


# 7. Worked-project override beats default project assignment.
def test_override_beats_default(result):
    beta = [r for r in result.report.rows if r.staff == "Beta Tech"][0]
    assert beta.project == "Admin Project Team"
    assert beta.project_source == "worked"


# 8. Excluded non-member names do not leak into Project Team totals.
def test_excluded_names_do_not_leak(result):
    assert is_excluded_name("Yostinn Minaya")
    assert is_excluded_name("Steven Marques (Inventory)")
    staff_in_rows = {r.staff for r in result.report.rows}
    assert "Yostinn Minaya" not in staff_in_rows
    assert "Steven Marques (Inventory)" not in staff_in_rows
    assert any(f.category == "excluded_name" for f in result.report.review_flags)
    text = _all_cell_text(Path(result.outputs["workbook"]))
    assert "Yostinn Minaya" not in text


# 9. Partial-hour rows are flagged for review and kept out of admin totals.
def test_partial_rows_flagged(result):
    assert any(
        f.category == "partial_hours" and f.staff == "Dan Tech"
        for f in result.report.review_flags
    )
    assert "Dan Tech" not in {r.staff for r in result.report.rows}


# 10. Rich Perez short day is NOT downgraded/flagged (pinned full-day guard).
def test_rich_guard_not_flagged(result):
    rich = [r for r in result.report.rows if r.staff == "Rich Perez"][0]
    assert rich.gross_hours == 3.0
    assert not any(
        f.category == "partial_hours" and f.staff == "Rich Perez"
        for f in result.report.review_flags
    )


# 11. Combined totals are exact and Web Excel preflight passes.
def test_totals_and_preflight(result):
    assert result.report.combined_gross == 33.0
    assert result.report.combined_lunch == 2.0
    assert result.report.combined_net == 31.0
    assert result.report.webexcel_preflight_pass is True
    pre = json.loads(Path(result.outputs["preflight"]).read_text())
    assert pre["preflight_pass"] is True
    assert pre["token_failures"] == []
    assert pre["has_calc_chain"] is False


# 12. No stop-ship tokens / calc chain / external links in the package.
def test_no_stopship_tokens(result):
    with zipfile.ZipFile(result.outputs["workbook"]) as z:
        names = z.namelist()
        assert "xl/calcChain.xml" not in names
        assert not [n for n in names if n.startswith("xl/externalLinks/")]
        blob = "".join(
            z.read(n).decode("utf-8", "ignore")
            for n in names if n.endswith(".xml")
        )
        for tok in ("inlineStr", "ns0:", "xmlns:ns0"):
            assert tok not in blob


# Bonus: invoice pivot rolls up by category/vendor and review CSV has a header.
def test_invoice_pivot_and_review_csv(result):
    assert result.report.invoice_count == 3
    text = _all_cell_text(Path(result.outputs["workbook"]))
    assert "Cabling" in text and "Globex Logistics" in text
    with open(result.outputs["review_queue"], newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ["category", "staff", "date", "detail"]
