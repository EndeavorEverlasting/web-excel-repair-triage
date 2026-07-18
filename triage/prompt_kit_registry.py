"""Extract and validate the AI Harness Prompt Kit machine registry.

The workbook remains the operator-facing artifact. This module reads its OOXML
package without reserializing it and emits a deterministic JSON registry that
other applications can consume without scraping workbook presentation details.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence
from xml.etree import ElementTree as ET

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SCHEMA_VERSION = "ai-harness-prompt-registry/v1"
DEFAULT_KIT_VERSION = "v38"
PROMPT_ID = re.compile(r"^P\d{2}$")
VARIABLE = re.compile(r"\bxyz_[a-z0-9_]+\b")
COPY_RANGE = re.compile(r"Copy A1:A(\d+) only")


class PromptRegistryError(ValueError):
    """Raised when a workbook or registry violates the prompt registry contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _column_number(reference: str) -> int:
    letters = "".join(ch for ch in reference if ch.isalpha()).upper()
    if not letters:
        raise PromptRegistryError(f"cell reference has no column: {reference}")
    result = 0
    for letter in letters:
        result = result * 26 + (ord(letter) - ord("A") + 1)
    return result


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall(f"{{{MAIN_NS}}}si"):
        values.append("".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")))
    return values


def _sheet_paths(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    result: dict[str, str] = {}
    for sheet in workbook.findall(f".//{{{MAIN_NS}}}sheet"):
        relationship_id = sheet.attrib[f"{{{DOC_REL_NS}}}id"]
        target = targets[relationship_id]
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = posixpath.normpath(posixpath.join("xl", target))
        result[sheet.attrib["name"]] = path
    return result


def _cell_text(cell: ET.Element, shared_strings: Sequence[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
    value = cell.findtext(f"{{{MAIN_NS}}}v")
    if value is None:
        return ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError) as exc:
            raise PromptRegistryError(f"invalid shared string index: {value}") from exc
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    return value


def _sheet_rows(
    archive: zipfile.ZipFile,
    path: str,
    shared_strings: Sequence[str],
) -> dict[int, dict[int, str]]:
    root = ET.fromstring(archive.read(path))
    rows: dict[int, dict[int, str]] = {}
    for row in root.findall(f".//{{{MAIN_NS}}}row"):
        row_number = int(row.attrib.get("r", "0"))
        row_values: dict[int, str] = {}
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            reference = cell.attrib.get("r", "")
            row_values[_column_number(reference)] = _cell_text(cell, shared_strings)
        rows[row_number] = row_values
    return rows


def _table(rows: Mapping[int, Mapping[int, str]], header_row: int) -> list[dict[str, str]]:
    headers = rows.get(header_row, {})
    if not headers:
        raise PromptRegistryError(f"missing header row {header_row}")
    result: list[dict[str, str]] = []
    for row_number in sorted(number for number in rows if number > header_row):
        row = rows[row_number]
        result.append({header: row.get(column, "") for column, header in headers.items() if header})
    return result


def _find_header_row(rows: Mapping[int, Mapping[int, str]], required: str) -> int:
    for row_number, row in rows.items():
        if required in row.values():
            return row_number
    raise PromptRegistryError(f"could not find header {required!r}")


def _load_overrides(path: Optional[Path]) -> dict[str, dict[str, str]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != "ai-harness-prompt-variable-overrides/v1":
        raise PromptRegistryError(f"unsupported variable override schema in {path}")
    result: dict[str, dict[str, str]] = {}
    for record in payload.get("variables", []):
        name = str(record.get("name", ""))
        if not VARIABLE.fullmatch(name):
            raise PromptRegistryError(f"invalid variable override name: {name!r}")
        if name in result:
            raise PromptRegistryError(f"duplicate variable override: {name}")
        result[name] = {
            "name": name,
            "meaning": str(record.get("meaning", "")),
            "example": str(record.get("example", "")),
            "origin": "registry override inferred from V38 prompt usage",
        }
    return result


def _execution_surface(prompt_class: str, text: str) -> str:
    if prompt_class.startswith("GNHF /") or text.lstrip().startswith(("gnhf `", "& {")):
        return "gnhf_launch_artifact"
    return "regular_ai_prompt"


def extract_registry(
    workbook_path: Path,
    *,
    kit_version: str = DEFAULT_KIT_VERSION,
    variable_overrides_path: Optional[Path] = None,
) -> dict[str, Any]:
    """Extract a deterministic registry from a prompt-kit workbook."""
    workbook_path = workbook_path.resolve()
    workbook_bytes = workbook_path.read_bytes()
    overrides = _load_overrides(variable_overrides_path)

    with zipfile.ZipFile(workbook_path) as archive:
        archive.testzip()
        shared_strings = _read_shared_strings(archive)
        sheet_paths = _sheet_paths(archive)
        required_sheets = {"Prompt_Library", "Prompt_Sequence", "Variables"}
        missing_sheets = sorted(required_sheets - set(sheet_paths))
        if missing_sheets:
            raise PromptRegistryError(f"missing required workbook sheets: {missing_sheets}")

        library_rows = _sheet_rows(archive, sheet_paths["Prompt_Library"], shared_strings)
        sequence_rows = _sheet_rows(archive, sheet_paths["Prompt_Sequence"], shared_strings)
        variable_rows = _sheet_rows(archive, sheet_paths["Variables"], shared_strings)

        library = _table(library_rows, _find_header_row(library_rows, "Prompt ID"))
        sequence = _table(sequence_rows, _find_header_row(sequence_rows, "Prompt ID"))
        variables = _table(variable_rows, _find_header_row(variable_rows, "Variable"))
        sequence_by_id = {record.get("Prompt ID", ""): record for record in sequence}

        declared_variables: dict[str, dict[str, str]] = {}
        for record in variables:
            name = record.get("Variable", "")
            if not name:
                continue
            declared_variables[name] = {
                "name": name,
                "meaning": record.get("Meaning", ""),
                "example": record.get("Example", ""),
                "origin": "Variables!A:C",
            }

        prompts: list[dict[str, Any]] = []
        used_variables: set[str] = set()
        for record in library:
            prompt_id = record.get("Prompt ID", "")
            if not PROMPT_ID.fullmatch(prompt_id):
                continue
            copy_sheet = record.get("Copy-Safe Sheet", "")
            if copy_sheet not in sheet_paths:
                raise PromptRegistryError(f"{prompt_id} references missing copy-safe sheet {copy_sheet!r}")
            copy_rows = _sheet_rows(archive, sheet_paths[copy_sheet], shared_strings)
            copy_end: Optional[int] = None
            for row in copy_rows.values():
                for value in row.values():
                    match = COPY_RANGE.search(value)
                    if match:
                        copy_end = int(match.group(1))
                        break
                if copy_end is not None:
                    break
            if copy_end is None:
                copy_end = max((row for row, values in copy_rows.items() if values.get(1, "") != ""), default=0)
            if copy_end < 1:
                raise PromptRegistryError(f"{prompt_id} has no copy-safe prompt rows")
            text = "\n".join(copy_rows.get(row, {}).get(1, "") for row in range(1, copy_end + 1))
            sequence_record = sequence_by_id.get(prompt_id)
            if sequence_record is None:
                raise PromptRegistryError(f"{prompt_id} is missing from Prompt_Sequence")
            required_variables = sorted(set(VARIABLE.findall(text)))
            used_variables.update(required_variables)
            prompts.append(
                {
                    "id": prompt_id,
                    "sequence": int(record.get("Seq", "0")),
                    "name": record.get("Prompt Name", ""),
                    "moment": sequence_record.get("Moment", ""),
                    "promptType": record.get("Prompt Type", ""),
                    "promptClass": record.get("Prompt Class", ""),
                    "executionSurface": _execution_surface(record.get("Prompt Class", ""), text),
                    "sprintPathRole": record.get("Sprint Path Role", ""),
                    "useForProgress": record.get("Use For Progress?", ""),
                    "useThisWhen": record.get("Use This When", ""),
                    "doNotUseWhen": sequence_record.get("Do NOT Use When", ""),
                    "inspectFirst": record.get("Inspect First", ""),
                    "expectedOutput": record.get("Expected Output", ""),
                    "nextStep": record.get("Next Step", ""),
                    "acceptanceGate": record.get("Proof / Acceptance Gate", ""),
                    "mutatesRepository": sequence_record.get("Mutates Repo?", ""),
                    "authority": sequence_record.get("Authority", ""),
                    "proofCeiling": sequence_record.get("Proof Ceiling", ""),
                    "color": record.get("Color", ""),
                    "copySafeSheet": copy_sheet,
                    "copyRange": f"A1:A{copy_end}",
                    "requiredVariables": required_variables,
                    "textSha256": _sha256_bytes(text.encode("utf-8")),
                    "text": text,
                }
            )

    variable_catalog = {**declared_variables, **overrides}
    unresolved = sorted(used_variables - set(variable_catalog))
    if unresolved:
        raise PromptRegistryError(
            "V38 prompt text uses variables missing from Variables and overrides: " + ", ".join(unresolved)
        )

    registry = {
        "schemaVersion": SCHEMA_VERSION,
        "kitVersion": kit_version,
        "source": {
            "artifact": workbook_path.name,
            "sha256": _sha256_bytes(workbook_bytes),
            "promptLibrarySheet": "Prompt_Library",
            "promptSequenceSheet": "Prompt_Sequence",
            "variablesSheet": "Variables",
            "promptCount": len(prompts),
            "promptIdRange": f"{prompts[0]['id']}-{prompts[-1]['id']}" if prompts else "",
        },
        "ownership": {
            "canonicalProducer": "EndeavorEverlasting/web-excel-repair-triage",
            "consumer": "EndeavorEverlasting/AgentSwitchboard",
            "boundary": (
                "The triage repository owns extraction and validation. AgentSwitchboard may vendor a pinned "
                "snapshot and render prompts but must not silently rewrite prompt IDs or execution-surface doctrine."
            ),
        },
        "executionSurfaces": [
            {
                "id": "regular_ai_prompt",
                "description": "Instructions pasted into an interactive AI chat or coding-agent conversation.",
            },
            {
                "id": "gnhf_launch_artifact",
                "description": (
                    "Executable shell or PowerShell launch content that invokes GNHF with explicit bounds and "
                    "an embedded or referenced objective."
                ),
            },
        ],
        "variables": [variable_catalog[name] for name in sorted(variable_catalog)],
        "prompts": sorted(prompts, key=lambda item: item["sequence"]),
    }
    errors = validate_registry(registry)
    if errors:
        raise PromptRegistryError("generated registry failed validation: " + "; ".join(errors))
    return registry


def validate_registry(registry: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a registry payload."""
    errors: list[str] = []
    if registry.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    prompts = registry.get("prompts")
    variables = registry.get("variables")
    if not isinstance(prompts, list) or not prompts:
        errors.append("prompts must be a non-empty list")
        return errors
    if not isinstance(variables, list):
        errors.append("variables must be a list")
        variables = []
    variable_names = [str(item.get("name", "")) for item in variables if isinstance(item, Mapping)]
    if len(variable_names) != len(set(variable_names)):
        errors.append("variable names must be unique")
    variable_set = set(variable_names)

    ids: list[str] = []
    sequences: list[int] = []
    for prompt in prompts:
        if not isinstance(prompt, Mapping):
            errors.append("every prompt must be an object")
            continue
        prompt_id = str(prompt.get("id", ""))
        ids.append(prompt_id)
        try:
            sequences.append(int(prompt.get("sequence")))
        except (TypeError, ValueError):
            errors.append(f"{prompt_id or '<unknown>'} sequence must be an integer")
        if not PROMPT_ID.fullmatch(prompt_id):
            errors.append(f"invalid prompt id: {prompt_id!r}")
        text = prompt.get("text")
        if not isinstance(text, str) or not text:
            errors.append(f"{prompt_id} text must be non-empty")
            continue
        expected_sha = _sha256_bytes(text.encode("utf-8"))
        if prompt.get("textSha256") != expected_sha:
            errors.append(f"{prompt_id} textSha256 mismatch")
        surface = prompt.get("executionSurface")
        expected_surface = _execution_surface(str(prompt.get("promptClass", "")), text)
        if surface != expected_surface:
            errors.append(f"{prompt_id} executionSurface must be {expected_surface}")
        required_variables = sorted(set(VARIABLE.findall(text)))
        if prompt.get("requiredVariables") != required_variables:
            errors.append(f"{prompt_id} requiredVariables do not match prompt text")
        missing = sorted(set(required_variables) - variable_set)
        if missing:
            errors.append(f"{prompt_id} references undefined variables: {', '.join(missing)}")
        copy_range = str(prompt.get("copyRange", ""))
        if not re.fullmatch(r"A1:A\d+", copy_range):
            errors.append(f"{prompt_id} copyRange is invalid: {copy_range!r}")

    if len(ids) != len(set(ids)):
        errors.append("prompt IDs must be unique")
    if len(sequences) != len(set(sequences)):
        errors.append("prompt sequences must be unique")
    expected_ids = [f"P{number:02d}" for number in range(len(prompts))]
    if ids != expected_ids:
        errors.append(f"prompt IDs must be contiguous and ordered: expected {expected_ids[0]}-{expected_ids[-1]}")
    expected_sequences = list(range(len(prompts)))
    if sequences != expected_sequences:
        errors.append("prompt sequences must be contiguous and ordered from zero")
    source = registry.get("source")
    if not isinstance(source, Mapping) or int(source.get("promptCount", -1)) != len(prompts):
        errors.append("source.promptCount must equal the number of prompts")
    return errors


def write_registry(
    workbook_path: Path,
    output_path: Path,
    *,
    kit_version: str = DEFAULT_KIT_VERSION,
    variable_overrides_path: Optional[Path] = None,
) -> dict[str, Any]:
    registry = extract_registry(
        workbook_path,
        kit_version=kit_version,
        variable_overrides_path=variable_overrides_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return registry


def load_registry(path: Path) -> dict[str, Any]:
    """Load a monolithic registry or resolve a catalog plus prompt-text shards."""
    path = path.resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, MutableMapping):
        raise PromptRegistryError("registry root must be an object")
    registry = dict(payload)
    shard_records = registry.get("promptShards")
    if not shard_records:
        return registry

    shard_prompts: dict[tuple[str, str], Mapping[str, Any]] = {}
    for record in shard_records:
        relative_path = str(record.get("path", ""))
        shard_path = (path.parent / relative_path).resolve()
        if path.parent not in shard_path.parents:
            raise PromptRegistryError(f"prompt shard escapes registry directory: {relative_path}")
        shard_bytes = shard_path.read_bytes()
        expected_sha = str(record.get("sha256", ""))
        actual_sha = _sha256_bytes(shard_bytes)
        if expected_sha != actual_sha:
            raise PromptRegistryError(f"prompt shard SHA mismatch: {relative_path}")
        shard = json.loads(shard_bytes.decode("utf-8"))
        if shard.get("schemaVersion") != "ai-harness-prompt-text-shard/v1":
            raise PromptRegistryError(f"unsupported prompt shard schema: {relative_path}")
        if shard.get("kitVersion") != registry.get("kitVersion"):
            raise PromptRegistryError(f"prompt shard kit version mismatch: {relative_path}")
        for prompt in shard.get("prompts", []):
            prompt_id = str(prompt.get("id", ""))
            key = (relative_path, prompt_id)
            if key in shard_prompts:
                raise PromptRegistryError(f"duplicate prompt in shard: {relative_path}#{prompt_id}")
            shard_prompts[key] = prompt

    resolved_prompts: list[dict[str, Any]] = []
    for prompt in registry.get("prompts", []):
        resolved = dict(prompt)
        reference = str(resolved.get("textRef", ""))
        if "#" not in reference:
            raise PromptRegistryError(f"{resolved.get('id', '<unknown>')} has invalid textRef")
        relative_path, prompt_id = reference.rsplit("#", 1)
        shard_prompt = shard_prompts.get((relative_path, prompt_id))
        if shard_prompt is None:
            raise PromptRegistryError(f"missing prompt shard record: {reference}")
        if prompt_id != resolved.get("id"):
            raise PromptRegistryError(f"prompt textRef ID mismatch: {reference}")
        text = str(shard_prompt.get("text", ""))
        if _sha256_bytes(text.encode("utf-8")) != resolved.get("textSha256"):
            raise PromptRegistryError(f"{prompt_id} text hash mismatch between catalog and shard")
        resolved["text"] = text
        resolved_prompts.append(resolved)
    registry["prompts"] = resolved_prompts
    return registry


def write_sharded_registry(
    workbook_path: Path,
    output_dir: Path,
    *,
    kit_version: str = DEFAULT_KIT_VERSION,
    variable_overrides_path: Optional[Path] = None,
    shard_size: int = 9,
) -> dict[str, Any]:
    """Write a catalog and bounded prompt-text shards for repository consumption."""
    if shard_size < 1:
        raise PromptRegistryError("shard_size must be positive")
    registry = extract_registry(
        workbook_path,
        kit_version=kit_version,
        variable_overrides_path=variable_overrides_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    shards_dir = output_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    catalog = {key: value for key, value in registry.items() if key != "prompts"}
    catalog["promptShards"] = []
    catalog_prompts: list[dict[str, Any]] = []
    prompts = registry["prompts"]
    for start in range(0, len(prompts), shard_size):
        chunk = prompts[start : start + shard_size]
        relative_path = f"shards/prompts-{chunk[0]['id']}-{chunk[-1]['id']}.json"
        shard = {
            "schemaVersion": "ai-harness-prompt-text-shard/v1",
            "kitVersion": kit_version,
            "promptRange": f"{chunk[0]['id']}-{chunk[-1]['id']}",
            "prompts": [
                {"id": prompt["id"], "textSha256": prompt["textSha256"], "text": prompt["text"]}
                for prompt in chunk
            ],
        }
        shard_path = output_dir / relative_path
        shard_path.write_text(json.dumps(shard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        catalog["promptShards"].append(
            {
                "range": shard["promptRange"],
                "path": relative_path,
                "sha256": _sha256_bytes(shard_path.read_bytes()),
            }
        )
        for prompt in chunk:
            catalog_prompt = {key: value for key, value in prompt.items() if key != "text"}
            catalog_prompt["textRef"] = f"{relative_path}#{prompt['id']}"
            catalog_prompts.append(catalog_prompt)
    catalog["prompts"] = catalog_prompts
    catalog_path = output_dir / "prompt-registry.v1.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    resolved = load_registry(catalog_path)
    errors = validate_registry(resolved)
    if errors:
        raise PromptRegistryError("sharded registry failed validation: " + "; ".join(errors))
    return catalog


def _load_registry(path: Path) -> dict[str, Any]:
    return load_registry(path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    extract = subcommands.add_parser("extract", help="extract a registry from an XLSX prompt kit")
    extract.add_argument("workbook")
    extract.add_argument("--out", required=True)
    extract.add_argument("--kit-version", default=DEFAULT_KIT_VERSION)
    extract.add_argument("--variable-overrides")
    extract.add_argument("--sharded", action="store_true", help="write catalog plus bounded prompt-text shards")

    validate = subcommands.add_parser("validate", help="validate an existing registry JSON file")
    validate.add_argument("registry")

    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            if args.sharded:
                registry = write_sharded_registry(
                    Path(args.workbook),
                    Path(args.out),
                    kit_version=args.kit_version,
                    variable_overrides_path=Path(args.variable_overrides) if args.variable_overrides else None,
                )
                prompt_count = registry["source"]["promptCount"]
                output = str(Path(args.out) / "prompt-registry.v1.json")
            else:
                registry = write_registry(
                    Path(args.workbook),
                    Path(args.out),
                    kit_version=args.kit_version,
                    variable_overrides_path=Path(args.variable_overrides) if args.variable_overrides else None,
                )
                prompt_count = len(registry["prompts"])
                output = args.out
            print(json.dumps({"status": "PASS", "prompts": prompt_count, "output": output}))
            return 0
        registry = _load_registry(Path(args.registry))
        errors = validate_registry(registry)
        if errors:
            print(json.dumps({"status": "FAIL", "errors": errors}, indent=2))
            return 1
        print(json.dumps({"status": "PASS", "prompts": len(registry["prompts"]), "registry": args.registry}))
        return 0
    except (OSError, zipfile.BadZipFile, ET.ParseError, json.JSONDecodeError, PromptRegistryError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
