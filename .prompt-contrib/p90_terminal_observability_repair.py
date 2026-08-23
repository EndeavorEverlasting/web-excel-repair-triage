from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "prompts" / "spec-architecture-prompts.v1.json"
TEST_FILE = ROOT / "tests" / "test_spec_architecture_prompt_registry.py"
P90_NAME = "Lua Flagging + Host Enforcement Repair Loop"
TEST_NAME = "test_p90_command_snippets_preserve_operator_terminal_observability"
HISTORICAL_REFS = (
    "dd4eb11381bc64b46dc7df68cb7d4504d113ee7f",
    "f334b882a641299c22b46d5ff98575f8b6712672",
    "origin/feat/prompt4-lua-host-enforcement-20260821",
)


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    if check and proc.returncode:
        raise SystemExit(proc.returncode)
    return proc


def recover_p90() -> dict:
    for ref in HISTORICAL_REFS:
        proc = run(
            "git",
            "show",
            f"{ref}:registry/prompts/spec-architecture-prompts.v1.json",
            check=False,
        )
        if proc.returncode:
            continue
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            continue
        for prompt in data.get("prompts", []):
            if prompt.get("id") == "P90" and prompt.get("name") == P90_NAME:
                print(f"recovered canonical P90 from {ref}")
                return prompt
    raise SystemExit("accepted P90 owner could not be recovered from known repository history")


def append_semantic(text: str, addition: str) -> str:
    if addition in text:
        return text
    return text.rstrip() + " " + addition


def strengthen(prompt: dict) -> dict:
    prompt = dict(prompt)
    prompt["useWhen"] = append_semantic(
        prompt["useWhen"],
        "Use it also when an otherwise plausible operator-facing snippet closes or replaces the terminal before the human can inspect stdout, stderr, the exit status, or the failure context.",
    )
    prompt["inspectFirst"] = append_semantic(
        prompt["inspectFirst"],
        "Resolve invocation mode (interactive paste, transient/double-click console, child process, or automation/CI), caller-terminal lifetime, current logging/evidence conventions, and whether the operator must inspect the terminal after completion.",
    )
    prompt["expectedOutput"] = append_semantic(
        prompt["expectedOutput"],
        "Operator-facing command variants preserve diagnostic visibility and the true child result without terminating the caller shell, while unattended variants preserve nonzero status and durable evidence without blocking on interactive input.",
    )
    prompt["nextStep"] = append_semantic(
        prompt["nextStep"],
        "When the incident is a disappearing terminal, reproduce the invocation mode explicitly and prove both terminal survival/inspection behavior and exit-status preservation before calling the snippet repaired.",
    )
    prompt["proofGate"] = append_semantic(
        prompt["proofGate"],
        "Operator observability is execution-mode aware: interactive/transient commands remain inspectable, child failures cannot kill the parent shell, unattended jobs never hang on a human pause, and the original result code plus durable diagnostics remain recoverable.",
    )

    section = r'''

OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT
A command can be logically correct and still be a bad operator handoff if the window disappears before the human can inspect what happened. Treat premature terminal loss as a command usability and diagnostic defect, not as harmless presentation. Before emitting or approving an operator-facing snippet, classify how it will run:
- INTERACTIVE_PASTE — pasted into an already-open PowerShell, CMD, Bash, or other interactive shell;
- TRANSIENT_CONSOLE — launched by double-click, Run dialog, temporary terminal window, or wrapper whose console would normally close at process completion;
- CHILD_PROCESS — started by a parent shell/launcher that must survive the child result;
- AUTOMATION_CI — unattended execution where interactive waits are forbidden.

Apply the matching lifetime rule instead of blindly appending `pause` everywhere:
- INTERACTIVE_PASTE: do not use top-level `exit`, `[Environment]::Exit(...)`, `Stop-Process`, `taskkill`, or equivalent process termination merely to propagate failure. Preserve the real command/child status, print the result and diagnostic context, and return/throw/set status through the repository-native boundary without killing the caller's terminal process.
- TRANSIENT_CONSOLE: when human inspection is part of the requested workflow, deliberately keep the terminal available at the terminal state using a shell-appropriate inspection mechanism such as CMD `pause` / `cmd /k`, PowerShell `-NoExit` or a final `Read-Host`, or the platform's existing launcher convention. Capture the real child exit code BEFORE the inspection wait so the pause cannot erase failure truth.
- CHILD_PROCESS: the child may terminate with its real status, but it must not terminate the parent/operator shell. The parent must receive or record the child result and retain the diagnostic surface.
- AUTOMATION_CI: never add `pause`, `Read-Host`, `-NoExit`, or another human wait that can hang an unattended job. Propagate the real nonzero result and persist stdout/stderr or the repository's normal durable log/artifact instead.

For human-run recommendations and copy/paste snippets, default to the operator-survivable form appropriate to the known invocation mode. Show enough terminal context to diagnose the run: what was attempted, the first material failure or final success, the final status/exit code, and the durable log/evidence path when one exists. For longer or failure-prone operations, prefer the repository's existing tee/log/summary mechanism so visible terminal evidence has a durable twin.

Do not hide failures merely to keep a window open. `pause`, `Read-Host`, or `-NoExit` is an inspection aid, not an error handler. Preserve the original result before waiting, and make the eventual continuation/close behavior explicit. If the requested operation intentionally reboots, shuts down, signs out, or otherwise ends the session, preserve evidence first and make that terminal-ending side effect explicit rather than treating it like routine command completion.
'''
    content = prompt["copyContent"]
    if "OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT" not in content:
        marker = "\nHOST ENFORCEMENT\n"
        if marker not in content:
            raise SystemExit("P90 HOST ENFORCEMENT insertion marker not found")
        content = content.replace(marker, section + marker, 1)
    prompt["copyContent"] = content

    keywords = list(prompt.get("keywords", []))
    for keyword in (
        "terminal stays open",
        "terminal closes",
        "terminal crash",
        "operator observable command",
        "interactive shell exit",
        "transient console",
        "powershell noexit",
        "pause after command",
        "preserve exit code",
        "durable command logs",
    ):
        if keyword not in keywords:
            keywords.append(keyword)
    prompt["keywords"] = keywords
    return prompt


