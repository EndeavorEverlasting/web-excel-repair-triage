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
