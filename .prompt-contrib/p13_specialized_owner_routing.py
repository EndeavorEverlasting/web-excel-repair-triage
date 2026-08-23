#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/prompt-overrides.v1.json"
TEST = ROOT / "tests/test_prompt_kit_mainline_delivery.py"
BRANCH_WORKFLOW = ROOT / ".github/workflows/p13-specialized-owner-routing-repair.yml"
SELF = Path(__file__).resolve()


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
before_len = len(p13["copyContent"])

p13["expectedOutput"] = (
    "Immediate advancement of the current critical path, an explicit Sub-Part Agent launch/packet or "
    "serialized-dependency reason, the smallest implemented durable prevention, specialist repair routed "
    "to its existing canonical owner instead of duplicated into P13, and the exact validated owned change "
    "integrated into the current default branch and verified there; otherwise an exact integration/user-only "
    "blocker plus the action that advances it."
)
p13["proofGate"] = (
    "The recurrence is evidence-backed; current proof floor and next gate are explicit; critical-path work "
    "advances until a bounded fixed point or exact blocker; Sub-Part Agent analysis is present; one correct "
    "authority owns the prevention; any material specialist failure mode is routed to its canonical owner "
    "without duplicating that owner's doctrine into P13; focused regression/build/parity validation passes; "
    "a deliberate second pass finds no practical in-scope improvement; and the exact validated owned head is "
    "integrated into and verified on the current default branch when authorized. A branch or PR alone is "
    "insufficient completion; when integration is blocked, the exact gate and advancing action are proven "
    "without proof inflation."
)

marker = "6A. SPECIALIZED OWNER ROUTING — REFER, DO NOT DUPLICATE"
block = """

6A. SPECIALIZED OWNER ROUTING — REFER, DO NOT DUPLICATE
P13 owns recurrence recovery, urgency, durable prevention, and convergence. It must not absorb the full operating doctrine of specialist prompts.
- If the recurring defect is an agent's plausible-but-wrong result and the repair depends on whether required truth was absent, ignored, or buried in excessive context, route diagnosis to P100. If exact IDs, schemas, API/tool parameters, or protected side effects need deterministic grounding, route the prevention layer to P101.
- If the defect is systemic runtime context load/selection, route to P68; if it is repository spec/harness progressive-disclosure bloat, route to P76.
- If the recurrence is a questionable done/closed/handoff claim, route verification to P83. If a live-certification claim depends on exact subject/evidence freshness or stale-proof invalidation, route certification to P48.
- Record the specialist owner and the evidence that triggered it, invoke or extend that owner when the specialized repair is in scope, and continue P13's critical path. Routing is not a stopping condition.
- Do not copy the specialist prompt's full checklist into P13. Add only the smallest P13-specific routing sentence or regression needed to prevent the recurrence.
"""
if marker not in p13["copyContent"]:
    needle = "\n\n7. REGRESSION SCENARIO\n"
    if needle not in p13["copyContent"]:
        raise SystemExit("P13 regression section anchor not found")
    p13["copyContent"] = p13["copyContent"].replace(needle, block + needle, 1)

after_len = len(p13["copyContent"])
growth = after_len - before_len
if growth > 1800:
    raise SystemExit(f"P13 routing growth too large: +{growth} chars")
if after_len >= 18000:
    raise SystemExit(f"P13 raw copy exceeds anti-bloat ceiling: {after_len}")
print(f"P13 copyContent: {before_len} -> {after_len} (+{growth})")
REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

text = TEST.read_text(encoding="utf-8")
test_marker = "    def test_p13_routes_specialized_failures_without_absorbing_their_doctrine(self):\n"
if test_marker not in text:
    insertion = '''    def test_p13_routes_specialized_failures_without_absorbing_their_doctrine(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        self.assertIn("specialist repair routed", p13["expectedOutput"])
        self.assertIn("specialist failure mode is routed to its canonical owner", p13["proofGate"])
        for phrase in (
            "SPECIALIZED OWNER ROUTING — REFER, DO NOT DUPLICATE",
            "route diagnosis to P100",
            "route the prevention layer to P101",
            "route to P68",
            "route to P76",
            "route verification to P83",
            "route certification to P48",
            "Routing is not a stopping condition",
            "Do not copy the specialist prompt's full checklist into P13",
        ):
            self.assertIn(phrase, copy)

        ai = load_json("registry/prompts/ai-engineering-level-up-prompts.v1.json")
        ai_ids = {item["id"] for item in ai["prompts"]}
        self.assertTrue({"P68", "P100", "P101"}.issubset(ai_ids))
        spec = load_json("registry/prompts/spec-architecture-prompts.v1.json")
        spec_ids = {item["id"] for item in spec["prompts"]}
        self.assertIn("P76", spec_ids)
        base = load_json("docs/prompts.json")
        base_ids = {item["id"] for item in base}
        self.assertIn("P48", base_ids)
        ledger = load_json("registry/prompts/repository-work-ledger-prompts.v1.json")
        ledger_ids = {item["id"] for item in ledger["prompts"]}
        self.assertIn("P83", ledger_ids)
        self.assertLess(len(copy), 18000)

'''
    anchor = "    def test_p65_can_route_repeated_friction_without_browser_finder(self):\n"
    if anchor not in text:
        raise SystemExit("focused test insertion anchor not found")
    TEST.write_text(text.replace(anchor, insertion + anchor, 1), encoding="utf-8")

run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
run("python", "-m", "unittest", "tests.test_prompt_kit_mainline_delivery", "-v")
run("python", "-m", "unittest", "tests.test_remote_freshness_p13_iteration", "-v")
run("python", "-m", "unittest", "tests.test_ai_engineering_level_up", "tests.test_repository_work_ledger_prompt", "tests.test_spec_architecture_prompt_registry", "-v")
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("git", "diff", "--check")

copy = p13["copyContent"]
required = ["P100", "P101", "P68", "P76", "P83", "P48", "Routing is not a stopping condition"]
missing = [item for item in required if item not in copy]
if missing:
    raise SystemExit(f"missing specialized owner routes: {missing}")
forbidden = ["FACTUALITY_MISSING_CONTEXT", "FAITHFULNESS_CONTEXT_IGNORED", "ATTENTION_SATURATION", "GROUNDED_PASS", "UNSOURCED_BLOCK"]
leaked = [item for item in forbidden if item in copy]
if leaked:
    raise SystemExit(f"P13 absorbed specialist implementation doctrine: {leaked}")
print(f"P13 specialized routing second-pass critique: PASS; chars={len(copy)}")
run("git", "diff", "--stat")

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
if BRANCH_WORKFLOW.exists():
    run("git", "rm", str(BRANCH_WORKFLOW.relative_to(ROOT)))
run("git", "rm", str(SELF.relative_to(ROOT)))
run("git", "add", "registry/prompts/prompt-overrides.v1.json", "tests/test_prompt_kit_mainline_delivery.py", "web/prompt-kit/index.html")
run("git", "diff", "--cached", "--check")
run("git", "commit", "-m", "feat(prompt-kit): route P13 to specialized canonical owners")
run("git", "push", "origin", "HEAD:feat/p13-specialized-owner-routing-20260822")
