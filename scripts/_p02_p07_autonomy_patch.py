#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_PATH = ROOT / "docs" / "prompts.json"

prompts = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
by_id = {item["id"]: item for item in prompts}
p02 = by_id["P02"]
p07 = by_id["P07"]

p02["sprintRole"] = (
    "Recover prior chat/context, prototype and critique the implementation launch pack "
    "iteratively, and present only the refined executable result"
)
p02["expectedOutput"] = (
    "A context-grounded launch order and executable build panels that have been privately "
    "prototyped, checked against the recovered requirements and repo evidence, revised until "
    "a bounded fixed point, and presented without unnecessary user involvement."
)
p02["nextStep"] = (
    "Privately prototype the launch pack, validate it against recovered context and repository "
    "evidence, critique gaps/collisions/ambiguity, revise until the fixed-point gate is met, "
    "then present the final pack and launch the first executable panel."
)
p02["proofGate"] = (
    "Prior context is recovered as far as available; at least one deliberate prototype -> "
    "critique -> revise pass occurs before presentation; every identified harness/application "
    "gap has an executable owner or evidence that no build is needed; unresolved questions "
    "are escalated to the user only when the missing fact or action is genuinely user-only."
)

p02_intro = """CONTEXT RECOVERY + ITERATIVE PROTOTYPE CONTRACT
- When this prompt follows another chat, named conversation, pasted context, handoff, plan, or partial implementation, recover that context first using the conversation/history/context/repository evidence available to the agent. Do not ask the user to repeat information that the agent can retrieve, inspect, infer safely, or verify from repository truth.
- Build a PRIVATE candidate launch pack first. Do not present the first plausible mapping as final.
- Run at least one deliberate prototype loop before presentation: PROTOTYPE -> CHECK AGAINST RECOVERED REQUIREMENTS -> INSPECT REPO EVIDENCE -> CRITIQUE -> REVISE.
- Critique the candidate for missing decisions, duplicated ownership, wrong dependency order, unsafe assumptions, weak proof gates, excessive prompt size, omitted executable work, and places where the candidate would unnecessarily send work back to the user.
- When the critique finds a concrete in-scope defect, revise the candidate and repeat the relevant checks. Continue until a bounded fixed point: no practical unresolved requirement, ownership collision, dependency defect, missing execution instruction, or safe refinement revealed by current evidence remains.
- Present only the refined launch order/panels/supporting map. Do not narrate discarded prototypes unless a rejected alternative materially affects the final decision.
- Do not manufacture endless revisions. A later pass may make zero changes when its evidence review proves the candidate is already at the bounded fixed point.

AUTONOMOUS EXECUTION / USER-ONLY GATE
- Keep agent-capable work with the agent. Do not ask the user to inspect files, run commands, compare outputs, choose among technically equivalent implementation details, approve routine safe steps, restate recoverable context, perform tests the agent can run, or manually carry information between tools/chats when the agent has access to do so.
- Resolve ambiguity from current chat/context, repository evidence, existing conventions, tests, validators, history, and safe reversible prototypes before escalating.
- If multiple safe choices exist and repository/user constraints do not distinguish them, choose the smallest reversible option that best matches existing patterns, record the assumption, and continue.
- Involve the user only when progress requires something genuinely user-only: a preference that materially changes the product and cannot be inferred, credentials/secrets the agent cannot access, explicit authorization/consent, a physical-world action, access to a private system/tool the agent cannot reach, or a consequential irreversible choice reserved for the user.
- When a user-only gate is unavoidable, ask one minimal concrete question or request one exact action. State what has already been completed, why the gate cannot be resolved agent-side, and what work will resume immediately afterward."""

p02_anchor = "SOURCE OF TRUTH\nUse the best available chat context"
if "CONTEXT RECOVERY + ITERATIVE PROTOTYPE CONTRACT" not in p02["copyContent"]:
    if p02_anchor not in p02["copyContent"]:
        raise SystemExit("P02 insertion anchor missing")
    p02["copyContent"] = p02["copyContent"].replace(
        "SOURCE OF TRUTH\n", p02_intro + "\n\nSOURCE OF TRUTH\n", 1
    )

p02_quality_anchor = "7. QUALITY RULES\n"
if "- Present only the refined candidate after the prototype loop; do not expose the user to avoidable intermediate drafts." not in p02["copyContent"]:
    if p02_quality_anchor not in p02["copyContent"]:
        raise SystemExit("P02 quality anchor missing")
    p02["copyContent"] = p02["copyContent"].replace(
        p02_quality_anchor,
        p02_quality_anchor
        + "- Present only the refined candidate after the prototype loop; do not expose the user to avoidable intermediate drafts.\n"
        + "- Do not delegate agent-capable discovery, validation, comparison, or repair work back to the user.\n",
        1,
    )

p07_autonomy = """AUTONOMOUS EXECUTION / USER-ONLY GATE
- Keep agent-capable work with the agent. Do not ask the user to inspect files, run commands, compare logs, execute tests, choose routine implementation details, approve safe reversible repo mutations, restate recoverable context, or manually bridge information between tools when the agent can do that work itself.
- Before asking a question, exhaust current conversation/context, repository evidence, existing conventions, tests/validators, connected tools, safe reversible experiments, and the current iteration loop.
- If several safe bounded implementations satisfy the request and no user preference materially distinguishes them, choose the smallest reversible option that best matches repository patterns, record the assumption, implement it, and validate it.
- Do not turn the user into the test runner, log collector, CI watcher, or integration operator when the current environment can perform those actions.
- Involve the user only for a genuinely user-only dependency: missing preference that materially changes the requested product and cannot be inferred, credentials/secrets unavailable to the agent, explicit authorization/consent, physical-world action, inaccessible private-system action, or consequential irreversible choice reserved for the operator.
- When blocked by a user-only dependency, advance every other safe owned action first. Then ask one minimal concrete question or request one exact action, name the completed work and exact blocker, and resume from that gate rather than restarting the sprint."""

p07_anchor = "Your job is to change the repository, validate the change, commit and push it"
if "AUTONOMOUS EXECUTION / USER-ONLY GATE" not in p07["copyContent"]:
    if p07_anchor not in p07["copyContent"]:
        raise SystemExit("P07 insertion anchor missing")
    p07["copyContent"] = p07["copyContent"].replace(
        p07_anchor, p07_autonomy + "\n" + p07_anchor, 1
    )

if "user-only" not in p07["expectedOutput"].casefold():
    p07["expectedOutput"] = p07["expectedOutput"].rstrip(".") + (
        "; agent-capable work remains autonomous and user involvement is reserved for "
        "genuinely user-only dependencies."
    )
if "user-only" not in p07["proofGate"].casefold():
    p07["proofGate"] = p07["proofGate"].rstrip(".") + (
        "; no agent-capable task is delegated back to the user, and any user escalation "
        "names a genuinely user-only dependency."
    )

PROMPTS_PATH.write_text(
    json.dumps(prompts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
