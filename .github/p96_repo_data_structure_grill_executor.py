from __future__ import annotations

import json
from pathlib import Path

REGISTRY = Path("registry/prompts/tutorial-discovery-prompts.v1.json")
TEST = Path("tests/test_prompt_registry_expansion_regression_design_teach.py")

payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
p96_matches = [p for p in payload["prompts"] if p.get("id") == "P96"]
p65_matches = [p for p in payload["prompts"] if p.get("id") == "P65"]
if len(p96_matches) != 1 or len(p65_matches) != 1:
    raise SystemExit(f"expected one P96 and one P65, found P96={len(p96_matches)} P65={len(p65_matches)}")
p96 = p96_matches[0]
p65 = p65_matches[0]
if p96.get("name") != "Stateful Socratic Technical Tutor Workspace":
    raise SystemExit(f"unexpected P96 identity: {p96.get('name')!r}")
if p65.get("name") != "Guided Prompt Finder Questionnaire":
    raise SystemExit(f"unexpected P65 identity: {p65.get('name')!r}")

p96["sprintRole"] = (
    "Turn a repository, technical system, or other structured skill into a persistent multi-session mastery workspace using "
    "grounded resources, first-principles decomposition, active retrieval, atomic practice, repository data-structure grilling, "
    "reusable visual lesson assets, and evidence-backed learning records"
)

use_add = (
    " It also owns repository data-structure grilling when the learner wants to understand the models, schemas, types, keys, "
    "ownership, lifecycle, transformations, persistence, boundaries, and invariants well enough to review and complement AI work."
)
if "repository data-structure grilling" not in p96["useWhen"]:
    p96["useWhen"] = p96["useWhen"].rstrip() + use_add

inspect_add = (
    " For repository data-structure goals, inspect the actual model/type/schema definitions, serializers, persistence/state owners, "
    "API or event payloads, tests/fixtures, migrations, and representative call/data flows before questioning the learner."
)
if "model/type/schema definitions" not in p96["inspectFirst"]:
    p96["inspectFirst"] = p96["inspectFirst"].rstrip() + inspect_add

output_add = (
    " For a repository data-structure goal, maintain a compact evidence-backed structure map and run a one-question-at-a-time "
    "Grill-Me-style interview until the learner can trace representative data, explain invariants and ownership, predict affected "
    "structures, and challenge an AI-generated change instead of merely recognizing names."
)
if "evidence-backed structure map" not in p96["expectedOutput"]:
    p96["expectedOutput"] = p96["expectedOutput"].rstrip() + output_add

next_add = (
    " For a repository data-structure goal, first build the evidence-backed structure map, then grill the first unresolved "
    "dependency or invariant one question at a time before advancing to implementation-oriented practice."
)
if "first build the evidence-backed structure map" not in p96["nextStep"]:
    p96["nextStep"] = p96["nextStep"].rstrip() + next_add

proof_add = (
    " In repository data-structure grill mode, code-answerable facts are researched by the agent rather than delegated to the "
    "learner; the interview proceeds one dependency-aware question at a time with a concise evidence-backed recommended model to "
    "challenge; the learner traces at least one representative datum end to end; and mastery is withheld until the learner can "
    "explain identity/keys, ownership/lifecycle, transformations, persistence or state boundaries, material invariants/failure "
    "states, predict which structures a proposed change touches, and critically review an AI-generated change."
)
if "In repository data-structure grill mode" not in p96["proofGate"]:
    p96["proofGate"] = p96["proofGate"].rstrip() + proof_add

content = p96["copyContent"]
grill_block = """4A. REPOSITORY DATA-STRUCTURE GRILL MODE — USE MATT POCOCK'S `grill-me` DISCIPLINE
When the mastery goal is understanding the data structures at play in a repository, switch from broad teaching into a repository-specific grilling lane. The purpose is human upscaling: the learner should understand the structural model deeply enough to complement AI capabilities, catch bad assumptions, and review generated changes rather than becoming a passive prompt operator.

GROUND THE STRUCTURE MAP BEFORE ASKING FACT QUESTIONS
Inspect the repository yourself first. Build a compact evidence-backed map of the structures that actually matter, including as applicable:
- entities/types/classes/records and their fields or shapes;
- identity and keys, cardinality, containment, references, indexes, and graph relationships;
- ownership and lifecycle: who creates, mutates, validates, caches, persists, expires, or deletes each structure;
- schemas, serializers/deserializers, API/event/message payloads, migrations, persistence models, state stores, caches, queues, and configuration representations;
- transformations between representations and the call/data-flow seams where shape or ownership changes;
- mutability, concurrency, ordering, nullability, versioning, and other material invariants;
- tests, fixtures, migrations, and failure paths that reveal the intended model.
Do not make the learner perform repository archaeology that the agent can perform. If a question can be answered by exploring the codebase, explore it first and turn the finding into a reasoning challenge.

USE THE ACTUAL SKILL WHEN AVAILABLE; NEVER PRETEND IT RAN
If Matt Pocock's `grill-me` skill is available in the current agent environment, invoke it as the interview primitive for this lane. If it is unavailable, say `SKILL_UNAVAILABLE` once and follow the same documented discipline locally; do not claim the skill executed. Do not install tools or mutate the repository merely to obtain the skill unless the user separately authorizes that setup.

GRILL ONE DEPENDENCY AT A TIME
- Ask exactly one data-structure question at a time and wait for the learner's answer before selecting the next branch.
- Walk the dependency tree rather than following a fixed questionnaire. Resolve prerequisite concepts before downstream ones.
- Each question should include a short evidence-backed current model or recommended answer as a hypothesis for the learner to defend, refine, or reject; do not dump the full solution or remove the need for retrieval.
- Prefer questions about relationships and consequences over trivia: why a key exists, who owns mutation, where a representation changes, what invariant prevents corruption, what breaks if cardinality or ordering changes, and which boundary should reject an invalid shape.
- When the learner misses a relation, lower the abstraction, show a smaller trace or concrete instance, then ask a new one-question retrieval check.

TRACE REAL DATA THROUGH THE REPOSITORY
Before calling the structure understood, trace at least one representative datum from an entrypoint or source through validation, transformation, in-memory/state ownership, persistence or transport, and final consumer/output. Name the concrete files/types/functions that establish each hop. If the repository has multiple materially different data paths, choose another trace only when it tests a distinct ownership or representation boundary.

COMPLEMENT-AI MASTERY GATE
Do not mark this lane MASTERED merely because the learner can recite type names. The learner should be able to:
- reconstruct the important structure map without reading it verbatim;
- explain identity and keys, ownership and lifecycle, and the highest-value invariants;
- predict which structures and boundaries a proposed feature or repair is likely to touch and why;
- diagnose at least one plausible shape/ownership/invariant failure from evidence;
- challenge an AI-generated design or diff by identifying a structural assumption that must be proved against the repository.
The target is leverage: AI can search and generate quickly; the human must upscale enough to reason about the model, detect architectural drift, and make higher-quality decisions with the AI.
"""
if "4A. REPOSITORY DATA-STRUCTURE GRILL MODE" not in content:
    anchor = "\n\n5. RUN A SHORT DIAGNOSTIC, THEN TEACH AT THE FRONTIER"
    if anchor not in content:
        raise SystemExit("P96 section-5 insertion anchor missing")
    content = content.replace(anchor, "\n\n" + grill_block.rstrip() + anchor, 1)
