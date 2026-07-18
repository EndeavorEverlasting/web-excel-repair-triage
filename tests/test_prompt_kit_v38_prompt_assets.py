from __future__ import annotations

import json
from pathlib import Path

import pytest

from triage.prompt_kit_v38_prompt_assets import (
    DEFAULT_REGISTRY,
    DEFAULT_SOURCE,
    OUTPUT_FILENAME,
    PROMPT_CLASS,
    PROMPT_ID,
    load_prompt_registry,
    materialize_prompt_assets,
    validate_prompt_text,
)


def test_local_runtime_prompt_is_registry_backed_executable_and_directory_safe(tmp_path: Path) -> None:
    definitions = load_prompt_registry()
    assert len(definitions) == 1
    definition = definitions[0]
    assert definition.prompt_id == PROMPT_ID
    assert definition.prompt_class == PROMPT_CLASS
    assert definition.execution_mode == "local_runtime_build"
    assert definition.source == DEFAULT_SOURCE
    assert definition.output_filename == OUTPUT_FILENAME
    assert definition.distinct_from == ("harness_factoring", "prompt_authoring")
    assert definition.requires_local_access is True
    assert definition.requires_runtime_execution is True

    assets = materialize_prompt_assets(tmp_path)
    assert len(assets) == 1
    asset = assets[0]
    assert asset.prompt_id == PROMPT_ID
    assert asset.prompt_class == PROMPT_CLASS
    assert asset.execution_mode == "local_runtime_build"
    assert asset.validation_passed is True
    assert asset.distinct_from == ("harness_factoring", "prompt_authoring")
    assert asset.registry == str(DEFAULT_REGISTRY.resolve())
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
    assert text == DEFAULT_SOURCE.read_text(encoding="utf-8").rstrip() + "\n"


def test_registry_rejects_runtime_prompt_without_factoring_separation(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    payload["prompt_assets"][0]["distinct_from"] = ["prompt_authoring"]
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="distinct from harness_factoring"):
        load_prompt_registry(registry)


def test_registry_rejects_nonlocal_execution_contract(tmp_path: Path) -> None:
    payload = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    payload["prompt_assets"][0]["requires_runtime_execution"] = False
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="require runtime execution"):
        load_prompt_registry(registry)


def test_local_runtime_prompt_rejects_factoring_only_payload() -> None:
    with pytest.raises(ValueError, match="missing required markers"):
        validate_prompt_text("Factor this sprint into prompts and return a plan.")


def test_local_runtime_prompt_rejects_deferred_work_language() -> None:
    text = DEFAULT_SOURCE.read_text(encoding="utf-8") + "\nSit tight while I finish later.\n"
    with pytest.raises(ValueError, match="forbidden markers"):
        validate_prompt_text(text)
