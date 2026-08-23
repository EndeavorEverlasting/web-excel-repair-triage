from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json"
TEST = ROOT / "tests/test_ai_engineering_level_up.py"

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p68 = next(item for item in payload["prompts"] if item["id"] == "P68")

expected_identity = {
    "id": "P68",
    "seq": "68",
    "name": "Context Engineering System Refactorer",
    "type": "BUILD + FACTOR",
    "class": "AI ENGINEERING / CONTEXT",
    "color": "Purple",
    "copySheet": "P68_COPY_SAFE",
    "category": "standard",
}
actual_identity = {key: p68[key] for key in expected_identity}
if actual_identity != expected_identity:
    raise SystemExit(f"P68 identity drift before hardening: {actual_identity!r}")

before = p68["copyContent"]
before_len = len(before)
if "CONTINUOUS CONTEXT-CONVERGENCE LOOP" in before:
    raise SystemExit("P68 already contains convergence semantics; refusing duplicate hardening")
if "RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE" not in before:
    raise SystemExit("P68 defining attention-saturation semantics are missing")

p68["sprintRole"] = (
    "Refactor the model context system through repeated measured context-selection passes until a bounded fixed point, "
    "preserving task quality and converging the exact validated owned changes onto the current default branch when authorized"
)
p68["expectedOutput"] = (
    "A context map and budget, measured baseline, deterministic routing/pruning changes, tests for context selection and precedence, "
    "repeated before/after context-quality evidence through a deliberate second pass, reduced unnecessary context load with preserved task quality, "
    "and the exact validated owned change integrated into and verified on the current default branch when authorized. "
    "When attention saturation is observed, include a provenance-preserving compaction or fresh-session handoff and prove critical constraints survive it."
)
p68["nextStep"] = (
    "Repeat REFRESH -> MEASURE -> SELECT HIGHEST-IMPACT CONTEXT DEFECT -> REFACTOR -> VALIDATE -> CRITIQUE -> INTEGRATE -> REMEASURE -> CONTINUE "
    "until a bounded fixed point or exact external/user-only blocker; integrate independently green owned slices when authorized and do not stop at the first green candidate, open PR, or merged slice."
)
p68["proofGate"] = (
    "Every loaded context source has a purpose and owner; deterministic routing replaces default prompt bloat where practical; precedence is explicit; "
    "measured context reduction preserves required behavior; and no hidden context dependency is claimed away without tests. If required truth is already present but ignored, "
    "the first repair reduces/reprioritizes context rather than adding more; compaction must preserve authoritative constraints and provenance. "
    "Completion additionally requires repeated measured refactor/validate/critique passes through a deliberate second pass, no practical in-scope context-system improvement remaining at the bounded fixed point, "
    "and the exact validated owned head integrated into and verified on the current default branch when authorized; a branch, PR, or green CI result alone is insufficient completion."
)

anchor = "\n\n6. DELIVER MEASURED IMPROVEMENT\n"
if anchor not in before:
    raise SystemExit("P68 delivery anchor missing")
section = """

6. CONTINUOUS CONTEXT-CONVERGENCE LOOP
Run context engineering as a bounded evidence loop, not a one-pass cleanup:
REFRESH -> MEASURE -> SELECT HIGHEST-IMPACT CONTEXT DEFECT -> REFACTOR -> VALIDATE -> CRITIQUE -> INTEGRATE -> REMEASURE -> CONTINUE
- A pass counts only when it removes or reroutes a measured context defect, closes a quality/precedence failure, produces decision-changing evidence, or integrates a validated owned slice. Re-reading the same telemetry, branch status, or PR is not progress.
- After the first green candidate, perform a deliberate second pass over remaining context load, stale/duplicated authority, selection failures, representative task quality, and the exact diff. Repair practical in-scope misses and rerun affected proof.
- Integrate independently green context slices when authorized rather than stranding them while broader refactoring remains. A branch, worktree, commit, push, open PR, review-ready state, or green CI is intermediate evidence.
- When the exact validated owned head is mergeable and the repository's shared integration gates permit, merge it into the current default branch in the same run, refresh that branch, and verify the context-system changes and owning validation are present there.
- Continue from refreshed default-branch truth when another safe bounded context defect remains. Do not stop merely because one context slice is green or one bounded slice merged.
- Stop only at the bounded fixed point: measured context-load/quality criteria are satisfied, the deliberate second pass finds no practical in-scope improvement, authorized integration is complete and verified, and no safe executable continuation remains. Otherwise continue or prove the exact blocker and the action that advances it.

7. DELIVER MEASURED IMPROVEMENT
"""
p68["copyContent"] = before.replace(anchor, section, 1)
after_len = len(p68["copyContent"])
if after_len >= 7000:
    raise SystemExit(f"P68 anti-bloat ceiling exceeded: {after_len}")
