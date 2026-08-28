from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_prompt_kit_registry

DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "p67_source_faithfulness" / "opencode_p122_pair.v1.json"
VALID_DECISIONS = {"GROUND", "CONTINUE", "TERMINAL"}
VALID_CLASSIFICATIONS = {"FACTUALITY_CONTEXT_MISSING", "FAITHFULNESS_CONTEXT_IGNORED", "NONE"}
VALID_REMEDIATIONS = {"TARGETED_GROUNDING", "REANCHOR_EXISTING_CONTEXT", "NONE"}
PROTOCOL_FIELDS = ("DECISION", "CLASSIFICATION", "REMEDIATION", "REASONS")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_p100() -> dict[str, Any]:
    by_id = {item["id"]: item for item in build_prompt_kit_registry.load_prompt_registry()}
    if "P100" not in by_id:
        raise ValueError("P100 missing from effective Prompt Kit registry")
    return by_id["P100"]


def _load_pair_fixture(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get("schema_version") != "p67-source-faithfulness/v1":
        raise ValueError(f"unsupported P67 fixture schema: {payload.get('schema_version')!r}")
    if payload.get("owner") != "P67" or payload.get("guard_owner") != "P100":
        raise ValueError("P67 fixture must declare owner=P67 and guard_owner=P100")
    return payload


def _source_fixture(pair_fixture: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    rel = pair_fixture.get("source_fixture")
    if not rel:
        raise ValueError("P67 fixture is missing source_fixture")
    path = ROOT / rel
    source = _load_json(path)
    if source.get("schema_version") != "p100-closeout-replay/v1":
        raise ValueError("P67 source_fixture must point to p100-closeout-replay/v1")
    return path, source


def _source_evidence_by_id(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in source.get("authoritative_evidence", []) if item.get("id")}


def materialize_case(pair_case: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    mode = pair_case.get("context_mode")
    evidence_by_id = _source_evidence_by_id(source)
    refs = list(pair_case.get("evidence_refs") or [])
    unknown_refs = [ref for ref in refs if ref not in evidence_by_id]
    if unknown_refs:
        raise ValueError(f"unknown source evidence refs: {unknown_refs}")
    evidence = [evidence_by_id[ref] for ref in refs]

    if mode == "present":
        if not pair_case.get("observed_closeout_from_source"):
            raise ValueError("present case must preserve the source closeout")
        closeout = source["before"]["observed_closeout_text"]
    elif mode == "missing":
        if refs:
            raise ValueError("missing-context case must not import authoritative evidence")
        closeout = str(pair_case["observed_closeout_text"])
    else:
        raise ValueError(f"unsupported context_mode: {mode!r}")

    return {
        "id": pair_case["id"],
        "context_mode": mode,
        "observed_closeout_text": closeout,
        "authoritative_evidence": evidence,
        "expected": pair_case["expected"],
    }


def _format_evidence(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return "NONE SUPPLIED. Do not invent CI state, branch names, run IDs, or conflict details."
    lines = []
    for item in evidence:
        fields = [
            f"id={item.get('id')}",
            f"kind={item.get('kind')}",
            f"status={item.get('status')}",
            f"required={item.get('required')}",
            f"safe_action_available={item.get('safe_action_available')}",
        ]
        if item.get("run_id") is not None:
            fields.append(f"run_id={item.get('run_id')}")
        if item.get("candidate_sha"):
            fields.append(f"candidate_sha={item.get('candidate_sha')}")
        detail = item.get("detail")
        if detail:
            fields.append(f"detail={detail}")
        continuation = item.get("continuation")
        if continuation:
            fields.append(f"continuation={continuation}")
        lines.append("- " + " | ".join(fields))
    return "\n".join(lines)


def build_prompt(case: dict[str, Any], p100: dict[str, Any]) -> str:
    return (
        "P67 SOURCE-FAITHFULNESS EVAL\n"
        "Use only the supplied case context and the effective P100 contract below. "
        "Do not use hidden repository knowledge or invent missing evidence. "
        "Diagnose whether the preserved closeout should remain terminal and choose the remediation that matches the cause.\n\n"
        "EFFECTIVE P100 CONTRACT\n"
        "-----\n"
        f"{p100['copyContent']}\n"
        "-----\n\n"
        f"CASE ID: {case['id']}\n"
        f"CONTEXT MODE: {case['context_mode']}\n"
        "OBSERVED CLOSEOUT\n"
        "-----\n"
        f"{case['observed_closeout_text']}\n"
        "-----\n"
        "AUTHORITATIVE EVIDENCE\n"
        f"{_format_evidence(case['authoritative_evidence'])}\n\n"
        "Return any brief reasoning you need, then end with EXACTLY these four protocol lines:\n"
        "DECISION: <GROUND|CONTINUE|TERMINAL>\n"
        "CLASSIFICATION: <FACTUALITY_CONTEXT_MISSING|FAITHFULNESS_CONTEXT_IGNORED|NONE>\n"
        "REMEDIATION: <TARGETED_GROUNDING|REANCHOR_EXISTING_CONTEXT|NONE>\n"
        "REASONS: <comma-separated reason codes or none>\n\n"
        "Classification meanings:\n"
        "- FACTUALITY_CONTEXT_MISSING: required truth is absent from supplied context; do not invent it.\n"
        "- FAITHFULNESS_CONTEXT_IGNORED: supplied authoritative truth contradicts the observed closeout.\n"
        "- NONE: supplied proof supports the closeout without a factuality/faithfulness defect.\n"
        "Remediation meanings:\n"
        "- TARGETED_GROUNDING: obtain the missing authoritative evidence before deciding.\n"
        "- REANCHOR_EXISTING_CONTEXT: use the authoritative evidence already supplied and continue or route the work.\n"
        "- NONE: no corrective action is required.\n"
        "Reason-code vocabulary: missing_authoritative_evidence, required_gate_failure, "
        "acknowledged_identity_conflict, none.\n"
    )


def parse_protocol(text: str) -> tuple[dict[str, Any] | None, list[str]]:
    found: dict[str, str] = {}
    errors: list[str] = []
    for field in PROTOCOL_FIELDS:
        matches = re.findall(rf"(?mi)^\s*{field}\s*:\s*(.+?)\s*$", text)
        if not matches:
            errors.append(f"missing protocol field {field}")
            continue
        found[field] = matches[-1].strip()

    if errors:
        return None, errors

    decision = found["DECISION"].upper()
    classification = found["CLASSIFICATION"].upper()
    remediation = found["REMEDIATION"].upper()
    reasons_raw = found["REASONS"]
    reasons = [] if reasons_raw.lower() == "none" else [part.strip() for part in reasons_raw.split(",") if part.strip()]

    if decision not in VALID_DECISIONS:
        errors.append(f"invalid DECISION {decision}")
    if classification not in VALID_CLASSIFICATIONS:
        errors.append(f"invalid CLASSIFICATION {classification}")
    if remediation not in VALID_REMEDIATIONS:
        errors.append(f"invalid REMEDIATION {remediation}")
    if errors:
        return None, errors
    return {
        "decision": decision,
        "classification": classification,
        "remediation": remediation,
        "reasons": reasons,
    }, []


def _hidden_source_tokens(source: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for item in source.get("authoritative_evidence", []):
        if item.get("run_id") is not None:
            tokens.append(str(item["run_id"]))
        detail = str(item.get("detail") or "")
        branch_match = re.search(r"\bfeat/[A-Za-z0-9._/-]+", detail)
        if branch_match:
            tokens.append(branch_match.group(0))
    return tokens


def score_response(case: dict[str, Any], response_text: str, source: dict[str, Any]) -> dict[str, Any]:
    parsed, parse_errors = parse_protocol(response_text)
    errors = list(parse_errors)
    expected = case["expected"]

    if parsed is not None:
        for field in ("decision", "classification", "remediation"):
            if parsed[field] != expected[field]:
                errors.append(f"{field} expected {expected[field]}, got {parsed[field]}")
        if set(parsed["reasons"]) != set(expected["reasons"]):
            errors.append(
                "reasons expected "
                + ",".join(expected["reasons"])
                + ", got "
                + (",".join(parsed["reasons"]) or "none")
            )

    hidden_mentions: list[str] = []
    if case["context_mode"] == "missing":
        hidden_mentions = [token for token in _hidden_source_tokens(source) if token and token in response_text]
        if hidden_mentions:
            errors.append("invented hidden evidence: " + ", ".join(hidden_mentions))

    return {
        "case_id": case["id"],
        "context_mode": case["context_mode"],
        "status": "PASS" if not errors else "FAIL",
        "parsed": parsed,
        "errors": errors,
        "hidden_evidence_mentions": hidden_mentions,
        "response_sha256": _sha256_text(response_text),
        "response_text": response_text,
    }


def evaluate_responses(
    pair_fixture: dict[str, Any],
    source: dict[str, Any],
    p100: dict[str, Any],
    responses: dict[str, str],
    *,
    evidence_class: str,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    cases = [materialize_case(item, source) for item in pair_fixture["cases"]]
    results: list[dict[str, Any]] = []
    for case in cases:
        if case["id"] not in responses:
            results.append(
                {
                    "case_id": case["id"],
                    "context_mode": case["context_mode"],
                    "status": "FAIL",
                    "parsed": None,
                    "errors": ["missing response"],
                    "hidden_evidence_mentions": [],
                    "response_sha256": None,
                    "response_text": None,
                }
            )
            continue
        results.append(score_response(case, responses[case["id"]], source))

    status = "PASS" if results and all(item["status"] == "PASS" for item in results) else "FAIL"
    return {
        "schema_version": "p67-source-faithfulness-result/v1",
        "case_id": pair_fixture["case_id"],
        "status": status,
        "owner": "P67",
        "guard_owner": "P100",
        "evidence_class": evidence_class,
        "p100_copy_content_sha256": _sha256_text(p100["copyContent"]),
        "runtime": runtime,
        "cases": results,
        "proof_ceiling": (
            "Synthetic response scoring proves the deterministic oracle only."
            if evidence_class == "synthetic"
            else "target_runtime_observed proves the invoked OpenCode CLI responses for this exact paired case and current P100 digest; it does not prove all models, providers, sessions, or future outputs."
        ),
    }


def unproven_report(
    pair_fixture: dict[str, Any],
    p100: dict[str, Any],
    reason: str,
    runtime: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "p67-source-faithfulness-result/v1",
        "case_id": pair_fixture["case_id"],
        "status": "UNPROVEN",
        "owner": "P67",
        "guard_owner": "P100",
        "evidence_class": "none",
        "p100_copy_content_sha256": _sha256_text(p100["copyContent"]),
        "runtime": runtime,
        "cases": [],
        "blocker": reason,
        "proof_ceiling": "No live OpenCode/model behavior was observed; runtime behavior remains UNPROVEN.",
    }


def resolve_runtime(
    requested: str,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[str | None, str | None]:
    candidates = ["opencode", "opencode2"] if requested == "auto" else [requested]
    for candidate in candidates:
        path = which(candidate)
        if path:
            return candidate, path
    return None, None


def _run_command(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def run_opencode(
    pair_fixture: dict[str, Any],
    source: dict[str, Any],
    p100: dict[str, Any],
    *,
    requested_runtime: str,
    model: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    runtime_name, runtime_path = resolve_runtime(requested_runtime)
    runtime_meta: dict[str, Any] = {
        "mode": "opencode_cli",
        "requested_runtime": requested_runtime,
        "executable": runtime_name,
        "path": runtime_path,
        "model_requested": model,
    }
    if not runtime_path or not runtime_name:
        return unproven_report(
            pair_fixture,
            p100,
            f"OpenCode CLI not found for runtime={requested_runtime}",
            runtime_meta,
        )

    try:
        version_proc = _run_command([runtime_path, "--version"], min(timeout_seconds, 30))
        runtime_meta["version_exit_code"] = version_proc.returncode
        runtime_meta["version"] = (version_proc.stdout or version_proc.stderr).strip() or None
    except (OSError, subprocess.TimeoutExpired) as exc:
        return unproven_report(pair_fixture, p100, f"OpenCode version probe failed: {exc}", runtime_meta)

    responses: dict[str, str] = {}
    invocations: list[dict[str, Any]] = []
    for case_def in pair_fixture["cases"]:
        case = materialize_case(case_def, source)
        prompt = build_prompt(case, p100)
        command = [runtime_path, "run"]
        if model:
            command.extend(["--model", model])
        command.append(prompt)
        try:
            proc = _run_command(command, timeout_seconds)
        except (OSError, subprocess.TimeoutExpired) as exc:
            runtime_meta["invocations"] = invocations
            return unproven_report(pair_fixture, p100, f"OpenCode case {case['id']} did not complete: {exc}", runtime_meta)

        invocations.append(
            {
                "case_id": case["id"],
                "exit_code": proc.returncode,
                "stderr_sha256": _sha256_text(proc.stderr or ""),
            }
        )
        if proc.returncode != 0:
            runtime_meta["invocations"] = invocations
            return unproven_report(
                pair_fixture,
                p100,
                f"OpenCode case {case['id']} exited {proc.returncode}; provider/auth/runtime proof unavailable",
                runtime_meta,
            )
        responses[case["id"]] = proc.stdout

    runtime_meta["invocations"] = invocations
    return evaluate_responses(
        pair_fixture,
        source,
        p100,
        responses,
        evidence_class="target_runtime_observed",
        runtime=runtime_meta,
    )


def build_observed_receipt(
    report: dict[str, Any],
    *,
    commit_sha: str,
    fixture_path: Path,
) -> dict[str, Any]:
    if report.get("status") != "PASS" or report.get("evidence_class") != "target_runtime_observed":
        raise ValueError("observed receipt requires a passing target_runtime_observed report")
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise ValueError("commit_sha must be an exact 40-character lowercase SHA")
    rel = fixture_path.resolve().relative_to(ROOT.resolve()).as_posix()
    observations = []
    observation_ids = []
    for item in report["cases"]:
        oid = f"p67-{item['case_id']}"
        observation_ids.append(oid)
        observations.append(
            {
                "id": oid,
                "occurred": True,
                "passed": item["status"] == "PASS",
                "response_sha256": item["response_sha256"],
            }
        )
    return {
        "schema_version": "observed-behavior-proof/v1",
        "verdict": "PASS",
        "evidence_class": "target_runtime_observed",
        "subject": {
            "commit_sha": commit_sha,
            "artifact": {
                "path": rel,
                "sha256": _sha256_bytes(fixture_path.read_bytes()),
            },
        },
        "claims": [
            {
                "id": "p67-source-faithfulness-paired-runtime",
                "status": "PASS",
                "required_evidence_class": "target_runtime_observed",
                "observation_ids": observation_ids,
            }
        ],
        "observations": observations,
        "runtime": report["runtime"],
        "p100_copy_content_sha256": report["p100_copy_content_sha256"],
    }


def _git_head() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = proc.stdout.strip()
    return value if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None


def _load_responses_dir(path: Path, case_ids: list[str]) -> dict[str, str]:
    responses: dict[str, str] = {}
    for case_id in case_ids:
        response_path = path / f"{case_id}.txt"
        if response_path.is_file():
            responses[case_id] = response_path.read_text(encoding="utf-8")
    return responses


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the P67 paired factuality/faithfulness eval against P100.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--responses-dir", type=Path)
    parser.add_argument("--runtime", choices=("auto", "opencode", "opencode2"))
    parser.add_argument("--model")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--commit-sha")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    if bool(args.responses_dir) == bool(args.runtime):
        parser.error("choose exactly one of --responses-dir or --runtime")

    pair_fixture = _load_pair_fixture(args.fixture)
    _, source = _source_fixture(pair_fixture)
    p100 = _load_p100()

    if args.responses_dir:
        case_ids = [item["id"] for item in pair_fixture["cases"]]
        responses = _load_responses_dir(args.responses_dir, case_ids)
        report = evaluate_responses(
            pair_fixture,
            source,
            p100,
            responses,
            evidence_class="synthetic",
            runtime={"mode": "saved_responses", "path": str(args.responses_dir)},
        )
    else:
        report = run_opencode(
            pair_fixture,
            source,
            p100,
            requested_runtime=args.runtime,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
        )

    if args.output:
        _write_json(args.output, report)

    if args.receipt_output:
        commit_sha = args.commit_sha or _git_head()
        if not commit_sha:
            print("P67 source-faithfulness eval: receipt UNPROVEN (exact git HEAD unavailable)", file=sys.stderr)
            return 2
        try:
            receipt = build_observed_receipt(report, commit_sha=commit_sha, fixture_path=args.fixture)
        except ValueError as exc:
            print(f"P67 source-faithfulness eval: receipt UNPROVEN ({exc})", file=sys.stderr)
            return 2
        _write_json(args.receipt_output, receipt)

    if args.summary:
        print(
            "p67_source_faithfulness "
            f"status={report['status']} "
            f"evidence_class={report['evidence_class']} "
            f"p100={report['p100_copy_content_sha256'][:12]} "
            f"cases={len(report.get('cases', []))}"
        )
        if report.get("blocker"):
            print(f"blocker={report['blocker']}")

    if report["status"] == "PASS":
        return 0
    if report["status"] == "UNPROVEN":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
