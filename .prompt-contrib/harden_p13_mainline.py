from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "registry/prompts/prompt-overrides.v1.json"
TESTS = ROOT / "tests/test_prompt_kit_mainline_delivery.py"

payload = json.loads(OVERRIDES.read_text(encoding="utf-8"))
p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
identity_before = {key: p13.get(key) for key in ("id", "seq", "name", "type", "class", "color", "copySheet", "category")}
copy_before = p13["copyContent"]
size_before = len(copy_before)

p13["sprintRole"] = (
    "Turn recurring pain, urgency misses, proof-floor loops, and missing parallelism into immediate critical-path progress, "
    "durable prevention, and verified mainline convergence through a bounded fixed point"
)
p13["expectedOutput"] = (
    "Immediate advancement of the current critical path, an explicit Sub-Part Agent launch/packet or serialized-dependency reason, "
    "the smallest implemented durable prevention, and the exact validated owned change integrated into the current default branch "
    "and verified there; otherwise an exact integration/user-only blocker plus the action that advances it."
)
p13["nextStep"] = (
    "Repeat REFRESH -> SELECT NEXT GATE -> EXECUTE -> PREVENT -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE; "
    "integrate each independently green owned slice when authorized, then continue until a bounded fixed point or exact external/user-only blocker. "
    "An open PR, green CI, or one merged slice is not a stopping point while safe owned work remains."
)
p13["proofGate"] = (
    "The recurrence is evidence-backed; current proof floor and next gate are explicit; critical-path work advances until a bounded fixed point or exact blocker; "
    "Sub-Part Agent analysis is present; one correct authority owns the prevention; focused regression/build/parity validation passes; a deliberate second pass "
    "finds no practical in-scope improvement; and the exact validated owned head is integrated into and verified on the current default branch when authorized. "
    "A branch or PR alone is insufficient completion; when integration is blocked, the exact gate and advancing action are proven without proof inflation."
)

old_isolation = (
    "Preserve dirty or separately owned work through an isolated branch/worktree. A repeated-urgency signal accelerates the critical path; "
    "it never bypasses repository safety or authority."
)
new_isolation = (
    "Do not create a feature branch merely because P13 fired. Reuse the current safe owner when possible; isolate only for repository policy/protection, "
    "dirty or separately owned work, review requirements, or collision safety. When isolation is required, preserve dirty or separately owned work through "
    "an isolated branch/worktree. A repeated-urgency signal accelerates the critical path; it never bypasses repository safety or authority."
)
if old_isolation not in p13["copyContent"]:
    raise SystemExit("P13 sprint-declaration isolation sentence moved; refusing stale patch")
p13["copyContent"] = p13["copyContent"].replace(old_isolation, new_isolation, 1)

marker = "9. P13 CONTINUOUS MAINLINE CONVERGENCE"
if marker not in p13["copyContent"]:
    block = """

9. P13 CONTINUOUS MAINLINE CONVERGENCE
Run the recurrence-repair sprint as a continuing gate loop, not a one-shot repair:
`REFRESH -> SELECT NEXT GATE -> EXECUTE -> PREVENT -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE`.
- A pass counts as progress only when it changes owned state, closes a real gap, produces decision-relevant evidence, integrates a validated slice, or proves an exact blocker. Planning, status repetition, CI polling, and re-reporting an established proof floor do not count.
- After the first green result, perform one deliberate second pass over the recurrence, nearby failure surface, current critical path, diff, and remaining acceptance gates. Repair any practical in-scope miss and rerun affected proof.
- A branch, worktree, commit, push, open PR, review-ready state, or green CI is intermediate evidence. When the exact validated owned head is mergeable, required gates are green, dependencies/reviews/conflicts/protection are clear, merge authority exists, and the operator has not prohibited integration, merge the exact validated owned head into the current default branch in the same run.
- After merge, refresh remote/default-branch truth and verify that the intended change is present there with the owning semantic/build/parity proof. If another independent bounded green slice remains, continue from refreshed main instead of stranding it behind the completed slice.
- Do not stop merely because one bounded slice merged. Stop only at a bounded fixed point: current critical-path work is advanced as far as authorized; the durable prevention and regression are proven; authorized integration is complete and verified; the deliberate second pass finds no practical in-scope improvement; and no safe executable continuation remains. Otherwise continue, or prove the exact external/user-only gate and the action that advances it.
"""
    if "\nFINAL RESPONSE\n" not in p13["copyContent"]:
        raise SystemExit("P13 FINAL RESPONSE anchor moved; refusing stale patch")
    p13["copyContent"] = p13["copyContent"].replace("\nFINAL RESPONSE\n", block + "\nFINAL RESPONSE\n", 1)

