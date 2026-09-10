from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_conversation_context_canary_prompt.py"
TARGET_ID = "P114"
TARGET_NAME = "Conversation Context Canary & Handoff Guard"


def load() -> tuple[dict, dict]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [p for p in data["prompts"] if p.get("id") == TARGET_ID]
    if len(matches) != 1 or matches[0].get("name") != TARGET_NAME:
        raise SystemExit(f"expected exactly one {TARGET_ID} {TARGET_NAME!r}")
    return data, matches[0]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    return text.replace(old, new, 1)


def verify() -> None:
    _, prompt = load()
    content = prompt["copyContent"]
    required = (
        "Query issued at: xyz_offset_aware_RFC3339_turn_start_or_resolve_from_accessible_runtime",
        "CANARY | ISSUED=<query-issued offset-aware RFC3339> | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",
        "QUERY ISSUANCE TIME / TEMPORAL FRESHNESS",
        "capture it once at user-query receipt or the earliest trustworthy turn-start observation",
        "Freeze that ISSUED value for every progress update and the final answer produced for the same user query",
        "Preserve `Z` or a numeric UTC offset",
        "ISSUED=UNKNOWN",
        "The previous Canary's ISSUED value is temporal provenance",
        "A large elapsed gap is a freshness signal, not proof of context exhaustion",
        "Do not invent a universal stale-minutes threshold",
        "refresh only the affected evidence before carrying its prior proof forward",
        "Evaluators can use the ISSUED sequence",
        "same ISSUED value across multiple outputs for one query",
        "a later query with a later offset-aware ISSUED value",
        "a large query gap that forces refresh of time-sensitive provider/repository evidence",
        "a large gap on a timeless task that does not falsely trigger handoff",
    )
    missing = [phrase for phrase in required if phrase not in content]
    if missing:
        raise SystemExit(f"P114 temporal verification missing: {missing}")
    if prompt.get("id") != "P114" or prompt.get("seq") != "114" or prompt.get("copySheet") != "P114_COPY_SAFE":
        raise SystemExit("P114 identity changed")
    for preserved in (
        "ACCOUNT / ROLE RELEVANCE",
        "ACCOUNT SWITCH GATE",
        "EXEC=<shell>@<kernel/runtime>",
        "NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",
        "P92 owns canonical path",
        "P19 owns installation/deployment execution and direct UI control guidance",
        "CANARY IS A SENSOR, NOT PROOF",
        "HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT",
    ):
        if preserved not in content:
            raise SystemExit(f"P114 preserved behavior missing: {preserved}")
    tests = TEST.read_text(encoding="utf-8")
    for test_name in (
        "test_query_issuance_timestamp_is_offset_aware_and_frozen_per_turn",
        "test_temporal_gap_triggers_freshness_review_not_fake_context_exhaustion",
        "test_account_relevance_resolves_role_before_navigation",
        "test_network_and_conditional_execution_context_survive_account_strengthening",
    ):
        if test_name not in tests:
            raise SystemExit(f"focused regression missing {test_name}")
    print("P114_QUERY_ISSUED_TIMESTAMP_PASS")


