from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"

REQUIRED_PHRASES = (
    "PROVIDER-SIDE MERGE EXECUTOR — NO HUMAN MEMORY STEP",
    "explicit repository-owned required-check names",
    "unresolved review threads",
    "immediately re-read provider truth",
    "expected head SHA",
    "A local branch switch or local checkout is not part of normal merge convergence",
    "duplicate wakeups are idempotent",
)


def strengthen_p105() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [p for p in data["prompts"] if p.get("id") == "P105"]
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one P105 owner, found {len(matches)}")
    p = matches[0]

    p["sprintRole"] = (
        "Design and implement a repository-owned GitHub Actions/CI/CD promotion mechanism whose provider-side "
        "merge executor notices when an exact candidate satisfies explicit repository-owned gates and performs the "
        "authorized merge/push/release/deploy itself without relying on a human or agent to remember the last-mile action"
    )
    p["useWhen"] = (
        "A repository should automatically validate code authored by humans, agents, or repo-native generators and then "
        "safely push, merge, release, or deploy that exact code through GitHub Actions/CI/CD, including the last-mile "
        "provider-side merge, rather than relying on manual promotion commands, local branch switching, or operator memory."
    )
    p["inspectFirst"] = (
        "Fresh default-branch/PR/workflow truth; current GitHub Actions and CI/CD files; tracked required-check/promotion "
        "policy; branch protection, merge queue, review requirements and unresolved review threads; GitHub App/workflow "
        "identity and token permissions; canonical test/build/harness commands including P11-style harness validation; "
        "application E2E suites; artifact/package provenance; deployment/release paths; existing bot writers, concurrency "
        "groups, webhook/event coverage, retries, and prior pipeline failures."
    )
    p["expectedOutput"] = (
        "A tracked promotion architecture and implemented provider-side executor that delegates to repo-owned validation "
        "commands, pins proof to one exact candidate SHA, requires explicit repository-owned check names and resolved "
        "review gates, re-reads GitHub immediately before mutation, preserves artifact provenance, fails closed on "
        "stale/moved/skipped/failed/missing proof, serializes and idempotently owns write authority, uses least privilege "
        "and loop guards, performs only repository-authorized provider-side merge/push/release/deploy actions, and emits "
        "provider-runtime evidence without requiring a local branch switch or remembered human/agent merge command."
    )
    p["nextStep"] = (
        "Implement the smallest provider-side merge canary for one non-production candidate: configure the explicit "
        "repository-owned required-check set, trigger the real GitHub-facing executor from provider events, prove one "
        "successful exact-head merge plus representative missing-check, unresolved-review, stale-head, duplicate-event, "
        "and unauthorized-target blocks, then broaden destinations only after those gates are stable. When a promotion "
        "gate fails with an agent-capable repair, emit the exact repair packet to P115 AFK Feedback-Driven Development "
        "Loop Executor; keep promotion blocked until a newly authored exact candidate returns through all required gates."
    )
    p["proofGate"] = (
        "The actual provider workflow/app validates one pinned candidate SHA through required static/unit/integration gates, "
        "the canonical harness validator, and applicable application E2E tests; the exact repository-owned required-check "
        "names are present and successful for that SHA; unresolved review threads, insufficient review decision, required "
        "SKIP/FAIL/missing/pending checks, stale head/base, and unauthorized destination block mutation; the executor "
        "immediately re-reads provider truth and performs the merge itself with an expected-head/merge-queue guard; duplicate "
        "wakeups cannot double-merge; artifacts are traceable to that SHA; least-privilege permissions and concurrent/recursive "
        "writer guards are explicit; and post-promotion provider evidence contains the proven candidate without relying on "
        "local checkout state or bypassing repository protection."
    )

    content = p["copyContent"]
    if REQUIRED_PHRASES[0] not in content:
        anchor = "9. MAKE ARTIFACTS AND CACHES PART OF THE PROOF CHAIN"
        if anchor not in content:
            raise SystemExit("P105 insertion anchor moved")
        section = '''8A. PROVIDER-SIDE MERGE EXECUTOR — NO HUMAN MEMORY STEP
The durable promotion system must own the last-mile provider mutation. Use a GitHub-facing application/workflow/bot with repository-owned policy rather than depending on a person or coding agent to notice a green PR and remember a final merge command.
- Keep an explicit repository-owned manifest/configuration of required check names for each destination. Query conclusions for the exact candidate SHA and require every named check; do not infer readiness from whichever checks happen to be visible, from an aggregate green badge, or from check counts. A renamed/missing required check is a blocking contract mismatch until policy is deliberately updated.
- Query GitHub/provider truth directly for PR state, exact head/base identity, draft/open state, head repository, mergeability or merge-queue eligibility, branch/ruleset requirements, review decision, and unresolved review threads. Treat unresolved threads or insufficient required approval as blocking even when CI is green.
- Wake on provider events that can change readiness (candidate/check/workflow/review/base/queue state), with a bounded recovery recheck only where provider event coverage is incomplete. Each wakeup reconstructs readiness from provider truth; it does not trust remembered model state or an earlier event payload as current truth.
- Immediately before mutation, immediately re-read provider truth and compare the current head/base/gates with the proven candidate. Merge through the provider API with the expected head SHA when direct merge is authorized, or enter the repository's merge queue when protection requires it. Never bypass queue/protection merely because the app token can write.
- A local branch switch or local checkout is not part of normal merge convergence. Local checkout may be used for authoring, diagnostics, or repository-owned validation when needed, but readiness and the merge side effect are provider-side operations. The terminal success criterion is provider merge/queue result plus refreshed containment, not `git switch main` on an operator workstation.
- Make duplicate wakeups idempotent. If the PR is already merged, verify the recorded integration SHA/containment and emit the existing-success receipt rather than attempting another mutation. Serialize competing writers and use compare-and-set/expected-head semantics so a head move between readiness evaluation and merge is rejected.
- Give the merge executor only the minimum GitHub App/workflow permissions it needs. Never hardcode a PAT. Record app/workflow identity, event ID/run ID, policy/check-set version, candidate SHA/base, review-thread status, merge API/queue response, and resulting integration SHA in the promotion receipt.

'''
        content = content.replace(anchor, section + anchor, 1)

    if "provider-side merge executor" not in content.lower():
        raise SystemExit("provider-side merge section did not materialize")

    old_probe = "Prove: green exact-head path reaches the authorized promotion action; harness-validator failure blocks it; application-E2E failure blocks it when required; required SKIP blocks; stale/moved candidate blocks; unauthorized target blocks; concurrent writer/merge-queue behavior is safe; recursion guard prevents a bot loop."
    new_probe = "Prove: green exact-head path reaches the authorized provider-side promotion action without a remembered human/agent merge step; harness-validator failure blocks it; application-E2E failure blocks it when required; required SKIP blocks; an explicitly required check that is missing/renamed/pending/failing blocks; an unresolved review thread or insufficient required approval blocks; stale/moved candidate blocks at the final provider re-read; unauthorized target blocks; duplicate wakeups are idempotent; concurrent writer/merge-queue behavior is safe; recursion guard prevents a bot loop."
    if old_probe in content:
        content = content.replace(old_probe, new_probe, 1)
    elif new_probe not in content:
        raise SystemExit("P105 prototype proof sentence moved")

    old_receipt = "Emit a concise workflow summary plus machine-readable promotion receipt containing provider run ID, event/actor, candidate SHA/base identity, required jobs/conclusions, harness receipt identity, E2E receipt/artifacts, promoted artifact identity, target, mutation result, final integration/deployment SHA, and proof ceiling."
    new_receipt = "Emit a concise workflow summary plus machine-readable promotion receipt containing provider run ID/event ID, app/workflow actor identity, candidate SHA/base identity, repository-owned required-check policy version and exact check names/conclusions, review decision and unresolved-thread count, harness receipt identity, E2E receipt/artifacts, promoted artifact identity, target, merge API/queue mutation result, final integration/deployment SHA, and proof ceiling."
    if old_receipt in content:
        content = content.replace(old_receipt, new_receipt, 1)
    elif new_receipt not in content:
        raise SystemExit("P105 receipt sentence moved")

    old_deliver = "Report promotion graph; canonical commands/workflows; exact-head identity model; harness-vs-application-E2E gates; trigger/dependency design; permissions/concurrency/loop guards; artifact provenance; success and blocking-run evidence; provider run/receipt; post-promotion containment; commit/PR/mainline state; proof ceiling; exact next canary command or authorization blocker."
    new_deliver = "Report promotion graph; canonical commands/workflows; provider-side merge executor/app identity; explicit required-check manifest and review-thread gate; exact-head identity and final compare-and-set model; harness-vs-application-E2E gates; trigger/recovery-event design; permissions/concurrency/idempotency/loop guards; artifact provenance; success and blocking-run evidence; provider run/merge-or-queue receipt; post-promotion containment; commit/PR/mainline state; proof ceiling; exact next canary trigger or authorization blocker."
    if old_deliver in content:
        content = content.replace(old_deliver, new_deliver, 1)
    elif new_deliver not in content:
        raise SystemExit("P105 deliver sentence moved")

    p["copyContent"] = content
    keywords = p.setdefault("keywords", [])
    for keyword in (
        "provider-side merge executor",
        "automated PR merge",
        "GitHub App merge bot",
        "explicit required check names",
        "unresolved review threads",
        "expected head merge",
        "idempotent merge",
        "last-mile merge automation",
    ):
        if keyword not in keywords:
            keywords.append(keyword)

    for phrase in REQUIRED_PHRASES:
        if phrase not in p["copyContent"]:
            raise SystemExit(f"missing strengthened P105 phrase: {phrase}")

    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_regression() -> None:
    text = TEST.read_text(encoding="utf-8")
    method_name = "test_p105_owns_provider_side_last_mile_merge_execution"
    if method_name in text:
        return
    marker = "    def test_repository_automation_prompts_have_distinct_generation_and_promotion_roles(self) -> None:\n"
    if marker not in text:
        raise SystemExit("focused P105 regression anchor moved")
    method = '''    def test_p105_owns_provider_side_last_mile_merge_execution(self) -> None:
        prompt = self.full["P105"]
        content = prompt["copyContent"]
        self.assertEqual(prompt["name"], "Validated CI/CD Promotion Pipeline Builder")
        self.assertEqual(prompt["class"], "HARNESS / CI-CD PROMOTION")
        for phrase in (
            "PROVIDER-SIDE MERGE EXECUTOR — NO HUMAN MEMORY STEP",
            "explicit repository-owned required-check names",
            "unresolved review threads",
            "immediately re-read provider truth",
            "expected head SHA",
            "A local branch switch or local checkout is not part of normal merge convergence",
            "duplicate wakeups are idempotent",
            "GitHub App/workflow permissions",
            "merge API/queue response",
            "missing/renamed/pending/failing blocks",
        ):
            self.assertIn(phrase, content)
        self.assertIn("last-mile provider-side merge", prompt["useWhen"])
        self.assertIn("provider-side executor", prompt["expectedOutput"])
        self.assertIn("unresolved review threads", prompt["proofGate"])
        self.assertIn("explicit repository-owned required-check set", prompt["nextStep"])
        self.assertNotIn("git switch main", content)

'''
    text = text.replace(marker, method + marker, 1)
    TEST.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    strengthen_p105()
    strengthen_regression()
    print("P105 provider-side merge executor strengthening applied")
