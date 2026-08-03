#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from triage.fun_nth_artifact_export import build_fun_nth_export, write_export_result


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the sanitized FUN NTH producer fixture.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--producer-commit", required=True)
    args = parser.parse_args(argv)

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    artifact = out / "sanitized_nth.xlsx"
    packet_path = out / "packet-spec.json"
    profile_path = out / "export-profile.json"
    manifest_path = out / "artifact-manifest.json"
    receipt_path = out / "producer-receipt.json"

    workbook = Workbook()
    nth = workbook.active
    nth.title = "NTH"
    nth["A1"] = "Fixture"
    nth["A2"] = "Configuration"
    nth["B2"] = 8.0
    summary = workbook.create_sheet("Task Summary")
    summary["A1"] = "Workstream"
    summary["B1"] = "Hours"
    summary["A2"] = "Configuration"
    summary["B2"] = 8.0
    workbook.save(artifact)

    packet = {
        "schema": "fun-nth-packet-spec/v1",
        "packet_id": "triage.fun-nth.fixture",
        "period": {"label": "Sanitized fixture", "start": "2026-08-03", "end": "2026-08-03"},
        "controls": {"hours": 8.0, "shift_records": 1, "control_kind": "operational"},
        "workstreams": [
            {
                "id": "configuration",
                "label": "Configuration",
                "hours": 8.0,
                "color": "#D9EAF7",
                "allocation_basis": [{"kind": "synthetic_fixture"}],
                "included_activities": ["Synthetic fixture generation"],
                "evidence_authority": [{"kind": "synthetic_fixture"}],
                "defense_boundaries": ["No production or evidence claim"],
                "share_safe_claim": "Synthetic fixture only"
            }
        ],
        "palette": {"configuration": "#D9EAF7"},
        "share_surface": {
            "artifact_name": artifact.name,
            "approved_tabs": ["NTH", "Task Summary"],
            "forbidden_content": ["Evidence References", "Source Notes"]
        },
        "proof_boundaries": ["Synthetic fixture only; no production or evidence truth proof"]
    }
    profile = {
        "schema": "web-excel-fun-nth-export-profile/v1",
        "packet_id": packet["packet_id"],
        "sheet_contract": {
            "allowed_sheets": ["NTH", "Task Summary"],
            "hidden_sheets_forbidden": True,
            "forbidden_sheet_patterns": ["(?i)evidence", "(?i)source notes"],
            "forbidden_text": ["Evidence References", "Source Notes"]
        },
        "cell_assertions": [
            {"sheet": "NTH", "cell": "A1", "value": "Fixture"},
            {"sheet": "Task Summary", "cell": "B2", "value": 8.0, "tolerance": 0.0}
        ],
        "reconciliations": [
            {
                "label": "fixture workstream total",
                "terms": [{"sheet": "Task Summary", "cell": "B2"}],
                "expected": 8.0,
                "tolerance": 0.0
            }
        ],
        "required_text": [
            {"sheet": "NTH", "text": "Fixture"},
            {"sheet": "Task Summary", "text": "Configuration"}
        ]
    }
    write_json(packet_path, packet)
    write_json(profile_path, profile)

    result = build_fun_nth_export(
        artifact_path=artifact,
        packet_spec_path=packet_path,
        export_profile_path=profile_path,
        lock_path=ROOT / "contracts/upstream/fun/nth-artifact-contract.lock.json",
        repository_root=ROOT,
        artifact_type="fixture",
        builder_version="fun-nth-integration-fixture/1",
        producer_commit=args.producer_commit,
        publication_posture="sanitized_fixture",
        generation_mode="generated",
    )
    write_export_result(result, manifest_path=manifest_path, receipt_path=receipt_path)
    print(artifact)
    print(manifest_path)
    print(receipt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
