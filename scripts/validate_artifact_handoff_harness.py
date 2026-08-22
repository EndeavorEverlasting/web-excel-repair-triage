#!/usr/bin/env python3
"""Validate the artifact alias/download handoff harness and optional real file pair."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "harness" / "artifact-handoff"
MANIFEST = DOMAIN / "manifest.v1.json"
CONTRACT = DOMAIN / "contracts" / "share-alias-download.v1.json"
PERCENT_OCTET = re.compile(r"%[0-9A-Fa-f]{2}")


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON: {path.relative_to(ROOT)}: {exc}") from exc


def is_tracked(path: Path) -> bool:
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
    if not is_tracked(path):
        raise ValidationError(f"untracked harness component: {relative}")
    return path


def suffix(name: str) -> str:
    return Path(name).suffix.lower()


def validate_alias_metadata(
    canonical_name: str,
    alias_name: str,
    filesystem_basename: str,
    transport_href: str | None = None,
) -> list[str]:
    errors: list[str] = []
    for label, value in (
        ("canonical_name", canonical_name),
        ("alias_name", alias_name),
        ("filesystem_basename", filesystem_basename),
    ):
        if not value or value != value.strip():
            errors.append(f"{label} is empty or padded")
        if "/" in value or "\\" in value or "\x00" in value:
            errors.append(f"{label} contains a path separator or NUL")
    if PERCENT_OCTET.search(alias_name) or PERCENT_OCTET.search(filesystem_basename):
        errors.append("actual alias filename contains URL percent-encoded octets")
    if filesystem_basename != alias_name:
        errors.append("filesystem basename does not equal the intended alias")
    if not suffix(canonical_name) or suffix(canonical_name) != suffix(alias_name):
        errors.append("alias extension does not match canonical extension")
    if transport_href:
        parsed = urlparse(transport_href)
        decoded_basename = Path(unquote(parsed.path)).name
        if decoded_basename != alias_name:
            errors.append("transport href does not decode to the intended alias basename")
    return errors


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_runtime_pair(canonical: Path, alias: Path, expected_alias: str) -> dict:
    if not canonical.is_file():
        raise ValidationError(f"canonical file does not exist: {canonical}")
    if not alias.is_file():
        raise ValidationError(f"alias file does not exist: {alias}")
    errors = validate_alias_metadata(canonical.name, expected_alias, alias.name)
    if errors:
        raise ValidationError("; ".join(errors))
    canonical_hash = sha256(canonical)
    alias_hash = sha256(alias)
    if canonical_hash != alias_hash:
        raise ValidationError("alias bytes differ from canonical bytes")
    return {
        "schema_version": "share-artifact-alias-handoff-receipt/v1",
        "canonical_name": canonical.name,
        "alias_name": alias.name,
        "extension": canonical.suffix,
        "canonical_sha256": canonical_hash,
        "alias_sha256": alias_hash,
        "byte_identical": True,
    }


def validate_static_harness() -> dict:
    manifest = load_json(MANIFEST)
    if manifest.get("schema_version") != "artifact-handoff-harness/v1":
        raise ValidationError("unsupported artifact handoff harness schema")
    required_components = {
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
    if not isinstance(components, dict) or set(components) != required_components:
        raise ValidationError("artifact handoff component registry drifted")
    for relative in components.values():
        require_file(str(relative))

    skill_text = require_file(str(components["skill"])).read_text(encoding="utf-8")
    for heading in (
        "## Trigger",
        "## Required inputs",
        "## Outputs",
        "## Procedure",
        "## Guardrails",
        "## Validation",
        "## Proof ceiling",
    ):
        if heading not in skill_text:
            raise ValidationError(f"artifact handoff skill missing heading: {heading}")

    contract = load_json(CONTRACT)
    if contract.get("schema_version") != "share-artifact-alias-download/v1":
        raise ValidationError("unsupported alias-download contract schema")
    rules = contract.get("rules")
    if not isinstance(rules, dict) or len(rules) < 6:
        raise ValidationError("alias-download rules are incomplete")
    fixtures = contract.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) < 4:
        raise ValidationError("alias-download fixtures are incomplete")
    fixture_results = []
    for case in fixtures:
        errors = validate_alias_metadata(
            str(case.get("canonical_name", "")),
            str(case.get("alias_name", "")),
            str(case.get("filesystem_basename", "")),
            str(case.get("transport_href", "")) or None,
        )
        actual = not errors
        expected = bool(case.get("expected_valid"))
        if actual != expected:
            raise ValidationError(
                f"fixture {case.get('id')} expected valid={expected} got {actual}: {errors}"
            )
        fixture_results.append({"id": case.get("id"), "valid": actual})

    integration_markers = {
        "harness/CONTEXT.md": "harness/artifact-handoff/CODEBASE_MAP.md",
        "CODEBASE_MAP.md": "artifact-handoff",
        "SKILLS.md": ".ai/skills/share-artifact-alias-handoff/SKILL.md",
        ".githooks/pre-commit": "validate_artifact_handoff_harness.py",
        ".githooks/pre-push": "validate_artifact_handoff_harness.py",
        ".github/workflows/artifact-handoff-harness.yml": "test_artifact_handoff_harness",
    }
    for relative, marker in integration_markers.items():
        text = require_file(relative).read_text(encoding="utf-8")
        if marker not in text:
            raise ValidationError(f"{relative} is missing artifact-handoff integration marker: {marker}")

    return {
        "schema_version": "artifact-handoff-harness-validation/v1",
        "components": sorted(components),
        "fixtures": fixture_results,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical")
    parser.add_argument("--alias", dest="alias_path")
    parser.add_argument("--expected-alias")
    parser.add_argument("--output")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    try:
        report = validate_static_harness()
        runtime_args = [args.canonical, args.alias_path, args.expected_alias]
        if any(runtime_args) and not all(runtime_args):
            raise ValidationError("--canonical, --alias, and --expected-alias must be supplied together")
        if all(runtime_args):
            runtime = validate_runtime_pair(
                Path(args.canonical).expanduser().resolve(),
                Path(args.alias_path).expanduser().resolve(),
                args.expected_alias,
            )
            report["runtime_pair"] = runtime
        if args.output:
            output = Path(args.output)
            if not output.is_absolute():
                output = ROOT / output
            try:
                output.relative_to(ROOT / "Outputs")
            except ValueError as exc:
                raise ValidationError("receipt output must stay under Outputs/") from exc
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if args.summary:
            print("PASS: artifact alias/download handoff harness")
            print(f"- components: {len(report['components'])}")
            print(f"- fixtures: {len(report['fixtures'])}")
            print("- literal percent-encoded filenames: rejected")
            print("- extension drift: rejected")
            print("- byte identity: required for real alias pairs")
        return 0
    except ValidationError as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
