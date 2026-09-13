from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run(*args: str) -> None:
    subprocess.run(args, check=True)


registry_path = Path("registry/prompts/spec-architecture-prompts.v1.json")
data = json.loads(registry_path.read_text(encoding="utf-8"))
prompts = {p["id"]: p for p in data["prompts"]}
p141 = prompts["P141"]
p82 = prompts["P82"]

p141_section = """

8A. P82 EXPERIMENT ADMISSION GATE
Route to P82 only after strategic exploration has collapsed to one surviving thesis and the remaining uncertainty is empirical. Before P82 admission, produce a P82 Experiment Admission Record containing: selected thesis; direct repository fact plus an independent corroborating signal; alternatives dispositioned; falsification already performed; primary empirical uncertainty; falsifiable hypothesis; baseline/comparator; prototype boundary; measurement plan; and a predeclared decision rule with PROMOTE / WEAKEN / REJECT / INCONCLUSIVE outcomes.

Fail closed instead of routing to P82 when multiple strategic theses remain viable; the unresolved question is still what should we build; no baseline/comparator or observable metric exists; failure would not change the decision; the prototype would effectively be the full implementation; or the dominant uncertainty is architecture/design rather than empirical behavior. Stay in P141 for unresolved strategic choice, route architecture-dominant uncertainty to P95, and route already-bounded implementation to P07. A P82 experiment is justified only when a bounded observation could still make us decide not to pursue the thesis.

The admission artifact proves the transition. P82 must be able to begin from that record without reopening broad strategic discovery. If the record cannot name one primary empirical uncertainty, one falsifiable hypothesis, one baseline/comparator, one bounded prototype, at least one observable metric, and a decision rule capable of changing the strategic decision, do not graduate from P141 to P82.
""".rstrip()

p141_marker = "\n\n9. PRESERVE THE EXPLORATION / EXECUTION BOUNDARY"
if "P82 EXPERIMENT ADMISSION GATE" not in p141["copyContent"]:
    if p141_marker not in p141["copyContent"]:
        raise SystemExit("P141 insertion marker not found")
    p141["copyContent"] = p141["copyContent"].replace(
        p141_marker, p141_section + p141_marker, 1
    )
if "P82 Experiment Admission Record" not in p141["expectedOutput"]:
    p141["expectedOutput"] += (
        " When P82 is selected, include a P82 Experiment Admission Record proving "
        "one surviving thesis, a primary empirical uncertainty, falsifiable hypothesis, "
        "baseline/comparator, bounded prototype, measurement plan, and predeclared "
        "PROMOTE/WEAKEN/REJECT/INCONCLUSIVE decision rule."
    )
if "P82 admission record" not in p141["nextStep"]:
    p141["nextStep"] += (
        " For P82, launch only after the P82 admission record is complete; otherwise "
        "keep strategic ambiguity in P141, route architecture uncertainty to P95, or "
        "route implementation-ready work to P07."
    )
if "P82 admission" not in p141["proofGate"]:
    p141["proofGate"] += (
        " P82 admission additionally requires one surviving thesis and one bounded "
        "empirical uncertainty whose measured result could change the decision; "
        "unresolved multi-thesis strategy stays in P141, architecture uncertainty routes "
        "to P95, and already-bounded implementation routes to P07."
    )

p82_section = """

P141 -> P82 ADMISSION CONTRACT
Admit a P141 handoff only with one selected thesis when the remaining uncertainty is empirical. Require a P82 Experiment Admission Record: falsifiable hypothesis; baseline/comparator; prototype boundary; measurement; decision rule. Its result must be able to change the decision.

FAIL-CLOSED ROUTING
- multiple strategic theses or unresolved strategy -> P141.
- architecture/design dominant -> P95.
- implementation already bounded -> P07.
- no baseline/comparator, observable metric, bounded slice, or falsifier -> fail admission.
P82 tests one selected empirical hypothesis; it does not generate competing strategic theses.

PROMOTE -> P95 if design remains unresolved, otherwise P07. WEAKEN / REJECT -> P141. INCONCLUSIVE -> retry only if the same thesis and experiment remain repairable; otherwise P141.
""".rstrip()

