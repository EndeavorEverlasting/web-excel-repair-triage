#!/usr/bin/env python3
"""Deterministic Improvement-Candidate Compiler for Prompt Compilation.

Call-stack prototype (non-production):
  owner-native recurrence/eval evidence
    -> fingerprint
    -> recurrence gate
    -> hypothesis catalog
    -> prompt-improvement-candidate/v1
    -> gold regression eval against Language Engine
    -> reviewed_pr_only draft package (never auto-merge / auto-mutate)
    -> optional Outputs/ draft retention
    -> P115-compatible work-request handoff (does not absorb P115 ownership)

Does not own Evidence Spine lifecycle events. Does not write repository source
except optional ephemeral draft retention under Outputs/prompt-improvement-drafts/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prompt_language_compiler as compiler

FIXTURES_ROOT = ROOT / "harness" / "prompt-compilation" / "fixtures"
HYPOTHESIS_CATALOG_PATH = (
    ROOT / "harness" / "prompt-compilation" / "improvement-hypothesis-catalog.v1.json"
)
DEFAULT_DRAFT_RETENTION_DIR = ROOT / "Outputs" / "prompt-improvement-drafts"
P115_WORK_REQUEST_SCHEMA = "evidence-spine-p115-work-request/v1"
P115_HANDOFF_COORDINATOR = "P115"
REMEDIATION_OWNER_BY_AUTHORITY = {
    "language-engine": "P07",
    "prompt-semantics": "P07",
    "execution-profile": "P07",
    "prompt-context": "P07",
    "fixtures": "P07",
}

ELIGIBLE_FINDING_STATES = frozenset({"confirmed_recurrence", "monitoring_reopened"})
AFFECTED_AUTHORITIES = frozenset(
    {"language-engine", "prompt-semantics", "execution-profile", "prompt-context", "fixtures"}
)


class ImprovementCompilerError(ValueError):
    """Raised when improvement compilation fails closed."""


def load_hypothesis_catalog(path: Path = HYPOTHESIS_CATALOG_PATH) -> dict[str, Any]:
    catalog = compiler.load_json(path)
    if not isinstance(catalog, dict):
        raise ImprovementCompilerError("hypothesis catalog must be an object")
    if catalog.get("schema_version") != "prompt-improvement-hypothesis-catalog/v1":
        raise ImprovementCompilerError("unsupported hypothesis catalog schema")
    hypotheses = catalog.get("hypotheses")
    if not isinstance(hypotheses, dict) or not hypotheses:
        raise ImprovementCompilerError("hypothesis catalog requires hypotheses object")
    return catalog


def fingerprint_failure(failure_identity: str) -> str:
    normalized = re.sub(r"\s+", " ", str(failure_identity or "").strip().lower())
    if not normalized:
        raise ImprovementCompilerError("failure_identity required")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_finding(finding: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(finding, dict):
        raise ImprovementCompilerError("finding must be an object")
    failure_identity = str(
        finding.get("failure_identity")
        or finding.get("contract_failure_id")
        or ""
    ).strip()
    if not failure_identity:
        raise ImprovementCompilerError("finding requires failure_identity or contract_failure_id")
    state = str(finding.get("state") or "").strip()
    if not state:
        raise ImprovementCompilerError("finding.state required")
    evidence_refs = finding.get("evidence_refs")
    if evidence_refs is None:
        evidence_refs = finding.get("receipt_ids") or []
    if not isinstance(evidence_refs, list):
        raise ImprovementCompilerError("evidence_refs must be a list")
    refs = [str(item).strip() for item in evidence_refs if str(item).strip()]
    return {
        "failure_identity": failure_identity,
        "state": state,
        "evidence_refs": refs,
        "count": int(finding.get("count") or len(refs) or 0),
        "threshold": int(finding.get("threshold") or 0),
        "fingerprint": fingerprint_failure(failure_identity),
    }


def recurrence_gate(finding: dict[str, Any]) -> dict[str, Any]:
    """Admit only confirmed/reopened recurrence with enough evidence refs."""
    normalized = normalize_finding(finding)
    if normalized["state"] not in ELIGIBLE_FINDING_STATES:
        return {
            "admitted": False,
            "reason": "recurrence_threshold_not_met",
            "finding": normalized,
        }
    if len(normalized["evidence_refs"]) < 1:
        return {
            "admitted": False,
            "reason": "missing_evidence_refs",
            "finding": normalized,
        }
    if normalized["threshold"] and normalized["count"] and normalized["count"] < normalized["threshold"]:
        return {
            "admitted": False,
            "reason": "count_below_owner_threshold",
            "finding": normalized,
        }
    return {"admitted": True, "reason": "ok", "finding": normalized}


def resolve_hypothesis(
    failure_identity: str,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    catalog = catalog or load_hypothesis_catalog()
    hypotheses = catalog["hypotheses"]
    exact = hypotheses.get(failure_identity)
    if isinstance(exact, dict):
        return dict(exact)
    # Prefix match for dotted identities (e.g. parallel_dispatch.modality_weakened).
    for key, value in hypotheses.items():
        if failure_identity == key or failure_identity.startswith(f"{key}."):
            if isinstance(value, dict):
                return dict(value)
    generic = hypotheses.get("generic")
    if isinstance(generic, dict):
        return dict(generic)
    raise ImprovementCompilerError(f"no hypothesis catalog entry for {failure_identity}")


def compile_candidate_from_finding(
    finding: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    gate = recurrence_gate(finding)
    if not gate["admitted"]:
        raise ImprovementCompilerError(f"recurrence gate rejected: {gate['reason']}")
    normalized = gate["finding"]
    hypothesis = resolve_hypothesis(normalized["failure_identity"], catalog=catalog)
    authority = str(hypothesis.get("affected_authority") or "").strip()
    if authority not in AFFECTED_AUTHORITIES:
        raise ImprovementCompilerError(f"invalid affected_authority: {authority}")
    rule = str(hypothesis.get("rule") or "").strip()
    if not rule:
        raise ImprovementCompilerError("hypothesis rule required")
    regressions = hypothesis.get("required_regressions") or []
    if not isinstance(regressions, list) or not regressions:
        raise ImprovementCompilerError("hypothesis required_regressions required")
    candidate = compiler.compile_improvement_candidate(
        failure_identity=normalized["failure_identity"],
        evidence_refs=normalized["evidence_refs"],
        affected_authority=authority,
        rule=rule,
        required_regressions=[str(item) for item in regressions],
        candidate_id=candidate_id,
    )
    return {
        "candidate": candidate,
        "fingerprint": normalized["fingerprint"],
        "hypothesis_id": hypothesis.get("id") or normalized["failure_identity"],
        "gate": gate,
    }


def evaluate_candidate_regressions(
    candidate: dict[str, Any],
    *,
    fixtures_root: Path = FIXTURES_ROOT,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run required gold fixtures; never mutates repository state."""
    candidate = compiler.validate_improvement_candidate(candidate)
    policy = policy or compiler.load_policy()
    results: list[dict[str, Any]] = []
    for regression_id in candidate["required_regressions"]:
        case_dir = fixtures_root / str(regression_id)
        if not case_dir.is_dir():
            raise ImprovementCompilerError(f"missing required regression fixture: {regression_id}")
        fixture_result = compiler.run_fixture(case_dir, policy=policy)
        results.append(fixture_result)
    return {
        "ok": True,
        "candidate_id": candidate["candidate_id"],
        "regressions": results,
    }


