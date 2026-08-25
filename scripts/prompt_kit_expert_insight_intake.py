#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

REPORT_SCHEMA = "prompt-kit-expert-insight-intake-report/v1"
REQUIRED_HEADERS = [
    "Insight ID",
    "Source ID",
    "Captured Date",
    "Timestamp",
    "Domain",
    "Topic",
    "Atomic Insight",
    "Why It Matters",
    "Prompt Kit Relevance",
    "Candidate Action",
    "Candidate Owner",
    "Target Surface",
    "Sprint Track",
    "Priority",
    "Status",
    "Acceptance / Proof Idea",
    "Validation Lenses",
    "Tags",
    "CI Eligible",
    "Notes",
]
ACTIONS = {"ASSESS", "ADD", "STRENGTHEN", "ALREADY_COVERED", "REJECT", "HOLD"}
PRIORITIES = {"High", "Medium", "Low"}
STATUSES = {
    "CAPTURED",
    "TRIAGED",
    "EVALUATING",
    "READY_FOR_REPO",
    "IN_REPO_REVIEW",
    "INTEGRATED",
    "REJECTED",
    "BLOCKED",
}
CI_ELIGIBLE = {"YES", "PARTIAL", "NO"}
READY_ACTIONS = {"ADD", "STRENGTHEN"}
INSIGHT_ID_RE = re.compile(r"^INS-[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIMESTAMP_RE = re.compile(r"^\d{2,3}:\d{2}(?::\d{2})?$")
MAX_ROWS = 5000
MAX_TEXT = 4000


def _text(row: dict[str, str], field: str, *, allow_blank: bool = False) -> str:
    value = row.get(field, "")
    if not isinstance(value, str):
        raise SystemExit(f"{field} must be text")
    value = value.strip()
    if not value and not allow_blank:
        raise SystemExit(f"{field} must be non-empty")
    if len(value) > MAX_TEXT:
        raise SystemExit(f"{field} exceeds {MAX_TEXT} characters")
    return value


def _validate_headers(fieldnames: list[str] | None) -> None:
    if not fieldnames:
        raise SystemExit("expert insight CSV has no header row")
    if len(fieldnames) != len(set(fieldnames)):
        raise SystemExit("expert insight CSV contains duplicate headers")
    if fieldnames != REQUIRED_HEADERS:
        missing = [field for field in REQUIRED_HEADERS if field not in fieldnames]
        extra = [field for field in fieldnames if field not in REQUIRED_HEADERS]
        order_only = not missing and not extra
        detail = "column order differs from contract" if order_only else f"missing={missing} extra={extra}"
        raise SystemExit(f"expert insight CSV schema mismatch: {detail}")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_headers(reader.fieldnames)
        rows = list(reader)
    if len(rows) > MAX_ROWS:
        raise SystemExit(f"expert insight CSV exceeds {MAX_ROWS} rows")
    return rows


def normalize_row(raw: dict[str, str]) -> dict[str, str]:
    row = {
        field: _text(
            raw,
            field,
            allow_blank=field
            in {"Sprint Track", "Acceptance / Proof Idea", "Validation Lenses", "Tags", "Notes"},
        )
        for field in REQUIRED_HEADERS
    }
    insight_id = row["Insight ID"]
    if not INSIGHT_ID_RE.fullmatch(insight_id):
        raise SystemExit(f"invalid Insight ID: {insight_id}")
    if not row["Source ID"].startswith("SRC-"):
        raise SystemExit(f"Source ID must start with SRC-: {row['Source ID']}")
    if not DATE_RE.fullmatch(row["Captured Date"]):
        raise SystemExit(f"Captured Date must be YYYY-MM-DD: {insight_id}")
    if not TIMESTAMP_RE.fullmatch(row["Timestamp"]):
        raise SystemExit(f"Timestamp must be video timestamp text (MM:SS or HH:MM:SS): {insight_id}")
    if row["Candidate Action"] not in ACTIONS:
        raise SystemExit(f"unsupported Candidate Action for {insight_id}: {row['Candidate Action']}")
    if row["Priority"] not in PRIORITIES:
        raise SystemExit(f"unsupported Priority for {insight_id}: {row['Priority']}")
    if row["Status"] not in STATUSES:
        raise SystemExit(f"unsupported Status for {insight_id}: {row['Status']}")
    if row["CI Eligible"] not in CI_ELIGIBLE:
        raise SystemExit(f"unsupported CI Eligible for {insight_id}: {row['CI Eligible']}")
    if row["Status"] == "READY_FOR_REPO":
        if row["Candidate Action"] not in READY_ACTIONS:
            raise SystemExit(f"READY_FOR_REPO requires ADD or STRENGTHEN: {insight_id}")
        if row["Candidate Owner"].upper() == "UNKNOWN":
            raise SystemExit(f"READY_FOR_REPO requires a proven Candidate Owner: {insight_id}")
        if not row["Acceptance / Proof Idea"]:
            raise SystemExit(f"READY_FOR_REPO requires Acceptance / Proof Idea: {insight_id}")
        if not row["Validation Lenses"]:
            raise SystemExit(f"READY_FOR_REPO requires Validation Lenses: {insight_id}")
        if row["CI Eligible"] == "NO":
            raise SystemExit(f"READY_FOR_REPO cannot be CI Eligible=NO: {insight_id}")
    return row


def build_report(rows: Iterable[dict[str, str]], source_ref: str) -> dict[str, object]:
    seen: set[str] = set()
    normalized: list[dict[str, str]] = []
    for raw in rows:
        row = normalize_row(raw)
        insight_id = row["Insight ID"]
        if insight_id in seen:
            raise SystemExit(f"duplicate Insight ID: {insight_id}")
        seen.add(insight_id)
        normalized.append(row)

    status_counts = Counter(row["Status"] for row in normalized)
    candidates = []
    summaries = []
    for row in normalized:
        summaries.append(
            {
                "insight_id": row["Insight ID"],
                "status": row["Status"],
                "candidate_action": row["Candidate Action"],
                "candidate_owner": row["Candidate Owner"],
                "sprint_track": row["Sprint Track"],
                "priority": row["Priority"],
                "ci_eligible": row["CI Eligible"],
            }
        )
        if row["Status"] == "READY_FOR_REPO":
            candidates.append(
                {
                    "insight_id": row["Insight ID"],
                    "source_id": row["Source ID"],
                    "captured_date": row["Captured Date"],
                    "timestamp": row["Timestamp"],
                    "domain": row["Domain"],
                    "topic": row["Topic"],
                    "atomic_insight": row["Atomic Insight"],
                    "why_it_matters": row["Why It Matters"],
                    "prompt_kit_relevance": row["Prompt Kit Relevance"],
                    "candidate_action": row["Candidate Action"],
                    "candidate_owner": row["Candidate Owner"],
                    "target_surface": row["Target Surface"],
                    "sprint_track": row["Sprint Track"],
                    "priority": row["Priority"],
                    "acceptance_proof_idea": row["Acceptance / Proof Idea"],
                    "validation_lenses": row["Validation Lenses"],
                    "tags": row["Tags"],
                    "ci_eligible": row["CI Eligible"],
                }
            )

    return {
        "schema_version": REPORT_SCHEMA,
        "source_ref": source_ref,
        "raw_source_authority": "DRIVE-AUTHORITATIVE",
        "repo_candidate_authority": "REVIEW-ONLY",
        "mutation_authority": False,
        "input_rows": len(normalized),
        "status_counts": dict(sorted(status_counts.items())),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "summaries": summaries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Prompt Kit expert-insight CSV export and emit review-only candidates."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-ref", default="sanitized-file")
    args = parser.parse_args(argv)
    source_ref = args.source_ref.strip()
    if not source_ref or len(source_ref) > 120:
        raise SystemExit("source-ref must be 1..120 characters")
    report = build_report(load_rows(args.input), source_ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "input_rows": report["input_rows"],
                "candidates": report["candidate_count"],
                "output": args.output.as_posix(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
