#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs" / "prompts.json"
TESTS = ROOT / "tests" / "test_actionable_prompt_registry.py"

raw_text = PROMPTS.read_text(encoding="utf-8")
records = json.loads(raw_text)
p34 = next(prompt for prompt in records if prompt.get("id") == "P34")
if p34.get("name") != "GNHF Technician Experience":
    raise SystemExit("P34 canonical identity changed; refuse blind patch")

p34["sprintRole"] = (
    "Build one clear technician or operator workflow whose launcher, terminal lifecycle, "
    "and evidence remain recoverable after success or failure"
)
p34["useWhen"] = (
    "Users should not need to recover commands from chat, guess the terminal, or hunt for "
    "vanished output after a launcher or shell closes."
)
p34["inspectFirst"] = (
    "Implemented entry points, invocation mode (existing shell versus spawned/double-click), "
    "OS and shell, exit behavior, stdout/stderr handling, persistent log/artifact paths, "
    "docs, examples, and failure modes."
)
p34["expectedOutput"] = (
    "Launcher/help/docs/example commits plus validated terminal-survival and durable-evidence "
    "behavior for success, failure, and noninteractive execution."
)
p34["nextStep"] = (
    "Use P11/P12 and field acceptance only after the human launch path preserves visible "
    "completion/failure evidence without making automation interactive."
)
p34["proofGate"] = (
    "One clear implemented operator path remains; an ephemeral human launcher cannot silently "
    "disappear before acknowledgement; durable logs survive success and failure; noninteractive "
    "paths do not hang; and the original exit status is preserved."
)
p34["copyContent"] = """gnhf `
--agent opencode `
--worktree `
--max-iterations 4 `
--max-tokens 350000 `
--prevent-sleep on `
--stop-when \"The selected operator workflow has one clear validated entry point, human-launched terminals preserve visible completion evidence, durable logs survive success and failure, and no remaining owned usability blocker exists.\" `
\"Repo: xyz_repo_or_path

Sprint: Technician experience
Lane: launcher, help, guide, examples

Audience:
- xyz_audience

Workflow:
- xyz_workflow

Objective:
Turn implemented behavior into one clear operator path that does not require recovering commands or vanished terminal output from chat.

Owned scope:
- xyz_owned_scope

Priorities:
- canonical one-click entry point
- exact OS, shell, and terminal labels
- plan versus apply distinction
- terminal survival for ephemeral human launchers
- durable stdout/stderr, exit-status, log, and artifact locations
- failure and recovery steps
- help, examples, navigation, documentation contracts

TERMINAL SURVIVAL + EVIDENCE PERSISTENCE
1. Classify the invocation before designing the wrapper: command typed in an already-open parent terminal; spawned/double-click human launcher; or automation/CI/noninteractive execution.
2. For a spawned or double-click human PowerShell or Bash launcher, keep the terminal/window open after BOTH success and failure until the operator explicitly acknowledges completion. A child process ending must not make the evidence disappear.
3. Before acknowledgement or exit, persist the relevant stdout/stderr, command/run identity, and real exit status to the repository-approved durable log/output location. Print the final status and exact log path visibly. Do not rely on a transient terminal buffer as the only evidence.
4. Put hold-open behavior at the OUTER HUMAN LAUNCHER boundary only. Do not bury `Read-Host`, `Pause`, `-NoExit`, Bash `read`, or equivalent interaction inside reusable scripts, libraries, CI, remote automation, or commands typed into an already-open shell.
5. Preserve the original process result through transcripts, `tee`, wrappers, and cleanup. A logging or pause layer must not turn failure into success. For shell-specific implementations, prove the real child/command exit code is what the wrapper ultimately reports.
6. If durable logging fails, never silently close an ephemeral human terminal: keep the failure visible and name the logging problem. Noninteractive execution must fail nonzero rather than waiting for input.
7. End the human path with a concise SUCCESS/FAILURE summary, durable log path, and exact recovery/retry command so the operator never has to reconstruct the run from chat.

VALIDATE THE LIFECYCLE
Exercise the practical matrix: success and failure in an existing terminal, an ephemeral human launcher, and noninteractive automation. Prove that the human ephemeral path stays open until acknowledgement, evidence survives afterward, failure status is preserved, and noninteractive runs never hang. Use a test seam or wrapper-level automation rather than requiring a person to wait during CI.

Rules:
- Validate every command and path that can be checked offline.
- Do not invent capabilities or create competing entry points.
- Preserve safe defaults and manual authentication.
- Do not commit routine runtime logs, secrets, or machine-local junk merely to preserve evidence; follow the repository output/artifact policy.
- No elevation, deployment, paid calls, secrets, or live-proof claims unless explicitly owned.

Report:
- usability and terminal-lifecycle gaps repaired
- commits and files
- commands and launcher modes verified
- durable log/artifact location and exit-status proof
- proof ceiling
- field acceptance still required
- git status\""" + "\n" * 24
p34["keywords"] = [
    "technician experience",
    "ux",
    "operator path",
    "operator blockers",
    "user experience",
    "terminal stays open",
    "terminal survival",
    "persistent logs",
    "powershell launcher",
    "bash launcher",
]

serialized = json.dumps(p34, indent=2, ensure_ascii=False)
pattern = re.compile(r'  \{\n    "id": "P34",.*?\n  \},\n  \{\n    "id": "P35",', re.S)
replacement = "  " + serialized.replace("\n", "\n  ") + ",\n  {\n    \"id\": \"P35\","
updated, count = pattern.subn(replacement, raw_text, count=1)
if count != 1:
    raise SystemExit(f"expected one P34 block replacement, got {count}")
PROMPTS.write_text(updated, encoding="utf-8")

text = TESTS.read_text(encoding="utf-8")
method_name = "test_p34_preserves_terminal_evidence_without_hanging_automation"
if method_name not in text:
    anchor = "    def test_policy_rejects_an_empty_next_step(self) -> None:\n"
    if anchor not in text:
        raise SystemExit("focused-test insertion anchor moved")
    method = '''    def test_p34_preserves_terminal_evidence_without_hanging_automation(self) -> None:\n        raw_prompts = json.loads(\n            (REPO_ROOT / "docs" / "prompts.json").read_text(encoding="utf-8")\n        )\n        raw_p34 = next(prompt for prompt in raw_prompts if prompt["id"] == "P34")\n        effective_p34 = {prompt["id"]: prompt for prompt in self.prompts}["P34"]\n\n        self.assertEqual(raw_p34["name"], "GNHF Technician Experience")\n        self.assertEqual(raw_p34["type"], "ENABLEMENT + BUILD")\n        self.assertEqual(raw_p34["class"], "GNHF / TECHNICIAN UX")\n        self.assertEqual(raw_p34["copySheet"], "P34_COPY_SAFE")\n        self.assertEqual(raw_p34["category"], "gnhf")\n\n        for phrase in (\n            "TERMINAL SURVIVAL + EVIDENCE PERSISTENCE",\n            "keep the terminal/window open after BOTH success and failure",\n            "OUTER HUMAN LAUNCHER",\n            "Noninteractive execution must fail nonzero rather than waiting for input",\n            "real exit status",\n            "durable log path",\n            "noninteractive runs never hang",\n            "PowerShell or Bash launcher",\n        ):\n            self.assertIn(phrase, raw_p34["copyContent"])\n\n        self.assertIn("spawned/double-click", raw_p34["inspectFirst"])\n        self.assertIn("original exit status is preserved", raw_p34["proofGate"])\n        self.assertIn("terminal stays open", raw_p34["keywords"])\n        self.assertIn("persistent logs", raw_p34["keywords"])\n        self.assertNotIn(self.policy["marker"], raw_p34["copyContent"])\n        self.assertIn(self.policy["marker"], effective_p34["copyContent"])\n        self.assertNotIn("REMOTE FRESHNESS / BRANCH FLOOR CONTRACT", raw_p34["copyContent"])\n        self.assertLessEqual(len(raw_p34["copyContent"]), 4200)\n\n'''
    text = text.replace(anchor, method + anchor, 1)
    TESTS.write_text(text, encoding="utf-8")

print("P34 terminal-survival hardening staged")
