#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
prompts_path = ROOT / "docs" / "prompts.json"
policy_path = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
operator_path = ROOT / "harness" / "specs" / "operator-delivery.md"
test_path = ROOT / "tests" / "test_remote_freshness_p13_iteration.py"

prompts_text = prompts_path.read_text(encoding="utf-8")
policy_text = policy_path.read_text(encoding="utf-8")
operator_text = operator_path.read_text(encoding="utf-8")
test_text = test_path.read_text(encoding="utf-8")

prompts = json.loads(prompts_text)
policy = json.loads(policy_text)
by_id = {item["id"]: item for item in prompts}
for required in ("P07", "P48"):
    if required not in by_id:
        raise SystemExit(f"Missing canonical prompt {required}")

# P07 is a raw canonical execution prompt as well as an effective-policy consumer.
p07 = by_id["P07"]
p07["inspectFirst"] = (
    "Fresh fetched remote refs/default branch; current/open/recent overlapping branches and PRs; "
    "latest relevant commits; owning contracts, profiles, registries, generators, validators, CI "
    "results, artifact manifests/reports, branch/worktree state, diff, and mutation capability."
)
if "fresh repository and evidence floor" not in p07["expectedOutput"]:
    p07["expectedOutput"] = p07["expectedOutput"].replace(
        "Repository progress executed from a refreshed and reconciled remote/default-branch floor,",
        "Repository progress executed from a refreshed and reconciled remote/default-branch floor and fresh repository and evidence floor,",
    )
if "current evidence floor" not in p07["proofGate"]:
    p07["proofGate"] += (
        " The current evidence floor—latest relevant commits, owning contracts/profiles/generators, "
        "validator/CI conclusions, and registered artifact/report identities—is refreshed before "
        "build/repair decisions; stale prior-agent or prior-head proof is never reused as current proof."
    )
p07_anchor = (
    "- After fetching, compare the current HEAD, its tracking branch, and the remote default branch; "
    "inspect current/open/recent overlapping branches and PRs from the refreshed floor. Treat an unfetched local branch list as stale evidence.\n"
)
p07_evidence = (
    "- Establish a FRESH EVIDENCE FLOOR before BUILD, REPAIR, ARTIFACT, implementation, or certification work: inspect the latest relevant commits; owning contracts/specs/profiles/registries/generators; current validators/tests/CI conclusions; registered artifact manifests/reports; and relevant handoff/ledger evidence. Prefer current provider/repository truth over remembered context, copied prior-agent claims, or stale local outputs.\n"
    "- Resolve the current canonical generator/template/schema and latest accepted/reference artifact identity after the refresh. A prior artifact, validation result, or successful run belongs to the head and inputs that produced it; do not silently promote it to a moved head or changed dependency floor.\n"
)
if "FRESH EVIDENCE FLOOR" not in p07["copyContent"]:
    if p07_anchor not in p07["copyContent"]:
        raise SystemExit("P07 freshness anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(
        p07_anchor, p07_anchor + p07_evidence, 1
    )

# P48 is the direct live-cert prompt, so harden its raw source even if a consumer bypasses
# effective policy injection and copies docs/prompts.json directly.
p48 = by_id["P48"]
p48["inspectFirst"] = (
    "Fresh remote/default-branch state; current/open/recent overlapping branches and PRs; latest "
    "relevant commits and required evidence; exact commit/artifact to certify; local repository and "
    "terminal access; live-runtime-certification policy; AgentSwitchboard v1 schemas; Cursor runtime "
    "entrypoint; real provider route; validators; evidence root; and intended PR authority."
)
if "freshness gate" not in p48["proofGate"].lower():
    p48["proofGate"] += (
        " The live-cert freshness gate proves remote refs/default branch, overlapping PR/branch "
        "ownership, latest required evidence, and the exact certified commit/artifact were current "
        "when certification began; any material head, base, dependency, generator/profile, or artifact "
        "movement invalidates affected proof until it is refreshed and rerun."
    )
