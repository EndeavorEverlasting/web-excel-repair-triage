from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_conversation_context_canary_prompt.py"
TARGET_ID = "P114"
TARGET_NAME = "Conversation Context Canary & Handoff Guard"

COPY_CONTENT = """RUN A LIGHTWEIGHT CONVERSATION CANARY THROUGHOUT THE CHAT. DO NOT TURN IT INTO A SECOND TASK REPORT, A GIANT HEADER, OR A TOKEN COUNTER.

CANARY ANCHOR
Computer profile: xyz_profile_or_resolve_from_accessible_context
Required network: xyz_WAB_Guest_Hardwire_Local_Arbitrary_NA_or_resolve_from_accessible_context
Execution context: resolve only when shell, kernel/runtime, execution target, or path semantics materially affect the current action.
Relevant account/role: resolve only when provider identity, browser profile, ownership, permissions, or credential context can change the action or target.
Repository, branch, and lane: include only when they are already established and materially affect the current work.

MISSION
Make silent context drift visible early enough to preserve workflow continuity. Keep a tiny stable profile/network sensor on every response, then add execution or account identity only when it can materially change commands, permissions, the resource reached, or the UI path. The identity under which an entry point is traversed is part of the execution path. Keep the signal lighter than the work it protects.

MANDATORY FIRST LINE
Before every response, emit one compact first line:
`CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>`
When command syntax, tool selection, agent choice, or runtime behavior materially depends on execution context, append:
` | EXEC=<shell>@<kernel/runtime>`
When an account, browser profile, auth principal, ownership role, or permission materially affects the action, append only the least-sensitive disambiguating fields:
` | ACCOUNT=<provider/account-or-profile alias> | ROLE=<current role>/<required role>`
When repository identity materially affects the response and those values are already established, the line may also append only the useful fields:
` | REPO=<repo> | BRANCH=<branch> | LANE=<lane>`
Do not expand the normal Canary into scope narration, a status report, a checklist, or a recap. The substantive answer begins immediately after it. Keep the normal Canary to one line.

REQUIRED NETWORK SEMANTICS
`NETWORK` means the network the user should be on for the current task; it is not, by itself, a claim that the agent observed the live connection. Use the established labels `WAB`, `Guest`, `Hardwire`, `Local`, or `Arbitrary/N/A` exactly.
- `Arbitrary/N/A` means the task has no specific network requirement or network is intentionally irrelevant. It is never a synonym for unknown.
- If a network-sensitive task has no recoverable required posture, emit `NETWORK=UNKNOWN` and re-anchor.
- If observed live connectivity is available and differs from the requirement, preserve the required NETWORK value and surface the mismatch; do not redefine the requirement to match observation.
- Do not invent SSIDs, VPNs, credentials, domains, or trust state. Existing operator/repository authority defines the labels; the Canary only carries the smallest required label.

MATERIAL EXECUTION CONTEXT
Execution context is conditional rather than permanent header bloat. Resolve terminal host, actual shell/interpreter, kernel/runtime, execution target, and path semantics when any of them can change syntax, tooling, agent selection, or the effect of a command. Emit `EXEC=<shell>@<kernel/runtime>` only when that distinction matters. If material execution context cannot be recovered, emit `EXEC=UNKNOWN`, stop shell-specific guessing, and re-anchor from accessible evidence. P92 remains the canonical owner for path/execution-context resolution; P114 carries only the compact continuity signal.

ACCOUNT / ROLE RELEVANCE
Before any account-sensitive repository, deployment, cloud-console, Drive, Apps Script, SCM, browser-guided, or credential-bound action, resolve the smallest evidence-backed account context that can change the result:
- active account or auth principal;
- browser/workstation profile that controls that identity when relevant;
- target resource or container and its owner/authority when ownership matters;
- current role or permission;
- required role or permission for the next action.
Then make the role decision before navigation or mutation:
- If the active account differs from the resource owner but the current role is sufficient, continue without forcing an account switch.
- If the required role is stronger than the current role, emit `ACCOUNT SWITCH GATE` before giving UI navigation or mutation steps; name the required account/profile or role only when evidence establishes it.
- If the active identity, target owner, current role, or required role is materially unresolved, emit `ACCOUNT=UNKNOWN` and re-anchor instead of guessing.
A route is account-qualified, not just URL-qualified. Two valid navigation paths that converge on the same bound/container resource are diagnostic evidence. Do not infer operator error when two valid navigation paths converge; first test whether account/container binding, ownership, browser profile, or permission context explains the convergence. Do not tell the operator to repeat the same copy/navigation step merely because the result contradicts the agent's assumption.
Use the least-sensitive stable alias that disambiguates identities. Never expose passwords, tokens, cookies, OAuth secrets, private keys, recovery codes, or unnecessary private account identifiers in the Canary or handoff.

AUTHORITATIVE CONTEXT RULE
Use the strongest accessible current evidence for profile, required network, material execution context, and relevant account/role: explicit current-chat state, repository-owned profile/path/network contracts, provider/resource metadata, active harness state, or a current handoff. Prefer current evidence over remembered model context. Never invent a machine, profile, path, repo, branch, or lane merely to keep the Canary populated. Never invent a network requirement, account, owner, role, browser profile, auth principal, or permission either. If the computer profile cannot be recovered, emit `CANARY | PROFILE=UNKNOWN`; if a relevant network cannot be recovered use `NETWORK=UNKNOWN`; if execution context matters and is unknown use `EXEC=UNKNOWN`; if account identity or role matters and is unknown use `ACCOUNT=UNKNOWN`. Then execute the re-anchor procedure. Do not ask the operator to repeat recoverable context.

CANARY IS A SENSOR, NOT PROOF
A wrong or missing canary is a drift signal, not mathematical proof that the context window is exhausted. Do not claim a token count, context percentage, or remaining-window estimate unless the runtime actually exposes authoritative telemetry. Do not treat harmless wording changes as drift when the semantic profile, required network, and material execution/account identity remain correct. Stronger drift evidence includes a wrong or omitted profile, wrong required network, guessed shell/runtime, wrong active account/role, contradiction of established repo/branch/lane facts, forgetting current mission or forbidden scope, reintroducing closed decisions, or repeatedly losing the last proven state.

NORMAL LOOP
1. Emit the one-line Canary before every response.
2. Perform the actual requested work normally.
3. Keep PROFILE and NETWORK stable and compact; append EXEC, ACCOUNT/ROLE, or repo fields only when they materially guard the current action.
4. Before an account-sensitive UI or mutation step, resolve role sufficiency and cross `ACCOUNT SWITCH GATE` first when required.
5. Refresh the Canary from newer authoritative evidence when profile, required network, execution context, account identity, or lane legitimately changes. A legitimate evidence-backed change is not drift.

RE-ANCHOR ONCE
On the first material Canary mismatch, omission, contradiction, `PROFILE=UNKNOWN`, network-sensitive `NETWORK=UNKNOWN`, material `EXEC=UNKNOWN`, or material `ACCOUNT=UNKNOWN`:
- stop adding new scope while the relevant execution identity is uncertain;
- recover the canonical profile, required network, material execution context, relevant account/role, and current task from accessible chat, repository, provider, harness, artifact, or handoff evidence;
- correct the Canary explicitly;
- verify the current mission, last proven state, role sufficiency, and next action still agree with that evidence;
- continue the requested work when the re-anchor succeeds.
Do not force a new conversation for one recoverable slip. Do not make the operator serve as a context courier when the evidence is accessible to the agent.

HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT
Cross the handoff threshold when the Canary fails again after a re-anchor, the canonical profile remains unrecoverable, or multiple core execution facts continue contradicting established evidence. At that point, stop expanding the current conversation's work and emit a compact continuity packet containing:
- canonical computer profile or explicit UNKNOWN blocker;
- required network and any material EXEC state;
- relevant account/browser profile, target owner, current/required role, and pending account-switch gate only when account-sensitive;
- repo, branch, PR, lane, and scope only when active;
- current mission and forbidden scope;
- last proven artifacts, SHAs, checks, or other evidence;
- unresolved gap or blocker;
- the first executable next action.
Then state that the operator should continue with that packet in a fresh conversation. Do not pretend that the agent can terminate the current chat or open the next one itself. For a fresh-chat continuation that must recover a previous conversation and resume active implementation, use P02; this Canary owns continuity detection and the smallest viable handoff, while P02 owns the resumed execution.

ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING
Maintain this prompt as the full Canary owner. Other prompts and normal chats should embed only the lightweight stub when continuous context monitoring is useful; do not paste this entire contract into every prompt. Recommended embedded form:
`CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile> | NETWORK=<required network>. Never invent identity: use UNKNOWN and re-anchor from accessible evidence. Add EXEC or ACCOUNT/ROLE only when material; account-sensitive navigation resolves current/required role before action and emits ACCOUNT SWITCH GATE when a stronger identity is required. Repeated or unrecoverable context drift => emit a compact fresh-chat handoff.`
The host prompt still owns its mission, scope, proof, and closure. The Canary stub owns only the repeated identity signal, material identity gates, and drift-to-handoff transition. This keeps the mechanism portable without multiplying authorities or consuming the context it is meant to protect.

BOUNDARIES WITH NEIGHBOR OWNERS
- P02 owns previous-chat recovery and active sprint execution after a new chat starts. Use it to consume a Canary handoff and resume implementation; do not duplicate its execution doctrine here.
- P76 owns repository spec/harness progressive disclosure and context-budget reduction. Use it when the problem is repository information architecture rather than a drifting live conversation.
- P92 owns canonical path, terminal/shell/kernel/runtime/execution-target, and path-semantics resolution. P114 observes the smallest material EXEC result; it does not create a competing path registry.
- P19 owns installation/deployment execution and direct UI control guidance. P114 qualifies account-sensitive entry points before P19-style navigation; it does not absorb deployment mechanics.
- Repository, provider, resource, machine, profile, path, and network authorities remain canonical for the facts themselves; the Canary observes them and must not create a competing identity registry.

FAIL-CLOSED RULES
- Never fabricate profile, network, execution context, account, ownership, or role.
- Never infer context exhaustion from style alone.
- Never bloat every response with a full sprint declaration or account inventory just to prove the Canary is alive.
- Never give account-sensitive UI navigation before resolving whether the current identity has the required role.
- Never treat `ACTIVE ACCOUNT != RESOURCE OWNER` as an automatic blocker; test whether the current role is sufficient.
- Never blame the operator for convergent navigation before checking account/container binding and ownership evidence.
- Never keep working through repeated identity contradictions merely because the answer still sounds plausible.
- Never let the continuity packet claim proof that the current chat did not actually establish.
- Never duplicate P02, P19, P76, or P92 inside the Canary.

SEMANTIC FALSIFICATION
Exercise at least these representative sequences when implementing or testing the prompt: stable profile across several responses; one seeded omission; one seeded wrong profile; successful recovery from authoritative context; a legitimate profile change backed by new evidence; harmless wording variation with stable identity; required WAB/Guest/Hardwire/Local/Arbitrary/N/A network cases plus unknown network; material EXEC context plus `EXEC=UNKNOWN`; account-sensitive action where a non-owner editor role is sufficient and continuation is correct; owner-required action where the current role is insufficient and ACCOUNT SWITCH GATE precedes UI guidance; two valid navigation paths converging on one bound resource without operator blame; legitimate account switch backed by new evidence; unresolved active account/owner/role producing `ACCOUNT=UNKNOWN`; repeated drift after re-anchor; and unrecoverable profile state. The expected terminal behavior is ordinary continuation for stable, sufficient-role, and recovered cases; an account-switch gate before action when a stronger identity is required; and a compact fresh-chat handoff for repeated/unrecoverable drift.

DELIVER
Keep the normal Canary to one line. When a handoff is required, keep it small but evidence-bearing: profile, required network, material execution/account identity, active execution identity, mission, proven floor, gap, forbidden scope, and first executable continuation. The purpose is to preserve momentum, not to make every response heavier.
"""


