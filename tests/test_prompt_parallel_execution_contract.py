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

    def test_shared_contract_uses_graph_width_capability_ladder_and_executable_surfaces(self) -> None:
        for phrase in (
            "Parallel capability ladder and autonomy",
            "no connected self-hosted workers",
            "PARALLEL EXECUTION: NOT_APPLICABLE",
            "PARALLEL EXECUTION: DEGRADED",
            "AUTONOMY_GAP",
            "PARALLEL DISPATCH MANIFEST",
            "Copyable chat panels are machine-readable transport that agents must ingest and dispatch",
            "harness/contracts/prompt-parallel-dispatch.v1.json",
            "scripts/prompt_parallel_dispatch.py",
            "prompt-parallel-dispatch-receipt/v1",
            "manifest-shaped prose",
        ):
            self.assertIn(phrase, self.spec)
        for path in (
            "harness/contracts/prompt-parallel-dispatch.v1.json",
            "scripts/prompt_parallel_dispatch.py",
            ".github/workflows/prompt-parallel-dispatch.yml",
        ):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_planners_materialize_and_validate_dispatch_before_human_panels(self) -> None:
        for pid in ("P04", "P59"):
            prompt = self.raw[pid]
            text = prompt["copyContent"]
            self.assertIn("PARALLEL CAPABILITY LADDER / AUTONOMY GATE", text)
            self.assertIn("PARALLEL DISPATCH MANIFEST", text)
            self.assertIn("EXECUTABLE MANIFEST CONTRACT", text)
            self.assertIn("Outputs/prompt-parallel-dispatch/manifest.json", text)
            self.assertIn("scripts/prompt_parallel_dispatch.py validate", text)
            self.assertIn("scripts/prompt_parallel_dispatch.py run", text)
            self.assertIn("verify-receipt", text)
            self.assertIn("exact launch action", text.lower())
            self.assertIn("portability", text.lower())
            self.assertIn("operator", text.lower())
            self.assertIn("AUTONOMY_GAP", text)
            self.assertLess(text.index("PARALLEL DISPATCH MANIFEST"), text.index("PORTABILITY FALLBACK") if "PORTABILITY FALLBACK" in text else len(text))
        self.assertIn("machine-executable PARALLEL DISPATCH MANIFEST", self.raw["P59"]["nextStep"])
        self.assertIn("do not make the operator launch chats", self.raw["P04"]["nextStep"].lower())
        self.assertIn("smallest tracked plan artifact", self.raw["P04"]["nextStep"])
        self.assertIn("separately owned", self.raw["P04"]["nextStep"])
        self.assertIn("read-only", self.raw["P04"]["nextStep"].lower())
        self.assertIn("2. PARALLEL DISPATCH MANIFEST", self.raw["P04"]["copyContent"])
        self.assertIn("3. COMPACT COORDINATION PREAMBLE", self.raw["P04"]["copyContent"])
        order = self.raw["P04"]["copyContent"].split("OUTPUT ORDER", 1)[-1][:2500]
        self.assertIn("4. PORTABILITY FALLBACK", order)
        self.assertNotIn("3. PORTABILITY FALLBACK", order)
        self.assertNotIn("\\scripts/prompt_parallel_dispatch.py", self.raw["P04"]["nextStep"])
        self.assertIn("`scripts/prompt_parallel_dispatch.py`", self.raw["P04"]["nextStep"])

    def test_cursor_regression_must_continue_past_missing_self_hosted_workers_before_fallback(self) -> None:
        p07 = self.raw["P07"]
        p13 = self.overrides["P13"]
        content = p07["copyContent"]
        regression = "no connected self-hosted workers"
        for prompt in (p07, p13):
            text = " ".join(str(prompt.get(k, "")) for k in ("expectedOutput", "nextStep", "proofGate", "copyContent"))
            self.assertIn(regression, text)
            self.assertIn("capability ladder", text.lower())
            self.assertIn("DEGRADED", text)
            self.assertIn("AUTONOMY_GAP", text)
            self.assertNotIn("PARALLEL EXECUTION: unavailable — <exact capability limitation>", text)
        probe = content.index("Probe execution adapters in order")
        missing_one = content.index(regression)
        dispatch = content.index("At the first safe rung")
        degraded = content.index("If graph width is at least two but every safe rung is genuinely unavailable or blocked")
        self.assertLess(probe, missing_one)
        self.assertLess(missing_one, dispatch)
        self.assertLess(dispatch, degraded)
        self.assertNotIn("no connected self-hosted workers. Proceeding serially", content)
        self.assertNotIn("If no usable mechanism exists", content)

    def test_serial_execution_has_only_conditioned_not_applicable_or_degraded_paths(self) -> None:
        p07 = self.raw["P07"]["copyContent"]
        width_one = "If graph width is one after real dependency/collision analysis, report `PARALLEL EXECUTION: NOT_APPLICABLE — dependency graph width is 1.`"
        exhausted = "If graph width is at least two but every safe rung is genuinely unavailable or blocked, serial progress may continue only to avoid deadlock."
        self.assertIn(width_one, p07)
        self.assertIn(exhausted, p07)
        self.assertIn("Report `PARALLEL EXECUTION: DEGRADED", p07)
        self.assertIn("AUTONOMY_GAP:", p07)
        self.assertIn("parallel proof remains UNPROVEN", p07)
        for contradiction in (
            "PARALLEL EXECUTION: unavailable",
            "proceed serially",
            "Proceeding serially",
            "skip the capability ladder",
        ):
            self.assertNotIn(contradiction, p07)
        self.assertLess(p07.index("At the first safe rung"), p07.index(exhausted))

    def test_p07_requires_receipt_not_manifest_shaped_prose(self) -> None:
        p07 = self.raw["P07"]
        content = p07["copyContent"]
        for phrase in (
            "EXECUTABLE MANIFEST CONTRACT",
            "prose, a lane table, or copy panels alone do not satisfy this gate",
            "Validation without launch is not dispatch proof",
            "observed_parallelism=true",
            "runtime_tool",
            "verify-receipt",
        ):
            self.assertIn(phrase, content)
        self.assertIn("prompt-parallel-dispatch/v1", p07["proofGate"])
        self.assertIn("prompt-parallel-dispatch-receipt/v1", p07["proofGate"])
        self.assertIn("manifest validation alone or prose-only lanes are insufficient", p07["proofGate"])

    def test_parallel_strengthening_preserves_p07_freshness_and_fixed_point_contracts(self) -> None:
        p07 = self.raw["P07"]
        self.assertIn("refreshed and reconciled remote/default-branch floor", p07["expectedOutput"])
        self.assertIn("integrated into the current default branch", p07["expectedOutput"])
        self.assertIn("capability ladder", p07["expectedOutput"].lower())
        self.assertIn("remaining gaps, risks, blockers, proof ceiling, integration state", p07["expectedOutput"].lower())
        self.assertIn("refreshed before implementation", p07["proofGate"])
        self.assertIn("fixed point", p07["proofGate"])
        self.assertIn("readability/editability regression", p07["proofGate"])
        self.assertIn("Closeout is incomplete", p07["proofGate"])
        self.assertIn("Report the current gap/risk/blocker", p07["nextStep"])
        self.assertIn("phase-local exclusions", p07["nextStep"])
        self.assertIn("successor sprint", p07["nextStep"])
        self.assertIn("branch or PR alone is insufficient completion evidence", p07["proofGate"])
        self.assertIn("Strategic follow-on discovery never authorizes unfinished owned work", p07["proofGate"])
        self.assertIn("prompt-parallel-dispatch-receipt/v1", p07["proofGate"])


if __name__ == "__main__":
    unittest.main()
