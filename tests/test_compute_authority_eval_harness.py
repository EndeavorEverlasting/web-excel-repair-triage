from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
SCRIPTS = EVAL / "scripts"


class ComputeAuthorityEvalHarnessTests(unittest.TestCase):
    def test_prompt_identities_are_frozen_and_distinct(self) -> None:
        identities = json.loads((EVAL / "prompts" / "identities.json").read_text(encoding="utf-8"))
        self.assertFalse(identities["control"]["markers"]["compute_authority"])
        self.assertFalse(identities["control"]["markers"]["exhaustive_compute"])
        self.assertTrue(identities["treatment"]["markers"]["compute_authority"])
        self.assertTrue(identities["treatment"]["markers"]["exhaustive_compute"])
        self.assertTrue(identities["treatment"]["markers"]["end_state_horizon"])
        self.assertNotEqual(
            identities["control"]["prompt_contract_sha"],
            identities["treatment"]["prompt_contract_sha"],
        )
        for condition in ("control", "treatment"):
            meta = identities[condition]
            body = (ROOT / meta["prompt_path"]).read_text(encoding="utf-8")
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            self.assertEqual(digest, meta["prompt_contract_sha"], condition)

    def test_hidden_manifests_exist_and_are_excluded_from_workspaces(self) -> None:
        for case_id in [f"TC{i:02d}" for i in range(1, 9)]:
            hidden = EVAL / "fixtures" / case_id / "evaluator.manifest.yaml"
            self.assertTrue(hidden.is_file(), case_id)
            ws = EVAL / "fixtures" / case_id / "workspace"
            leaked = [
                p
                for p in ws.rglob("*")
                if p.is_file()
                and p.name
                in {"evaluator.manifest.yaml", "naive_solution_reference.py", "acceptance.py"}
            ]
            self.assertEqual(leaked, [], case_id)
        self.assertTrue(
            (EVAL / "fixtures" / "TC05" / "evaluator" / "naive_solution_reference.py").is_file()
        )
        self.assertTrue((EVAL / "fixtures" / "TC05" / "evaluator" / "acceptance.py").is_file())

    def test_reset_does_not_leak_evaluator_manifest(self) -> None:
        run_id = "harness-reset-smoke"
        run_workspace_parent = EVAL / "runs" / run_id
        if run_workspace_parent.exists():
            shutil.rmtree(run_workspace_parent, ignore_errors=True)
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "reset_fixture.py"),
                "--case",
                "TC01",
                "--run-id",
                run_id,
                "--print-path",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        work = Path(proc.stdout.strip())
        self.assertTrue(work.is_dir())
        self.assertFalse((work / "evaluator.manifest.yaml").exists())
        shutil.rmtree(run_workspace_parent, ignore_errors=True)

    def test_phase_a_fixture_validation_passes(self) -> None:
        out = ROOT / "Outputs" / "compute-authority-fixture-validation.json"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_fixtures.py"),
                "--summary",
                "--output",
                str(out),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
        report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(report["fail_count"], 0)
        self.assertEqual(report["pass_count"], 8)

    def test_aggregate_scaffolding_runs_without_grades(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "aggregate.py"), "--summary"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((EVAL / "aggregate" / "summary.md").is_file())
        self.assertTrue((EVAL / "aggregate" / "statistical-summary.json").is_file())


if __name__ == "__main__":
    unittest.main()