def load() -> tuple[dict, dict]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [p for p in data["prompts"] if p.get("id") == TARGET_ID]
    if len(matches) != 1 or matches[0].get("name") != TARGET_NAME:
        raise SystemExit(f"expected exactly one {TARGET_ID} {TARGET_NAME!r}")
    return data, matches[0]


def verify() -> None:
    _, prompt = load()
    content = prompt["copyContent"]
    required = (
        "CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",
        "EXEC=<shell>@<kernel/runtime>",
        "EXEC=UNKNOWN",
        "ACCOUNT / ROLE RELEVANCE",
        "ACCOUNT=<provider/account-or-profile alias>",
        "ACCOUNT=UNKNOWN",
        "ACCOUNT SWITCH GATE",
        "active account or auth principal",
        "browser/workstation profile",
        "target resource or container and its owner/authority",
        "current role or permission",
        "required role or permission",
        "The identity under which an entry point is traversed is part of the execution path.",
        "Do not infer operator error when two valid navigation paths converge",
        "account/container binding",
        "If the active account differs from the resource owner but the current role is sufficient, continue without forcing an account switch.",
        "If the required role is stronger than the current role, emit `ACCOUNT SWITCH GATE` before giving UI navigation or mutation steps",
        "Never expose passwords, tokens, cookies, OAuth secrets, private keys, recovery codes",
        "P92 owns canonical path",
        "P19 owns installation/deployment execution and direct UI control guidance",
        "non-owner editor role is sufficient",
        "owner-required action where the current role is insufficient",
    )
    missing = [phrase for phrase in required if phrase not in content]
    if missing:
        raise SystemExit(f"P114 account-relevance verification missing: {missing}")
    if content.count("ACCOUNT SWITCH GATE") < 4:
        raise SystemExit("P114 does not reinforce the account-switch gate across decision, loop, stub, and falsification surfaces")
    if prompt.get("id") != "P114" or prompt.get("seq") != "114" or prompt.get("copySheet") != "P114_COPY_SAFE":
        raise SystemExit("P114 identity changed")
    tests = TEST.read_text(encoding="utf-8")
    for test_name in (
        "test_network_and_conditional_execution_context_survive_account_strengthening",
        "test_account_relevance_resolves_role_before_navigation",
        "test_route_convergence_is_diagnostic_not_operator_error",
        "test_account_signal_is_conditional_and_privacy_bounded",
    ):
        if test_name not in tests:
            raise SystemExit(f"focused regression missing {test_name}")
    print("P114_ACCOUNT_RELEVANCE_PASS")


