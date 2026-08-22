#!/usr/bin/env python3
"""Fail-closed source-preservation and artifact-derivation harness validator."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "harness" / "artifact-derivation"
MANIFEST = DOMAIN / "manifest.v1.json"
CONTRACT = DOMAIN / "contracts" / "create-new-from-source.v1.json"
LOCAL_PREFIXES = {"path", "repo"}
REMOTE_PREFIXES = {"drive", "file", "library"}
NEGATED_UPDATE = re.compile(
    r"\b(?:do\s+not|don't|dont|never|not)\b(?:\s+[a-z0-9_-]+){0,3}\s+"
    r"(?:update|modify|repair|replace|overwrite)\b",
    re.IGNORECASE,
)


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
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def require_file(relative: str) -> Path:
    path = ROOT / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise ValidationError(f"missing/empty harness component: {relative}")
    if not tracked(path):
        raise ValidationError(f"untracked harness component: {relative}")
    return path


def _split_identity(value: str) -> tuple[str | None, str]:
    raw = str(value or "").strip().replace("\\", "/")
    if not raw:
        raise ValidationError("artifact identity must be non-empty")
    prefix, sep, rest = raw.partition(":")
    if sep and prefix.casefold() in LOCAL_PREFIXES | REMOTE_PREFIXES:
        if not rest.strip():
            raise ValidationError("artifact identity payload must be non-empty")
        return prefix.casefold(), rest.strip()
    return None, raw


def _local_path(identity: str) -> Path | None:
    prefix, payload = _split_identity(identity)
    if prefix not in LOCAL_PREFIXES:
        return None
    raw = Path(payload)
    resolved = raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    if prefix == "repo":
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValidationError("repo: identity escapes the repository root") from exc
    return resolved


def normalize_identity(value: str) -> str:
    prefix, payload = _split_identity(value)
    if prefix in LOCAL_PREFIXES:
        resolved = _local_path(value)
        assert resolved is not None
        canonical = os.path.normcase(str(resolved)).replace("\\", "/")
        return "fs:" + canonical
    if prefix in REMOTE_PREFIXES:
        # Provider/file IDs may be case-sensitive; normalize only the namespace.
        return f"{prefix}:{payload}"
    return payload


def _contains_phrase(text: str, phrase: str) -> bool:
    words = [re.escape(part) for part in phrase.casefold().split()]
    if not words:
        return False
    pattern = r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)"
    return re.search(pattern, text.casefold()) is not None


def classify_intent(request_text: str, *, explicit_update: bool = False) -> str:
    contract = load_json(CONTRACT)
    text = str(request_text or "").strip()
    if not text:
        return "create_new"
    if NEGATED_UPDATE.search(text):
        return "create_new"
    # Mixed create/update wording is ambiguous. Fail closed to a new artifact.
    if any(_contains_phrase(text, token) for token in contract["create_language"]):
        return "create_new"
    if explicit_update and any(
        _contains_phrase(text, token) for token in contract["update_language"]
    ):
        return "update_existing"
    return "create_new"


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_protected_output(output: str, contract: dict[str, Any]) -> Path | None:
    output_path = _local_path(output)
    if output_path is None:
        return None
    for relative in contract.get("protected_input_prefixes", []):
        protected = (ROOT / str(relative)).resolve(strict=False)
        if _is_within(output_path, protected):
            raise ValidationError(
                f"output targets protected input/source path: {relative}"
            )
    return output_path


def _resolve_create_output_existence(
    output: str,
    output_path: Path | None,
    claimed_exists: bool | None,
) -> bool:
    if output_path is not None:
        actual = output_path.exists()
        if claimed_exists is not None and claimed_exists != actual:
            raise ValidationError(
                "caller output-existence assertion disagrees with filesystem state"
            )
        return actual
    prefix, _ = _split_identity(output)
    if prefix in REMOTE_PREFIXES and claimed_exists is None:
        raise ValidationError(
            "remote create output requires explicit existence resolution: "
            "use --output-exists or --output-does-not-exist after provider lookup"
        )
    return bool(claimed_exists)


def validate_envelope(
    *,
    intent: str,
    sources: list[str],
    output: str,
    output_exists: bool | None = None,
    explicit_update: bool = False,
) -> dict[str, Any]:
    contract = load_json(CONTRACT)
    if intent not in {"create_new", "update_existing"}:
        raise ValidationError(f"unsupported intent: {intent}")
    source_ids = [normalize_identity(item) for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValidationError("duplicate source identities")
    output_id = normalize_identity(output)
    output_path = _validate_protected_output(output, contract)

    if intent == "create_new":
        if output_id in source_ids:
            raise ValidationError("create_new output identity equals a source identity")
        if _resolve_create_output_existence(output, output_path, output_exists):
            raise ValidationError("create_new output already exists; choose a new identity")
        return {
            "status": "PASS",
            "intent": intent,
            "source_policy": "read_only_reference",
            "sources": source_ids,
            "output": output_id,
            "source_mutation_allowed": False,
        }

    if not explicit_update:
        raise ValidationError("update_existing requires explicit operator update intent")
    if output_id not in source_ids:
        raise ValidationError(
            "update_existing target must be one of the explicitly named existing source identities"
        )
    return {
        "status": "PASS",
        "intent": intent,
        "source_policy": "explicit_mutation_target",
        "sources": source_ids,
        "output": output_id,
        "source_mutation_allowed": True,
    }


def validate_static_harness() -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != "web-excel-artifact-derivation-harness/v1":
        raise ValidationError("unexpected artifact-derivation manifest schema")
    required = {
        "codebase_map",
        "workflow",
        "artifact_registry",
        "contract",
        "validator",
        "tests",
        "skill",
        "operator_report",
    }
    components = manifest.get("components")
    if not isinstance(components, dict) or set(components) != required:
        raise ValidationError("artifact-derivation component registry drifted")
    for relative in components.values():
        require_file(str(relative))

    contract = load_json(CONTRACT)
    if contract.get("schema_version") != "artifact-derivation-create-new-from-source/v1":
        raise ValidationError("unexpected derivation contract schema")
    if (
        contract.get("default_intent") != "create_new"
        or contract.get("source_role") != "read_only_reference"
    ):
        raise ValidationError("create-new/read-only defaults drifted")
    create = contract.get("create_new", {})
    if (
        create.get("output_must_be_new_identity") is not True
        or create.get("output_may_equal_source_identity") is not False
        or create.get("output_may_already_exist") is not False
    ):
        raise ValidationError("create_new collision rules drifted")
    if (
        contract.get("update_existing", {}).get(
            "requires_explicit_operator_update_intent"
        )
        is not True
    ):
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
            raise ValidationError(
                f"{relative} missing integration marker: {marker}"
            )
    skill = require_file(str(components["skill"])).read_text(encoding="utf-8")
    for heading in (
        "## Trigger",
        "## Required inputs",
        "## Outputs",
        "## Procedure",
        "## Guardrails",
        "## Validation",
        "## Proof ceiling",
    ):
        if heading not in skill:
            raise ValidationError(
                f"artifact derivation skill missing heading: {heading}"
            )
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
    existence = parser.add_mutually_exclusive_group()
    existence.add_argument(
        "--output-exists", dest="output_exists", action="store_const", const=True
    )
    existence.add_argument(
        "--output-does-not-exist",
        dest="output_exists",
        action="store_const",
        const=False,
    )
    parser.set_defaults(output_exists=None)
    parser.add_argument("--explicit-update", action="store_true")
    parser.add_argument("--output-report")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    try:
        report: dict[str, Any] = {"static": validate_static_harness()}
        runtime_requested = bool(
            args.output or args.source or args.request_text or args.intent
        )
        if runtime_requested:
            if not args.output:
                raise ValidationError("runtime preflight requires --output")
            classified = classify_intent(
                args.request_text, explicit_update=args.explicit_update
            )
            if args.intent == "update_existing" and args.request_text and classified != "update_existing":
                raise ValidationError(
                    "request text does not unambiguously authorize update_existing"
                )
            intent = args.intent or classified
            report["runtime"] = validate_envelope(
                intent=intent,
                sources=args.source,
                output=args.output,
                output_exists=args.output_exists,
                explicit_update=args.explicit_update,
            )
        if args.output_report:
            destination = resolve_report(args.output_report)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
        if args.summary:
            print("PASS: artifact derivation/source-preservation harness")
            print("- create requests: new identity required")
            print("- existing artifacts: read-only references by default")
            print("- local path aliases: canonicalized before collision checks")
            print("- local output existence: checked directly")
            print("- remote output existence: explicit provider result required")
            print("- protected input paths: refused as create outputs")
            print("- same-identity update: explicit, unambiguous operator intent required")
        return 0
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