p82_marker = "\n\n1. LOCK THE OUTCOME BEFORE ITERATING"
if "P141 -> P82 ADMISSION CONTRACT" not in p82["copyContent"]:
    if p82_marker not in p82["copyContent"]:
        raise SystemExit("P82 insertion marker not found")
    p82["copyContent"] = p82["copyContent"].replace(
        p82_marker, p82_section + p82_marker, 1
    )

old_3a = """3A. WHEN USER FLOW IS THE UNKNOWN — MEASURE THE JOURNEY, NOT THE SCREEN
When the risky assumption is interaction flow, write the actual sequence from entrypoint to terminal user value before changing UI. Track steps/keystrokes, focus changes, search/filter/selection state, intermediate panels, completion feedback, and destructive resets. Do not accept `panel opened` or `detail visible` as success when the user's real goal is to copy, execute, submit, compare, navigate, or otherwise use the object. Prefer the shortest understandable route that preserves safety and discoverability.

Test composed sequences, not only isolated controls. A control that owns visibility must not erase an active query, selection, or unrelated state unless that destructive transition is part of its explicit contract. If the user requests personalization or a most-used surface, measure semantic completion events such as successful copy/execute/export rather than hover, focus, panel-open, or detail-view noise; derive preference views from that canonical event owner instead of hard-coded ordering."""
new_3a = """3A. WHEN USER FLOW IS THE UNKNOWN — MEASURE THE JOURNEY, NOT THE SCREEN
Trace entrypoint -> terminal user value before UI changes. Measure steps/keystrokes, focus/search/filter/selection, feedback, and resets. A visibility control must not erase an active query or unrelated state unless it owns that transition. For personalization, count semantic completion events such as successful copy/execute/export, not view/focus noise; derive preferences from that event owner."""
old_4 = """4. PRESERVE THE LAST KNOWN-GOOD STATE
Iteration must not destroy evidence. Use branch/worktree isolation, commits, versioned artifacts, fixtures, screenshots, manifests, hashes, or repository-native checkpoints as appropriate. Preserve the last known-good candidate before a risky redesign. Never use destructive cleanup merely to make a prototype floor look clean. Make it possible to compare or roll back candidates."""
new_4 = """4. PRESERVE THE LAST KNOWN-GOOD STATE
Preserve the last known-good candidate before risky redesign with repository-native checkpoints. Keep evidence comparable and rollback possible; never destructively clean merely to make a prototype floor look clean."""
old_5 = """5. COMPARE ALTERNATIVES FAIRLY
When two approaches are genuinely plausible and the choice matters, build bounded competing prototypes rather than arguing abstractly. Run both through the SAME acceptance rubric and representative data/workload. Compare correctness first, then user experience, complexity, maintainability, performance, cost, security, and reversibility as relevant. Do not keep multiple production paths after the evidence selects one unless redundancy itself is a requirement."""
new_5 = """5. COMPARE ALTERNATIVES FAIRLY
Test plausible candidates with the SAME acceptance rubric and representative data/workload. Compare correctness first, then relevant UX, complexity, maintainability, performance, cost, security, and reversibility. Retire redundant paths after evidence selects one unless redundancy is required."""
for old, new, label in (
    (old_3a, new_3a, "P82 user-flow section"),
    (old_4, new_4, "P82 preservation section"),
    (old_5, new_5, "P82 comparison section"),
):
    if old not in p82["copyContent"]:
        raise SystemExit(f"{label} compression marker not found")
    p82["copyContent"] = p82["copyContent"].replace(old, new, 1)

if "P82 Experiment Admission Record" not in p82["inspectFirst"]:
    p82["inspectFirst"] += (
        " For a P141 strategic handoff, inspect the P82 Experiment Admission Record first "
        "and fail closed if it does not prove one selected thesis, a bounded empirical "
        "uncertainty, baseline/comparator, measurable falsifier, and decision rule."
    )
if "admission contract" not in p82["expectedOutput"]:
    p82["expectedOutput"] += (
        " For P141 handoffs, preserve the admission contract and finish with PROMOTE, "
        "WEAKEN, REJECT, or INCONCLUSIVE plus the resulting P95/P07/P141 route."
    )
if "P141 handoff" not in p82["proofGate"]:
    p82["proofGate"] += (
        " A P141 handoff is admissible only when broad strategic choice is already "
        "resolved and one bounded empirical result can still promote, weaken, reject, or "
        "leave the thesis inconclusive; architecture-dominant work routes to P95 and "
        "implementation-ready work routes to P07."
    )