p96["copyContent"] = content

for keyword in (
    "grill me repository",
    "repository data structures",
    "data structure grill",
    "repository data model",
    "schema ownership",
    "human ai complement",
    "ai upskilling",
):
    if keyword not in p96.setdefault("keywords", []):
        p96["keywords"].append(keyword)

old_route = (
    "- P96 Stateful Socratic Technical Tutor Workspace: learn a system or structured skill through persistent grounded lessons, "
    "active retrieval, practical exercises, visualizers, and verified mastery records."
)
new_route = (
    old_route
    + " Explicit requests to be grilled on a repository’s data structures, data model, schemas, types, keys, ownership, "
    "lifecycle, or invariants route here; P65’s own grilling is only for selecting the right Prompt Kit route."
)
if "P65’s own grilling is only for selecting the right Prompt Kit route" not in p65["copyContent"]:
    if old_route not in p65["copyContent"]:
        raise SystemExit("P65 P96 route anchor missing")
    p65["copyContent"] = p65["copyContent"].replace(old_route, new_route, 1)

for keyword in ("repository data structure grill", "grill repo data model"):
    if keyword not in p65.setdefault("keywords", []):
        p65["keywords"].append(keyword)

REGISTRY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# The focused regression may have been seeded before this executor is triggered.
tests = TEST.read_text(encoding="utf-8")
if "test_teach_repo_data_structure_grill_upscales_the_human" not in tests:
    anchor = "    def test_p79_harvests_whole_chat_twice_and_complements_utility(self) -> None:\n"
    if anchor not in tests:
        raise SystemExit("focused teaching test insertion anchor missing")
    block = '''    def test_teach_repo_data_structure_grill_upscales_the_human(self) -> None:\n        teach = self.by_name["Stateful Socratic Technical Tutor Workspace"]\n        content = teach["copyContent"]\n        for phrase in (\n            "REPOSITORY DATA-STRUCTURE GRILL MODE",\n            "MATT POCOCK'S `grill-me` DISCIPLINE",\n            "GROUND THE STRUCTURE MAP BEFORE ASKING FACT QUESTIONS",\n            "identity and keys",\n            "ownership and lifecycle",\n            "serializers/deserializers",\n            "If a question can be answered by exploring the codebase",\n            "SKILL_UNAVAILABLE",\n            "Ask exactly one data-structure question at a time",\n            "TRACE REAL DATA THROUGH THE REPOSITORY",\n            "COMPLEMENT-AI MASTERY GATE",\n            "predict which structures and boundaries",\n            "challenge an AI-generated design or diff",\n            "the human must upscale enough",\n        ):\n            self.assertIn(phrase, content)\n        self.assertIn("repository data-structure grilling", teach["useWhen"])\n        self.assertIn("evidence-backed structure map", teach["expectedOutput"])\n        self.assertIn("critically review an AI-generated change", teach["proofGate"])\n        self.assertIn("repository data structures", teach["keywords"])\n\n    def test_p65_routes_repository_data_structure_grilling_to_p96(self) -> None:\n        p65 = self.full["P65"]\n        content = p65["copyContent"]\n        self.assertIn("Explicit requests to be grilled on a repository’s data structures", content)\n        self.assertIn("P65’s own grilling is only for selecting the right Prompt Kit route", content)\n        self.assertIn("repository data structure grill", p65["keywords"])\n        self.assertIn("grill repo data model", p65["keywords"])\n\n'''
    TEST.write_text(tests.replace(anchor, block + anchor, 1), encoding="utf-8")
