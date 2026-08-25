from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "tutorial-discovery-prompts.v1.json"
TESTS = ROOT / "tests" / "test_prompt_kit_discovery.py"
GENERATED = ROOT / "web" / "prompt-kit" / "index.html"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def patch_p65() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    matches = [p for p in payload["prompts"] if p.get("id") == "P65"]
    if len(matches) != 1:
        raise SystemExit(f"expected one canonical P65, found {len(matches)}")
    p65 = matches[0]
    if p65.get("name") != "Guided Prompt Finder Questionnaire":
        raise SystemExit(f"unexpected P65 identity: {p65.get('name')!r}")

    p65["sprintRole"] = (
        "Run an adaptive, bounded decision-tree interview that granularly resolves the user need and desired prompt behavior, "
        "then recommend the smallest useful Prompt Kit route"
    )

    use_add = (
        " It also applies when the initial request is underspecified and the user wants the finder to probe granularly rather "
        "than force the request through a fixed questionnaire."
    )
    if "probe granularly rather than force the request through a fixed questionnaire" not in p65["useWhen"]:
        p65["useWhen"] = p65["useWhen"].rstrip() + use_add

    inspect_add = (
        " Recover facts already available from the conversation, repository, runtime, tools, or current Prompt Kit before "
        "asking the user; reserve questions for user-owned decisions and unresolved routing distinctions."
    )
    if "reserve questions for user-owned decisions and unresolved routing distinctions" not in p65["inspectFirst"]:
        p65["inspectFirst"] = p65["inspectFirst"].rstrip() + inspect_add

    output_add = (
        " The recommendation is preceded by a compact resolved-need model that distinguishes the user outcome from the desired "
        "prompt behavior and identifies any remaining ambiguity that materially changes the route."
    )
    if "compact resolved-need model" not in p65["expectedOutput"]:
        p65["expectedOutput"] = p65["expectedOutput"].rstrip() + output_add

    p65["proofGate"] = (
        "The interview asks one decision-shaping question at a time, reuses recoverable context instead of making the user repeat "
        "facts, gives a provisional/recommended answer for each question, and recomputes only the unresolved routing frontier after "
        "each response. It normally resolves in 2-4 questions and may continue up to six only while materially different primary "
        "routes remain plausible. Recommendations use current prompt IDs and names, distinguish user outcome from desired prompt "
        "behavior, remain minimal and dependency-aware, and assume no deployment or runtime proof from questionnaire answers."
    )

    content = p65["copyContent"]
    old_intro = (
        "Use the AI Harness Prompt Kit prompt IDs and names below as the recommendation vocabulary. Ask one concise question at a time, "
        "wait for my answer, and ask no more than four questions. Do not assume that I have a repository checkout, a known task, a clean "
        "branch, a working runtime, or permission to deploy."
    )
    new_intro = (
        "Use the AI Harness Prompt Kit prompt IDs and names below as the recommendation vocabulary. Run an adaptive, granular routing "
        "interview: ask one concise question at a time, wait for my answer, and choose the next question from the unresolved decision "
        "tree instead of marching through a fixed script. Do not assume that I have a repository checkout, a known task, a clean branch, "
        "a working runtime, or permission to deploy."
    )
    if new_intro not in content:
        if old_intro not in content:
            raise SystemExit("P65 intro anchor missing")
        content = content.replace(old_intro, new_intro, 1)

    old_dims = """QUESTIONNAIRE DIMENSIONS
1. Starting state: no checkout, unfamiliar repository, known repository, active failure, open PR floor, or app currently in front of me.
2. Desired outcome: recover repeated friction or urgency, understand, plan, coordinate or maintain a repository work ledger, build or repair, diagnose, validate, integrate or deploy, document or teach, or close out and hand off.
3. Work shape: one bounded task, several parallel lanes, strict sequential lanes, tutorial portfolio, artifact creation, or immediate coaching.
4. Proof need: static validation, generated artifact, live runtime observation, production or field acceptance, or not yet known.
"""
    new_dims = """ADAPTIVE ROUTING INTERVIEW
Build a small routing decision tree from the user's actual request. A branch exists only when its answer can materially change the primary prompt or the dependency order. Resolve prerequisites before dependent questions, and after every answer recompute the unresolved frontier.

QUESTION POOL — ASK ONLY UNRESOLVED BRANCHES
1. Starting state: no checkout, unfamiliar repository, known repository, active failure, inherited/claimed work, open PR floor, or app currently in front of me.
2. User outcome: what useful state should exist when the work is done — understand, decide, plan, build/repair, diagnose, verify/review, coordinate, teach, create an artifact, deploy, integrate, or hand off.
3. Desired prompt behavior: should the agent execute now, investigate first, design/plan, critique or verify existing work, coach interactively, teach over time, create a reusable artifact, or orchestrate multiple lanes.
4. Work shape: one bounded task, several parallel lanes, strict sequential lanes, tutorial portfolio, artifact creation, immediate coaching, or an uncertain idea that needs refinement before execution.
5. Evidence and proof need: static validation, generated artifact, live runtime observation, production/field acceptance, external research, or not yet known.
6. Constraints and authority: repository/runtime access, permissions, destructive-risk tolerance, required human decisions, deadlines, or explicit forbidden scope.

GRANULAR GRILLING DISCIPLINE
- Ask one decision-shaping question at a time. Do not dump the whole pool or a batch of generic questions on the user.
- If a fact can be recovered from the current conversation, repository, runtime, Prompt Kit registry, or tools, recover it yourself rather than asking the user to act as a context courier.
- Facts are agent-owned; decisions are user-owned. Never silently decide a genuine preference, authority boundary, risk tolerance, or desired outcome on the user's behalf.
- For each question, state your current read and recommended answer in one short sentence so the user can react to a concrete proposal instead of a blank prompt.
- After each answer, recompute the unresolved frontier. A question whose answer depends on an unresolved prerequisite waits; questions made irrelevant by the answer disappear.
- Do not ask a question merely because it appears in the pool. If earlier context already resolves a branch, mark it resolved internally and spend the next question on the highest-information remaining distinction.
- Default to 2-4 questions. You may continue up to six only when materially different primary routes are still plausible; stop early as soon as one primary route and any necessary follow-ons are decision-complete.
- Granularity is for route accuracy, not interrogation theater. Do not keep questioning once additional answers would not change the recommended Prompt Kit path.
"""
    if "ADAPTIVE ROUTING INTERVIEW" not in content:
        if old_dims not in content:
            raise SystemExit("P65 questionnaire-dimensions anchor missing")
        content = content.replace(old_dims, new_dims, 1)

    gate = """ROUTE CONFIDENCE GATE
Before recommending, state the resolved need model in one compact line: `starting state | user outcome | desired prompt behavior | work shape | proof need | material constraints`. If a missing user-owned decision could change the primary prompt, ask it before routing. If remaining uncertainty would change only a follow-on detail, recommend the primary prompt now and name that uncertainty instead of prolonging the interview.
"""
    if "ROUTE CONFIDENCE GATE" not in content:
        anchor = "\n\nPRIMARY ROUTING MAP"
        if anchor not in content:
            raise SystemExit("P65 primary-routing-map anchor missing")
        content = content.replace(anchor, "\n\n" + gate.rstrip() + anchor, 1)

    p65["copyContent"] = content
    keywords = p65.setdefault("keywords", [])
    for keyword in (
        "grill me",
        "granular prompt finder",
        "adaptive questionnaire",
        "decision tree interview",
        "prompt intent assessment",
        "desired prompt behavior",
    ):
        if keyword not in keywords:
            keywords.append(keyword)

    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_test() -> None:
    tests = TESTS.read_text(encoding="utf-8")
    test_name = "test_guided_finder_granularly_resolves_need_and_prompt_behavior"
    if test_name in tests:
        return
    anchor = "    def test_repo_front_door_exposes_browser_phone_zip_cmd_and_clone(self) -> None:\n"
    if anchor not in tests:
        raise SystemExit("focused discovery test insertion anchor missing")
    block = '''    def test_guided_finder_granularly_resolves_need_and_prompt_behavior(self) -> None:\n        payload = json.loads(TUTORIAL_PROMPTS.read_text(encoding="utf-8"))\n        p65 = next(item for item in payload["prompts"] if item["id"] == "P65")\n        content = p65["copyContent"]\n        for marker in (\n            "ADAPTIVE ROUTING INTERVIEW",\n            "QUESTION POOL — ASK ONLY UNRESOLVED BRANCHES",\n            "User outcome:",\n            "Desired prompt behavior:",\n            "GRANULAR GRILLING DISCIPLINE",\n            "If a fact can be recovered from the current conversation, repository, runtime, Prompt Kit registry, or tools",\n            "Facts are agent-owned; decisions are user-owned",\n            "state your current read and recommended answer",\n            "recompute the unresolved frontier",\n            "Do not ask a question merely because it appears in the pool",\n            "Default to 2-4 questions",\n            "continue up to six only when materially different primary routes are still plausible",\n            "ROUTE CONFIDENCE GATE",\n            "starting state | user outcome | desired prompt behavior | work shape | proof need | material constraints",\n        ):\n            self.assertIn(marker, content)\n        self.assertNotIn("ask no more than four questions", content.lower())\n        self.assertIn("adaptive", p65["sprintRole"].lower())\n        self.assertIn("probe granularly", p65["useWhen"].lower())\n        self.assertIn("2-4 questions", p65["proofGate"])\n        self.assertIn("up to six", p65["proofGate"])\n        self.assertIn("desired prompt behavior", p65["proofGate"].lower())\n        self.assertIn("grill me", p65["keywords"])\n\n'''
    TESTS.write_text(tests.replace(anchor, block + anchor, 1), encoding="utf-8")


