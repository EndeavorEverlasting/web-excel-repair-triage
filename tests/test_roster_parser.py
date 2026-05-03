"""
tests/test_roster_parser.py
----------------------------
Unit and integration tests for triage.roster_parser.

Coverage
--------
  T1  _time_to_hours — standard datetime.time input
  T2  _time_to_hours — datetime.datetime input
  T3  _time_to_hours — Excel float fraction input
  T4  _time_to_hours — None input
  T5  _time_to_hours — annotated string "9:28:00 AM/ Bonita"  (real-file quirk)
  T6  _time_to_hours — plain AM/PM string "5:00:00 PM"
  T7  _time_to_hours — 24-h string without AM/PM "17:00:00"
  T8  _time_to_hours — HH:MM string without seconds "9:28 AM/note"
  T9  _time_to_hours — midnight AM edge case "12:00:00 AM"
  T10 _time_to_hours — noon PM edge case "12:00:00 PM"
  T11 _time_to_hours — unrecognisable string returns None
  T12 _time_to_hours — invalid int (e.g. 8) returns None (not a fraction)
  T13 parse_roster — smoke test against live April 2026 roster file
  T14 parse_roster — Patricia Marrero Apr 30 record parsed (was the bug)
  T15 parse_roster — zero malformed rows on April 2026 file
"""
from __future__ import annotations

import datetime
import os
from pathlib import Path

import pytest

from triage.roster_parser import _time_to_hours, parse_roster, RosterParseError

_ROSTER = Path(__file__).parent.parent / "attached_assets" / (
    "Active_Roster_Log_5_1_2026_Billing_April_Pack_(1)_1777807743057.xlsx"
)
_ROSTER_PRESENT = _ROSTER.exists()

# ── _time_to_hours unit tests ─────────────────────────────────────────────────

class TestTimeToHours:
    def test_datetime_time(self):
        assert _time_to_hours(datetime.time(9, 30)) == pytest.approx(9.5)

    def test_datetime_time_with_seconds(self):
        assert _time_to_hours(datetime.time(9, 28, 0)) == pytest.approx(9 + 28/60, rel=1e-6)

    def test_datetime_datetime(self):
        dt = datetime.datetime(2026, 4, 1, 17, 0, 0)
        assert _time_to_hours(dt) == pytest.approx(17.0)

    def test_excel_float_fraction(self):
        # 0.5 = noon in Excel's serial-time system
        assert _time_to_hours(0.5) == pytest.approx(12.0)

    def test_none_returns_none(self):
        assert _time_to_hours(None) is None

    # ── string branch (new in this fix) ──────────────────────────────────────

    def test_string_annotated_am_time(self):
        """Real-file value: '9:28:00 AM/ Bonita' — appended note must be ignored."""
        result = _time_to_hours("9:28:00 AM/ Bonita")
        assert result == pytest.approx(9 + 28/60, rel=1e-6)

    def test_string_pm_time(self):
        assert _time_to_hours("5:00:00 PM") == pytest.approx(17.0)

    def test_string_24h_no_ampm(self):
        assert _time_to_hours("17:00:00") == pytest.approx(17.0)

    def test_string_hhmm_no_seconds(self):
        result = _time_to_hours("9:28 AM/note")
        assert result == pytest.approx(9 + 28/60, rel=1e-6)

    def test_string_midnight_am(self):
        """12:xx AM should be treated as 0:xx (midnight)."""
        assert _time_to_hours("12:00:00 AM") == pytest.approx(0.0)

    def test_string_noon_pm(self):
        """12:xx PM should stay 12:xx (not add 12)."""
        assert _time_to_hours("12:00:00 PM") == pytest.approx(12.0)

    def test_string_no_time_returns_none(self):
        assert _time_to_hours("N/A") is None

    def test_string_empty_returns_none(self):
        assert _time_to_hours("") is None

    def test_large_int_returns_none(self):
        """Integers ≥2 are not Excel time fractions; should return None."""
        assert _time_to_hours(8) is None

    def test_string_dash_note(self):
        """Dash-separated annotation like '8:30 AM - note here'."""
        assert _time_to_hours("8:30 AM - note here") == pytest.approx(8.5)


