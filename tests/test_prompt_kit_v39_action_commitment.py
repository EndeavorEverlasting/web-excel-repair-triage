from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from triage import prompt_kit_v39_ooxml_base as ooxml
from triage.prompt_kit_v39_generator import ARTIFACT_NAME, DEFAULT_CORE_ACTION_SPEC, generate_v39, validate_v39

ROOT = Path(__file__).resolve().parents[1]
STANDARD_SPEC = ROOT / "configs/prompt_kit/v39_standard_ai_extensions.json"
GNHF_SPEC = ROOT / "configs/prompt_kit/v39_gnhf_harness_prompts.json"


def _fixture_builder():
    path = ROOT / "tests/test_prompt_kit_v39_generator.py"
    spec = importlib.util.spec_from_file_location("v39_fixture_builder", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._build_v38


def _library_row(parts: dict[str, bytes], prompt_id: str) -> dict[str, str]:
    _, mapping, _, _ = ooxml._sheet_map(parts)
    library_part = mapping["Prompt_Library"]
    root, headers, prompt_rows, _, _ = ooxml._find_library_rows(parts, library_part)
    cells = ooxml._cells(root)
    shared = ooxml._shared_strings(parts)
    row = prompt_rows[prompt_id]
    return {
        header: ooxml._cell_display(cells.get(f"{ooxml._impl._column_name(column)}{row}"), shared)
        for header, column in headers.items()
    }


def test_p00_installs_doctrine_instead_of_acknowledging_it(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _fixture_builder()(source)
    output = tmp_path / "out"
    manifest = generate_v39(source, output, standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC, core_action_spec=DEFAULT_CORE_ACTION_SPEC)
    workbook = output / f"{ARTIFACT_NAME}.xlsx"
    report = validate_v39(workbook, standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC, core_action_spec=DEFAULT_CORE_ACTION_SPEC)
    assert report.valid, report.findings

    package = ooxml._read_workbook(workbook)
    _, mapping, _, _ = ooxml._sheet_map(package.parts)
    _, ranges = ooxml._prompt_rows_and_ranges(package.parts)
    last = int(ranges["P00"].rsplit("A", 1)[-1])
    payload = "\n".join(ooxml._prompt_payload(package.parts, mapping["P00_COPY_SAFE"], last))
    row = _library_row(package.parts, "P00")

    assert payload.startswith("INSTALL THE HARNESS DOCTRINE NOW. DO NOT MERELY ACKNOWLEDGE, SUMMARIZE, OR REPEAT THESE RULES.")
    for marker in (
        "Modify tracked repository files",
        "git diff --check",
        "git commit -m",
        "git push -u origin",
        "Open or update a pull request",
        "exact blocker",
    ):
        assert marker in payload
    for invalid in (
        "acknowledgment only",
        "summary only",
        "rewritten prompt only",
        "plan only",
        "handoff only",
        "preflight only",
    ):
        assert invalid in payload
    assert row["Use For Progress?"] == "YES"
    assert row["Prompt Name"] == "Commit-Required Harness Doctrine Installer"
    assert "committed" in row["Expected Output"].lower()
    assert "commit sha" in row["Proof / Acceptance Gate"].lower()
    assert row["Next Step"].endswith("proven.")
    assert manifest["core_prompt_action_overrides"]["prompt_ids"] == ["P00"]
    assert manifest["core_prompt_action_overrides"]["acknowledgment_only_completion_allowed"] is False


def test_p00_action_contract_fails_closed_when_commit_marker_is_removed(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _fixture_builder()(source)
    payload = json.loads(DEFAULT_CORE_ACTION_SPEC.read_text(encoding="utf-8"))
    prompt = payload["prompts"][0]
    prompt["lines"] = [line for line in prompt["lines"] if "git commit -m" not in line]
    bad = tmp_path / "bad-core-action.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing markers"):
        generate_v39(source, tmp_path / "out", standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC, core_action_spec=bad)


def test_p00_action_contract_fails_closed_when_progress_is_downgraded(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _fixture_builder()(source)
    payload = json.loads(DEFAULT_CORE_ACTION_SPEC.read_text(encoding="utf-8"))
    payload["prompts"][0]["use_for_progress"] = "No"
    bad = tmp_path / "bad-progress.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="progress-bearing"):
        generate_v39(source, tmp_path / "out", standard_ai_spec=STANDARD_SPEC, gnhf_spec=GNHF_SPEC, core_action_spec=bad)
