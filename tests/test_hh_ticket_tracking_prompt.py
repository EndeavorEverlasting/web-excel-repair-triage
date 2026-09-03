from __future__ import annotations

import unittest

from scripts import build_prompt_kit_registry


TARGET_NAME = "Health + Hospitals Ticket Discovery & Tracking Harvester"


class HHTicketTrackingPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prompts = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.by_id = {prompt["id"]: prompt for prompt in cls.prompts}
        matches = [prompt for prompt in cls.prompts if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected exactly one {TARGET_NAME!r}, found {len(matches)}")
        cls.target = matches[0]

    def test_is_new_ticket_operations_owner_not_billing_harvester(self) -> None:
        prompt = self.target
        self.assertRegex(prompt["id"], r"^P\d+$")
        self.assertEqual(prompt["seq"], prompt["id"][1:])
        self.assertEqual(prompt["copySheet"], f"{prompt['id']}_COPY_SAFE")
        self.assertEqual(prompt["profile"], "triage-management")
        self.assertEqual(prompt["class"], "H+H SUPPORT / TICKET TRACKING")
        self.assertNotEqual(prompt["id"], "P88")
        self.assertNotEqual(prompt["id"], "P89")
        self.assertEqual(self.by_id["P88"]["name"], "Outlook Work-Evidence Harvester")
        self.assertEqual(self.by_id["P89"]["name"], "Teams Work-Evidence Harvester")
        self.assertEqual(self.by_id["P88"]["class"], "BILLING / EVIDENCE DISCOVERY")
        self.assertEqual(self.by_id["P89"]["class"], "BILLING / EVIDENCE DISCOVERY")

    def test_searches_outlook_and_teams_as_one_daily_ticket_workflow(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "SEARCH OUTLOOK AND MICROSOFT TEAMS TOGETHER FOR HEALTH + HOSPITALS TICKETS",
            "Period: [since last run / today / date range]",
            "Search both Outlook and Teams inside the requested window",
            "If an Outlook hit contains an incident number, search that incident in Teams",
            "if a Teams hit contains one, search it in Outlook",
            "Do not stop merely because one source already produced a useful hit",
        ):
            self.assertIn(phrase, content)

    def test_priority_people_are_exact_and_nonexclusive(self) -> None:
        content = self.target["copyContent"]
        for person in (
            "Brian McCarthy",
            "Dennis O'Connell",
            "Kurt Lavia",
            "Anthony James",
            "Vanessa Burks",
            "Richard Plaza",
            "Carol Ann Rosado",
            "Kaiyang He (Kelly)",
        ):
            self.assertIn(person, content)
        self.assertIn("Kai Yang / Kelly", content)
        self.assertIn("DO NOT TREAT THEM AS AN EXCLUSIVE WHITELIST", content)
        self.assertIn("A valid H+H ticket from another participant still belongs", content)

    def test_ticket_identity_deduplicates_cross_source_without_collapsing_distinct_incidents(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "Prefer an explicit ServiceNow/incident/ticket ID as the durable ticket identity",
            "Reconcile Outlook and Teams messages about the same explicit incident into one ticket record",
            "PROVISIONAL identity",
            "Never merge two records solely because they concern the same hospital, kiosk type, person, or day",
            "Preserve conflicting ticket/site/status evidence",
        ):
            self.assertIn(phrase, content)

    def test_status_model_separates_intake_assignment_completion_and_closure(self) -> None:
        content = self.target["copyContent"]
        for state in (
            "NEW / INTAKE",
            "COORDINATION",
            "ASSIGNED",
            "IN PROGRESS",
            "WAITING / BLOCKED",
            "COMPLETION REPORTED",
            "CLOSED / RESOLVED",
            "UNKNOWN",
        ):
            self.assertIn(state, content)
        for boundary in (
            "A request or relay is not assignment unless the message says who owns it",
            "Assignment is not proof work started",
            "`In progress` is not completion",
            "do not upgrade to CLOSED / RESOLVED unless the evidence actually establishes closure/resolution",
        ):
            self.assertIn(boundary, content)

    def test_does_not_smuggle_billing_or_unproven_field_completion_into_ticket_tracking(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("THIS IS NOT A BILLING HARVEST", content)
        self.assertIn(
            "Do not infer repair, replacement, delivery, attendance, hours, billing ownership, billing category, or technician completion",
            content,
        )
        self.assertIn("P88 Outlook Work-Evidence Harvester and P89 Teams Work-Evidence Harvester are billing/work-evidence discovery owners", content)
        self.assertIn("must not calculate hours, billing allocations, attendance", content)

    def test_digest_is_ticket_level_and_follow_up_oriented(self) -> None:
        content = self.target["copyContent"]
        for field in (
            "Ticket / Incident ID",
            "Facility / site",
            "Issue / request",
            "Current evidence state",
            "Requester / relay",
            "Current assignee / owner",
            "First seen + latest relevant update",
            "What changed since the prior digest",
            "Next follow-up",
            "Sources — Outlook / Teams / both",
            "Evidence note",
        ):
            self.assertIn(field, content)
        for section in (
            "NEW OR CHANGED TICKETS",
            "OPEN / NEEDS FOLLOW-UP",
            "COMPLETION REPORTED / CLOSED",
            "IDENTITY OR EVIDENCE GAPS",
        ):
            self.assertIn(section, content)

    def test_empty_result_fails_closed_instead_of_inventing_tickets(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("If no relevant tickets are found", content)
        self.assertIn("do not manufacture a ticket to make the digest nonempty", content)


if __name__ == "__main__":
    unittest.main()
