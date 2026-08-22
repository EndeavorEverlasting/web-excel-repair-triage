#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry/prompts/tutorial-discovery-prompts.v1.json"
FOCUSED = ROOT / "tests/test_prompt_registry_expansion_regression_design_teach.py"
DISCOVERY = ROOT / "tests/test_prompt_kit_discovery.py"


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def strengthen_p96() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p = next(x for x in payload["prompts"] if x["name"] == "Stateful Socratic Technical Tutor Workspace")
    p["useWhen"] = "The user invokes `/teach <topic>`, `/teach recap`, or otherwise wants to genuinely learn a technical system, architecture, algorithm, repository, tool, or workflow through an already-established persistent teaching workspace rather than receive a passive guide or black-box implementation."
    p["inspectFirst"] = "The learner's mastery goal and current conversation; `.teach/MISSION.md`, `.teach/RESOURCES.md`, all relevant `.teach/learning-records/`, existing lessons/assets, and current repository/topic evidence. If the canonical `.teach/` core is absent, route setup to Teach Workspace Protocol Bootstrapper before beginning the lesson instead of cloning or installing a teaching package."
    p["expectedOutput"] = "A stateful `/teach` session that updates the current mission, creates or reuses one atomic lesson, ends with exactly one conceptual trade-off/mechanism question plus one code diagnostic or edge-case exercise, waits for the learner response, and writes a dated learning record only after demonstrated mastery; `/teach recap` instead rebuilds working memory from verified records with a brief refresher quiz."
    p["nextStep"] = "For `/teach <topic>`, recover the mission/resources and prior records, teach one atomic frontier concept, then stop at the two-question checkpoint until the learner responds. For `/teach recap`, read verified records first, run a roughly two-minute refresher, and resume only at the first decayed or unmastered concept."
    p["proofGate"] = "The `.teach/` workspace is repository-local protocol state rather than an external package; factual teaching is grounded in RESOURCES.md/repository truth; `/teach <topic>` updates MISSION.md and creates/reuses a numbered lesson; each lesson ends with exactly one conceptual trade-off/mechanism question and one code diagnostic or edge-case exercise; the tutor stops for the learner response; no final production implementation is supplied during teaching; learning records are written only after verification; and `/teach recap` reads persistent learning records before a short refresher."
    c = p["copyContent"]
    old = "Teaching workspace: reuse an existing `.teach/` or tutor directory; otherwise prefer `.teach/` when repository policy permits\n\nMISSION"
    new = "Teaching workspace: use the repository-local `.teach/` protocol. If its canonical core is absent, route first to Teach Workspace Protocol Bootstrapper; do not clone or install an external teaching package merely to use `/teach`.\nSession invocations: `/teach <topic>` starts or resumes one topic; `/teach recap` refreshes verified prior learning.\n\nMISSION"
    if c.count(old) != 1:
        raise SystemExit(f"P96 intro anchor mismatch: {c.count(old)}")
    c = c.replace(old, new, 1)
    a, b = c.index("2. KEEP TEACHING STATE ISOLATED AND PERSISTENT"), c.index("3. GROUND BEFORE EXPLAINING")
    c = c[:a] + """2. REQUIRE THE CANONICAL `.teach/` CORE BEFORE A SESSION
`/teach <topic>` is a teaching-session command, not a bootstrap command. The established core is:
.teach/
  MISSION.md            # current topic, target outcome, constraints, frontier
  RESOURCES.md          # ground-truth repository docs/specs and trusted references
  lessons/              # numbered modular lessons or visual `.html` simulators
  learning-records/     # dated evidence of verified understanding
If this core is absent, use Teach Workspace Protocol Bootstrapper first. Do not create or clone a separate teaching repository and do not require an external package. Optional `assets/` or `reference/` material may be added later only when a lesson actually needs it. Keep tutorial state out of production code.

""" + c[b:]
    a, b = c.index("6. EVERY LESSON REQUIRES ACTIVE RETRIEVAL + PRACTICE"), c.index("7. ZERO BLACK-BOX PRODUCTION GENERATION DURING TEACHING")
    c = c[:a] + """6. END EVERY ATOMIC LESSON WITH EXACTLY TWO LEARNER CHECKPOINTS
After the first-principles explanation, halt with exactly:
A. CONCEPTUAL TRADE-OFF / MECHANISM — one question about the invariant, trade-off, causal mechanism, or failure state; and
B. CODE DIAGNOSTIC / EDGE CASE — one small exercise requiring diagnosis, a critical code fragment, test expectation, state transition, or edge-case reasoning.
Then stop and wait for the learner's response. Do not answer the checkpoint yourself in the same turn. Evaluate the response before advancing; incorrect or incomplete reasoning changes the scaffolding rather than being silently promoted to mastery.

""" + c[b:]
    a, b = c.index("10. RECORD LEARNING STATE HONESTLY"), c.index("11. RECAP WITHOUT STARTING OVER")
    c = c[:a] + """10. VERIFY BEFORE WRITING THE LEARNING RECORD
Do not create a VERIFIED/MASTERED learning record merely because a lesson was delivered. Evaluate the learner's conceptual and diagnostic responses first. When understanding is demonstrated, write or update `.teach/learning-records/<date>_<topic>.md` with concise evidence: concept, checkpoint result, practical/edge-case evidence, remaining weak point if any, and next frontier. If verification fails, record NEEDS_REVIEW/PRACTICED only when that state is useful and continue scaffolding; never label exposure as mastery.

""" + c[b:]
    a, b = c.index("11. RECAP WITHOUT STARTING OVER"), c.index("12. ITERATE THE CURRICULUM")
    c = c[:a] + """11. `/teach recap` — RE-ANCHOR VERIFIED WORKING MEMORY
When invoked with `/teach recap`, read `.teach/MISSION.md` plus all relevant files in `.teach/learning-records/` before teaching anything new. Build a compact refresher from concepts actually verified, then run a quick roughly two-minute quiz focused on the most important or fragile relationships. Revisit only what decayed and continue from the first unmastered frontier. Do not replay the curriculum from the beginning and do not infer mastery from a record that lacks verification evidence.

""" + c[b:]
    p["copyContent"] = c
    REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add_bootstrap() -> dict:
    draft = {
        "name": "Teach Workspace Protocol Bootstrapper",
        "type": "TEACH SETUP",
        "class": "LEARNING / WORKSPACE BOOTSTRAP",
        "sprintRole": "Install or repair the repository-local `.teach/` protocol and agent routing rule so later `/teach <topic>` and `/teach recap` sessions have durable state without an external package or dedicated teaching repository",
        "useWhen": "A repository or ordinary directory does not yet have the `/teach` workspace protocol, its core `.teach/` state is incomplete, or the agent instruction for `/teach` has not been installed; use P96 instead when the workspace already exists and the user wants an actual lesson or recap.",
        "inspectFirst": "Repository root and policy/governance files; existing `.teach/` contents if any; current agent instruction owners such as AGENTS.md, CLAUDE.md, `.cursorrules`, or repo-specific equivalents; ignore unrelated production implementation.",
        "expectedOutput": "A minimal repository-local `.teach/` workspace with MISSION.md, RESOURCES.md, lessons/, and learning-records/, plus one canonical agent instruction rule that routes `/teach <topic>` and `/teach recap` into that stateful protocol without installing an external package or cloning a separate teaching repository.",
        "nextStep": "Validate the exact workspace tree and instruction markers, report the installed owner, then invoke P96 with `/teach <topic>`; do not begin teaching the topic inside this bootstrap sprint unless the user separately switches to the teaching prompt.",
        "proofGate": "The `.teach/` core exists in the target repository/directory; MISSION.md and RESOURCES.md have usable templates rather than invented subject matter; lessons/ and learning-records/ exist; the existing canonical agent instruction surface contains the `/teach` routing contract; no external package/dedicated teaching repo was introduced; existing unrelated agent instructions were preserved; and a static smoke check proves `/teach <topic>` and `/teach recap` are discoverable.",
        "color": "Amber",
        "category": "standard",
        "copyContent": """ESTABLISH OR REPAIR THE REPOSITORY-LOCAL `/teach` WORKSPACE PROTOCOL. DO NOT TEACH THE TOPIC YET.

Repo or directory: xyz_repo_or_path
Lane: teaching workspace bootstrap
Owned scope: `.teach/` core state plus the existing canonical agent-instruction surface needed to route `/teach`
Forbidden scope: production feature work, a separate teaching repository, external teaching packages, unrelated agent-rule rewrites, fabricated learning records

MISSION
Make `/teach` a pure workspace protocol that can be dropped into an ordinary repository or directory. Establish durable state and one discoverable agent rule so later teaching sessions can resume from evidence instead of reconstructing the learner's history. This bootstrap prompt owns setup only; Stateful Socratic Technical Tutor Workspace owns actual `/teach <topic>` and `/teach recap` sessions.

1. RECOVER THE LOCAL OWNER BEFORE CREATING FILES
Inspect repository policy and existing agent instruction surfaces first. Reuse the canonical owner already used by the project (for example AGENTS.md, CLAUDE.md, `.cursorrules`, or a repo-specific system-prompt file). If several exist, follow repository precedence rather than duplicating the `/teach` rule into all of them. Preserve unrelated instructions.

2. NO PACKAGE OR CLONE DEPENDENCY
Treat `/teach` as folders + Markdown/HTML lesson artifacts + an agent routing rule. Do not install an external dependency and do not clone or create a dedicated teaching repository merely to enable it. The target repository/directory itself owns the learning state.

3. ESTABLISH THE CANONICAL CORE
Create or repair only this required core:
.teach/
  MISSION.md            # current learning objective, target outcome, constraints, frontier
  RESOURCES.md          # ground-truth repository docs/specs and trusted references
  lessons/              # numbered modular lessons; `.html` is allowed when a visual simulator materially helps
  learning-records/     # dated records written after learning verification
Do not pre-create decorative subtrees. Preserve valid existing `.teach/` work and merge missing structure non-destructively.

4. SEED STATE WITHOUT INVENTING MASTERY
MISSION.md may contain a compact blank/current template for Topic, Target outcome, Constraints, and Current frontier. RESOURCES.md may explain how authoritative repository/spec links and notes are recorded. Do not invent completed lessons, resources, or MASTERED records. Empty directories may use the repository's established placeholder convention only when version control requires it.

5. INSTALL THE `/teach` AGENT RULE
Add a bounded rule to the canonical agent instruction owner:
- `/teach <topic>` updates `.teach/MISSION.md`, grounds the lesson from `.teach/RESOURCES.md` plus repository truth, creates/reuses `.teach/lessons/<number>_<topic>.md` (or `.html` for a useful visual), teaches from first principles, never jumps to final production code, and ends with exactly one conceptual trade-off/mechanism question plus one code diagnostic or edge-case exercise.
- The agent must stop for the learner response, evaluate it, and write `.teach/learning-records/<date>_<topic>.md` as VERIFIED/MASTERED only after demonstrated understanding.
- `/teach recap` reads the learning records first and runs a quick roughly two-minute refresher quiz before resuming at the first weak/unmastered frontier.
Keep this rule as routing/behavior policy; do not duplicate the whole tutor prompt into governance.

6. VALIDATE THE BOOTSTRAP
Use repository-native checks where available. At minimum prove the four core paths exist, MISSION.md/RESOURCES.md are readable, the canonical instruction owner contains both `/teach <topic>` and `/teach recap`, and no unintended production files changed. Run `git diff --check` and the closest docs/governance test if the repository has one.

7. CLOSE AT THE SETUP BOUNDARY
Report the instruction owner, `.teach/` artifacts created/reused, validation, any repository-specific limitation, and the exact next invocation `/teach <topic>`. Do not silently cross into the lesson itself. If a `.teach/` workspace was already complete and correctly routed, prove that and make no ceremonial churn.""",
        "keywords": ["teach setup", "teach bootstrap", "/teach workspace", ".teach", "learning workspace setup", "teaching protocol", "MISSION.md", "learning-records", "teach skill install", "socratic workspace bootstrap"],
    }
    draft_path = ROOT / ".teach-bootstrap-draft.tmp.json"
    receipt_path = ROOT / ".teach-bootstrap-receipt.tmp.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    out = subprocess.check_output(["python", "scripts/prompt_registry_ops.py", "add", "--input", str(draft_path), "--registry", "tutorial-discovery-prompts"], cwd=ROOT, text=True)
    receipt_path.write_text(out, encoding="utf-8")
    draft_path.unlink()
    receipt = json.loads(out)
    print(json.dumps({"helper_receipt": receipt}, ensure_ascii=False))
    return receipt


