from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PromptParallelExecutionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = {p["id"]: p for p in json.loads((ROOT / "docs/prompts.json").read_text(encoding="utf-8"))}
        overrides = json.loads((ROOT / "registry/prompts/prompt-overrides.v1.json").read_text(encoding="utf-8"))["overrides"]
        cls.overrides = {p["id"]: p for p in overrides}
        cls.spec = (ROOT / "harness/specs/prompt-operations.md").read_text(encoding="utf-8")

    def test_shared_contract_uses_graph_width_and_capability_ladder(self) -> None:
        for phrase in (
            "Parallel capability ladder and autonomy",
            "no connected self-hosted workers",
            "PARALLEL EXECUTION: NOT_APPLICABLE",
            "PARALLEL EXECUTION: DEGRADED",
            "AUTONOMY_GAP",
            "PARALLEL DISPATCH MANIFEST",
            "Copyable chat panels are portability/recovery fallback only",
        ):
            self.assertIn(phrase, self.spec)

    def test_planners_produce_machine_executable_dispatch_before_human_panels(self) -> None:
        for pid in ("P04", "P59"):
            prompt = self.raw[pid]
            text = prompt["copyContent"]
            self.assertIn("PARALLEL CAPABILITY LADDER / AUTONOMY GATE", text)
            self.assertIn("PARALLEL DISPATCH MANIFEST", text)
            self.assertIn("exact launch action", text.lower())
            self.assertIn("portability", text.lower())
            self.assertIn("operator", text.lower())
            self.assertIn("AUTONOMY_GAP", text)
        self.assertIn("machine-executable PARALLEL DISPATCH MANIFEST", self.raw["P59"]["nextStep"])
        self.assertIn("do not make the operator launch chats", self.raw["P04"]["nextStep"].lower())

    def test_cursor_regression_cannot_stop_at_missing_self_hosted_workers(self) -> None:
        p07 = self.raw["P07"]
        p13 = self.overrides["P13"]
        regression = "no connected self-hosted workers"
        for prompt in (p07, p13):
            text = " ".join(str(prompt.get(k, "")) for k in ("expectedOutput", "nextStep", "proofGate", "copyContent"))
            self.assertIn(regression, text)
            self.assertIn("capability ladder", text.lower())
            self.assertIn("DEGRADED", text)
            self.assertIn("AUTONOMY_GAP", text)
        self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>", p07["copyContent"])
        self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>", p13["copyContent"])

    def test_serial_execution_has_only_two_honest_dispositions(self) -> None:
        p07 = self.raw["P07"]["copyContent"]
        self.assertIn("dependency graph width is 1", p07)
        self.assertIn("parallel proof remains UNPROVEN", p07)
        self.assertIn("serial progress may continue only to avoid deadlock", p07)


if __name__ == "__main__":
    unittest.main()
