from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from triage import prompt_kit_v39_generator as base
from triage.prompt_kit_v39_composed_generator import (
    ADVANCED_STANDARD_AI_IDS,
    ARTIFACT_NAME,
    NEW_PROMPT_IDS,
    compose_spec,
    generate_v39,
    validate_v39,
)


def _load_v38_fixture_builder():
    path = Path(__file__).with_name("test_prompt_kit_v39_generator.py")
    module_spec = importlib.util.spec_from_file_location("_v39_base_test_helpers", path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"unable to load V38 fixture helper from {path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module._build_v38


_build_v38 = _load_v38_fixture_builder()
BASE_SPEC = Path(__file__).parents[1] / "configs/prompt_kit/v39_local_first_prompts.json"
REPO_PROMPT_SPEC = Path(__file__).parents[1] / "configs/prompt_kit/v39_github_repo_creation_prompt.json"


def test_composed_spec_places_p50_in_advanced_standard_ai_section() -> None:
    payload = compose_spec(BASE_SPEC, REPO_PROMPT_SPEC)

    assert [item["prompt_id"] for item in payload["new_prompts"]] == list(NEW_PROMPT_IDS)
    sections = {item["id"]: item for item in payload["sections"]}
    assert sections["standard_ai_advanced_local"]["prompt_ids"] == list(ADVANCED_STANDARD_AI_IDS)
    p50 = payload["new_prompts"][-1]
    text = "\n".join(p50["lines"])
    assert p50["surface"] == "standard_ai"
    assert "gh auth status" in text
    assert "gh repo create" in text
    assert "--clone" in text
    assert "--source" in text
    assert "--push" in text
    assert "Never use --show-token" in text
    assert not text.lstrip().startswith("gnhf `")


def test_complete_v39_generates_and_validates_p50(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    output = tmp_path / "out"
    _build_v38(source)

    manifest = generate_v39(
        source,
        output,
        base_spec_path=BASE_SPEC,
        repo_prompt_spec_path=REPO_PROMPT_SPEC,
    )

    workbook = output / f"{ARTIFACT_NAME}.xlsx"
    report = validate_v39(
        workbook,
        base_spec_path=BASE_SPEC,
        repo_prompt_spec_path=REPO_PROMPT_SPEC,
    )
    assert report.valid, report.findings
    assert report.prompt_count == 51
    assert report.new_prompt_ids == NEW_PROMPT_IDS
    assert report.directory_gate_prompts == NEW_PROMPT_IDS
    assert report.zero_token_prompts == ("P46",)
    assert manifest["generator"] == "triage.prompt_kit_v39_composed_generator"
    assert manifest["new_prompt_ids"] == list(NEW_PROMPT_IDS)
    assert manifest["composition"]["repository_creation_prompt"] == "P50"

    package = base._read_workbook(workbook)
    _, mapping, _, _ = base._sheet_map(package.parts)
    rows, ranges = base._prompt_rows_and_ranges(package.parts)
    assert rows["P50"] == rows["P49"] + 1
    assert "P50_COPY_SAFE" in mapping
    last_row = int(ranges["P50"].rsplit("A", 1)[-1])
    payload = "\n".join(base._prompt_payload(package.parts, mapping["P50_COPY_SAFE"], last_row))
    assert "GitHub CLI" in payload
    assert "gh repo create" in payload
    assert "gh repo view" in payload
    assert "DIRECTORY GATE" in payload
    assert not payload.lstrip().startswith("gnhf `")

    with zipfile.ZipFile(workbook) as archive:
        root = ET.fromstring(archive.read("xl/workbook.xml"))
        names = [item.attrib["name"] for item in root.findall(f".//{{{base.MAIN_NS}}}sheet")]
    assert names[-14:] == [f"{prompt_id}_COPY_SAFE" for prompt_id in ADVANCED_STANDARD_AI_IDS]


def test_complete_v39_workbook_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "AI_Harness_Prompt_Kit_v38.xlsx"
    _build_v38(source)

    generate_v39(source, tmp_path / "out1", base_spec_path=BASE_SPEC, repo_prompt_spec_path=REPO_PROMPT_SPEC)
    generate_v39(source, tmp_path / "out2", base_spec_path=BASE_SPEC, repo_prompt_spec_path=REPO_PROMPT_SPEC)

    one = (tmp_path / "out1" / f"{ARTIFACT_NAME}.xlsx").read_bytes()
    two = (tmp_path / "out2" / f"{ARTIFACT_NAME}.xlsx").read_bytes()
    assert one == two
