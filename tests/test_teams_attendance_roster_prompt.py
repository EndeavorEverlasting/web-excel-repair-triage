from __future__ import annotations

import unittest
from scripts import build_prompt_kit_registry

TARGET = "Teams Attendance Roster Reconstructor"


class TeamsAttendanceRosterPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.by_name = {item["name"]: item for item in cls.prompts}
        matches = [item for item in cls.prompts if item.get("name") == TARGET]
        if len(matches) != 1:
            raise AssertionError(f"expected one {TARGET!r}, found {len(matches)}")
        cls.target = matches[0]

    def test_is_distinct_from_p89_billing_harvester(self) -> None:
        self.assertIn("Teams Work-Evidence Harvester", self.by_name)
        p89 = self.by_name["Teams Work-Evidence Harvester"]
        self.assertEqual(p89["id"], "P89")
        self.assertNotEqual(self.target["id"], "P89")
        self.assertEqual(p89["class"], "BILLING / EVIDENCE DISCOVERY")
        self.assertEqual(self.target["class"], "MANAGEMENT / ATTENDANCE EVIDENCE")
        self.assertIn("P89 `Teams Work-Evidence Harvester` owns", self.target["copyContent"])
        self.assertIn("must not assign billing categories", self.target["copyContent"])

    def test_named_sources_are_primary_and_coverage_is_fail_closed(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "Named Teams chats or channels",
            "Resolve every named chat/channel to a unique source",
            "Start with the explicitly named chats",
            "EXECUTED-PARTIAL",
            "FAILED",
            "UNAVAILABLE",
            "Zero matches is not the same as failed access",
        ):
            self.assertIn(phrase, content)

    def test_notches_drive_recovery_not_absence(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "A NOTCH is an expected evidence checkpoint, not an attendance fact",
            "explicit manager/team rule",
            "repeated observed check-in pattern",
            "Do not invent a universal morning/noon/end-of-day cadence",
            "A missing notch means MISSING EVIDENCE / FOLLOW-UP",
            "it does not mean absent, zero hours, late, or noncompliant",
        ):
            self.assertIn(phrase, content)

    def test_presence_event_is_not_full_shift_or_paid_hours(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "A single check-in supports presence at that observed moment",
            "It does not automatically establish an eight-hour day",
            "do not convert first/last message timestamps into worked hours",
            "DO NOT TURN CHAT ACTIVITY INTO PAID HOURS, BILLING, OR DISCIPLINARY CONCLUSIONS",
        ):
            self.assertIn(phrase, content)

    def test_person_date_states_preserve_expected_only_conflict_and_unknown(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PRESENT — DIRECT CHECK-IN",
            "PRESENT — CORROBORATED",
            "EXPLICIT NOT WORKING",
            "EXPECTED ONLY",
            "CONFLICT",
            "UNKNOWN",
        ):
            self.assertIn(phrase, content)

    def test_multi_chat_corrections_and_source_provenance_survive(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "MULTI-CHAT RECONCILIATION",
            "retaining every source reference",
            "Normalize aliases without merging distinct people",
            "moves sites or tasks during a day",
            "Never choose whichever source makes the roster look most complete",
        ):
            self.assertIn(phrase, content)

    def test_other_attendance_mechanisms_are_bounded_and_separate(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("Other known attendance mechanism", content)
        self.assertIn("follow it only when it is accessible and relevant to a specific gap", content)
        self.assertIn("Preserve that mechanism as a separate source", content)
        self.assertIn("do not pretend Teams supplied evidence that came from somewhere else", content)

    def test_two_pass_roster_closes_each_person_date_or_gap(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("PASS 1 — CHRONOLOGICAL CHECK-IN CENSUS", content)
        self.assertIn("PASS 2 — NOTCH RECOVERY + CONFLICT SEARCH", content)
        self.assertIn("This pass is required even when pass 1 produced a plausible roster", content)
        self.assertIn("every in-scope person/date is represented by an evidence-supported state or an explicit gap", content)

    def test_generated_site_is_exact_and_prompt_is_discoverable(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn(self.target["id"], html)
        self.assertIn(TARGET, html)
        searchable = " ".join([self.target["name"], *self.target["keywords"]]).casefold()
        for term in ("teams attendance", "attendance roster", "check-in cadence", "named teams chats"):
            self.assertIn(term, searchable)


if __name__ == "__main__":
    unittest.main()