live_block = """FRESH REPOSITORY + EVIDENCE FLOOR BEFORE LIVE CERT
- Before recording the Git floor or selecting the certification subject, run `git fetch --all --prune --tags` (or provider-equivalent refresh), resolve the actual remote default branch, and inspect current/open/recent overlapping branches and PRs plus the latest relevant commits. Never certify a remembered SHA, unfetched checkout, or branch merely because it worked earlier.
- Resolve and record the exact certification subject after that refresh: commit SHA, required base/dependency floor, artifact path plus manifest/hash when applicable, owning generator/profile/schema, target, phase, and proof ceiling.
- Inspect the latest relevant evidence before running: current validators/tests/CI conclusions, registered build/artifact reports, prior live-cert receipts, handoff/ledger evidence, and known blockers. Classify prior proof as current or stale; CI/build proof from another head is context, not certification of this one.
- If the remote base/head, required dependency, generator/profile/schema, target artifact, or evidence owner moves after preflight, invalidate the affected proof, refresh/reconcile safely, rebuild/revalidate where required, and rerun the affected live certification. Do not bless stale code with a newer runtime result or a newer head with an older runtime receipt.
"""
if "FRESH REPOSITORY + EVIDENCE FLOOR BEFORE LIVE CERT" not in p48["copyContent"]:
    header, sep, rest = p48["copyContent"].partition("\n\n")
    if not sep:
        raise SystemExit("P48 copyContent header separator missing")
    p48["copyContent"] = header + "\n\n" + live_block + "\n" + rest

# Shared effective-prompt policy: all operational BUILD/REPAIR/ARTIFACT prompts inherit this.
appendix = str(policy["copy_content_appendix"])
shared_anchor = (
    "- Inspect current/open/recent overlapping branches and PRs after the refresh. Do not treat an "
    "unfetched local branch list, remembered SHA, or stale feature base as the repository floor.\n"
)
shared_evidence = (
    "- Establish a FRESH EVIDENCE FLOOR before BUILD, REPAIR, ARTIFACT, implementation, or certification work: inspect latest relevant commits; owning contracts/specs/profiles/registries/generators; current validators/tests/CI conclusions; registered artifact manifests/reports; and relevant handoff/ledger evidence. Prefer current repository/provider truth over remembered context, prior-agent completion claims, or stale local outputs.\n"
    "- For BUILD / REPAIR / ARTIFACT prompts, resolve the current canonical generator/template/schema and latest accepted/reference artifact identity after refresh. Reuse prior artifacts or proof only when their commit, inputs, dependencies, and owning contract still match the current floor.\n"
    "- Treat evidence as versioned proof: a successful validator, CI run, build, or live-cert receipt proves the exact head/artifact/input floor it observed. If that head, required base/dependency, generator/profile/schema, or target artifact moves, refresh and rerun the affected proof instead of carrying stale evidence forward.\n"
)
if "FRESH EVIDENCE FLOOR" not in appendix:
    if shared_anchor not in appendix:
        raise SystemExit("Shared freshness anchor missing")
    appendix = appendix.replace(shared_anchor, shared_anchor + shared_evidence, 1)
policy["copy_content_appendix"] = appendix
reuse_rule = str(policy["existing_work_reuse"]["rule"])
evidence_clause = (
    " Refresh the relevant evidence floor too—latest commits, owning contracts/generators, "
    "validators/CI, and registered artifact/report identities—before treating prior branch or PR "
    "proof as current."
)
if "Refresh the relevant evidence floor too" not in reuse_rule:
    policy["existing_work_reuse"]["rule"] = reuse_rule.rstrip() + evidence_clause

# Live-cert domain law: current code and current evidence must both be pinned before runtime proof.
live_section = """## Freshness gate for live certification

- Before selecting the certification subject, refresh remote/provider truth (`git fetch --all --prune --tags` or provider equivalent), resolve the actual default branch, and inspect current/open/recent overlapping PRs and branches plus the latest relevant commits. An unfetched checkout, remembered SHA, old feature base, or prior handoff is not a certification floor.
- Establish the current evidence floor: owning runtime-certification contract, launcher/generator/profile/schema, focused validators, current CI/build conclusions, registered artifact manifests/reports, prior live-cert receipts, and known blockers. Prior evidence remains useful history but only proves the exact head/artifact/inputs it observed.
- Pin the exact subject after refresh: commit SHA, required base/dependency floor, target, phase, artifact path and manifest/hash when applicable, runtime route/provider, and proof ceiling. The runtime report must record those identities.
- If the remote base/head, dependency, launcher/generator/profile/schema, target artifact, or evidence owner moves after preflight, mark affected proof stale and refresh/reconcile/rebuild/revalidate before claiming certification. A runtime pass cannot bless stale repository state, and old runtime evidence cannot certify a newer head.
- Preserve dirty/divergent/local-only work while refreshing; never force-reset merely to obtain a certification floor.

"""
if "## Freshness gate for live certification" not in operator_text:
    operator_anchor = "## Evidence and artifact safety\n"
    if operator_anchor not in operator_text:
        raise SystemExit("Operator-delivery evidence section anchor missing")
    operator_text = operator_text.replace(operator_anchor, live_section + operator_anchor, 1)

