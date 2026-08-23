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
        "Use it also when an operator-facing snippet closes the terminal before the human can inspect stdout, stderr, exit status, or failure context.",
    )
    prompt["inspectFirst"] = append_semantic(
        prompt["inspectFirst"],
        "Resolve invocation mode (interactive paste, transient console, child process, or automation/CI), caller-terminal lifetime, and existing log/evidence conventions.",
    )
    prompt["expectedOutput"] = append_semantic(
        prompt["expectedOutput"],
        "Human-run variants remain inspectable without losing the true result; unattended variants preserve nonzero status and durable evidence without blocking for input.",
    )
    prompt["nextStep"] = append_semantic(
        prompt["nextStep"],
        "For a disappearing-terminal incident, reproduce the invocation mode and prove terminal survival plus exit-status preservation.",
    )
    prompt["proofGate"] = append_semantic(
        prompt["proofGate"],
        "Interactive/transient runs remain inspectable, child failure cannot kill the parent shell, unattended runs never hang on a human wait, and result/evidence remain recoverable.",
    )

    section = r'''

OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT
Classify execution as INTERACTIVE_PASTE, TRANSIENT_CONSOLE, CHILD_PROCESS, or AUTOMATION_CI. Closing the terminal before stdout/stderr/status inspection is a defect.
- INTERACTIVE_PASTE / CHILD_PROCESS: no top-level `exit` or process-kill just to propagate failure; preserve status and keep the parent shell alive.
- TRANSIENT_CONSOLE: if inspection is needed, save exit code first, then use a native wait (`pause`/`cmd /k`, PowerShell `-NoExit`/`Read-Host`) and show status/log evidence.
- AUTOMATION_CI: never wait for human input; propagate nonzero status and durable logs.
Waits are inspection aids, not error handling. Intentional session end must preserve evidence first.
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
    for index, prompt in enumerate(prompts):
        if prompt.get("id") == "P90":
            prompts[index] = strengthened
            break
    else:
        raise SystemExit("P90 replacement failed")

    prompts.sort(key=lambda p: int(str(p["seq"])))
    data["prompts"] = prompts
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"canonical registry now contains {len(prompts)} source prompts in this registry")
    print(f"P90 raw copyContent chars={len(strengthened['copyContent'])}")


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
        for phrase in (
            "ARCHITECTURE BOUNDARY — HOST STAYS IN CONTROL",
            "COMMAND CLASSES TO EXERCISE",
            "wrong-shell syntax",
            "HOST ENFORCEMENT",
            "SCAN -> LUA FLAGS -> HOST BLOCK/RAISE -> AGENT REPAIR -> REVALIDATE",
            "CHECKER_FAILURE",
        ):
            self.assertIn(phrase, content)
        for phrase in (
            "OPERATOR OBSERVABILITY / TERMINAL-LIFETIME CONTRACT",
            "INTERACTIVE_PASTE",
            "TRANSIENT_CONSOLE",
            "CHILD_PROCESS",
            "AUTOMATION_CI",
            "no top-level `exit`",
            "preserve status and keep the parent shell alive",
            "save exit code first",
            "never wait for human input",
            "Waits are inspection aids, not error handling",
        ):
            self.assertIn(phrase, content)
        self.assertIn("terminal", prompt["useWhen"].lower())
        self.assertIn("invocation mode", prompt["inspectFirst"].lower())
        self.assertIn("unattended", prompt["proofGate"].lower())
        self.assertIn("terminal stays open", prompt["keywords"])
        self.assertIn("preserve exit code", prompt["keywords"])
        self.assertGreater(len(raw_content), 5000)
        self.assertLess(len(raw_content), 8000)
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