def build_pr_draft_package(
    candidate: dict[str, Any],
    eval_result: dict[str, Any],
    *,
    fingerprint: str,
) -> dict[str, Any]:
    """Produce a reviewed_pr_only draft descriptor. Does not open or merge a PR."""
    try:
        candidate = compiler.validate_improvement_candidate(candidate)
    except compiler.PromptCompilationError as exc:
        raise ImprovementCompilerError(str(exc)) from exc
    if candidate.get("promotion_authority") != "reviewed_pr_only":
        raise ImprovementCompilerError("promotion_authority must remain reviewed_pr_only")
    if not eval_result.get("ok"):
        raise ImprovementCompilerError("cannot draft PR for failed evaluation")
    return {
        "schema_version": "prompt-improvement-pr-draft/v1",
        "promotion_authority": "reviewed_pr_only",
        "auto_merge": False,
        "auto_mutate_source": False,
        "candidate": candidate,
        "fingerprint": fingerprint,
        "evaluation": {
            "ok": True,
            "regression_ids": [item.get("case_id") for item in eval_result.get("regressions") or []],
        },
        "proposed_paths": [
            "harness/contracts/prompt-language-compiler-policy.v1.json",
            "harness/prompt-compilation/fixtures/",
            "tests/test_prompt_compilation.py",
        ],
        "operator_gate": "human_review_required_before_git_apply",
    }


