from __future__ import annotations

from pathlib import Path

import pytest

from triage.prompt_kit_v38_prompt_assets import (
    DEFAULT_SOURCE,
    OUTPUT_FILENAME,
    PROMPT_CLASS,
    PROMPT_ID,
    materialize_prompt_assets,
    validate_prompt_text,
)


def test_local_runtime_prompt_is_agent_neutral_executable_and_directory_safe(tmp_path: Path) -> None:
    assets = materialize_prompt_assets(tmp_path)

    assert len(assets) == 1
    asset = assets[0]
    assert asset.prompt_id == PROMPT_ID
    assert asset.prompt_class == PROMPT_CLASS
    assert asset.validation_passed is True
    assert asset.supported_agents == (
        "Cosmos by Augment",
        "Cursor",
        "Codex",
        "other local coding agents",
    )

    output = tmp_path / OUTPUT_FILENAME
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "Do not merely factor" in text
    assert "Build the local runtime surface" in text
    assert "Execute locally" in text
    assert "git rev-parse --show-toplevel" in text
    assert "Do not stop after creating scripts" in text
    assert "LOCAL RUNTIME PROOF" in text
    assert output.read_text(encoding="utf-8") == DEFAULT_SOURCE.read_text(encoding="utf-8").rstrip() + "\n"


def test_local_runtime_prompt_rejects_factoring_only_payload() -> None:
    with pytest.raises(ValueError, match="missing required markers"):
        validate_prompt_text("Factor this sprint into prompts and return a plan.")


def test_local_runtime_prompt_rejects_deferred_work_language() -> None:
    text = DEFAULT_SOURCE.read_text(encoding="utf-8") + "\nSit tight while I finish later.\n"
    with pytest.raises(ValueError, match="forbidden markers"):
        validate_prompt_text(text)
