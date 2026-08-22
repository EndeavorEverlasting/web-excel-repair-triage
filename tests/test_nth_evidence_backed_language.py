from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from triage.nth_qualitative_admin.builder import build_package
from triage.nth_qualitative_admin.evidence_phrases import resolve_evidence_backed_contexts
from triage.nth_qualitative_admin.model import QualitativeAdminError

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "configs" / "examples" / "nth_qualitative_admin_completed.synthetic.json"


def _catalog() -> dict:
    return {
        "catalog_id": "test-workstream-catalog-v1",
        "terms": {
            "inventory_reconciliation": {
                "canonical_label": "Inventory / Reconciliation",
                "risk_tier": "lower",
                "required_evidence_scope": "dated_context",
                "pattern_evidence_allowed": True,
                "outward_variants": [
                    "Inventory counts and reconciliation",
                    "Stock review and discrepancy follow-up",
                    "Asset-count validation and readiness review",
                ],
            },
            "client_correspondence": {
                "canonical_label": "Client Correspondence",
                "risk_tier": "high",
                "required_evidence_scope": "dated_person_task",
                "pattern_evidence_allowed": False,
                "outward_variants": [
                    "Client request clarification",
                    "Stakeholder correspondence and alignment",
                    "External request review and response coordination",
                ],
            },
        },
    }


def _spec() -> dict:
    spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    spec["qualitative_phrase_catalog"] = _catalog()
    for idx, row in enumerate(spec["detail_rows"]):
        row.pop("qualitative_work_context", None)
        row["workstream_evidence"] = [
            {
                "code": "inventory_reconciliation",
                "evidence_scope": "dated_context",
                "evidence_refs": [f"EVID-{idx + 1}"],
            }
        ]
    return spec


def test_evidence_backed_context_is_deterministic_and_preserves_receipt() -> None:
    spec = _spec()
    first = resolve_evidence_backed_contexts(spec)
    second = resolve_evidence_backed_contexts(spec)
    assert [row["qualitative_work_context"] for row in first["detail_rows"]] == [
        row["qualitative_work_context"] for row in second["detail_rows"]
    ]
    receipt = first["_evidence_backed_context_receipt"]
    assert receipt["catalog_id"] == "test-workstream-catalog-v1"
    assert receipt["canonical_codes_preserved"] is True
    assert receipt["evidence_refs_preserved"] is True
    assert receipt["kpi_semantics_changed"] is False
    assert receipt["rows"][0]["workstreams"][0]["code"] == "inventory_reconciliation"
    assert receipt["rows"][0]["workstreams"][0]["evidence_refs"] == ["EVID-1"]


def test_repeated_canonical_code_can_render_with_multiple_readable_variants() -> None:
    resolved = resolve_evidence_backed_contexts(_spec())
    contexts = [row["qualitative_work_context"] for row in resolved["detail_rows"]]
    assert len(set(contexts)) > 1
    receipt = resolved["_evidence_backed_context_receipt"]
    assert {item["workstreams"][0]["code"] for item in receipt["rows"]} == {"inventory_reconciliation"}


def test_high_risk_term_requires_dated_person_task() -> None:
    spec = _spec()
    item = spec["detail_rows"][0]["workstream_evidence"][0]
    item["code"] = "client_correspondence"
    item["evidence_scope"] = "dated_context"
    with pytest.raises(QualitativeAdminError, match="requires dated_person_task"):
        resolve_evidence_backed_contexts(spec)


def test_high_risk_term_rejects_recurring_pattern_fallback() -> None:
    spec = _spec()
    item = spec["detail_rows"][0]["workstream_evidence"][0]
    item["code"] = "client_correspondence"
    item["evidence_scope"] = "recurring_pattern"
    with pytest.raises(QualitativeAdminError, match="requires dated_person_task"):
        resolve_evidence_backed_contexts(spec)


def test_missing_or_unknown_evidence_fails_closed() -> None:
    spec = _spec()
    spec["detail_rows"][0]["workstream_evidence"][0]["evidence_refs"] = []
    with pytest.raises(QualitativeAdminError, match="requires evidence_refs"):
        resolve_evidence_backed_contexts(spec)

    spec = _spec()
    spec["detail_rows"][0]["workstream_evidence"][0]["code"] = "unknown_workstream"
    with pytest.raises(QualitativeAdminError, match="unknown workstream code"):
        resolve_evidence_backed_contexts(spec)


def test_free_text_and_evidence_backed_authority_cannot_compete() -> None:
    spec = _spec()
    spec["detail_rows"][0]["qualitative_work_context"] = "Hand-written alternate claim."
    with pytest.raises(QualitativeAdminError, match="cannot combine"):
        resolve_evidence_backed_contexts(spec)


def test_legacy_free_text_path_remains_unchanged() -> None:
    legacy = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    assert resolve_evidence_backed_contexts(legacy) == legacy


def test_build_manifest_keeps_canonical_codes_and_evidence_refs(tmp_path: Path) -> None:
    spec = _spec()
    manifest = build_package(spec, tmp_path)
    assert manifest["validation_pass"] is True
    assert manifest["qualitative_context_mode"] == "evidence_backed_catalog"
    receipt = manifest["qualitative_context_receipt"]
    assert receipt["rows"][0]["workstreams"][0]["code"] == "inventory_reconciliation"
    assert receipt["rows"][0]["workstreams"][0]["evidence_refs"] == ["EVID-1"]


def test_invalid_catalog_cannot_smuggle_high_risk_pattern_use() -> None:
    spec = _spec()
    bad = deepcopy(spec["qualitative_phrase_catalog"])
    bad["terms"]["client_correspondence"]["pattern_evidence_allowed"] = True
    spec["qualitative_phrase_catalog"] = bad
    item = spec["detail_rows"][0]["workstream_evidence"][0]
    item["code"] = "client_correspondence"
    item["evidence_scope"] = "dated_person_task"
    with pytest.raises(QualitativeAdminError, match="must forbid pattern evidence"):
        resolve_evidence_backed_contexts(spec)
