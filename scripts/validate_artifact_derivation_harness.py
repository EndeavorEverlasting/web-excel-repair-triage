#!/usr/bin/env python3
"""Fail-closed source-preservation and artifact-derivation harness validator."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "harness" / "artifact-derivation"
MANIFEST = DOMAIN / "manifest.v1.json"
CONTRACT = DOMAIN / "contracts" / "create-new-from-source.v1.json"


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path.relative_to(ROOT)}: {exc}") from exc


def tracked(path: Path) -> bool:
    if not (ROOT / ".git").exists():
        return True
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return result.returncode == 0


def require_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise ValidationError(f"missing/empty harness component: {relative}")
    if not tracked(path):
        raise ValidationError(f"untracked harness component: {relative}")
    return path


def normalize_identity(value: str) -> str:
    value = str(value or "").strip().replace("\\", "/")
    if not value:
        raise ValidationError("artifact identity must be non-empty")
    prefix, sep, rest = value.partition(":")
    if sep and prefix.casefold() in {"drive", "file", "library", "repo", "path"}:
        return prefix.casefold() + ":" + rest.strip().casefold()
    return value.casefold()


def classify_intent(request_text: str, *, explicit_update: bool = False) -> str:
    contract = load_json(CONTRACT)
    text = str(request_text or "").casefold()
    if explicit_update and any(token.casefold() in text for token in contract["update_language"]):
        return "update_existing"
    return "create_new"


def _path_payload(identity: str) -> str | None:
    normalized = str(identity).strip().replace("\\", "/")
    if normalized.casefold().startswith("path:"):
        return normalized[5:].lstrip("/")
    if normalized.casefold().startswith("repo:"):
        return normalized[5:].lstrip("/")
    return None


def validate_envelope(*, intent: str, sources: list[str], output: str, output_exists: bool = False, explicit_update: bool = False) -> dict[str, Any]:
    contract = load_json(CONTRACT)
    if intent not in {"create_new", "update_existing"}:
        raise ValidationError(f"unsupported intent: {intent}")
    source_ids = [normalize_identity(item) for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValidationError("duplicate source identities")
    output_id = normalize_identity(output)
    protected = tuple(str(item).casefold() for item in contract.get("protected_input_prefixes", []))
    output_path = _path_payload(output)
    if output_path and output_path.casefold().startswith(protected):
        raise ValidationError("output targets a protected input/source path")

    if intent == "create_new":
        if output_id in source_ids:
            raise ValidationError("create_new output identity equals a source identity")
        if output_exists:
            raise ValidationError("create_new output already exists; choose a new identity")
        return {"status": "PASS", "intent": intent, "source_policy": "read_only_reference", "sources": source_ids, "output": output_id, "source_mutation_allowed": False}

    if not explicit_update:
        raise ValidationError("update_existing requires explicit operator update intent")
    if output_id not in source_ids:
        raise ValidationError("update_existing target must be one of the explicitly named existing source identities")
    return {"status": "PASS", "intent": intent, "source_policy": "explicit_mutation_target", "sources": source_ids, "output": output_id, "source_mutation_allowed": True}


def validate_static_harness() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != "web-excel-artifact-derivation-harness/v1":
        raise ValidationError("unexpected artifact-derivation manifest schema")
    required = {"codebase_map", "workflow", "artifact_registry", "contract", "validator", "tests", "skill", "operator_report"}
    components = manifest.get("components")
    if not isinstance(components, dict) or set(components) != required:
        raise ValidationError("artifact-derivation component registry drifted")
    for relative in components.values():
        require_file(str(relative))

    contract = load_json(CONTRACT)
    if contract.get("schema_version") != "artifact-derivation-create-new-from-source/v1":
        raise ValidationError("unexpected derivation contract schema")
    if contract.get("default_intent") != "create_new" or contract.get("source_role") != "read_only_reference":
        raise ValidationError("create-new/read-only defaults drifted")
    create = contract.get("create_new", {})
    if create.get("output_must_be_new_identity") is not True or create.get("output_may_equal_source_identity") is not False or create.get("output_may_already_exist") is not False:
        raise ValidationError("create_new collision rules drifted")
    if contract.get("update_existing", {}).get("requires_explicit_operator_update_intent") is not True:
        raise ValidationError("explicit-update gate drifted")

    markers = {
        "harness/CONTEXT.md": "Artifact creation / derivation",
        ".githooks/pre-commit": "validate_artifact_derivation_harness.py",
        ".githooks/pre-push": "validate_artifact_derivation_harness.py",
        ".github/workflows/artifact-derivation-harness.yml": "test_artifact_derivation_harness",
    }
    for relative, marker in markers.items():
        text = require_file(relative).read_text(encoding="utf-8")
        if marker not in text:
            raise ValidationError(f"{relative} missing integration marker: {marker}")
    skill = require_file(str(components["skill"])).read_text(encoding="utf-8")
    for heading in ("## Trigger", "## Required inputs", "## Outputs", "## Procedure", "## Guardrails", "## Validation", "## Proof ceiling"):
        if heading not in skill:
            raise ValidationError(f"artifact derivation skill missing heading: {heading}")
    return {"status": "PASS", "components": sorted(components)}


def resolve_report(raw: str) -> Path:
    target = Path(raw)
    if not target.is_absolute():
        target = ROOT / target
    target = target.resolve()
    outputs = (ROOT / "Outputs").resolve()
    try:
        target.relative_to(outputs)
    except ValueError as exc:
        raise ValidationError("output report must stay under Outputs/") from exc
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-text", default="")
    parser.add_argument("--intent", choices=("create_new", "update_existing"))
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--output-exists", action="store_true")
    parser.add_argument("--explicit-update", action="store_true")
    parser.add_argument("--output-report")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        report: dict[str, Any] = {"static": validate_static_harness()}
        runtime_requested = bool(args.output or args.source or args.request_text or args.intent)
        if runtime_requested:
            if not args.output:
                raise ValidationError("runtime preflight requires --output")
            intent = args.intent or classify_intent(args.request_text, explicit_update=args.explicit_update)
            report["runtime"] = validate_envelope(intent=intent, sources=args.source, output=args.output, output_exists=args.output_exists, explicit_update=args.explicit_update)
        if args.output_report:
            destination = resolve_report(args.output_report)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.summary:
            print("PASS: artifact derivation/source-preservation harness")
            print("- create requests: new identity required")
            print("- existing artifacts: read-only references by default")
            print("- protected input paths: refused as create outputs")
            print("- same-identity update: explicit operator update intent required")
        return 0
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
