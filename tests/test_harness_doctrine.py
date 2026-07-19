"""Validate that harness doctrine is installed and connected."""
import os
import re
import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path):
    with open(os.path.join(REPO_ROOT, path), "r", encoding="utf-8") as f:
        return f.read()


class TestHarnessDoctrineInstalled:
    """Verify the AgentSwitchboard harness doctrine is present and connected."""

    def test_harness_md_exists(self):
        assert os.path.exists(os.path.join(REPO_ROOT, "HARNESS.md")), (
            "HARNESS.md must exist"
        )

    def test_agents_md_references_harness(self):
        agents = _read("AGENTS.md")
        assert "HARNESS.md" in agents, (
            "AGENTS.md must reference HARNESS.md"
        )

    def test_harness_contains_sprint_declaration(self):
        harness = _read("HARNESS.md")
        assert "Sprint Declaration" in harness, (
            "HARNESS.md must contain Required Sprint Declaration section"
        )

    def test_harness_contains_executable_loop(self):
        harness = _read("HARNESS.md")
        assert "request -> evidence review" in harness or "request→evidence review" in harness, (
            "HARNESS.md must contain the executable loop"
        )

    def test_harness_contains_action_commitment_rule(self):
        harness = _read("HARNESS.md")
        assert "Action-Commitment Rule" in harness, (
            "HARNESS.md must contain the Action-Commitment Rule"
        )

    def test_harness_contains_forbidden_responses(self):
        harness = _read("HARNESS.md")
        assert "acknowledgment only" in harness, (
            "HARNESS.md must list forbidden responses"
        )

    def test_harness_contains_completion_standard(self):
        harness = _read("HARNESS.md")
        assert "Completion Standard" in harness, (
            "HARNESS.md must contain Completion Standard section"
        )

    def test_harness_contains_capability_rule(self):
        harness = _read("HARNESS.md")
        assert "Capability" in harness and "Authority Rule" in harness, (
            "HARNESS.md must contain Capability and Authority Rule"
        )
