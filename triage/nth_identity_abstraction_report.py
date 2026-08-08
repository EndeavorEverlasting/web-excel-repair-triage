from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

RESULT_SCHEMA = "fun-nth-identity-abstraction-result/v1"
POLICY_SCHEMA = "fun-nth-identity-abstraction-policy/v1"
REPORT_SCHEMA = "triage-nth-abstract-detail-report/v1"
COUNT_KEYS = (
    "identities_scanned",
    "allowed_row_identity_occurrences",
    "identity_violations",
    "special_case_label_violations",
    "package_identity_violations",
)


@dataclass(frozen=True)
class ReportBundle:
    report: dict[str, Any]
    markdown: str


def _identity_tokens(policy: dict[str, Any]) -> tuple[str, ...]:
    tokens: list[str] = []
    for item in policy.get("identity_tokens", []):
        if not isinstance(item, dict):
            continue
        token = item.get("token")
        if isinstance(token, str) and token:
            tokens.append(token)
        for alias in item.get("aliases", []):
            if isinstance(alias, str) and alias:
                tokens.append(alias)
    return tuple(tokens)


def _require_inputs(validation: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if validation.get("schema") != RESULT_SCHEMA:
        errors.append(f"validation schema must be {RESULT_SCHEMA}")
    if policy.get("schema") != POLICY_SCHEMA:
        errors.append(f"policy schema must be {POLICY_SCHEMA}")
    if not isinstance(validation.get("policy_id"), str) or not validation.get("policy_id"):
        errors.append("validation policy_id is required")
    if not isinstance(policy.get("policy_id"), str) or not policy.get("policy_id"):
        errors.append("policy policy_id is required")
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
        if artifact.get("artifact_type") not in {"share_ready", "internal", "fixture"}:
            errors.append("artifact type is invalid")
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
    if not isinstance(policy.get("identity_tokens"), list) or not policy.get("identity_tokens"):
        errors.append("policy identity_tokens must be a non-empty list")
    return errors


def _sanitized_locations(validation: dict[str, Any]) -> list[dict[str, Any]]:
    locations: list[dict[str, Any]] = []
    for item in validation.get("violations", []):
        if not isinstance(item, dict):
            continue
        location: dict[str, Any] = {"kind": item.get("kind", "unknown")}
        for key in ("sheet", "cell", "part", "identity_index", "label_index"):
            value = item.get(key)
            if isinstance(value, (str, int)):
                location[key] = value
        locations.append(location)
    return locations


def _markdown(report: dict[str, Any]) -> str:
    artifact = report["artifact"]
    counts = report["counts"]
    lines = [
        "# NTH Abstract-Detail Producer Report",
        "",
        f"- Disposition: **{report['status']}**",
        f"- Policy: `{report['policy_id']}`",
        f"- Artifact: `{artifact['filename']}`",
        f"- Artifact type: `{artifact['artifact_type']}`",
        f"- Size: `{artifact['size']}` bytes",
        f"- SHA-256: `{artifact['sha256']}`",
        "",
        "## Identity posture",
        "",
        f"- Identities scanned: `{counts['identities_scanned']}`",
        f"- Allowed ordinary-row occurrences: `{counts['allowed_row_identity_occurrences']}`",
        f"- Identity violations: `{counts['identity_violations']}`",
        f"- Special-case-label violations: `{counts['special_case_label_violations']}`",
        f"- Chart/drawing/package identity violations: `{counts['package_identity_violations']}`",
        "",
        "Names are permitted only in policy-approved ordinary attendance or dated-work identity ranges. Administrative summaries, KPI cards, charts, controls, notes, defenses, and reports remain workstream-centered.",
        "",
    ]
    if report["locations"]:
        lines.extend(["## Violation locations", ""])
        for item in report["locations"]:
            fields = [f"kind={item['kind']}"]
            for key in ("sheet", "cell", "part", "identity_index", "label_index"):
                if key in item:
                    fields.append(f"{key}={item[key]}")
            lines.append("- " + "; ".join(fields))
        lines.append("")
    if report["errors"]:
        lines.extend(["## Report errors", ""])
        lines.extend(f"- {error}" for error in report["errors"])
        lines.append("")
    lines.extend([
        "## Proof ceiling",
        "",
        report["proof_ceiling"],
        "",
    ])
    return "\n".join(lines)


def build_report(validation: dict[str, Any], policy: dict[str, Any]) -> ReportBundle:
    errors = _require_inputs(validation, policy)
    artifact = validation.get("artifact") if isinstance(validation.get("artifact"), dict) else {}
    counts = validation.get("counts") if isinstance(validation.get("counts"), dict) else {key: 0 for key in COUNT_KEYS}
    upstream_pass = validation.get("status") == "PASS"
    zero_violations = all(counts.get(key, 0) == 0 for key in (
        "identity_violations",
        "special_case_label_violations",
        "package_identity_violations",
    ))
    no_upstream_errors = not validation.get("errors")
    status = "PASS" if not errors and upstream_pass and zero_violations and no_upstream_errors else "FAIL"
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "policy_id": validation.get("policy_id") or policy.get("policy_id"),
        "artifact": {
            "filename": artifact.get("filename"),
            "size": artifact.get("size"),
            "sha256": artifact.get("sha256"),
            "artifact_type": artifact.get("artifact_type"),
        },
        "counts": {key: counts.get(key, 0) for key in COUNT_KEYS},
        "locations": _sanitized_locations(validation),
        "errors": [*errors, *[str(value) for value in validation.get("errors", [])]],
        "upstream_status": validation.get("status"),
        "proof_ceiling": (
            "Confirms that the FUN-compatible identity-abstraction validation result is complete and passing. "
            "It does not independently prove workbook bytes, evidence truth, attendance truth, allocation truth, or client acceptance."
        ),
    }
    markdown = _markdown(report)
    serialized = json.dumps(report, sort_keys=True) + "\n" + markdown
    leaked = [token for token in _identity_tokens(policy) if token.casefold() in serialized.casefold()]
    if leaked:
        report["status"] = "FAIL"
        report["errors"].append("producer report echoed one or more protected identity tokens")
        markdown = _markdown(report)
    return ReportBundle(report=report, markdown=markdown)
