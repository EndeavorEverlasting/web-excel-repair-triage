#!/usr/bin/env python3
"""Exhaustive prompt-language audit for canonical and effective Prompt Kit prompts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

POLICY_PATH = ROOT / "harness" / "evals" / "prompt-language-audit.v1.json"


class PromptLanguageAuditError(RuntimeError):
    """Raised when the audit contract or registry cannot be evaluated safely."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptLanguageAuditError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PromptLanguageAuditError(f"invalid JSON in {path}: {exc}") from exc


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise PromptLanguageAuditError("prompt-language policy must be a JSON object")
    if payload.get("schema_version") != "prompt-language-audit/v1":
        raise PromptLanguageAuditError("unsupported prompt-language policy schema")
    required = {
        "capability_id",
        "policy_id",
        "actionability_marker",
        "required_prompt_fields",
        "dispositions",
        "fail_severities",
        "lazy_next_step_patterns",
        "required_effective_next_step_phrases",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise PromptLanguageAuditError(f"prompt-language policy is missing fields: {missing}")
    for list_field in (
        "required_prompt_fields",
        "dispositions",
        "fail_severities",
        "lazy_next_step_patterns",
        "required_effective_next_step_phrases",
    ):
        value = payload.get(list_field)
        if not isinstance(value, list) or not value:
            raise PromptLanguageAuditError(f"policy field must be a non-empty array: {list_field}")
    return payload


def load_raw_registry() -> list[dict[str, Any]]:
    import build_prompt_kit_registry

    raw: list[dict[str, Any]] = []
    base = load_json(build_prompt_kit_registry.BASE_REGISTRY)
    if not isinstance(base, list):
        raise PromptLanguageAuditError("base prompt registry must be an array")
    raw.extend(base)
    for path in build_prompt_kit_registry.EXTENSION_REGISTRIES:
        payload = load_json(path)
        prompts = payload.get("prompts") if isinstance(payload, dict) else None
        if not isinstance(prompts, list):
            raise PromptLanguageAuditError(f"extension prompts must be an array: {path}")
        raw.extend(prompts)
    return raw


def load_effective_registry() -> list[dict[str, Any]]:
    import build_prompt_kit_registry

    return build_prompt_kit_registry.load_prompt_registry()


def _finding(rule_id: str, severity: str, field: str, message: str) -> dict[str, str]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "field": field,
        "message": message,
    }


