#!/usr/bin/env python3
"""Deterministic Prompt Language Compiler (Context → Semantics × Profile → Effective Prompt)."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "harness" / "contracts" / "prompt-language-compiler-policy.v1.json"
FIXTURES_ROOT = ROOT / "harness" / "prompt-compilation" / "fixtures"

REQUIRED_NON_WEAKENABLE = frozenset(
    {
        "safety",
        "evidence_truth",
        "destructive_operation_rules",
        "privacy",
        "explicit_user_scope",
        "required_acceptance_gates",
    }
)


class PromptCompilationError(ValueError):
    """Raised when compilation inputs or outputs violate contracts."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PromptCompilationError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PromptCompilationError(f"invalid JSON in {path}: {exc}") from exc


def canonical_sha256(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    policy = load_json(path)
    if not isinstance(policy, dict):
        raise PromptCompilationError("language compiler policy must be an object")
    if policy.get("schema_version") != "prompt-language-compiler-policy/v1":
        raise PromptCompilationError("unsupported language compiler policy schema")
    for key in (
        "language_engine_revision",
        "must_weakening_patterns",
        "action_renderers",
        "when_predicates",
        "non_weakenable_constraints",
        "promotion_authority",
    ):
        if key not in policy:
            raise PromptCompilationError(f"policy missing field: {key}")
    if policy.get("promotion_authority") != "reviewed_pr_only":
        raise PromptCompilationError("promotion_authority must be reviewed_pr_only")
    if set(policy["non_weakenable_constraints"]) != REQUIRED_NON_WEAKENABLE:
        raise PromptCompilationError("policy non_weakenable_constraints mismatch")
    return policy


def _require_schema_version(payload: dict[str, Any], expected: str) -> None:
    if payload.get("schema_version") != expected:
        raise PromptCompilationError(f"expected schema_version {expected}, got {payload.get('schema_version')}")


def validate_semantics(semantics: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(semantics, dict):
        raise PromptCompilationError("semantics must be an object")
    _require_schema_version(semantics, "prompt-semantics/v1")
    for key in ("prompt_id", "goal", "obligations", "invariants"):
        if key not in semantics:
            raise PromptCompilationError(f"semantics missing field: {key}")
    if not isinstance(semantics["obligations"], list) or not semantics["obligations"]:
        raise PromptCompilationError("semantics.obligations must be a non-empty array")
    for obligation in semantics["obligations"]:
        if not isinstance(obligation, dict):
            raise PromptCompilationError("obligation must be an object")
        for key in ("id", "when", "modality", "action", "proof", "failure_state"):
            if key not in obligation:
                raise PromptCompilationError(f"obligation missing field: {key}")
        if obligation["modality"] not in {"MUST", "SHOULD", "MAY"}:
            raise PromptCompilationError(f"invalid modality: {obligation['modality']}")
    return semantics


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise PromptCompilationError("profile must be an object")
    _require_schema_version(profile, "prompt-execution-profile/v1")
    name = profile.get("profile")
    if name not in {"exhaustive", "efficient"}:
        raise PromptCompilationError(f"invalid profile: {name}")
    constraints = set(profile.get("non_weakenable_constraints") or [])
    if constraints != REQUIRED_NON_WEAKENABLE:
        missing = sorted(REQUIRED_NON_WEAKENABLE - constraints)
        raise PromptCompilationError(f"profile weakens or omits constraints: {missing}")
    expected = {
        "exhaustive": {
            "compute_policy": "maximize_useful_compute_until_fixed_point",
            "parallel_policy": "dispatch_when_safe_parallel_width_exists",
            "hypothesis_policy": "falsify_material_alternatives",
            "validation_policy": "advance_all_executable_contracts",
            "stop_policy": "evidence_defined_fixed_point",
        },
        "efficient": {
            "compute_policy": "minimum_sufficient_compute",
            "parallel_policy": "parallelize_when_expected_gain_exceeds_coordination_cost",
            "hypothesis_policy": "test_alternatives_only_when_materially_ambiguous",
            "validation_policy": "minimum_authoritative_acceptance_set",
            "stop_policy": "sufficient_proof_for_requested_scope",
        },
    }[name]
    for key, value in expected.items():
        if profile.get(key) != value:
            raise PromptCompilationError(f"profile {name} requires {key}={value}")
    return profile


def validate_context(context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise PromptCompilationError("context must be an object")
    _require_schema_version(context, "prompt-context/v1")
    for key in ("repository", "execution", "history", "evidence"):
        if key not in context or not isinstance(context[key], dict):
            raise PromptCompilationError(f"context.{key} must be an object")
    execution = context["execution"]
    for key in ("parallel_width", "safe_capacity"):
        if not isinstance(execution.get(key), int) or execution[key] < 0:
            raise PromptCompilationError(f"context.execution.{key} must be a non-negative integer")
    # Context Engine must not claim event ownership.
    forbidden_keys = {"events", "event_bus", "lifecycle_envelope", "raw_conversation", "transcript"}
    if forbidden_keys.intersection(context):
        raise PromptCompilationError("prompt-context must not own events or raw conversation fields")
    return context


def validate_improvement_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise PromptCompilationError("improvement candidate must be an object")
    _require_schema_version(candidate, "prompt-improvement-candidate/v1")
    for key in (
        "candidate_id",
        "failure_identity",
        "evidence_refs",
        "affected_authority",
        "proposed_change",
        "required_regressions",
        "promotion_authority",
    ):
        if key not in candidate:
            raise PromptCompilationError(f"improvement candidate missing field: {key}")
    if candidate.get("promotion_authority") != "reviewed_pr_only":
        raise PromptCompilationError("improvement candidates may not self-authorize")
    if not isinstance(candidate["evidence_refs"], list) or not candidate["evidence_refs"]:
        raise PromptCompilationError("evidence_refs must be a non-empty array")
    if not isinstance(candidate["required_regressions"], list) or not candidate["required_regressions"]:
        raise PromptCompilationError("required_regressions must be a non-empty array")
    return candidate


def predicate_satisfied(when: str, context: dict[str, Any], policy: dict[str, Any]) -> bool:
    predicates = policy.get("when_predicates") or {}
    spec = predicates.get(when)
    execution = context.get("execution") or {}
    if spec is None:
        # Unknown predicates are not auto-satisfied.
        return False
    requires = spec.get("requires") or {}
    dep_width = execution.get("dependency_ready_width")
    if dep_width is None:
        dep_width = execution.get("parallel_width", 0)
    safe_capacity = execution.get("safe_capacity", 0)
    if dep_width < int(requires.get("min_dependency_ready_width", 0)):
        return False
    if safe_capacity < int(requires.get("min_safe_capacity", 0)):
        return False
    return True


def find_weakening(text: str, policy: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for pattern in policy["must_weakening_patterns"]:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def render_obligation(obligation: dict[str, Any], policy: dict[str, Any]) -> str:
    action = obligation["action"]
    renderer = (policy.get("action_renderers") or {}).get(action)
    if renderer is None:
        return (
            f"- Obligation `{obligation['id']}` ({obligation['modality']}): execute `{action}` "
            f"with proof `{obligation['proof']}` and failure disposition `{obligation['failure_state']}`."
        )
    phrases = renderer.get("imperative_required_phrases") or []
    lines = [f"- Obligation `{obligation['id']}` ({obligation['modality']}):"]
    for phrase in phrases:
        lines.append(f"  - {phrase}")
    if renderer.get("failure_state_required"):
        lines.append(f"  - typed failure disposition {obligation['failure_state']}")
    if renderer.get("proof_required"):
        lines.append(f"  - proof requirement: {obligation['proof']}")
    return "\n".join(lines)


def render(
    semantics: dict[str, Any],
    profile: dict[str, Any],
    context: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    effective_prompt_override: str | None = None,
) -> dict[str, Any]:
    """Compile IRs into effective prompt text and a build receipt."""
    policy = policy or load_policy()
    semantics = validate_semantics(semantics)
    profile = validate_profile(profile)
    context = validate_context(context)

    activated: list[dict[str, Any]] = []
    for obligation in semantics["obligations"]:
        if obligation["modality"] == "MUST" and predicate_satisfied(obligation["when"], context, policy):
            activated.append(obligation)

    if effective_prompt_override is None:
        lines = [
            f"# Effective prompt {semantics['prompt_id']}",
            "",
            f"Goal: {semantics['goal']}",
            "",
            f"Execution profile: {profile['profile']}",
            f"Compute policy: {profile['compute_policy']}",
            f"Parallel policy: {profile['parallel_policy']}",
            f"Stop policy: {profile['stop_policy']}",
            "",
            "Non-weakenable constraints:",
        ]
        for constraint in sorted(REQUIRED_NON_WEAKENABLE):
            lines.append(f"- {constraint}")
        lines.append("")
        lines.append("Invariants:")
        for invariant in semantics["invariants"]:
            lines.append(f"- {invariant}")
        lines.append("")
        lines.append("Activated obligations:")
        if not activated:
            lines.append("- none")
        else:
            for obligation in activated:
                lines.append(render_obligation(obligation, policy))
        lines.append("")
        lines.append(
            "Do not weaken safety, evidence truth, destructive-operation rules, privacy, "
            "explicit user scope, or required acceptance gates."
        )
        effective_prompt = "\n".join(lines) + "\n"
    else:
        effective_prompt = effective_prompt_override

    must_activated = [item for item in activated if item["modality"] == "MUST"]
    if must_activated:
        weakening_hits = find_weakening(effective_prompt, policy)
        if weakening_hits:
            raise PromptCompilationError(
                "non-weakening validator rejected permissive constructs for MUST obligations: "
                + ", ".join(sorted(set(weakening_hits)))
            )

    for obligation in must_activated:
        renderer = (policy.get("action_renderers") or {}).get(obligation["action"]) or {}
        for phrase in renderer.get("imperative_required_phrases") or []:
            if phrase not in effective_prompt:
                raise PromptCompilationError(
                    f"MUST obligation {obligation['id']} missing required phrase: {phrase}"
                )
        if renderer.get("failure_state_required") and obligation["failure_state"] not in effective_prompt:
            raise PromptCompilationError(
                f"MUST obligation {obligation['id']} missing failure disposition {obligation['failure_state']}"
            )
        if renderer.get("proof_required") and obligation["proof"] not in effective_prompt:
            raise PromptCompilationError(
                f"MUST obligation {obligation['id']} missing proof requirement {obligation['proof']}"
            )

    receipt = {
        "schema_version": "prompt-build-receipt/v1",
        "prompt_id": semantics["prompt_id"],
        "semantic_sha256": canonical_sha256(semantics),
        "context_sha256": canonical_sha256(context),
        "profile_sha256": canonical_sha256(profile),
        "execution_profile": profile["profile"],
        "language_engine_revision": policy["language_engine_revision"],
        "effective_prompt_sha256": hashlib.sha256(effective_prompt.encode("utf-8")).hexdigest(),
        "activated_obligations": [item["id"] for item in activated],
        "non_weakening_passed": True,
    }
    return {"effective_prompt": effective_prompt, "receipt": receipt}


def compile_improvement_candidate(
    *,
    failure_identity: str,
    evidence_refs: list[str],
    affected_authority: str,
    rule: str,
    required_regressions: list[str],
    candidate_id: str | None = None,
) -> dict[str, Any]:
    if not evidence_refs:
        raise PromptCompilationError("improvement candidate requires evidence_refs")
    if not required_regressions:
        raise PromptCompilationError("improvement candidate requires required_regressions")
    candidate = {
        "schema_version": "prompt-improvement-candidate/v1",
        "candidate_id": candidate_id or f"IC-{re.sub(r'[^A-Za-z0-9._-]+', '-', failure_identity)[:60]}",
        "failure_identity": failure_identity,
        "evidence_refs": list(evidence_refs),
        "affected_authority": affected_authority,
        "proposed_change": {"rule": rule},
        "required_regressions": list(required_regressions),
        "promotion_authority": "reviewed_pr_only",
    }
    return validate_improvement_candidate(candidate)


def load_fixture_case(case_dir: Path) -> dict[str, Any]:
    return {
        "case": load_json(case_dir / "case.json"),
        "semantics": load_json(case_dir / "semantics.json"),
        "profile": load_json(case_dir / "profile.json"),
        "context": load_json(case_dir / "context.json"),
    }


def run_fixture(case_dir: Path, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    bundle = load_fixture_case(case_dir)
    case = bundle["case"]
    expect = case.get("expect") or {}
    result = render(bundle["semantics"], bundle["profile"], bundle["context"], policy=policy)
    prompt = result["effective_prompt"]
    activated = result["receipt"]["activated_obligations"]
    expected_activated = expect.get("activated_obligations") or []
    if activated != expected_activated:
        raise PromptCompilationError(
            f"{case_dir.name}: activated_obligations={activated}, expected={expected_activated}"
        )
    for phrase in expect.get("required_phrases") or []:
        if phrase not in prompt:
            raise PromptCompilationError(f"{case_dir.name}: missing required phrase: {phrase}")
    for phrase in expect.get("forbidden_phrases") or []:
        if phrase.lower() in prompt.lower():
            raise PromptCompilationError(f"{case_dir.name}: forbidden phrase present: {phrase}")

    # Explicit adversarial check: weakening override must be rejected.
    if expect.get("must_reject_weakening"):
        weak = (
            "Consider parallel dispatch where useful. Agents could dispatch lanes "
            "if appropriate and may parallelize."
        )
        try:
            render(
                bundle["semantics"],
                bundle["profile"],
                bundle["context"],
                policy=policy,
                effective_prompt_override=weak,
            )
        except PromptCompilationError:
            pass
        else:
            raise PromptCompilationError(f"{case_dir.name}: weakening override was incorrectly accepted")

    return {
        "case_id": case.get("case_id") or case_dir.name,
        "ok": True,
        "receipt": result["receipt"],
    }


def validate_fixtures(fixtures_root: Path = FIXTURES_ROOT, *, summary: bool = False) -> int:
    policy = load_policy()
    if not fixtures_root.is_dir():
        raise PromptCompilationError(f"fixtures root missing: {fixtures_root}")
    case_dirs = sorted(path for path in fixtures_root.iterdir() if path.is_dir())
    if not case_dirs:
        raise PromptCompilationError("no prompt-compilation fixtures found")
    results = []
    for case_dir in case_dirs:
        results.append(run_fixture(case_dir, policy=policy))
    if summary:
        print(json.dumps({"ok": True, "cases": len(results), "results": results}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    render_cmd = sub.add_parser("render", help="Compile semantics × profile × context")
    render_cmd.add_argument("--semantics", type=Path, required=True)
    render_cmd.add_argument("--profile", type=Path, required=True)
    render_cmd.add_argument("--context", type=Path, required=True)
    render_cmd.add_argument("--output-prompt", type=Path)
    render_cmd.add_argument("--output-receipt", type=Path)
    render_cmd.add_argument("--summary", action="store_true")

    fixtures_cmd = sub.add_parser("validate-fixtures", help="Validate gold compilation fixtures")
    fixtures_cmd.add_argument("--fixtures-root", type=Path, default=FIXTURES_ROOT)
    fixtures_cmd.add_argument("--summary", action="store_true")

    candidate_cmd = sub.add_parser("emit-improvement-candidate", help="Emit a reviewed_pr_only candidate")
    candidate_cmd.add_argument("--failure-identity", required=True)
    candidate_cmd.add_argument("--evidence-ref", action="append", required=True)
    candidate_cmd.add_argument("--affected-authority", required=True)
    candidate_cmd.add_argument("--rule", required=True)
    candidate_cmd.add_argument("--required-regression", action="append", required=True)
    candidate_cmd.add_argument("--candidate-id")
    candidate_cmd.add_argument("--output", type=Path)
    candidate_cmd.add_argument("--summary", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-fixtures":
            return validate_fixtures(args.fixtures_root, summary=args.summary)
        if args.command == "render":
            result = render(
                load_json(args.semantics),
                load_json(args.profile),
                load_json(args.context),
            )
            if args.output_prompt:
                args.output_prompt.write_text(result["effective_prompt"], encoding="utf-8")
            if args.output_receipt:
                args.output_receipt.write_text(
                    json.dumps(result["receipt"], indent=2) + "\n", encoding="utf-8"
                )
            if args.summary or not (args.output_prompt or args.output_receipt):
                print(json.dumps(result["receipt"], indent=2))
            return 0
        if args.command == "emit-improvement-candidate":
            candidate = compile_improvement_candidate(
                failure_identity=args.failure_identity,
                evidence_refs=args.evidence_ref,
                affected_authority=args.affected_authority,
                rule=args.rule,
                required_regressions=args.required_regression,
                candidate_id=args.candidate_id,
            )
            if args.output:
                args.output.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
            if args.summary or not args.output:
                print(json.dumps(candidate, indent=2))
            return 0
        parser.error(f"unknown command: {args.command}")
        return 2
    except PromptCompilationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
