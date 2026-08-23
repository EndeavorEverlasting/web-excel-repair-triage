#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "registry/prompts/spec-architecture-prompts.v1.json"
TUTORIAL = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
TEST_SPEC = ROOT / "tests/test_spec_architecture_prompt_registry.py"
TEST_EXPANSION = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"
DRAFT = ROOT / ".prompt-contrib/flow-preference-telemetry-draft.json"
RECEIPT = ROOT / ".prompt-contrib/flow-preference-telemetry-receipt.json"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def add_prompt() -> dict:
    raw = subprocess.check_output(
        [
            "python",
            "scripts/prompt_registry_ops.py",
            "add",
            "--input",
            str(DRAFT),
            "--registry",
            "spec-architecture-prompts",
        ],
        cwd=ROOT,
        text=True,
    )
    receipt = json.loads(raw)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"helper_receipt": receipt}, ensure_ascii=False))
    return receipt


def append_once(value: str, extra: str) -> str:
    if extra in value:
        return value
    return value.rstrip() + " " + extra


def insert_before(content: str, anchor: str, block: str, label: str) -> str:
    if block.strip() in content:
        return content
    count = content.count(anchor)
    if count != 1:
        raise SystemExit(f"{label} anchor mismatch: {count}")
    return content.replace(anchor, block + anchor, 1)


