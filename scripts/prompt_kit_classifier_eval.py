#!/usr/bin/env python3
"""Evaluate Prompt Finder routing against versioned canonical-runtime cases."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_prompt_kit
from scripts import build_prompt_kit_registry

POLICY_PATH = ROOT / "harness" / "evals" / "prompt-finder-classifier.v1.json"
CASES_PATH = ROOT / "harness" / "evals" / "fixtures" / "prompt-finder-classifier-cases.v1.json"
SEARCH_RUNTIME = ROOT / "docs" / "prompt-kit.js"
GUIDED_RUNTIME = ROOT / "docs" / "prompt-kit-guided-recommendations.js"
DEFAULT_OUTPUT = ROOT / "Outputs" / "prompt-finder-classifier-eval.json"
OUTPUT_ROOT = ROOT / "Outputs"
PROMPT_FIELDS = (
    "id",
    "seq",
    "name",
    "type",
    "class",
    "useWhen",
    "sprintRole",
    "proofGate",
    "copyContent",
    "keywords",
    "discoveryRank",
)


class EvalError(RuntimeError):
    """Raised when the eval harness itself is invalid or cannot execute."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalError(f"missing required eval file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise EvalError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvalError(f"expected JSON object: {path.relative_to(ROOT)}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_head() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip() or None


def _extract_between(text: str, start_marker: str, end_marker: str, source: Path) -> str:
    try:
        start = text.index(start_marker)
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise EvalError(
            f"canonical runtime markers drifted in {source.relative_to(ROOT)}: "
            f"{start_marker!r} -> {end_marker!r}"
        ) from exc
    return text[start:end]


def _registry_source_paths() -> tuple[Path, ...]:
    """Return every file that can influence load_prompt_kit_registry()."""
    candidates = [
        Path(__file__),
        Path(build_prompt_kit.__file__),
        Path(build_prompt_kit_registry.__file__),
        Path(build_prompt_kit_registry.prompt_classification.__file__),
        build_prompt_kit_registry.BASE_REGISTRY,
        *build_prompt_kit_registry.EXTENSION_REGISTRIES,
        *build_prompt_kit_registry.CONTENT_REGISTRIES,
        build_prompt_kit_registry.PROMPT_OVERRIDES,
        build_prompt_kit_registry.ACTIONABILITY_POLICY,
        build_prompt_kit_registry.DISPLAY_ORDER_POLICY,
    ]
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = Path(candidate).resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return tuple(unique)


def _all_source_paths() -> tuple[Path, ...]:
    candidates = [POLICY_PATH, CASES_PATH, SEARCH_RUNTIME, GUIDED_RUNTIME, *_registry_source_paths()]
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = Path(candidate).resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return tuple(unique)


def _resolve_output(output: Path) -> Path:
    candidate = output.expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    resolved = candidate.resolve()
    output_root = OUTPUT_ROOT.resolve()
    try:
        relative = resolved.relative_to(output_root)
    except ValueError as exc:
        raise EvalError(f"output must be inside Outputs/: {resolved}") from exc
    if relative == Path("."):
        raise EvalError("output must name a file below Outputs/")
    source_paths = set(_all_source_paths())
    if resolved in source_paths:
        raise EvalError(f"output path collides with an eval source: {resolved}")
    return resolved


def _expected_target() -> dict[str, str]:
    return {
        "runtime": str(GUIDED_RUNTIME.relative_to(ROOT)),
        "classifier_function": "scorePromptFinderAnswers",
        "shared_search_runtime": str(SEARCH_RUNTIME.relative_to(ROOT)),
        "registry_builder": str(Path(build_prompt_kit_registry.__file__).resolve().relative_to(ROOT)),
    }


def _validate_target(policy: dict[str, Any]) -> dict[str, str]:
    declared = policy.get("target")
    expected = _expected_target()
    if declared != expected:
        raise EvalError(
            "eval policy target does not match the executed canonical runtime: "
            f"expected={expected!r} declared={declared!r}"
        )
    return expected


def _project_registry() -> list[dict[str, Any]]:
    try:
        prompts = build_prompt_kit_registry.load_prompt_kit_registry()
    except SystemExit as exc:
        raise EvalError(f"canonical Prompt Kit registry failed to load: {exc}") from exc
    projected: list[dict[str, Any]] = []
    for prompt in prompts:
        projected.append({field: prompt.get(field) for field in PROMPT_FIELDS})
    return projected


def _projected_registry_sha256(prompts: list[dict[str, Any]]) -> str:
    canonical = json.dumps(
        prompts,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256_bytes(canonical)


def _validate_contract(policy: dict[str, Any], fixtures: dict[str, Any]) -> list[dict[str, Any]]:
    if policy.get("schema_version") != "prompt-finder-classifier-eval/v1":
        raise EvalError("unsupported Prompt Finder classifier eval policy schema")
    if fixtures.get("schema_version") != "prompt-finder-classifier-cases/v1":
        raise EvalError("unsupported Prompt Finder classifier fixture schema")
    cases = fixtures.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvalError("classifier eval fixtures must contain at least one case")

    seen_ids: set[str] = set()
    seen_kinds: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise EvalError("every classifier eval case must be an object")
        case_id = case.get("id")
        kind = case.get("kind")
        answers = case.get("answers")
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvalError("every classifier eval case needs a non-empty id")
        if case_id in seen_ids:
            raise EvalError(f"duplicate classifier eval case id: {case_id}")
        if not isinstance(kind, str) or not kind.strip():
            raise EvalError(f"classifier eval case {case_id} needs a kind")
        if not isinstance(answers, dict):
            raise EvalError(f"classifier eval case {case_id} answers must be an object")
        seen_ids.add(case_id)
        seen_kinds.add(kind)

    required_kinds = set(policy.get("required_case_kinds", []))
    missing_kinds = sorted(required_kinds - seen_kinds)
    if missing_kinds:
        raise EvalError(f"classifier eval case kinds missing: {missing_kinds}")
    return cases


def _build_node_program(
    cases: list[dict[str, Any]],
    repetitions: int,
    prompts: list[dict[str, Any]],
) -> str:
    search_text = SEARCH_RUNTIME.read_text(encoding="utf-8")
    guided_text = GUIDED_RUNTIME.read_text(encoding="utf-8")
    search_helpers = _extract_between(
        search_text,
        "function normalizeSearchText",
        "function promptSequenceValue",
        SEARCH_RUNTIME,
    )
    classifier_source = _extract_between(
        guided_text,
        "var PROMPT_FINDER_QUESTIONS=",
        "function shell(",
        GUIDED_RUNTIME,
    )
    prompt_sequence = (
        "function promptSequenceValue(p){"
        "var raw=String((p&&p.seq)||((p&&p.id)||''));"
        "var n=parseInt(raw.replace(/\\D/g,''),10);"
        "return isNaN(n)?Number.MAX_SAFE_INTEGER:n}"
    )
    return "\n".join(
        [
            "'use strict';",
            "var SYNONYMS=" + json.dumps(build_prompt_kit.SYNONYMS, separators=(",", ":")) + ";",
            prompt_sequence,
            search_helpers,
            "var PROMPTS=" + json.dumps(prompts, separators=(",", ":")) + ";",
            classifier_source,
            "var CASES=" + json.dumps(cases, separators=(",", ":")) + ";",
            f"var REPETITIONS={int(repetitions)};",
            "function compact(item){return {id:item.prompt.id,score:item.score,reasons:item.reasons};}",
            "function one(c){return scorePromptFinderAnswers(c.answers).map(compact);}",
            "var output=CASES.map(function(c){",
            "  var first=one(c),deterministic=true;",
            "  for(var i=1;i<REPETITIONS;i++){if(JSON.stringify(one(c))!==JSON.stringify(first)) deterministic=false;}",
            "  return {id:c.id,results:first,deterministic:deterministic};",
            "});",
            "process.stdout.write(JSON.stringify(output));",
        ]
    )


def _run_canonical_classifier(
    cases: list[dict[str, Any]],
    repetitions: int,
    prompts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    node = shutil.which("node")
    if not node:
        raise EvalError("Node.js is required to execute the canonical Prompt Finder runtime")
    program = _build_node_program(cases, repetitions, prompts)
    with tempfile.TemporaryDirectory(prefix="prompt-finder-eval-") as tmp:
        script_path = Path(tmp) / "evaluate.js"
        script_path.write_text(program, encoding="utf-8")
        completed = subprocess.run(
            [node, str(script_path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    if completed.returncode != 0:
        raise EvalError(
            "canonical Prompt Finder runtime failed: "
            + (completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}")
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise EvalError("canonical Prompt Finder runtime returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise EvalError("canonical Prompt Finder runtime returned a non-list result")
    return payload


def evaluate(policy: dict[str, Any], fixtures: dict[str, Any]) -> dict[str, Any]:
    cases = _validate_contract(policy, fixtures)
    target = _validate_target(policy)
    prompts = _project_registry()
    projected_registry_sha256 = _projected_registry_sha256(prompts)
    thresholds = policy.get("metrics", {})
    repetitions = int(thresholds.get("deterministic_repetitions", 3))
    max_recommendations = int(thresholds.get("max_recommendations", 3))
    runtime_results = _run_canonical_classifier(cases, repetitions, prompts)
    by_id = {item.get("id"): item for item in runtime_results if isinstance(item, dict)}
    canonical_ids = {prompt["id"] for prompt in prompts if prompt.get("id")}

    primary_total = 0
    primary_hits = 0
    required_total = 0
    required_hits = 0
    deterministic_cases = 0
    case_reports: list[dict[str, Any]] = []

    for case in cases:
        case_id = case["id"]
        runtime = by_id.get(case_id)
        if runtime is None:
            raise EvalError(f"runtime omitted classifier eval case: {case_id}")
        results = runtime.get("results", [])
        if not isinstance(results, list):
            raise EvalError(f"runtime result is not a list for case: {case_id}")
        ids = [item.get("id") for item in results if isinstance(item, dict)]
        scores = [item.get("score") for item in results if isinstance(item, dict)]
        deterministic = bool(runtime.get("deterministic"))
        if deterministic:
            deterministic_cases += 1

        failures: list[str] = []
        if len(ids) > max_recommendations:
            failures.append(f"recommendation_count>{max_recommendations}")
        if len(ids) != len(set(ids)):
            failures.append("duplicate_recommendation_id")
        if any(prompt_id not in canonical_ids for prompt_id in ids):
            failures.append("unknown_recommendation_id")
        if any(
            not isinstance(scores[index], (int, float))
            or not isinstance(scores[index + 1], (int, float))
            or scores[index] < scores[index + 1]
            for index in range(max(0, len(scores) - 1))
        ):
            failures.append("scores_not_non_increasing")
        if not deterministic:
            failures.append("non_deterministic_result")

        expected_primary = case.get("expected_primary")
        if expected_primary is not None:
            primary_total += 1
            if ids and ids[0] == expected_primary:
                primary_hits += 1
            else:
                failures.append(f"primary_expected:{expected_primary}")

        required_ids = case.get("expected_top3_contains", [])
        if not isinstance(required_ids, list):
            raise EvalError(f"expected_top3_contains must be a list for case: {case_id}")
        for required_id in required_ids:
            required_total += 1
            if required_id in ids[:3]:
                required_hits += 1
            else:
                failures.append(f"top3_missing:{required_id}")

        forbidden_ids = case.get("forbidden_top3", [])
        if not isinstance(forbidden_ids, list):
            raise EvalError(f"forbidden_top3 must be a list for case: {case_id}")
        for forbidden_id in forbidden_ids:
            if forbidden_id in ids[:3]:
                failures.append(f"top3_forbidden:{forbidden_id}")

        if case.get("expected_empty") is True and ids:
            failures.append("expected_empty")

        case_reports.append(
            {
                "id": case_id,
                "kind": case["kind"],
                "purpose": case.get("purpose", ""),
                "answers": case["answers"],
                "expected_primary": expected_primary,
                "expected_top3_contains": required_ids,
                "actual": results,
                "deterministic": deterministic,
                "verdict": "pass" if not failures else "fail",
                "failures": failures,
            }
        )

    case_passes = sum(item["verdict"] == "pass" for item in case_reports)
    case_count = len(case_reports)
    primary_accuracy = primary_hits / primary_total if primary_total else 1.0
    required_recall = required_hits / required_total if required_total else 1.0
    case_pass_rate = case_passes / case_count if case_count else 0.0
    deterministic_rate = deterministic_cases / case_count if case_count else 0.0

    metrics = {
        "case_count": case_count,
        "case_passes": case_passes,
        "case_pass_rate": case_pass_rate,
        "primary_expected": primary_total,
        "primary_hits": primary_hits,
        "primary_accuracy": primary_accuracy,
        "required_top3_targets": required_total,
        "required_top3_hits": required_hits,
        "required_recall_at_3": required_recall,
        "deterministic_cases": deterministic_cases,
        "deterministic_rate": deterministic_rate,
    }
    passes_thresholds = (
        case_pass_rate >= float(thresholds.get("case_pass_rate_min", 1.0))
        and primary_accuracy >= float(thresholds.get("primary_accuracy_min", 1.0))
        and required_recall >= float(thresholds.get("required_recall_at_3_min", 1.0))
        and deterministic_cases == case_count
    )
    proof_ceiling = str(policy.get("proof_ceiling", ""))
    registry_sources = _registry_source_paths()
    return {
        "schema_version": "prompt-finder-classifier-eval-result/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_head(),
        "target": target,
        "sources": {
            "policy": str(POLICY_PATH.relative_to(ROOT)),
            "policy_sha256": _sha256(POLICY_PATH),
            "fixtures": str(CASES_PATH.relative_to(ROOT)),
            "fixtures_sha256": _sha256(CASES_PATH),
            "shared_search_runtime": str(SEARCH_RUNTIME.relative_to(ROOT)),
            "shared_search_runtime_sha256": _sha256(SEARCH_RUNTIME),
            "classifier_runtime": str(GUIDED_RUNTIME.relative_to(ROOT)),
            "classifier_runtime_sha256": _sha256(GUIDED_RUNTIME),
            "projected_registry_sha256": projected_registry_sha256,
            "projected_registry_prompt_count": len(prompts),
            "registry_source_files": [
                {
                    "path": str(path.relative_to(ROOT)),
                    "sha256": _sha256(path),
                }
                for path in registry_sources
            ],
        },
        "thresholds": thresholds,
        "metrics": metrics,
        "verdict": "pass" if passes_thresholds else "fail",
        "cases": case_reports,
        "proof_ceiling": proof_ceiling,
        "proof_binding": {
            "policy_proof_ceiling": proof_ceiling,
            "validated_target": target,
            "projected_registry_sha256": projected_registry_sha256,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    try:
        output = _resolve_output(args.output)
        policy = _load_json(POLICY_PATH)
        fixtures = _load_json(CASES_PATH)
        report = evaluate(policy, fixtures)
    except EvalError as exc:
        print(f"PROMPT_FINDER_CLASSIFIER_EVAL_ERROR: {exc}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.summary:
        metrics = report["metrics"]
        print(
            "PROMPT_FINDER_CLASSIFIER_EVAL_"
            + report["verdict"].upper()
            + f": cases={metrics['case_passes']}/{metrics['case_count']} "
            + f"primary={metrics['primary_hits']}/{metrics['primary_expected']} "
            + f"recall@3={metrics['required_top3_hits']}/{metrics['required_top3_targets']} "
            + f"deterministic={metrics['deterministic_cases']}/{metrics['case_count']} "
            + f"output={output.relative_to(ROOT)}"
        )
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
