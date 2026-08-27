from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"


def require_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing anchor: {label}")
    return text.replace(old, new, 1)


def strengthen_prompts() -> None:
    payload = json.loads(REG.read_text(encoding="utf-8"))
    by_id = {p["id"]: p for p in payload["prompts"]}

    p92 = by_id["P92"]
    if p92["name"] != "Canonical Path Prompt":
        raise SystemExit("P92 identity mismatch")
    p92["sprintRole"] = (
        "Establish and enforce one repository-owned canonical development checkout and production/use path per supported machine/profile, "
        "derive literal paths from current OS/user/special-folder/cloud-sync evidence, resolve the material terminal/shell/kernel/runtime boundary before "
        "choosing syntax or agent tooling, prevent duplicate working copies, and separate remote integration proof from local workstation deployment proof"
    )
    p92["useWhen"] = (
        "Agents or humans are using, cloning, installing, launching, or updating a repository and its canonical development or production path is missing, "
        "ambiguous, inconsistent across tools, or varies with OS, user profile, special-folder redirection, OneDrive/cloud state, terminal host, shell/interpreter, "
        "kernel/runtime boundary, or machine profile; especially when GitHub main is current but the workstation checkout/install may still be stale."
    )
    p92["inspectFirst"] = (
        "Current remote/default-branch truth; repository governance and harness entrypoints; existing canonical-path or machine/profile contracts; current working "
        "directory and verified checkout candidates; native OS home/profile and special-folder resolution; username/account only as runtime evidence; OneDrive/cloud "
        "roots plus target-folder redirection/availability state when relevant; terminal surface, shell/interpreter, kernel/OS/runtime boundary, local/remote/container "
        "execution target, path semantics, and material agent/tool availability; launcher/installer/updater/worktree contracts; dirty or unique work; and tests/CI that "
        "claim path or deployment readiness."
    )
    p92["expectedOutput"] = (
        "A canonical-path ledger plus a repo-owned harness contract, PATH INPUT RECEIPT, and material EXECUTION CONTEXT RECEIPT that identify the machine/profile "
        "resolution rule, OS/home/special-folder/cloud inputs, terminal/shell/kernel/runtime boundary, development checkout, production/use path, optional worktree root, "
        "and entrypoint; safe noncanonical-copy disposition; and separate evidence for remote integration, local development freshness, production/install freshness, "
        "and real-entrypoint behavior."
    )
    p92["nextStep"] = (
        "Resolve repository and machine/profile truth; derive host path inputs from native OS/environment evidence; resolve the material terminal, shell/interpreter, "
        "kernel/runtime, execution target, and path semantics before syntax-sensitive commands or shell-bound agent selection; repair/reuse the single canonical path "
        "contract; preserve conflicting work; then prove development and production paths separately."
    )
    p92["proofGate"] = (
        "Exactly one path owner exists per supported profile; literals derive from current OS/home/special-folder/cloud evidence rather than hard-coded usernames; "
        "material execution context distinguishes terminal host, shell/interpreter, kernel/runtime, and target instead of guessing syntax from a terminal label; "
        "command/agent selection fails closed when that context is unknown; path roles are explicit; noncanonical copies are diagnosed without destructive cleanup; "
        "remote merge is never local deployment proof; and the strongest safe same-entrypoint check proves the resolved use path or names the runtime blocker."
    )
    content = p92["copyContent"]
    anchor = (
        "Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. "
        "Lower-precedence evidence may expose drift but may not silently replace the owner. If current host and target profile differ, route/handoff rather than fabricate a target path locally.\n\n"
        "6. FAIL CLOSED ON PATH DRIFT"
    )
    insert = (
        "Resolution precedence: tracked canonical-path/profile contract -> authorized machine/profile override -> native home/special-folder/environment resolution -> verified existing-checkout evidence. "
        "Lower-precedence evidence may expose drift but may not silently replace the owner. If current host and target profile differ, route/handoff rather than fabricate a target path locally.\n\n"
        "5A. EXECUTION CONTEXT RECEIPT BEFORE COMMANDS OR AGENT SELECTION\n"
        "When command syntax, path semantics, launcher behavior, or agent/tool availability depends on execution context, record the material terminal surface/host; actual shell/interpreter; "
        "kernel/OS/runtime boundary; execution target (local, WSL, container, VM, SSH/remote, or CI); path/filesystem semantics; and only the tool/agent availability that changes the next action. "
        "A terminal application is not the shell: Windows Terminal can host PowerShell, `cmd.exe`, WSL shells, and other profiles. Do not infer kernel/runtime from the shell prompt either. "
        "If syntax or agent choice is context-sensitive and those facts cannot be recovered, set `EXECUTION_CONTEXT=UNKNOWN`, re-anchor from current host/repository evidence, and do not emit a guessed shell-specific mutation command. "
        "If host and target differ, route/handoff or use an explicitly target-scoped invocation rather than treating host syntax/path semantics as target truth.\n\n"
        "6. FAIL CLOSED ON PATH DRIFT"
    )
    content = require_replace(content, anchor, insert, "P92 execution context")
    content = require_replace(
        content,
        "- Could OS/user/home, Desktop Known Folder, OneDrive redirection, mount/junction, or profile state make the same logical rule resolve differently?\n",
        "- Could OS/user/home, Desktop Known Folder, OneDrive redirection, mount/junction, or profile state make the same logical rule resolve differently?\n"
        "- Could the terminal host mask a different shell, kernel/runtime, execution target, or path semantics and make the next command or agent selection wrong?\n",
        "P92 second pass",
    )
    content = require_replace(
        content,
        "Report the PATH INPUT RECEIPT/resolution source; canonical development/use/worktree paths;",
        "Report the PATH INPUT RECEIPT/resolution source; the material EXECUTION CONTEXT RECEIPT when command/agent choice depends on it; canonical development/use/worktree paths;",
        "P92 deliver",
    )
    p92["copyContent"] = content
    for keyword in ("terminal context", "shell context", "kernel context", "runtime context", "powershell vs bash", "wsl shell"):
        if keyword not in p92["keywords"]:
            p92["keywords"].append(keyword)

    donor_text = subprocess.check_output(
        ["git", "show", "origin/feat/p114-canary-network-20260826:registry/prompts/spec-architecture-prompts.v1.json"],
        cwd=ROOT,
        text=True,
    )
    donor = json.loads(donor_text)
    donor_p114 = next(p for p in donor["prompts"] if p.get("id") == "P114")
    if donor_p114.get("name") != "Conversation Context Canary & Handoff Guard":
        raise SystemExit("P114 donor identity mismatch")

    p114 = by_id["P114"]
    identity = {k: p114[k] for k in ("id", "seq", "name", "type", "class", "progress", "color", "copySheet", "category", "profile")}
    p114.clear()
    p114.update(donor_p114)
    p114.update(identity)
    p114["sprintRole"] = (
        "Keep a tiny per-response computer-profile and required-network signal visible during ordinary AI work, append material shell/kernel execution context only when "
        "command or agent choice depends on it, catch context drift early, re-anchor recoverable drift once, and produce a clean fresh-chat handoff on repeated degradation"
    )
    p114["useWhen"] = (
        "A long-running AI conversation depends on a stable computer profile, required network posture, or execution identity and the operator wants a lightweight visible signal; "
        "append execution context only when shell syntax, path semantics, terminal/kernel boundary, or AI-agent/tool selection materially affects the work."
    )
    p114["inspectFirst"] = (
        "The current conversation's established computer profile, required network posture, and active execution identity; exact WAB, Guest, Hardwire, Local, or Arbitrary/N/A labels when established; "
        "when command or agent choice is context-sensitive, the actual terminal host, shell/interpreter, kernel/OS/runtime boundary, execution target, and path semantics; when repository work is active, "
        "the canonical profile/path/network owner plus current repo, branch, lane, and task evidence; latest proven artifacts/handoff state; and accessible context needed to recover those facts without user repetition."
    )
    p114["expectedOutput"] = (
        "One compact Canary line before every response with canonical PROFILE and required NETWORK, optionally `EXEC=<shell>@<kernel/runtime>` only when execution context materially affects command or agent selection; "
        "exact network labeling, fail-closed UNKNOWN handling, one bounded re-anchor, and a compact continuity handoff on repeated or unrecoverable drift."
    )
    p114["nextStep"] = (
        "Keep doing substantive work while PROFILE and NETWORK remain correct and any material EXEC value matches evidence; before syntax-sensitive commands or agent selection resolve shell/kernel context when required; "
        "on the first mismatch re-anchor from accessible evidence, and on repeated or unrecoverable drift emit the continuity handoff with the proven floor."
    )
    p114["proofGate"] = (
        "Representative sequences keep the Canary compact; required network labels retain P114 semantics; Arbitrary/N/A never hides unknown; execution context is omitted when irrelevant and distinguishes terminal host from shell/interpreter and kernel/runtime when material; "
        "`EXEC=UNKNOWN` blocks guessed shell-specific commands/agent selection; seeded profile/network/execution drift recovers once; stylistic variation is not false drift; validation order reaches repeated/unrecoverable handoff."
    )
    c = p114["copyContent"]
    c = require_replace(
        c,
        "Required network: xyz_WAB_Guest_Hardwire_Local_Arbitrary_NA_or_resolve_from_accessible_context\nRepository, branch, and lane:",
        "Required network: xyz_WAB_Guest_Hardwire_Local_Arbitrary_NA_or_resolve_from_accessible_context\nExecution context when command/agent selection is material: xyz_shell_at_kernel_runtime_or_resolve_from_accessible_context\nRepository, branch, and lane:",
        "P114 anchor",
    )
    c = require_replace(
        c,
        "`CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>`\nWhen repository identity materially affects the response",
        "`CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>`\n"
        "When command syntax, path semantics, or agent/tool selection materially depends on the execution environment, append only:\n"
        "` | EXEC=<shell>@<kernel/runtime>`\n"
        "Examples of shape are `pwsh@Windows`, `bash@WSL2-Ubuntu`, or `bash@Linux`; use evidence-backed runtime labels. When execution context is irrelevant, omit EXEC instead of bloating every response.\n"
        "When repository identity materially affects the response",
        "P114 mandatory line",
    )
    c = require_replace(
        c,
        "- Do not invent SSIDs, VPNs, domains, credentials, trust state, or technical meaning behind these labels. Existing operator/repository network authority defines what the labels mean; the Canary only carries the smallest required label.\n\nAUTHORITATIVE PROFILE + NETWORK RULE",
        "- Do not invent SSIDs, VPNs, domains, credentials, trust state, or technical meaning behind these labels. Existing operator/repository network authority defines what the labels mean; the Canary only carries the smallest required label.\n\n"
        "EXECUTION CONTEXT SEMANTICS\n"
        "`EXEC` is conditional execution identity, not a mandatory third field. Use it when the next command, path, launcher, or AI-agent/tool choice could change because the environment changes. Resolve the actual shell/interpreter and kernel/OS/runtime boundary; treat the terminal application only as a host surface. Windows Terminal, for example, can host PowerShell, `cmd.exe`, WSL shells, and other profiles, so the terminal brand is not enough to choose syntax. Include the execution target (local, WSL, container, VM, SSH/remote, CI) in the substantive re-anchor when it matters.\n"
        "- If material execution context is established, emit `EXEC=<shell>@<kernel/runtime>`.\n"
        "- If it is required but unrecoverable, emit `EXEC=UNKNOWN`, re-anchor, and do not guess a shell-specific mutation command or shell-bound agent runtime.\n"
        "- If current host and intended target differ, keep that distinction explicit; do not treat host syntax/path semantics as target truth.\n"
        "- A legitimate shell/kernel/target change backed by newer evidence is not drift.\n\n"
        "AUTHORITATIVE PROFILE + NETWORK + EXECUTION CONTEXT RULE",
        "P114 exec semantics",
    )
    c = require_replace(c, "Use the strongest accessible current evidence for the computer profile and required network:", "Use the strongest accessible current evidence for the computer profile, required network, and material execution context:", "P114 authority")
    c = require_replace(
        c,
        "If the computer profile cannot be recovered, emit `PROFILE=UNKNOWN`; if a relevant required network cannot be recovered, emit `NETWORK=UNKNOWN`; then execute the re-anchor procedure.",
        "If the computer profile cannot be recovered, emit `PROFILE=UNKNOWN`; if a relevant required network cannot be recovered, emit `NETWORK=UNKNOWN`; if syntax/agent selection requires execution context that cannot be recovered, emit `EXEC=UNKNOWN`; then execute the re-anchor procedure.",
        "P114 unknown",
    )
    c = require_replace(c, "Keep PROFILE and NETWORK semantically stable and compact;", "Keep PROFILE and NETWORK semantically stable and compact; keep EXEC omitted when irrelevant and stable when material;", "P114 loop")
    c = require_replace(c, "On the first material Canary mismatch, omission, contradiction, `PROFILE=UNKNOWN`, or network-sensitive `NETWORK=UNKNOWN`:", "On the first material Canary mismatch, omission, contradiction, `PROFILE=UNKNOWN`, network-sensitive `NETWORK=UNKNOWN`, or command-sensitive `EXEC=UNKNOWN`:", "P114 reanchor")
    c = require_replace(c, "- recover the canonical computer profile, required network, and current task from accessible chat, repository, harness, artifact, or handoff evidence;", "- recover the canonical computer profile, required network, material shell/kernel/target context, and current task from accessible chat, repository, harness, artifact, or handoff evidence;", "P114 recover")
    c = require_replace(
        c,
        "- required network (`WAB`, `Guest`, `Hardwire`, `Local`, `Arbitrary/N/A`) or explicit UNKNOWN blocker;\n- repo, branch, PR, lane, and scope only when active;",
        "- required network (`WAB`, `Guest`, `Hardwire`, `Local`, `Arbitrary/N/A`) or explicit UNKNOWN blocker;\n- material execution context (`<shell>@<kernel/runtime>` plus target detail when needed) or explicit UNKNOWN blocker;\n- repo, branch, PR, lane, and scope only when active;",
        "P114 handoff",
    )
    c = require_replace(
        c,
        "CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>. NETWORK is the required posture, not observed connectivity.",
        "CANARY STUB — Before every response emit CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>. Append ` | EXEC=<shell>@<kernel/runtime>` only when command/agent choice materially depends on execution context. NETWORK is the required posture, not observed connectivity.",
        "P114 stub",
    )
    c = require_replace(
        c,
        "- Repository machine/profile/path/network contracts remain authoritative for what the computer profile and required network actually are;",
        "- P92 Canonical Path Prompt and repository machine/profile/path/network contracts remain authoritative for canonical paths and material execution context; this Canary carries only the smallest signal and must not create a competing registry.\n- Repository machine/profile/path/network contracts remain authoritative for what the computer profile and required network actually are;",
        "P114 owner boundary",
    )
    c = require_replace(c, "- Never fabricate a required network or use `Arbitrary/N/A` merely because the requirement was forgotten.\n", "- Never fabricate a required network or use `Arbitrary/N/A` merely because the requirement was forgotten.\n- Never infer shell/kernel/runtime from a terminal brand, and never choose syntax-sensitive mutation commands or shell-bound agent tooling from unresolved EXEC context.\n", "P114 fail closed")
    c = require_replace(c, "2. RECOVERY CASE — seed one omission, one wrong profile, and one wrong required-network label;", "2. RECOVERY CASE — seed one omission, one wrong profile, one wrong required-network label, and one wrong material shell/kernel execution context;", "P114 recovery case")
    c = require_replace(c, "3. LEGITIMATE CHANGE — change the profile or required network only when newer authoritative evidence establishes the change;", "3. LEGITIMATE CHANGE — change the profile, required network, shell/kernel runtime, or execution target only when newer authoritative evidence establishes the change;", "P114 legit change")
    c = require_replace(c, "5. UNRECOVERABLE STATE — make the canonical profile or a relevant required network unrecoverable;", "5. UNRECOVERABLE STATE — make the canonical profile, a relevant required network, or a command-sensitive execution context unrecoverable;", "P114 unknown case")
    c = require_replace(c, "profile, required network, active execution identity, mission, proven floor, gap, forbidden scope, and first executable continuation.", "profile, required network, material execution context when relevant, active execution identity, mission, proven floor, gap, forbidden scope, and first executable continuation.", "P114 deliver")
    p114["copyContent"] = c
    for keyword in ("execution canary", "shell canary", "kernel runtime", "terminal context", "exec unknown"):
        if keyword not in p114["keywords"]:
            p114["keywords"].append(keyword)

    REG.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strengthen_tests() -> None:
    path = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
    text = path.read_text(encoding="utf-8")
    anchor = '            "tracked canonical-path/profile contract -> authorized machine/profile override",\n'
    addition = anchor + (
        '            "EXECUTION CONTEXT RECEIPT BEFORE COMMANDS OR AGENT SELECTION",\n'
        '            "A terminal application is not the shell",\n'
        '            "Windows Terminal can host PowerShell",\n'
        '            "EXECUTION_CONTEXT=UNKNOWN",\n'
        '            "do not emit a guessed shell-specific mutation command",\n'
    )
    text = require_replace(text, anchor, addition, "P92 regression")
    path.write_text(text, encoding="utf-8")

    (ROOT / "tests" / "test_conversation_context_canary_prompt.py").write_text(
        '''from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_prompt_kit_registry

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_REGISTRY = REPO_ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST_FLOOR = REPO_ROOT / "harness" / "test-floor.v1.json"
TARGET_NAME = "Conversation Context Canary & Handoff Guard"
TEST_PATH = "tests/test_conversation_context_canary_prompt.py"


class ConversationContextCanaryPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.full = build_prompt_kit_registry.load_prompt_kit_registry()
        cls.by_id = {prompt["id"]: prompt for prompt in cls.full}
        matches = [prompt for prompt in cls.full if prompt.get("name") == TARGET_NAME]
        if len(matches) != 1:
            raise AssertionError(f"expected one {TARGET_NAME!r}, found {len(matches)}")
        cls.target = matches[0]
        raw_prompts = json.loads(RAW_REGISTRY.read_text(encoding="utf-8"))["prompts"]
        raw_matches = [prompt for prompt in raw_prompts if prompt.get("name") == TARGET_NAME]
        if len(raw_matches) != 1:
            raise AssertionError(f"expected one raw {TARGET_NAME!r}, found {len(raw_matches)}")
        cls.raw = raw_matches[0]

    def test_identity_and_profile_remain_stable(self) -> None:
        self.assertEqual(self.target["id"], "P114")
        self.assertEqual(self.target["seq"], "114")
        self.assertEqual(self.target["copySheet"], "P114_COPY_SAFE")
        self.assertEqual(self.target["profile"], "spec-architecture")
        self.assertEqual(self.target["class"], "CONTEXT / CONTINUITY")
        self.assertEqual(self.raw["id"], self.target["id"])

    def test_canary_requires_profile_and_required_network_every_response(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "MANDATORY FIRST LINE",
            "CANARY | PROFILE=<canonical computer profile> | NETWORK=<WAB|Guest|Hardwire|Local|Arbitrary/N/A>",
            "Do not expand the normal Canary into scope narration",
            "Keep the normal Canary to one line",
        ):
            self.assertIn(phrase, content)
        for network in ("WAB", "Guest", "Hardwire", "Local", "Arbitrary/N/A"):
            self.assertIn(network, content)

    def test_network_is_required_posture_not_observed_connectivity(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "REQUIRED NETWORK SEMANTICS",
            "network the user should be on for the current task",
            "not, by itself, a claim that the agent has observed the user's live connection",
            "It must never be used as a synonym for unknown",
            "NETWORK=UNKNOWN",
        ):
            self.assertIn(phrase, content)

    def test_execution_context_is_conditional_and_distinguishes_terminal_shell_kernel(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "EXECUTION CONTEXT SEMANTICS",
            "EXEC=<shell>@<kernel/runtime>",
            "EXEC=UNKNOWN",
            "terminal application only as a host surface",
            "Windows Terminal, for example, can host PowerShell, `cmd.exe`, WSL shells",
            "do not guess a shell-specific mutation command or shell-bound agent runtime",
            "When execution context is irrelevant, omit EXEC",
        ):
            self.assertIn(phrase, content)

    def test_unknown_material_context_fails_closed_and_reanchors(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "PROFILE=UNKNOWN",
            "NETWORK=UNKNOWN",
            "command-sensitive `EXEC=UNKNOWN`",
            "RE-ANCHOR ONCE",
            "Do not ask the operator to repeat recoverable context",
        ):
            self.assertIn(phrase, content)

    def test_handoff_preserves_network_and_material_execution_context(self) -> None:
        content = self.target["copyContent"]
        for phrase in (
            "HANDOFF ON REPEATED OR UNRECOVERABLE DRIFT",
            "required network (`WAB`, `Guest`, `Hardwire`, `Local`, `Arbitrary/N/A`)",
            "material execution context (`<shell>@<kernel/runtime>` plus target detail when needed)",
            "current mission and forbidden scope",
            "last proven artifacts, SHAs, checks, or other evidence",
            "first executable next action",
        ):
            self.assertIn(phrase, content)

    def test_lightweight_stub_preserves_owner_boundaries(self) -> None:
        content = self.target["copyContent"]
        self.assertIn("ONE CANONICAL CONTRACT, LIGHTWEIGHT EMBEDDING", content)
        self.assertIn("do not paste this entire contract into every prompt", content)
        self.assertIn("Append ` | EXEC=<shell>@<kernel/runtime>` only when command/agent choice materially depends", content)
        self.assertIn("P92 Canonical Path Prompt", content)
        self.assertIn("must not create a competing profile or network registry", content)

    def test_semantic_falsification_order_covers_exec_context(self) -> None:
        content = self.target["copyContent"]
        ordered = ("1. STABLE BASELINE", "2. RECOVERY CASE", "3. LEGITIMATE CHANGE", "4. REPEATED DRIFT", "5. UNRECOVERABLE STATE")
        positions = [content.index(marker) for marker in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("wrong material shell/kernel execution context", content)
        self.assertIn("shell/kernel runtime, or execution target", content)
        self.assertIn("command-sensitive execution context unrecoverable", content)

    def test_neighbor_owners_remain_distinct(self) -> None:
        self.assertEqual(self.by_id["P02"]["name"], "Previous Chat → Active Sprint Executor")
        self.assertEqual(self.by_id["P76"]["name"], "Progressive-Disclosure Spec & Harness Factorer")
        self.assertNotEqual(self.target["id"], "P02")
        self.assertNotEqual(self.target["id"], "P76")

    def test_registered_in_deterministic_test_floor(self) -> None:
        floor = json.loads(TEST_FLOOR.read_text(encoding="utf-8"))
        self.assertEqual(floor["self_tests"].count(TEST_PATH), 1)
        self.assertIn("tests/test_*_prompt.py", floor["prompt_semantic_test_globs"])

    def test_generated_site_is_exact_and_contains_canary(self) -> None:
        html = build_prompt_kit_registry.DEFAULT_OUTPUT.read_text(encoding="utf-8")
        self.assertEqual(html, build_prompt_kit_registry.render())
        self.assertIn("P114", html)
        self.assertIn(TARGET_NAME, html)
        self.assertIn("kernel/runtime", html)
        self.assertIn("EXEC=", html)


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


def strengthen_finder() -> None:
    path = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
    text = path.read_text(encoding="utf-8")
    old_goal = """ {id:'goal',prompt:'What are you trying to accomplish?',options:[
  {id:'plan',label:'Plan or divide the work',queries:['plan','factor','sprint plan']},
  {id:'coordinate',label:'Keep human and agent work continuous in a repository ledger',queries:['repository ledger','work ledger','agent queue','shared work state']},
  {id:'build',label:'Implement a bounded change',queries:['implement','build','sprint']},
  {id:'ai-level-up',label:'Level up an AI/agent repository for production',queries:['ai engineering level up','evals','context engineering','production agents','llm ops','adaptability']},
  {id:'prove',label:'Validate or prove behavior',queries:['validate','behavior proof','runtime']},
  {id:'ship',label:'Integrate, deploy, or release',queries:['integrate','deploy','release']},
  {id:'teach',label:'Create tutorials or guidance',queries:['tutorial','documentation','repo tutorial']},
  {id:'close',label:'Clean up or hand off work',queries:['closeout','handoff','pr cleanup']}
 ]},"""
    new_goal = """ {id:'goal',prompt:'What outcome must this tutorial hand you?',options:[
  {id:'create-prompt',label:'Create or strengthen a Prompt Kit prompt',ownerId:'P79',terminal:'A Prompt Kit contribution is added or its canonical owner is strengthened and proved.',queries:['add prompt','prompt registry','strengthen prompt']},
  {id:'implement',label:'Implement a bounded repository change',ownerId:'P07',terminal:'A bounded repository change is implemented, validated, and integrated or exactly blocked.',queries:['implement','build','sprint']},
  {id:'troubleshoot',label:'Diagnose something that is failing now',ownerId:'P58',terminal:'The failure has evidence, a narrowed cause, and a bounded repair route.',queries:['troubleshoot','diagnose','root cause']},
  {id:'verify-inherited',label:'Verify work another agent says is complete',ownerId:'P83',terminal:'The inherited completion claim is independently verified, repaired, and advanced as evidence permits.',queries:['agent work verifier','inherited completion','verify agent work']},
  {id:'prioritize-repos-now',label:'Decide which repository should move first right now',ownerId:'P23',terminal:'Repositories are ranked by current circumstances separately from structural gap severity.',queries:['circumstance priority','which repo now','urgency access']},
  {id:'publish-tutorial',label:'Create or repair durable tutorial documentation',ownerId:'P18',terminal:'Operator-ready documentation is written from current behavior and validated.',queries:['tutorial','documentation','repo tutorial']},
  {id:'prove-change',label:'Prove a change preserved behavior',ownerId:'P94',terminal:'Requested behavior and impacted protected behavior are both regression-proved at the strongest safe level.',queries:['regression testing','live regression','preserve existing behavior']},
  {id:'ship',label:'Integrate, deploy, or release validated work',ownerId:'P15',terminal:'Validated work is integrated through the repository-authorized gate with resulting identity proof.',queries:['integrate','deploy','release']},
  {id:'close',label:'Compress completed or blocked work for handoff',ownerId:'P12',terminal:'The exact sprint state is compressed into an evidence-bearing continuation.',queries:['closeout','handoff','next command']}
 ]},"""
    text = require_replace(text, old_goal, new_goal, "finder outcome question")
    text = require_replace(
        text,
        "];\nvar S={step:0,answers:{},origin:null};",
        "];\nvar PROMPT_FINDER_OUTCOMES=PROMPT_FINDER_QUESTIONS.find(function(q){return q.id==='goal'}).options.map(function(o){return {id:o.id,label:o.label,ownerId:o.ownerId,terminal:o.terminal}});\nvar S={step:0,answers:{},origin:null};",
        "finder outcome export data",
    )
    old_score = "function scorePromptFinderAnswers(answers){var scores={},reasons={};Object.keys(answers).forEach(function(questionId){var question=questionById(questionId),option=optionById(question,answers[questionId]);if(!option)return;option.queries.forEach(function(query){sharedSearch(query).slice(0,5).forEach(function(prompt,index){var id=prompt.id,points=10-(index*2);scores[id]=(scores[id]||0)+Math.max(points,2);(reasons[id]||(reasons[id]=[])).push(option.label)})})});return Object.keys(scores).map(function(id){var prompt=PROMPTS.find(function(p){return p.id===id});return prompt?{prompt:prompt,score:scores[id],reasons:Array.from(new Set(reasons[id]))}:null}).filter(Boolean).sort(function(a,b){return b.score-a.score||rank(a.prompt)-rank(b.prompt)}).slice(0,3)}"
    new_score = "function promptFinderRouteIsActionable(prompt){return !!prompt&&['copyContent','expectedOutput','proofGate','nextStep'].every(function(key){var value=String(prompt[key]||'').trim();return value.length>0&&!/^xyz[_ -]/i.test(value)})}\nfunction resolvePromptFinderOutcome(answers){var question=questionById('goal'),option=optionById(question,answers&&answers.goal);if(!option||!option.ownerId)return {error:'Choose a terminal outcome before continuing.'};var prompt=PROMPTS.find(function(p){return p.id===option.ownerId});if(!prompt)return {error:'Registered outcome owner '+option.ownerId+' is missing from this Prompt Kit build.'};if(!promptFinderRouteIsActionable(prompt))return {error:'Registered outcome owner '+option.ownerId+' does not currently expose an actionable output/proof/next-step contract.'};return {prompt:prompt,option:option}}\nfunction scorePromptFinderAnswers(answers){var route=resolvePromptFinderOutcome(answers),scores={},reasons={},out=[];if(route.error){out.routeError=route.error;return out}Object.keys(answers).forEach(function(questionId){var question=questionById(questionId),option=optionById(question,answers[questionId]);if(!option)return;(option.queries||[]).forEach(function(query){sharedSearch(query).slice(0,5).forEach(function(prompt,index){if(prompt.id===route.prompt.id)return;var id=prompt.id,points=10-(index*2);scores[id]=(scores[id]||0)+Math.max(points,2);(reasons[id]||(reasons[id]=[])).push(option.label)})})});var follow=Object.keys(scores).map(function(id){var prompt=PROMPTS.find(function(p){return p.id===id});return prompt&&promptFinderRouteIsActionable(prompt)?{prompt:prompt,score:scores[id],reasons:Array.from(new Set(reasons[id]))}:null}).filter(Boolean).sort(function(a,b){return b.score-a.score||rank(a.prompt)-rank(b.prompt)}).slice(0,2);return [{prompt:route.prompt,score:Number.MAX_SAFE_INTEGER,reasons:[route.option.label],outcome:route.option}].concat(follow)}"
    text = require_replace(text, old_score, new_score, "finder scorer")
    old_card = "function card(item,i){var p=item.prompt,label=i===0?'Primary recommendation':'Follow-on option';return '<article class=\"finder-result'+(i===0?' primary':'')+'\"><small>'+label+'</small><h3><span>'+escapePromptHtml(p.id)+'</span> '+escapePromptHtml(p.name)+'</h3><p>'+escapePromptHtml(item.reasons.join(' · '))+'</p><div><button data-finder-open=\"'+p.id+'\">Open</button><button data-finder-copy=\"'+p.id+'\">Copy</button></div></article>'}"
    new_card = "function card(item,i){var p=item.prompt,label=i===0?'Outcome owner':'Context follow-on',terminal=i===0&&item.outcome?'<p><strong>Terminal outcome:</strong> '+escapePromptHtml(item.outcome.terminal)+'</p>':'';return '<article class=\"finder-result'+(i===0?' primary':'')+'\"><small>'+label+'</small><h3><span>'+escapePromptHtml(p.id)+'</span> '+escapePromptHtml(p.name)+'</h3><p>'+escapePromptHtml(item.reasons.join(' · '))+'</p>'+terminal+'<div><button data-finder-open=\"'+p.id+'\">Open owner</button><button data-finder-copy=\"'+p.id+'\">'+(i===0?'Copy & start':'Copy')+'</button></div></article>'}"
    text = require_replace(text, old_card, new_card, "finder card")
    old_results = "function renderPromptFinderResults(){var results=scorePromptFinderAnswers(S.answers),body='<p class=\"finder-intro\">These recommendations use the same registry, synonym, metadata, and search-ranking logic as the main Prompt Kit. Start with the primary prompt.</p>';if(results.length)results.forEach(function(x,i){body+=card(x,i)});else body+='<p>No registered prompt matched strongly enough. Search for P65 for the conversational fallback.</p>';"
    new_results = "function renderPromptFinderResults(){var results=scorePromptFinderAnswers(S.answers),body='<p class=\"finder-intro\">Your declared terminal outcome selects the canonical owner. The other answers use shared search only to refine context follow-ons; they cannot displace the outcome owner.</p>';if(results.routeError)body+='<p class=\"finder-route-error\">'+escapePromptHtml(results.routeError)+' Use P65 for a conversational fallback; do not silently substitute P07.</p>';else if(results.length)results.forEach(function(x,i){body+=card(x,i)});else body+='<p>No actionable registered outcome owner is available. Search for P65 for the conversational fallback.</p>';"
    text = require_replace(text, old_results, new_results, "finder result text")
    old_export = "window.closePromptFinder=function(){closePromptDetail()};window.openPromptFinder=openPromptFinder;window.scorePromptFinderAnswers=scorePromptFinderAnswers;window.PROMPT_FINDER_QUESTIONS=PROMPT_FINDER_QUESTIONS;"
    new_export = "window.closePromptFinder=function(){closePromptDetail()};window.openPromptFinder=openPromptFinder;window.scorePromptFinderAnswers=scorePromptFinderAnswers;window.resolvePromptFinderOutcome=resolvePromptFinderOutcome;window.promptFinderRouteIsActionable=promptFinderRouteIsActionable;window.PROMPT_FINDER_OUTCOMES=PROMPT_FINDER_OUTCOMES;window.PROMPT_FINDER_QUESTIONS=PROMPT_FINDER_QUESTIONS;"
    text = require_replace(text, old_export, new_export, "finder exports")
    path.write_text(text, encoding="utf-8")

    validator = ROOT / "scripts" / "validate_prompt_finder_outcomes.js"
    validator.write_text(
        r'''#!/usr/bin/env node
'use strict';
const fs=require('fs');
const vm=require('vm');
const cp=require('child_process');
const path=require('path');
const root=path.resolve(__dirname,'..');
const py=process.env.PYTHON || process.env.PYTHON3 || 'python';
const registry=JSON.parse(cp.execFileSync(py,['-c',"from scripts import build_prompt_kit_registry; import json; print(json.dumps(build_prompt_kit_registry.load_prompt_kit_registry()))"],{cwd:root,encoding:'utf8'}));
global.PROMPTS=registry;
global.window=global;
global.document={createElement:function(){return {}},head:{appendChild:function(){}},getElementById:function(){return null}};
global.filterPromptsForQuery=function(prompts,query){const q=String(query||'').toLowerCase();return prompts.filter(p=>[p.id,p.name,p.type,p.class,p.useWhen,p.sprintRole].concat(p.keywords||[]).join(' ').toLowerCase().includes(q)).slice(0,8)};
global.escapePromptHtml=function(value){return String(value)};
vm.runInThisContext(fs.readFileSync(path.join(root,'docs/prompt-kit-guided-recommendations.js'),'utf8'));
const outcomes=global.PROMPT_FINDER_OUTCOMES;
if(!Array.isArray(outcomes)||!outcomes.length) throw new Error('no PROMPT_FINDER_OUTCOMES exported');
const byId=new Map(registry.map(p=>[p.id,p]));
const expectedCritical=new Map([['create-prompt','P79'],['prioritize-repos-now','P23'],['implement','P07']]);
const contexts={startingPoint:['new-repo','in-repo','app-open'],problemKnown:['known-failure','known-task','repeated-stall','not-yet'],shape:['one-sprint','parallel','sequential','runtime-proof']};
const repeats=10;
let cases=0;
for(const outcome of outcomes){
  if(!byId.has(outcome.ownerId)) throw new Error(`missing owner ${outcome.ownerId} for ${outcome.id}`);
  const owner=byId.get(outcome.ownerId);
  if(!global.promptFinderRouteIsActionable(owner)) throw new Error(`non-actionable owner ${outcome.ownerId} for ${outcome.id}`);
  if(expectedCritical.has(outcome.id)&&expectedCritical.get(outcome.id)!==outcome.ownerId) throw new Error(`critical owner drift ${outcome.id}: ${outcome.ownerId}`);
  for(const startingPoint of contexts.startingPoint) for(const problemKnown of contexts.problemKnown) for(const shape of contexts.shape) for(let repeat=0;repeat<repeats;repeat++){
    const route=global.resolvePromptFinderOutcome({startingPoint,problemKnown,goal:outcome.id,shape});
    if(route.error) throw new Error(`${outcome.id}: ${route.error}`);
    if(route.prompt.id!==outcome.ownerId) throw new Error(`${outcome.id} routed ${route.prompt.id}, expected ${outcome.ownerId}`);
    cases++;
  }
}
const createRoute=global.resolvePromptFinderOutcome({startingPoint:'in-repo',problemKnown:'known-task',goal:'create-prompt',shape:'one-sprint'});
if(createRoute.error) throw new Error(createRoute.error);
if(createRoute.prompt.id!=='P79') throw new Error(`prompt creation must route P79, got ${createRoute.prompt.id}`);
if(createRoute.prompt.id==='P07') throw new Error('prompt creation silently collapsed to P07');
process.stdout.write(JSON.stringify({schema_version:'prompt-finder-outcome-validation/v1',status:'PASS',outcomes:outcomes.length,repeats,cases,critical:Object.fromEntries(expectedCritical)})+'\n');
''',
        encoding="utf-8",
    )


def strengthen_tutorial_tests() -> None:
    path = ROOT / "tests" / "test_prompt_kit_guidance.py"
    text = path.read_text(encoding="utf-8")
    old = '''    def test_existing_questionnaire_remains_shared_search_driven(self) -> None:
        guided = GUIDED.read_text(encoding="utf-8")
        self.assertIn("filterPromptsForQuery(PROMPTS,query)", guided)
        self.assertIn("slice(0,3)", guided)
        self.assertIn("✦ Tutorial · Find My Prompt", guided)
'''
    new = '''    def test_finder_uses_terminal_outcome_owner_before_shared_search_followons(self) -> None:
        guided = GUIDED.read_text(encoding="utf-8")
        for marker in (
            "What outcome must this tutorial hand you?",
            "ownerId:'P79'",
            "ownerId:'P23'",
            "resolvePromptFinderOutcome",
            "promptFinderRouteIsActionable",
            "PROMPT_FINDER_OUTCOMES",
            "they cannot displace the outcome owner",
            "do not silently substitute P07",
            "filterPromptsForQuery(PROMPTS,query)",
            "slice(0,2)",
            "✦ Tutorial · Find My Prompt",
        ):
            self.assertIn(marker, guided)

    def test_repeated_outcome_route_validator_proves_actionable_terminal_owners(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is not installed in this test environment")
        completed = subprocess.run(
            [node, "scripts/validate_prompt_finder_outcomes.js"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["repeats"], 10)
        self.assertGreaterEqual(receipt["cases"], 1000)
        self.assertEqual(receipt["critical"]["create-prompt"], "P79")
        self.assertEqual(receipt["critical"]["prioritize-repos-now"], "P23")
'''
    text = require_replace(text, old, new, "guidance finder regression")
    path.write_text(text, encoding="utf-8")

    path = ROOT / "tests" / "test_prompt_kit_discovery.py"
    text = path.read_text(encoding="utf-8")
    marker = '            "filterPromptsForQuery(PROMPTS,query)",\n            "PROMPTS.find",\n'
    marker_new = marker + '            "ownerId:\'P79\'",\n            "resolvePromptFinderOutcome",\n            "promptFinderRouteIsActionable",\n'
    text = require_replace(text, marker, marker_new, "discovery outcome assertions")
    path.write_text(text, encoding="utf-8")


def strengthen_docs() -> None:
    path = ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md"
    text = path.read_text(encoding="utf-8")
    text = require_replace(text, "   - **What are you trying to accomplish?** — plan, coordinate, build, AI/agent production hardening, prove, ship, teach, or close out.", "   - **What outcome must this tutorial hand you?** — create/strengthen a Prompt Kit prompt, implement, troubleshoot, verify inherited work, prioritize repositories by current circumstances, publish tutorial docs, prove a change, ship validated work, or close out.", "tutorial outcome wording")
    text = require_replace(text, "4. Review the **Primary recommendation** first. The page may show up to two additional candidates.", "4. Review the **Outcome owner** first. The page may show up to two context follow-ons, but they cannot displace the owner selected by your declared terminal outcome.", "tutorial owner wording")
    text = require_replace(text, "6. Select **Open** to inspect the full prompt or **Copy** to place it on the clipboard.", "6. Select **Open owner** to inspect the full prompt or **Copy & start** to place the canonical owner prompt on the clipboard. Copying routes you to executable work; it does not claim the work is complete.", "tutorial controls")
    old_compute = '''## How recommendations are computed

The browser finder does not maintain a private prompt-ID routing table. Each selected answer contributes ordinary search phrases and passes them through the same `filterPromptsForQuery(PROMPTS, query)` path used by normal Prompt Kit search.

For each phrase, the finder considers the first five shared-search results, gives stronger results more weight, aggregates evidence across the four answers, sorts by score and discovery rank, and returns at most three candidates.

That means the tutorial reuses the current prompt registry, synonyms, metadata, search ranking, and filters rather than creating a second recommendation database. It also means the questionnaire is a routing aid—not an authorization or correctness oracle. If you already know the exact specialist you need, search its ID or exact name directly.
'''
    new_compute = '''## How recommendations are computed

The browser finder separates **terminal outcome ownership** from **context discovery**. The outcome answer names a canonical Prompt Kit owner ID already present in the registry. That owner must exist and expose non-empty copy content, expected output, proof gate, and next-step contract; otherwise the route fails closed to P65 rather than silently substituting P07.

The other answers still contribute ordinary phrases through `filterPromptsForQuery(PROMPTS, query)`. For each phrase, the finder considers the first five shared-search results, but those scores are used only for at most two context follow-ons. Shared-search ranking cannot displace the terminal outcome owner, so the full result returns at most three recommendations.

The key regression case is explicit: **Create or strengthen a Prompt Kit prompt** resolves to **P79 — Prompt Registry Prompt Adder**, regardless of broad surrounding words such as `implement`, `sprint`, or `one bounded sprint`. **Decide which repository should move first right now** resolves to **P23 — Circumstance-Aware Repo Priority Planner**.

This remains a routing aid, not authorization or completion proof. The selected owner must execute its own mission and proof gate.
'''
    text = require_replace(text, old_compute, new_compute, "tutorial computation model")
    common = "| A bounded implementation task is already known | P07 | Executes one owned sprint through validation and delivery. |\n"
    common_new = "| Create or strengthen a Prompt Kit prompt | P79 | Harvests relevant chat context, strengthens canonical owners first, and helper-adds only genuinely missing prompt identities. |\n| Decide which repository should move first under current circumstances | P23 | Separates urgency/access/readiness from structural gap severity. |\n" + common
    text = require_replace(text, common, common_new, "tutorial common routes")
    text = require_replace(text, "python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v\n", "node scripts/validate_prompt_finder_outcomes.js\npython -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v\n", "tutorial validation command")
    text = require_replace(text, "Repository validation can prove registry integrity, the current four-question shared-search implementation, registry-owned next-step extraction,", "Repository validation can prove registry integrity, the current four-question outcome-owner model, repeated terminal-route stability across many context combinations, registry-owned next-step extraction,", "tutorial proof ceiling")
    text = require_replace(text, "Browser recommendations are computed from the current registry and shared search path, while subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.", "Browser outcome ownership is resolved from the current registry, shared search supplies only context follow-ons, and subsequent workflow guidance comes from each selected prompt's current registry-owned `nextStep`.", "tutorial table boundary")
    text = require_replace(text, "A specific inherited-completion claim is an important case that the current four-question browser questionnaire does not represent with a dedicated answer.", "Inherited-completion verification is now an explicit terminal outcome in the four-question browser questionnaire.", "tutorial inherited route")
    text = require_replace(text, "Do not force a broader questionnaire answer such as **known task**, **runtime proof**, or **one sprint** to stand in for the inherited-claim distinction. Prototyping, regression proof, runtime proof, and integration may be later gates after the inherited work has been verified.", "Choose **Verify work another agent says is complete** to route directly to P83. Prototyping, regression proof, runtime proof, and integration may be later gates after the inherited work has been verified.", "tutorial inherited action")
    path.write_text(text, encoding="utf-8")

    path = ROOT / "docs" / "PROMPT_KIT_OPERATOR_GUIDE.md"
    text = path.read_text(encoding="utf-8")
    text = require_replace(text, "   - **What are you trying to accomplish?** — plan, coordinate, build, AI/agent production hardening, prove, ship, teach, or close out.", "   - **What outcome must this tutorial hand you?** — prompt creation/strengthening, implementation, troubleshooting, inherited-work verification, circumstance-aware repo prioritization, tutorial publication, regression proof, integration/release, or closeout.", "operator guide outcome")
    text = require_replace(text, "4. Read the **Primary recommendation** first. The page may show up to two additional candidates.", "4. Read the **Outcome owner** first. The page may show up to two context follow-ons, but context scoring cannot displace the declared outcome owner.", "operator guide owner")
    text = require_replace(text, "5. Use **Open** when you need to inspect the full prompt before committing to it, or **Copy** when you are ready to paste the prompt into a new chat.", "5. Use **Open owner** when you need to inspect the full prompt, or **Copy & start** when you are ready to paste that owner into a new chat and execute it.", "operator guide controls")
    old_compute = '''### What the browser finder actually does

The browser questionnaire is not a hard-coded prompt-ID decision tree. Each selected answer contributes ordinary search phrases. Those phrases are sent through the same `filterPromptsForQuery(PROMPTS, query)` path used by normal Prompt Kit search. For each phrase, the finder scores the first five shared-search results, aggregates evidence across answers, sorts by score/discovery rank, and returns at most three recommendations.

That keeps the finder aligned with the current registry, synonyms, metadata, and search behavior, but it also means the questionnaire is a routing aid rather than an authorization or correctness oracle. When you already know the exact specialist you need, searching its ID or exact name is more precise than intentionally answering broader questions until it appears.
'''
    new_compute = '''### What the browser finder actually does

The finder uses an **outcome-owner contract** for the primary route. The selected terminal outcome resolves to one canonical prompt ID already present in the registry, and that owner must expose actionable copy content, expected output, proof gate, and next-step guidance. Context answers still use `filterPromptsForQuery(PROMPTS, query)`; the first five shared-search results may contribute at most two follow-ons, so the page still returns at most three recommendations. Those context scores cannot replace the outcome owner.

Two canary routes are deliberately protected: **Create or strengthen a Prompt Kit prompt → P79 — Prompt Registry Prompt Adder**, and **Decide which repository should move first right now → P23 — Circumstance-Aware Repo Priority Planner**. If a registered owner is missing or non-actionable, the finder fails closed to P65; it does not silently send the user to P07 merely because broad `implement` or `sprint` terms scored highly.

The questionnaire remains a routing aid rather than authorization or correctness proof. The copied owner still has to execute its own mission and pass its own proof gate.
'''
    text = require_replace(text, old_compute, new_compute, "operator guide computation")
    text = require_replace(text, "The current four-question browser questionnaire does not have a dedicated \"another agent claims this is complete\" answer. In that situation, search **`P83`** or the exact name directly instead of forcing the broader questionnaire to infer the distinction.", "The four-question browser questionnaire now has an explicit **Verify work another agent says is complete** outcome that resolves directly to **P83**. Exact-ID/name search remains available when you already know the specialist.", "operator guide P83")
    text = require_replace(text, "| Finder recommendation feels too generic | Search the exact prompt ID/name, or use P65 conversationally when you truly need another guided selection pass. | A high-ranked finder result is not automatic authorization or proof that adjacent prompts are wrong. |", "| Finder outcome owner is missing, non-actionable, or clearly wrong | Use P65 conversationally and report the exact terminal outcome. The automated route gate treats an owner mismatch as a defect. | Do not keep answering broad questions until P07 appears; context ranking cannot replace the terminal owner. |", "operator troubleshooting")
    text = require_replace(text, "python -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v\n", "node scripts/validate_prompt_finder_outcomes.js\npython -m unittest tests.test_prompt_kit_discovery tests.test_prompt_kit_guidance -v\n", "operator validation command")
    text = require_replace(text, "Repository validation can prove source syntax, finder structure, shared-search routing mechanics,", "Repository validation can prove source syntax, finder structure, deterministic outcome-owner routing plus repeated context-combination checks, shared-search follow-on mechanics,", "operator proof ceiling")
    path.write_text(text, encoding="utf-8")


def strengthen_automation() -> None:
    path = ROOT / "harness" / "test-floor.v1.json"
    floor = json.loads(path.read_text(encoding="utf-8"))
    if "tests/test_prompt_kit_guidance.py" not in floor["self_tests"]:
        floor["self_tests"].append("tests/test_prompt_kit_guidance.py")
        floor["self_tests"].sort()
    path.write_text(json.dumps(floor, indent=2) + "\n", encoding="utf-8")

    path = ROOT / ".github" / "workflows" / "prompt-kit-pages.yml"
    text = path.read_text(encoding="utf-8")
    anchor = "      - name: Validate exact checked-in Prompt Kit\n        run: python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check\n"
    new = "      - name: Prompt Finder terminal-outcome gate\n        run: |\n          node scripts/validate_prompt_finder_outcomes.js\n          python -m unittest tests.test_prompt_kit_guidance -v\n      - name: Validate exact checked-in Prompt Kit\n        run: python scripts/build_prompt_kit_registry.py --output web/prompt-kit/index.html --check\n"
    text = require_replace(text, anchor, new, "pages outcome gate")
    path.write_text(text, encoding="utf-8")


def verify_fixed_point() -> None:
    from scripts import build_prompt_kit_registry

    prompts = {p["id"]: p for p in build_prompt_kit_registry.load_prompt_kit_registry()}
    assert prompts["P79"]["name"] == "Prompt Registry Prompt Adder"
    assert prompts["P23"]["name"] == "Circumstance-Aware Repo Priority Planner"
    assert prompts["P92"]["name"] == "Canonical Path Prompt"
    assert prompts["P114"]["name"] == "Conversation Context Canary & Handoff Guard"
    for phrase in ("EXECUTION CONTEXT RECEIPT BEFORE COMMANDS OR AGENT SELECTION", "A terminal application is not the shell", "EXECUTION_CONTEXT=UNKNOWN"):
        assert phrase in prompts["P92"]["copyContent"], phrase
    assert len(next(p for p in json.loads(REG.read_text(encoding="utf-8"))["prompts"] if p["id"] == "P92")["copyContent"]) < 9000
    for phrase in ("EXECUTION CONTEXT SEMANTICS", "EXEC=<shell>@<kernel/runtime>", "EXEC=UNKNOWN", "Windows Terminal, for example, can host PowerShell"):
        assert phrase in prompts["P114"]["copyContent"], phrase
    guided = (ROOT / "docs" / "prompt-kit-guided-recommendations.js").read_text(encoding="utf-8")
    for phrase in ("id:'create-prompt'", "ownerId:'P79'", "ownerId:'P23'", "resolvePromptFinderOutcome", "promptFinderRouteIsActionable", "they cannot displace the outcome owner"):
        assert phrase in guided, phrase
    assert guided.count("id:'create-prompt'") == 1
    assert guided.count("ownerId:'P79'") == 1
    tutorial = (ROOT / "docs" / "PROMPT_FINDER_QUESTIONNAIRE_TUTORIAL.md").read_text(encoding="utf-8")
    assert "Create or strengthen a Prompt Kit prompt" in tutorial
    assert "P79 — Prompt Registry Prompt Adder" in tutorial
    assert "P23 — Circumstance-Aware Repo Priority Planner" in tutorial
    floor = json.loads((ROOT / "harness" / "test-floor.v1.json").read_text(encoding="utf-8"))
    assert floor["self_tests"].count("tests/test_prompt_kit_guidance.py") == 1
    pages = (ROOT / ".github" / "workflows" / "prompt-kit-pages.yml").read_text(encoding="utf-8")
    assert "Prompt Finder terminal-outcome gate" in pages
    assert "node scripts/validate_prompt_finder_outcomes.js" in pages
    raw = json.loads(REG.read_text(encoding="utf-8"))["prompts"]
    ids = [p["id"] for p in raw]
    assert len(ids) == len(set(ids))
    assert not any(p["name"] == "Prompt Registry Prompt Adder" and p["id"] != "P79" for p in raw)
    print("whole-chat fixed-point PASS: strengthen-only; no new prompt identity")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        strengthen_prompts()
        strengthen_tests()
        strengthen_finder()
        strengthen_tutorial_tests()
        strengthen_docs()
        strengthen_automation()
    verify_fixed_point()


if __name__ == "__main__":
    main()