final_anchor = "- push / PR / merge state:\n- proof achieved / proof ceiling:"
final_replacement = (
    "- push / PR / merge state:\n"
    "- integration target + pre/post default-branch SHA:\n"
    "- fixed-point reason or exact blocker + advancing action:\n"
    "- proof achieved / proof ceiling:"
)
if final_anchor not in p13["copyContent"]:
    raise SystemExit("P13 delivery-report anchor moved; refusing stale patch")
p13["copyContent"] = p13["copyContent"].replace(final_anchor, final_replacement, 1)

identity_after = {key: p13.get(key) for key in identity_before}
if identity_after != identity_before:
    raise SystemExit(f"P13 identity drifted: before={identity_before} after={identity_after}")

size_after = len(p13["copyContent"])
delta = size_after - size_before
print(f"P13_COPY_SIZE_BEFORE={size_before}")
print(f"P13_COPY_SIZE_AFTER={size_after}")
print(f"P13_COPY_SIZE_DELTA={delta}")
if delta > 3200:
    raise SystemExit(f"P13 hardening grew raw copyContent by {delta} chars; anti-bloat ceiling is 3200")

OVERRIDES.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

test_text = TESTS.read_text(encoding="utf-8")
method_marker = "    def test_p13_requires_continuous_mainline_convergence(self):"
if method_marker not in test_text:
    insertion = '''    def test_p13_requires_continuous_mainline_convergence(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"]
        self.assertIn("recurring pain", p13["sprintRole"])
        self.assertIn("current default branch", p13["expectedOutput"])
        self.assertIn("bounded fixed point", p13["nextStep"])
        self.assertIn("branch or PR alone is insufficient", p13["proofGate"])
        for phrase in (
            "P13 CONTINUOUS MAINLINE CONVERGENCE",
            "REFRESH -> SELECT NEXT GATE -> EXECUTE -> PREVENT -> VALIDATE -> CRITIQUE -> INTEGRATE -> REFRESH -> CONTINUE",
            "Do not create a feature branch merely because P13 fired",
            "branch, worktree, commit, push, open PR, review-ready state, or green CI",
            "merge the exact validated owned head into the current default branch",
            "verify that the intended change is present there",
            "deliberate second pass",
            "Do not stop merely because one bounded slice merged",
            "bounded fixed point",
        ):
            self.assertIn(phrase, copy)
        self.assertLess(len(copy), 18000)

    def test_p13_does_not_absorb_hallucination_diagnostic_role(self):
        payload = load_json("registry/prompts/prompt-overrides.v1.json")
        p13 = next(item for item in payload["overrides"] if item["id"] == "P13")
        copy = p13["copyContent"].lower()
        self.assertIn("recover the repeated failure from evidence", copy)
        self.assertNotIn("factuality hallucination", copy)
        self.assertNotIn("faithfulness hallucination", copy)
        self.assertNotIn("dumb zone", copy)

'''
    needle = "    def test_p65_can_route_repeated_friction_without_browser_finder(self):\n"
    if needle not in test_text:
        raise SystemExit("Focused P13 test insertion anchor moved; refusing stale patch")
    test_text = test_text.replace(needle, insertion + needle, 1)
    TESTS.write_text(test_text, encoding="utf-8")