def implement() -> None:
    data, prompt = load()
    old = prompt["copyContent"]
    if "QUERY ISSUANCE TIME / TEMPORAL FRESHNESS" in old:
        verify()
        return

    # The account/network/EXEC strengthening on current main is the required floor.
    for marker in (
        "ACCOUNT / ROLE RELEVANCE",
        "ACCOUNT SWITCH GATE",
        "REQUIRED NETWORK SEMANTICS",
        "EXEC=<shell>@<kernel/runtime>",
        "CANARY IS A SENSOR, NOT PROOF",
        "ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING",
        "SEMANTIC FALSIFICATION",
    ):
        if marker not in old:
            raise SystemExit(f"unexpected P114 floor; missing {marker!r}; reconcile instead of overwriting")

    prompt["sprintRole"] = (
        "Keep a tiny per-query issued-at plus per-response profile/network signal visible during ordinary AI work, add execution or account/role identity only when materially relevant, use elapsed query time to challenge stale evidence without inventing a universal timeout, re-anchor recoverable drift once, and hand off repeated degradation before useful workflow state is lost"
    )
    prompt["useWhen"] = (
        "A long-running AI conversation depends on stable computer/network/execution identity or fresh provider/repository evidence, an account-sensitive workflow can change behavior by identity or role, and the operator wants a lightweight visible signal that makes transcript chronology, stale-iteration risk, and context drift legible before the chat becomes unreliable."
    )
    prompt["inspectFirst"] = (
        "The current user-query ingress timestamp or earliest trustworthy turn-start clock with timezone/offset; the prior Canary ISSUED value and any evidence TTL/freshness contract that governs reuse; explicit current-chat profile and required-network evidence; material shell/kernel/runtime/execution-target/path context; for account-sensitive work, active provider/account or auth principal, browser/workstation profile, target resource/container owner, current role, required role, and role sufficiency; then active repo/branch/lane, latest proven artifacts/handoff, and accessible provider/repository evidence needed to recover facts without making the operator repeat them."
    )
    prompt["expectedOutput"] = (
        "One compact Canary line on every response with a query-issued offset-aware ISSUED timestamp plus stable PROFILE/NETWORK and only material EXEC or ACCOUNT/ROLE fields; the same ISSUED value is frozen across all outputs for one user query; elapsed query gaps trigger bounded freshness review of affected evidence rather than fake context-exhaustion claims; UNKNOWN replaces invented time or identity; and repeated unrecoverable drift still yields a compact evidence-bearing handoff."
    )
    prompt["nextStep"] = (
        "Capture ISSUED once at query receipt/turn start, keep doing the user's substantive work while the Canary remains semantically correct, compare the prior/current ISSUED values before reusing time-sensitive proof and refresh only evidence whose freshness may no longer hold; continue account-role gating as before, re-anchor the first material mismatch, and hand off only repeated or unrecoverable drift."
    )
    prompt["proofGate"] = (
        "Representative sequences keep the Canary one-line and lightweight; ISSUED is offset-aware, captured once per user query, frozen across that query's progress/final outputs, and advances on later queries; unavailable time fails closed as ISSUED=UNKNOWN; a material elapsed gap causes affected time-sensitive evidence to be refreshed when its owner requires freshness but does not invent a universal stale threshold or falsely prove context exhaustion; evaluator-readable timestamp sequences expose stale-proof reuse; exact network, EXEC, account/role, re-anchor, handoff, and P02/P19/P76/P92 boundaries remain intact."
    )

    content = old
    content = replace_once(
        content,
        "Computer profile: xyz_profile_or_resolve_from_accessible_context\nRequired network:",
        "Computer profile: xyz_profile_or_resolve_from_accessible_context\nQuery issued at: xyz_offset_aware_RFC3339_turn_start_or_resolve_from_accessible_runtime\nRequired network:",
        "canary anchor timestamp",
    )
    content = replace_once(
        content,
        "Make silent context drift visible early enough to preserve workflow continuity. Keep a tiny stable profile/network sensor on every response, then add execution or account identity only when it can materially change commands, permissions, the resource reached, or the UI path.",
        "Make silent context drift and temporal discontinuity visible early enough to preserve workflow continuity. Keep a tiny query-issued timestamp plus stable profile/network sensor on every response, then add execution or account identity only when it can materially change commands, permissions, the resource reached, or the UI path.",
        "mission temporal sensor",
    )
    content = replace_once(
        content,
        "`CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>`",
        "`CANARY | ISSUED=<query-issued offset-aware RFC3339> | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>`",
        "mandatory first line",
    )

    temporal_section = """QUERY ISSUANCE TIME / TEMPORAL FRESHNESS
`ISSUED` is the timestamp for the user query that caused the current assistant iteration. Prefer authoritative message-ingress metadata when the runtime exposes it; otherwise capture it once at user-query receipt or the earliest trustworthy turn-start observation before substantive work. Freeze that ISSUED value for every progress update and the final answer produced for the same user query; do not recompute it from later tool-return, validation, or completion time. Use RFC3339 and Preserve `Z` or a numeric UTC offset so ordering and elapsed-time comparisons remain unambiguous. If neither message metadata nor a trustworthy turn-start clock is available, emit `ISSUED=UNKNOWN`; do not fabricate a clock value.

The previous Canary's ISSUED value is temporal provenance. Compare it with the current query's ISSUED value before carrying forward time-sensitive provider, repository, deployment, market, schedule, credential/session, or other freshness-bounded evidence. A large elapsed gap is a freshness signal, not proof of context exhaustion. If an authoritative TTL, SLA, lease, token expiry, provider-freshness rule, or evidence-age contract exists, obey that owner. Otherwise Do not invent a universal stale-minutes threshold. When elapsed time could invalidate the last proof floor or a current-state claim, refresh only the affected evidence before carrying its prior proof forward and bind the new proof to the refreshed observation. A long gap on a timeless task is not itself a handoff condition. Evaluators can use the ISSUED sequence to reconstruct iteration timing, detect stale-proof reuse, distinguish same-query progress from later queries, and score recovery behavior.

"""
    content = replace_once(
        content,
        "REQUIRED NETWORK SEMANTICS\n",
        temporal_section + "REQUIRED NETWORK SEMANTICS\n",
        "temporal section insertion",
    )
    content = replace_once(
        content,
        "A wrong or missing canary is a drift signal, not mathematical proof that the context window is exhausted.",
        "A wrong or missing canary is a drift signal, not mathematical proof that the context window is exhausted. Likewise, elapsed ISSUED time is temporal evidence that can make a prior iteration stale for a freshness-bounded task, but elapsed time alone does not prove context exhaustion or semantic drift.",
        "sensor not proof temporal clause",
    )
    old_loop = """NORMAL LOOP
1. Emit the one-line Canary before every response.
2. Perform the actual requested work normally.
3. Keep PROFILE and NETWORK stable and compact; append EXEC, ACCOUNT/ROLE, or repo fields only when they materially guard the current action.
4. Before an account-sensitive UI or mutation step, resolve role sufficiency and cross `ACCOUNT SWITCH GATE` first when required.
5. Refresh the Canary from newer authoritative evidence when profile, required network, execution context, account identity, or lane legitimately changes. A legitimate evidence-backed change is not drift.
"""
    new_loop = """NORMAL LOOP
1. Capture ISSUED once for the incoming user query before substantive work and freeze it for every assistant output belonging to that query.
2. Emit the one-line Canary before every response.
3. Before reusing freshness-bounded evidence, compare prior/current ISSUED values and refresh only the affected evidence when its owning contract or material elapsed time makes prior proof stale or uncertain.
4. Perform the actual requested work normally.
5. Keep PROFILE and NETWORK stable and compact; append EXEC, ACCOUNT/ROLE, or repo fields only when they materially guard the current action.
6. Before an account-sensitive UI or mutation step, resolve role sufficiency and cross `ACCOUNT SWITCH GATE` first when required.
7. Refresh the Canary from newer authoritative evidence when profile, required network, execution context, account identity, or lane legitimately changes. A legitimate evidence-backed change is not drift.
"""
    content = replace_once(content, old_loop, new_loop, "normal loop")
    content = replace_once(
        content,
        "- canonical computer profile or explicit UNKNOWN blocker;\n- required network and any material EXEC state;",
        "- canonical computer profile or explicit UNKNOWN blocker;\n- last reliable query ISSUED timestamp or explicit temporal UNKNOWN when freshness matters;\n- required network and any material EXEC state;",
        "handoff temporal provenance",
    )
    old_stub = "`CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile> | NETWORK=<required network>. Never invent identity: use UNKNOWN and re-anchor from accessible evidence. Add EXEC or ACCOUNT/ROLE only when material; account-sensitive navigation resolves current/required role before action and emits ACCOUNT SWITCH GATE when a stronger identity is required. Repeated or unrecoverable context drift => emit a compact fresh-chat handoff.`"
    new_stub = "`CANARY STUB — Capture one offset-aware query-issued timestamp at turn start and freeze it across that query's outputs. Before every response emit CANARY | ISSUED=<query-issued offset-aware RFC3339> | PROFILE=<canonical computer profile> | NETWORK=<required network>. Never invent time or identity: use UNKNOWN and recover from accessible evidence. Compare prior/current ISSUED before reusing freshness-bounded proof; refresh affected stale evidence without inventing a universal timeout. Add EXEC or ACCOUNT/ROLE only when material; account-sensitive navigation resolves current/required role before action and emits ACCOUNT SWITCH GATE when a stronger identity is required. Repeated or unrecoverable context drift => emit a compact fresh-chat handoff.`"
    content = replace_once(content, old_stub, new_stub, "lightweight stub")
    content = replace_once(
        content,
        "- Repository, provider, resource, machine, profile, path, and network authorities remain canonical for the facts themselves; the Canary observes them and must not create a competing identity registry.",
        "- Evidence/provider owners remain authoritative for TTLs, leases, session expiry, and freshness requirements. P114 carries query-issued temporal provenance and triggers bounded refresh; it does not invent a competing stale-time policy.\n- Repository, provider, resource, machine, profile, path, and network authorities remain canonical for the facts themselves; the Canary observes them and must not create a competing identity registry.",
        "temporal owner boundary",
    )
    content = replace_once(
        content,
        "FAIL-CLOSED RULES\n- Never fabricate profile, network, execution context, account, ownership, or role.",
        "FAIL-CLOSED RULES\n- Never fabricate ISSUED, profile, network, execution context, account, ownership, or role.\n- Never infer a universal stale threshold from elapsed time alone; apply an owning freshness contract or refresh only when elapsed time is materially relevant to the evidence being reused.",
        "fail closed temporal rules",
    )
    content = replace_once(
        content,
        "unresolved active account/owner/role producing `ACCOUNT=UNKNOWN`; repeated drift after re-anchor; and unrecoverable profile state.",
        "unresolved active account/owner/role producing `ACCOUNT=UNKNOWN`; same ISSUED value across multiple outputs for one query; a later query with a later offset-aware ISSUED value; `ISSUED=UNKNOWN` when no trustworthy clock is available; a large query gap that forces refresh of time-sensitive provider/repository evidence; a large gap on a timeless task that does not falsely trigger handoff; repeated drift after re-anchor; and unrecoverable profile state.",
        "semantic falsification temporal cases",
    )
    content = replace_once(
        content,
        "Keep the normal Canary to one line. When a handoff is required, keep it small but evidence-bearing: profile, required network, material execution/account identity, active execution identity, mission, proven floor, gap, forbidden scope, and first executable continuation.",
        "Keep the normal Canary to one line. When a handoff is required, keep it small but evidence-bearing: last reliable query ISSUED time, profile, required network, material execution/account identity, active execution identity, mission, proven floor, gap, forbidden scope, and first executable continuation.",
        "deliver temporal provenance",
    )
    prompt["copyContent"] = content

    existing_keywords = list(prompt.get("keywords", []))
    for keyword in (
        "query timestamp",
        "query issued",
        "issued at",
        "RFC3339",
        "temporal provenance",
        "freshness gap",
        "stale iteration",
        "evidence freshness",
        "transcript chronology",
        "evaluation timing",
    ):
        if keyword not in existing_keywords:
            existing_keywords.append(keyword)
    prompt["keywords"] = existing_keywords
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tests = TEST.read_text(encoding="utf-8")
    tests = replace_once(
        tests,
        '            "CANARY | PROFILE=<canonical computer profile>",\n',
        '            "CANARY | ISSUED=<query-issued offset-aware RFC3339> | PROFILE=<canonical computer profile>",\n',
        "existing mandatory-line assertion",
    )
    tests = replace_once(
        tests,
        '            "CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile>",\n',
        '            "CANARY STUB — Capture one offset-aware query-issued timestamp at turn start",\n',
        "existing stub assertion",
    )
    insertion_marker = "    def test_network_and_conditional_execution_context_survive_account_strengthening(self) -> None:\n"
    if insertion_marker not in tests:
        raise SystemExit("focused test insertion anchor moved")
    added = '''    def test_query_issuance_timestamp_is_offset_aware_and_frozen_per_turn(self) -> None:\n        content = self.target["copyContent"]\n        for phrase in (\n            "QUERY ISSUANCE TIME / TEMPORAL FRESHNESS",\n            "Query issued at: xyz_offset_aware_RFC3339_turn_start_or_resolve_from_accessible_runtime",\n            "CANARY | ISSUED=<query-issued offset-aware RFC3339>",\n            "capture it once at user-query receipt or the earliest trustworthy turn-start observation",\n            "Freeze that ISSUED value for every progress update and the final answer produced for the same user query",\n            "Preserve `Z` or a numeric UTC offset",\n            "ISSUED=UNKNOWN",\n        ):\n            self.assertIn(phrase, content)\n\n    def test_temporal_gap_triggers_freshness_review_not_fake_context_exhaustion(self) -> None:\n        content = self.target["copyContent"]\n        for phrase in (\n            "The previous Canary's ISSUED value is temporal provenance",\n            "A large elapsed gap is a freshness signal, not proof of context exhaustion",\n            "Do not invent a universal stale-minutes threshold",\n            "refresh only the affected evidence before carrying its prior proof forward",\n            "A long gap on a timeless task is not itself a handoff condition",\n            "Evaluators can use the ISSUED sequence",\n            "a large query gap that forces refresh of time-sensitive provider/repository evidence",\n            "a large gap on a timeless task that does not falsely trigger handoff",\n        ):\n            self.assertIn(phrase, content)\n\n'''
    if "def test_query_issuance_timestamp_is_offset_aware_and_frozen_per_turn" not in tests:
        tests = tests.replace(insertion_marker, added + insertion_marker, 1)
    TEST.write_text(tests, encoding="utf-8")
    verify()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify()
    else:
        implement()


if __name__ == "__main__":
    main()
