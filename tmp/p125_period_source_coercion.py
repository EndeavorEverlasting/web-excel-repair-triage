from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("registry/prompts/management-operations-prompts.v1.json")
TESTS = Path("tests/test_hh_ticket_tracking_prompt.py")
MARKER = "PARAMETER RESOLUTION — PERIOD IS A SHARED SOURCE CONTRACT"


def strengthen_registry() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [prompt for prompt in data["prompts"] if prompt.get("id") == "P125"]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one P125, found {len(matches)}")
    prompt = matches[0]
    if prompt.get("name") != "Health + Hospitals Ticket Discovery & Tracking Harvester":
        raise SystemExit(f"unexpected P125 owner: {prompt.get('name')!r}")
    content = prompt["copyContent"]
    if MARKER in content:
        return

    window_anchor = "Prior ticket digest, if supplied: [paste/reference or `none`]"
    if window_anchor not in content:
        raise SystemExit("P125 SEARCH WINDOW anchor changed; refusing blind patch")
    parameter_rules = """

PARAMETER RESOLUTION — PERIOD IS A SHARED SOURCE CONTRACT
- Treat any operator-entered `Period` value as authoritative, including natural-language values such as `since last Monday`. Resolve relative wording to one concrete start/end boundary using the runtime date/time before searching.
- If `Period` is blank, omitted, or left at the bracketed template/default, resolve it automatically to `since last run`. Do not report the window as unspecified and do not ask the operator to fill unrelated blank parameters.
- The one RESOLVED PERIOD is mandatory for BOTH Outlook and Teams. Apply the exact same boundary to both pass-1 source searches and every pass-2 recovery search; there is no Outlook-only or Teams-only default.
- Blank or omitted `Prior ticket digest` and other optional parameters mean only `not supplied`; they must never disable, narrow, or silently skip either Outlook or Teams.
- For `since last run`, recover the previous P125/digest boundary from the current conversation or supplied prior digest when available. If no previous boundary is recoverable, state that bootstrap condition explicitly and use a labeled `last 7 days` bootstrap window rather than leaving the search window unknown.
- Echo the resolved concrete boundary before searching so source coverage is reproducible."""
    content = content.replace(window_anchor, window_anchor + parameter_rules, 1)

    pass1_anchor = "Search both Outlook and Teams inside the requested window."
    if pass1_anchor not in content:
        raise SystemExit("P125 pass-1 source anchor changed; refusing blind patch")
    content = content.replace(
        pass1_anchor,
        pass1_anchor
        + " Use the RESOLVED PERIOD above for both sources even when every other parameter is blank; a successful Outlook result never permits skipping Teams, and a Teams zero-result never changes the Outlook window.",
        1,
    )

    identity_anchor = "TICKET IDENTITY + DEDUPLICATION\n"
    if identity_anchor not in content:
        raise SystemExit("P125 identity anchor changed; refusing blind patch")
    identity_rules = """TICKET IDENTITY + DEDUPLICATION
- Classify the identifier type the source actually supports: INCIDENT / REQUEST / CASE / REFERENCE / UNKNOWN. An identifier such as `COB...` described only as a case/reference must remain a case/reference; do not relabel it as a ServiceNow incident/ticket without evidence.
- A coordination or escalation-policy discussion is not itself a ticket merely because it concerns support contacts. Unless the communication establishes a concrete operational request/work item, place it under IDENTITY OR EVIDENCE GAPS rather than OPEN / NEEDS FOLLOW-UP.
"""
    content = content.replace(identity_anchor, identity_rules, 1)

    normalized_anchor = "- Ticket / Incident ID — or PROVISIONAL / UNKNOWN\n"
    if normalized_anchor not in content:
        raise SystemExit("P125 normalized-record anchor changed; refusing blind patch")
    content = content.replace(
        normalized_anchor,
        normalized_anchor
        + "- Identifier type — INCIDENT / REQUEST / CASE / REFERENCE / UNKNOWN; preserve the source-supported type\n",
        1,
    )

    deliver_anchor = (
        "DELIVER\nGive me the daily ticket digest, the declared search window, pass-1 versus pass-2 additions/corrections, "
        "the count of unique ticket identities, and the unresolved evidence gaps. Optimize for quick operational follow-up, not billing reconstruction."
    )
    if deliver_anchor not in content:
        raise SystemExit("P125 DELIVER anchor changed; refusing blind patch")
    deliver = """DELIVER
Start with a compact SOURCE COVERAGE RECEIPT:
- Resolved Search Window — echo the concrete boundary actually applied.
- Outlook — EXECUTED + match count, FAILED, or UNAVAILABLE.
- Teams — EXECUTED + match count, FAILED, or UNAVAILABLE.
- Priority anchors — state whether all eight named people plus `Kaiyang He`, `Kai Yang`, and `Kelly` alias searches were attempted; list any not searched.
- Newest relevant timestamp found in Outlook and in Teams separately, or `none found`.
Treat `EXECUTED — 0 MATCHES` as different from FAILED/UNAVAILABLE. Do not claim `latest H+H correspondence` across both sources unless both source searches actually executed over the same RESOLVED PERIOD; otherwise state the narrower proof ceiling.

Then give me the daily ticket digest, the resolved search window, pass-1 versus pass-2 additions/corrections, the count of unique ticket identities, and the unresolved evidence gaps. Optimize for quick operational follow-up, not billing reconstruction. Do not append repository/PR/integration-state closeout sections unless repository work was explicitly requested in the same task."""
    content = content.replace(deliver_anchor, deliver, 1)

    prompt["copyContent"] = content
    prompt["inspectFirst"] = prompt["inspectFirst"].rstrip(".") + "; resolve Period first (operator value wins; blank/template defaults to since last run), and bind that one resolved window to both Outlook and Teams even when all other optional parameters are blank."
    prompt["expectedOutput"] = prompt["expectedOutput"].rstrip(".") + "; begin with a source-coverage receipt proving the resolved window, Outlook/Teams execution state and match counts, priority-anchor coverage, and newest relevant timestamp per source."
    prompt["nextStep"] = prompt["nextStep"].rstrip(".") + "; never return an unspecified window when Period was supplied or can default to since last run, and never let blank optional fields suppress one source."
    prompt["proofGate"] = prompt["proofGate"].rstrip(".") + "; the operator-supplied Period or since-last-run default is resolved once and applied identically to Outlook and Teams, zero matches are distinguished from failed/unavailable searches, coordination-only chatter is not promoted to a ticket, and case/reference identifiers retain their supported type."
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_tests() -> None:
    text = TESTS.read_text(encoding="utf-8")
    marker = "    def test_period_defaults_and_coerces_both_sources(self) -> None:"
    if marker in text:
        return
    block = r'''
    def test_period_defaults_and_coerces_both_sources(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PARAMETER RESOLUTION — PERIOD IS A SHARED SOURCE CONTRACT",
            "including natural-language values such as `since last Monday`",
            "resolve it automatically to `since last run`",
            "Do not report the window as unspecified",
            "mandatory for BOTH Outlook and Teams",
            "Apply the exact same boundary to both pass-1 source searches and every pass-2 recovery search",
            "must never disable, narrow, or silently skip either Outlook or Teams",
            "`last 7 days` bootstrap window",
        ):
            self.assertIn(phrase, content)

    def test_source_coverage_receipt_proves_latest_scope(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "SOURCE COVERAGE RECEIPT",
            "Resolved Search Window",
            "Outlook — EXECUTED + match count, FAILED, or UNAVAILABLE",
            "Teams — EXECUTED + match count, FAILED, or UNAVAILABLE",
            "Treat `EXECUTED — 0 MATCHES` as different from FAILED/UNAVAILABLE",
            "Do not claim `latest H+H correspondence` across both sources unless both source searches actually executed",
            "Newest relevant timestamp found in Outlook and in Teams separately",
        ):
            self.assertIn(phrase, content)

    def test_priority_anchor_receipt_includes_alias_sweep(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("all eight named people plus `Kaiyang He`, `Kai Yang`, and `Kelly` alias searches were attempted", content)
        self.assertIn("list any not searched", content)

    def test_coordination_only_chatter_is_not_promoted_to_ticket(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("A coordination or escalation-policy discussion is not itself a ticket", content)
        self.assertIn("place it under IDENTITY OR EVIDENCE GAPS rather than OPEN / NEEDS FOLLOW-UP", content)

    def test_case_reference_identity_does_not_imply_servicenow_incident(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("INCIDENT / REQUEST / CASE / REFERENCE / UNKNOWN", content)
        self.assertIn("described only as a case/reference must remain a case/reference", content)
        self.assertIn("do not relabel it as a ServiceNow incident/ticket without evidence", content)
        self.assertIn("Identifier type — INCIDENT / REQUEST / CASE / REFERENCE / UNKNOWN", content)

    def test_operational_digest_does_not_append_repo_closeout_noise(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("Do not append repository/PR/integration-state closeout sections unless repository work was explicitly requested", content)
'''
    footer = '\n\nif __name__ == "__main__":\n'
    if footer not in text:
        raise SystemExit("focused test file footer changed; refusing blind patch")
    TESTS.write_text(text.replace(footer, "\n" + block + footer, 1), encoding="utf-8")


if __name__ == "__main__":
    strengthen_registry()
    strengthen_tests()
    print("P125 period/source coercion carrier: applied or already present")
