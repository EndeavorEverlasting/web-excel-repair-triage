from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "artifact-engines.yml"


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
        self.assertNotIn("actions/checkout@v4", workflow)
        self.assertNotIn("actions/setup-python@v5", workflow)
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


if __name__ == "__main__":
    unittest.main()
