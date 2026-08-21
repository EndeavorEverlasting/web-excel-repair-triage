from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


for draft in (
    ".github/prompt91-draft.json",
    ".github/prompt92-draft.json",
    ".github/prompt93-draft.json",
):
    run("python", "scripts/prompt_registry_ops.py", "add", "--input", draft, "--registry", "spec-architecture-prompts")

# Effective P02 owns the live website behavior.
overrides = ROOT / "registry/prompts/prompt-overrides.v1.json"
payload = json.loads(overrides.read_text(encoding="utf-8"))
p02 = next(item for item in payload["overrides"] if item["id"] == "P02")
p02["expectedOutput"] = (
    "Actual progress on the first safe unresolved sprint, with compact in-flight evidence updates during multi-pass work; "
    "tracked changes or exact completion proof; validation, commit/push/PR state, proof ceiling, fixed-point reason, and next executable action."
)
p02["nextStep"] = (
    "Keep executing. During multi-pass work, emit a terse evidence update after each meaningful pass or roughly 2-3 tool groups; "
    "then continue until the owned gate, bounded fixed point, or exact external blocker."
)
p02["proofGate"] = (
    "The named chat is resolved; stale context is reconciled; actual repo/artifact movement plus validation or an exact blocker exists; "
    "multi-pass work reports at least one concise in-flight evidence update before the final response; and the final report states pass count plus fixed-point reason or blocker."
)
anchor = (
    "MISSION\nTake the unfinished principles and work from the previous chat and sprint upon them now. "
    "A short execution plan is allowed, but planning is subordinate to implementation. Preserve only context that prevents rework.\n\n"
)
progress = (
    "0. CONCISE PROGRESS LOOP\n"
    "- Do not work through multiple meaningful passes silently.\n"
    "- After each evidence-changing pass, or roughly every 2-3 tool groups during long execution, emit one compact update and continue.\n"
    "- Preferred shape: `CHANGED: ... | PROVED: ... | NEXT: ...`; use `BLOCKED: ...` only for a real blocker.\n"
    "- Prefer fragments over filler. Maximum two short sentences. Grammar polish is less important than signal.\n"
    "- Do not repeat the plan, narrate polling, or use an update as a stopping point while safe work remains.\n"
    "- Before the final response, state pass count and fixed-point reason, or the exact blocker.\n"
    "- One trivial pass needs no mid-run update. Multi-pass silent execution fails this prompt.\n\n"
)
if "0. CONCISE PROGRESS LOOP" not in p02["copyContent"]:
    if anchor not in p02["copyContent"]:
        raise SystemExit("P02 mission anchor missing")
    p02["copyContent"] = p02["copyContent"].replace(anchor, anchor + progress, 1)
overrides.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

spec = ROOT / "tests/test_spec_architecture_prompt_registry.py"
text = spec.read_text(encoding="utf-8")
marker = "    def test_failure_suite_prompts_cover_class_path_and_closure_without_collapsing_roles(self) -> None:"
if marker not in text:
    insert = r'''
    def test_failure_suite_prompts_cover_class_path_and_closure_without_collapsing_roles(self) -> None:
        expected = {
            "P91": ("Failure-Class Generalization & Repository Audit", "TESTING / FAILURE GENERALIZATION"),
            "P92": ("Production-Path Proof Gap Auditor", "TESTING / PRODUCTION PATH"),
            "P93": ("Use-Case Closure Certification", "VERIFICATION / USE-CASE CLOSURE"),
        }
        for prompt_id, (name, prompt_class) in expected.items():
            prompt = self.full[prompt_id]
            self.assertEqual(prompt["id"], prompt_id)
            self.assertEqual(prompt["seq"], prompt_id[1:])
            self.assertEqual(prompt["copySheet"], f"{prompt_id}_COPY_SAFE")
            self.assertEqual(prompt["category"], "standard")
            self.assertEqual(prompt["profile"], "spec-architecture")
            self.assertEqual(prompt["color"], "Cyan")
            self.assertEqual(prompt["name"], name)
            self.assertEqual(prompt["class"], prompt_class)
            self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
            self.assertIn(self.policy["marker"], prompt["copyContent"])

        p91 = self.full["P91"]["copyContent"]
        self.assertIn("BUILD A FAILURE-STATE MATRIX", p91)
        self.assertIn("UNKNOWN is not PASS", p91)
        self.assertIn("Do not blanket-replace", p91)
        self.assertIn("What adjacent state could still fail for the same underlying reason?", p91)

        p92 = self.full["P92"]["copyContent"]
        self.assertIn("MAP BOTH PATHS", p92)
        self.assertIn("PRODUCTION-ONLY", p92)
        self.assertIn("Green helper tests do not prove a production wrapper", p92)
        self.assertIn("same-entrypoint synthetic proof", p92)

        p93 = self.full["P93"]["copyContent"]
        self.assertIn("BUILD THE OBLIGATION LEDGER", p93)
        self.assertIn("UNKNOWN is not PASS", p93)
        self.assertIn("FALSIFY CLOSURE", p93)
        self.assertIn("NOT CERTIFIED", p93)

        html = build_prompt_kit_registry.render()
        for _, (name, _) in expected.items():
            self.assertIn(name, html)
'''
    end = '\n\nif __name__ == "__main__":'
    if end not in text:
        raise SystemExit("spec test insertion anchor missing")
    spec.write_text(text.replace(end, "\n" + insert.rstrip() + end, 1), encoding="utf-8")

p02test = ROOT / "tests/test_p02_p07_autonomous_iteration.py"
ptext = p02test.read_text(encoding="utf-8")
pmarker = "    def test_effective_p02_requires_concise_inflight_progress_without_status_stops(self) -> None:"
if pmarker not in ptext:
    insert = r'''
    def test_effective_p02_requires_concise_inflight_progress_without_status_stops(self) -> None:
        prompt = self.effective["P02"]
        content = prompt["copyContent"]
        self.assertIn("0. CONCISE PROGRESS LOOP", content)
        self.assertIn("Do not work through multiple meaningful passes silently", content)
        self.assertIn("CHANGED: ... | PROVED: ... | NEXT: ...", content)
        self.assertIn("Prefer fragments over filler", content)
        self.assertIn("Maximum two short sentences", content)
        self.assertIn("Do not repeat the plan, narrate polling, or use an update as a stopping point", content)
        self.assertIn("pass count and fixed-point reason", content)
        self.assertIn("Multi-pass silent execution fails this prompt", content)
        self.assertIn("compact in-flight evidence updates", prompt["expectedOutput"])
'''
    target = "    def test_p07_preserves_fixed_point_and_adds_user_only_gate(self) -> None:"
    if target not in ptext:
        raise SystemExit("P02 test insertion anchor missing")
    p02test.write_text(ptext.replace(target, insert + "\n" + target, 1), encoding="utf-8")

# P02 override changed after the helper builds; rebuild exact website parity now.
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "tests.test_p02_p07_autonomous_iteration", "-v")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "tests.test_prompt_kit_guidance", "-v")
run("python", "scripts/validate_prompt_kit_order_navigation.py", "--output", "/tmp/failure-suite-order.json", "--summary")
run("python", "-m", "unittest", "tests.test_prompt_kit_order_navigation_contract", "-v")
run("python", "-m", "unittest", "tests.test_prompt_language_audit", "-v")
run("python", "scripts/evaluate_prompt_language.py", "--output", "/tmp/failure-suite-language.json", "--summary")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("git", "diff", "--check")
