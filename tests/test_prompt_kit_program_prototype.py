from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs" / "prompt-kit-program-prototype.js"
DESIGN = ROOT / "docs" / "PROMPT_KIT_PROGRAM_ARCHITECTURE.md"


class PromptKitProgramPrototypeTests(unittest.TestCase):
    def run_prototype(self) -> dict:
        result = subprocess.run(
            ["node", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_javascript_syntax_and_executable_seams(self) -> None:
        syntax = subprocess.run(
            ["node", "--check", str(PROTOTYPE)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr or syntax.stdout)

        report = self.run_prototype()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["selectedDesign"], "COMMAND_KERNEL_WITH_OWNED_STATE_AND_PORTS")
        self.assertTrue(all(value == "PASS" for value in report["journeys"].values()))
        self.assertEqual(report["journeys"]["asyncCopyRejection"], "PASS")
        self.assertEqual(report["journeys"]["invalidCommandResult"], "PASS")
        self.assertIn("await execute(command)", report["comparison"]["commandKernel"]["publicExecutionSeam"])
        self.assertIn("precommit/postcommit", report["comparison"]["reducerEffect"]["effectOrdering"])
        self.assertIn("command-heavy", report["comparison"]["decision"])

    def test_async_clipboard_and_result_validation_are_owned_by_kernel_seam(self) -> None:
        text = PROTOTYPE.read_text(encoding="utf-8")
        self.assertIn("async execute(command)", text)
        self.assertIn("validateCommandResult(await handler(command), command.type)", text)
        self.assertIn("await clipboard.writeText(prompt.copyContent)", text)
        self.assertIn("INVALID_COMMAND_RESULT", text)
        self.assertIn("completion telemetry is absent while async clipboard write is pending", text)
        self.assertIn("rejected async clipboard write does not create completion telemetry", text)

    def test_copy_completion_is_terminal_and_inspection_is_not_copy(self) -> None:
        report = self.run_prototype()
        kernel_trace = report["kernelTrace"]

        copy_completions = [
            event
            for event in kernel_trace
            if event.get("layer") == "usage_ledger"
            and event.get("event") == "completion_recorded"
            and event.get("type") == "PROMPT_COPIED"
        ]
        self.assertEqual(len(copy_completions), 2)

        detail_index = next(
            index
            for index, event in enumerate(kernel_trace)
            if event.get("layer") == "surface" and event.get("event") == "detail_opened"
        )
        next_kernel_events = kernel_trace[detail_index : detail_index + 4]
        self.assertFalse(
            any(
                event.get("layer") == "usage_ledger"
                and event.get("type") == "PROMPT_COPIED"
                for event in next_kernel_events
            )
        )

    def test_design_document_separates_program_from_harness_and_build(self) -> None:
        text = DESIGN.read_text(encoding="utf-8")
        required = [
            "## User outcomes",
            "## Domain vocabulary",
            "## Candidate architectures",
            "Candidate B — global reducer + effect runner",
            "Candidate C — command kernel + deep state owners + ports",
            "## Selected module/interface map",
            "## State/data ownership",
            "## Dependency direction",
            "## Failure call stacks",
            "## Second-pass architecture critique",
            "## Feature admission checklist",
            "## Exact implementation seam ready for the next build sprint",
            "## Proof ceiling",
            "governance (`AGENTS.md`",
            "operational harness",
            "full production implementation",
        ]
        for marker in required:
            self.assertIn(marker, text)

        self.assertIn("Terminal value beats intermediate UI", text)
        self.assertIn("Inspection is not completion telemetry", text)
        self.assertIn("Durable preference writes publish after persistence", text)
        self.assertIn("Telemetry is subordinate to user value", text)
        self.assertIn("Promise<CommandResult>", text)
        self.assertIn("do not add Redux", text)
        self.assertIn("do not add a generic event bus", text)


if __name__ == "__main__":
    unittest.main()
