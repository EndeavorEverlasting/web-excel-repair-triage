"""Deterministic evidence-backed qualitative context rendering.

Vocabulary ownership stays with the producer (for example FUN). This module only
validates a supplied catalog, binds evidence references to canonical codes, and
selects presentation variants deterministically. It never invents a workstream.
"""
from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any, Mapping

from .model import QualitativeAdminError

ALLOWED_SCOPES = {"recurring_pattern", "dated_context", "dated_person_task"}
SCOPE_RANK = {"recurring_pattern": 1, "dated_context": 2, "dated_person_task": 3}
ALLOWED_RISKS = {"lower", "high"}


def _clean_string(value: Any, field: str) -> str:
    text = str(value if value is not None else "").strip()
    if not text:
        raise QualitativeAdminError(f"{field} is required")
    return text


def _catalog_terms(catalog: Mapping[str, Any]) -> tuple[str, Mapping[str, Any]]:
    catalog_id = _clean_string(catalog.get("catalog_id"), "qualitative_phrase_catalog.catalog_id")
    terms = catalog.get("terms")
    if not isinstance(terms, Mapping) or not terms:
        raise QualitativeAdminError("qualitative_phrase_catalog.terms must be a non-empty object")
    return catalog_id, terms


def _term_contract(code: str, term: Mapping[str, Any]) -> tuple[str, str, bool, list[str]]:
    risk = str(term.get("risk_tier", "")).strip()
    if risk not in ALLOWED_RISKS:
        raise QualitativeAdminError(f"qualitative phrase term {code!r} has invalid risk_tier")
    required_scope = str(term.get("required_evidence_scope", "")).strip()
    if required_scope not in ALLOWED_SCOPES:
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r} has invalid required_evidence_scope"
        )
    pattern_allowed = term.get("pattern_evidence_allowed", False)
    if not isinstance(pattern_allowed, bool):
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r}.pattern_evidence_allowed must be boolean"
        )
    variants = term.get("outward_variants")
    if not isinstance(variants, list) or len(variants) < 2:
        raise QualitativeAdminError(
            f"qualitative phrase term {code!r} requires at least two outward_variants"
        )
    cleaned = [_clean_string(value, f"qualitative phrase term {code!r}.outward_variants") for value in variants]
    if len({value.casefold() for value in cleaned}) != len(cleaned):
        raise QualitativeAdminError(f"qualitative phrase term {code!r} variants must be unique")
    if risk == "high" and (pattern_allowed or required_scope != "dated_person_task"):
        raise QualitativeAdminError(
            f"high-risk qualitative phrase term {code!r} must forbid pattern evidence and require dated_person_task"
        )
    return risk, required_scope, pattern_allowed, cleaned


def _select_variant(
    *,
    catalog_id: str,
    month_key: str,
    row: Mapping[str, Any],
    code: str,
    variants: list[str],
    last_index_by_code: dict[str, int],
) -> tuple[int, str]:
    seed = "|".join(
        (
            catalog_id,
            month_key,
            str(row.get("date", "")),
            str(row.get("technician", "")),
            code,
        )
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest[:16], 16) % len(variants)
    if len(variants) > 1 and last_index_by_code.get(code) == index:
        index = (index + 1) % len(variants)
    last_index_by_code[code] = index
    return index, variants[index]