# ── Integration: parse_roster against the live April 2026 file ───────────────

@pytest.mark.skipif(not _ROSTER_PRESENT, reason="Live roster asset not present")
class TestParseRosterApril2026:
    @pytest.fixture(scope="class")
    def april_records(self):
        malformed: list[str] = []
        records = parse_roster(
            str(_ROSTER),
            target_month="April 2026",
            malformed_out=malformed,
        )
        return records, malformed

    def test_non_empty(self, april_records):
        records, _ = april_records
        assert len(records) > 0, "Expected at least one parsed record"

    def test_expected_staff_count(self, april_records):
        records, _ = april_records
        staffs = {r["staff"] for r in records}
        assert len(staffs) == 12

    def test_known_staff_present(self, april_records):
        records, _ = april_records
        staffs = {r["staff"] for r in records}
        for name in ("Alejandro Perales", "Geoff Gerber", "Patricia Marrero"):
            assert name in staffs, f"Expected staff member '{name}' not found"

    def test_zero_malformed_rows(self, april_records):
        """No rows should be dropped as malformed after the string-time fix."""
        _, malformed = april_records
        assert malformed == [], f"Unexpected malformed rows: {malformed}"

    def test_patricia_marrero_apr30_parsed(self, april_records):
        """Patricia Marrero's Apr 30 record was the triggering bug — verify present."""
        records, _ = april_records
        target = datetime.date(2026, 4, 30)
        pm_apr30 = [
            r for r in records
            if r["staff"] == "Patricia Marrero" and r["date"] == target
        ]
        assert len(pm_apr30) == 1, "Patricia Marrero Apr 30 record missing"
        rec = pm_apr30[0]
        assert rec["clock_in"]  == pytest.approx(9 + 28/60, rel=1e-4)
        assert rec["clock_out"] == pytest.approx(18.0)
        assert rec["gross_hours"] == pytest.approx(8.5333, rel=1e-3)
        assert rec["net_hours"]   == pytest.approx(7.5333, rel=1e-3)

    def test_record_schema(self, april_records):
        """Every record has the required keys with correct types."""
        records, _ = april_records
        required_keys = {
            "staff", "project", "date",
            "clock_in", "clock_out",
            "gross_hours", "lunch_deduction", "net_hours",
        }
        for rec in records:
            assert required_keys == set(rec.keys()), f"Unexpected record keys: {rec.keys()}"
            assert isinstance(rec["staff"],  str)
            assert isinstance(rec["date"],   datetime.date)
            assert isinstance(rec["net_hours"], float)

    def test_all_dates_in_april(self, april_records):
        records, _ = april_records
        for rec in records:
            assert rec["date"].month == 4, (
                f"Expected April date, got {rec['date']} for {rec['staff']}"
            )
            assert rec["date"].year == 2026

    def test_net_hours_positive(self, april_records):
        records, _ = april_records
        for rec in records:
            assert rec["net_hours"] >= 0.0, (
                f"Negative net hours for {rec['staff']} on {rec['date']}"
            )


# ── Synthetic workbook tests: missing sheet, missing columns, lunch deduction ──