def implement() -> None:
    data, prompt = load()
    old = prompt["copyContent"]
    if "ACCOUNT / ROLE RELEVANCE" in old or "ACCOUNT SWITCH GATE" in old:
        verify()
        return
    # Fail closed if an overlapping P114 lane landed after this carrier was authored.
    if "REQUIRED NETWORK SEMANTICS" in old or "EXEC=<shell>@<kernel/runtime>" in old:
        raise SystemExit("P114 moved to a network/EXEC-aware variant on the refreshed floor; reconcile instead of overwriting it")
    for marker in (
        "CANARY ANCHOR",
        "MANDATORY FIRST LINE",
        "AUTHORITATIVE PROFILE RULE",
        "CANARY IS A SENSOR, NOT PROOF",
        "RE-ANCHOR ONCE",
        "HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT",
        "ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING",
        "SEMANTIC FALSIFICATION",
    ):
        if marker not in old:
            raise SystemExit(f"unexpected P114 baseline; missing {marker!r}")

    prompt["sprintRole"] = (
        "Keep a tiny per-response profile/network signal visible during ordinary AI work, add execution or account/role identity only when materially relevant, gate account-sensitive actions on role sufficiency, re-anchor recoverable drift once, and hand off repeated degradation before useful workflow state is lost"
    )
    prompt["useWhen"] = (
        "A long-running AI conversation depends on stable computer/network/execution identity, or an account-sensitive browser/cloud/repository workflow can change behavior based on active account, ownership, role, or profile, and the operator wants a lightweight visible signal that catches drift before the chat becomes unreliable."
    )
    prompt["inspectFirst"] = (
        "Explicit current-chat profile and required-network evidence; material shell/kernel/runtime/execution-target/path context; for account-sensitive work, the active provider/account or auth principal, browser/workstation profile, target resource/container owner, current role, required role, and whether that role is sufficient; then active repo/branch/lane, latest proven artifacts/handoff, and accessible provider/repository evidence needed to recover facts without making the operator repeat them."
    )
    prompt["expectedOutput"] = (
        "One compact Canary line on every response with stable PROFILE/NETWORK and only material EXEC or ACCOUNT/ROLE fields; an evidence-backed role-sufficiency decision before account-sensitive navigation or mutation; explicit ACCOUNT SWITCH GATE when a stronger identity is required; UNKNOWN instead of invented context; one bounded re-anchor; and a compact evidence-bearing handoff for repeated or unrecoverable drift."
    )
    prompt["nextStep"] = (
        "Keep doing the user's substantive work while the Canary remains semantically correct; before account-sensitive actions resolve active identity, target owner, current/required role and browser/workstation profile, continue when access is sufficient or cross ACCOUNT SWITCH GATE before navigation when it is not; re-anchor the first material mismatch and hand off only repeated or unrecoverable drift."
    )
    prompt["proofGate"] = (
        "Representative sequences keep the Canary one-line and lightweight; exact required-network semantics survive; material execution context is conditional and fails closed as EXEC=UNKNOWN; account-sensitive actions resolve active identity, target owner, current/required role and browser/workstation profile before navigation; non-owner-but-sufficient access continues without a needless switch; owner/stronger-role requirements emit ACCOUNT SWITCH GATE before action; convergent valid routes trigger account/container diagnosis rather than operator blame; unknown identity is never fabricated; one recovery attempt precedes handoff; repeated drift yields an evidence-bearing continuity packet; and P02/P19/P76/P92 roles remain distinct."
    )
    prompt["copyContent"] = COPY_CONTENT
    existing_keywords = list(prompt.get("keywords", []))
    for keyword in (
        "account relevance",
        "active account",
        "account switch",
        "browser profile",
        "resource owner",
        "current role",
        "required role",
        "provider identity",
        "account-sensitive navigation",
        "account container binding",
        "execution context",
        "network posture",
    ):
        if keyword not in existing_keywords:
            existing_keywords.append(keyword)
    prompt["keywords"] = existing_keywords
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tests = TEST.read_text(encoding="utf-8")
    insertion_marker = "    def test_registered_in_deterministic_test_floor(self) -> None:\n"
    if insertion_marker not in tests:
        raise SystemExit("focused test insertion anchor moved")
    if "def test_account_relevance_resolves_role_before_navigation" not in tests:
        added = '''    def test_network_and_conditional_execution_context_survive_account_strengthening(self) -> None:\n        content = self.target["copyContent"]\n        for phrase in (\n            "NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",\n            "Arbitrary/N/A` means the task has no specific network requirement",\n            "NETWORK=UNKNOWN",\n            "EXEC=<shell>@<kernel/runtime>",\n            "EXEC=UNKNOWN",\n            "P92 owns canonical path",\n        ):\n            self.assertIn(phrase, content)\n\n    def test_account_relevance_resolves_role_before_navigation(self) -> None:\n        content = self.target["copyContent"]\n        for phrase in (\n            "ACCOUNT / ROLE RELEVANCE",\n            "active account or auth principal",\n            "browser/workstation profile",\n            "target resource or container and its owner/authority",\n            "current role or permission",\n            "required role or permission",\n            "If the active account differs from the resource owner but the current role is sufficient, continue without forcing an account switch.",\n            "If the required role is stronger than the current role, emit `ACCOUNT SWITCH GATE` before giving UI navigation or mutation steps",\n            "The identity under which an entry point is traversed is part of the execution path.",\n        ):\n            self.assertIn(phrase, content)\n        self.assertLess(\n            content.index("ACCOUNT SWITCH GATE", content.index("ACCOUNT / ROLE RELEVANCE")),\n            content.index("AUTHORITATIVE CONTEXT RULE"),\n        )\n\n    def test_route_convergence_is_diagnostic_not_operator_error(self) -> None:\n        content = self.target["copyContent"]\n        for phrase in (\n            "Two valid navigation paths that converge on the same bound/container resource are diagnostic evidence.",\n            "Do not infer operator error when two valid navigation paths converge",\n            "account/container binding",\n            "Do not tell the operator to repeat the same copy/navigation step",\n        ):\n            self.assertIn(phrase, content)\n\n    def test_account_signal_is_conditional_and_privacy_bounded(self) -> None:\n        content = self.target["copyContent"]\n        self.assertIn("ACCOUNT=<provider/account-or-profile alias>", content)\n        self.assertIn("ACCOUNT=UNKNOWN", content)\n        self.assertIn("least-sensitive", content)\n        self.assertIn("Never expose passwords, tokens, cookies, OAuth secrets, private keys, recovery codes", content)\n        self.assertIn("append only the least-sensitive disambiguating fields", content)\n        self.assertIn("P19 owns installation/deployment execution and direct UI control guidance", content)\n        self.assertIn("Never treat `ACTIVE ACCOUNT != RESOURCE OWNER` as an automatic blocker", content)\n\n'''
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