def retain_draft_package(
    draft: dict[str, Any],
    *,
    retention_dir: Path | None = None,
) -> Path:
    """Optionally persist an ephemeral PR draft under Outputs/ (never auto-applies)."""
    if not isinstance(draft, dict):
        raise ImprovementCompilerError("draft must be an object")
    if draft.get("promotion_authority") != "reviewed_pr_only":
        raise ImprovementCompilerError("promotion_authority must remain reviewed_pr_only")
    if draft.get("auto_merge") is not False or draft.get("auto_mutate_source") is not False:
        raise ImprovementCompilerError("retained drafts must forbid auto_merge and auto_mutate_source")
    fingerprint = str(draft.get("fingerprint") or "").strip()
    if not fingerprint:
        raise ImprovementCompilerError("draft fingerprint required for retention")
    target_dir = Path(retention_dir) if retention_dir is not None else DEFAULT_DRAFT_RETENTION_DIR
    if not target_dir.is_absolute():
        target_dir = ROOT / target_dir
    try:
        target_dir.relative_to(ROOT / "Outputs")
    except ValueError as exc:
        raise ImprovementCompilerError(
            "draft retention must stay under Outputs/ (ephemeral local evidence only)"
        ) from exc
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"pr-draft-{fingerprint[:16]}.json"
    path.write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    return path


def build_p115_work_request_handoff(
    candidate: dict[str, Any],
    eval_result: dict[str, Any],
    *,
    fingerprint: str,
) -> dict[str, Any]:
    """Emit a P115-compatible work-request handoff without absorbing P115 ownership.

    Shape mirrors evidence-spine-p115-work-request/v1 required ticket fields so P115
    can coordinate recovery. This module does not open queues, mutate P115 contracts,
    or claim recovery ownership.
    """
    try:
        candidate = compiler.validate_improvement_candidate(candidate)
    except compiler.PromptCompilationError as exc:
        raise ImprovementCompilerError(str(exc)) from exc
    if candidate.get("promotion_authority") != "reviewed_pr_only":
        raise ImprovementCompilerError("promotion_authority must remain reviewed_pr_only")
    if not eval_result.get("ok"):
        raise ImprovementCompilerError("cannot hand off failed evaluation to P115")
    authority = str(candidate.get("affected_authority") or "").strip()
    remediation_owner = REMEDIATION_OWNER_BY_AUTHORITY.get(authority)
    if not remediation_owner:
        raise ImprovementCompilerError(f"no remediation owner mapping for authority: {authority}")
    evidence_refs = [str(item).strip() for item in (candidate.get("evidence_refs") or []) if str(item).strip()]
    if not evidence_refs:
        raise ImprovementCompilerError("P115 handoff requires linked evidence refs")
    regressions = [item.get("case_id") for item in eval_result.get("regressions") or []]
    proposed = candidate.get("proposed_change") or {}
    expected_behavior = str(proposed.get("rule") or "").strip()
    if not expected_behavior:
        raise ImprovementCompilerError("P115 handoff requires proposed_change.rule")
    return {
        "compiled": True,
        "schema_version": P115_WORK_REQUEST_SCHEMA,
        "handoff_coordinator": P115_HANDOFF_COORDINATOR,
        "source_subsystem": "prompt-compilation-improvement-compiler",
        "absorbs_p115_ownership": False,
        "remediation_owner": remediation_owner,
        "contract_failure_id": candidate["failure_identity"],
        "linked_receipt_ids": evidence_refs,
        "observed_behavior": (
            f"recurring instruction-construction failure `{candidate['failure_identity']}` "
            f"under authority `{authority}`"
        ),
        "expected_behavior": expected_behavior,
        "acceptance_criteria": (
            "required gold regressions pass; promotion remains reviewed_pr_only; "
            "no auto-merge or auto-mutate"
        ),
        "proof_requirements": (
            "Language Engine fixture eval for "
            + ", ".join(str(item) for item in regressions if item)
            + "; human review before git apply"
        ),
        "promotion_authority": "reviewed_pr_only",
        "auto_merge": False,
        "fingerprint": fingerprint,
        "candidate_id": candidate["candidate_id"],
        "required_regressions": list(candidate.get("required_regressions") or []),
    }