def update_registry() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    current = next((p for p in prompts if p.get("id") == "P90"), None)
    if current is None:
        current = recover_p90()
        prompts.append(current)
        print("restored missing accepted P90 identity into current canonical registry")
    elif current.get("name") != P90_NAME:
        raise SystemExit(f"P90 identity collision: {current.get('name')!r}")

    strengthened = strengthen(current)
    replaced = False
    for index, prompt in enumerate(prompts):
        if prompt.get("id") == "P90":
            prompts[index] = strengthened
            replaced = True
            break
    if not replaced:
        raise SystemExit("P90 replacement failed")

    prompts.sort(key=lambda p: int(str(p["seq"])))
    data["prompts"] = prompts
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"canonical registry now contains {len(prompts)} source prompts in this registry")


def update_test() -> None:
    source = TEST_FILE.read_text(encoding="utf-8")
    if TEST_NAME in source:
        print("focused terminal-observability test already present")
        return
    marker = '\n\nif __name__ == "__main__":\n'
    if marker not in source:
        raise SystemExit("focused-test insertion marker not found")
    method = r'''
    def test_p90_command_snippets_preserve_operator_terminal_observability(self) -> None:
        prompt = self.full["P90"]
        content = prompt["copyContent"]
        raw_content = self.raw["P90"]["copyContent"]
        self.assertEqual(prompt["name"], "Lua Flagging + Host Enforcement Repair Loop")
        self.assertEqual(prompt["class"], "HARNESS / LUA HOST ENFORCEMENT")
        self.assertEqual(prompt["profile"], "spec-architecture")
        # Preserve the original P90 command-safety role.
        for phrase in (
            "ARCHITECTURE BOUNDARY — HOST STAYS IN CONTROL",
            "COMMAND CLASSES TO EXERCISE",
            "wrong-shell syntax",
            "HOST ENFORCEMENT",
            "SCAN -> LUA FLAGS -> HOST BLOCK/RAISE -> AGENT REPAIR -> REVALIDATE",
            "CHECKER_FAILURE",
        ):
            self.assertIn(phrase, content)
        # Strengthen operator-visible execution without turning every environment into an interactive wait.
        for phrase in (
            "OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT",
            "INTERACTIVE_PASTE",
            "TRANSIENT_CONSOLE",
            "CHILD_PROCESS",
            "AUTOMATION_CI",
            "do not use top-level `exit`",
            "Capture the real child exit code BEFORE the inspection wait",
            "it must not terminate the parent/operator shell",
            "never add `pause`, `Read-Host`, `-NoExit`",
            "visible terminal evidence has a durable twin",
            "`pause`, `Read-Host`, or `-NoExit` is an inspection aid, not an error handler",
        ):
            self.assertIn(phrase, content)
        self.assertIn("terminal", prompt["useWhen"].lower())
        self.assertIn("invocation mode", prompt["inspectFirst"].lower())
        self.assertIn("unattended", prompt["proofGate"].lower())
        self.assertIn("terminal stays open", prompt["keywords"])
        self.assertIn("preserve exit code", prompt["keywords"])
        self.assertGreater(len(raw_content), 4500)
        self.assertLess(len(raw_content), 10000)
        self.assertEqual(prompt["actionabilityPolicy"], self.policy["policy_id"])
        self.assertIn(self.policy["marker"], content)
        html = build_prompt_kit_registry.render()
        self.assertIn("Lua Flagging + Host Enforcement Repair Loop", html)
'''
    TEST_FILE.write_text(source.replace(marker, "\n" + method + marker, 1), encoding="utf-8")
    print("inserted focused P90 terminal-observability semantic regression")


def main() -> None:
    update_registry()
    update_test()
    run(sys.executable, "scripts/build_prompt_kit_registry.py", "--output", "web/prompt-kit/index.html")


if __name__ == "__main__":
    main()
