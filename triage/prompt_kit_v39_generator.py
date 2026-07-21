"""Generate V39 with semantic segmentation and commit-required core actions.

The accepted segmented implementation is preserved in
``_prompt_kit_v39_generator_legacy``. This canonical wrapper hardens inherited
prompts whose workbook labels claim action while their payloads previously
allowed acknowledgment-only completion. P00 is the first registered repair.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence

from . import _prompt_kit_v39_generator_legacy as _legacy
from . import harness_operational_discipline as harness_discipline
from . import prompt_kit_v39_ooxml_base as ooxml
from . import prompt_kit_visual_contract as visual_contract

ARTIFACT_NAME = _legacy.ARTIFACT_NAME
DEFAULT_OUTPUT_DIR = _legacy.DEFAULT_OUTPUT_DIR
DEFAULT_STANDARD_AI_SPEC = _legacy.DEFAULT_STANDARD_AI_SPEC
DEFAULT_GNHF_SPEC = _legacy.DEFAULT_GNHF_SPEC
SOURCE_PROMPT_IDS = _legacy.SOURCE_PROMPT_IDS
STANDARD_AI_EXTENSION_IDS = _legacy.STANDARD_AI_EXTENSION_IDS
GNHF_HARNESS_IDS = _legacy.GNHF_HARNESS_IDS
APPEND_ORDER = _legacy.APPEND_ORDER
EXPECTED_PROMPT_ORDER = _legacy.EXPECTED_PROMPT_ORDER
V39SegmentedReport = _legacy.V39SegmentedReport

DEFAULT_CORE_ACTION_SPEC = Path("configs/prompt_kit/v39_core_prompt_action_overrides.json")
CORE_ACTION_PROMPT_IDS = ("P00",)


def _load_core_action_contract(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("core action prompt source requires schema_version 1")
    policy = payload.get("policy")
    prompts = payload.get("prompts")
    if not isinstance(policy, dict) or not isinstance(prompts, list):
        raise ValueError("core action prompt source requires policy and prompts")
    prompt_ids = tuple(item.get("prompt_id") for item in prompts)
    if prompt_ids != CORE_ACTION_PROMPT_IDS:
        raise ValueError(f"core action prompt source must define exactly {list(CORE_ACTION_PROMPT_IDS)}")
    required_markers = policy.get("required_action_markers")
    forbidden_shapes = policy.get("forbidden_completion_shapes")
    if not isinstance(required_markers, list) or not required_markers:
        raise ValueError("core action policy requires action markers")
    if not isinstance(forbidden_shapes, list) or not forbidden_shapes:
        raise ValueError("core action policy requires forbidden completion shapes")
    for prompt in prompts:
        prompt_id = str(prompt.get("prompt_id", ""))
        lines = prompt.get("lines")
        if prompt.get("surface_family") != "standard_ai":
            raise ValueError(f"{prompt_id} must remain a standard-AI surface")
        if prompt.get("execution_shape") != "repo_mutation":
            raise ValueError(f"{prompt_id} must require repository mutation")
        if prompt.get("use_for_progress") != "YES":
            raise ValueError(f"{prompt_id} must be progress-bearing after claiming installation")
        if not isinstance(lines, list) or len(lines) < 2 or any(not isinstance(line, str) for line in lines):
            raise ValueError(f"{prompt_id} requires a non-empty string line list")
        for field in ooxml.LIBRARY_FIELDS.values():
            if field == "sheet_name":
                continue
            if not str(prompt.get(field, "")).strip():
                raise ValueError(f"{prompt_id} requires library field {field}")
        text = "\n".join(lines)
        if not text.startswith("INSTALL THE HARNESS DOCTRINE NOW."):
            raise ValueError(f"{prompt_id} must begin with an imperative installation command")
        if "DO NOT MERELY ACKNOWLEDGE" not in lines[0]:
            raise ValueError(f"{prompt_id} must reject acknowledgment-only completion on its first line")
        missing = [marker for marker in required_markers if marker not in text]
        if missing:
            raise ValueError(f"{prompt_id} action contract is missing markers: {missing}")
        for shape in forbidden_shapes:
            if shape not in text:
                raise ValueError(f"{prompt_id} must explicitly reject completion shape: {shape}")
        if "commit" not in str(prompt["expected_output"]).lower() or "commit" not in str(prompt["proof_gate"]).lower():
            raise ValueError(f"{prompt_id} expected output and proof gate must require commit evidence")
    return payload


def _library_row_values(prompt: Mapping[str, object]) -> dict[str, str]:
    values = {key: str(prompt.get(key, "")) for key in ooxml.LIBRARY_FIELDS.values()}
    values["sheet_name"] = f"{prompt['prompt_id']}_COPY_SAFE"
    return values


def _replace_library_prompt_row(root, header_columns: Mapping[str, int], prompt_rows: Mapping[str, int], prompt: Mapping[str, object]) -> None:
    prompt_id = str(prompt["prompt_id"])
    row_number = prompt_rows[prompt_id]
    rows = {int(row.attrib.get("r", "0")): row for row in root.findall("m:sheetData/m:row", ooxml.NS)}
    row = rows[row_number]
    values = _library_row_values(prompt)
    prompt_range = f"A1:A{len(prompt['lines'])}"
    hyperlink_updates: dict[str, tuple[str, str]] = {}
    for header, field in ooxml.LIBRARY_FIELDS.items():
        column = ooxml._impl._column_name(header_columns[header])
        ref = f"{column}{row_number}"
        value = values[field]
        formula = None
        if field == "prompt_id":
            formula = f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!{prompt_range}","{prompt_id}")'
            hyperlink_updates[ref] = (f"'{prompt_id}_COPY_SAFE'!{prompt_range}", prompt_id)
        elif field == "sheet_name":
            formula = f'HYPERLINK("#\'{prompt_id}_COPY_SAFE\'!{prompt_range}","{value}")'
            hyperlink_updates[ref] = (f"'{prompt_id}_COPY_SAFE'!{prompt_range}", value)
        ooxml._replace_row_cell(row, ref, formula=formula, cached=value)
    links = ooxml._impl._hyperlinks_element(root)
    by_ref = {item.attrib.get("ref"): item for item in links.findall("m:hyperlink", ooxml.NS)}
    for ref, (location, display) in hyperlink_updates.items():
        item = by_ref.get(ref)
        if item is None:
            item = ooxml.ET.SubElement(links, f"{{{ooxml.MAIN_NS}}}hyperlink")
        item.attrib.update({"ref": ref, "location": location, "display": display})


def _update_reference_row(root, shared: Sequence[str], anchor: str, replacements: Mapping[str, str]) -> bool:
    matching_rows = []
    for row in root.findall("m:sheetData/m:row", ooxml.NS):
        cells = list(row.findall("m:c", ooxml.NS))
        displays = [ooxml._cell_display(cell, shared) for cell in cells]
        if anchor in displays:
            matching_rows.append((row, cells, displays))
    if len(matching_rows) != 1:
        raise ValueError(f"reference sheet requires exactly one row anchored by {anchor!r}; found {len(matching_rows)}")
    row, cells, displays = matching_rows[0]
    changed = False
    for cell, display in zip(cells, displays):
        if display not in replacements:
            continue
        ooxml._replace_row_cell(row, cell.attrib["r"], formula=None, cached=replacements[display])
        changed = True
    return changed


def _apply_reference_repairs(parts: MutableMapping[str, bytes], mapping: Mapping[str, str]) -> set[str]:
    changed: set[str] = set()
    repairs = (
        ("START_HERE", "P00", {
            "Install baseline behavior": "Install and commit baseline doctrine",
            "Sets universal harness discipline.": "Writes universal harness discipline into repo-owned doctrine and enforces it.",
            "No repo mutation.": "Commit-required bounded doctrine mutation.",
            "Use task prompt.": "Use the task prompt after the doctrine commit.",
            "Rules active.": "Doctrine file, validator, passing checks, commit SHA, and push or PR evidence.",
            "No": "YES",
        }),
        ("Prompt_Class_Legend", "P00-P01", {
            "No/Support": "YES/Support",
            "Rules and harness surfaces exist": "P00 doctrine commit and P01 harness surfaces exist",
            "Setup and doctrine; establishes the baseline without claiming sprint progress.": "P00 commits doctrine; P01 builds the broader repo-local harness.",
        }),
        ("Import_Checklist", "P00", {
            "Install baseline harness discipline": "Install and commit baseline harness doctrine",
            "AGENTS.md / custom instructions": "Repo-native doctrine file, validator, commit/PR evidence",
            "Keep task prompts authoritative": "Acknowledgment-only completion is invalid",
        }),
        ("Prompt_Sequence", "P00", {
            "Use this to set model behavior across all repo work.": "Install repository doctrine that governs subsequent repo work.",
            "You need repo-specific execution now.": "Repository mutation is forbidden or no writable doctrine authority exists.",
            "Stable harness behavior baseline.": "Tracked doctrine and validator committed and pushed or attached to a PR.",
            "Then use 02/14/07 depending on state.": "Then use the task-specific prompt after the doctrine commit.",
            "Rules are stored or visible before repo work.": "Tracked rules, validator, passing checks, commit SHA, and push or PR evidence.",
            "No": "YES",
            "Permanent rules, repo-local harness doctrine, and baseline behavior.": "P00 installs committed doctrine; P01 builds the broader harness.",
        }),
    )
    for sheet_name, anchor, replacements in repairs:
        part = mapping.get(sheet_name)
        if not part:
            continue
        root = ooxml._root(parts[part], part)
        shared = ooxml._shared_strings(parts)
        if _update_reference_row(root, shared, anchor, replacements):
            parts[part] = ooxml._xml(root)
            changed.add(part)
    return changed


def _apply_core_action_overrides(parts: MutableMapping[str, bytes], contract: Mapping[str, object]) -> set[str]:
    changed: set[str] = set()
    _, mapping, _, _ = ooxml._sheet_map(parts)
    library_part = mapping.get("Prompt_Library")
    if not library_part:
        raise ValueError("missing Prompt_Library while applying core action overrides")
    library_root, headers, prompt_rows, _, _ = ooxml._find_library_rows(parts, library_part)
    for prompt in contract["prompts"]:
        prompt_id = str(prompt["prompt_id"])
        sheet_part = mapping.get(f"{prompt_id}_COPY_SAFE")
        if not sheet_part or prompt_id not in prompt_rows:
            raise ValueError(f"missing registered core prompt {prompt_id}")
        parts[sheet_part] = ooxml._make_prompt_sheet(parts[sheet_part], prompt, prompt_rows[prompt_id])
        changed.add(sheet_part)
        _replace_library_prompt_row(library_root, headers, prompt_rows, prompt)
    ooxml._apply_prompt_library_row_links(library_root, ooxml._shared_strings(parts))
    parts[library_part] = ooxml._xml(library_root)
    changed.add(library_part)
    changed.update(_apply_reference_repairs(parts, mapping))
    if ooxml._rebuild_calc_chain(parts):
        changed.add("xl/calcChain.xml")
    return changed


def _rewrite_workbook(workbook: Path, contract: Mapping[str, object]) -> tuple[str, ...]:
    package = ooxml._read_workbook(workbook)
    parts = dict(package.parts)
    changed = _apply_core_action_overrides(parts, contract)
    placeholder_changed, _ = ooxml._normalize_prompt_placeholders(parts)
    visual_changed, _ = ooxml._apply_prompt_visual_coordination(parts)
    scaffold_changed, scaffold_report = ooxml._apply_prompt_body_scaffold(parts)
    changed.update(placeholder_changed)
    changed.update(visual_changed)
    changed.update(scaffold_changed)
    if ooxml._rebuild_calc_chain(parts):
        changed.add("xl/calcChain.xml")
    with tempfile.NamedTemporaryFile(prefix="v39-action-", suffix=".xlsx", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        ooxml._write_package(package, temporary, parts, ())
        temporary.replace(workbook)
    finally:
        temporary.unlink(missing_ok=True)
    return tuple(sorted(changed))


def _row_displays(parts: Mapping[str, bytes], mapping: Mapping[str, str], sheet_name: str, anchor: str) -> list[str]:
    part = mapping.get(sheet_name)
    if not part:
        return []
    root = ooxml._root(parts[part], part)
    shared = ooxml._shared_strings(parts)
    rows = []
    for row in root.findall("m:sheetData/m:row", ooxml.NS):
        displays = [ooxml._cell_display(cell, shared) for cell in row.findall("m:c", ooxml.NS)]
        if anchor in displays:
            rows.append(displays)
    if len(rows) != 1:
        raise ValueError(f"{sheet_name} requires exactly one row anchored by {anchor!r}; found {len(rows)}")
    return rows[0]


def validate_v39(workbook: str | Path, *, standard_ai_spec: str | Path = DEFAULT_STANDARD_AI_SPEC, gnhf_spec: str | Path = DEFAULT_GNHF_SPEC, core_action_spec: str | Path = DEFAULT_CORE_ACTION_SPEC, changed_parts: Sequence[str] = ()) -> V39SegmentedReport:
    report = _legacy.validate_v39(workbook, standard_ai_spec=standard_ai_spec, gnhf_spec=gnhf_spec, changed_parts=changed_parts)
    findings = list(report.findings)
    try:
        contract = _load_core_action_contract(Path(core_action_spec))
        package = ooxml._read_workbook(Path(workbook))
        parts = package.parts
        _, mapping, _, _ = ooxml._sheet_map(parts)
        rows, ranges = ooxml._prompt_rows_and_ranges(parts)
        library_part = mapping["Prompt_Library"]
        library_root = ooxml._root(parts[library_part], library_part)
        library_cells = ooxml._cells(library_root)
        shared = ooxml._shared_strings(parts)
        findings.extend(ooxml._validate_prompt_library_row_links(library_root, shared))
        findings.extend(ooxml._validate_prompt_placeholder_ergonomics(parts))
        findings.extend(ooxml._validate_prompt_visual_coordination(parts))
        findings.extend(ooxml._validate_prompt_body_scaffold(parts))
        policy = harness_discipline.load_policy()
        for issue in harness_discipline.validate_policy(policy):
            findings.append({"rule": "portable harness operational discipline", "error": issue})
        headers = {ooxml._cell_display(cell, shared): ooxml._impl._column_number(ooxml._cell_parts(ref)[0]) for ref, cell in library_cells.items() if ooxml._cell_parts(ref)[1] == 1}
        for prompt in contract["prompts"]:
            prompt_id = str(prompt["prompt_id"])
            prompt_range = ranges.get(prompt_id)
            sheet_part = mapping.get(f"{prompt_id}_COPY_SAFE")
            if not prompt_range or not sheet_part:
                findings.append({"rule": "core action prompt registered", "prompt": prompt_id})
                continue
            last_row = int(prompt_range.rsplit("A", 1)[-1])
            actual = "\n".join(ooxml._prompt_payload(parts, sheet_part, last_row))
            if actual != "\n".join(prompt["lines"]):
                findings.append({"rule": "core action prompt payload exact", "prompt": prompt_id})
            row = rows[prompt_id]
            values = _library_row_values(prompt)
            for header, field in ooxml.LIBRARY_FIELDS.items():
                column = ooxml._impl._column_name(headers[header])
                actual_value = ooxml._cell_display(library_cells.get(f"{column}{row}"), shared)
                if actual_value != values[field]:
                    findings.append({"rule": "core action Prompt Library metadata", "prompt": prompt_id, "field": field, "expected": values[field], "actual": actual_value})
            root = ooxml._root(parts[sheet_part], sheet_part)
            if root.find("m:sheetProtection", ooxml.NS) is None:
                findings.append({"rule": "core action prompt sheet protected", "prompt": prompt_id})
        reference_expectations = (
            ("START_HERE", "P00", "Commit-required bounded doctrine mutation."),
            ("Prompt_Class_Legend", "P00-P01", "YES/Support"),
            ("Import_Checklist", "P00", "Acknowledgment-only completion is invalid"),
            ("Prompt_Sequence", "P00", "YES"),
        )
        for sheet_name, anchor, marker in reference_expectations:
            if sheet_name in mapping and marker not in _row_displays(parts, mapping, sheet_name, anchor):
                findings.append({"rule": "core action reference repair", "sheet": sheet_name, "missing": marker})
    except (KeyError, ValueError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        findings.append({"rule": "core action contract", "error": str(exc)})
    return replace(report, valid=not findings, changed_parts=tuple(changed_parts), findings=tuple(findings))


def _rewrite_bundle(bundle_path: Path, replacements: Mapping[str, bytes]) -> None:
    with zipfile.ZipFile(bundle_path) as source:
        members = [(info, source.read(info.filename)) for info in source.infolist()]
    with tempfile.NamedTemporaryFile(prefix="v39-bundle-", suffix=".zip", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w") as output:
            seen: set[str] = set()
            for info, data in members:
                name = Path(info.filename).name
                if name in replacements:
                    data = replacements[name]
                    seen.add(name)
                output.writestr(info, data)
            for name, data in replacements.items():
                if name not in seen:
                    output.writestr(name, data)
        temporary.replace(bundle_path)
    finally:
        temporary.unlink(missing_ok=True)


def generate_v39(source: Path, output_dir: Path = DEFAULT_OUTPUT_DIR, *, standard_ai_spec: Path = DEFAULT_STANDARD_AI_SPEC, gnhf_spec: Path = DEFAULT_GNHF_SPEC, core_action_spec: Path = DEFAULT_CORE_ACTION_SPEC) -> dict:
    contract = _load_core_action_contract(Path(core_action_spec))
    policy = harness_discipline.load_policy()
    policy_issues = harness_discipline.validate_policy(policy)
    if policy_issues:
        raise ValueError(f"portable harness policy failed: {list(policy_issues)[:8]}")
    manifest = _legacy.generate_v39(source, output_dir, standard_ai_spec=standard_ai_spec, gnhf_spec=gnhf_spec)
    workbook = Path(manifest["workbook"])
    action_changed = _rewrite_workbook(workbook, contract)
    changed_parts = tuple(sorted(set(manifest["changed_parts"]) | set(action_changed)))
    report = validate_v39(workbook, standard_ai_spec=standard_ai_spec, gnhf_spec=gnhf_spec, core_action_spec=core_action_spec, changed_parts=changed_parts)
    if not report.valid:
        raise ValueError(f"V39 core action commitment failed: {list(report.findings)[:8]}")
    manifest["workbook_sha256"] = _legacy._sha256(workbook)
    manifest["changed_parts"] = list(changed_parts)
    manifest["validation"] = report.to_dict()
    manifest["context_to_artifact_prompt"] = "P56"
    manifest["portable_harness_discipline_prompt"] = "P57"
    manifest["prompt_placeholder_ergonomics"] = {
        "quote_wrapped_xyz_placeholders_allowed": False,
        "replacement_shape": "bare underscore-delimited xyz token",
    }
    manifest["prompt_visual_coordination"] = {
        "row_color_columns": "B:O",
        "semantic_source": "Prompt Library Color label",
        "prompt_tab_color": "matching semantic RGB fill",
        "policy": "configs/harness/prompt_library_visual_policy_v1.json",
    }
    visual_policy = visual_contract.load_policy()
    scaffold_rgb = visual_policy.get("prompt_body_range", {}).get("scaffold_fill", {}).get("rgb", "F8FAFC")
    manifest["prompt_body_scaffold"] = {
        "scaffold_rgb": scaffold_rgb,
        "description": "configurable neutral scaffold fill applied to complete interior body range of every prompt tab",
        "range_detection": "top and bottom navigation rows detected from HYPERLINK formulas referencing Prompt_Library",
        "policy": "configs/harness/prompt_library_visual_policy_v1.json",
    }
    manifest["prompt_library_row_links"] = {
        "columns": "B:O",
        "target": "associated prompt tab exact copy range",
        "display_values_preserved": True,
        "sparse_navigation_columns": ["A", "P"],
        "allowed_sparse_cadences": [10, 5, 2],
    }
    manifest["harness_operational_discipline"] = {
        "policy_id": policy["policy_id"],
        "schema_version": policy["schema_version"],
        "source": str(harness_discipline.DEFAULT_POLICY_PATH),
        "portable": True,
    }
    manifest["core_prompt_action_overrides"] = {
        "prompt_ids": [item["prompt_id"] for item in contract["prompts"]],
        "source": str(Path(core_action_spec).resolve()),
        "policy": contract["policy"]["description"],
        "acknowledgment_only_completion_allowed": False,
    }
    manifest["proof_ceiling"] += " Core prompt action commitment is additionally proven for the registered inherited prompts; repository installation by an agent still requires the target repository's commit and PR evidence."
    manifest_path = workbook.with_name(f"{ARTIFACT_NAME}_manifest.json")
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    _rewrite_bundle(Path(manifest["bundle"]), {workbook.name: workbook.read_bytes(), manifest_path.name: manifest_bytes})
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--standard-ai-spec", type=Path, default=DEFAULT_STANDARD_AI_SPEC)
    parser.add_argument("--gnhf-spec", type=Path, default=DEFAULT_GNHF_SPEC)
    parser.add_argument("--core-action-spec", type=Path, default=DEFAULT_CORE_ACTION_SPEC)
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.source and not args.validate_only:
        parser.error("--source is required unless --validate-only is used")
    try:
        if args.validate_only:
            report = validate_v39(args.validate_only, standard_ai_spec=args.standard_ai_spec, gnhf_spec=args.gnhf_spec, core_action_spec=args.core_action_spec)
            result = report.to_dict()
            valid = report.valid
        else:
            result = generate_v39(args.source, args.out_dir, standard_ai_spec=args.standard_ai_spec, gnhf_spec=args.gnhf_spec, core_action_spec=args.core_action_spec)
            valid = True
    except Exception as exc:
        print(f"V39 segmented generation failed: {exc}")
        return 1
    print(json.dumps(result, indent=2) if args.json or args.validate_only else f"Generated: {result['workbook']}\nBundle: {result['bundle']}")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
