"""Validate and execute the bidirectional website/spreadsheet input-analysis contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Mapping, Optional, Sequence

ROOT = Path(__file__).parents[1]
DEFAULT_POLICY_PATH = ROOT / "configs/harness/bidirectional_web_spreadsheet_v1.json"
DEFAULT_SCHEMA_PATH = ROOT / "configs/harness/web_spreadsheet_ir_v1.schema.json"
DEFAULT_MANIFEST_PATH = ROOT / "configs/harness/harness_manifest_v1.json"
DEFAULT_WORKFLOWS_PATH = ROOT / "configs/harness/workflows_v1.json"
DEFAULT_ARTIFACT_REGISTRY_PATH = ROOT / "configs/harness/artifact_registry_v1.json"

_REQUIRED_CONTEXT = (
    "repo",
    "branch_or_worktree",
    "pr_or_sprint",
    "lane",
    "owned_scope",
    "forbidden_scope",
    "expected_artifacts",
)
_SOURCE_KINDS = (
    "sidecar_portal_html",
    "generic_html",
    "xlsx_workbook",
    "workbook_bundle",
    "unsupported",
)
_DIRECTION_ORDER = ("website_to_spreadsheet", "spreadsheet_to_website")
_IMPLEMENTATION_SEQUENCE = (
    "install_contract_and_input_analyzer",
    "implement_website_to_spreadsheet_for_sidecar_portal_html",
    "extend_website_to_spreadsheet_with_operator_approved_generic_html_profiles",
    "implement_spreadsheet_to_website_through_shared_ir",
    "prove_bidirectional_semantic_round_trip",
)


def _load_object(path: str | Path, *, label: str) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be one JSON object")
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_policy(path: str | Path = DEFAULT_POLICY_PATH) -> dict:
    return _load_object(path, label="bidirectional conversion policy")


def load_schema(path: str | Path = DEFAULT_SCHEMA_PATH) -> dict:
    return _load_object(path, label="web spreadsheet IR schema")


def validate_policy(policy: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if policy.get("schema_version") != 1:
        issues.append("bidirectional conversion policy schema_version must be 1")
    if policy.get("contract_id") != "bidirectional-web-spreadsheet-generator":
        issues.append("bidirectional conversion contract id drift")
    if tuple(policy.get("required_context_fields", ())) != _REQUIRED_CONTEXT:
        issues.append("bidirectional conversion required context fields drift")
    conditional = policy.get("conditional_context_fields")
    if not isinstance(conditional, Mapping) or "validation_order" not in conditional:
        issues.append("conditional validation_order requirement missing")

    evidence = policy.get("current_repository_evidence")
    if not isinstance(evidence, Mapping):
        issues.append("current repository conversion evidence missing")
    else:
        if evidence.get("website_surface") != "triage/sidecar_html/portal.py":
            issues.append("sidecar HTML portal authority drift")
        if evidence.get("structured_payload_marker") != "const PORTAL =":
            issues.append("structured PORTAL payload marker drift")
        if evidence.get("inverse_converter_exists") is not False:
            issues.append("policy must not claim an existing inverse converter")

    analysis = policy.get("input_analysis")
    if not isinstance(analysis, Mapping):
        issues.append("input analysis contract missing")
    else:
        if analysis.get("required_before_conversion") is not True:
            issues.append("input analysis must precede conversion")
        if analysis.get("output_artifact") != "conversion_analysis.json":
            issues.append("input analysis artifact name drift")
        if tuple(analysis.get("source_kinds", ())) != _SOURCE_KINDS:
            issues.append("input source-kind taxonomy drift")
        if analysis.get("network_fetch_requires_explicit_scope") is not True:
            issues.append("network fetch must require explicit scope")
        if analysis.get("execute_remote_javascript") is not False:
            issues.append("remote JavaScript execution must remain forbidden")
        if analysis.get("use_cookies_or_credentials") is not False:
            issues.append("cookies and credentials must remain forbidden")

    shared = policy.get("shared_intermediate_representation")
    if not isinstance(shared, Mapping):
        issues.append("shared intermediate representation contract missing")
    else:
        if shared.get("id") != "web-spreadsheet-ir-v1":
            issues.append("shared IR id drift")
        if shared.get("schema") != "configs/harness/web_spreadsheet_ir_v1.schema.json":
            issues.append("shared IR schema path drift")
        for field in (
            "required_for_both_directions",
            "semantic_hash_required",
            "presentation_is_separate_from_semantics",
        ):
            if shared.get(field) is not True:
                issues.append(f"shared IR rule must be true: {field}")

    directions = policy.get("directions")
    direction_ids = (
        tuple(item.get("id") for item in directions if isinstance(item, Mapping))
        if isinstance(directions, list)
        else ()
    )
    if direction_ids != _DIRECTION_ORDER:
        issues.append(
            "conversion direction order must be website_to_spreadsheet then spreadsheet_to_website"
        )
    elif len(directions) == 2:
        website, workbook = directions
        if website.get("implementation_priority") != 1:
            issues.append("website_to_spreadsheet must remain implementation priority 1")
        if workbook.get("implementation_priority") != 2:
            issues.append("spreadsheet_to_website must remain implementation priority 2")
        extraction = tuple(website.get("extraction_precedence", ()))
        if not extraction or extraction[0] != "embedded_portal_json":
            issues.append("website extraction must prefer embedded PORTAL JSON")
        forbidden = set(website.get("forbidden_primary_extraction", ()))
        for item in (
            "screenshot_reconstruction",
            "ocr",
            "pixel_matching",
            "remote_javascript_execution",
        ):
            if item not in forbidden:
                issues.append(f"website primary extraction must forbid: {item}")
        if "triage.sidecar_html.portal" not in str(
            workbook.get("rendering_authority", "")
        ):
            issues.append(
                "spreadsheet-to-website must reuse the sidecar portal renderer"
            )

    if tuple(policy.get("implementation_sequence", ())) != _IMPLEMENTATION_SEQUENCE:
        issues.append("bidirectional implementation sequence drift")

    action = policy.get("action_commitment")
    if not isinstance(action, Mapping):
        issues.append("bidirectional action commitment missing")
    else:
        for field in (
            "analysis_claim_requires_analysis_artifact",
            "conversion_claim_requires_output_artifact",
            "generation_claim_requires_mutation_and_validation",
            "plan_prompt_handoff_or_acknowledgment_is_not_conversion",
            "task_specific_rules_override_generic_closeout",
        ):
            if action.get(field) is not True:
                issues.append(
                    f"bidirectional action commitment must be true: {field}"
                )

    safety = policy.get("preservation_and_safety")
    if not isinstance(safety, Mapping):
        issues.append("bidirectional preservation and safety contract missing")
    else:
        for field in (
            "source_immutable",
            "outputs_under_approved_output_paths",
            "preserve_existing_contracts_before_invention",
            "no_whole_workbook_serializer_when_package_preserving_path_exists",
            "no_untrusted_html_execution",
            "sanitize_generated_html",
            "do_not_claim_visual_or_round_trip_fidelity_from_static_structure_only",
        ):
            if safety.get(field) is not True:
                issues.append(f"bidirectional safety rule must be true: {field}")
    return tuple(issues)


def validate_schema(schema: Mapping[str, object]) -> tuple[str, ...]:
    issues: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        issues.append("web spreadsheet IR must use JSON Schema 2020-12")
    required = set(schema.get("required", ()))
    for field in ("schema_version", "direction", "source", "document", "provenance"):
        if field not in required:
            issues.append(f"web spreadsheet IR required field missing: {field}")
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return tuple([*issues, "web spreadsheet IR properties missing"])
    direction = properties.get("direction")
    if not isinstance(direction, Mapping) or tuple(direction.get("enum", ())) != _DIRECTION_ORDER:
        issues.append("web spreadsheet IR direction enum drift")
    source = properties.get("source")
    source_properties = source.get("properties") if isinstance(source, Mapping) else None
    kind = source_properties.get("kind") if isinstance(source_properties, Mapping) else None
    if not isinstance(kind, Mapping) or tuple(kind.get("enum", ())) != _SOURCE_KINDS[:-1]:
        issues.append("web spreadsheet IR source-kind enum drift")
    definitions = schema.get("$defs")
    section = definitions.get("section") if isinstance(definitions, Mapping) else None
    if not isinstance(section, Mapping):
        issues.append("web spreadsheet IR section definition missing")
    return tuple(issues)


def validate_repository(repo_root: str | Path = ROOT) -> tuple[str, ...]:
    root = Path(repo_root).resolve()
    issues: list[str] = []
    required_paths = (
        "configs/harness/bidirectional_web_spreadsheet_v1.json",
        "configs/harness/web_spreadsheet_ir_v1.schema.json",
        "triage/harness_bidirectional_conversion_contract.py",
        "docs/HARNESS_BIDIRECTIONAL_WEB_SPREADSHEET.md",
        "triage/sidecar_html/portal.py",
        "triage/sidecar_html/rebuild.py",
        "triage/sidecar_html/adapters.py",
    )
    for relative in required_paths:
        if not (root / relative).exists():
            issues.append(f"bidirectional harness surface missing: {relative}")

    manifest = _load_object(
        root / "configs/harness/harness_manifest_v1.json",
        label="harness manifest",
    )
    contracts = manifest.get("conversion_contracts")
    expected_contracts = [
        "configs/harness/bidirectional_web_spreadsheet_v1.json",
        "configs/harness/web_spreadsheet_ir_v1.schema.json",
        "triage/harness_bidirectional_conversion_contract.py",
        "docs/HARNESS_BIDIRECTIONAL_WEB_SPREADSHEET.md",
    ]
    if contracts != expected_contracts:
        issues.append(
            "harness manifest bidirectional conversion contract registration drift"
        )

    workflows = _load_object(
        root / "configs/harness/workflows_v1.json",
        label="workflow registry",
    )
    matches = [
        item
        for item in workflows.get("workflows", [])
        if item.get("id") == "bidirectional-web-spreadsheet-conversion"
    ]
    if len(matches) != 1:
        issues.append(
            "bidirectional conversion workflow registration missing or duplicated"
        )
    elif matches[0].get("prompt") != "P56":
        issues.append("bidirectional conversion workflow must route through P56")

    artifacts = _load_object(
        root / "configs/harness/artifact_registry_v1.json",
        label="artifact registry",
    )
    matches = [
        item
        for item in artifacts.get("artifacts", [])
        if item.get("id") == "web-spreadsheet-input-analysis"
    ]
    if len(matches) != 1:
        issues.append(
            "web spreadsheet input-analysis artifact registration missing or duplicated"
        )
    else:
        generator = str(matches[0].get("generator", ""))
        if (
            "triage.harness_bidirectional_conversion_contract" not in generator
            or "--analyze-input" not in generator
        ):
            issues.append(
                "input-analysis artifact must route through the bidirectional analyzer"
            )
        validators = set(matches[0].get("validators", ()))
        if "triage.harness_bidirectional_conversion_contract" not in validators:
            issues.append(
                "input-analysis artifact must include the bidirectional validator"
            )
    return tuple(issues)


def _portal_payload(text: str) -> Optional[dict]:
    match = re.search(r"\bconst\s+PORTAL\s*=", text)
    if not match:
        return None
    candidate = text[match.end():].lstrip()
    try:
        payload, _ = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def analyze_input(path: str | Path) -> dict:
    raw = str(path)
    if raw.startswith(("http://", "https://")):
        raise ValueError(
            "network website fetch requires explicit implementation scope; "
            "provide a local HTML snapshot"
        )
    source = Path(path).resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    result = {
        "contract_id": "bidirectional-web-spreadsheet-generator",
        "source_path": str(source),
        "source_sha256": _sha256(source),
        "source_kind": "unsupported",
        "recommended_direction": None,
        "structured_payload_available": False,
        "extraction_strategy": None,
        "mapping_profile": None,
        "blockers": [],
        "implementation_priority": None,
        "proof_ceiling": (
            "Input classification only; no conversion artifact or field "
            "acceptance is proven."
        ),
    }
    suffix = source.suffix.lower()
    if suffix in {".html", ".htm"}:
        text = source.read_text(encoding="utf-8", errors="replace")
        portal = _portal_payload(text)
        if portal is not None and isinstance(portal.get("sections"), list):
            result.update(
                {
                    "source_kind": "sidecar_portal_html",
                    "recommended_direction": "website_to_spreadsheet",
                    "structured_payload_available": True,
                    "extraction_strategy": "embedded_portal_json",
                    "mapping_profile": "sidecar_portal_v1",
                    "implementation_priority": 1,
                    "portal_title": str(portal.get("title", "")),
                    "portal_section_count": len(portal["sections"]),
                }
            )
        else:
            has_semantic_html = bool(
                re.search(
                    r"<(?:table|section|article|dl|ul|ol)\b",
                    text,
                    re.IGNORECASE,
                )
            )
            result.update(
                {
                    "source_kind": "generic_html",
                    "recommended_direction": "website_to_spreadsheet",
                    "extraction_strategy": (
                        "semantic_dom_tables_and_labels"
                        if has_semantic_html
                        else "operator_approved_mapping_profile"
                    ),
                    "implementation_priority": 1,
                    "blockers": [
                        "operator_approved_mapping_profile_required"
                    ],
                }
            )
        return result

    if suffix in {".xlsx", ".xlsm"}:
        try:
            with zipfile.ZipFile(source) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile as exc:
            result["blockers"] = [f"invalid_workbook_package: {exc}"]
            return result
        required = {"[Content_Types].xml", "xl/workbook.xml"}
        if required.issubset(names):
            result.update(
                {
                    "source_kind": "xlsx_workbook",
                    "recommended_direction": "spreadsheet_to_website",
                    "structured_payload_available": True,
                    "extraction_strategy": "package_preserving_workbook_reader",
                    "mapping_profile": (
                        "registered_workbook_contract_or_operator_profile"
                    ),
                    "implementation_priority": 2,
                    "blockers": [
                        "approved_sheet_and_range_mapping_profile_required"
                    ],
                }
            )
        else:
            result["blockers"] = [
                "missing_required_workbook_package_parts"
            ]
        return result

    if suffix == ".zip":
        try:
            with zipfile.ZipFile(source) as archive:
                workbook_members = [
                    name
                    for name in archive.namelist()
                    if name.lower().endswith((".xlsx", ".xlsm"))
                ]
        except zipfile.BadZipFile as exc:
            result["blockers"] = [f"invalid_zip_package: {exc}"]
            return result
        if workbook_members:
            result.update(
                {
                    "source_kind": "workbook_bundle",
                    "recommended_direction": "spreadsheet_to_website",
                    "structured_payload_available": True,
                    "extraction_strategy": (
                        "extract_registered_workbook_then_"
                        "package_preserving_reader"
                    ),
                    "mapping_profile": "bundle_manifest_and_workbook_contract",
                    "implementation_priority": 2,
                    "blockers": [
                        "bundle_member_selection_and_mapping_approval_required"
                    ],
                }
            )
        else:
            result["blockers"] = ["no_workbook_member_in_bundle"]
        return result

    result["blockers"] = ["unsupported_input_type"]
    return result


def _validated_output_path(
    output_path: str | Path,
    *,
    source_path: str | Path | None = None,
) -> Path:
    """Resolve an analysis output and enforce the source/output safety boundary."""
    output = Path(output_path).resolve()
    if not any(part.casefold() == "outputs" for part in output.parts):
        raise ValueError(
            "analysis output must be written under an approved Outputs/ path"
        )
    if source_path is not None and output == Path(source_path).resolve():
        raise ValueError("analysis output must not overwrite the analyzed source")
    return output


def validate_all(
    policy_path: str | Path = DEFAULT_POLICY_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
    repo_root: str | Path = ROOT,
) -> tuple[str, ...]:
    issues: list[str] = []
    try:
        issues.extend(validate_policy(load_policy(policy_path)))
        issues.extend(validate_schema(load_schema(schema_path)))
        issues.extend(validate_repository(repo_root))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        issues.append(str(exc))
    return tuple(issues)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--analyze-input", type=str)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    issues = validate_all(args.policy, args.schema, args.repo_root)
    result: dict[str, object] = {
        "valid": not issues,
        "policy": str(args.policy),
        "schema": str(args.schema),
        "issues": list(issues),
    }

    if args.analyze_input:
        try:
            result["analysis"] = analyze_input(args.analyze_input)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            result["valid"] = False
            result["issues"] = [*result["issues"], str(exc)]

    if args.out:
        try:
            output = _validated_output_path(
                args.out,
                source_path=args.analyze_input,
            )
        except ValueError as exc:
            result["valid"] = False
            result["issues"] = [*result["issues"], str(exc)]
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(result, indent=2) + "\n",
                encoding="utf-8",
            )

    print(
        json.dumps(result, indent=2)
        if args.json or args.out or not result["valid"]
        else "bidirectional web/spreadsheet contract: PASS"
    )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
