#!/usr/bin/env python3
"""Validate copy-safe operator command envelopes for repository handoffs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness" / "contracts" / "operator-command-envelope.v1.json"
FIXTURES = ROOT / "harness" / "evals" / "fixtures" / "operator-command-cases.v1.json"
TEMPLATE = ROOT / "harness" / "templates" / "Invoke-RemoteHarnessProof.ps1"

EXPECTED_RULES = {
    "OC001": "person_specific_path",
    "OC002": "markdown_link_in_command",
    "OC003": "interactive_shell_exit",
    "OC004": "git_before_directory_gate",
    "OC005": "remote_work_not_pinned",
    "OC006": "dirty_work_not_preserved",
    "OC007": "canonical_artifact_not_resolved",
    "OC008": "failure_not_propagated",
}

PERSON_PATH = re.compile(r"(?i)\b[A-Z]:\\Users\\(?![$%<])[^\\\r\n'\"`]+\\")
MARKDOWN_LINK = re.compile(r"\[[^\]\r\n]+\]\(https?://[^)\r\n]+\)", re.IGNORECASE)
INTERACTIVE_EXIT = re.compile(r"(?im)(?:^|[;{]\s*)exit(?:\s+[^;\r\n}]*)?(?=\s*(?:[;\r\n}]|$))")
NATIVE_GIT = re.compile(r"(?im)^\s*(?:&\s*)?(?:git(?:\.exe)?\b)")
ERROR_STOP = re.compile(r"(?i)\$ErrorActionPreference\s*=\s*['\"]Stop['\"]")
FAILURE_PROPAGATION = re.compile(
    r"(?i)(?:throw\b|Invoke-NativeChecked\b|\$LASTEXITCODE\s*-ne\s*0)"
)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    message: str


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path.relative_to(ROOT)}")
    return payload


def _positions(text: str, needles: Iterable[str]) -> list[int]:
    lowered = text.lower()
    return [pos for needle in needles if (pos := lowered.find(needle.lower())) >= 0]


def audit_command(text: str) -> list[Finding]:
    findings: list[Finding] = []

    if PERSON_PATH.search(text):
        findings.append(
            Finding("OC001", "command embeds a literal C:\\Users\\<name> path")
        )

    if MARKDOWN_LINK.search(text):
        findings.append(
            Finding("OC002", "command contains Markdown hyperlink syntax")
        )

    if INTERACTIVE_EXIT.search(text):
        findings.append(
            Finding("OC003", "command can terminate the interactive PowerShell session")
        )

    git_positions = _positions(
        text,
        ("git fetch", "git.exe fetch", "git status", "git.exe status"),
    )
    if git_positions:
        first_git = min(git_positions)
        gate_positions = _positions(
            text,
            (
                "set-location",
                "push-location",
                "git clone",
                "git.exe clone",
                "gh repo clone",
            ),
        )
        if not gate_positions or min(gate_positions) > first_git:
            findings.append(
                Finding("OC004", "Git runs before a repository/directory gate")
            )

    if "git fetch" in text.lower() or "git.exe fetch" in text.lower():
        pin_markers = (
            "rev-parse fetch_head",
            "rev-parse', 'fetch_head",
            'rev-parse", "fetch_head',
            "remote branch moved",
            "head mismatch",
            "-ne $expected",
            "-ne $commit",
        )
        if not any(marker in text.lower() for marker in pin_markers):
            findings.append(
                Finding("OC005", "remote work is fetched without exact commit verification")
            )

    if re.search(
        r"(?i)(?:reset\s+--hard|clean\s+-[a-z]*f|stash\s+(?:push|drop)|checkout\s+-f)",
        text,
    ):
        findings.append(
            Finding("OC006", "command uses destructive or opaque dirty-work handling")
        )

    normalized = text.replace("\\", "/")
    if (
        ("validate_harness.py" in text or "harness-completeness-report" in text)
        and "harness/artifacts.v1.json" not in normalized
    ):
        findings.append(
            Finding("OC007", "canonical artifact is not resolved from harness/artifacts.v1.json")
        )
    elif "git fetch" in text.lower() and "harness/artifacts.v1.json" not in normalized:
        findings.append(
            Finding("OC007", "remote proof command does not resolve a canonical artifact")
        )

    if NATIVE_GIT.search(text):
        if not ERROR_STOP.search(text) or not FAILURE_PROPAGATION.search(text):
            findings.append(
                Finding("OC008", "native command failures are not converted to terminating errors")
            )

    return findings


def validate_contract() -> dict:
    contract = _load_json(CONTRACT)
    if contract.get("schema_version") != "operator-command-envelope/v1":
        raise ValueError("operator command contract schema drifted")
    if contract.get("contract_id") != "operator-command-envelope":
        raise ValueError("operator command contract ID drifted")
    if contract.get("prompt_surface") != "standard-ai":
        raise ValueError("operator command contract must remain Standard AI")
    if contract.get("failure_classes") != EXPECTED_RULES:
        raise ValueError("operator command failure-class registry drifted")
    if contract.get("canonical_template") != str(TEMPLATE.relative_to(ROOT)).replace("\\", "/"):
        raise ValueError("canonical operator command template path drifted")
    if contract.get("fixtures") != str(FIXTURES.relative_to(ROOT)).replace("\\", "/"):
        raise ValueError("operator command fixture path drifted")
    if contract.get("validator") != "scripts/validate_operator_command_envelope.py":
        raise ValueError("operator command validator path drifted")
    if contract.get("tests") != "tests/test_operator_command_envelope.py":
        raise ValueError("operator command test path drifted")
    if contract.get("canonical_artifact_id") != "harness-completeness-report":
        raise ValueError("operator command canonical artifact ID drifted")
    return contract


def validate_template() -> str:
    if not TEMPLATE.is_file():
        raise ValueError(f"missing canonical template: {TEMPLATE.relative_to(ROOT)}")
    text = TEMPLATE.read_text(encoding="utf-8")
    required = (
        "$env:LOCALAPPDATA",
        "$env:TEMP",
        "WebExcelTriage\\HarnessProof",
        "'clone', '--no-checkout'",
        "'fetch', 'origin', $Branch, '--prune'",
        "'rev-parse', 'FETCH_HEAD'",
        "'checkout', '--detach', $Commit",
        "Preserving dirty proof checkout",
        "scripts\\validate_operator_command_envelope.py",
        "scripts\\validate_harness.py",
        "tests.test_operator_command_envelope",
        "tests.test_harness_contract",
        "harness\\artifacts.v1.json",
        "harness-completeness-report",
        "'diff', '--check', 'origin/main...HEAD'",
        "$ErrorActionPreference = 'Stop'",
        "throw",
    )
    for marker in required:
        if marker not in text:
            raise ValueError(f"canonical template missing marker: {marker}")
    findings = audit_command(text)
    if findings:
        rendered = ", ".join(f"{item.rule_id}:{item.message}" for item in findings)
        raise ValueError(f"canonical template violates envelope rules: {rendered}")
    if "https://github.com/" in text:
        raise ValueError("canonical template contains a raw auto-linkable repository URL")
    if "C:\\Users\\" in text:
        raise ValueError("canonical template contains a person-specific Windows path")
    return text


def validate_fixtures() -> list[dict]:
    payload = _load_json(FIXTURES)
    if payload.get("schema_version") != "operator-command-fixtures/v1":
        raise ValueError("operator command fixture schema drifted")
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) < 8:
        raise ValueError("operator command fixtures are incomplete")
    ids: set[str] = set()
    results: list[dict] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("operator command fixture must be an object")
        case_id = str(case.get("id", "")).strip()
        if not case_id or case_id in ids:
            raise ValueError(f"duplicate or empty fixture ID: {case_id}")
        ids.add(case_id)
        text = case.get("text")
        expected = case.get("expected_violations")
        if not isinstance(text, str) or not isinstance(expected, list):
            raise ValueError(f"fixture {case_id} has invalid text or expected_violations")
        actual = sorted({item.rule_id for item in audit_command(text)})
        expected_ids = sorted(str(item) for item in expected)
        if actual != expected_ids:
            raise ValueError(
                f"fixture {case_id} mismatch: expected={expected_ids} actual={actual}"
            )
        results.append({"id": case_id, "violations": actual})
    return results


def _resolve_report(value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError:
        return resolved
    outputs = (ROOT / "Outputs").resolve()
    try:
        resolved.relative_to(outputs)
    except ValueError as exc:
        raise ValueError("repository-local report must be written under Outputs/") from exc
    return resolved


def validate_all() -> dict:
    contract = validate_contract()
    template = validate_template()
    fixtures = validate_fixtures()
    return {
        "schema_version": "operator-command-envelope-result/v1",
        "status": "PASS",
        "contract": str(CONTRACT.relative_to(ROOT)).replace("\\", "/"),
        "template": str(TEMPLATE.relative_to(ROOT)).replace("\\", "/"),
        "template_sha256": hashlib.sha256(template.encode("utf-8")).hexdigest(),
        "fixture_count": len(fixtures),
        "rules": sorted(EXPECTED_RULES),
        "proof_ceiling": contract["proof_ceiling"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = validate_all()
        report = _resolve_report(args.report)
        if report is not None:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        if args.summary:
            print(
                "Operator command envelope: PASS "
                f"({result['fixture_count']} fixtures, {len(result['rules'])} rules, "
                f"template={result['template_sha256'][:12]})"
            )
        return 0
    except (OSError, TypeError, ValueError) as exc:
        print(f"Operator command envelope: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
