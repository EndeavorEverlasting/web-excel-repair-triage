"""Generate the segmented, package-preserving AI Harness Prompt Kit V39.

V39 extends the operator-accepted V38 workbook without a whole-workbook
serializer. Section ownership is semantic and explicit:

* P50-P57 extend the standard-AI advanced section.
* P45-P49 retain the established GNHF harness/runtime meanings.
* The standard-AI extension is physically inserted before the GNHF block.

Prompt IDs are stable contract identifiers. Numeric order does not override the
section taxonomy or permit repurposing P45-P49.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence
from xml.etree import ElementTree as ET

from . import prompt_kit_v39_ooxml_base as ooxml

ARTIFACT_NAME = "AI_Harness_Prompt_Kit_v39"
DEFAULT_OUTPUT_DIR = Path("Outputs") / "prompt_kit_v39"
DEFAULT_STANDARD_AI_SPEC = Path("configs/prompt_kit/v39_standard_ai_extensions.json")
DEFAULT_GNHF_SPEC = Path("configs/prompt_kit/v39_gnhf_harness_prompts.json")
SOURCE_PROMPT_IDS = tuple(f"P{number:02d}" for number in range(45))
STANDARD_AI_EXTENSION_IDS = tuple(f"P{number:02d}" for number in range(50, 58))
GNHF_HARNESS_IDS = tuple(f"P{number:02d}" for number in range(45, 50))
APPEND_ORDER = STANDARD_AI_EXTENSION_IDS + GNHF_HARNESS_IDS
EXPECTED_PROMPT_ORDER = SOURCE_PROMPT_IDS + APPEND_ORDER


@dataclass(frozen=True)
class V39SegmentedReport:
    path: str
    valid: bool
    prompt_count: int
    standard_ai_extension: tuple[str, ...]
    gnhf_harness_section: tuple[str, ...]
    append_order: tuple[str, ...]
    directory_gate_prompts: tuple[str, ...]
    zero_token_prompts: tuple[str, ...]
    changed_parts: tuple[str, ...]
    findings: tuple[dict, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON prompt source {path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"prompt source requires one schema_version 1 object: {path}")
    return payload


def _validate_prompt_shape(prompt: Mapping[str, object], *, family: str) -> None:
    prompt_id = str(prompt.get("prompt_id", ""))
    lines = prompt.get("lines")
    if not isinstance(lines, list) or not lines or any(not isinstance(line, str) for line in lines):
        raise ValueError(f"{prompt_id} requires a non-empty string line list")
    if prompt.get("surface_family") != family:
        raise ValueError(f"{prompt_id} must belong to {family}")
    text = "\n".join(lines)
    if family == "standard_ai":
        if not text.startswith("PROMPT SURFACE: STANDARD AI."):
            raise ValueError(f"{prompt_id} must declare the standard-AI surface")
        if "DIRECTORY GATE" not in text:
            raise ValueError(f"{prompt_id} must contain a directory gate")
        if text.lstrip().startswith("gnhf `") or "--max-tokens" in text or "--max-iterations" in text:
            raise ValueError(f"{prompt_id} is standard AI but contains GNHF launch markers")
    elif family == "gnhf":
        execution_shape = prompt.get("execution_shape")
        if execution_shape == "gnhf_command":
            required = ("gnhf `", "--max-iterations", "--max-tokens", "--prevent-sleep", "--stop-when")
            missing = [marker for marker in required if marker not in text]
            if missing:
                raise ValueError(f"{prompt_id} is a GNHF command missing markers: {missing}")
        elif execution_shape not in {"compile_only", "local_agent_runtime", "environment_configuration"}:
            raise ValueError(f"{prompt_id} has unsupported GNHF execution shape: {execution_shape!r}")
        if "STANDARD AI. THIS IS NOT" in text:
            raise ValueError(f"{prompt_id} is in the GNHF family but declares the standard-AI surface")


def _load_prompt_contracts(standard_path: Path, gnhf_path: Path) -> tuple[dict, dict, list[dict]]:
    standard = _load_json(standard_path)
    gnhf = _load_json(gnhf_path)
    standard_section = standard.get("section", {})
    gnhf_section = gnhf.get("section", {})
    if standard_section.get("surface_family") != "standard_ai":
        raise ValueError("standard-AI prompt source has the wrong surface family")
    if gnhf_section.get("surface_family") != "gnhf":
        raise ValueError("GNHF prompt source has the wrong surface family")
    if tuple(standard_section.get("prompt_ids", [])) != STANDARD_AI_EXTENSION_IDS:
        raise ValueError(f"standard-AI extension must define {list(STANDARD_AI_EXTENSION_IDS)}")
    if tuple(gnhf_section.get("prompt_ids", [])) != GNHF_HARNESS_IDS:
        raise ValueError(f"GNHF harness section must preserve {list(GNHF_HARNESS_IDS)}")
    standard_prompts = standard.get("prompts")
    gnhf_prompts = gnhf.get("prompts")
    if not isinstance(standard_prompts, list) or tuple(item.get("prompt_id") for item in standard_prompts) != STANDARD_AI_EXTENSION_IDS:
        raise ValueError("standard-AI prompt definitions do not match their section order")
    if not isinstance(gnhf_prompts, list) or tuple(item.get("prompt_id") for item in gnhf_prompts) != GNHF_HARNESS_IDS:
        raise ValueError("GNHF prompt definitions do not match their section order")
    for prompt in standard_prompts:
        _validate_prompt_shape(prompt, family="standard_ai")
    for prompt in gnhf_prompts:
        _validate_prompt_shape(prompt, family="gnhf")
    github = next(item for item in standard_prompts if item["prompt_id"] == "P55")
    github_text = "\n".join(github["lines"])
    required_github = (
        "gh auth status --active --hostname github.com",
        "gh repo create",
        "gh repo view",
        "--clone",
        "--source",
        "--push",
        "Never use --show-token",
    )
    missing = [marker for marker in required_github if marker not in github_text]
    if missing:
        raise ValueError(f"P55 GitHub bootstrap contract is missing: {missing}")
    artifact = next(item for item in standard_prompts if item["prompt_id"] == "P56")
    artifact_text = "\n".join(artifact["lines"])
    required_artifact = (
        "GENERATE THE ACTUAL ARTIFACT",
        "ARTIFACT EXECUTION CONTRACT",
        "actual requested file or files",
        "output path",
        "proof ceiling",
    )
    missing = [marker for marker in required_artifact if marker not in artifact_text]
    if missing:
        raise ValueError(f"P56 context-to-artifact contract is missing: {missing}")
    harness = next(item for item in standard_prompts if item["prompt_id"] == "P57")
    harness_text = "\n".join(harness["lines"])
    required_harness = (
        "INSTALL AND ENFORCE PORTABLE HARNESS DISCIPLINE",
        "connected GitHub branch as the mutation surface",
        "request -> evidence review -> bounded decision -> repo/Git/GitHub mutation -> artifacts -> validation -> report -> next decision",
        "columns B:O",
        "largest divisor among 10, 5, and 2",
        "Use P03",
        "P12 for closeout",
        "Acknowledgment-only completion is invalid",
    )
    missing = [marker for marker in required_harness if marker not in harness_text]
    if missing:
        raise ValueError(f"P57 portable harness contract is missing: {missing}")
    return standard, gnhf, [*standard_prompts, *gnhf_prompts]


def _formula_cells(parts: Mapping[str, bytes]) -> set[tuple[int, str]]:
    return ooxml._formula_cells(parts)


def _prompt_rows_ranges(parts: Mapping[str, bytes]) -> tuple[dict[str, int], dict[str, str]]:
    return ooxml._prompt_rows_and_ranges(parts)


def _prompt_text(parts: Mapping[str, bytes], part: str, prompt_range: str) -> str:
    last_row = int(prompt_range.rsplit("A", 1)[-1])
    return "\n".join(ooxml._prompt_payload(parts, part, last_row))


def _is_contiguous(order: Sequence[str], names: Sequence[str]) -> bool:
    try:
        positions = [order.index(name) for name in names]
    except ValueError:
        return False
    return positions == list(range(positions[0], positions[0] + len(positions)))


def validate_v39(
    workbook: str | Path,
    *,
    standard_ai_spec: str | Path = DEFAULT_STANDARD_AI_SPEC,
    gnhf_spec: str | Path = DEFAULT_GNHF_SPEC,
    changed_parts: Sequence[str] = (),
) -> V39SegmentedReport:
    path = Path(workbook)
    findings: list[dict] = []
    directory_gate: list[str] = []
    zero_token: list[str] = []
    try:
        _, _, prompts = _load_prompt_contracts(Path(standard_ai_spec), Path(gnhf_spec))
        prompt_by_id = {item["prompt_id"]: item for item in prompts}
    except Exception as exc:
        return V39SegmentedReport(
            str(path), False, 0, STANDARD_AI_EXTENSION_IDS, GNHF_HARNESS_IDS, APPEND_ORDER, (), (), tuple(changed_parts),
            ({"rule": "prompt contracts", "error": str(exc)},),
        )
    if not path.exists():
        return V39SegmentedReport(
            str(path), False, 0, STANDARD_AI_EXTENSION_IDS, GNHF_HARNESS_IDS, APPEND_ORDER, (), (), tuple(changed_parts),
            ({"rule": "file exists", "path": str(path)},),
        )
    prompt_sheets: list[str] = []
    try:
        package = ooxml._read_workbook(path)
        parts = package.parts
        workbook_order, mapping, _, _ = ooxml._sheet_map(parts)
        prompt_sheets = [name for name in workbook_order if ooxml.PROMPT_SHEET_RE.fullmatch(name)]
        expected_sheets = [f"{prompt_id}_COPY_SAFE" for prompt_id in EXPECTED_PROMPT_ORDER]
        if prompt_sheets != expected_sheets:
            findings.append({"rule": "semantic prompt order", "expected": expected_sheets, "actual": prompt_sheets})
        standard_names = [f"{prompt_id}_COPY_SAFE" for prompt_id in STANDARD_AI_EXTENSION_IDS]
        gnhf_names = [f"{prompt_id}_COPY_SAFE" for prompt_id in GNHF_HARNESS_IDS]
        if not _is_contiguous(workbook_order, standard_names):
            findings.append({"rule": "standard-AI extension contiguous", "expected": standard_names})
        if not _is_contiguous(workbook_order, gnhf_names):
            findings.append({"rule": "GNHF harness block contiguous", "expected": gnhf_names})
        if workbook_order.index(standard_names[-1]) >= workbook_order.index(gnhf_names[0]):
            findings.append({"rule": "standard-AI extension precedes GNHF harness block"})

        rows, ranges = _prompt_rows_ranges(parts)
        appended_rows = [rows.get(prompt_id) for prompt_id in APPEND_ORDER]
        if None in appended_rows or appended_rows != list(range(appended_rows[0], appended_rows[0] + len(appended_rows))):
            findings.append({"rule": "Prompt Library append order", "expected": list(APPEND_ORDER), "actual_rows": appended_rows})
        library_part = mapping.get("Prompt_Library")
        if not library_part:
            raise ValueError("missing Prompt_Library")
        shared = ooxml._shared_strings(parts)
        library_cells = ooxml._cells(ooxml._root(parts[library_part], library_part))

        for prompt_id in APPEND_ORDER:
            prompt = prompt_by_id[prompt_id]
            sheet_name = f"{prompt_id}_COPY_SAFE"
            prompt_range = ranges.get(prompt_id)
            sheet_part = mapping.get(sheet_name)
            if not prompt_range or not sheet_part:
                findings.append({"rule": "prompt registered", "prompt": prompt_id})
                continue
            payload = _prompt_text(parts, sheet_part, prompt_range)
            expected_payload = "\n".join(prompt["lines"])
            if payload != expected_payload:
                findings.append({"rule": "prompt payload exact", "prompt": prompt_id})
            if prompt["surface_family"] == "standard_ai":
                if "DIRECTORY GATE" in payload:
                    directory_gate.append(prompt_id)
                else:
                    findings.append({"rule": "standard-AI directory gate", "prompt": prompt_id})
                if "zero-token" in payload.lower() or "no model, api, provider, or coding-agent tokens" in payload.lower():
                    zero_token.append(prompt_id)
                if payload.lstrip().startswith("gnhf `") or "--max-tokens" in payload or "--max-iterations" in payload:
                    findings.append({"rule": "standard AI excludes GNHF launch syntax", "prompt": prompt_id})
            elif prompt.get("execution_shape") == "gnhf_command":
                for marker in ("gnhf `", "--max-iterations", "--max-tokens", "--stop-when"):
                    if marker not in payload:
                        findings.append({"rule": "GNHF command marker", "prompt": prompt_id, "missing": marker})
            row = rows.get(prompt_id)
            if row is not None:
                prompt_class = ooxml._cell_display(library_cells.get(f"E{row}"), shared)
                if prompt["surface_family"] == "standard_ai" and not prompt_class.startswith("STANDARD AI"):
                    findings.append({"rule": "standard-AI Prompt Library class", "prompt": prompt_id, "actual": prompt_class})
                if prompt["surface_family"] == "gnhf" and "GNHF" not in prompt_class and prompt_id != "P49":
                    findings.append({"rule": "GNHF Prompt Library class", "prompt": prompt_id, "actual": prompt_class})
            last_row = int(prompt_range.rsplit("A", 1)[-1])
            root = ooxml._root(parts[sheet_part], sheet_part)
            cells = ooxml._cells(root)
            expected_formula = f'HYPERLINK("#\'{sheet_name}\'!A1:A{last_row}","Copy A1:A{last_row} only")'
            for ref in ("C1", f"C{last_row}"):
                if ooxml._formula(cells.get(ref)) != expected_formula:
                    findings.append({"rule": "exact prompt-range formula", "prompt": prompt_id, "cell": ref})
            links = {
                item.attrib.get("ref"): item.attrib.get("location")
                for item in root.findall("m:hyperlinks/m:hyperlink", ooxml.NS)
            }
            for ref in ("C1", f"C{last_row}"):
                if links.get(ref) != "'Prompt_Library'!A1":
                    findings.append({"rule": "Prompt Library backlink", "prompt": prompt_id, "cell": ref, "actual": links.get(ref)})
            if root.find("m:sheetProtection", ooxml.NS) is None:
                findings.append({"rule": "prompt sheet protected", "prompt": prompt_id})

        if tuple(directory_gate) != STANDARD_AI_EXTENSION_IDS:
            findings.append({"rule": "all standard-AI extensions directory-gated", "actual": directory_gate})
        if "P51" not in zero_token:
            findings.append({"rule": "P51 explicit zero-token boundary"})
        p55_text = _prompt_text(parts, mapping["P55_COPY_SAFE"], ranges["P55"])
        for marker in ("gh auth status --active --hostname github.com", "gh repo create", "gh repo view", "--clone", "--source"):
            if marker not in p55_text:
                findings.append({"rule": "P55 GitHub CLI contract", "missing": marker})

        formulas = _formula_cells(parts)
        if "xl/calcChain.xml" in parts:
            chain_root = ooxml._root(parts["xl/calcChain.xml"], "xl/calcChain.xml")
            chain_cells = {
                (int(item.attrib["i"]), item.attrib["r"])
                for item in chain_root.findall("m:c", ooxml.NS)
            }
            if chain_cells != formulas:
                findings.append({
                    "rule": "calcChain exact formula-cell match",
                    "missing": sorted(formulas - chain_cells)[:20],
                    "stale": sorted(chain_cells - formulas)[:20],
                })
    except (ValueError, KeyError, IndexError, zipfile.BadZipFile, ET.ParseError) as exc:
        findings.append({"rule": "package readable", "error": str(exc)})
    return V39SegmentedReport(
        path=str(path.resolve()),
        valid=not findings,
        prompt_count=len(prompt_sheets),
        standard_ai_extension=STANDARD_AI_EXTENSION_IDS,
        gnhf_harness_section=GNHF_HARNESS_IDS,
        append_order=APPEND_ORDER,
        directory_gate_prompts=tuple(directory_gate),
        zero_token_prompts=tuple(zero_token),
        changed_parts=tuple(changed_parts),
        findings=tuple(findings),
    )


def _build_candidate(
    source_workbook: Path,
    output: Path,
    prompts: Sequence[Mapping[str, object]],
) -> tuple[tuple[str, ...], dict[str, bytes]]:
    package = ooxml._read_workbook(source_workbook)
    parts = dict(package.parts)
    workbook_order, mapping, _, _ = ooxml._sheet_map(parts)
    referenced = set(mapping.values())
    package_sheets = {name for name in parts if ooxml.SHEET_PART_RE.fullmatch(name)}
    orphans = sorted(package_sheets - referenced)
    if orphans:
        raise ValueError(f"V39 source contains unreferenced worksheet parts: {orphans}")
    prompt_sheets = [name for name in workbook_order if ooxml.PROMPT_SHEET_RE.fullmatch(name)]
    expected_source = [f"{prompt_id}_COPY_SAFE" for prompt_id in SOURCE_PROMPT_IDS]
    if prompt_sheets != expected_source:
        raise ValueError(f"V39 requires the exact P00-P44 V38 prompt floor; discovered {prompt_sheets}")
    library_part = mapping.get("Prompt_Library")
    template_part = mapping.get("P44_COPY_SAFE")
    if not library_part or not template_part:
        raise ValueError("V39 source must contain Prompt_Library and P44_COPY_SAFE")

    library_root, headers, prompt_rows, max_row, inherited_color = ooxml._find_library_rows(parts, library_part)
    new_rows, links = ooxml._append_library_rows(
        library_root,
        headers,
        prompt_rows,
        max_row,
        prompts,
        inherited_color,
    )
    ooxml._append_hyperlinks(library_root, links, ooxml._shared_strings(parts))
    parts[library_part] = ooxml._xml(library_root)
    prompt_xml = {
        prompt["prompt_id"]: ooxml._make_prompt_sheet(
            parts[template_part],
            prompt,
            new_rows[prompt["prompt_id"]],
        )
        for prompt in prompts
    }
    created_parts, _ = ooxml._append_workbook_sheets(parts, prompts, prompt_xml)
    placeholder_changed, _ = ooxml._normalize_prompt_placeholders(parts)
    visual_changed, _ = ooxml._apply_prompt_visual_coordination(parts)
    app_changed = ooxml._update_app_properties(parts, list(created_parts))
    calc_changed = ooxml._rebuild_calc_chain(parts)
    changed = {
        "[Content_Types].xml",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        library_part,
        *created_parts.values(),
        *placeholder_changed,
        *visual_changed,
    }
    if app_changed:
        changed.add("docProps/app.xml")
    if calc_changed:
        changed.add("xl/calcChain.xml")
    new_parts = list(created_parts.values())
    ooxml._write_package(package, output, parts, new_parts)
    return tuple(sorted(changed)), parts


def generate_v39(
    source: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    standard_ai_spec: Path = DEFAULT_STANDARD_AI_SPEC,
    gnhf_spec: Path = DEFAULT_GNHF_SPEC,
) -> dict:
    source = source.resolve()
    output_dir = output_dir.resolve()
    standard_ai_spec = standard_ai_spec.resolve()
    gnhf_spec = gnhf_spec.resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    standard_contract, gnhf_contract, prompts = _load_prompt_contracts(standard_ai_spec, gnhf_spec)
    if tuple(item["prompt_id"] for item in prompts) != APPEND_ORDER:
        raise ValueError(f"V39 append order must be {list(APPEND_ORDER)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    workbook = output_dir / f"{ARTIFACT_NAME}.xlsx"
    manifest_path = output_dir / f"{ARTIFACT_NAME}_manifest.json"
    bundle_path = output_dir / f"{ARTIFACT_NAME}_bundle.zip"

    with tempfile.TemporaryDirectory(prefix="prompt-kit-v39-segmented-") as temporary:
        source_workbook, support_files = ooxml._source_workbook(source, Path(temporary))
        source_hash_before = _sha256(source_workbook)
        changed_parts, _ = _build_candidate(source_workbook, workbook, prompts)
        if _sha256(source_workbook) != source_hash_before:
            raise ValueError("V39 generation modified the accepted V38 source workbook")
        report = validate_v39(
            workbook,
            standard_ai_spec=standard_ai_spec,
            gnhf_spec=gnhf_spec,
            changed_parts=changed_parts,
        )
        if not report.valid:
            raise ValueError(f"V39 segmented contract failed: {list(report.findings)[:8]}")
        deterministic = Path(temporary) / f"{ARTIFACT_NAME}-deterministic.xlsx"
        second_changed, _ = _build_candidate(source_workbook, deterministic, prompts)
        if changed_parts != second_changed or workbook.read_bytes() != deterministic.read_bytes():
            raise ValueError("V39 generation is not byte-deterministic for identical source and prompt contracts")

        manifest = {
            "schema_version": 1,
            "artifact": ARTIFACT_NAME,
            "generator": "triage.prompt_kit_v39_generator",
            "source": str(source),
            "source_sha256": _sha256(source),
            "source_workbook_sha256": source_hash_before,
            "workbook": str(workbook),
            "workbook_sha256": _sha256(workbook),
            "bundle": str(bundle_path),
            "prompt_count": report.prompt_count,
            "source_prompt_ids": list(SOURCE_PROMPT_IDS),
            "standard_ai_extension": list(STANDARD_AI_EXTENSION_IDS),
            "gnhf_harness_section": list(GNHF_HARNESS_IDS),
            "append_order": list(APPEND_ORDER),
            "section_doctrine": {
                "standard_ai": standard_contract["section"],
                "gnhf": gnhf_contract["section"],
                "rule": "section family and placement are authoritative; numeric sorting must not interleave the families",
            },
            "prompt_sources": {
                "standard_ai": str(standard_ai_spec),
                "gnhf": str(gnhf_spec),
            },
            "directory_gate_prompts": list(report.directory_gate_prompts),
            "zero_token_prompts": list(report.zero_token_prompts),
            "github_cli_bootstrap_prompt": "P55",
            "changed_parts": list(changed_parts),
            "source_immutable": True,
            "whole_workbook_serializer_forbidden": True,
            "byte_deterministic": True,
            "validation": report.to_dict(),
            "proof_level": "static_package_validation",
            "proof_ceiling": (
                "V39 prompt payloads, semantic section segmentation, directory-first standard-AI commands, "
                "zero-token test guidance, repository factoring prompts, GitHub CLI bootstrap safety, exact links, "
                "package structure, formulas, calculation-chain integrity, source immutability, and deterministic "
                "generation. Excel for Web behavior, any GNHF execution, and any GitHub repository creation remain "
                "separate runtime and operator gates."
            ),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(workbook, workbook.name)
            archive.write(manifest_path, manifest_path.name)
            for name, data in sorted(support_files.items()):
                if not name.lower().endswith(".xlsx") and Path(name).name != manifest_path.name:
                    archive.writestr(name, data)
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--standard-ai-spec", type=Path, default=DEFAULT_STANDARD_AI_SPEC)
    parser.add_argument("--gnhf-spec", type=Path, default=DEFAULT_GNHF_SPEC)
    parser.add_argument("--validate-only", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.source and not args.validate_only:
        parser.error("--source is required unless --validate-only is used")
    try:
        if args.validate_only:
            report = validate_v39(
                args.validate_only,
                standard_ai_spec=args.standard_ai_spec,
                gnhf_spec=args.gnhf_spec,
            )
            result = report.to_dict()
            valid = report.valid
        else:
            result = generate_v39(
                args.source,
                args.out_dir,
                standard_ai_spec=args.standard_ai_spec,
                gnhf_spec=args.gnhf_spec,
            )
            valid = True
    except Exception as exc:
        print(f"V39 segmented generation failed: {exc}")
        return 1
    print(
        json.dumps(result, indent=2)
        if args.json or args.validate_only
        else f"Generated: {result['workbook']}\nBundle: {result['bundle']}"
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