class TestRosterParserSynthetic:
    """Tests using minimal in-memory workbooks — no live asset required."""

    def _build_wb(self, tmp_path, sheet_name: str, headers: list, rows: list):
        """Create a minimal roster workbook with the given sheet/header/row layout."""
        import openpyxl as _xl
        wb = _xl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        ws.append(["Attendance Log — Test"])      # row 1: title
        ws.append(headers)                         # row 2: headers
        for row in rows:
            ws.append(row)                         # row 3+: data
        path = str(tmp_path / "roster.xlsx")
        wb.save(path)
        return path

    def test_missing_live_sheet_raises(self, tmp_path):
        """Workbook with no 'Live - ...' sheet must raise RosterParseError."""
        import openpyxl as _xl
        wb = _xl.Workbook()
        wb.active.title = "Summary"
        path = str(tmp_path / "no_live.xlsx")
        wb.save(path)
        with pytest.raises(RosterParseError, match="[Ll]ive"):
            parse_roster(path)

    def test_missing_staff_column_raises(self, tmp_path):
        """Sheet that has no 'Staff Name' column must raise RosterParseError."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[[datetime.time(9, 0), datetime.time(17, 0)]],
        )
        with pytest.raises(RosterParseError, match="[Ss]taff"):
            parse_roster(path)

    def test_missing_date_columns_raises(self, tmp_path):
        """Sheet with only Staff Name column and no date columns raises RosterParseError."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project"],
            rows=[["Test Worker", "Alpha"]],
        )
        with pytest.raises(RosterParseError, match="[Dd]ate"):
            parse_roster(path)

    def test_target_month_not_found_raises(self, tmp_path):
        """Requesting a month that has no matching Live sheet raises RosterParseError."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Test Worker", "Alpha", datetime.time(9, 0), datetime.time(17, 0)]],
        )
        with pytest.raises(RosterParseError, match="[Ll]ive|[Mm]atching"):
            parse_roster(path, target_month="March 2026")

    def test_happy_path_parses_record(self, tmp_path):
        """Valid workbook with one staff member produces one record."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Jane Doe", "Alpha", datetime.time(9, 0), datetime.time(17, 0)]],
        )
        records = parse_roster(path, target_month="April 2026")
        assert len(records) == 1
        rec = records[0]
        assert rec["staff"] == "Jane Doe"
        assert rec["project"] == "Alpha"
        assert rec["gross_hours"] == pytest.approx(8.0)

    def test_lunch_deduction_under_six_hours(self, tmp_path):
        """Shifts under 6h receive no lunch deduction."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Short Worker", "Beta", datetime.time(9, 0), datetime.time(13, 0)]],
        )
        records = parse_roster(path, target_month="April 2026")
        assert len(records) == 1
        assert records[0]["lunch_deduction"] == pytest.approx(0.0)
        assert records[0]["net_hours"] == pytest.approx(4.0)

    def test_lunch_deduction_six_to_eight_hours(self, tmp_path):
        """Shifts between 6h and <8h receive 0.5h lunch deduction."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Mid Worker", "Beta", datetime.time(9, 0), datetime.time(15, 0)]],
        )
        records = parse_roster(path, target_month="April 2026")
        assert len(records) == 1
        assert records[0]["lunch_deduction"] == pytest.approx(0.5)
        assert records[0]["net_hours"] == pytest.approx(5.5)

    def test_lunch_deduction_eight_or_more_hours(self, tmp_path):
        """Shifts of 8h+ receive 1.0h lunch deduction."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Full Worker", "Alpha", datetime.time(9, 0), datetime.time(17, 0)]],
        )
        records = parse_roster(path, target_month="April 2026")
        assert len(records) == 1
        assert records[0]["lunch_deduction"] == pytest.approx(1.0)
        assert records[0]["net_hours"] == pytest.approx(7.0)

    def test_both_clocks_missing_skips_row(self, tmp_path):
        """A row with no clock-in and no clock-out is silently skipped."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Ghost Worker", "Alpha", None, None]],
        )
        records = parse_roster(path, target_month="April 2026")
        assert records == []

    def test_one_clock_missing_strict_raises(self, tmp_path):
        """One clock value missing in strict mode (no malformed_out) raises."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Half Worker", "Alpha", datetime.time(9, 0), None]],
        )
        with pytest.raises(RosterParseError, match="[Mm]alformed|[Bb]lank|[Cc]lock"):
            parse_roster(path, target_month="April 2026")

    def test_one_clock_missing_collect_mode_warns(self, tmp_path):
        """One clock value missing in collect mode appends warning and skips row."""
        path = self._build_wb(
            tmp_path,
            sheet_name="Live - April 2026",
            headers=["Staff Name", "Project", "Apr 01 - Clock In", "Apr 01 - Clock Out"],
            rows=[["Half Worker", "Alpha", datetime.time(9, 0), None]],
        )
        malformed = []
        records = parse_roster(path, target_month="April 2026", malformed_out=malformed)
        assert records == []
        assert len(malformed) == 1
        assert "Half Worker" in malformed[0]