def strengthen_spec_prompts(new_id: str, new_name: str) -> None:
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in payload["prompts"]}

    p82 = by_id["P82"]
    p82["inspectFirst"] = append_once(
        p82["inspectFirst"],
        "When interaction flow is the uncertainty, inspect the exact terminal user goal, current step/keystroke sequence, focus/search/filter/selection state, completion feedback, and any existing semantic usage/preference event owner before prototyping a new UI path.",
    )
    p82["expectedOutput"] = append_once(
        p82["expectedOutput"],
        "For flow-focused iterations, include before/after journey evidence that distinguishes useful terminal actions from redundant intermediate screens and, when personalization is requested, measures semantic completions rather than views or focus events.",
    )
    p82["proofGate"] = append_once(
        p82["proofGate"],
        "When the hypothesis is interaction flow, orthogonal UI state is preserved unless the action explicitly owns it, the candidate reaches the terminal user goal without redundant steps, and any usage metric counts a meaningful completion exactly once rather than treating panel opens or views as intent.",
    )
    p82_block = """3A. WHEN USER FLOW IS THE UNKNOWN — MEASURE THE JOURNEY, NOT THE SCREEN\nWhen the risky assumption is interaction flow, write the actual sequence from entrypoint to terminal user value before changing UI. Track steps/keystrokes, focus changes, search/filter/selection state, intermediate panels, completion feedback, and destructive resets. Do not accept `panel opened` or `detail visible` as success when the user's real goal is to copy, execute, submit, compare, navigate, or otherwise use the object. Prefer the shortest understandable route that preserves safety and discoverability.\n\nTest composed sequences, not only isolated controls. A control that owns visibility must not erase an active query, selection, or unrelated state unless that destructive transition is part of its explicit contract. If the user requests personalization or a most-used surface, measure semantic completion events such as successful copy/execute/export rather than hover, focus, panel-open, or detail-view noise; derive preference views from that canonical event owner instead of hard-coded ordering.\n\n"""
    p82["copyContent"] = insert_before(
        p82["copyContent"],
        "4. PRESERVE THE LAST KNOWN-GOOD STATE",
        p82_block,
        "P82 flow section",
    )

    p94 = by_id["P94"]
    p94["inspectFirst"] = append_once(
        p94["inspectFirst"],
        "For interactive products, inspect multi-step keyboard/pointer sequences and the ownership of search, filters, focus, selection, panel, clipboard, notification, and preference state rather than testing each control in isolation.",
    )
    p94["expectedOutput"] = append_once(
        p94["expectedOutput"],
        "For UI changes, include sequence-level controls proving orthogonal state survives unrelated actions and that a repaired shortcut reaches its intended terminal action without creating a new redundant interaction.",
    )
    p94["proofGate"] = append_once(
        p94["proofGate"],
        "Interactive regressions include realistic action sequences: controls preserve state they do not semantically own, and keyboard/pointer routes that mean the same thing converge on equivalent observable results.",
    )
    p94_block = """3A. PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES\nFor interactive products, a set of individually passing controls can still form a broken journey. Add sequence-level protected controls around state that composes across actions: search query/results, active filters, focus, selection, detail/panel visibility, clipboard/completion feedback, and persisted preferences where relevant. For each action, name the state it semantically owns and the state it must leave untouched.\n\nA visibility toggle should not erase an active search query or its matching result set unless clearing search is an explicit product contract. Likewise, a shortcut that is meant to complete a user action must be tested through that terminal outcome, not merely through an intermediate panel open. Exercise keyboard and pointer routes together when they represent the same semantic action. Keep deliberate clear/reset commands as protected counterexamples so preservation rules do not make state impossible to clear intentionally.\n\n"""
    p94["copyContent"] = insert_before(
        p94["copyContent"],
        "4. BASELINE WHEN IT ADDS SIGNAL",
        p94_block,
        "P94 composed-state section",
    )

    p95 = by_id["P95"]
    p95["inspectFirst"] = append_once(
        p95["inspectFirst"],
        "For user-facing journeys, identify the terminal user value and current interaction count/state transitions so an intermediate screen or focus target is not mistaken for completion.",
    )
    p95["expectedOutput"] = append_once(
        p95["expectedOutput"],
        "User-facing call stacks also identify the terminal value action, redundant intermediate states, and any product-usage telemetry owner needed for explicitly requested personalization.",
    )
    p95["proofGate"] = append_once(
        p95["proofGate"],
        "A representative user journey is not considered successful merely because an intermediate panel rendered: the prototype reaches the stated terminal user value with intentional state transitions and no unexplained redundant step.",
    )
    p95_block = """5A. END THE JOURNEY AT USER VALUE, NOT AN INTERMEDIATE SCREEN\nBefore accepting a user-facing call stack, name the terminal user value and classify each UI state as ENTRYPOINT, REQUIRED INTERMEDIATE, OPTIONAL INSPECTION, or TERMINAL ACTION. Opening a detail panel, focusing a close button, or navigating to an object is not success when the initiating command unambiguously means copy, execute, submit, export, or another deeper action. Prototype the stack through the terminal result and normal completion feedback. Remove redundant intermediate transitions when they add neither safety, comprehension, nor a genuinely separate inspection choice.\n\nWhen the requested product includes preference-driven personalization, distinguish operational logs from product-usage events. Give semantic completion telemetry one owner, count the completed domain action rather than incidental views/focus, define its storage/privacy/reset boundary, and keep dashboards/recommendations as projections of that owner rather than second sources of truth.\n\n"""
    p95["copyContent"] = insert_before(
        p95["copyContent"],
        "6. PROTOTYPE FAILURE CALL STACKS TOO",
        p95_block,
        "P95 terminal-value section",
    )

    new_prompt = by_id[new_id]
    if new_prompt["name"] != new_name:
        raise SystemExit("helper-created prompt identity/name mismatch")

    SPEC.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def route_discovery(new_id: str, new_name: str) -> None:
    payload = json.loads(TUTORIAL.read_text(encoding="utf-8"))
    p65 = next(p for p in payload["prompts"] if p["id"] == "P65")
    p65["useWhen"] = append_once(
        p65["useWhen"],
        "It also covers product-flow friction and preference-telemetry/dashboard work when the user is unsure whether to prototype broadly, repair regressions, redesign seams, or refine the end-to-end journey.",
    )
    p65["expectedOutput"] = append_once(
        p65["expectedOutput"],
        "For product-flow requests, the recommendation distinguishes general prototyping, regression protection, program design, and dedicated flow/telemetry refinement instead of collapsing them into one route.",
    )
    anchor = "- P94 Regression Test & Live Behavior Guard: prove a change preserves impacted previously accepted behavior with automated and live controls.\n"
    additions = (
        "- P82 Prototype-Measure-Refine Delivery Loop: iterate a broadly uncertain feature/interface through measured working candidates when the main question is experimentation rather than a specific flow defect.\n"
        + anchor
        + f"- {new_id} {new_name}: repair technically-working but inefficient user journeys, preserve orthogonal UI state, instrument semantic usage, and derive preference/most-used dashboards when requested.\n"
    )
    if f"- {new_id} {new_name}:" not in p65["copyContent"]:
        if p65["copyContent"].count(anchor) != 1:
            raise SystemExit("P65 P94 route anchor mismatch")
        p65["copyContent"] = p65["copyContent"].replace(anchor, additions, 1)
    TUTORIAL.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_tests(new_id: str, new_name: str) -> None:
    text = TEST_SPEC.read_text(encoding="utf-8")
    anchor = '        self.assertIn("FINAL PROOF IS STRICTER THAN PROTOTYPE PROOF", content)\n'
    additions = (
        anchor
        + '        self.assertIn("WHEN USER FLOW IS THE UNKNOWN", content)\n'
        + '        self.assertIn("terminal user value", content)\n'
        + '        self.assertIn("semantic completion events", content)\n'
        + '        self.assertIn("must not erase an active query", content)\n'
    )
    if 'self.assertIn("WHEN USER FLOW IS THE UNKNOWN", content)' not in text:
        if text.count(anchor) != 1:
            raise SystemExit("P82 test anchor mismatch")
        text = text.replace(anchor, additions, 1)

    marker = "    def test_new_source_prompts_are_intentionally_bounded(self) -> None:\n"
    new_test = f'''    def test_flow_friction_prompt_owns_terminal_actions_and_preference_telemetry(self) -> None:\n        prompt = self.full["{new_id}"]\n        content = prompt["copyContent"]\n        self.assertEqual(prompt["name"], "{new_name}")\n        self.assertEqual(prompt["class"], "PRODUCT / UX FLOW + TELEMETRY")\n        self.assertEqual(prompt["profile"], "spec-architecture")\n        for phrase in (\n            "DEFINE THE TERMINAL USER VALUE",\n            "PRESERVE ORTHOGONAL STATE",\n            "COLLAPSE REDUNDANT INTERMEDIATE STEPS",\n            "UNIFY ENTRYPOINTS ON SEMANTIC ACTIONS",\n            "INSTRUMENT SEMANTIC USAGE, NOT NOISE",\n            "DERIVE THE DASHBOARD FROM EVENTS",\n            "active search -> unrelated filter show/hide/toggle",\n            "favorite shortcut -> terminal action occurs once",\n            "duplicate event dispatch does not double-count one completion",\n        ):\n            self.assertIn(phrase, content)\n        self.assertNotEqual(prompt["id"], "P82")\n        self.assertNotEqual(prompt["id"], "P94")\n        self.assertNotEqual(prompt["id"], "P95")\n        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])\n\n'''
    if f'def test_flow_friction_prompt_owns_terminal_actions_and_preference_telemetry' not in text:
        if text.count(marker) != 1:
            raise SystemExit("new flow prompt test anchor mismatch")
        text = text.replace(marker, new_test + marker, 1)

    old_ids = '        for prompt_id in ("P78", "P79", "P80", "P81", "P82"):\n'
    new_ids = f'        for prompt_id in ("P78", "P79", "P80", "P81", "P82", "{new_id}"):\n'
    if new_ids not in text:
        if text.count(old_ids) != 1:
            raise SystemExit("bounded prompt-id test anchor mismatch")
        text = text.replace(old_ids, new_ids, 1)

    render_anchor = '        self.assertIn("Prototype-Measure-Refine Delivery Loop", html)\n'
    render_new = render_anchor + f'        self.assertIn("{new_name}", html)\n'
    if f'self.assertIn("{new_name}", html)' not in text:
        if text.count(render_anchor) != 1:
            raise SystemExit("render test anchor mismatch")
        text = text.replace(render_anchor, render_new, 1)
    TEST_SPEC.write_text(text, encoding="utf-8")

    text = TEST_EXPANSION.read_text(encoding="utf-8")
    p94_anchor = '            "What behavior could this change break that our selected tests would not notice?",\n'
    p94_new = (
        p94_anchor
        + '            "PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES",\n'
        + '            "visibility toggle should not erase an active search query",\n'
        + '            "shortcut that is meant to complete a user action",\n'
    )
    if '"PROTECT COMPOSED UI STATE AND INTERACTION SEQUENCES"' not in text:
        if text.count(p94_anchor) != 1:
            raise SystemExit("P94 expansion-test anchor mismatch")
        text = text.replace(p94_anchor, p94_new, 1)

    p95_anchor = '            "This prompt may create design artifacts, thin prototypes",\n'
    p95_new = (
        p95_anchor
        + '            "END THE JOURNEY AT USER VALUE, NOT AN INTERMEDIATE SCREEN",\n'
        + '            "OPTIONAL INSPECTION",\n'
        + '            "semantic completion telemetry",\n'
    )
    if '"END THE JOURNEY AT USER VALUE, NOT AN INTERMEDIATE SCREEN"' not in text:
        if text.count(p95_anchor) != 1:
            raise SystemExit("P95 expansion-test anchor mismatch")
        text = text.replace(p95_anchor, p95_new, 1)

    route_anchor = '            "Teach Workspace Protocol Bootstrapper",\n'
    route_new = (
        route_anchor
        + '            "Prototype-Measure-Refine Delivery Loop",\n'
        + f'            "{new_name}",\n'
    )
    if f'            "{new_name}",\n' not in text:
        if text.count(route_anchor) != 1:
            raise SystemExit("P65 expansion route-test anchor mismatch")
        text = text.replace(route_anchor, route_new, 1)
    TEST_EXPANSION.write_text(text, encoding="utf-8")


def main() -> None:
    receipt = add_prompt()
    new_id = receipt["id"]
    new_name = receipt["name"]
    strengthen_spec_prompts(new_id, new_name)
    route_discovery(new_id, new_name)
    strengthen_tests(new_id, new_name)

    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "-m", "unittest", "tests.test_spec_architecture_prompt_registry", "-v")
    run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "-v")
    run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--summary")
    run("python", "scripts/evaluate_prompt_language.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