def evaluate_prompt(
    raw_prompt: dict[str, Any],
    effective_prompt: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    prompt_id = str(raw_prompt.get("id", "unknown"))
    findings: list[dict[str, str]] = []

    for field in policy["required_prompt_fields"]:
        if field in {"nextStep", "copyContent"}:
            continue
        value = raw_prompt.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            findings.append(_finding("PLA001", "error", field, "required canonical field is empty"))

    raw_next_step = str(raw_prompt.get("nextStep", ""))
    if not raw_next_step.strip():
        findings.append(_finding("PLA002", "error", "nextStep", "canonical nextStep is empty"))
    else:
        for pattern in policy["lazy_next_step_patterns"]:
            if re.fullmatch(pattern, raw_next_step, flags=re.IGNORECASE):
                findings.append(
                    _finding(
                        "PLA003",
                        "warning",
                        "nextStep",
                        "canonical nextStep is placeholder, generic, or observation-only",
                    )
                )
                break

    raw_copy = str(raw_prompt.get("copyContent", ""))
    if not raw_copy.strip():
        findings.append(_finding("PLA006", "error", "copyContent", "canonical copyContent is empty"))

    marker = str(policy["actionability_marker"])
    effective_copy = str(effective_prompt.get("copyContent", ""))
    if marker not in effective_copy:
        findings.append(
            _finding("PLA004", "error", "copyContent", "effective prompt lacks actionability policy marker")
        )

    effective_next = str(effective_prompt.get("nextStep", "")).lower()
    missing_phrases = [
        phrase
        for phrase in policy["required_effective_next_step_phrases"]
        if str(phrase).lower() not in effective_next
    ]
    if missing_phrases:
        findings.append(
            _finding(
                "PLA005",
                "error",
                "nextStep",
                f"effective nextStep lacks required actionability language: {missing_phrases}",
            )
        )

    disposition = "repair" if findings else "pass"
    return {
        "prompt_id": prompt_id,
        "sequence": str(raw_prompt.get("seq", "")),
        "name": str(raw_prompt.get("name", "")),
        "disposition": disposition,
        "findings": findings,
    }


def evaluate_registry(
    raw_prompts: Iterable[dict[str, Any]] | None = None,
    effective_prompts: Iterable[dict[str, Any]] | None = None,
    *,
    policy: dict[str, Any] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    policy = policy or load_policy()
    raw_list = list(raw_prompts if raw_prompts is not None else load_raw_registry())
    effective_list = list(
        effective_prompts if effective_prompts is not None else load_effective_registry()
    )

    raw_by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for prompt in raw_list:
        prompt_id = str(prompt.get("id", ""))
        if prompt_id in raw_by_id:
            duplicate_ids.append(prompt_id)
        raw_by_id[prompt_id] = prompt
    effective_by_id = {str(prompt.get("id", "")): prompt for prompt in effective_list}

    missing_effective = sorted(set(raw_by_id) - set(effective_by_id))
    extra_effective = sorted(set(effective_by_id) - set(raw_by_id))
    results: list[dict[str, Any]] = []
    for prompt_id in sorted(raw_by_id, key=lambda value: int(str(raw_by_id[value].get("seq", 0)))):
        effective = effective_by_id.get(prompt_id, {})
        results.append(evaluate_prompt(raw_by_id[prompt_id], effective, policy))

    findings = [finding for result in results for finding in result["findings"]]
    error_count = sum(finding["severity"] == "error" for finding in findings)
    warning_count = sum(finding["severity"] == "warning" for finding in findings)
    coverage_complete = (
        not duplicate_ids
        and not missing_effective
        and not extra_effective
        and len(results) == len(raw_list) == len(effective_list)
    )

    if not coverage_complete or error_count:
        verdict = "fail"
    elif strict and warning_count:
        verdict = "fail"
    elif warning_count:
        verdict = "needs-repair"
    else:
        verdict = "pass"

    return {
        "schema_version": "prompt-language-audit-result/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy_id": policy["policy_id"],
        "strict": strict,
        "prompt_count": len(raw_list),
        "effective_prompt_count": len(effective_list),
        "disposition_count": len(results),
        "coverage_complete": coverage_complete,
        "duplicate_ids": sorted(set(duplicate_ids)),
        "missing_effective_ids": missing_effective,
        "extra_effective_ids": extra_effective,
        "error_count": error_count,
        "warning_count": warning_count,
        "verdict": verdict,
        "prompts": results,
    }


def _write_report(
    report: dict[str, Any], output: Path | None, *, print_json: bool = True
) -> None:
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if output is None:
        if print_json:
            print(rendered)
        return
    output = output.expanduser().resolve()
    protected = (ROOT / "Candidates", ROOT / "Active")
    for root in protected:
        try:
            output.relative_to(root.resolve())
        except ValueError:
            continue
        raise PromptLanguageAuditError(f"refusing protected output path: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    print(f"Prompt-language audit report: {output}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail on warning findings.")
    parser.add_argument("--summary", action="store_true", help="Print a compact summary after the report path.")
    args = parser.parse_args(argv)

    try:
        report = evaluate_registry(policy=load_policy(args.policy), strict=args.strict)
        _write_report(report, args.output, print_json=not args.summary)
    except PromptLanguageAuditError as exc:
        print(f"Prompt-language audit failed: {exc}", file=sys.stderr)
        return 2

    if args.summary:
        print(
            "Prompt-language audit "
            f"{report['verdict']}: prompts={report['prompt_count']} "
            f"errors={report['error_count']} warnings={report['warning_count']} "
            f"coverage_complete={report['coverage_complete']}"
        )
    return 0 if report["verdict"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
