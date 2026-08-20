#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 1. Strengthen P07 and P13 in their canonical raw source.
prompts_path = ROOT / "docs" / "prompts.json"
prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
by_id = {item["id"]: item for item in prompts}

p07 = by_id["P07"]
p07["inspectFirst"] = (
    "Fresh fetched remote refs/default branch and overlapping branches/PRs; repo patterns, "
    "branch/worktree state, tests, validators, diff, and mutation capability."
)
p07["expectedOutput"] = (
    "Repository progress executed from a freshly reconciled remote/default-branch floor, "
    "iterated through implementation, validation, evidence review, critique, and improvement "
    "until a bounded fixed point, then integrated into the current default branch when gates "
    "permit or stopped at an exact named blocker; agent-capable work remains autonomous and "
    "user involvement is reserved for genuinely user-only dependencies."
)
p07["proofGate"] = (
    "Remote refs/default branch and overlapping work are refreshed before implementation and "
    "again before integration; stale or diverged local branch state is reconciled or safely "
    "isolated without overwriting unique work; at least one deliberate second-pass evidence "
    "review follows the first implementation/validation pass; every concrete in-scope gap "
    "discovered by a pass is repaired and revalidated; the loop reaches a fixed point with no "
    "practical safe in-scope improvement or unresolved acceptance gap, then the intended "
    "change is verified on the current default branch or an exact integration blocker is "
    "proven; a branch or PR alone is insufficient; no agent-capable task is delegated back to "
    "the user, and any user escalation names a genuinely user-only dependency."
)
fresh_block = """REMOTE FRESHNESS / BRANCH FLOOR CONTRACT
- Before branch-sensitive analysis or repository mutation, refresh remote truth with `git fetch --all --prune --tags` (or the provider-equivalent fetch when a local git remote is unavailable).
- Resolve the repository's actual remote default branch from provider metadata or `refs/remotes/origin/HEAD`; do not assume a local `main`, remembered SHA, or previously opened feature branch is current.
- After fetching, compare the current HEAD, its tracking branch, and the remote default branch; inspect current/open/recent overlapping branches and PRs from the refreshed floor. Treat an unfetched local branch list as stale evidence.
- If the current clean tracking branch is only behind, fast-forward with `git pull --ff-only` or the repository-approved equivalent. If it diverged, reconcile with the repository-approved merge/rebase strategy or use an isolated worktree; never force-reset, force-pull, or overwrite unique dirty/separately owned work.
- If the owned feature branch is based on an older default-branch floor, update/reconcile that base before implementation and proof unless the sprint explicitly requires historical-state testing.
- Re-fetch immediately before final exact-head validation/integration. If the remote base or owned head moved after proof, reconcile and rerun affected validation instead of merging stale evidence.
- `Pull latest` means refresh and safely reconcile remote truth, not blindly rewrite local state."""
if "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT" not in p07["copyContent"]:
    anchor = "MAINLINE CONVERGENCE\n"
    if anchor not in p07["copyContent"]:
        raise SystemExit("P07 mainline anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(
        anchor, fresh_block + "\n" + anchor, 1
    )