def resolve_evidence_backed_contexts(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy whose evidence-backed rows have deterministic visible context.

    Legacy rows with ``qualitative_work_context`` and no ``workstream_evidence``
    remain unchanged. Evidence-backed rows must not also supply free text because
    that would create two competing semantic authorities.
    """

    resolved: dict[str, Any] = deepcopy(dict(spec))
    detail = resolved.get("detail_rows")
    if not isinstance(detail, list):
        return resolved

    evidence_rows = [row for row in detail if isinstance(row, Mapping) and row.get("workstream_evidence") is not None]
    if not evidence_rows:
        return resolved

    catalog = resolved.get("qualitative_phrase_catalog")
    if not isinstance(catalog, Mapping):
        raise QualitativeAdminError(
            "detail_rows.workstream_evidence requires qualitative_phrase_catalog"
        )
    catalog_id, terms = _catalog_terms(catalog)
    month_key = _clean_string(resolved.get("month_key"), "month_key")
    last_index_by_code: dict[str, int] = {}
    receipt_rows: list[dict[str, Any]] = []

    for row_index, row in enumerate(detail):
        if not isinstance(row, dict):
            continue
        evidence = row.get("workstream_evidence")
        if evidence is None:
            continue
        if str(row.get("qualitative_work_context", "")).strip():
            raise QualitativeAdminError(
                f"detail_rows[{row_index}] cannot combine qualitative_work_context with workstream_evidence"
            )
        if not isinstance(evidence, list) or not evidence:
            raise QualitativeAdminError(
                f"detail_rows[{row_index}].workstream_evidence must be a non-empty list"
            )

        fragments: list[str] = []
        receipt_items: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for item_index, item in enumerate(evidence):
            if not isinstance(item, Mapping):
                raise QualitativeAdminError(
                    f"detail_rows[{row_index}].workstream_evidence[{item_index}] must be an object"
                )
            code = _clean_string(item.get("code"), f"detail_rows[{row_index}].workstream_evidence[{item_index}].code")
            if code in seen_codes:
                raise QualitativeAdminError(f"detail_rows[{row_index}] repeats workstream code {code!r}")
            seen_codes.add(code)
            term = terms.get(code)
            if not isinstance(term, Mapping):
                raise QualitativeAdminError(f"detail_rows[{row_index}] references unknown workstream code {code!r}")
            risk, required_scope, pattern_allowed, variants = _term_contract(code, term)
            scope = _clean_string(
                item.get("evidence_scope"),
                f"detail_rows[{row_index}].workstream_evidence[{item_index}].evidence_scope",
            )
            if scope not in ALLOWED_SCOPES:
                raise QualitativeAdminError(f"detail_rows[{row_index}] has invalid evidence_scope {scope!r}")
            refs = item.get("evidence_refs")
            if not isinstance(refs, list) or not refs:
                raise QualitativeAdminError(f"detail_rows[{row_index}] workstream {code!r} requires evidence_refs")
            evidence_refs = [_clean_string(ref, f"detail_rows[{row_index}] {code}.evidence_refs") for ref in refs]
            if len(set(evidence_refs)) != len(evidence_refs):
                raise QualitativeAdminError(f"detail_rows[{row_index}] workstream {code!r} has duplicate evidence_refs")
            if risk == "high" and scope != "dated_person_task":
                raise QualitativeAdminError(
                    f"high-risk workstream {code!r} requires dated_person_task evidence"
                )
            if scope == "recurring_pattern" and not pattern_allowed:
                raise QualitativeAdminError(
                    f"workstream {code!r} does not allow recurring_pattern evidence"
                )
            if scope != "recurring_pattern" and SCOPE_RANK[scope] < SCOPE_RANK[required_scope]:
                raise QualitativeAdminError(
                    f"workstream {code!r} evidence_scope {scope!r} is weaker than required {required_scope!r}"
                )

            variant_index, fragment = _select_variant(
                catalog_id=catalog_id,
                month_key=month_key,
                row=row,
                code=code,
                variants=variants,
                last_index_by_code=last_index_by_code,
            )
            fragments.append(fragment)
            receipt_items.append(
                {
                    "code": code,
                    "risk_tier": risk,
                    "evidence_scope": scope,
                    "evidence_refs": evidence_refs,
                    "variant_index": variant_index,
                    "visible_phrase": fragment,
                }
            )

        row["qualitative_work_context"] = "; ".join(fragments) + "."
        receipt_rows.append(
            {
                "detail_row_index": row_index,
                "date": str(row.get("date", "")),
                "technician": str(row.get("technician", "")),
                "workstreams": receipt_items,
            }
        )

    resolved["_evidence_backed_context_receipt"] = {
        "schema_version": "nth-qualitative-context-receipt/v1",
        "catalog_id": catalog_id,
        "selection": "sha256 stable row identity with deterministic no-immediate-repeat guard",
        "canonical_codes_preserved": True,
        "evidence_refs_preserved": True,
        "kpi_semantics_changed": False,
        "rows": receipt_rows,
    }
    return resolved
