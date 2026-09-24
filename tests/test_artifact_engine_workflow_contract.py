from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "artifact-engines.yml"
CORE_WORKFLOWS = (
    ROOT / ".github" / "workflows" / "artifact-engines.yml",
    ROOT / ".github" / "workflows" / "app-harness-validation.yml",
    ROOT / ".github" / "workflows" / "deterministic-test-floor.yml",
    ROOT / ".github" / "workflows" / "harness-contract.yml",
    ROOT / ".github" / "workflows" / "prompt-kit-pages.yml",
)


class ArtifactEngineWorkflowContractTests(unittest.TestCase):
    def test_workflow_is_single_read_only_artifact_engine_lane(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        jobs_text = workflow.split("\njobs:\n", 1)[1]
        job_ids = re.findall(r"^  ([A-Za-z0-9_-]+):\s*$", jobs_text, flags=re.MULTILINE)

        self.assertEqual(["artifact-engines"], job_ids)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn(".prompt-contrib", workflow)
        self.assertNotIn("canonical-local-path-prompt-repair", workflow)
        self.assertNotIn("hierarchy-state-transition-repair", workflow)
        self.assertNotIn("p65-verifier-routing-repair", workflow)

    def test_workflow_pins_exact_candidate_and_current_node24_actions(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("uses: actions/checkout@v7", workflow)
        self.assertIn("uses: actions/setup-python@v7", workflow)
        self.assertIn("ref: ${{ github.event.pull_request.head.sha || github.sha }}", workflow)
        self.assertIn("EXPECTED_SHA: ${{ github.event.pull_request.head.sha || github.sha }}", workflow)
        self.assertIn('test "$actual" = "$EXPECTED_SHA"', workflow)
        self.assertIn("fetch-depth: 1", workflow)

    def test_workflow_uses_pinned_repository_test_floor_dependencies(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("python -m pip install -r requirements-test-floor.txt", workflow)
        self.assertNotIn("python -m pip install -r requirements.txt", workflow)
        self.assertNotIn("python -m pip install --upgrade pip", workflow)
        self.assertIn("-q -rs", workflow)

    def test_active_core_ci_uses_node24_backed_action_majors(self) -> None:
        forbidden = (
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "actions/upload-artifact@v4",
        )
        for path in CORE_WORKFLOWS:
            text = path.read_text(encoding="utf-8")
            with self.subTest(workflow=path.name):
                for marker in forbidden:
                    self.assertNotIn(marker, text)
                if "actions/checkout@" in text:
                    self.assertIn("actions/checkout@v7", text)
                if "actions/setup-python@" in text:
                    self.assertIn("actions/setup-python@v7", text)
                if "actions/upload-artifact@" in text:
                    self.assertIn("actions/upload-artifact@v7", text)

    def test_pages_ci_uses_current_node24_backed_pages_actions(self) -> None:
        pages = (ROOT / ".github" / "workflows" / "prompt-kit-pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/configure-pages@v6", pages)
        self.assertIn("actions/upload-pages-artifact@v5", pages)
        self.assertIn("actions/deploy-pages@v5", pages)


if __name__ == "__main__":
    unittest.main()