registry_path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)

test_path = Path("tests/test_spec_architecture_prompt_registry.py")
text = test_path.read_text(encoding="utf-8")
method_name = "test_p141_to_p82_seam_routes_only_bounded_empirical_uncertainty"
if method_name not in text:
    marker = (
        "    def test_flow_friction_prompt_owns_terminal_actions_and_preference_telemetry"
        "(self) -> None:\n"
    )
    if marker not in text:
        raise SystemExit("Cross-owner test insertion marker not found")
    test = '''    def test_p141_to_p82_seam_routes_only_bounded_empirical_uncertainty(self) -> None:
        p141 = self.full["P141"]["copyContent"]
        p82 = self.full["P82"]["copyContent"]

        sender_fixture = {
            "admission_artifact": "P82 Experiment Admission Record",
            "selected_thesis": "one surviving thesis",
            "empirical_uncertainty": "primary empirical uncertainty",
            "hypothesis": "falsifiable hypothesis",
            "baseline": "baseline/comparator",
            "prototype": "prototype boundary",
            "measurement": "measurement",
        }
        receiver_fixture = {
            "admission_artifact": "P82 Experiment Admission Record",
            "hypothesis": "falsifiable hypothesis",
            "baseline": "baseline/comparator",
            "prototype": "prototype boundary",
            "measurement": "measurement",
            "decision_rule": "decision rule",
        }

        for field, phrase in sender_fixture.items():
            self.assertIn(
                phrase,
                p141,
                f"P141->P82 sender contract missing {field}: expected {phrase!r}.",
            )
        for field, phrase in receiver_fixture.items():
            self.assertIn(
                phrase,
                p82,
                f"P141->P82 receiver contract missing {field}: expected {phrase!r}.",
            )

        self.assertIn(
            "remaining uncertainty is empirical",
            p141,
            "P141 must admit P82 only when the remaining uncertainty is empirical.",
        )
        self.assertIn(
            "multiple strategic theses",
            p141.lower(),
            "P141 must retain routing when multiple strategic theses remain viable.",
        )
        self.assertIn(
            "P95",
            p141,
            "P141 must route dominant architecture uncertainty to P95.",
        )
        self.assertIn(
            "P95",
            p82,
            "P82 must reject architecture-dominant work toward P95.",
        )
        self.assertIn(
            "P07",
            p141,
            "P141 must route implementation-ready work to P07 instead of P82.",
        )

        for forbidden in (
            "generate 3-5 competing strategic theses",
            "decide what the repository should build next",
        ):
            self.assertNotIn(
                forbidden,
                p82.lower(),
                f"P141->P82 seam collapsed: P82 absorbed P141 behavior {forbidden!r}.",
            )

        for outcome in ("PROMOTE", "WEAKEN", "REJECT", "INCONCLUSIVE"):
            self.assertIn(
                outcome,
                p82,
                f"P82 decision contract missing experiment outcome {outcome}.",
            )
        self.assertIn(
            "P141",
            p82,
            "P82 must return strategically weakened/rejected evidence to P141.",
        )

'''
    text = text.replace(marker, test + marker, 1)
    test_path.write_text(text, encoding="utf-8")

run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
run("python", "-m", "unittest", "tests.test_ux_design_prompt_suite", "-v")
run("python", "scripts/prompt_registry_ops.py", "validate")
run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
run("python", "scripts/evaluate_prompt_language.py", "--summary")
run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
run("git", "diff", "--check")

run("git", "config", "user.name", "github-actions[bot]")
run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
Path(".github/workflows/_temp_p141_p82_seam.yml").unlink()
Path("scripts/_temp_p141_p82_seam.py").unlink()
run(
    "git",
    "add",
    "registry/prompts/spec-architecture-prompts.v1.json",
    "tests/test_spec_architecture_prompt_registry.py",
    "web/prompt-kit/index.html",
    ".github/workflows/_temp_p141_p82_seam.yml",
    "scripts/_temp_p141_p82_seam.py",
)
run("git", "commit", "-m", "feat(prompt-kit): gate P141 to P82 experiments")
run("git", "push", "origin", "HEAD:feat/p141-p82-experiment-admission-20260912")