def run_improvement_journey(
    finding: dict[str, Any],
    *,
    catalog: dict[str, Any] | None = None,
    fixtures_root: Path = FIXTURES_ROOT,
    candidate_id: str | None = None,
    retain_draft: bool = False,
    retention_dir: Path | None = None,
) -> dict[str, Any]:
    """Full success call stack for one admitted recurrence finding."""
    compiled = compile_candidate_from_finding(
        finding,
        catalog=catalog,
        candidate_id=candidate_id,
    )
    evaluation = evaluate_candidate_regressions(
        compiled["candidate"],
        fixtures_root=fixtures_root,
    )
    draft = build_pr_draft_package(
        compiled["candidate"],
        evaluation,
        fingerprint=compiled["fingerprint"],
    )
    handoff = build_p115_work_request_handoff(
        compiled["candidate"],
        evaluation,
        fingerprint=compiled["fingerprint"],
    )
    stack = [
        "normalize_finding",
        "recurrence_gate",
        "resolve_hypothesis",
        "compile_improvement_candidate",
        "evaluate_candidate_regressions",
        "build_pr_draft_package",
        "build_p115_work_request_handoff",
    ]
    retained_path: str | None = None
    if retain_draft:
        path = retain_draft_package(draft, retention_dir=retention_dir)
        retained_path = str(path.relative_to(ROOT)).replace("\\", "/")
        stack.append("retain_draft_package")
    return {
        "ok": True,
        "stack": stack,
        "candidate": compiled["candidate"],
        "fingerprint": compiled["fingerprint"],
        "hypothesis_id": compiled["hypothesis_id"],
        "evaluation": evaluation,
        "pr_draft": draft,
        "p115_work_request_handoff": handoff,
        "retained_draft_path": retained_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    journey = sub.add_parser("run-journey", help="Execute improvement call stack for one finding")
    journey.add_argument("--finding", type=Path, required=True)
    journey.add_argument("--candidate-id")
    journey.add_argument("--output", type=Path)
    journey.add_argument(
        "--retain-draft",
        action="store_true",
        help="Optionally write the PR draft under Outputs/prompt-improvement-drafts/",
    )
    journey.add_argument(
        "--retention-dir",
        type=Path,
        help="Override Outputs/ retention directory (must remain under Outputs/)",
    )
    journey.add_argument("--summary", action="store_true")

    gate = sub.add_parser("recurrence-gate", help="Evaluate recurrence admission only")
    gate.add_argument("--finding", type=Path, required=True)
    gate.add_argument("--summary", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        finding = compiler.load_json(args.finding)
        if args.command == "recurrence-gate":
            result = recurrence_gate(finding)
            print(json.dumps(result, indent=2))
            return 0 if result.get("admitted") else 2
        if args.command == "run-journey":
            result = run_improvement_journey(
                finding,
                candidate_id=args.candidate_id,
                retain_draft=bool(args.retain_draft),
                retention_dir=args.retention_dir,
            )
            if args.output:
                args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            if args.summary or not args.output:
                print(json.dumps(result, indent=2))
            return 0
        parser.error(f"unknown command: {args.command}")
        return 2
    except (ImprovementCompilerError, compiler.PromptCompilationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
