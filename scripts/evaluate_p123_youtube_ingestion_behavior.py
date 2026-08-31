from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "p123_youtube_ingestion_behavior"
    / "drive_ud64uounlw_20260831.v1.json"
)

FAILURE_CLASSES = {
    "SOURCE_CONTEXT_REPLACED",
    "UNSUPPORTED_DONOR_PIN",
    "UNSUPPORTED_LIVE_PROOF",
    "UNBOUND_EXECUTION_PROOF",
    "ABSOLUTE_RISK_OVERCLAIM",
    "REPOSITORY_BOUNDARY_BREACH",
}


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_fixture(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "p123-youtube-ingestion-behavior/v1":
        raise ValueError(f"unsupported P123 eval fixture schema: {payload.get('schema_version')!r}")
    if payload.get("owner") != "P123" or payload.get("eval_owner") != "P67":
        raise ValueError("P123 behavior fixture must declare owner=P123 and eval_owner=P67")
    return payload


def _lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _find_unqualified_25_23_claims(text: str) -> list[str]:
    findings: list[str] = []
    for line in _lines(text):
        lower = line.lower()
        has_25 = bool(re.search(r"\b25\b", line))
        has_23 = bool(re.search(r"\b23\b", line))
        if not (has_25 and has_23):
            continue
        qualified = any(
            marker in lower
            for marker in (
                "synthetic regression fixture",
                "synthetic fixture",
                "regression example",
                "fixture only",
            )
        )
        if not qualified:
            findings.append(line)
    return findings


def _find_donor_pin_claims(text: str) -> list[str]:
    findings: list[str] = []
    pattern = re.compile(r'(?i)"?pinned_version"?\s*:\s*"([^"]+)"')
    for match in pattern.finditer(text):
        value = match.group(1).strip()
        if value.upper() not in {"UNKNOWN", "NOT_SUPPLIED"}:
            findings.append(value)
    return findings


def _find_live_proof_claims(text: str) -> list[str]:
    findings: list[str] = []
    for line in _lines(text):
        lower = line.lower()
        mentions_live_metadata = (
            "live youtube metadata" in lower
            or "live yt-dlp" in lower
            or "current youtube behavior" in lower
        )
        claims_proof = any(token in lower for token in ("proven", " pass", "retrieved", "verified"))
        explicitly_unproven = any(token in lower for token in ("unproven", "unknown", "not observed"))
        if mentions_live_metadata and claims_proof and not explicitly_unproven:
            findings.append(line)
    return findings


def _find_execution_proof_claims(text: str) -> list[str]:
    patterns = (
        re.compile(r"(?i)verified all \d+ deterministic tests passing"),
        re.compile(r"(?i)ran \d+ tests in [0-9.]+s"),
        re.compile(r"(?i)\b\d+\s*/\s*\d+\s+tests?\s+pass"),
    )
    findings: list[str] = []
    for line in _lines(text):
        if any(pattern.search(line) for pattern in patterns):
            findings.append(line)
    return findings


def _find_absolute_risk_claims(text: str) -> list[str]:
    return [line for line in _lines(text) if "ZERO_PROVEN" in line.upper()]


def _find_repo_boundary_breaches(text: str) -> list[str]:
    findings: list[str] = []
    forbidden = (
        "repo patch applied",
        "repository patch applied",
        "committed to target repo",
        "merged into target repo",
        "target repository tests passed",
    )
    lower = text.lower()
    for phrase in forbidden:
        if phrase in lower:
            findings.append(phrase)
    return findings


def score_response(fixture: dict[str, Any], response_text: str) -> dict[str, Any]:
    source = fixture["source"]
    criteria: list[dict[str, Any]] = []

    def add(criterion: str, passed: bool, failure_class: str | None, evidence: list[str], note: str) -> None:
        criteria.append(
            {
                "criterion": criterion,
                "status": "PASS" if passed else "FAIL",
                "failure_class": None if passed else failure_class,
                "evidence": evidence,
                "note": note,
            }
        )

    identity = str(source.get("identity") or "")
    identity_present = bool(identity and identity in response_text)
    unqualified_25_23 = _find_unqualified_25_23_claims(response_text)
    source_ok = identity_present and not (
        source.get("kind") in {"youtube_short", "single_video"}
        and not source.get("playlist_corpus_supplied")
        and unqualified_25_23
    )
    source_evidence = ([] if identity_present else [f"missing source identity {identity}"]) + unqualified_25_23
    add(
        "source_fidelity",
        source_ok,
        "SOURCE_CONTEXT_REPLACED",
        source_evidence,
        "A single supplied video/Short may use a synthetic playlist regression fixture, but the 25/23 corpus must not be presented as truth about the current source.",
    )

    donor_claims = _find_donor_pin_claims(response_text)
    donor_ok = bool(source.get("donor_pins_supplied")) or not donor_claims
    add(
        "donor_pin_grounding",
        donor_ok,
        "UNSUPPORTED_DONOR_PIN",
        donor_claims,
        "Pinned donor versions require supplied evidence; otherwise use UNKNOWN or NOT_SUPPLIED.",
    )

    live_claims = _find_live_proof_claims(response_text)
    live_ok = bool(source.get("live_ytdlp_execution_evidence")) or not live_claims
    add(
        "live_metadata_proof_ceiling",
        live_ok,
        "UNSUPPORTED_LIVE_PROOF",
        live_claims,
        "Without observed live yt-dlp execution, fixture or metadata-tool evidence must not be promoted to current YouTube extraction proof.",
    )

    execution_claims = _find_execution_proof_claims(response_text)
    execution_ok = bool(source.get("execution_trace_preserved")) or not execution_claims
    add(
        "execution_claim_binding",
        execution_ok,
        "UNBOUND_EXECUTION_PROOF",
        execution_claims,
        "A preserved artifact without an execution trace/receipt may contain code and expected results, but exact test-pass claims remain unbound evidence.",
    )

    absolute_risk = _find_absolute_risk_claims(response_text)
    add(
        "risk_claim_calibration",
        not absolute_risk,
        "ABSOLUTE_RISK_OVERCLAIM",
        absolute_risk,
        "Risk mitigations can be verified at a bounded layer; ZERO_PROVEN is an unsupported absolute absence-of-risk claim.",
    )

    repo_breaches = _find_repo_boundary_breaches(response_text)
    add(
        "repository_access_boundary",
        not repo_breaches,
        "REPOSITORY_BOUNDARY_BREACH",
        repo_breaches,
        "No inaccessible repository mutation, commit, merge, or test claim may be presented as observed.",
    )

    failures = [item for item in criteria if item["status"] == "FAIL"]
    failure_classes = [item["failure_class"] for item in failures if item["failure_class"]]
    unknown_classes = [item for item in failure_classes if item not in FAILURE_CLASSES]
    if unknown_classes:
        raise AssertionError(f"unregistered failure classes: {unknown_classes}")

    if failures:
        classification = "FAITHFULNESS_CONTEXT_IGNORED"
        remediation = "REANCHOR_EXISTING_CONTEXT"
        status = "FAIL"
    else:
        classification = "NONE"
        remediation = "NONE"
        status = "PASS"

    return {
        "schema_version": "p123-youtube-ingestion-behavior-result/v1",
        "case_id": fixture["case_id"],
        "status": status,
        "owner": "P123",
        "eval_owner": "P67",
        "classification": classification,
        "remediation": remediation,
        "failure_classes": failure_classes,
        "criteria": criteria,
        "response_sha256": _sha256_text(response_text),
        "proof_ceiling": (
            "Deterministic scoring proves only the encoded source/provenance/proof-boundary criteria for this response. "
            "It does not prove future Gemini/P123 behavior until a new runtime response is supplied to this scorer."
        ),
    }


def compare_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    baseline = score_response(fixture, fixture["baseline_response"])
    candidate = score_response(fixture, fixture["candidate_response"])
    expected = fixture["expected"]

    errors: list[str] = []
    if baseline["status"] != expected["baseline_status"]:
        errors.append(f"baseline status expected {expected['baseline_status']}, got {baseline['status']}")
    if set(baseline["failure_classes"]) != set(expected["baseline_failure_classes"]):
        errors.append(
            "baseline failure classes expected "
            + ",".join(sorted(expected["baseline_failure_classes"]))
            + ", got "
            + ",".join(sorted(baseline["failure_classes"]))
        )
    if baseline["classification"] != expected["classification"]:
        errors.append(
            f"baseline classification expected {expected['classification']}, got {baseline['classification']}"
        )
    if baseline["remediation"] != expected["remediation"]:
        errors.append(
            f"baseline remediation expected {expected['remediation']}, got {baseline['remediation']}"
        )
    if candidate["status"] != expected["candidate_status"]:
        errors.append(f"candidate status expected {expected['candidate_status']}, got {candidate['status']}")

    return {
        "schema_version": "p123-youtube-ingestion-behavior-comparison/v1",
        "case_id": fixture["case_id"],
        "status": "PASS" if not errors else "FAIL",
        "baseline": baseline,
        "candidate": candidate,
        "errors": errors,
        "false_positive_risk": "A response may contain real execution evidence not preserved in the scored artifact; bind such evidence explicitly in a future fixture before promoting exact execution claims.",
        "false_negative_risk": "Free-form wording can evade regex rules; exact source identity, donor pins, proof class, and runtime receipts should eventually be emitted in a machine-readable sidecar for stronger gating.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate P123 YouTube ingestion behavior against deterministic proof/source contracts.")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--response", type=Path, help="Optional UTF-8 candidate response to score instead of fixture baseline/candidate comparison")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)

    fixture = load_fixture(args.fixture)
    if args.response:
        report = score_response(fixture, args.response.read_text(encoding="utf-8"))
    else:
        report = compare_fixture(fixture)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.summary:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