if after_len - before_len > 2500:
    raise SystemExit(f"P68 growth exceeds hardening budget: +{after_len - before_len}")

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_text = TEST.read_text(encoding="utf-8")
method_name = "test_p68_repeats_context_refactor_until_fixed_point_and_mainline"
if method_name in test_text:
    raise SystemExit("P68 hardening focused regression already exists")
insert_before = "    def test_prompt_finder_and_search_route_the_five_tracks(self) -> None:\n"
if insert_before not in test_text:
    raise SystemExit("P68 focused-test insertion anchor missing")
method = '''    def test_p68_repeats_context_refactor_until_fixed_point_and_mainline(self) -> None:
        raw = json.loads((ROOT / "registry/prompts/ai-engineering-level-up-prompts.v1.json").read_text(encoding="utf-8"))
        source = next(item for item in raw["prompts"] if item["id"] == "P68")
        effective = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}["P68"]
        policy = build_prompt_kit_registry.load_actionability_policy()

        self.assertEqual(source["name"], "Context Engineering System Refactorer")
        self.assertEqual(source["class"], "AI ENGINEERING / CONTEXT")
        self.assertEqual(source["color"], "Purple")
        self.assertEqual(source["category"], "standard")
        self.assertIn("bounded fixed point", source["sprintRole"])
        self.assertIn("current default branch", source["expectedOutput"])
        self.assertIn("REFRESH -> MEASURE -> SELECT HIGHEST-IMPACT CONTEXT DEFECT -> REFACTOR -> VALIDATE -> CRITIQUE -> INTEGRATE -> REMEASURE -> CONTINUE", source["nextStep"])
        self.assertIn("branch, PR, or green CI result alone is insufficient completion", source["proofGate"])

        copy = source["copyContent"]
        for phrase in (
            "ENGINEER THE FULL CONTEXT SYSTEM AROUND THE MODEL",
            "RECOVER FROM ATTENTION SATURATION / THE DUMB ZONE",
            "CONTINUOUS CONTEXT-CONVERGENCE LOOP",
            "A pass counts only when",
            "deliberate second pass",
            "merge it into the current default branch in the same run",
            "verify the context-system changes and owning validation are present there",
            "Do not stop merely because one context slice is green or one bounded slice merged",
            "Stop only at the bounded fixed point",
        ):
            self.assertIn(phrase, copy)

        self.assertNotIn(policy["integration_marker"], copy)
        self.assertIn(policy["integration_marker"], effective["copyContent"])
        for forbidden in ("50,000 FT", "30,000 FT", "15,000 FT", "TREAT CLAIMS AS HYPOTHESES"):
            self.assertNotIn(forbidden, copy)
        self.assertLess(len(copy), 7000)

'''
TEST.write_text(test_text.replace(insert_before, method + insert_before, 1), encoding="utf-8")

print(json.dumps({
    "target": "P68",
    "before_copy_chars": before_len,
    "after_copy_chars": after_len,
    "delta_copy_chars": after_len - before_len,
    "identity": actual_identity,
}, indent=2))