def falsify() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in payload["prompts"]}
    p65 = by_id["P65"]
    p96 = by_id["P96"]
    html = GENERATED.read_text(encoding="utf-8")
    checks = {
        "P65 identity preserved": p65["name"] == "Guided Prompt Finder Questionnaire",
        "adaptive routing": "ADAPTIVE ROUTING INTERVIEW" in p65["copyContent"],
        "granular need and prompt behavior": "User outcome:" in p65["copyContent"] and "Desired prompt behavior:" in p65["copyContent"],
        "facts vs decisions": "Facts are agent-owned; decisions are user-owned" in p65["copyContent"],
        "recommended answer": "state your current read and recommended answer" in p65["copyContent"],
        "adaptive frontier": "recompute the unresolved frontier" in p65["copyContent"],
        "bounded finder role": "Default to 2-4 questions" in p65["copyContent"] and "up to six only" in p65["copyContent"],
        "route confidence": "ROUTE CONFIDENCE GATE" in p65["copyContent"],
        "P96 remains teaching owner": p96["name"] == "Stateful Socratic Technical Tutor Workspace",
        "generated site parity marker": "GRANULAR GRILLING DISCIPLINE" in html,
    }
    failed = [label for label, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"P65 granular finder falsification failed: {failed}")
    print("P65 granular finder falsification: PASS", flush=True)


def main() -> None:
    patch_p65()
    patch_test()
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run(
        "python", "-m", "unittest",
        "tests.test_prompt_kit_discovery.PromptKitDiscoveryTests.test_guided_finder_granularly_resolves_need_and_prompt_behavior",
        "-v",
    )
    run("python", "-m", "unittest", "tests.test_prompt_kit_discovery", "-v")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/validate_prompt_kit_order_navigation.py", "--require-implementation", "--summary")
    run("python", "scripts/evaluate_prompt_language.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")
    falsify()


if __name__ == "__main__":
    main()