p13 = by_id["P13"]
p13["sprintRole"] = (
    "Turn repeated pain into the smallest enforceable repo doctrine through fresh-floor "
    "evidence and iterative rule/validator prototypes"
)
p13["inspectFirst"] = (
    "Fresh remote/default-branch state; the repeated incident and counterexample; current "
    "rules, validators, hooks, workflows, skills, tests, and existing enforcement points."
)
p13["expectedOutput"] = (
    "A minimal rule/validator/hook improvement that has been prototyped, tested against the "
    "actual repeated failure plus a counterexample, critiqued for overlap/context bloat and "
    "false positives, refined to a bounded fixed point, and routed to the existing owner."
)
p13["nextStep"] = (
    "Refresh repository truth, prototype the smallest prevention mechanism, test it against "
    "the incident and a counterexample, critique and revise until the bounded fixed point, "
    "then implement it when already authorized or hand the exact bounded patch to P07 without "
    "asking the user to choose among technically equivalent safe variants."
)
p13["proofGate"] = (
    "Stale branch state is ruled out before inventing doctrine; at least one deliberate "
    "PROTOTYPE -> TEST -> CRITIQUE -> REVISE pass occurs; the final change is the smallest "
    "non-duplicative enforceable prevention mechanism, practical false-positive/counterexample "
    "behavior is considered, and the result does not create a rule landfill or redundant docs."
)
p13["copyContent"] = """REVIEW THIS SPRINT FOR A REUSABLE SELF-IMPROVING RULE, VALIDATOR, HOOK, OR WORKFLOW CHANGE. PROTOTYPE THE PREVENTION MECHANISM BEFORE PRESENTING IT; DO NOT TURN ONE BAD RUN INTO PERMANENT DOCTRINE WITHOUT CURRENT EVIDENCE.

REMOTE TRUTH FIRST
- When repository access exists, refresh remote truth before diagnosing the incident: `git fetch --all --prune --tags`, resolve the actual remote default branch, and compare the relevant local/feature head with the refreshed default/tracking refs.
- Inspect current/open/recent overlapping branches and PRs. A stale checkout, old feature base, unpulled remote change, or already-fixed mainline state is an incident cause to repair—not evidence that another permanent rule is needed.
- Never force-reset or overwrite dirty/separately owned work merely to obtain freshness; reconcile safely or use an isolated worktree.

ITERATIVE RULE PROTOTYPE LOOP
1. EVIDENCE THE REPEATED PAIN
- Name the concrete repeated mistake, explanation, setup issue, stale-branch failure, command failure, safety issue, or coordination defect.
- Separate FACT from INFERENCE. Require at least one real incident; prefer multiple occurrences when available.

2. FIND THE EXISTING OWNER BEFORE INVENTING
- Search current rules, path-scoped governance, validators, hooks, workflows, scripts, skills, manifests, tests, and code for an existing prevention mechanism.
- If an existing mechanism already owns the behavior, repair or strengthen it instead of adding another document/rule surface.

3. PROTOTYPE THE SMALLEST PREVENTION
- Draft the smallest candidate that would have prevented or detected the incident: a concise rule, validator assertion, hook, workflow gate, helper, test, or deletion/simplification of stale doctrine.
- Prefer executable enforcement over prose when the behavior can be checked deterministically.
- Keep the prototype reversible and scoped; do not publish the first plausible wording as final.

4. TEST THE PROTOTYPE AGAINST REALITY
- Apply or simulate the candidate against the actual incident.
- Check at least one counterexample/normal workflow so the candidate does not block valid work or create needless operator ceremony.
- For branch/state problems, test that the candidate distinguishes stale remote/local state from legitimately divergent or dirty work.

5. CRITIQUE
Ask:
- Would this have prevented or detected the incident early enough?
- Does it duplicate a stronger existing contract?
- Is the rule too broad, too verbose, or likely to cause context/documentation bloat?
- Can a validator/test/helper enforce it instead of prose?
- Does it create false positives, destructive git behavior, permission theater, or user involvement for agent-capable work?
- What old rule can be deleted, merged, or simplified if this one is adopted?

6. REVISE AND REPEAT
- Convert each concrete critique into the next bounded prototype immediately.
- Repeat PROTOTYPE -> TEST -> CRITIQUE -> REVISE until a bounded fixed point: the smallest useful prevention mechanism handles the incident, preserves the counterexample, has one clear owner, and no practical safe simplification/enforcement improvement remains.
- Do not manufacture revisions merely to increase iteration count. A later pass may make zero changes only when its evidence proves the candidate is already at the fixed point.

AUTONOMY
- Do not ask the user to compare rule wording, inspect files, rerun tests, or choose among technically equivalent safe implementations when the agent can resolve those questions from repository evidence and prototypes.
- If mutation is already authorized by the active sprint and safe, implement/validate the bounded prevention in its existing owner. Otherwise produce the exact patch/target and route execution to P07. Escalate only a genuinely user-only preference, authorization, credential, physical action, or irreversible policy decision.

OUTPUT
1. WHAT REPEATED
- incident(s), evidence, and whether stale branch/floor state contributed
2. EXISTING OWNER
- current rule/validator/hook/workflow/skill inspected and why it is sufficient or insufficient
3. PROTOTYPE ITERATIONS
- candidate by pass
- incident test
- counterexample test
- critique/gap closed
4. FINAL PREVENTION MECHANISM
- target file/owner
- exact concise wording or executable validator/hook/test change
- why this is smaller/stronger than alternatives
5. VALIDATION
- command/test/fixture that proves prevention
- false-positive/counterexample result
6. DELETE / PRUNE
- stale or duplicated doctrine to remove/merge/simplify
7. EXECUTION STATE
- implemented now / route to P07 / genuine user-only gate
- commit/PR/mainline proof when mutation occurred

The goal is repository memory that improves itself through evidence, not a rule landfill."

prompts_path.write_text(json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# 2. Strengthen the shared operational policy so every operational/build prompt starts from
# refreshed remote truth without duplicating the block in every raw prompt record.
policy_path = ROOT / "registry" / "prompts" / "actionable-next-step-policy.v1.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
policy["freshness_marker"] = "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT"
shared_fresh = """REMOTE FRESHNESS / BRANCH FLOOR CONTRACT
- Before branch-sensitive conclusions or repository mutation, refresh remote refs with `git fetch --all --prune --tags` (or provider-equivalent remote refresh), resolve the actual remote default branch, and compare the current/tracking head with refreshed remote truth.
- Inspect current/open/recent overlapping branches and PRs after the refresh. Do not treat an unfetched local branch list, remembered SHA, or stale feature base as the repository floor.
- Fast-forward a clean behind-only tracking branch with `git pull --ff-only` or repository-approved equivalent. If diverged or dirty, preserve unique/separately owned work and reconcile with repo policy or an isolated worktree; never force-reset merely to become current.
- Reconcile an owned feature branch with the latest required default/dependency floor before implementation/proof when that floor materially affects the work.
- Re-fetch before final exact-head validation/integration. If the base or owned head moved after proof, reconcile and rerun affected checks before merge."""
appendix = str(policy["copy_content_appendix"])
if policy["freshness_marker"] not in appendix:
    integration = str(policy["integration_marker"])
    insertion = "\n\n" + shared_fresh + "\n\n" + integration
    if integration not in appendix:
        raise SystemExit("Shared policy integration marker missing")
    appendix = appendix.replace(integration, insertion, 1)
policy["copy_content_appendix"] = appendix
# Make freshness part of reuse, not merely a late final-report concern.
reuse = policy["existing_work_reuse"]
fresh_clause = (
    " Refresh remote refs/default-branch/provider state before deciding whether an existing "
    "owner is current, stale, diverged, superseded, or safe to extend."
)
if fresh_clause.strip() not in reuse["rule"]:
    reuse["rule"] = reuse["rule"].rstrip() + fresh_clause
policy_path.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# 3. Teach the builder to recognize freshness as part of the current injected policy so raw
# prompts containing an older appendix are upgraded rather than silently retaining stale policy.
builder_path = ROOT / "scripts" / "build_prompt_kit_registry.py"
builder = builder_path.read_text(encoding="utf-8")
required_anchor = '    "integration_marker",\n    "integration_target",'
if '    "freshness_marker",\n' not in builder:
    if required_anchor not in builder:
        raise SystemExit("Builder required-field anchor missing")
    builder = builder.replace(
        required_anchor,
        '    "integration_marker",\n    "freshness_marker",\n    "integration_target",',
        1,
    )
field_anchor = '        "integration_marker",\n        "integration_target",'
if '        "freshness_marker",\n' not in builder:
    if field_anchor not in builder:
        raise SystemExit("Builder string-field anchor missing")
    builder = builder.replace(
        field_anchor,
        '        "integration_marker",\n        "freshness_marker",\n        "integration_target",',
        1,
    )
check_anchor = '''    integration_marker = str(payload["integration_marker"])
    if integration_marker not in appendix:
        raise SystemExit("Actionability appendix must include its integration marker")
    return payload
'''
check_replacement = '''    integration_marker = str(payload["integration_marker"])
    if integration_marker not in appendix:
        raise SystemExit("Actionability appendix must include its integration marker")
    freshness_marker = str(payload["freshness_marker"])
    if freshness_marker not in appendix:
        raise SystemExit("Actionability appendix must include its freshness marker")
    return payload
'''
if "Actionability appendix must include its freshness marker" not in builder:
    if check_anchor not in builder:
        raise SystemExit("Builder policy marker validation anchor missing")
    builder = builder.replace(check_anchor, check_replacement, 1)
apply_anchor = '''    integration_marker = str(policy.get("integration_marker", "")).strip()
    has_current_integration = not integration_marker or integration_marker in copy_content
    if marker not in copy_content:
        strengthened["copyContent"] = f"{copy_content}\\n\\n{appendix}"
    elif not has_current_integration:
'''
apply_replacement = '''    integration_marker = str(policy.get("integration_marker", "")).strip()
    has_current_integration = not integration_marker or integration_marker in copy_content
    freshness_marker = str(policy.get("freshness_marker", "")).strip()
    has_current_freshness = not freshness_marker or freshness_marker in copy_content
    if marker not in copy_content:
        strengthened["copyContent"] = f"{copy_content}\\n\\n{appendix}"
    elif not has_current_integration or not has_current_freshness:
'''
if "has_current_freshness" not in builder:
    if apply_anchor not in builder:
        raise SystemExit("Builder policy application anchor missing")
    builder = builder.replace(apply_anchor, apply_replacement, 1)
builder_path.write_text(builder, encoding="utf-8")

# 4. Add focused regression coverage.
test_path = ROOT / "tests" / "test_remote_freshness_p13_iteration.py"
test_path.write_text('''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry


ROOT = Path(__file__).resolve().parents[1]


class RemoteFreshnessAndP13IterationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {
            item["id"]: item
            for item in json.loads((ROOT / "docs" / "prompts.json").read_text(encoding="utf-8"))
        }
        cls.policy = build_prompt_kit_registry.load_actionability_policy()
        cls.effective = {
            item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()
        }

    def test_shared_operational_policy_requires_fresh_remote_floor(self) -> None:
        marker = self.policy["freshness_marker"]
        appendix = self.policy["copy_content_appendix"]
        self.assertEqual(marker, "REMOTE FRESHNESS / BRANCH FLOOR CONTRACT")
        self.assertIn("git fetch --all --prune --tags", appendix)
        self.assertIn("git pull --ff-only", appendix)
        self.assertIn("Re-fetch before final exact-head validation/integration", appendix)
        self.assertIn("never force-reset", appendix)

        # Representative build/repair executors must inherit freshness from one shared owner.
        for prompt_id in ("P01", "P03", "P07", "P14", "P17", "P18", "P83"):
            with self.subTest(prompt_id=prompt_id):
                content = self.effective[prompt_id]["copyContent"]
                self.assertIn(marker, content)
                self.assertIn("git fetch --all --prune --tags", content)

    def test_builder_upgrades_old_appendix_that_lacks_freshness(self) -> None:
        base = dict(self.raw["P07"])
        marker = self.policy["marker"]
        integration = self.policy["integration_marker"]
        freshness = self.policy["freshness_marker"]
        base["copyContent"] = (
            "BASE PROMPT\\n\\n"
            + marker
            + "\\n- Do not leave NEXT COMMAND blank.\\n\\n"
            + integration
            + "\\n- Treat integration as completion."
        )
        upgraded = build_prompt_kit_registry.apply_actionability_policy(base, self.policy)
        content = upgraded["copyContent"]
        self.assertIn(freshness, content)
        self.assertEqual(content.count(marker), 1)
        self.assertEqual(content.count(integration), 1)

    def test_p07_raw_source_refreshes_and_reconciles_before_building(self) -> None:
        p07 = self.raw["P07"]
        content = p07["copyContent"]
        self.assertIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("refs/remotes/origin/HEAD", content)
        self.assertIn("git pull --ff-only", content)
        self.assertIn("Re-fetch immediately before final exact-head validation/integration", content)
        self.assertIn("never force-reset, force-pull, or overwrite unique", content)
        self.assertIn("refreshed remote/default-branch floor", p07["expectedOutput"])
        self.assertIn("refreshed before implementation", p07["proofGate"])

    def test_p13_prototypes_rules_and_rules_out_stale_branch_before_doctrine(self) -> None:
        p13 = self.raw["P13"]
        content = p13["copyContent"]
        self.assertIn("REMOTE TRUTH FIRST", content)
        self.assertIn("git fetch --all --prune --tags", content)
        self.assertIn("already-fixed mainline state", content)
        self.assertIn("ITERATIVE RULE PROTOTYPE LOOP", content)
        self.assertIn("PROTOTYPE -> TEST -> CRITIQUE -> REVISE", content)
        self.assertIn("counterexample", content)
        self.assertIn("Prefer executable enforcement over prose", content)
        self.assertIn("Do not manufacture revisions", content)
        self.assertIn("Do not ask the user to compare rule wording", content)
        self.assertIn("Stale branch state is ruled out before inventing doctrine", p13["proofGate"])
        self.assertIn("smallest enforceable repo doctrine", p13["sprintRole"])


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")