# Regression coverage: enumerate the whole build-like effective registry and bind P48/domain law.
setup_anchor = (
    "        cls.effective = {\n"
    "            item[\"id\"]: item for item in build_prompt_kit_registry.load_prompt_registry()\n"
    "        }\n"
)
if "cls.operator_delivery" not in test_text:
    if setup_anchor not in test_text:
        raise SystemExit("Focused test setup anchor missing")
    test_text = test_text.replace(
        setup_anchor,
        setup_anchor
        + "        cls.operator_delivery = (ROOT / \"harness\" / \"specs\" / \"operator-delivery.md\").read_text(encoding=\"utf-8\")\n",
        1,
    )
shared_assert_anchor = '        self.assertIn("never force-reset", appendix)\n'
if 'self.assertIn("FRESH EVIDENCE FLOOR", appendix)' not in test_text:
    if shared_assert_anchor not in test_text:
        raise SystemExit("Shared freshness assertion anchor missing")
    test_text = test_text.replace(
        shared_assert_anchor,
        shared_assert_anchor
        + '        self.assertIn("FRESH EVIDENCE FLOOR", appendix)\n'
        + '        self.assertIn("owning contracts/specs/profiles/registries/generators", appendix)\n'
        + '        self.assertIn("registered artifact manifests/reports", appendix)\n'
        + '        self.assertIn("versioned proof", appendix)\n',
        1,
    )
new_tests = r'''
    def test_every_build_repair_or_artifact_prompt_inherits_fresh_evidence_floor(self) -> None:
        build_like = [
            prompt
            for prompt in self.effective.values()
            if any(token in str(prompt["type"]).upper() for token in ("BUILD", "REPAIR", "ARTIFACT"))
        ]
        self.assertGreater(len(build_like), 0)
        for prompt in build_like:
            with self.subTest(prompt_id=prompt["id"], prompt_type=prompt["type"]):
                content = prompt["copyContent"]
                self.assertIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", content)
                self.assertIn("current/open/recent overlapping branches and PRs", content)
                self.assertIn("FRESH EVIDENCE FLOOR", content)
                self.assertIn("registered artifact manifests/reports", content)
                self.assertIn("current canonical generator/template/schema", content)

    def test_p48_and_live_cert_domain_law_pin_fresh_code_artifact_and_evidence(self) -> None:
        p48 = self.raw["P48"]
        content = p48["copyContent"]
        self.assertIn("FRESH REPOSITORY + EVIDENCE FLOOR BEFORE LIVE CERT", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("current/open/recent overlapping branches and PRs", content)
        self.assertIn("artifact path plus manifest/hash", content)
        self.assertIn("current validators/tests/CI conclusions", content)
        self.assertIn("prior live-cert receipts", content)
        self.assertIn("invalidate the affected proof", content)
        self.assertIn("freshness gate", p48["proofGate"].lower())

        domain = self.operator_delivery
        self.assertIn("## Freshness gate for live certification", domain)
        self.assertIn("git fetch --all --prune --tags", domain)
        self.assertIn("current/open/recent overlapping PRs and branches", domain)
        self.assertIn("artifact path and manifest/hash", domain)
        self.assertIn("Prior evidence remains useful history", domain)
        self.assertIn("mark affected proof stale", domain)
'''
if "test_every_build_repair_or_artifact_prompt_inherits_fresh_evidence_floor" not in test_text:
    final_anchor = "\n\nif __name__ == \"__main__\":\n"
    if final_anchor not in test_text:
        raise SystemExit("Focused test final anchor missing")
    test_text = test_text.replace(final_anchor, "\n" + new_tests + final_anchor, 1)

# Validate complete transformed content before any writes, so a missing anchor cannot leave a
# partially migrated checkout.
prompts_out = json.dumps(prompts, indent=2, ensure_ascii=False) + "\n"
policy_out = json.dumps(policy, indent=2, ensure_ascii=False) + "\n"
json.loads(prompts_out)
json.loads(policy_out)
for label, text, required in (
    ("P07", by_id["P07"]["copyContent"], "FRESH EVIDENCE FLOOR"),
    ("P48", by_id["P48"]["copyContent"], "FRESH REPOSITORY + EVIDENCE FLOOR BEFORE LIVE CERT"),
    ("policy", policy_out, "FRESH EVIDENCE FLOOR"),
    ("operator", operator_text, "## Freshness gate for live certification"),
    ("tests", test_text, "test_every_build_repair_or_artifact_prompt_inherits_fresh_evidence_floor"),
):
    if required not in text:
        raise SystemExit(f"Transformed {label} missing required marker: {required}")

prompts_path.write_text(prompts_out, encoding="utf-8")
policy_path.write_text(policy_out, encoding="utf-8")
operator_path.write_text(operator_text, encoding="utf-8")
test_path.write_text(test_text, encoding="utf-8")
