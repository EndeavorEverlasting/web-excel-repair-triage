"""Focused contract tests for the canonical repository governance file."""
from __future__ import annotations

from pathlib import Path

from triage import governance_contract

ROOT = Path(__file__).parents[1]


def test_canonical_governance_file_exists_is_tracked_and_is_valid() -> None:
    assert governance_contract.validate_repository(ROOT) == ()


def test_validator_rejects_missing_operating_principle() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    mutated = text.replace("**One writer per branch.**", "**Writer isolation.**", 1)
    issues = governance_contract.validate_text(mutated)
    assert any("one writer per branch" in issue for issue in issues)


def test_validator_rejects_reordered_instruction_precedence() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    second = "2. This governance contract."
    third = "3. Task-specific prompts and execution contracts."
    mutated = text.replace(second, "2. Task-specific prompts and execution contracts.", 1)
    mutated = mutated.replace(third, "3. This governance contract.", 1)
    issues = governance_contract.validate_text(mutated)
    assert "instruction precedence order is invalid" in issues


def test_validator_rejects_incomplete_sprint_declaration() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    mutated = text.replace("- proof ceiling;", "- confidence statement;", 1)
    issues = governance_contract.validate_text(mutated)
    assert any("proof ceiling" in issue for issue in issues)


def test_validator_rejects_completion_without_commit_proof() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    mutated = text.replace("- a commit SHA exists for requested repository work;", "", 1)
    issues = governance_contract.validate_text(mutated)
    assert any("commit SHA" in issue for issue in issues)


def test_validator_rejects_secret_exposure_omission() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    mutated = text.replace(
        "- secret, credential, personal-data, private-host, or customer-evidence exposure;",
        "- accidental disclosure;",
        1,
    )
    issues = governance_contract.validate_text(mutated)
    assert any("secret, credential" in issue for issue in issues)


def test_shared_planning_files_are_not_completion_proof() -> None:
    text = (ROOT / "HARNESS.md").read_text(encoding="utf-8")
    assert "plans and handoffs are coordination artifacts, not execution or completion proof" in text.lower()
    assert "competing planning roots are forbidden" in text.lower()