def route_and_test(receipt: dict) -> None:
    new_id, new_name = receipt["id"], receipt["name"]
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    p65 = next(x for x in data["prompts"] if x["id"] == "P65")
    anchor = "- P96 Stateful Socratic Technical Tutor Workspace: learn a technical topic through persistent grounded lessons, active retrieval, practical exercises, visualizers, and mastery records."
    route = f"- {new_id} {new_name}: establish or repair the repository-local `.teach/` protocol and agent routing rule before a teaching session."
    if p65["copyContent"].count(anchor) != 1:
        raise SystemExit("P65 route anchor mismatch")
    p65["copyContent"] = p65["copyContent"].replace(anchor, route + "\n" + anchor, 1)
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    t = FOCUSED.read_text(encoding="utf-8")
    old = '''        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        self.assertEqual(regression["class"], "TESTING / REGRESSION")\n        self.assertEqual(design["class"], "SOFTWARE ARCHITECTURE / PROGRAM DESIGN")\n        self.assertEqual(teach["class"], "LEARNING / STATEFUL TUTOR")\n        self.assertEqual(len({regression["id"], design["id"], teach["id"]}), 3)\n        for prompt in (regression, design, teach):'''
    new = '''        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        self.assertEqual(regression["class"], "TESTING / REGRESSION")\n        self.assertEqual(design["class"], "SOFTWARE ARCHITECTURE / PROGRAM DESIGN")\n        self.assertEqual(bootstrap["class"], "LEARNING / WORKSPACE BOOTSTRAP")\n        self.assertEqual(teach["class"], "LEARNING / STATEFUL TUTOR")\n        self.assertEqual(len({regression["id"], design["id"], bootstrap["id"], teach["id"]}), 4)\n        for prompt in (regression, design, bootstrap, teach):'''
    if t.count(old) != 1:
        raise SystemExit("distinctness anchor mismatch")
    t = t.replace(old, new, 1)
    old = '            "RECAP WITHOUT STARTING OVER",\n        ):'
    new = '            "`/teach <topic>`",\n            "`/teach recap`",\n            "exactly two learner checkpoints",\n            ".teach/learning-records/<date>_<topic>.md",\n        ):'
    if t.count(old) != 1:
        raise SystemExit("teach assertions anchor mismatch")
    t = t.replace(old, new, 1)
    marker = "    def test_p79_harvests_whole_chat_twice_and_complements_utility(self) -> None:\n"
    add = '''    def test_teach_bootstrap_is_distinct_pure_workspace_setup(self) -> None:\n        bootstrap = self.by_name["Teach Workspace Protocol Bootstrapper"]\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        self.assertNotEqual(bootstrap["id"], teach["id"])\n        self.assertIn("use P96 instead", bootstrap["useWhen"])\n        content = bootstrap["copyContent"]\n        for phrase in (\n            "NO PACKAGE OR CLONE DEPENDENCY", ".teach/", "MISSION.md", "RESOURCES.md",\n            "lessons/", "learning-records/", "`/teach <topic>`", "`/teach recap`",\n            "exactly one conceptual trade-off/mechanism question", "one code diagnostic or edge-case exercise",\n            "Do not silently cross into the lesson itself",\n        ):\n            self.assertIn(phrase, content)\n\n'''
    if t.count(marker) != 1:
        raise SystemExit("bootstrap test anchor mismatch")
    t = t.replace(marker, add + marker, 1)
    old = '            "Stateful Socratic Technical Tutor Workspace",\n        ):'
    new = '            "Stateful Socratic Technical Tutor Workspace",\n            "Teach Workspace Protocol Bootstrapper",\n        ):'
    if t.count(old) != 1:
        raise SystemExit("P65 route test anchor mismatch")
    FOCUSED.write_text(t.replace(old, new, 1), encoding="utf-8")

    t = DISCOVERY.read_text(encoding="utf-8")
    old = '        self.assertEqual(set(by_id), {"P64", "P65", "P96"})\n'
    new = f'        self.assertEqual(set(by_id), {{"P64", "P65", "P96", "{new_id}"}})\n'
    if t.count(old) != 1:
        raise SystemExit("discovery id-set anchor mismatch")
    t = t.replace(old, new, 1)
    anchor = '        self.assertIn("active retrieval", by_id["P96"]["copyContent"].lower())\n'
    if t.count(anchor) != 1:
        raise SystemExit("discovery name anchor mismatch")
    DISCOVERY.write_text(t.replace(anchor, anchor + f'        self.assertEqual(by_id["{new_id}"]["name"], "{new_name}")\n', 1), encoding="utf-8")


def main() -> None:
    strengthen_p96()
    receipt = add_bootstrap()
    route_and_test(receipt)
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")
    run("python", "scripts/prompt_registry_ops.py", "validate")
    run("python", "-m", "unittest", "tests.test_prompt_registry_expansion_regression_design_teach", "tests.test_prompt_kit_discovery", "-v")
    run("python", "scripts/validate_prompt_kit_discovery.py", "--summary")
    run("python", "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html", "--check")
    run("git", "diff", "--check")


if __name__ == "__main__":
    main()
