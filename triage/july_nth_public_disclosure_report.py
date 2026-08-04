from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

RESULT_SCHEMA = "fun-july-nth-public-disclosure-result/v1"
POLICY_SCHEMA = "fun-july-nth-public-disclosure-policy/v1"
REPORT_SCHEMA = "triage-july-nth-public-disclosure-report/v1"
COUNT_KEYS = (
    "rules_scanned",
    "cell_disclosure_violations",
    "package_disclosure_violations",
    "math_lock_violations",
    "scope_violations",
)


@dataclass(frozen=True)
class ReportBundle:
    report: dict[str, Any]
    markdown: str


def _require_inputs(validation: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if validation.get("schema") != RESULT_SCHEMA:
        errors.append(f"validation schema must be {RESULT_SCHEMA}")
    if policy.get("schema") != POLICY_SCHEMA:
        errors.append(f"policy schema must be {POLICY_SCHEMA}")
    if validation.get("policy_id") != policy.get("policy_id"):
        errors.append("validation and policy identifiers do not match")
    artifact = validation.get("artifact")
    if not isinstance(artifact, dict):
        errors.append("validation artifact object is required")
    else:
        if not isinstance(artifact.get("filename"), str) or not artifact.get("filename"):
            errors.append("artifact filename is required")
        if not isinstance(artifact.get("size"), int) or artifact.get("size", 0) < 1:
            errors.append("artifact size must be a positive integer")
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            errors.append("artifact sha256 must be 64 lowercase hexadecimal characters")
    counts = validation.get("counts")
    if not isinstance(counts, dict):
        errors.append("validation counts object is required")
    else:
        for key in COUNT_KEYS:
            if not isinstance(counts.get(key), int) or counts.get(key, -1) < 0:
                errors.append(f"counts.{key} must be a non-negative integer")
    if not isinstance(validation.get("violations"), list):
        errors.append("validation violations must be a list")
    if not isinstance(validation.get("errors"), list):
        errors.append("validation errors must be a list")
    if not isinstance(policy.get("forbidden_rules"), list) or not policy.get("forbidden_rules"):
        errors.append("policy forbidden_rules must be a non-empty list")
    return errors


def _locations(validation: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in validation.get("violations", []):
        if not isinstance(item, dict):
            continue
        location: dict[str, Any] = {"kind": item.get("kind", "unknown")}
        for key in ("rule_id", "surface", "sheet", "cell", "part"):
            value = item.get(key)
            if isinstance(value, str):
                location[key] = value
        output.append(location)
    return output


def _markdown(report: dict[str, Any]) -> str:
    artifact = report["artifact"]
    counts = report["counts"]
    lines = [
        "# July NTH Public-Disclosure Producer Report",
        "",
        f"- Disposition: **{report['status']}**",
        f"- Policy: `{report['policy_id']}`",
        f"- Artifact: `{artifact['filename']}`",
        f"- Size: `{artifact['size']}` bytes",
        f"- SHA-256: `{artifact['sha256']}`",
        "",
        "## Disclosure posture",
        "",
        f"- Rules scanned: `{counts['rules_scanned']}`",
        f"- Cell disclosure violations: `{counts['cell_disclosure_violations']}`",
        f"- Chart/drawing/package disclosure violations: `{counts['package_disclosure_violations']}`",
        f"- Math-lock violations: `{counts['math_lock_violations']}`",
        f"- Scope violations: `{counts['scope_violations']}`",
        "",
        "The July public workbook retains confirmed math and ordinary workstream records while excluding private rationale and evidence mechanics.",
        "",
    ]
    if report["locations"]:
        lines.extend(["## Violation locations", ""])
        for item in report["locations"]:
            fields = [f"kind={item['kind']}"]
            for key in ("rule_id", "surface", "sheet", "cell", "part"):
                if key in item:
                    fields.append(f"{key}={item[key]}")
            lines.append("- " + "; ".join(fields))
        lines.append("")
    if report["errors"]:
        lines.extend(["## Report errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    lines.extend(["## Validation boundary", "", report["proof_ceiling"], ""])
    return "\n".join(lines)


def build_report(validation: dict[str, Any], policy: dict[str, Any]) -> ReportBundle:
    errors = _require_inputs(validation, policy)
    artifact = validation.get("artifact") if isinstance(validation.get("artifact"), dict) else {}
    counts = validation.get("counts") if isinstance(validation.get("counts"), dict) else {}
    zero_violations = all(counts.get(key, 0) == 0 for key in (
        "cell_disclosure_violations",
        "package_disclosure_violations",
        "math_lock_violations",
        "scope_violations",
    ))
    status = "PASS" if (
        not errors
        and validation.get("status") == "PASS"
        and zero_violations
        and not validation.get("errors")
    ) else "FAIL"
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "policy_id": validation.get("policy_id") or policy.get("policy_id"),
        "artifact": {
            "filename": artifact.get("filename"),
            "size": artifact.get("size"),
            "sha256": artifact.get("sha256"),
        },
        "counts": {key: counts.get(key, 0) for key in COUNT_KEYS},
        "locations": _locations(validation),
        "errors": [*errors, *[str(value) for value in validation.get("errors", [])]],
        "upstream_status": validation.get("status"),
        "proof_ceiling": (
            "Confirms that the FUN July public-disclosure result is complete and passing. "
            "It does not independently prove workbook math, attendance truth, compensation compliance, or legal conclusions."
        ),
    }
    markdown = _markdown(report)

    serialized = json.dumps(report, sort_keys=True) + "\n" + markdown
    leaked_rules: list[str] = []
    for rule in policy.get("forbidden_rules", []):
        if not isinstance(rule, dict) or not isinstance(rule.get("pattern"), str):
            continue
        try:
            if re.search(rule["pattern"], serialized, re.IGNORECASE):
                leaked_rules.append(str(rule.get("id", "unknown")))
        except re.error:
            continue
    if leaked_rules:
        report["status"] = "FAIL"
        report["errors"].append("producer report matched one or more protected disclosure rules")
        markdown = _markdown(report)
    return ReportBundle(report=report, markdown=markdown)
